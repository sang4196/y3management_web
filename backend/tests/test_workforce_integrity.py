# ruff: noqa: F811
"""Boundary constraints, late DB-time checks, races and migration history."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from tests.test_iam import ORIGIN, child_env, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_workforce import Scene, activity, counts, scene  # noqa: F401
from y3management.audit.infrastructure import Audit
from y3management.audit.public import InitialCompensationSet
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def branch_actor(scene: Scene, password: str) -> TestClient:
    r = call(
        scene.client,
        "/admin/accounts",
        csrf(scene.client),
        {"login_id": "workforce.branch", "branch_id": scene.branch},
    )
    assert r.status_code == 201
    client = TestClient(scene.client.app, base_url=ORIGIN)
    key = Authenticator()
    enroll(client, r.json()["setup_link"].split("#token=")[1], key, password)
    login_mfa(client, password, key, "workforce.branch")
    return client


@pytest.mark.parametrize("same", [True, False])
def test_distinct_actors_same_operation(
    scene: Scene, mfa: tuple[Settings, Database, str, str], same: bool
) -> None:
    with closing(branch_actor(scene, mfa[2])) as other:
        body = scene.body()
        alternate = body if same else {**body, "name": "다른 명령"}
        barrier = Barrier(2)
        nonce_a, nonce_b = csrf(scene.client), csrf(other)
        before = dict(activity(scene.db))

        def send(client: TestClient, nonce: str, payload: dict[str, Any]) -> int:
            barrier.wait(timeout=5)
            return int(call(client, "/admin/trainers", nonce, payload).status_code)

        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(send, scene.client, nonce_a, body)
            b = pool.submit(send, other, nonce_b, alternate)
            statuses = [a.result(timeout=10), b.result(timeout=10)]
        assert sorted(statuses) == ([200, 201] if same else [201, 409])
        assert counts(scene.db) == (1, 1, 1, 2)
        after = dict(activity(scene.db))
        assert sum(after[k] > v for k, v in before.items()) == (2 if same else 1)


def test_branch_scope_and_revocation(
    scene: Scene, mfa: tuple[Settings, Database, str, str]
) -> None:
    with closing(branch_actor(scene, mfa[2])) as other:
        body = scene.body()
        assert scene.send(body).status_code == 201
        assert call(other, "/admin/trainers", csrf(other), body).status_code == 200
        foreign = call(
            scene.client,
            "/admin/branches",
            csrf(scene.client),
            {"code": "OTHER", "name": "다른지점"},
        ).json()["id"]
        bad = {**scene.body(), "home_branch_id": foreign}
        assert call(other, "/admin/trainers", csrf(other), bad).status_code == 404
        with scene.db.session() as s:
            s.execute(
                text("UPDATE organization_branches SET active=false,row_version=2 WHERE id=:i"),
                {"i": scene.branch},
            )
            s.commit()
        assert other.get("/api/v1/admin/trainers").json()["total"] == 1
        assert call(other, "/admin/trainers", csrf(other), body).status_code == 200
        with scene.db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_accounts SET state='DISABLED',security_version=security_version+1 "
                    "WHERE login_id='workforce.branch'"
                )
            )
            s.commit()
        assert other.get("/api/v1/admin/trainers").status_code == 401
        assert counts(scene.db) == (1, 1, 1, 2)


def test_late_idle_check_not_rescued_by_touch(
    scene: Scene, monkeypatch: pytest.MonkeyPatch
) -> None:
    nonce = csrf(scene.client)
    with scene.db.session() as s:
        s.execute(
            text(
                "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',"
                "last_activity=clock_timestamp()-interval '29 minutes 58.5 seconds'"
            )
        )
        s.commit()
    observed: dict[str, bool] = {}
    original = Audit.append_initial_compensation

    def delayed(self: Audit, event: InitialCompensationSet) -> None:
        original(self, event)
        late_audit_proof(self, False, observed)

    monkeypatch.setattr(Audit, "append_initial_compensation", delayed)
    before = activity(scene.db)
    assert call(scene.client, "/admin/trainers", nonce, scene.body()).status_code == 401
    assert observed == {"reached": True, "writes": True, "only_selected_deadline_expired": True}
    assert activity(scene.db) == before and counts(scene.db) == (0, 0, 0, 0)


def test_database_constraints(scene: Scene) -> None:
    assert scene.send(scene.body()).status_code == 201
    for column, value in [
        ("fixed_amount_won", "NaN"),
        ("base_salary_won", "Infinity"),
        ("base_salary_won", "-Infinity"),
        ("fixed_amount_won", "1.5"),
        ("fixed_amount_won", "-1"),
    ]:
        with scene.db.session() as s:
            with pytest.raises(IntegrityError):
                s.execute(
                    text("UPDATE workforce_trainers SET " + column + "=CAST(:v AS numeric)"),
                    {"v": value},
                )
            s.rollback()
    with scene.db.session() as s:
        with pytest.raises(IntegrityError):
            s.execute(text("UPDATE workforce_trainers SET phone=NULL"))
        s.rollback()
    assert counts(scene.db) == (1, 1, 1, 2)


def test_commit_ack_loss_replay(scene: Scene, monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy.orm import Session

    body = scene.body()
    original = Session.commit
    fired = False

    def uncertain(self: Session) -> None:
        nonlocal fired
        has = self.execute(
            text("SELECT count(*) FROM workforce_registration_operations")
        ).scalar_one()
        original(self)
        if has and not fired:
            fired = True
            raise OperationalError("commit", {}, Exception("synthetic ack loss"))

    monkeypatch.setattr(Session, "commit", uncertain)
    r = scene.send(body)
    assert r.status_code == 503 and r.json()["detail"] == "commit_outcome_unknown"
    assert (
        scene.client.get("/api/v1/admin/trainer-registrations/" + body["operation_id"]).status_code
        == 200
    )
    assert scene.send(body).status_code == 200 and counts(scene.db) == (1, 1, 1, 2)


def test_migration_roundtrip_and_information_guard(
    scene: Scene, mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    def migrate(revision: str) -> None:
        downgrade = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", revision],
            env=child_env(mfa[0]),
            capture_output=True,
            timeout=30,
        )
        if downgrade.returncode != 0:
            from tests.workforce_state_seed import assert_loss_guard

            assert_loss_guard(
                scene.db,
                [
                    "0013_workforce_trainer_state.py",
                    "0012_iam_trainer_roles.py",
                    "0011_iam_trainer_login.py",
                    "0010_workforce_initial_registration.py",
                ],
                "workforce history or branch facts must be preserved",
            )

    def current() -> str:
        with scene.db.session() as s:
            return str(s.execute(text("SELECT version_num FROM alembic_version")).scalar_one())

    migrate("0009_iam_emergency_handoff")
    assert current() == "0009_iam_emergency_handoff"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=child_env(mfa[0]),
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0 and current() == "0013_workforce_trainer_state"
    with scene.db.session() as s:
        s.execute(text("UPDATE organization_branches SET active=false,row_version=2"))
        s.commit()
    migrate("0009_iam_emergency_handoff")
    assert current() == "0013_workforce_trainer_state"
    with scene.db.session() as s:
        assert s.execute(text("SELECT active FROM organization_branches")).scalar_one() is False
        s.execute(text("UPDATE organization_branches SET active=true,row_version=1"))
        s.commit()
    from tests.test_iam_trainer_roles_storage import migrate as migration
    from tests.workforce_state_seed import register_legacy

    assert migration(mfa[0], "downgrade", "0012_iam_trainer_roles") == 0
    assert register_legacy(scene, mfa[0], tmp_path)["active"] is True
    assert migration(mfa[0], "upgrade", "head") == 0
    migrate("0009_iam_emergency_handoff")
    assert current() == "0013_workforce_trainer_state" and counts(scene.db) == (1, 1, 1, 2)


@pytest.mark.parametrize("registration_first", [True, False])
def test_branch_state_lock_order(
    scene: Scene, monkeypatch: pytest.MonkeyPatch, registration_first: bool
) -> None:
    """Independent connections prove both Branch update/registration orders."""
    from threading import Event

    reached, release = Event(), Event()
    holder: list[int] = []
    from sqlalchemy import event as sa_event

    body = scene.body()
    nonce = csrf(scene.client)
    original = Audit.append_initial_compensation

    def delayed(self: Audit, event: InitialCompensationSet) -> None:
        original(self, event)
        holder.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        reached.set()
        assert release.wait(5)

    if registration_first:
        monkeypatch.setattr(Audit, "append_initial_compensation", delayed)

    def deactivate() -> None:
        with scene.db.session() as s:
            s.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": scene.branch},
            )
            if not registration_first:
                holder.append(int(s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
                reached.set()
                assert release.wait(5)
            s.commit()

    def register() -> int:
        return int(call(scene.client, "/admin/trainers", nonce, body).status_code)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(register if registration_first else deactivate)
        capture = None
        try:
            assert reached.wait(5)
            waiters: list[int] = []
            capture = observe_waiter(scene.db, waiters)
            second = pool.submit(deactivate if registration_first else register)
            wait_for_owned_block(scene.db, holder[0], waiters)
            assert not second.done()
        finally:
            release.set()
            if capture is not None:
                sa_event.remove(scene.db.engine, "before_cursor_execute", capture)
        first_result = first.result(timeout=10)
        second_result = second.result(timeout=10)
    assert (first_result if registration_first else second_result) == (
        201 if registration_first else 409
    )
    assert counts(scene.db) == ((1, 1, 1, 2) if registration_first else (0, 0, 0, 0))


def wait_for_owned_block(db: Database, holder: int, waiters: list[int]) -> None:
    import time

    deadline = time.monotonic() + 1.5
    while time.monotonic() < deadline:
        if waiters:
            with db.session() as observer:
                blockers = observer.execute(
                    text("SELECT pg_blocking_pids(:p)"), {"p": waiters[-1]}
                ).scalar_one()
            if holder in blockers:
                return
        time.sleep(0.01)
    raise AssertionError("Owned second connection did not demonstrably block on first")


def observe_waiter(db: Database, waiters: list[int]) -> Any:
    from sqlalchemy import event
    from sqlalchemy.engine import Connection

    def capture(
        conn: Connection, cursor: Any, statement: str, parameters: Any, context: Any, many: bool
    ) -> None:
        if "pg_blocking_pids" not in statement:
            driver = conn.connection.driver_connection
            assert driver is not None
            waiters.append(driver.info.backend_pid)

    event.listen(db.engine, "before_cursor_execute", capture)
    return capture


def late_audit_proof(adapter: Audit, absolute: bool, observed: dict[str, bool]) -> None:
    observed["reached"] = True
    observed["writes"] = all(
        adapter.s.execute(text("SELECT count(*) FROM " + table)).scalar_one() == count
        for table, count in [
            ("workforce_trainers", 1),
            ("workforce_initial_snapshots", 1),
            ("workforce_registration_operations", 1),
            ("audit_workforce_initial_events", 2),
        ]
    )
    row = adapter.s.execute(
        text(
            "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
            "expires_at>clock_timestamp() FROM iam_sessions"
        )
    ).one()
    assert tuple(row) == (True, True)
    adapter.s.execute(text("SELECT pg_sleep(1.1)"))
    adapter.s.execute(text("SELECT pg_sleep(1.1)"))
    row = adapter.s.execute(
        text(
            "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
            "expires_at>clock_timestamp() FROM iam_sessions"
        )
    ).one()
    observed["only_selected_deadline_expired"] = tuple(row) == (
        (True, False) if absolute else (False, True)
    )
