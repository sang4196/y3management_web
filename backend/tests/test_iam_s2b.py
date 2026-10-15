"""Real CLI/API, PostgreSQL locks and failures for authenticated password changes."""

import concurrent.futures
import secrets
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import urlsplit
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event as sql_event
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, SyntheticSecret, child_env, iam, login  # noqa: F401
from tests.test_iam_s2 import fingerprint_rows
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.passwords import Passwords
from y3management.iam.public import LoginProof
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


def expect(response: httpx.Response, status: int) -> None:
    if response.status_code != status:
        pytest.fail("S2B_HTTP_STATUS_MISMATCH", pytrace=False)


def nonce(client: TestClient) -> SyntheticSecret:
    response = client.get(
        "/api/v1/auth/csrf", headers={"X-Y3-Client": "acceptance", "Origin": ORIGIN}
    )
    expect(response, 200)
    return SyntheticSecret(response.json()["csrf_token"])


def auth(client: TestClient) -> SyntheticSecret:
    value = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
    if not value:
        pytest.fail("S2B_AUTH_PRECONDITION_MISSING", pytrace=False)
    return SyntheticSecret(value)


def headers(client: TestClient) -> dict[str, str]:
    return {"Origin": ORIGIN, "X-CSRF-Token": nonce(client)}


@dataclass(repr=False)
class World:
    settings: Settings
    db: Database
    service: Service
    master: TestClient
    master_twin: TestClient
    branch: TestClient
    branch_twin: TestClient
    master_password: str
    branch_password: str
    ident: UUID
    branch_id: UUID
    second_branch: UUID


@pytest.fixture
def world(iam: tuple[Settings, Database, str]) -> Iterator[World]:  # noqa: F811
    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        clients = [TestClient(app, base_url=ORIGIN) for _ in range(3)]
        try:
            master_twin, branch_client, branch_twin = clients
            login(master, "master.test", password)
            login(master_twin, "master.test", password)
            a = master.post(
                "/api/v1/admin/branches", json={"code": "A", "name": "A"}, headers=headers(master)
            )
            b = master.post(
                "/api/v1/admin/branches", json={"code": "B", "name": "B"}, headers=headers(master)
            )
            expect(a, 201)
            expect(b, 201)
            issued = master.post(
                "/api/v1/admin/accounts",
                json={"login_id": "password.branch", "branch_id": a.json()["id"]},
                headers=headers(master),
            )
            expect(issued, 201)
            setup = SyntheticSecret(urlsplit(issued.json()["setup_link"]).fragment[6:])
            branch_password = SyntheticSecret("가상 본인 암호 " + secrets.token_urlsafe(24))
            expect(
                branch_client.post(
                    "/api/v1/auth/credentials/complete",
                    json={"setup_token": setup, "new_password": branch_password},
                    headers=headers(branch_client),
                ),
                204,
            )
            login(branch_client, "password.branch", branch_password)
            login(branch_twin, "password.branch", branch_password)
            for client in [master, *clients]:
                expect(client.get("/api/v1/auth/me"), 200)
            independent_master = auth(master) != auth(master_twin)
            independent_branch = auth(branch_client) != auth(branch_twin)
            assert independent_master, "Independent Master sessions required"
            assert independent_branch, "Independent Branch sessions required"
            yield World(
                settings,
                db,
                app.state.iam_service,
                master,
                master_twin,
                branch_client,
                branch_twin,
                password,
                branch_password,
                UUID(issued.json()["account_id"]),
                UUID(a.json()["id"]),
                UUID(b.json()["id"]),
            )
        finally:
            for client in clients:
                client.close()


def facts(db: Database) -> list[str]:
    with db.session() as s:
        return [
            fingerprint_rows(s.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all())
            for table in (
                "iam_accounts",
                "iam_admin_grants",
                "iam_login_ids",
                "iam_sessions",
                "iam_credentials",
                "iam_attempts",
                "iam_budgets",
                "audit_events",
            )
        ]


