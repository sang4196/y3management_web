"""Original actor deadlines must survive required audit work and self credential changes."""

from contextlib import closing
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import activate, call, link_token, login_password, provision
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_master_management import command, state
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def expire_soon(db: Database, actor: str, clock: str) -> None:
    with db.session() as s:
        if clock == "idle":
            s.execute(
                text(
                    "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',"
                    "last_activity=clock_timestamp()-interval '30 minutes'+interval '3 seconds' "
                    "WHERE account_id=:a AND NOT revoked"
                ),
                {"a": actor},
            )
        else:
            s.execute(
                text(
                    "WITH p AS (UPDATE iam_security_states "
                    "SET expires_at=clock_timestamp()+interval '3 seconds' "
                    "WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a AND NOT revoked) "
                    "RETURNING id,expires_at) UPDATE iam_sessions s SET expires_at=p.expires_at,"
                    "created_at=p.expires_at-interval '8 hours' FROM p WHERE s.id=p.id"
                ),
                {"a": actor},
            )
        s.commit()


OPERATIONS = [
    "c3",
    "c3_dual",
    "c3_branch",
    "branch",
    "master",
    "master_restore",
    "master_id",
    "issue",
    "reissue",
    "change",
    "scope",
    "restore",
    "login_id",
    "issue_master",
    "reissue_master",
]


@dataclass(repr=False)
class Request:
    client: TestClient
    method: str
    path: str
    body: dict[str, Any]
    success: int
    nonce: str
    actor: str
    login: str

    def send(self) -> Any:
        return self.client.request(
            self.method,
            "/api/v1" + self.path,
            json=self.body,
            headers={"Origin": ORIGIN, "X-CSRF-Token": self.nonce},
        )


def prepare(
    actor: TestClient, target: TestClient, db: Database, password: str, operation: str
) -> Request:
    ident = provision(actor, target, password)
    version = state(actor, ident)["version"]
    client, login = actor, "master.test"
    method, path, body, success = "POST", "", {}, 200
    if operation in (
        "c3_dual",
        "c3_branch",
        "issue",
        "reissue",
        "change",
        "pending_disable",
        "scope",
        "restore",
        "login_id",
    ):
        branch = call(
            actor, "/admin/branches", csrf(actor), {"code": "A", "name": "가상 A"}
        ).json()["id"]
        if operation == "c3_dual":
            from tests.test_iam_trainer import TrainerScene
            from tests.test_iam_trainer_roles import change
            from tests.test_iam_trainer_roles_security import link
            from tests.test_workforce import Scene

            base = Scene(target, db, branch)
            trainer_id = base.send(base.body()).json()["trainer"]["id"]
            trainer = TrainerScene(base, trainer_id, actor, password, "master.test")
            actor_id = actor.get("/api/v1/auth/me").json()["account_id"]
            assert change(trainer, link(trainer, actor_id, "master.test")).status_code == 200
            login_password(actor, password)
        elif operation == "issue":
            path, body, success = (
                "/admin/accounts",
                {"login_id": "clock.branch", "branch_id": branch},
                201,
            )
        else:
            issued = call(
                actor,
                "/admin/accounts",
                csrf(actor),
                {"login_id": "clock.branch", "branch_id": branch},
            )
            assert issued.status_code == 201
            ident = issued.json()["account_id"]
            version = 1
            if operation not in ("reissue", "pending_disable"):
                target.cookies.clear()
                activate(target, link_token(issued.json()["setup_link"]), password)
                login_password(target, password, "clock.branch")
                version = 2
            if operation == "c3_branch":
                client, login = target, "clock.branch"
            elif operation == "reissue":
                path, body, success = (
                    f"/admin/accounts/{ident}/activation",
                    {"expected_version": version},
                    201,
                )
            else:
                path, body, method = (
                    f"/admin/accounts/{ident}/status",
                    {"expected_version": version, "status": "DISABLED"},
                    "PATCH",
                )
                if operation == "scope":
                    other = call(
                        actor, "/admin/branches", csrf(actor), {"code": "B", "name": "가상 B"}
                    ).json()["id"]
                    path, body = (
                        f"/admin/accounts/{ident}/access",
                        {"expected_version": version, "branch_id": other},
                    )
                elif operation == "login_id":
                    path, body = (
                        f"/admin/accounts/{ident}/login-id",
                        {"expected_version": version, "login_id": "clock.renamed"},
                    )
                elif operation == "restore":
                    assert (
                        actor.patch(
                            "/api/v1" + path,
                            json=body,
                            headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(actor)},
                        ).status_code
                        == 200
                    )
                    method, path, body = (
                        "POST",
                        f"/admin/accounts/{ident}/restore",
                        {"expected_version": version + 1},
                    )
    if operation.startswith("c3"):
        method, path, body, success = (
            "POST",
            "/auth/password",
            {"current_password": password, "new_password": password + " changed"},
            204,
        )
    elif operation == "branch":
        path, body, success = "/admin/branches", {"code": "CLOCK", "name": "가상 지점"}, 201
    elif operation.startswith("master"):
        method, path, body = (
            "PATCH",
            f"/admin/master-accounts/{ident}/status",
            {"expected_version": version, "status": "DISABLED"},
        )
        if operation == "master_restore":
            assert command(actor, ident, "status", version).status_code == 200
            method, path, body = (
                "POST",
                f"/admin/master-accounts/{ident}/restore",
                {"expected_version": version + 1},
            )
        elif operation == "master_id":
            path, body = (
                f"/admin/master-accounts/{ident}/login-id",
                {"expected_version": version, "login_id": "clock.renamed"},
            )
    elif operation in ("issue_master", "reissue_master"):
        path, body, success = "/admin/master-accounts", {"login_id": "pending.master"}, 201
        if operation == "reissue_master":
            pending = call(actor, path, csrf(actor), body)
            assert pending.status_code == 201
            path, body = (
                f"/admin/master-accounts/{pending.json()['account_id']}/activation",
                {"expected_version": 1},
            )
    actor_id = client.get("/api/v1/auth/me").json()["account_id"]
    nonce = csrf(client)
    return Request(client, method, path, body, success, nonce, actor_id, login)


