# ruff: noqa: F811
"""Observed PostgreSQL role serialization and durable COMMIT-ACK replay."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import event as sa_event
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body, change, state
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerRoleEvent
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("same", [True, False])
def test_role_commands_observed_block_and_single_transition(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    same: bool,
) -> None:
    t = trainer
    source(t.issue())
    request = body(t, False)
    reached, release = Event(), Event()
    holders: list[int] = []
    original = Audit.append_trainer_role

    def pause(self: Audit, event: TrainerRoleEvent) -> None:
        original(self, event)
        holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        reached.set()
        assert release.wait(10)

    with closing(branch_actor(t.base, mfa[2])) as other:
        nonce_a, nonce_b = csrf(t.base.client), csrf(other)
        alternate = request if same else {**request, "operation_id": str(uuid4())}
        path = "/admin/trainers/" + t.trainer + "/role"
        monkeypatch.setattr(Audit, "append_trainer_role", pause)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(call, t.base.client, path, nonce_a, request)
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
            assert first.result(timeout=10).status_code == 200
            assert second.result(timeout=10).status_code == (200 if same else 409)
        assert state(t)["role_version"] == 2
        with t.base.db.session() as s:
            assert (
                s.execute(text("SELECT count(*) FROM audit_trainer_role_events")).scalar_one() == 1
            )


def test_role_commit_ack_replay_preserves_later_login(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    request = body(t, False)
    original = Session.commit
    fired = False

    def commit(self: Session) -> None:
        nonlocal fired
        should_fail = not fired and bool(
            self.execute(
                text(
                    "SELECT EXISTS(SELECT 1 FROM iam_trainer_role_operations WHERE operation_id=:i)"
                ),
                {"i": request["operation_id"]},
            ).scalar_one()
        )
        original(self)
        if should_fail:
            fired = True
            raise OperationalError("synthetic committed ACK loss", {}, RuntimeError())

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", commit)
        assert change(t, request).status_code == 503
    assert fired and state(t)["granted"] is False
    assert t.recipient.get("/api/v1/auth/me").status_code == 401
    assert change(t, body(t, True)).status_code == 200
    assert t.signin().status_code == 204
    assert change(t, request).status_code == 200
    assert t.recipient.get("/api/v1/auth/me").status_code == 200


def test_prepared_password_login_cannot_cross_role_epoch(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.iam.infrastructure import IAM

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    original = IAM.verify_login
    changed = False

    def prepare(self: IAM, *args: Any, **kwargs: Any) -> Any:
        nonlocal changed
        proof = original(self, *args, **kwargs)
        if not changed:
            changed = True
            assert change(t, body(t, False)).status_code == 200
            assert change(t, body(t, True)).status_code == 200
        return proof

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "verify_login", prepare)
        assert t.signin().status_code == 401
    assert changed
    assert t.signin().status_code == 204


@pytest.mark.parametrize("same_trainer", [False, True])
def test_first_binding_competition_observed_one_immutable_pair(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    same_trainer: bool,
) -> None:
    from fastapi.testclient import TestClient

    from tests.test_iam import ORIGIN
    from tests.test_iam_mfa_management_races import provision
    from tests.test_iam_trainer_roles_security import link

    t = trainer
    with (
        closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target,
        closing(branch_actor(t.base, mfa[2])) as other,
    ):
        ident, _ = provision(t.base.client, target, mfa[2])
        first_request = link(t, ident, "second.master")
        if same_trainer:
            master = t.base.client.get("/api/v1/auth/me").json()["account_id"]
            second_request = link(t, master, "master.test")
            second_trainer = t.trainer
        else:
            created = t.base.send(t.base.body()).json()["trainer"]
            second_trainer = created["id"]
            second_request = {
                **first_request,
                "operation_id": str(uuid4()),
                "expected_trainer_version": created["version"],
            }
        nonce_a, nonce_b = csrf(t.base.client), csrf(other)
        reached, release = Event(), Event()
        holders: list[int] = []
        original = Audit.append_trainer_role

        def pause(self: Audit, event: TrainerRoleEvent) -> None:
            original(self, event)
            holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            reached.set()
            assert release.wait(10)

        monkeypatch.setattr(Audit, "append_trainer_role", pause)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                call,
                t.base.client,
                "/admin/trainers/" + t.trainer + "/role",
                nonce_a,
                first_request,
            )
            capture = None
            try:
                assert reached.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(
                    call,
                    other,
                    "/admin/trainers/" + second_trainer + "/role",
                    nonce_b,
                    second_request,
                )
                wait_for_owned_block(t.base.db, holders[0], waiters)
                assert not second.done()
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            assert first.result(timeout=10).status_code == 200
            assert second.result(timeout=10).status_code == 409
        with t.base.db.session() as s:
            rows = s.execute(text("SELECT account_id,trainer_id FROM iam_trainer_bindings")).all()
            assert [(str(r.account_id), str(r.trainer_id)) for r in rows] == [(ident, t.trainer)]
            assert (
                s.execute(text("SELECT count(*) FROM iam_trainer_role_operations")).scalar_one()
                == 1
            )
            assert (
                s.execute(text("SELECT count(*) FROM audit_trainer_role_events")).scalar_one() == 1
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_accounts WHERE trainer_role_epoch>0")
                ).scalar_one()
                == 1
            )
        assert other.get("/api/v1/auth/me").status_code == 200
        assert t.base.client.get("/api/v1/auth/me").status_code == 200


def test_downgrade_waits_for_actual_role_change_and_preserves_committed_history(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess
    import sys
    import time

    from tests.conftest import qa_register_process, qa_stop_process
    from tests.test_iam import child_env

    t = trainer
    source(t.issue())
    request = body(t, False)
    reached, release = Event(), Event()
    holder: list[int] = []
    original = Audit.append_trainer_role

    def pause(self: Audit, event: TrainerRoleEvent) -> None:
        original(self, event)
        holder.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        reached.set()
        assert release.wait(15)

    monkeypatch.setattr(Audit, "append_trainer_role", pause)
    appname = "roles-downgrade-" + uuid4().hex
    env = child_env(mfa[0])
    env["PGAPPNAME"] = appname
    with ThreadPoolExecutor(max_workers=1) as pool:
        changing = pool.submit(change, t, request)
        process = None
        try:
            assert reached.wait(5)
            process = subprocess.Popen(
                [sys.executable, "-m", "alembic", "downgrade", "0011_iam_trainer_login"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            qa_register_process(process)
            waiting = False
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and process.poll() is None:
                with t.base.db.session() as reader:
                    waiting = bool(
                        reader.execute(
                            text(
                                "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
                                "WHERE datname=current_database() AND application_name=:n "
                                "AND wait_event_type='Lock' AND pid<>:h "
                                "AND :h=ANY(pg_blocking_pids(pid)))"
                            ),
                            {"n": appname, "h": holder[0]},
                        ).scalar_one()
                    )
                if waiting:
                    break
                time.sleep(0.02)
            assert waiting
            release.set()
            assert changing.result(timeout=10).status_code == 200
            process.communicate(timeout=10)
            assert process.returncode != 0
            with t.base.db.session() as reader:
                assert (
                    reader.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                    == "0012_iam_trainer_roles"
                )
                assert (
                    reader.execute(
                        text("SELECT count(*) FROM audit_trainer_role_events")
                    ).scalar_one()
                    == 1
                )
                assert (
                    reader.execute(
                        text("SELECT count(*) FROM iam_trainer_role_operations")
                    ).scalar_one()
                    == 1
                )
                assert (
                    reader.execute(text("SELECT granted FROM iam_trainer_role_grants")).scalar_one()
                    is False
                )
                assert (
                    reader.execute(
                        text("SELECT role_version FROM iam_trainer_role_grants")
                    ).scalar_one()
                    == 2
                )
            assert state(t)["granted"] is False
        finally:
            release.set()
            if process is not None:
                qa_stop_process(process)