def change(client: TestClient, old: str, new: str) -> httpx.Response:
    response: httpx.Response = client.post(
        "/api/v1/auth/password",
        json={"current_password": old, "new_password": new},
        headers=headers(client),
    )
    return response


@pytest.mark.parametrize("actor", ["master", "branch"])
def test_password_change_two_sessions_and_scope(world: World, actor: str) -> None:
    client = world.master if actor == "master" else world.branch
    twin = world.master_twin if actor == "master" else world.branch_twin
    other = world.branch if actor == "master" else world.master
    old = world.master_password if actor == "master" else world.branch_password
    identifier = "master.test" if actor == "master" else "password.branch"
    before_scope = client.get("/api/v1/auth/me").json()
    old_cookie = auth(client)
    new = SyntheticSecret("변경된 본인 암호 " + secrets.token_urlsafe(24))
    with world.db.session() as s:
        budget = fingerprint_rows(s.execute(text("SELECT * FROM iam_budgets ORDER BY key")).all())
        other_id = UUID(other.get("/api/v1/auth/me").json()["account_id"])
        other_hash = fingerprint_rows(
            s.execute(text("SELECT * FROM iam_accounts WHERE id=:a"), {"a": other_id}).all()
        )
    response = change(client, old, new)
    expect(response, 204)
    empty_body = response.content == b""
    cookies_cleared = not client.cookies.get("__Host-y3-auth") and not client.cookies.get(
        "__Host-y3-preauth"
    )
    cookie_header_count = len(response.headers.get_list("set-cookie"))
    assert empty_body
    assert cookies_cleared
    assert cookie_header_count == 2
    expect(client.get("/api/v1/auth/me"), 401)
    expect(twin.get("/api/v1/auth/me"), 401)
    cookie_header = SyntheticSecret("__Host-y3-auth=" + old_cookie)
    expect(client.get("/api/v1/auth/me", headers={"Cookie": cookie_header}), 401)
    expect(other.get("/api/v1/auth/me"), 200)
    with world.db.session() as s:
        current_budget = fingerprint_rows(
            s.execute(text("SELECT * FROM iam_budgets ORDER BY key")).all()
        )
        current_other = fingerprint_rows(
            s.execute(text("SELECT * FROM iam_accounts WHERE id=:a"), {"a": other_id}).all()
        )
        assert current_budget == budget
        assert current_other == other_hash
        assert (
            s.execute(
                text("SELECT count(*) FROM audit_events WHERE action='password_change'")
            ).scalar_one()
            == 1
        )
    expect(
        client.post(
            "/api/v1/auth/login",
            json={"login_id": identifier, "password": old},
            headers=headers(client),
        ),
        401,
    )
    login(client, identifier, new)
    current_scope = client.get("/api/v1/auth/me").json()
    assert current_scope == before_scope
    if actor == "branch":
        expect(client.get(f"/api/v1/branches/{world.second_branch}"), 404)