def business_fingerprint(db: Database) -> str:
    # Only digest values leave the database; previously consumed GC rows are not authority.
    with db.session() as s:
        values = []
        for table in (
            "iam_accounts",
            "iam_login_ids",
            "iam_admin_grants",
            "iam_sessions",
            "audit_events",
            "organization_branches",
            "iam_trainer_bindings",
            "iam_trainer_role_grants",
        ):
            values.append(
                s.execute(
                    text(
                        f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                        f"ORDER BY row_to_json(t)::text),'')) FROM {table} t"
                    )
                ).scalar_one()
            )
        values.append(
            s.execute(
                text(
                    "SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                    "ORDER BY row_to_json(t)::text),'')) FROM iam_credentials t WHERE NOT consumed"
                )
            ).scalar_one()
        )
        return ":".join(values)


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("clock", ["idle", "absolute"])
def test_required_audit_crosses_original_actor_deadline(
    password_app: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    clock: str,
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, password)
        with closing(TestClient(actor.app, base_url=ORIGIN)) as target:
            request = prepare(actor, target, db, password, operation)
            expire_soon(db, request.actor, clock)
            before = business_fingerprint(db)
            original = Audit.append
            observed = []

            def delayed(adapter: Audit, event: Event) -> None:
                original(adapter, event)
                observed.append(True)
                adapter.s.execute(text("SELECT pg_sleep(1.6)"))
                adapter.s.execute(text("SELECT pg_sleep(1.6)"))

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", delayed)
                response = request.send()
            assert observed == [True]
            assert response.status_code == 401
            assert business_fingerprint(db) == before


@pytest.mark.parametrize("operation", OPERATIONS)
def test_success_uses_one_final_checked_clock(
    password_app: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    from datetime import datetime

    from sqlalchemy import event as sql_event

    from y3management.iam.infrastructure import IAM

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, password)
        with closing(TestClient(actor.app, base_url=ORIGIN)) as target:
            request = prepare(actor, target, db, password, operation)
            with closing(TestClient(actor.app, base_url=ORIGIN)) as twin:
                if operation.startswith("c3"):
                    login_password(twin, password, request.login)
                with db.session() as s:
                    sessions_before = s.execute(
                        text(
                            "SELECT id,last_activity FROM iam_sessions "
                            "WHERE account_id=:a ORDER BY id"
                        ),
                        {"a": request.actor},
                    ).all()
                audited = False
                checked: list[datetime] = []
                updates: list[str] = []
                original_audit, original_now = Audit.append, IAM.now

                def audit(adapter: Audit, value: Event) -> None:
                    nonlocal audited
                    original_audit(adapter, value)
                    audited = True

                def now(adapter: IAM) -> datetime:
                    value = original_now(adapter)
                    if audited:
                        checked.append(value)
                    return value

                def observe(
                    conn: Any, cursor: Any, statement: str, params: Any, context: Any, many: bool
                ) -> None:
                    if statement.startswith("UPDATE iam_sessions SET last_activity="):
                        updates.append(statement)
                        assert audited, "Actor activity changed before required audit"

                with monkeypatch.context() as patch:
                    patch.setattr(Audit, "append", audit)
                    patch.setattr(IAM, "now", now)
                    sql_event.listen(db.engine, "before_cursor_execute", observe)
                    try:
                        response = request.send()
                    finally:
                        sql_event.remove(db.engine, "before_cursor_execute", observe)
                assert response.status_code == request.success
                assert audited and len(checked) == 1
                assert len(updates) == (0 if operation.startswith("c3") else 1)
                with db.session() as s:
                    sessions = s.execute(
                        text(
                            "SELECT id,last_activity,revoked FROM iam_sessions "
                            "WHERE account_id=:a ORDER BY id"
                        ),
                        {"a": request.actor},
                    ).all()
                if operation.startswith("c3"):
                    assert [(r.id, r.last_activity) for r in sessions] == [
                        tuple(r) for r in sessions_before
                    ]
                    assert len(sessions) >= 2 and all(r.revoked for r in sessions)
                    assert request.client.get("/api/v1/auth/me").status_code == 401
                    assert twin.get("/api/v1/auth/me").status_code == 401
                    login_password(request.client, password + " changed", request.login)
                else:
                    assert any(r.last_activity == checked[0] for r in sessions)


