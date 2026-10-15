"""S2a normal Branch Admin restoration through actual CLI/API and owned PostgreSQL."""

import concurrent.futures
import hmac
import secrets
import subprocess
import sys
import threading
import time
from collections.abc import Iterable, Iterator, Sequence
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import event as sql_event
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, SyntheticSecret, child_env, csrf, iam, login  # noqa: F401
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres

_FINGERPRINT_KEY = secrets.token_bytes(32)


def fingerprint_rows(rows: Iterable[Sequence[object]]) -> str:
    """Compare every ordered field without keeping sensitive Rows in assertion operands."""
    digest = hmac.new(_FINGERPRINT_KEY, digestmod="sha256")
    for row in rows:
        encoded = repr(tuple(row)).encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def secret_csrf(
    service: Service, auth: str | None = None
) -> tuple[SyntheticSecret, SyntheticSecret | None]:
    nonce, preparation = service.csrf(auth, None)
    return (
        SyntheticSecret(nonce),
        SyntheticSecret(preparation) if preparation is not None else None,
    )


@pytest.fixture
def restored_subject(
    iam: tuple[Settings, Database, str],  # noqa: F811
) -> Iterator[tuple[Settings, Database, TestClient, Service, str, UUID, str, list[str]]]:
    settings, db, initial_password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        nonce = SyntheticSecret(login(master, "master.test", initial_password))
        headers = {"Origin": ORIGIN, "X-CSRF-Token": nonce}
        branch = master.post(
            "/api/v1/admin/branches", json={"code": "A", "name": "A"}, headers=headers
        ).json()["id"]
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "restore.test", "branch_id": branch},
            headers=headers,
        ).json()
        issued["setup_link"] = SyntheticSecret(issued["setup_link"])
        ident = UUID(issued["account_id"])
        password = SyntheticSecret("정상 차단 해제 검증 " + secrets.token_urlsafe(24))
        service: Service = app.state.iam_service
        n, pre = secret_csrf(service)
        service.complete(
            SyntheticSecret(urlsplit(issued["setup_link"]).fragment[6:]), password, pre, n
        )
        cookies: list[str] = []
        for _ in range(2):
            n, pre = secret_csrf(service)
            cookies.append(SyntheticSecret(service.login("restore.test", password, pre, n, None)))
        response = master.patch(
            f"/api/v1/admin/accounts/{ident}/status",
            json={"expected_version": 2, "status": "DISABLED"},
            headers=headers,
        )
        assert response.status_code == 200 and response.json()["version"] == 3
        yield settings, db, master, service, nonce, ident, password, cookies