@pytest.mark.parametrize(
    "case",
    [
        "current",
        "policy",
        "csrf",
        "origin",
        "json",
        "extra",
        "anonymous",
        "revoked",
        "expired",
        "disabled",
        "capacity",
    ],
)
def test_password_rejections_preserve_state(
    world: World, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    client = world.branch
    request_headers = headers(client)
    body = {
        "current_password": world.branch_password,
        "new_password": SyntheticSecret("새로운 가상 암호 " + secrets.token_urlsafe(24)),
    }
    expected = 401
    if case == "current":
        body["current_password"] = SyntheticSecret("synthetic incorrect current")
    elif case == "policy":
        body["new_password"] = SyntheticSecret("short")
        expected = 422
    elif case == "csrf":
        request_headers["X-CSRF-Token"] = "invalid"
        expected = 403
    elif case == "origin":
        request_headers["Origin"] = "https://localhost:1"
        expected = 403
    elif case == "json":
        request_headers["Content-Type"] = "text/plain"
        expected = 422  # Existing FastAPI body validation rejects non-JSON before the handler.
    elif case == "extra":
        body["account_id"] = str(world.ident)
        expected = 422
    elif case == "anonymous":
        client.cookies.clear()
    elif case == "revoked":
        expect(client.post("/api/v1/auth/logout", json={}, headers=request_headers), 204)
    elif case == "expired":
        with world.db.engine.begin() as c:
            c.execute(
                text(
                    "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',"
                    "last_activity=clock_timestamp()-interval '31 minutes' WHERE account_id=:a"
                ),
                {"a": world.ident},
            )
    elif case == "disabled":
        expect(
            world.master.patch(
                f"/api/v1/admin/accounts/{world.ident}/status",
                json={"expected_version": 2, "status": "DISABLED"},
                headers=headers(world.master),
            ),
            200,
        )
    elif case == "capacity":
        expected = 503
    old_cookie = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
    before = facts(world.db)
    original_verify = Passwords.verify

    def forbidden_verify(
        engine: Passwords, value: str, encoded: str | None
    ) -> tuple[bool, str | None]:
        pytest.fail("HASH_ENTERED_BEFORE_AUTH_CSRF_REJECTION", pytrace=False)

    no_hash = case in {"csrf", "origin", "extra", "anonymous", "revoked", "expired", "disabled"}
    with monkeypatch.context() as patch:
        if no_hash:
            patch.setattr(Passwords, "verify", forbidden_verify)
        if case == "capacity":
            with world.service.uow._passwords.capacity(), world.service.uow._passwords.capacity():
                response = client.post("/api/v1/auth/password", json=body, headers=request_headers)
        else:
            response = client.post("/api/v1/auth/password", json=body, headers=request_headers)
    assert Passwords.verify is original_verify
    expect(response, expected)
    no_cookie_headers = not response.headers.get_list("set-cookie")
    assert no_cookie_headers
    current_cookie = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
    cookie_unchanged = current_cookie == old_cookie
    assert cookie_unchanged
    assert facts(world.db) == before, "Rejected password change mutated persisted facts"


@pytest.mark.parametrize("fault", ["audit", "ack"])
def test_password_atomic_failures(
    world: World, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    new = SyntheticSecret("저장 실패 가상 암호 " + secrets.token_urlsafe(24))
    before = facts(world.db)
    original_commit, original_append = Session.commit, Audit.append

    def append(adapter: Audit, value: Event) -> None:
        original_append(adapter, value)
        if value.action == "password_change":
            if fault == "audit":
                raise Rejected(503, "unavailable")
            adapter.s.info["password_ack"] = True

    def commit(session: Session) -> None:
        original_commit(session)
        if session.info.pop("password_ack", False):
            raise SQLAlchemyError("SYNTHETIC_ACK_LOSS")

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", append)
        patch.setattr(Session, "commit", commit)
        response = change(world.branch, world.branch_password, new)
    expect(response, 503)
    no_cookie_headers = not response.headers.get_list("set-cookie")
    assert no_cookie_headers
    if fault == "audit":
        assert facts(world.db) == before
        expect(world.branch.get("/api/v1/auth/me"), 200)
        expect(world.branch_twin.get("/api/v1/auth/me"), 200)
    else:
        expect(world.branch.get("/api/v1/auth/me"), 401)
        expect(world.branch_twin.get("/api/v1/auth/me"), 401)
        world.branch.cookies.clear()
        login(world.branch, "password.branch", new)
        with world.db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='password_change'")
                ).scalar_one()
                == 1
            )


