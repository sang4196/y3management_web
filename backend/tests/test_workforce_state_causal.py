# ruff: noqa: F811
"""Real committed W1 proof, hint, shared-lock and DDL boundaries."""

import subprocess
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime
from threading import Event
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event as sa_event
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from tests.conftest import qa_register_process, qa_stop_process
from tests.test_iam import ORIGIN, SyntheticSecret, child_env, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles_causal import role_connections
from tests.test_iam_trainer_roles_security import link
from tests.test_iam_trainer_roles_storage import migrate
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
from tests.test_workforce_state import change, request
from tests.workforce_state_seed import assert_loss_guard, legacy_trainer  # noqa: F401
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerIdentityEvent, TrainerStateEvent
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.public import Authentication, TrainerSetupProof
from y3management.workforce.infrastructure import Repository
from y3management.workforce.public import TrainerIdentityFact

pytestmark = pytest.mark.postgres

IDENTITY_TABLES = (
    "iam_accounts",
    "iam_admin_grants",
    "iam_sessions",
    "iam_passkeys",
    "iam_trainer_bindings",
    "iam_trainer_role_grants",
    "iam_trainer_setup_credentials",
    "iam_trainer_role_operations",
    "audit_trainer_role_events",
    "iam_security_states",
    "iam_mfa_contexts",
    "iam_budgets",
    "iam_attempts",
)
STATE_TABLES = (
    "workforce_trainers",
    "workforce_initial_snapshots",
    "workforce_registration_operations",
    "workforce_trainer_state_origins",
    "workforce_trainer_state_operations",
    "workforce_trainer_state_transitions",
    "audit_trainer_state_events",
)


def fingerprints(db: Database, tables: tuple[str, ...]) -> dict[str, str]:
    """Return only DB-side digests so assertions cannot print credential/source rows."""
    with db.session() as s:
        return {
            table: str(
                s.execute(
                    text(
                        "SELECT md5(COALESCE(jsonb_agg(to_jsonb(x) "
                        "ORDER BY to_jsonb(x)::text)::text,'[]')) FROM " + table + " x"
                    )
                ).scalar_one()
            )
            for table in tables
        }


def source_fact(db: Database) -> tuple[str, datetime, bool]:
    with db.session() as s:
        row = s.execute(
            text(
                "SELECT md5((to_jsonb(c)-'consumed')::text),expires_at,consumed "
                "FROM iam_trainer_setup_credentials c"
            )
        ).one()
        return str(row[0]), row[1], bool(row[2])


def credentials(db: Database, ident: str) -> tuple[str, int, int]:
    with db.session() as s:
        row = s.execute(
            text(
                "SELECT md5(password_hash),row_version,security_version "
                "FROM iam_accounts WHERE id=:a"
            ),
            {"a": ident},
        ).one()
        return str(row[0]), int(row[1]), int(row[2])


def installation_witness(db: Database, holder: int, waiters: list[int]) -> int:
    wait_for_owned_block(db, holder, waiters)
    waiter = waiters[-1]
    with db.session() as observer:
        row = observer.execute(
            text(
                "SELECT pg_blocking_pids(pid),wait_event_type,query "
                "FROM pg_stat_activity WHERE pid=:p"
            ),
            {"p": waiter},
        ).one()
    assert waiter != holder and holder in row[0] and row[1] == "Lock"
    assert "iam_installation" in row[2]
    return waiter


