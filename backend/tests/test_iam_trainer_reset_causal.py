# ruff: noqa: F811
"""Real committed state/role changes, source waits, ACK loss and final actor time."""

import secrets
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime
from threading import Event

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import SyntheticSecret, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token
from tests.test_iam_password_reset import complete, reset_request
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body as role_body
from tests.test_iam_trainer_roles import change as role_change
from tests.test_iam_trainer_roles_causal import role_connections
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
from tests.test_workforce_state import request as state_request
from tests.test_workforce_state_causal import fingerprints
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event as AuditEvent
from y3management.audit.public import TrainerStateEvent
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.mfa import MFA
from y3management.iam.public import Authentication, ResetProof
from y3management.iam.roles import TrainerRoles

pytestmark = pytest.mark.postgres

IDENTITY = ("iam_trainer_bindings", "iam_trainer_role_grants")
BUSINESS = (
    "iam_accounts",
    "iam_sessions",
    "iam_reset_credentials",
    "audit_events",
    *IDENTITY,
)


def ready(t: TrainerScene) -> str:
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    return str(t.state()["account_id"])


def reset_source_fact(db: Database, ident: str) -> tuple[str, datetime, bool]:
    """Only fingerprints, expiry and consumed may escape credential queries."""
    with db.session() as s:
        row = s.execute(
            text(
                "SELECT md5((to_jsonb(c)-'consumed')::text),expires_at,consumed "
                "FROM iam_reset_credentials c WHERE account_id=:a ORDER BY generation DESC LIMIT 1"
            ),
            {"a": ident},
        ).one()
        return str(row[0]), row[1], bool(row[2])


def pending_without_password(db: Database, ident: str) -> bool:
    with db.session() as s:
        return bool(
            s.execute(
                text(
                    "SELECT state='ACTIVE' AND password_hash IS NULL AND password_reset_pending "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": ident},
            ).scalar_one()
        )


def test_prepared_reset_survives_committed_other_home_ba_off(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    t = trainer
    ident = ready(t)
    with closing(branch_actor(t.base, mfa[2])) as ba:
        actor = ba.get("/api/v1/auth/me").json()["account_id"]
        assert actor != ident
        token = link_token(reset_request(t.base.client, ident).json()["reset_link"])
        original_source = reset_source_fact(t.base.db, ident)
        original_identity = fingerprints(t.base.db, IDENTITY)
        reached, release = Event(), Event()
        proof_pids: list[int] = []
        state_pids: list[int] = []
        prepare, append = MFA.prepare_reset, Audit.append_trainer_state
        new = SyntheticSecret(secrets.token_urlsafe(24))

        def pause(self: MFA, raw: str, password: str) -> ResetProof:
            proof = prepare(self, raw, password)
            proof_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
            reached.set()
            assert release.wait(15)
            return proof

        def audit(self: Audit, event: TrainerStateEvent) -> None:
            append(self, event)
            state_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))

        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
            patch.setattr(MFA, "prepare_reset", pause)
            patch.setattr(Audit, "append_trainer_state", audit)
            pending = pool.submit(complete, t.recipient, token, new)
            try:
                assert reached.wait(5)
                payload = state_request(t, False)
                response = call(ba, "/admin/trainers/" + t.trainer + "/state", csrf(ba), payload)
                assert response.status_code == 200 and response.json()["changed"] is True
                with t.base.db.session() as reader:
                    assert reader.execute(
                        text(
                            "SELECT actor_id=:actor AND desired_active=false "
                            "FROM workforce_trainer_state_operations WHERE operation_id=:op"
                        ),
                        {"actor": actor, "op": payload["operation_id"]},
                    ).scalar_one()
                    assert not reader.execute(
                        text("SELECT active FROM workforce_trainers WHERE id=:t"),
                        {"t": t.trainer},
                    ).scalar_one()
                assert reset_source_fact(t.base.db, ident) == original_source
                assert fingerprints(t.base.db, IDENTITY) == original_identity
            finally:
                release.set()
            assert pending.result(timeout=10).status_code == 204
        assert len(proof_pids) == len(state_pids) == 1 and proof_pids != state_pids
        after = reset_source_fact(t.base.db, ident)
        assert after[:2] == original_source[:2] and after[2] is True
        assert fingerprints(t.base.db, IDENTITY) == original_identity
        assert t.signin(password=new).status_code == 401
        # Reactivation is a separate, explicit Master command; it does not reset credentials.
        on = state_request(t, True)
        assert (
            call(
                t.base.client, "/admin/trainers/" + t.trainer + "/state", csrf(t.base.client), on
            ).status_code
            == 200
        )
        assert t.signin(password=new).status_code == 204
        record_testsuite_property("reset_w1_proof_pid", proof_pids[0])
        record_testsuite_property("reset_w1_other_ba_commit_pid", state_pids[0])
        record_testsuite_property("reset_w1_inactive_credential_repair_then_explicit_on", True)


