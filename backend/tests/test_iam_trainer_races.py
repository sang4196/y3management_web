# ruff: noqa: F811
"""Independent actors/connections with observed PostgreSQL blocking edges."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from uuid import uuid4

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy import text

from tests.test_iam import csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, counts, source, trainer  # noqa: F401
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerIdentityEvent
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("same", [True, False])
def test_same_operation_actual_two_actor_block(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    same: bool,
) -> None:
    t = trainer
    reached, release = Event(), Event()
    holders: list[int] = []
    original = Audit.append_trainer_identity

    def pause(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == "issue":
            holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            reached.set()
            assert release.wait(10)

    with closing(branch_actor(t.base, mfa[2])) as other:
        nonce_a, nonce_b = csrf(t.base.client), csrf(other)
        monkeypatch.setattr(Audit, "append_trainer_identity", pause)
        payload = {"operation_id": str(uuid4()), "login_id": t.login}
        alternate = payload if same else {**payload, "login_id": t.login + "_other"}
        path = "/admin/trainers/" + t.trainer + "/login-account"
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(call, t.base.client, path, nonce_a, payload)
            capture = None
            try:
                assert reached.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(call, other, path, nonce_b, alternate)
                wait_for_owned_block(t.base.db, holders[0], waiters)
                assert not second.done()
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            a, b = first.result(timeout=10), second.result(timeout=10)
        assert a.status_code == 201
        assert b.status_code == (200 if same else 409)
        assert "setup_link" not in b.json()
        assert counts(t) == (1, 1, 1, 1)


@pytest.mark.parametrize("setup_first", [True, False])
def test_setup_against_actual_trainer_deactivation(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    setup_first: bool,
) -> None:
    t = trainer
    token = source(t.issue())
    nonce = csrf(t.recipient)
    reached, release = Event(), Event()
    holders: list[int] = []
    original = Audit.append_trainer_identity

    def pause(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == "setup_complete":
            holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            reached.set()
            assert release.wait(10)

    def deactivate() -> int:
        with t.base.db.session() as s:
            pid = s.execute(text("SELECT pg_backend_pid()")).scalar_one()
            s.execute(
                text(
                    "UPDATE workforce_trainers SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": t.trainer},
            )
            if not setup_first:
                holders.append(pid)
                reached.set()
                assert release.wait(10)
            s.commit()
        return 204

    def complete() -> int:
        return int(
            call(
                t.recipient,
                "/auth/trainer-credentials/complete",
                nonce,
                {"setup_token": token, "new_password": t.password},
            ).status_code
        )

    if setup_first:
        monkeypatch.setattr(Audit, "append_trainer_identity", pause)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(complete if setup_first else deactivate)
        capture = None
        try:
            assert reached.wait(5)
            waiters: list[int] = []
            capture = observe_waiter(t.base.db, waiters)
            second = pool.submit(deactivate if setup_first else complete)
            wait_for_owned_block(t.base.db, holders[0], waiters)
            assert not second.done()
        finally:
            release.set()
            if capture is not None:
                sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
        a, b = first.result(timeout=10), second.result(timeout=10)
    assert (a if setup_first else b) == (204 if setup_first else 400)
    assert t.state()["state"] == ("ACTIVE" if setup_first else "PENDING_SETUP")
    if not setup_first:
        t.active(True)
        assert t.complete(token).status_code == 204


def test_password_change_precedes_waiting_old_password_login(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi.testclient import TestClient

    from tests.test_iam import ORIGIN

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    reached, release = Event(), Event()
    holders: list[int] = []
    original = Audit.append_trainer_identity

    def pause(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == "password_change":
            holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            reached.set()
            assert release.wait(10)

    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as other:
        nonce_a, nonce_b = csrf(t.recipient), csrf(other)
        monkeypatch.setattr(Audit, "append_trainer_identity", pause)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                call,
                t.recipient,
                "/auth/password",
                nonce_a,
                {"current_password": t.password, "new_password": t.password + " changed"},
            )
            capture = None
            try:
                assert reached.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(
                    call,
                    other,
                    "/auth/login",
                    nonce_b,
                    {"login_id": t.login, "password": t.password},
                )
                wait_for_owned_block(t.base.db, holders[0], waiters)
                assert not second.done()
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            assert first.result(timeout=10).status_code == 204
            assert second.result(timeout=10).status_code in (401, 503)
        assert other.get("/api/v1/auth/me").status_code == 401
        assert t.recipient.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize(
    "first_kind,second_kind,expected",
    [
        ("setup_complete", "reissue", 409),
        ("reissue", "setup_complete", 400),
        ("setup_complete", "setup_complete", 400),
    ],
)
def test_reissue_and_consumption_serialize_on_actual_connection(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    first_kind: str,
    second_kind: str,
    expected: int,
) -> None:
    from fastapi.testclient import TestClient

    from tests.test_iam import ORIGIN

    t = trainer
    token = source(t.issue())
    reached, release = Event(), Event()
    holders: list[int] = []
    original = Audit.append_trainer_identity

    def pause(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == first_kind and not holders:
            holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            reached.set()
            assert release.wait(10)

    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as other:
        na, nb, nm = csrf(t.recipient), csrf(other), csrf(t.base.client)
        monkeypatch.setattr(Audit, "append_trainer_identity", pause)

        def execute(kind: str, second: bool) -> int:
            if kind == "reissue":
                return int(
                    call(
                        t.base.client,
                        "/admin/trainers/" + t.trainer + "/initial-setup",
                        nm,
                        {"operation_id": str(uuid4()), "expected_account_version": 1},
                    ).status_code
                )
            return int(
                call(
                    other if second else t.recipient,
                    "/auth/trainer-credentials/complete",
                    nb if second else na,
                    {"setup_token": token, "new_password": t.password},
                ).status_code
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(execute, first_kind, False)
            capture = None
            try:
                assert reached.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(execute, second_kind, True)
                wait_for_owned_block(t.base.db, holders[0], waiters)
                assert not second.done()
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            assert first.result(timeout=10) == (201 if first_kind == "reissue" else 204)
            assert second.result(timeout=10) == expected
        assert t.state()["state"] == ("PENDING_SETUP" if first_kind == "reissue" else "ACTIVE")