@pytest.mark.parametrize("reactivate", [False, True], ids=["off-only", "off-then-on"])
def test_prepared_setup_current_state_without_source_epoch(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
    reactivate: bool,
) -> None:
    t = trainer
    token = source(t.issue())
    original_source = source_fact(t.base.db)
    original_account = fingerprints(t.base.db, ("iam_accounts",))
    assert original_source[2] is False
    reached, release = Event(), Event()
    proof_pids: list[int] = []
    state_pids: list[int] = []
    original = IAM.prepare_trainer_setup
    original_audit = Audit.append_trainer_state

    def pause(self: IAM, token: str, password: str) -> TrainerSetupProof:
        proof = original(self, token, password)
        assert proof.expires_at == original_source[1] and proof.trainer_role_epoch == 1
        proof_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        reached.set()
        assert release.wait(15)
        return proof

    def audit(self: Audit, event: TrainerStateEvent) -> None:
        original_audit(self, event)
        state_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "prepare_trainer_setup", pause)
        patch.setattr(Audit, "append_trainer_state", audit)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(t.complete, token)
            try:
                assert reached.wait(5)
                off = change(t, request(t, False))
                assert off.status_code == 200 and off.json()["changed"] is True
                assert source_fact(t.base.db) == original_source
                if reactivate:
                    on = change(t, request(t, True))
                    assert on.status_code == 200 and on.json()["changed"] is True
                    assert source_fact(t.base.db) == original_source
                assert fingerprints(t.base.db, ("iam_accounts",)) == original_account
            finally:
                release.set()
            assert pending.result(timeout=10).status_code == (204 if reactivate else 400)
    final_source = source_fact(t.base.db)
    assert final_source[:2] == original_source[:2] and final_source[2] is reactivate
    assert len(proof_pids) == 1 and len(state_pids) == (2 if reactivate else 1)
    assert all(pid != proof_pids[0] for pid in state_pids)
    if reactivate:
        assert t.signin().status_code == 204
    else:
        assert fingerprints(t.base.db, ("iam_accounts",)) == original_account
    prefix = "w1_setup_" + ("off_on" if reactivate else "off")
    record_testsuite_property(prefix + "_proof_pid", proof_pids[0])
    record_testsuite_property(prefix + "_committed_state_pids", ",".join(map(str, state_pids)))
    record_testsuite_property(prefix + "_original_source_expiry_versions_preserved", True)


