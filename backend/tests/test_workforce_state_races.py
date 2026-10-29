# ruff: noqa: F811
"""Causal W1 boundaries with real transactions, current facts and durable receipts."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event as sa_event
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import call, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import change as role_change
from tests.test_iam_trainer_roles_security import link
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
from tests.test_workforce_state import change, request
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerStateEvent
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.infrastructure import IAM

pytestmark = pytest.mark.postgres


def test_admin_self_state_preserves_current_session(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str]
) -> None:
    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident, key = provision(t.base.client, target, mfa[2])
        assert role_change(t, link(t, ident, "second.master")).status_code == 200
        target.cookies.clear()
        login_mfa(target, mfa[2], key, "second.master")
        cookie = target.cookies.get("__Host-y3-auth")
        for active in (False, True):
            payload = request(t, active)
            r = call(target, "/admin/trainers/" + t.trainer + "/state", csrf(target), payload)
            assert r.status_code == 200
            me = target.get("/api/v1/auth/me")
            assert me.status_code == 200 and me.json()["roles"][0]["role"] == "ADMIN"
            assert len(me.json()["roles"]) == (2 if active else 1)
            assert target.cookies.get("__Host-y3-auth") == cookie


@pytest.mark.parametrize("reactivate", [False, True])
def test_pending_login_linearizes_current_active(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, reactivate: bool
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    original = IAM.verify_login
    reached, release = Event(), Event()

    def paused(self: IAM, *args: Any, **kwargs: Any) -> Any:
        proof = original(self, *args, **kwargs)
        reached.set()
        assert release.wait(15)
        return proof

    monkeypatch.setattr(IAM, "verify_login", paused)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(t.signin)
        try:
            assert reached.wait(5)
            assert change(t, request(t, False)).status_code == 200
            if reactivate:
                assert change(t, request(t, True)).status_code == 200
        finally:
            release.set()
        assert pending.result(timeout=10).status_code == (204 if reactivate else 401)


def test_ack_loss_receipt_does_not_revoke_new_session(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    payload = request(t, False)
    original = Session.commit
    fired = False

    def commit(self: Session) -> None:
        nonlocal fired
        fail = not fired and bool(
            self.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM "
                    "workforce_trainer_state_operations WHERE operation_id=:i)"
                ),
                {"i": payload["operation_id"]},
            ).scalar_one()
        )
        original(self)
        if fail:
            fired = True
            raise OperationalError("synthetic committed ACK loss", {}, RuntimeError())

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", commit)
        assert change(t, payload).status_code == 503
    assert fired
    assert change(t, request(t, True)).status_code == 200
    assert t.signin().status_code == 204
    assert change(t, payload).status_code == 200
    r = t.base.client.get("/api/v1/admin/trainer-state-operations/" + payload["operation_id"])
    assert r.status_code == 200 and r.json()["committed_active"] is False
    assert r.json()["current_state"]["active"] is True
    assert t.recipient.get("/api/v1/auth/me").status_code == 200


@pytest.mark.parametrize("same", [True, False])
def test_commands_observed_block_then_replay_or_conflict(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    same: bool,
) -> None:
    t = trainer
    payload = request(t, False)
    reached, release = Event(), Event()
    holders = []
    original = Audit.append_trainer_state

    def pause(self: Audit, event: TrainerStateEvent) -> None:
        original(self, event)
        holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        reached.set()
        assert release.wait(15)

    with closing(branch_actor(t.base, mfa[2])) as other:
        nonce_a, nonce_b = csrf(t.base.client), csrf(other)
        other_payload = payload if same else {**payload, "operation_id": str(uuid4())}
        monkeypatch.setattr(Audit, "append_trainer_state", pause)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                call, t.base.client, "/admin/trainers/" + t.trainer + "/state", nonce_a, payload
            )
            capture = None
            try:
                assert reached.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(
                    call, other, "/admin/trainers/" + t.trainer + "/state", nonce_b, other_payload
                )
                wait_for_owned_block(t.base.db, holders[0], waiters)
                assert not second.done()
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            assert first.result(timeout=10).status_code == 200
            assert second.result(timeout=10).status_code == (200 if same else 409)
        # Current Home changed: previous BA cannot access old receipt.
        with t.base.db.session() as s:
            assert (
                s.execute(text("SELECT count(*) FROM audit_trainer_state_events")).scalar_one() == 1
            )
        new = call(
            t.base.client, "/admin/branches", csrf(t.base.client), {"code": "NEXT", "name": "가상"}
        ).json()
        with t.base.db.session() as s:
            s.execute(
                text(
                    "UPDATE workforce_trainers SET home_branch_id=:b,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"b": new["id"], "i": t.trainer},
            )
            s.commit()
        assert (
            other.get(
                "/api/v1/admin/trainer-state-operations/" + payload["operation_id"]
            ).status_code
            == 404
        )
        assert (
            call(other, "/admin/trainers/" + t.trainer + "/state", csrf(other), payload).status_code
            == 404
        )


@pytest.mark.parametrize("absolute", [False, True])
def test_state_final_actor_read_crosses_original_deadline(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, absolute: bool
) -> None:
    from y3management.iam.public import Authentication
    from y3management.iam.roles import TrainerRoles

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    payload = request(t, False)
    nonce = csrf(t.base.client)
    actor = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    with t.base.db.session() as s:
        session_query = text(
            "SELECT id,revoked FROM iam_sessions WHERE account_id="
            "(SELECT account_id FROM iam_trainer_bindings WHERE trainer_id=:t) ORDER BY id"
        )
        target_sessions = s.execute(session_query, {"t": t.trainer}).all()
        assert target_sessions and all(not row.revoked for row in target_sessions)
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
                text(
                    "UPDATE iam_sessions SET "
                    "created_at=clock_timestamp()-interval '31 minutes',"
                    "last_activity=clock_timestamp()-interval '29 minutes 58 seconds' "
                    "WHERE account_id=:a"
                ),
                {"a": actor},
            )
        s.commit()
    original = TrainerRoles.stable_actor
    observations: list[tuple[bool, bool]] = []
    reads = 0

    def delayed(self: TrainerRoles, authentication: Authentication) -> bytes:
        nonlocal reads
        reads += 1
        value = original(self, authentication)
        if reads == 2:
            query = text(
                "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
                "expires_at>clock_timestamp() FROM iam_sessions WHERE id=:i"
            )
            row = self.s.execute(query, {"i": authentication.session_id}).one()
            observations.append((bool(row[0]), bool(row[1])))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            row = self.s.execute(query, {"i": authentication.session_id}).one()
            observations.append((bool(row[0]), bool(row[1])))
        return value

    monkeypatch.setattr(TrainerRoles, "stable_actor", delayed)
    response = call(t.base.client, "/admin/trainers/" + t.trainer + "/state", nonce, payload)
    assert response.status_code == 401
    assert observations[0] == (True, True)
    assert observations[1][1 if absolute else 0] is False
    with t.base.db.session() as s:
        assert s.execute(text("SELECT active FROM workforce_trainers")).scalar_one()
        assert (
            s.execute(text("SELECT count(*) FROM workforce_trainer_state_operations")).scalar_one()
            == 0
        )
        assert s.execute(text("SELECT count(*) FROM audit_trainer_state_events")).scalar_one() == 0
        assert s.execute(session_query, {"t": t.trainer}).all() == target_sessions

    assert t.recipient.get("/api/v1/auth/me").status_code == 200
