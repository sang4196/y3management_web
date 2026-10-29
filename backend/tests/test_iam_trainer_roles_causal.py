# ruff: noqa: F811
"""Committed role epochs and observed credential-chain serialization across real actors."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event as sa_event
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token, recovery_options, recovery_request
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body, change, state
from tests.test_iam_trainer_roles_security import link
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerRoleEvent
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.mfa import MFA
from y3management.iam.public import RegistrationProof, TrainerSetupProof
from y3management.iam.roles import TrainerRoles

pytestmark = pytest.mark.postgres


def role_connections(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    pids: list[int] = []
    original = Audit.append_trainer_role

    def append(self: Audit, event: TrainerRoleEvent) -> None:
        original(self, event)
        pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))

    monkeypatch.setattr(Audit, "append_trainer_role", append)
    return pids


def committed_cycle(t: TrainerScene) -> None:
    """Both HTTP responses follow commit; a separate connection reads both durable receipts."""
    initial = state(t)
    actor = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    assert actor != initial["account_id"]
    operations = []
    for desired in (False, True):
        request = body(t, desired)
        operations.append(request["operation_id"])
        response = change(t, request)
        assert response.status_code == 200
        assert response.json()["changed"] is True
    with t.base.db.session() as reader:
        rows = reader.execute(
            text(
                "SELECT actor_id,granted,committed_role_version FROM iam_trainer_role_operations "
                "WHERE operation_id IN (:a,:b) ORDER BY committed_role_version"
            ),
            {"a": operations[0], "b": operations[1]},
        ).all()
        assert [(str(r.actor_id), r.granted, r.committed_role_version) for r in rows] == [
            (actor, False, initial["role_version"] + 1),
            (actor, True, initial["role_version"] + 2),
        ]


def test_verified_uv_proof_cannot_cross_committed_role_cycle(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident, _ = provision(t.base.client, target, mfa[2])
        assert change(t, link(t, ident, "second.master")).status_code == 200
        issued = recovery_request(t.base.client, ident)
        assert issued.status_code == 201
        token = link_token(issued.json()["recovery_link"])
        options_response = recovery_options(target, token)
        assert options_response.status_code == 200
        options = options_response.json()
        replacement = Authenticator()
        payload = {"credential": replacement.registration(options["publicKey"])}
        with t.base.db.session() as reader:
            original_source = reader.execute(
                text("SELECT md5(row_to_json(x)::text) FROM iam_recovery_credentials x")
            ).scalar_one()
        original = MFA.verify_registration
        proof_pids: list[int] = []
        with monkeypatch.context() as patch:
            role_pids = role_connections(patch)

            def verify(
                self: MFA, token: str | None, nonce: str | None, payload: str
            ) -> RegistrationProof:
                proof = original(self, token, nonce, payload)
                assert proof.purpose == "recovery"
                proof_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
                committed_cycle(t)
                return proof

            patch.setattr(MFA, "verify_registration", verify)
            response = call(
                target, "/auth/passkeys/recovery/verify", options["csrf_token"], payload
            )
            assert response.status_code == 401
        assert len(proof_pids) == 1 and len(role_pids) == 2
        assert all(pid != proof_pids[0] for pid in role_pids)
        with t.base.db.session() as reader:
            assert (
                reader.execute(
                    text("SELECT md5(row_to_json(x)::text) FROM iam_recovery_credentials x")
                ).scalar_one()
                == original_source
            )
            assert (
                reader.execute(
                    text(
                        "SELECT count(*) FROM iam_passkeys "
                        "WHERE account_id=:a AND revoked_at IS NULL"
                    ),
                    {"a": ident},
                ).scalar_one()
                == 0
            )
        fresh_response = recovery_options(target, token)
        assert fresh_response.status_code == 200
        fresh = fresh_response.json()
        assert (
            call(
                target,
                "/auth/passkeys/recovery/verify",
                fresh["csrf_token"],
                {"credential": replacement.registration(fresh["publicKey"])},
            ).status_code
            == 204
        )
        login_mfa(target, mfa[2], replacement, "second.master")
        assert [r["role"] for r in target.get("/api/v1/auth/me").json()["roles"]] == [
            "ADMIN",
            "TRAINER",
        ]
        record_testsuite_property("causal_uv_proof_pid", proof_pids[0])
        record_testsuite_property("causal_uv_committed_role_pids", ",".join(map(str, role_pids)))


def test_prepared_initial_hash_cannot_cross_committed_role_cycle(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
) -> None:
    t = trainer
    old = source(t.issue())
    ident = state(t)["account_id"]
    with t.base.db.session() as reader:
        original_account = reader.execute(
            text(
                "SELECT state,password_hash IS NULL,row_version,security_version "
                "FROM iam_accounts WHERE id=:a"
            ),
            {"a": ident},
        ).one()
    original = IAM.prepare_trainer_setup
    proof_pids: list[int] = []
    with monkeypatch.context() as patch:
        role_pids = role_connections(patch)

        def prepare(self: IAM, token: str, password: str) -> TrainerSetupProof:
            proof = original(self, token, password)
            assert proof.trainer_role_epoch == 1
            proof_pids.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
            committed_cycle(t)
            return proof

        patch.setattr(IAM, "prepare_trainer_setup", prepare)
        assert t.complete(old).status_code == 400
    assert len(proof_pids) == 1 and len(role_pids) == 2
    assert all(pid != proof_pids[0] for pid in role_pids)
    with t.base.db.session() as reader:
        assert (
            reader.execute(
                text(
                    "SELECT state,password_hash IS NULL,row_version,security_version "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": ident},
            ).one()
            == original_account
        )
        assert reader.execute(
            text("SELECT consumed FROM iam_trainer_setup_credentials")
        ).scalar_one()
    assert state(t)["role_version"] == 3
    assert t.complete(old).status_code == 400
    fresh = source(t.reissue())
    assert t.complete(fresh).status_code == 204
    assert t.signin().status_code == 204
    # A signed-in client's CSRF belongs to its AuthSession, not the anonymous setup source.
    # Use fresh preauth so rejection must reach the old source rather than stop at CSRF.
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as signed_out:
        assert (
            call(
                signed_out,
                "/auth/trainer-credentials/complete",
                csrf(signed_out),
                {"setup_token": old, "new_password": t.password},
            ).status_code
            == 400
        )
    record_testsuite_property("causal_initial_proof_pid", proof_pids[0])
    record_testsuite_property("causal_initial_committed_role_pids", ",".join(map(str, role_pids)))


@pytest.mark.parametrize("role_first", [False, True], ids=["reissue-first", "role-first"])
def test_initial_reissue_and_role_share_observed_lock_chain(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    record_testsuite_property: Callable[[str, object], None],
    role_first: bool,
) -> None:
    """The holder reached real credential locks; the other actor waits at installation."""
    t = trainer
    old = source(t.issue())
    ident = str(state(t)["account_id"])
    request = body(t, False)
    setup_request = {"operation_id": str(uuid4()), "expected_account_version": 1}
    reached, release = Event(), Event()
    holders: list[int] = []
    original_credentials = IAM.lock_trainer_credentials
    original_role = TrainerRoles.lock

    def pause(adapter: Any) -> None:
        assert (
            adapter.s.execute(
                text("SELECT count(*) FROM iam_trainer_setup_credentials WHERE account_id=:a"),
                {"a": ident},
            ).scalar_one()
            == 1
        )
        holders.append(int(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        reached.set()
        assert release.wait(10), "Credential-chain holder was not released"

    def credentials(self: IAM, account: UUID) -> None:
        original_credentials(self, account)
        if not role_first and str(account) == ident and not holders:
            pause(self)

    def role(self: TrainerRoles, account: UUID) -> None:
        original_role(self, account)
        if role_first and str(account) == ident and not holders:
            pause(self)

    with closing(branch_actor(t.base, mfa[2])) as other:
        actor_a = t.base.client.get("/api/v1/auth/me").json()["account_id"]
        actor_b = other.get("/api/v1/auth/me").json()["account_id"]
        assert actor_a != actor_b and ident not in (actor_a, actor_b)
        nonce_a, nonce_b = csrf(t.base.client), csrf(other)

        def reissue() -> Any:
            return call(
                t.base.client,
                "/admin/trainers/" + t.trainer + "/initial-setup",
                nonce_a,
                setup_request,
            )

        def withdraw() -> Any:
            return call(other, "/admin/trainers/" + t.trainer + "/role", nonce_b, request)

        with monkeypatch.context() as patch:
            patch.setattr(IAM, "lock_trainer_credentials", credentials)
            patch.setattr(TrainerRoles, "lock", role)
            with ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(withdraw if role_first else reissue)
                capture = None
                waiters: list[int] = []
                try:
                    assert reached.wait(5), "First command did not reach credential locks"
                    capture = observe_waiter(t.base.db, waiters)
                    second = pool.submit(reissue if role_first else withdraw)
                    wait_for_owned_block(t.base.db, holders[0], waiters)
                    waiter = waiters[-1]
                    with t.base.db.session() as observer:
                        witness = observer.execute(
                            text(
                                "SELECT pg_blocking_pids(pid),wait_event_type,query "
                                "FROM pg_stat_activity WHERE pid=:p"
                            ),
                            {"p": waiter},
                        ).one()
                    assert waiter != holders[0]
                    assert holders[0] in witness[0] and witness[1] == "Lock"
                    assert "iam_installation" in witness[2]
                finally:
                    release.set()
                    if capture is not None:
                        sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
                a, b = first.result(timeout=10), second.result(timeout=10)
        role_result, setup_result = (a, b) if role_first else (b, a)
        assert role_result.status_code == (200 if role_first else 409)
        assert setup_result.status_code == (409 if role_first else 201)
        with t.base.db.session() as reader:
            assert reader.execute(
                text("SELECT granted FROM iam_trainer_role_grants")
            ).scalar_one() is (not role_first)
            assert reader.execute(
                text("SELECT count(*) FROM iam_trainer_role_operations")
            ).scalar_one() == int(role_first)
            assert reader.execute(
                text("SELECT count(*) FROM audit_trainer_role_events")
            ).scalar_one() == int(role_first)
            assert reader.execute(
                text("SELECT count(*) FROM iam_trainer_account_operations")
            ).scalar_one() == (1 if role_first else 2)
            assert reader.execute(
                text("SELECT count(*) FROM iam_trainer_setup_credentials WHERE NOT consumed")
            ).scalar_one() == int(not role_first)
        old_sources = [old]
        if not role_first:
            old_sources.append(source(setup_result))
            assert change(t, body(t, False)).status_code == 200
        assert change(t, body(t, True)).status_code == 200
        for token in old_sources:
            assert t.complete(token).status_code == 400
        assert t.complete(source(t.reissue())).status_code == 204
        assert t.signin().status_code == 204
        assert other.get("/api/v1/auth/me").status_code == 200
        prefix = "causal_lock_" + ("role_first" if role_first else "reissue_first")
        record_testsuite_property(prefix + "_holder_pid", holders[0])
        record_testsuite_property(prefix + "_waiter_pid", waiter)
        record_testsuite_property(prefix + "_observed_wait", "installation_lock_after_credentials")