@pytest.mark.parametrize("management", ["disable", "scope"])
def test_password_hash_has_no_business_lock_and_rechecks(
    world: World, monkeypatch: pytest.MonkeyPatch, management: str
) -> None:
    hashed, release = threading.Event(), threading.Event()
    new = SyntheticSecret("경합 비밀번호 가상 " + secrets.token_urlsafe(24))
    token, csrf = auth(world.branch), nonce(world.branch)
    original = Passwords.create

    def create(engine: Passwords, value: str, identifier: str) -> str:
        encoded = SyntheticSecret(original(engine, value, identifier))
        hashed.set()
        assert release.wait(10)
        return encoded

    def change_worker() -> int:
        try:
            world.service.change_password(token, csrf, world.branch_password, new)
            return 204
        except Rejected as error:
            return error.status

    with monkeypatch.context() as patch:
        patch.setattr(Passwords, "create", create)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(change_worker)
            try:
                assert hashed.wait(5)
                # Management commits while the hash phase is paused, proving no business row lock.
                world.service.change(
                    auth(world.master),
                    nonce(world.master),
                    world.ident,
                    2,
                    branch=world.second_branch if management == "scope" else None,
                    disable=management == "disable",
                )
            finally:
                release.set()
            assert pending.result(timeout=5) == 401
    with world.db.session() as s:
        assert (
            s.execute(
                text("SELECT count(*) FROM audit_events WHERE action='password_change'")
            ).scalar_one()
            == 0
        )


@pytest.mark.parametrize("competitor", ["login", "disable", "scope"])
def test_password_commit_orders_waiting_pg_connections(
    world: World, monkeypatch: pytest.MonkeyPatch, competitor: str
) -> None:
    held, release, entered = threading.Event(), threading.Event(), threading.Event()
    holders: list[int] = []
    waiters: list[int] = []
    new = SyntheticSecret("잠금 순서 검증 암호 " + secrets.token_urlsafe(24))
    branch_auth, branch_nonce = auth(world.branch), nonce(world.branch)
    master_auth, master_nonce = auth(world.master), nonce(world.master)
    n, pre = world.service.csrf(None, None)
    n = SyntheticSecret(n)
    pre = SyntheticSecret(pre) if pre else None
    original = Audit.append

    def append(adapter: Audit, value: Event) -> None:
        original(adapter, value)
        if value.action == "password_change":
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
        if threading.current_thread().name.startswith("s2b-waiter") and (
            "FOR UPDATE" in statement or "FOR SHARE" in statement
        ):
            driver = connection.connection.driver_connection
            assert driver is not None
            waiters.append(driver.info.backend_pid)
            entered.set()

    def compete() -> int:
        try:
            if competitor == "login":
                world.service.login("password.branch", world.branch_password, pre, n, None)
            else:
                world.service.change(
                    master_auth,
                    master_nonce,
                    world.ident,
                    2,
                    branch=world.second_branch if competitor == "scope" else None,
                    disable=competitor == "disable",
                )
            return 200
        except Rejected as error:
            return error.status

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", append)
        sql_event.listen(world.db.engine, "before_cursor_execute", observe)
        try:
            with (
                concurrent.futures.ThreadPoolExecutor(max_workers=1) as first_pool,
                concurrent.futures.ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="s2b-waiter"
                ) as second_pool,
            ):
                first = first_pool.submit(
                    world.service.change_password,
                    branch_auth,
                    branch_nonce,
                    world.branch_password,
                    new,
                )
                try:
                    assert held.wait(5)
                    second = second_pool.submit(compete)
                    assert entered.wait(5)
                    blocked = False
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        with world.db.session() as s:
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
                first.result(timeout=5)
                assert second.result(timeout=5) == (401 if competitor == "login" else 409)
        finally:
            release.set()
            sql_event.remove(world.db.engine, "before_cursor_execute", observe)
    expect(world.master.get("/api/v1/auth/me"), 200)