def test_withdraw_only_rejects_old_proof_then_same_source_repairs_role_zero(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    t = trainer
    ident = ready(t)
    token = link_token(reset_request(t.base.client, ident).json()["reset_link"])
    original_source = reset_source_fact(t.base.db, ident)
    binding = fingerprints(t.base.db, ("iam_trainer_bindings",))
    reached, release = Event(), Event()
    proof_pids: list[int] = []
    prepare = MFA.prepare_reset
    new = SyntheticSecret(secrets.token_urlsafe(24))

    def pause(self: MFA, raw: str, password: str) -> ResetProof:
        proof = prepare(self, raw, password)
        proof_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        reached.set()
        assert release.wait(15)
        return proof

    with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
        role_pids = role_connections(patch)
        patch.setattr(MFA, "prepare_reset", pause)
        pending = pool.submit(complete, t.recipient, token, new)
        try:
            assert reached.wait(5)
            payload = role_body(t, False)
            response = role_change(t, payload)
            assert response.status_code == 200 and response.json()["changed"] is True
            with t.base.db.session() as reader:
                assert reader.execute(
                    text(
                        "SELECT NOT granted AND committed_role_version=:v "
                        "FROM iam_trainer_role_operations WHERE operation_id=:op"
                    ),
                    {"v": payload["expected_role_version"] + 1, "op": payload["operation_id"]},
                ).scalar_one()
            assert reset_source_fact(t.base.db, ident) == original_source
        finally:
            release.set()
        assert pending.result(timeout=10).status_code == 401
    assert len(proof_pids) == len(role_pids) == 1 and proof_pids != role_pids
    assert reset_source_fact(t.base.db, ident) == original_source
    assert pending_without_password(t.base.db, ident)
    withdrawn_identity = fingerprints(t.base.db, IDENTITY)
    # There has been exactly one role transition. A fresh proof may repair Role0 credentials.
    assert complete(t.recipient, token, new).status_code == 204
    assert fingerprints(t.base.db, IDENTITY) == withdrawn_identity
    assert fingerprints(t.base.db, ("iam_trainer_bindings",)) == binding
    after = reset_source_fact(t.base.db, ident)
    assert after[:2] == original_source[:2] and after[2] is True
    assert t.signin(password=new).status_code == 401
    assert role_change(t, role_body(t, True)).status_code == 200
    assert t.signin(password=new).status_code == 204
    record_testsuite_property("reset_role0_old_proof_pid", proof_pids[0])
    record_testsuite_property("reset_role0_withdraw_commit_pid", role_pids[0])
    record_testsuite_property("reset_role0_same_source_new_proof_before_regrant", True)


@pytest.mark.parametrize("locked", ["account", "source"])
def test_trainer_reset_expires_during_observed_row_wait(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
    locked: str,
) -> None:
    t = trainer
    ident = ready(t)
    token = link_token(reset_request(t.base.client, ident).json()["reset_link"])
    reached, release = Event(), Event()
    prepare = MFA.prepare_reset
    proof_pids: list[int] = []
    new = SyntheticSecret(secrets.token_urlsafe(24))

    def pause(self: MFA, raw: str, password: str) -> ResetProof:
        proof = prepare(self, raw, password)
        proof_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        reached.set()
        assert release.wait(15)
        return proof

    with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
        patch.setattr(MFA, "prepare_reset", pause)
        pending = pool.submit(complete, t.recipient, token, new)
        try:
            assert reached.wait(5)
            with t.base.db.session() as holder:
                holder_pid = int(holder.execute(text("SELECT pg_backend_pid()")).scalar_one())
                assert holder_pid != proof_pids[0]
                if locked == "account":
                    holder.execute(
                        text("SELECT id FROM iam_accounts WHERE id=:a FOR UPDATE"), {"a": ident}
                    ).one()
                # Existing expiry-race control, while holding the actual source row until expiry.
                deadline = holder.execute(
                    text(
                        "UPDATE iam_reset_credentials SET expires_at=clock_timestamp()+"
                        "interval '800 milliseconds' WHERE account_id=:a RETURNING expires_at"
                    ),
                    {"a": ident},
                ).scalar_one()
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                try:
                    release.set()
                    wait_for_owned_block(t.base.db, holder_pid, waiters)
                    waiter_pid = waiters[-1]
                finally:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
                assert not pending.done() and waiter_pid != holder_pid
                with t.base.db.session() as observer:
                    row = observer.execute(
                        text(
                            "SELECT pg_blocking_pids(pid),wait_event_type,query "
                            "FROM pg_stat_activity WHERE pid=:p"
                        ),
                        {"p": waiter_pid},
                    ).one()
                    assert holder_pid in row[0] and row[1] == "Lock"
                    assert (
                        "iam_accounts" if locked == "account" else "iam_reset_credentials"
                    ) in row[2]
                assert holder.execute(
                    text("SELECT clock_timestamp()<:e"), {"e": deadline}
                ).scalar_one()
                holder.execute(text("SELECT pg_sleep(1.1)"))
                assert holder.execute(
                    text("SELECT clock_timestamp()>=:e"), {"e": deadline}
                ).scalar_one()
                holder.commit()
            assert pending.result(timeout=10).status_code == 401
        finally:
            release.set()
    assert pending_without_password(t.base.db, ident)
    fact = reset_source_fact(t.base.db, ident)
    assert fact[1] == deadline and fact[2] is False
    assert t.signin().status_code == 401
    record_testsuite_property("reset_expiry_" + locked + "_holder_pid", holder_pid)
    record_testsuite_property("reset_expiry_" + locked + "_waiter_pid", waiter_pid)
    record_testsuite_property("reset_expiry_" + locked + "_observed_block_before_expiry", True)


def test_committed_start_ack_loss_safe_get_then_explicit_reissue(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    t = trainer
    ident = ready(t)
    old_cookie = SyntheticSecret(t.recipient.cookies.get("__Host-y3-auth") or "")
    initial = t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset").json()
    identity = fingerprints(t.base.db, IDENTITY)
    append, commit = Audit.append, Session.commit
    committed: list[bool] = []

    def audit(self: Audit, event: AuditEvent) -> None:
        append(self, event)
        if event.action == "password_reset_start":
            self.s.info["causal_reset_ack"] = True

    def ack_lost(session: Session) -> None:
        commit(session)
        if session.info.pop("causal_reset_ack", False):
            committed.append(True)
            raise OperationalError("synthetic acknowledgement loss", {}, RuntimeError("lost"))

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", audit)
        patch.setattr(Session, "commit", ack_lost)
        response = reset_request(t.base.client, ident)
    assert response.status_code == 503 and response.json() == {"detail": "commit_outcome_unknown"}
    assert committed == [True] and "reset_link" not in response.json()
    source_before_get = reset_source_fact(t.base.db, ident)
    assert source_before_get[2] is False and pending_without_password(t.base.db, ident)
    with t.base.db.session() as reader:
        assert reader.execute(
            text("SELECT bool_and(revoked) FROM iam_sessions WHERE account_id=:a"), {"a": ident}
        ).scalar_one()
        assert (
            reader.execute(
                text(
                    "SELECT count(*) FROM audit_events WHERE target_id=:a "
                    "AND action='password_reset_start'"
                ),
                {"a": ident},
            ).scalar_one()
            == 1
        )
    assert (
        t.recipient.get(
            "/api/v1/auth/me", headers={"Cookie": "__Host-y3-auth=" + old_cookie}
        ).status_code
        == 401
    )
    assert t.signin().status_code == 401
    observed = t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset")
    assert observed.status_code == 200 and "reset_link" not in observed.json()
    current = observed.json()
    assert current["password_reset_pending"] is True
    assert current["generation"] == initial["generation"] + 1
    assert current["account_version"] == initial["account_version"] + 1
    assert reset_source_fact(t.base.db, ident) == source_before_get
    issued = reset_request(t.base.client, ident, reissue=True)
    assert issued.status_code == 201
    # Observe old-source invalidation before the next preauth allocation may GC it.
    with t.base.db.session() as reader:
        assert reader.execute(
            text(
                "SELECT count(*)=2 AND count(*) FILTER (WHERE consumed)=1 "
                "AND min(generation)=:g AND max(generation)=:g+1 "
                "FROM iam_reset_credentials WHERE account_id=:a"
            ),
            {"a": ident, "g": current["generation"]},
        ).scalar_one()
        assert reader.execute(
            text(
                "SELECT md5((to_jsonb(c)-'consumed')::text)=:fingerprint "
                "AND expires_at=:expiry AND consumed FROM iam_reset_credentials c "
                "WHERE account_id=:a AND generation=:g"
            ),
            {
                "a": ident,
                "g": current["generation"],
                "fingerprint": source_before_get[0],
                "expiry": source_before_get[1],
            },
        ).scalar_one()
    new = SyntheticSecret(secrets.token_urlsafe(24))
    assert complete(t.recipient, link_token(issued.json()["reset_link"]), new).status_code == 204
    assert fingerprints(t.base.db, IDENTITY) == identity
    assert t.signin().status_code == 401
    assert t.signin(password=new).status_code == 204
    with t.base.db.session() as reader:
        assert reader.execute(
            text(
                "SELECT NOT password_reset_pending AND password_hash IS NOT NULL "
                "AND reset_generation=:g FROM iam_accounts WHERE id=:a"
            ),
            {"a": ident, "g": initial["generation"] + 2},
        ).scalar_one()
    record_testsuite_property("reset_ack_actual_commit_then_503", True)
    record_testsuite_property("reset_ack_safe_get_then_explicit_reissue_only", True)


@pytest.mark.parametrize("absolute", [False, True], ids=["idle", "absolute"])
def test_real_actor_deadline_after_audit_and_final_facts_rolls_back(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
    absolute: bool,
) -> None:
    t = trainer
    ident = ready(t)
    # Both the real target session and the actor session are live before the mutation.
    assert t.recipient.get("/api/v1/auth/me").status_code == 200
    path = f"/admin/accounts/{ident}/password-reset"
    state = t.base.client.get("/api/v1" + path).json()
    actor = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    nonce = csrf(t.base.client)
    with t.base.db.session() as s:
        assert (
            s.execute(
                text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
                {"a": ident},
            ).scalar_one()
            == 1
        )
        if absolute:
            s.execute(
                text("""WITH shifted AS (UPDATE iam_security_states
                SET expires_at=clock_timestamp()+interval '2 seconds'
                WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a)
                RETURNING id,expires_at)
                UPDATE iam_sessions s SET expires_at=shifted.expires_at,
                created_at=shifted.expires_at-interval '8 hours',
                last_activity=shifted.expires_at-interval '1 minute'
                FROM shifted WHERE s.id=shifted.id"""),
                {"a": actor},
            )
        else:
            s.execute(
                text("""UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',
                last_activity=clock_timestamp()-interval '29 minutes 58 seconds'
                WHERE account_id=:a"""),
                {"a": actor},
            )
        s.commit()
    before = fingerprints(t.base.db, BUSINESS)
    stable, append = TrainerRoles.stable_actor, Audit.append
    audit_finished = False
    observations: list[tuple[bool, bool]] = []

    def audit(self: Audit, event: AuditEvent) -> None:
        nonlocal audit_finished
        append(self, event)
        if event.action == "password_reset_start":
            audit_finished = True

    def delayed(self: TrainerRoles, auth: Authentication) -> bytes:
        value = stable(self, auth)
        if audit_finished:
            # These are actual uncommitted writes, observed only after required audit append.
            assert self.s.execute(
                text(
                    "SELECT password_hash IS NULL AND password_reset_pending "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": ident},
            ).scalar_one()
            assert self.s.execute(
                text(
                    "SELECT count(*)=1 AND bool_and(expires_at>clock_timestamp() AND NOT consumed) "
                    "FROM iam_reset_credentials WHERE account_id=:a"
                ),
                {"a": ident},
            ).scalar_one()
            assert (
                self.s.execute(
                    text(
                        "SELECT count(*) FROM audit_events WHERE target_id=:a "
                        "AND action='password_reset_start'"
                    ),
                    {"a": ident},
                ).scalar_one()
                == 1
            )
            assert self.s.execute(
                text("SELECT bool_and(revoked) FROM iam_sessions WHERE account_id=:a"),
                {"a": ident},
            ).scalar_one()
            query = text(
                "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
                "expires_at>clock_timestamp() FROM iam_sessions WHERE id=:i"
            )
            observations.append(tuple(self.s.execute(query, {"i": auth.session_id}).one()))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            observations.append(tuple(self.s.execute(query, {"i": auth.session_id}).one()))
        return value

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", audit)
        patch.setattr(TrainerRoles, "stable_actor", delayed)
        response = call(
            t.base.client,
            path,
            nonce,
            {
                "expected_account_version": state["account_version"],
                "expected_generation": state["generation"],
                "identity_confirmed": True,
            },
        )
    assert response.status_code == 401 and audit_finished
    assert observations == [(True, True), (True, False) if absolute else (False, True)]
    # Includes actor activity and all target sessions: no partial target/source/audit commit.
    assert fingerprints(t.base.db, BUSINESS) == before
    assert t.recipient.get("/api/v1/auth/me").status_code == 200
    record_testsuite_property(
        "reset_actual_" + ("absolute" if absolute else "idle") + "_crossed_after_audit", True
    )