def test_restore_real_http_existing_password_scope_and_old_sessions(
    restored_subject: tuple[Settings, Database, TestClient, Service, str, UUID, str, list[str]],
) -> None:
    _, db, master, service, nonce, ident, password, cookies = restored_subject
    path = f"/api/v1/admin/accounts/{ident}/restore"
    headers = {"Origin": ORIGIN, "X-CSRF-Token": nonce}
    with db.session() as s:
        before = fingerprint_rows(
            s.execute(
                text("SELECT password_hash,login_id FROM iam_accounts WHERE id=:id"), {"id": ident}
            ).all()
        )
    assert (
        master.post(path, json={"expected_version": 3}, headers={"Origin": ORIGIN}).status_code
        == 403
    )
    assert master.post(path, json={"expected_version": 2}, headers=headers).status_code == 409
    assert (
        master.post(
            path, json={"expected_version": 3, "role": "MASTER"}, headers=headers
        ).status_code
        == 422
    )
    assert (
        master.post(
            f"/api/v1/admin/accounts/{uuid4()}/restore",
            json={"expected_version": 3},
            headers=headers,
        ).status_code
        == 404
    )
    actor = master.get("/api/v1/auth/me").json()["account_id"]
    assert (
        master.post(
            f"/api/v1/admin/accounts/{actor}/restore", json={"expected_version": 1}, headers=headers
        ).status_code
        == 404
    )
    pending = master.post(
        "/api/v1/admin/accounts",
        json={
            "login_id": "restore.pending",
            "branch_id": master.get(f"/api/v1/admin/accounts/{ident}").json()["admin_scope"][
                "branch_id"
            ],
        },
        headers=headers,
    ).json()["account_id"]
    assert (
        master.post(
            f"/api/v1/admin/accounts/{pending}/restore",
            json={"expected_version": 1},
            headers=headers,
        ).status_code
        == 409
    )
    restored = master.post(path, json={"expected_version": 3}, headers=headers)
    assert restored.status_code == 200
    assert restored.json()["state"] == "ACTIVE" and restored.json()["version"] == 4
    assert master.post(path, json={"expected_version": 4}, headers=headers).status_code == 409
    for cookie in cookies:
        cookie_header = SyntheticSecret("__Host-y3-auth=" + cookie)
        assert master.get("/api/v1/auth/me", headers={"Cookie": cookie_header}).status_code == 401
    n, pre = secret_csrf(service)
    fresh = SyntheticSecret(service.login("restore.test", password, pre, n, None))
    fresh_cookie = SyntheticSecret("__Host-y3-auth=" + fresh)
    scope = master.get("/api/v1/branches", headers={"Cookie": fresh_cookie})
    assert scope.status_code == 200 and scope.json()["total"] == 1
    branch_nonce, _ = secret_csrf(service, fresh)
    assert (
        master.post(
            path,
            json={"expected_version": 4},
            headers={
                "Origin": ORIGIN,
                "Cookie": fresh_cookie,
                "X-CSRF-Token": branch_nonce,
            },
        ).status_code
        == 403
    )
    assert master.get("/api/v1/auth/me").status_code == 200
    with db.session() as s:
        after = fingerprint_rows(
            s.execute(
                text("SELECT password_hash,login_id FROM iam_accounts WHERE id=:id"), {"id": ident}
            ).all()
        )
        assert before == after, "Credential or identifier changed during restore"
        assert s.execute(
            text("SELECT row_version,security_version FROM iam_accounts WHERE id=:id"),
            {"id": ident},
        ).one() == (4, 4)
        assert s.execute(
            text(
                "SELECT before_state,after_state,before_version,after_version,actor_role "
                "FROM audit_events WHERE target_id=:id AND action='account_restore'"
            ),
            {"id": ident},
        ).one() == ("DISABLED", "ACTIVE", 3, 4, "MASTER")