def test_login_snapshot_loses_to_password_change(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    verified, release = threading.Event(), threading.Event()
    original = IAM.verify_login
    new = SyntheticSecret("오래된 로그인 검증 " + secrets.token_urlsafe(24))
    n, pre = world.service.csrf(None, None)
    n, pre = SyntheticSecret(n), SyntheticSecret(pre) if pre else None

    def verify(adapter: IAM, identifier: str, value: str) -> LoginProof | None:
        proof = original(adapter, identifier, value)
        verified.set()
        assert release.wait(10)
        return proof

    def worker() -> int:
        try:
            world.service.login("password.branch", world.branch_password, pre, n, None)
            return 200
        except Rejected as error:
            return error.status

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "verify_login", verify)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(worker)
            try:
                assert verified.wait(5)
                expect(change(world.branch, world.branch_password, new), 204)
            finally:
                release.set()
            assert pending.result(timeout=5) == 401


def test_password_migration_roundtrip_and_history_guard(world: World) -> None:
    def migrate(direction: str, target: str) -> int:
        return subprocess.run(
            [sys.executable, "-m", "alembic", direction, target],
            env=child_env(world.settings),
            capture_output=True,
            timeout=30,
        ).returncode

    before = facts(world.db)
    assert migrate("downgrade", "0002_iam_restore") == 0
    assert migrate("upgrade", "head") == 0
    assert facts(world.db) == before
    new = SyntheticSecret("이력 보존 암호 변경 " + secrets.token_urlsafe(24))
    expect(change(world.branch, world.branch_password, new), 204)
    after = facts(world.db)
    assert migrate("downgrade", "0002_iam_restore") != 0
    assert facts(world.db) == after
    with world.db.session() as s:
        assert (
            s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0003_iam_password"
        )


def test_password_change_does_not_clear_existing_cooldown(world: World) -> None:
    for _ in range(5):
        n, pre = world.service.csrf(None, None)
        n, pre = SyntheticSecret(n), SyntheticSecret(pre) if pre else None
        with pytest.raises(Rejected) as rejected:
            world.service.login(
                "password.branch", SyntheticSecret("synthetic invalid"), pre, n, None
            )
        assert rejected.value.status == 401
    with world.db.session() as s:
        before = [
            fingerprint_rows(s.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all())
            for table in ("iam_budgets", "iam_attempts")
        ]
    new = SyntheticSecret("대기 보존 새 비밀번호 " + secrets.token_urlsafe(24))
    expect(change(world.branch, world.branch_password, new), 204)
    with world.db.session() as s:
        after = [
            fingerprint_rows(s.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all())
            for table in ("iam_budgets", "iam_attempts")
        ]
    assert before == after
    expect(
        world.branch.post(
            "/api/v1/auth/login",
            json={"login_id": "password.branch", "password": new},
            headers=headers(world.branch),
        ),
        429,
    )


def test_two_password_changes_cannot_apply_stale_proof(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    barrier = threading.Barrier(2)
    original = IAM.prepare_password_change
    tokens = [auth(world.branch), auth(world.branch_twin)]
    nonces = [nonce(world.branch), nonce(world.branch_twin)]
    new = [SyntheticSecret("동시 본인 변경 " + secrets.token_urlsafe(24)) for _ in range(2)]

    def prepare(adapter: IAM, ident: UUID, current_password: str, new_password: str) -> LoginProof:
        proof = original(adapter, ident, current_password, new_password)
        barrier.wait(timeout=10)
        return proof

    def run(index: int) -> int:
        try:
            world.service.change_password(
                tokens[index], nonces[index], world.branch_password, new[index]
            )
            return 204
        except Rejected as error:
            return error.status

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "prepare_password_change", prepare)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, range(2)))
    assert sorted(results) == [204, 401]
    expect(world.branch.get("/api/v1/auth/me"), 401)
    expect(world.branch_twin.get("/api/v1/auth/me"), 401)
    world.branch.cookies.clear()
    login(world.branch, "password.branch", new[results.index(204)])
    with world.db.session() as s:
        assert (
            s.execute(
                text("SELECT count(*) FROM audit_events WHERE action='password_change'")
            ).scalar_one()
            == 1
        )