def test_new_i2_binding_between_hint_and_main_rejected(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    t = trainer
    with closing(branch_actor(t.base, mfa[2])) as target:
        ident = target.get("/api/v1/auth/me").json()["account_id"]
        master = t.base.client.get("/api/v1/auth/me").json()["account_id"]
        assert ident != master
        linking = link(t, ident, "workforce.branch")
        payload = request(t, False)
        nonce, other_nonce = csrf(t.base.client), csrf(target)
        raw = SyntheticSecret(t.base.client.cookies.get("__Host-y3-auth") or "")
        original = IAM.authenticate
        prior_connections: list[Connection] = []
        main_pids: list[int] = []
        committed: dict[str, str] = {}
        calls = 0
        with monkeypatch.context() as patch:
            link_pids = role_connections(patch)

            def authenticate(self: IAM, token: str | None, **kwargs: Any) -> Authentication:
                nonlocal calls, committed
                selected = token == raw and kwargs.get("management") is True
                if selected:
                    calls += 1
                    if calls == 2:
                        assert len(prior_connections) == 1 and prior_connections[0].closed
                        main_pids.append(
                            int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
                        )
                        linked = call(
                            target, "/admin/trainers/" + t.trainer + "/role", other_nonce, linking
                        )
                        assert linked.status_code == 200
                        assert linked.json()["reauthentication_required"] is True
                        with t.base.db.session() as reader:
                            assert (
                                str(
                                    reader.execute(
                                        text("SELECT account_id FROM iam_trainer_bindings")
                                    ).scalar_one()
                                )
                                == ident
                            )
                        # Capture the other actor's durable effects before failed W1 resumes.
                        committed = fingerprints(t.base.db, IDENTITY_TABLES + STATE_TABLES)
                result = original(self, token, **kwargs)
                if selected and calls == 1:
                    prior_connections.append(self.s.connection())
                return result

            patch.setattr(IAM, "authenticate", authenticate)
            failed = call(t.base.client, "/admin/trainers/" + t.trainer + "/state", nonce, payload)
            assert failed.status_code == 409
        assert calls == 2 and len(link_pids) == len(main_pids) == 1
        assert link_pids[0] != main_pids[0]
        assert committed and fingerprints(t.base.db, IDENTITY_TABLES + STATE_TABLES) == committed
        assert change(t, request(t, False)).status_code == 200
        with t.base.db.session() as reader:
            assert (
                reader.execute(text("SELECT active FROM workforce_trainers")).scalar_one() is False
            )
            assert (
                reader.execute(text("SELECT row_version FROM workforce_trainers")).scalar_one() == 2
            )
            for table in ("workforce_trainer_state_operations", "audit_trainer_state_events"):
                assert reader.execute(text("SELECT count(*) FROM " + table)).scalar_one() == 1
        record_testsuite_property("w1_hint_preflight_connection_closed", True)
        record_testsuite_property("w1_hint_main_pid", main_pids[0])
        record_testsuite_property("w1_hint_other_actor_committed_link_pid", link_pids[0])
        record_testsuite_property("w1_hint_409_preserves_facts_fresh_request_200", True)


@pytest.mark.parametrize("password", [False, True], ids=["currentprincipal", "c3"])
@pytest.mark.parametrize("self_first", [False, True], ids=["w1-first", "self-first"])
def test_deactivate_and_self_request_observed_both_orders(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
    password: bool,
    self_first: bool,
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    ident = str(t.state()["account_id"])
    before = credentials(t.base.db, ident)
    nonce, admin_nonce = csrf(t.recipient), csrf(t.base.client)
    payload = request(t, False)
    new_password = SyntheticSecret(str(t.password) + "New")
    reached, release = Event(), Event()
    holders: list[int] = []
    phases: list[str] = []
    original_state = Audit.append_trainer_state
    original_identity = Audit.append_trainer_identity
    original_fact = Repository.identity

    def pause(s: Session, phase: str) -> None:
        holders.append(int(s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        phases.append(phase)
        reached.set()
        assert release.wait(15)

    def state_audit(self: Audit, event: TrainerStateEvent) -> None:
        original_state(self, event)
        if not self_first and not holders:
            pause(self.s, "W1 state/update/revocation/audit")

    def identity_audit(self: Audit, event: TrainerIdentityEvent) -> None:
        original_identity(self, event)
        if self_first and password and event.kind == "password_change" and not holders:
            pause(self.s, "C3 credential/Trainer-SHARE/password/audit")

    def fact(
        self: Repository, org: UUID, trainer: UUID, *, lock: bool = False, shared: bool = False
    ) -> TrainerIdentityFact:
        value = original_fact(self, org, trainer, lock=lock, shared=shared)
        if self_first and not password and shared and str(trainer) == t.trainer and not holders:
            pause(self.s, "currentprincipal Trainer-SHARE")
        return value

    def self_request() -> Any:
        if password:
            return call(
                t.recipient,
                "/auth/password",
                nonce,
                {"current_password": t.password, "new_password": new_password},
            )
        return t.recipient.get("/api/v1/auth/me")

    def deactivate() -> Any:
        return call(t.base.client, "/admin/trainers/" + t.trainer + "/state", admin_nonce, payload)

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append_trainer_state", state_audit)
        patch.setattr(Audit, "append_trainer_identity", identity_audit)
        patch.setattr(Repository, "identity", fact)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self_request if self_first else deactivate)
            capture = None
            try:
                assert reached.wait(5), "First command did not reach the actual locked phase"
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(deactivate if self_first else self_request)
                waiter = installation_witness(t.base.db, holders[0], waiters)
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            a, b = first.result(timeout=10), second.result(timeout=10)
    self_result, state_result = (a, b) if self_first else (b, a)
    assert state_result.status_code == 200
    assert self_result.status_code == ((204 if password else 200) if self_first else 401)
    if self_first and not password:
        assert self_result.json()["roles"][0]["role"] == "TRAINER"
    after = credentials(t.base.db, ident)
    if self_first and password:
        assert after[0] != before[0] and after[1:] == (before[1] + 1, before[2] + 1)
    else:
        assert after == before
    with t.base.db.session() as reader:
        assert reader.execute(text("SELECT active FROM workforce_trainers")).scalar_one() is False
        assert reader.execute(text("SELECT row_version FROM workforce_trainers")).scalar_one() == 2
        assert (
            reader.execute(
                text("SELECT count(*) FROM workforce_trainer_state_transitions")
            ).scalar_one()
            == 1
        )
    assert t.recipient.get("/api/v1/auth/me").status_code == 401
    assert change(t, request(t, True)).status_code == 200
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as fresh:
        effective_password = new_password if self_first and password else t.password
        assert t.signin(fresh, password=effective_password).status_code == 204
    prefix = "w1_lock_" + ("self_first_" if self_first else "w1_first_")
    prefix += "c3" if password else "principal"
    record_testsuite_property(prefix + "_holder_pid", holders[0])
    record_testsuite_property(prefix + "_waiter_pid", waiter)
    record_testsuite_property(prefix + "_holder_phase", phases[0])
    record_testsuite_property(prefix + "_actual_first_wait", "installation")


def test_downgrade_waits_for_actual_state_writer_and_preserves_history(
    legacy_trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    t = legacy_trainer
    # Positive control: the pure observed baseline is removable before a real state operation.
    assert migrate(mfa[0], "downgrade", "0012_iam_trainer_roles") == 0
    assert migrate(mfa[0], "upgrade", "head") == 0
    payload = request(t, False)
    reached, release = Event(), Event()
    holders: list[int] = []
    original = Audit.append_trainer_state

    def pause(self: Audit, event: TrainerStateEvent) -> None:
        original(self, event)
        holders.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        reached.set()
        assert release.wait(15)

    monkeypatch.setattr(Audit, "append_trainer_state", pause)
    appname = "state-downgrade-" + uuid4().hex
    env = child_env(mfa[0])
    env["PGAPPNAME"] = appname
    with ThreadPoolExecutor(max_workers=1) as pool:
        changing = pool.submit(change, t, payload)
        process = None
        try:
            assert reached.wait(5)
            process = subprocess.Popen(
                [sys.executable, "-m", "alembic", "downgrade", "0012_iam_trainer_roles"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            qa_register_process(process)
            waiter = None
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and process.poll() is None:
                with t.base.db.session() as reader:
                    row = reader.execute(
                        text(
                            "SELECT pid,query FROM pg_stat_activity "
                            "WHERE datname=current_database() AND application_name=:n "
                            "AND wait_event_type='Lock' AND pid<>:h "
                            "AND :h=ANY(pg_blocking_pids(pid))"
                        ),
                        {"n": appname, "h": holders[0]},
                    ).first()
                if row is not None:
                    waiter = int(row.pid)
                    assert "iam_installation" in row.query
                    break
                time.sleep(0.02)
            assert waiter is not None and waiter != holders[0]
            release.set()
            assert changing.result(timeout=10).status_code == 200
            process.communicate(timeout=10)
            assert process.returncode is not None and process.returncode != 0
            before_guard = fingerprints(t.base.db, IDENTITY_TABLES + STATE_TABLES)
            # CLI errors are redacted. Observe the actual revision's DB guard, rolling back DDL.
            assert_loss_guard(
                t.base.db,
                ["0013_workforce_trainer_state.py"],
                "trainer state facts must be preserved",
            )
            assert fingerprints(t.base.db, IDENTITY_TABLES + STATE_TABLES) == before_guard
            with t.base.db.session() as reader:
                assert (
                    reader.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                    == "0013_workforce_trainer_state"
                )
                assert (
                    reader.execute(text("SELECT active FROM workforce_trainers")).scalar_one()
                    is False
                )
                assert (
                    reader.execute(text("SELECT row_version FROM workforce_trainers")).scalar_one()
                    == 2
                )
                for table in (
                    "workforce_trainer_state_operations",
                    "workforce_trainer_state_transitions",
                    "audit_trainer_state_events",
                ):
                    assert reader.execute(text("SELECT count(*) FROM " + table)).scalar_one() == 1
                assert tuple(
                    reader.execute(
                        text(
                            "SELECT origin,active,trainer_version "
                            "FROM workforce_trainer_state_origins"
                        )
                    ).one()
                ) == ("legacy_observation", True, 1)
            record_testsuite_property("w1_ddl_holder_pid", holders[0])
            record_testsuite_property("w1_ddl_waiter_pid", waiter)
            record_testsuite_property("w1_ddl_actual_first_wait", "installation")
            record_testsuite_property("w1_ddl_child_exit_code", process.returncode)
            record_testsuite_property("w1_ddl_positive_control_and_guard_preservation", True)
        finally:
            release.set()
            if process is not None:
                qa_stop_process(process)