@pytest.mark.parametrize("operation", ["login_id", "master_id"])
def test_login_id_noop_does_not_touch_or_audit(
    password_app: tuple[Settings, Database, str], operation: str
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, password)
        with closing(TestClient(actor.app, base_url=ORIGIN)) as target:
            request = prepare(actor, target, db, password, operation)
            request.body["login_id"] = (
                "clock.branch" if operation == "login_id" else "second.master"
            )
            before = business_fingerprint(db)
            assert request.send().status_code == 200
            assert business_fingerprint(db) == before


@pytest.mark.parametrize(
    "mutation",
    [
        "row_version=row_version+1",
        "security_version=security_version+1",
        "password_hash='unexpected-synthetic-hash'",
        "session_unrevoked",
    ],
)
def test_c3_final_check_rejects_unexpected_self_changes(
    password_app: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, password)
        with closing(TestClient(actor.app, base_url=ORIGIN)) as target:
            request = prepare(actor, target, db, password, "c3")
            before = business_fingerprint(db)
            original = Audit.append

            def alter(adapter: Audit, value: Event) -> None:
                original(adapter, value)
                if mutation == "session_unrevoked":
                    adapter.s.execute(
                        text("UPDATE iam_sessions SET revoked=false WHERE account_id=:a"),
                        {"a": request.actor},
                    )
                else:
                    adapter.s.execute(
                        text("UPDATE iam_accounts SET " + mutation + " WHERE id=:a"),
                        {"a": request.actor},
                    )

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", alter)
                assert request.send().status_code == 401
            assert business_fingerprint(db) == before


@pytest.mark.parametrize("operation", ["c3", "branch", "pending_disable"])
@pytest.mark.parametrize("clock", ["idle", "absolute"])
def test_independent_audit_lock_crosses_original_deadline(
    password_app: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    clock: str,
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event as ThreadEvent
    from time import monotonic

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, password)
        with closing(TestClient(actor.app, base_url=ORIGIN)) as target:
            request = prepare(actor, target, db, password, operation)
            expire_soon(db, request.actor, clock)
            before = business_fingerprint(db)
            with db.session() as s:
                deadline = s.execute(
                    text(
                        "SELECT least(last_activity+interval '30 minutes',expires_at) "
                        "FROM iam_sessions WHERE account_id=:a AND NOT revoked"
                    ),
                    {"a": request.actor},
                ).scalar_one()
            reached = ThreadEvent()
            waiters: list[int] = []
            original = Audit.append

            def append(adapter: Audit, event: Event) -> None:
                # Enter the real INSERT lock wait with <1 second left, below the
                # unchanged 2-second statement/lock timeout. No clock is mocked.
                while True:
                    now = adapter.s.execute(text("SELECT clock_timestamp()")).scalar_one()
                    remaining = (deadline - now).total_seconds()
                    if remaining <= 0.7:
                        assert remaining > 0
                        break
                    adapter.s.execute(text("SELECT pg_sleep(0.05)"))
                waiters.append(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
                reached.set()
                original(adapter, event)

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
                patch.setattr(Audit, "append", append)
                with db.session() as holder:
                    holder.execute(text("LOCK TABLE audit_events IN SHARE MODE"))
                    holder_pid = holder.execute(text("SELECT pg_backend_pid()")).scalar_one()
                    future = pool.submit(request.send)
                    observed_block = False
                    try:
                        assert reached.wait(5)
                        assert len(waiters) == 1 and waiters[0] != holder_pid
                        limit = monotonic() + 1.5
                        while monotonic() < limit:
                            blocked, now = holder.execute(
                                text("SELECT :h=ANY(pg_blocking_pids(:w)),clock_timestamp()"),
                                {"h": holder_pid, "w": waiters[0]},
                            ).one()
                            if blocked:
                                if not observed_block:
                                    assert now < deadline
                                observed_block = True
                            if now >= deadline:
                                assert blocked and observed_block and not future.done()
                                break
                            holder.execute(text("SELECT pg_sleep(0.02)"))
                        else:
                            pytest.fail("Original deadline not crossed during owned audit lock")
                    finally:
                        holder.rollback()
                assert observed_block
                assert future.result(timeout=5).status_code == 401
            assert business_fingerprint(db) == before