@pytest.mark.parametrize("fault", ["audit", "commit_ack"])
def test_restore_atomic_faults(
    restored_subject: tuple[Settings, Database, TestClient, Service, str, UUID, str, list[str]],
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    _, db, master, _, nonce, ident, _, _ = restored_subject
    original_append, original_commit = Audit.append, Session.commit

    def append(adapter: Audit, value: Event) -> None:
        original_append(adapter, value)
        if value.action == "account_restore":
            if fault == "audit":
                raise Rejected(503, "unavailable")
            adapter.s.info["restore_ack"] = True

    def commit(session: Session) -> None:
        original_commit(session)
        if session.info.pop("restore_ack", False):
            raise SQLAlchemyError("SYNTHETIC_ACK_LOSS")

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", append)
        patch.setattr(Session, "commit", commit)
        response = master.post(
            f"/api/v1/admin/accounts/{ident}/restore",
            json={"expected_version": 3},
            headers={"Origin": ORIGIN, "X-CSRF-Token": nonce},
        )
    assert response.status_code == 503
    with db.session() as s:
        assert s.execute(
            text("SELECT state,row_version FROM iam_accounts WHERE id=:id"), {"id": ident}
        ).one() == (("DISABLED", 3) if fault == "audit" else ("ACTIVE", 4))
        assert s.execute(
            text(
                "SELECT count(*) FROM audit_events WHERE target_id=:id AND action='account_restore'"
            ),
            {"id": ident},
        ).scalar_one() == (0 if fault == "audit" else 1)
    assert master.get(f"/api/v1/admin/accounts/{ident}").status_code == 200
    assert master.get("/api/v1/auth/me").status_code == 200


def test_restore_preserves_login_cooldown(
    restored_subject: tuple[Settings, Database, TestClient, Service, str, UUID, str, list[str]],
) -> None:
    _, db, master, service, nonce, ident, password, _ = restored_subject
    for _ in range(5):
        n, pre = secret_csrf(service)
        with pytest.raises(Rejected) as rejected:
            service.login("restore.test", "synthetic wrong password", pre, n, None)
        assert rejected.value.status == 401
    with db.session() as s:
        budgets = s.execute(text("SELECT key,cooldown FROM iam_budgets ORDER BY key")).all()
    assert (
        master.post(
            f"/api/v1/admin/accounts/{ident}/restore",
            json={"expected_version": 3},
            headers={"Origin": ORIGIN, "X-CSRF-Token": nonce},
        ).status_code
        == 200
    )
    with db.session() as s:
        assert s.execute(text("SELECT key,cooldown FROM iam_budgets ORDER BY key")).all() == budgets
    n, pre = secret_csrf(service)
    with pytest.raises(Rejected) as rejected:
        service.login("restore.test", password, pre, n, None)
    assert rejected.value.status == 429


@pytest.mark.parametrize("competitor", ["restore", "login"])
def test_restore_pg_lock_order(
    restored_subject: tuple[Settings, Database, TestClient, Service, str, UUID, str, list[str]],
    monkeypatch: pytest.MonkeyPatch,
    competitor: str,
) -> None:
    _, db, master, service, nonce, ident, password, _ = restored_subject
    auth = master.cookies.get("__Host-y3-auth")
    auth = SyntheticSecret(auth) if auth is not None else None
    n, pre = secret_csrf(service)
    held, release, entering = threading.Event(), threading.Event(), threading.Event()
    holders: list[int] = []
    waiters: list[int] = []
    original = Audit.append

    def append(adapter: Audit, value: Event) -> None:
        original(adapter, value)
        if value.action == "account_restore":
            holders.append(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            held.set()
            assert release.wait(10)

    def observe(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        many: bool,
    ) -> None:
        if threading.current_thread().name.startswith("s2-waiter") and (
            "FOR UPDATE" in statement or "FOR SHARE" in statement
        ):
            driver = connection.connection.driver_connection
            assert driver is not None
            waiters.append(driver.info.backend_pid)
            entering.set()

    def compete() -> int:
        try:
            if competitor == "restore":
                service.restore(auth, nonce, ident, 3)
            else:
                service.login("restore.test", password, pre, n, None)
            return 200
        except Rejected as error:
            return error.status

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", append)
        sql_event.listen(db.engine, "before_cursor_execute", observe)
        try:
            with (
                concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool,
                concurrent.futures.ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="s2-waiter"
                ) as other,
            ):
                first = pool.submit(service.restore, auth, nonce, ident, 3)
                try:
                    assert held.wait(5)
                    second = other.submit(compete)
                    assert entering.wait(5)
                    deadline = time.monotonic() + 3
                    blocked = False
                    while time.monotonic() < deadline:
                        with db.session() as s:
                            blocked = (
                                holders[0]
                                in s.execute(
                                    text("SELECT pg_blocking_pids(:p)"), {"p": waiters[-1]}
                                ).scalar_one()
                            )
                        if blocked:
                            break
                        time.sleep(0.01)
                    assert blocked and not second.done()
                finally:
                    release.set()
                assert first.result(timeout=5).state == "ACTIVE"
                assert second.result(timeout=5) == (409 if competitor == "restore" else 200)
        finally:
            release.set()
            sql_event.remove(db.engine, "before_cursor_execute", observe)
    n, pre = secret_csrf(service)
    fresh = SyntheticSecret(service.login("restore.test", password, pre, n, None))
    assert service.me(fresh).account_id == ident


def test_restore_migration_preserves_existing_data_and_audit(
    restored_subject: tuple[Settings, Database, TestClient, Service, str, UUID, str, list[str]],
) -> None:
    settings, db, master, _, nonce, ident, _, _ = restored_subject

    def migrate(target: str, direction: str = "upgrade") -> int:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", direction, target],
            env=child_env(settings),
            capture_output=True,
            timeout=30,
        )
        return result.returncode

    def facts() -> list[str]:
        with db.session() as s:
            return [
                fingerprint_rows(s.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all())
                for table in (
                    "iam_accounts",
                    "iam_admin_grants",
                    "iam_login_ids",
                    "iam_credentials",
                    "audit_events",
                )
            ]

    before = facts()
    assert migrate("0001_iam_s1", "downgrade") == 0
    assert migrate("head") == 0
    assert facts() == before, "Existing IAM data changed during revision roundtrip"
    assert (
        master.post(
            f"/api/v1/admin/accounts/{ident}/restore",
            json={"expected_version": 3},
            headers={"Origin": ORIGIN, "X-CSRF-Token": nonce},
        ).status_code
        == 200
    )
    after = facts()
    assert migrate("0001_iam_s1", "downgrade") != 0
    assert facts() == after, "Restore audit was removed by downgrade"
    with db.session() as s:
        assert (
            s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == ScriptDirectory.from_config(Config("alembic.ini")).get_current_head()
        )
