"""Real isolated-schema S1 acceptance. Accounts are prepared through protected CLI/API."""

import os
import pty
import secrets
import select
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import ExitStack
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.conftest import qa_record_schema, qa_register_process, qa_stop_process
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres
ORIGIN = "https://localhost:8443"


class SyntheticSecret(str):
    def __repr__(self) -> str:
        return "<synthetic-secret>"


def child_env(settings: Settings) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("Y3_")}
    env.update(
        Y3_ENVIRONMENT="test",
        Y3_DATABASE_URL=settings.database_url.get_secret_value(),
        Y3_DATABASE_SCHEMA=settings.database_schema,
        Y3_IAM_ENABLED="true",
        Y3_CANONICAL_ORIGIN=ORIGIN,
        Y3_IAM_KEY=settings.iam_key.get_secret_value(),
        Y3_SECURITY_STATE_CAPACITY="2048",
        Y3_AUTH_SESSION_CAPACITY="128",
    )
    return env


def cli_bootstrap(settings: Settings, password: str, *, success: bool = True) -> None:
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "y3management.cli",
            "bootstrap-initial-master",
            "--organization",
            "Test Organization",
            "--login-id",
            "master.test",
            "--confirm-database",
            "y3management_test",
        ],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=child_env(settings),
        start_new_session=True,
    )
    qa_register_process(process)
    os.close(slave)
    output = b""
    sent = 0
    deadline = time.monotonic() + 30
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                output += chunk
                if sent == 0 and b"Initial Master password: " in output:
                    os.write(master, (password + "\n").encode())
                    sent += 1
                if sent == 1 and b"Confirm password: " in output:
                    os.write(master, (password + "\n").encode())
                    sent += 1
            if process.poll() is not None:
                break
        code = process.wait(timeout=5)
        assert code == (0 if success else 1), "Protected bootstrap outcome mismatch"
        assert password.encode() not in output, "Bootstrap secret echoed"
    finally:
        qa_stop_process(process)
        os.close(master)


@pytest.fixture
def iam(postgres_database: Database) -> Iterator[tuple[Settings, Database, str]]:
    schema = "iam_test_" + uuid4().hex
    qa_record_schema(schema, True)

    def drop_owned_schema() -> None:
        with postgres_database.engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        qa_record_schema(schema, False)

    with ExitStack() as cleanup:
        with postgres_database.engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        cleanup.callback(drop_owned_schema)
        settings = Settings(
            environment="test",
            database_url=postgres_database.engine.url.render_as_string(hide_password=False),
            database_schema=schema,
            iam_enabled=True,
            canonical_origin=ORIGIN,
            iam_key=secrets.token_urlsafe(32),
            security_state_capacity=2048,
            auth_session_capacity=128,
        )
        database = Database(settings)
        cleanup.callback(database.close)
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=child_env(settings),
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, "Owned-schema Alembic upgrade failed"
        password = SyntheticSecret("가상 검증 전용 " + secrets.token_urlsafe(24))
        cli_bootstrap(settings, password)
        yield settings, database, password


def csrf(client: TestClient) -> str:
    response = client.get("/api/v1/auth/csrf", headers={"X-Y3-Client": "test", "Origin": ORIGIN})
    assert response.status_code == 200
    return str(response.json()["csrf_token"])


def login(client: TestClient, identifier: str, password: str) -> str:
    nonce = csrf(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"login_id": identifier, "password": password},
        headers={"X-CSRF-Token": nonce, "Origin": ORIGIN},
    )
    assert response.status_code == 204, "Real password login failed"
    return csrf(client)


def post(client: TestClient, path: str, nonce: str, data: dict[str, object]) -> object:
    return client.post(
        "/api/v1" + path, json=data, headers={"X-CSRF-Token": nonce, "Origin": ORIGIN}
    )


def test_s1_cli_http_scope_revoke_and_audit(iam: tuple[Settings, Database, str]) -> None:
    settings, db, password = iam
    cli_bootstrap(settings, password, success=False)
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        m = login(master, "MASTER.TEST", password)
        branches = []
        for code in ["A", "B"]:
            r = master.post(
                "/api/v1/admin/branches",
                json={"code": code, "name": code},
                headers={"Origin": ORIGIN, "X-CSRF-Token": m},
            )
            assert r.status_code == 201
            branches.append(r.json()["id"])
        a, b = branches
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "branch.test", "branch_id": a},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert issued.status_code == 201
        account = issued.json()
        ident = account["account_id"]
        old = urlsplit(account["setup_link"]).fragment[6:]
        lookup = master.post(
            "/api/v1/admin/accounts/lookup",
            json={"login_id": "BRANCH.TEST"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert lookup.status_code == 200 and lookup.json()["account_id"] == ident
        assert "setup_link" not in lookup.text and "token" not in lookup.text
        renewed = master.post(
            f"/api/v1/admin/accounts/{ident}/activation",
            json={"expected_version": 1},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert renewed.status_code == 201
        token = urlsplit(renewed.json()["setup_link"]).fragment[6:]
        branch_client = TestClient(app, base_url=ORIGIN)
        pre = csrf(branch_client)
        new_password = "새로운 가상 암호 " + secrets.token_urlsafe(24)
        for invalid in [old, "x" * 43]:
            for candidate in ["비밀번호" * 4, new_password]:
                r = branch_client.post(
                    "/api/v1/auth/credentials/complete",
                    json={"setup_token": invalid, "new_password": candidate},
                    headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
                )
                assert r.status_code == 400
        completed = branch_client.post(
            "/api/v1/auth/credentials/complete",
            json={"setup_token": token, "new_password": new_password},
            headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
        )
        assert completed.status_code == 204
        assert branch_client.get("/api/v1/auth/me").status_code == 401
        n = login(branch_client, "branch.test", new_password)
        assert branch_client.get("/api/v1/branches").json()["total"] == 1
        assert branch_client.get("/api/v1/branches/" + a).status_code == 200
        assert branch_client.get("/api/v1/branches/" + b).status_code == 404
        assert (
            branch_client.get("/api/v1/branches?organization_id=" + str(uuid4())).status_code == 422
        )
        copied = branch_client.cookies.get("__Host-y3-auth")
        twin = TestClient(app, base_url=ORIGIN)
        login(twin, "branch.test", new_password)
        version = master.get("/api/v1/admin/accounts/" + ident).json()["version"]
        no_op = master.patch(
            "/api/v1/admin/accounts/" + ident + "/access",
            json={"expected_version": version, "branch_id": a},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert no_op.status_code == 200 and no_op.json()["version"] == version
        assert twin.get("/api/v1/auth/me").status_code == 200
        changed = master.patch(
            "/api/v1/admin/accounts/" + ident + "/access",
            json={"expected_version": version, "branch_id": b},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert changed.status_code == 200
        assert branch_client.get("/api/v1/auth/me").status_code == 401
        assert twin.get("/api/v1/auth/me").status_code == 401
        assert master.get("/api/v1/auth/me").status_code == 200
        stale = master.patch(
            "/api/v1/admin/accounts/" + ident + "/access",
            json={"expected_version": version, "branch_id": a},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert stale.status_code == 409
        n = login(branch_client, "branch.test", new_password)
        assert branch_client.get("/api/v1/branches/" + b).status_code == 200
        assert branch_client.get("/api/v1/branches/" + a).status_code == 404
        copied = branch_client.cookies.get("__Host-y3-auth")
        out = branch_client.post(
            "/api/v1/auth/logout", json={}, headers={"Origin": ORIGIN, "X-CSRF-Token": n}
        )
        assert out.status_code == 204
        copied_client = TestClient(app, base_url=ORIGIN)
        assert (
            copied_client.get(
                "/api/v1/auth/me", headers={"Cookie": "__Host-y3-auth=" + str(copied)}
            ).status_code
            == 401
        )
        login(branch_client, "branch.test", new_password)
        disabled = master.patch(
            "/api/v1/admin/accounts/" + ident + "/status",
            json={"expected_version": changed.json()["version"], "status": "DISABLED"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert disabled.status_code == 200
        assert branch_client.get("/api/v1/auth/me").status_code == 401
        assert master.get("/api/v1/auth/me").status_code == 200
        with db.session() as session:
            rows = session.execute(
                text("SELECT action,actor_role,actor_scope,request_id FROM audit_events")
            ).all()
            assert {
                "bootstrap",
                "branch_create",
                "account_issue",
                "setup_reissue",
                "setup_complete",
                "login",
                "logout",
                "scope_change",
                "account_disable",
            } <= {r.action for r in rows}
            assert all(r.actor_role and r.actor_scope and r.request_id for r in rows)
        for client in [branch_client, twin, copied_client]:
            client.close()


def test_failure_budget_nonleak_and_storage_bounds(iam: tuple[Settings, Database, str]) -> None:
    from y3management.contracts import Rejected
    from y3management.uow import UnitOfWork
    from y3management.use_cases import Service

    settings, db, _ = iam
    service = Service(UnitOfWork(db, settings))
    p_nonce, p_cookie = service.csrf(None, None)
    outcomes = []
    for identifier in ["master.test", "absent.test"]:
        series = []
        for _ in range(6):
            with pytest.raises(Rejected) as caught:
                service.login(
                    identifier, "가상 오입력 " + secrets.token_urlsafe(20), p_cookie, p_nonce, None
                )
            e = caught.value
            series.append((e.status, e.detail, e.retry_after is not None))
        outcomes.append(series)
    assert (
        outcomes[0]
        == outcomes[1]
        == [(401, "invalid_credentials", False)] * 5 + [(429, "try_later", True)]
    )
    uow = service.uow
    with uow.open() as w:
        orphan = w.security.allocate("credential")
    with db.session() as s:
        s.execute(
            text(
                "UPDATE iam_security_states SET created_at=clock_timestamp()-interval '31 "
                "seconds' WHERE id=:i"
            ),
            {"i": orphan},
        )
        s.commit()
    with uow.open() as w:
        w.security.preparation(None)
    with db.session() as s:
        assert (
            s.execute(text("SELECT 1 FROM iam_security_states WHERE id=:i"), {"i": orphan}).first()
            is None
        )
        # Live occupied states are retained at configured capacity; no live budget eviction.
        count = s.execute(
            text("SELECT count(*) FROM iam_security_states WHERE kind<>'session_slot'")
        ).scalar_one()
    limited = Settings.model_validate({**settings.model_dump(), "security_state_capacity": 64})
    capped = UnitOfWork(db, limited)
    for _ in range(64 - int(count)):
        with capped.open() as w:
            w.security.preparation(None)
    with pytest.raises(Rejected) as full:
        with capped.open() as w:
            w.security.preparation(None)
    assert full.value.status == 503
    with db.session() as s:
        assert (
            s.execute(
                text("SELECT count(*) FROM iam_security_states WHERE kind<>'session_slot'")
            ).scalar_one()
            == 64
        )
        assert s.execute(text("SELECT count(*) FROM iam_budgets")).scalar_one() == 2


def test_atomic_audit_rollback_and_sql_constraints(iam: tuple[Settings, Database, str]) -> None:
    from sqlalchemy.exc import IntegrityError

    settings, db, password = iam
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        nonce = login(client, "master.test", password)
        with db.session() as s:
            account = s.execute(text("SELECT id,organization_id FROM iam_accounts")).one()
            s.execute(
                text("""CREATE FUNCTION fail_audit() RETURNS trigger LANGUAGE plpgsql AS
            $$BEGIN RAISE EXCEPTION 'injected audit failure'; END$$""")
            )
            s.execute(
                text(
                    "CREATE TRIGGER fail_audit BEFORE INSERT ON audit_events FOR EACH ROW "
                    "EXECUTE FUNCTION fail_audit()"
                )
            )
            s.commit()
        failed = client.post(
            "/api/v1/admin/branches",
            json={"code": "FAIL", "name": "rollback"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": nonce},
        )
        assert failed.status_code == 503
        with db.session() as s:
            assert s.execute(text("SELECT count(*) FROM organization_branches")).scalar_one() == 0
            s.execute(text("DROP TRIGGER fail_audit ON audit_events"))
            s.commit()
        for sql, parameters in [
            (
                "UPDATE iam_accounts SET login_id=:v WHERE id=:id",
                {"v": "unreserved.test", "id": account.id},
            ),
            ("INSERT INTO iam_login_ids VALUES(:v,:id)", {"v": "UPPER.test", "id": account.id}),
            ("UPDATE iam_accounts SET row_version=0 WHERE id=:id", {"id": account.id}),
        ]:
            with pytest.raises(IntegrityError), db.session() as s:
                s.execute(text(sql), parameters)
                s.commit()
        foreign_org, foreign_branch = uuid4(), uuid4()
        with db.session() as s:
            s.execute(
                text("INSERT INTO organization_organizations VALUES(:id,:name)"),
                {"id": foreign_org, "name": "Foreign synthetic"},
            )
            s.execute(
                text("INSERT INTO organization_branches VALUES(:b,:o,:c,:n)"),
                {"b": foreign_branch, "o": foreign_org, "c": "X", "n": "X"},
            )
            s.commit()
        assert client.get("/api/v1/branches/" + str(foreign_branch)).status_code == 404
        issued = client.post(
            "/api/v1/admin/accounts",
            json={"login_id": "foreign.test", "branch_id": str(foreign_branch)},
            headers={"Origin": ORIGIN, "X-CSRF-Token": nonce},
        )
        assert issued.status_code == 404
        with pytest.raises(IntegrityError), db.session() as s:
            s.execute(
                text("UPDATE iam_admin_grants SET scope='BRANCH',branch_id=:b WHERE account_id=:a"),
                {"b": foreign_branch, "a": account.id},
            )
            s.commit()
        with db.session() as s:
            boot = s.execute(
                text(
                    "SELECT actor_id,actor_role,actor_scope FROM audit_events WHERE "
                    "action='bootstrap'"
                )
            ).one()
            assert tuple(boot) == (None, "INSTALLER", "INSTALLATION")


def test_invalid_setup_is_rejected_before_hash(
    iam: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.iam.passwords import Passwords

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        n = login(master, "master.test", password)
        branch = master.post(
            "/api/v1/admin/branches",
            json={"code": "A", "name": "A"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": n},
        ).json()["id"]
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "expiry.test", "branch_id": branch},
            headers={"Origin": ORIGIN, "X-CSRF-Token": n},
        ).json()
        target = TestClient(app, base_url=ORIGIN)
        pre = csrf(target)
        token = urlsplit(issued["setup_link"]).fragment[6:]
        with db.session() as s:
            s.execute(
                text("UPDATE iam_credentials SET expires_at=clock_timestamp()-interval '1 second'")
            )
            s.commit()

        def forbidden_hash(self: Passwords, value: str, login_id: str) -> str:
            raise AssertionError("INVALID_TOKEN_REACHED_HASH")

        monkeypatch.setattr(Passwords, "create", forbidden_hash)
        for value in ["비밀번호" * 4, "유효 길이 정상 암호 " + secrets.token_urlsafe(20)]:
            r = target.post(
                "/api/v1/auth/credentials/complete",
                json={"setup_token": token, "new_password": value},
                headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
            )
            assert r.status_code == 400
        target.close()


def test_independent_connection_reservation_race(iam: tuple[Settings, Database, str]) -> None:
    import concurrent.futures
    import threading

    from y3management.contracts import Rejected
    from y3management.uow import UnitOfWork

    settings, db, _ = iam
    uow = UnitOfWork(db, settings)
    barrier = threading.Barrier(10)

    def reserve(index: int) -> int:
        barrier.wait(timeout=10)
        try:
            with uow.open(commit_denial=True) as w:
                w.security.reserve("concurrent.test")
            return 0
        except Rejected as e:
            return e.status

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        statuses = list(ex.map(reserve, range(10)))
    assert statuses.count(0) == 5 and statuses.count(429) == 5
    with db.session() as s:
        assert (
            s.execute(
                text("SELECT count(*) FROM iam_attempts WHERE outcome='pending'")
            ).scalar_one()
            == 5
        )


def test_commit_ack_loss_preserves_committed_children(
    iam: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm import Session

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        m = login(master, "master.test", password)
        branch = master.post(
            "/api/v1/admin/branches",
            json={"code": "A", "name": "A"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()["id"]
        original = Session.commit
        inject: dict[str, object] = {}

        def commit(session: Session) -> None:
            fail = False
            if inject:
                count = session.execute(
                    text("SELECT count(*) FROM audit_events WHERE action=:a"),
                    {"a": inject["action"]},
                ).scalar_one()
                fail = int(count) > int(str(inject["baseline"]))
            original(session)
            if fail:
                inject.clear()
                raise SQLAlchemyError("SYNTHETIC_COMMIT_ACK_LOSS")

        monkeypatch.setattr(Session, "commit", commit)
        inject.update(action="account_issue", baseline=0)
        r = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "ack.test", "branch_id": branch},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert r.status_code == 503
        found = master.post(
            "/api/v1/admin/accounts/lookup",
            json={"login_id": "ack.test"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert found.status_code == 200
        ident = found.json()["account_id"]
        with db.session() as s:
            assert (
                s.execute(
                    text(
                        "SELECT count(*) FROM iam_credentials WHERE account_id=:a AND NOT consumed"
                    ),
                    {"a": UUID(ident)},
                ).scalar_one()
                == 1
            )
        inject.update(action="setup_reissue", baseline=0)
        r = master.post(
            "/api/v1/admin/accounts/" + ident + "/activation",
            json={"expected_version": 1},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert r.status_code == 503
        assert master.get("/api/v1/admin/accounts/" + ident).json()["version"] == 2
        with db.session() as s:
            assert (
                s.execute(
                    text(
                        "SELECT count(*) FROM iam_credentials WHERE account_id=:a AND NOT consumed"
                    ),
                    {"a": UUID(ident)},
                ).scalar_one()
                == 1
            )
        recovered = master.post(
            "/api/v1/admin/accounts/" + ident + "/activation",
            json={"expected_version": 2},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        )
        assert recovered.status_code == 201
        token = urlsplit(recovered.json()["setup_link"]).fragment[6:]
        target = TestClient(app, base_url=ORIGIN)
        pre = csrf(target)
        pw = "가상 ACK 검증 " + secrets.token_urlsafe(24)
        done = target.post(
            "/api/v1/auth/credentials/complete",
            json={"setup_token": token, "new_password": pw},
            headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
        )
        assert done.status_code == 204
        with db.session() as s:
            baseline = s.execute(
                text("SELECT count(*) FROM audit_events WHERE action='login'")
            ).scalar_one()
        pre = csrf(target)
        inject.update(action="login", baseline=baseline)
        r = target.post(
            "/api/v1/auth/login",
            json={"login_id": "ack.test", "password": pw},
            headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
        )
        assert r.status_code == 503
        assert not target.cookies.get("__Host-y3-auth")
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
                    {"a": UUID(ident)},
                ).scalar_one()
                == 1
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='login'")
                ).scalar_one()
                == baseline + 1
            )
        target.close()


def test_read_lock_orders_scope_change(iam: tuple[Settings, Database, str]) -> None:
    import threading

    from sqlalchemy import event as sql_event

    from y3management.uow import UnitOfWork
    from y3management.use_cases import Service

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        m = login(master, "master.test", password)
        a = master.post(
            "/api/v1/admin/branches",
            json={"code": "A", "name": "A"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()["id"]
        b = master.post(
            "/api/v1/admin/branches",
            json={"code": "B", "name": "B"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()["id"]
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "race.test", "branch_id": a},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()
        ident = UUID(issued["account_id"])
        token = urlsplit(issued["setup_link"]).fragment[6:]
        target = TestClient(app, base_url=ORIGIN)
        pre = csrf(target)
        pw = "가상 경합 검증 " + secrets.token_urlsafe(24)
        assert (
            target.post(
                "/api/v1/auth/credentials/complete",
                json={"setup_token": token, "new_password": pw},
                headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
            ).status_code
            == 204
        )
        login(target, "race.test", pw)
        service = Service(UnitOfWork(db, settings))
        entered = threading.Event()
        done = threading.Event()
        pids = []
        outcomes = []

        def observe(
            connection: object,
            cursor: object,
            statement: str,
            parameters: object,
            context: object,
            many: bool,
        ) -> None:
            if (
                threading.current_thread().name == "scope-writer"
                and "iam_accounts" in statement
                and "FOR UPDATE" in statement
            ):
                from sqlalchemy.engine import Connection

                assert isinstance(connection, Connection)
                driver = connection.connection.driver_connection
                assert driver is not None
                pids.append(driver.info.backend_pid)
                entered.set()

        def writer() -> None:
            try:
                account = service.change(master.cookies.get("__Host-y3-auth"), m, ident, 2, UUID(b))
                outcomes.append(account.version)
            except Exception:
                outcomes.append(-1)
            finally:
                done.set()

        sql_event.listen(db.engine, "before_cursor_execute", observe)
        thread = threading.Thread(target=writer, name="scope-writer")
        try:
            with service.uow.open() as work:
                caller = work.iam.authenticate(target.cookies.get("__Host-y3-auth")).caller
                thread.start()
                assert entered.wait(5)
                deadline = time.monotonic() + 1.5
                blocked = False
                while time.monotonic() < deadline:
                    with db.session() as inspector:
                        blocked = bool(
                            inspector.execute(
                                text("SELECT pg_blocking_pids(:p)"), {"p": pids[-1]}
                            ).scalar_one()
                        )
                    if blocked:
                        break
                    time.sleep(0.01)
                assert blocked and not done.is_set()
                assert work.organization.get_branch(caller, UUID(a)).id == UUID(a)
            assert done.wait(5)
            assert outcomes == [3]
            assert target.get("/api/v1/auth/me").status_code == 401
            assert master.get("/api/v1/auth/me").status_code == 200
        finally:
            if thread.ident:
                thread.join(timeout=5)
            sql_event.remove(db.engine, "before_cursor_execute", observe)
            target.close()


def test_valid_auth_login_conflict_and_verification_failure_budget(
    iam: tuple[Settings, Database, str],
) -> None:
    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        nonce = login(master, "master.test", password)
        old = master.cookies.get("__Host-y3-auth")
        conflict = master.post(
            "/api/v1/auth/login",
            json={"login_id": "master.test", "password": password},
            headers={"Origin": ORIGIN, "X-CSRF-Token": nonce},
        )
        assert conflict.status_code == 409 and conflict.json() == {"detail": "logout_required"}
        outsider = TestClient(app, base_url=ORIGIN)
        pre = csrf(outsider)
        forged = master.post(
            "/api/v1/auth/login",
            json={"login_id": "master.test", "password": password},
            headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
        )
        assert forged.status_code == 403 and master.cookies.get("__Host-y3-auth") == old
        service = app.state.iam_service
        with service.uow._passwords.capacity(), service.uow._passwords.capacity():
            busy = outsider.post(
                "/api/v1/auth/login",
                json={"login_id": "master.test", "password": password},
                headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
            )
        assert busy.status_code == 503
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome IN ('pending','failure')")
                ).scalar_one()
                == 0
            )
            s.execute(
                text("""CREATE FUNCTION reject_failure_audit() RETURNS trigger LANGUAGE plpgsql AS
            $$BEGIN IF NEW.action='login' AND NOT NEW.success THEN
            RAISE EXCEPTION 'injected failure audit outage'; END IF; RETURN NEW; END$$""")
            )
            s.execute(
                text(
                    "CREATE TRIGGER reject_failure_audit BEFORE INSERT ON audit_events FOR EACH "
                    "ROW EXECUTE FUNCTION reject_failure_audit()"
                )
            )
            s.commit()
        failed = outsider.post(
            "/api/v1/auth/login",
            json={
                "login_id": "master.test",
                "password": "가상 틀린 암호 " + secrets.token_urlsafe(20),
            },
            headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
        )
        assert failed.status_code == 503
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='pending'")
                ).scalar_one()
                == 1
            )
            s.execute(text("DROP TRIGGER reject_failure_audit ON audit_events"))
            s.execute(
                text(
                    "UPDATE iam_attempts SET lease_until=clock_timestamp()-interval '1 second' "
                    "WHERE outcome='pending'"
                )
            )
            s.commit()
        wrong = outsider.post(
            "/api/v1/auth/login",
            json={
                "login_id": "master.test",
                "password": "새 가상 틀린 암호 " + secrets.token_urlsafe(20),
            },
            headers={"Origin": ORIGIN, "X-CSRF-Token": pre},
        )
        assert wrong.status_code == 401
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
                ).scalar_one()
                == 2
            )
            audit = s.execute(
                text(
                    "SELECT actor_id,target_id,organization_id,actor_role FROM audit_events "
                    "WHERE action='login' AND NOT success"
                )
            ).one()
            assert audit.actor_id is None and audit.target_id and audit.organization_id
            assert audit.actor_role == "LOGIN_ATTEMPT"
        outsider.close()


def test_concurrent_setup_single_consumption(
    iam: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import concurrent.futures
    import threading

    from y3management.contracts import Rejected
    from y3management.iam.passwords import Passwords

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        m = login(master, "master.test", password)
        branch = master.post(
            "/api/v1/admin/branches",
            json={"code": "A", "name": "A"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()["id"]
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "setup.race", "branch_id": branch},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()
        token = urlsplit(issued["setup_link"]).fragment[6:]
        service = app.state.iam_service
        preparations = [service.csrf(None, None) for _ in range(2)]
        gate = threading.Barrier(2)
        original = Passwords.create

        def create(engine: Passwords, value: str, identifier: str) -> str:
            gate.wait(timeout=10)
            return original(engine, value, identifier)

        monkeypatch.setattr(Passwords, "create", create)
        password2 = "한 번만 설정할 가상 암호 " + secrets.token_urlsafe(24)

        def complete(index: int) -> int:
            nonce, pre = preparations[index]
            try:
                service.complete(token, password2, pre, nonce)
                return 204
            except Rejected as e:
                return e.status

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(complete, range(2)))
        assert sorted(outcomes) == [204, 400]
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='setup_complete'")
                ).scalar_one()
                == 1
            )
            assert s.execute(
                text(
                    "SELECT state,row_version,security_version FROM iam_accounts WHERE "
                    "login_id='setup.race'"
                )
            ).one() == ("ACTIVE", 2, 2)


def test_session_rows_and_slots_are_bounded_and_reclaimed(
    iam: tuple[Settings, Database, str],
) -> None:
    from sqlalchemy.exc import IntegrityError

    from y3management.uow import UnitOfWork

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        login(master, "master.test", password)
        with pytest.raises(IntegrityError), db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_security_states SET expires_at=expires_at-interval '1 hour' "
                    "WHERE kind='session_slot'"
                )
            )
            s.commit()
        with db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 "
                    "minutes', last_activity=clock_timestamp()-interval '31 minutes'"
                )
            )
            s.execute(
                text(
                    "UPDATE iam_security_states SET created_at=clock_timestamp()-interval '31 "
                    "seconds' WHERE kind='session_slot'"
                )
            )
            s.commit()
        assert master.get("/api/v1/auth/me").status_code == 401
        uow = UnitOfWork(db, settings)
        with uow.open() as w:
            w.iam.gc_sessions()
        with uow.open() as w:
            w.security.preparation(None)
        with db.session() as s:
            assert s.execute(text("SELECT count(*) FROM iam_sessions")).scalar_one() == 0
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_security_states WHERE kind='session_slot'")
                ).scalar_one()
                == 0
            )


def test_login_snapshot_then_disable_and_wait_expiry(
    iam: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import threading

    from sqlalchemy import event as sql_event
    from sqlalchemy.engine import Connection

    from y3management.contracts import Rejected
    from y3management.iam.infrastructure import IAM
    from y3management.iam.public import LoginProof

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        m = login(master, "master.test", password)
        branch = master.post(
            "/api/v1/admin/branches",
            json={"code": "A", "name": "A"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()["id"]
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "snapshot.test", "branch_id": branch},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()
        ident = UUID(issued["account_id"])
        token = urlsplit(issued["setup_link"]).fragment[6:]
        service = app.state.iam_service
        nonce, pre = service.csrf(None, None)
        pw = SyntheticSecret("검증 후 차단 경합 " + secrets.token_urlsafe(24))
        service.complete(token, pw, pre, nonce)
        nonce, pre = service.csrf(None, None)
        verified = threading.Event()
        release = threading.Event()
        outcomes = []
        original = IAM.verify_login

        def verify(adapter: IAM, identifier: str, value: str) -> LoginProof | None:
            proof = original(adapter, identifier, value)
            verified.set()
            assert release.wait(10)
            return proof

        def login_worker() -> None:
            try:
                service.login("snapshot.test", pw, pre, nonce, None)
                outcomes.append(204)
            except Rejected as e:
                outcomes.append(e.status)

        with monkeypatch.context() as patch:
            patch.setattr(IAM, "verify_login", verify)
            worker = threading.Thread(target=login_worker)
            worker.start()
            try:
                assert verified.wait(10)
                service.change(master.cookies.get("__Host-y3-auth"), m, ident, 2, disable=True)
            finally:
                release.set()
                worker.join(10)
        assert outcomes == [401]
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
                    {"a": ident},
                ).scalar_one()
                == 0
            )
        # Real idle deadline passes while an independent worker is blocked on Account SHARE.
        auth = master.cookies.get("__Host-y3-auth")
        with db.session() as s:
            actor = s.execute(
                text("SELECT id FROM iam_accounts WHERE login_id='master.test'")
            ).scalar_one()
            s.execute(
                text(
                    "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '1 hour', "
                    "last_activity=clock_timestamp()-interval '29 minutes 59 seconds' "
                    "WHERE account_id=:a"
                ),
                {"a": actor},
            )
            expiry = s.execute(
                text(
                    "SELECT last_activity+interval '30 minutes' FROM iam_sessions "
                    "WHERE account_id=:a"
                ),
                {"a": actor},
            ).scalar_one()
            s.commit()
        entered = threading.Event()
        pids = []
        result = []

        def observe(
            connection: Connection,
            cursor: object,
            statement: str,
            parameters: object,
            context: object,
            many: bool,
        ) -> None:
            if (
                threading.current_thread().name == "expiry-reader"
                and "iam_accounts" in statement
                and "FOR SHARE" in statement
            ):
                driver = connection.connection.driver_connection
                assert driver is not None
                pids.append(driver.info.backend_pid)
                entered.set()

        def read() -> None:
            try:
                service.me(auth)
                result.append(200)
            except Rejected as e:
                result.append(e.status)

        sql_event.listen(db.engine, "before_cursor_execute", observe)
        reader = threading.Thread(target=read, name="expiry-reader")
        try:
            with db.session() as holder:
                holder.execute(
                    text("SELECT id FROM iam_accounts WHERE id=:a FOR UPDATE"), {"a": actor}
                )
                reader.start()
                assert entered.wait(2)
                blocked = False
                deadline = time.monotonic() + 1.4
                while time.monotonic() < deadline:
                    with db.session() as inspector:
                        blocked = bool(
                            inspector.execute(
                                text("SELECT pg_blocking_pids(:p)"), {"p": pids[0]}
                            ).scalar_one()
                        )
                        started = inspector.execute(
                            text("SELECT xact_start FROM pg_stat_activity WHERE pid=:p"),
                            {"p": pids[0]},
                        ).scalar_one()
                        now = inspector.execute(text("SELECT clock_timestamp()")).scalar_one()
                    if blocked and now >= expiry:
                        break
                    time.sleep(0.01)
                assert blocked and started < expiry and now >= expiry
                holder.commit()
            reader.join(5)
            assert result == [401]
        finally:
            if reader.ident:
                reader.join(5)
            sql_event.remove(db.engine, "before_cursor_execute", observe)


def test_setup_snapshot_then_reissue(
    iam: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import threading

    from y3management.contracts import Rejected
    from y3management.iam.passwords import Passwords

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        m = login(master, "master.test", password)
        branch = master.post(
            "/api/v1/admin/branches",
            json={"code": "A", "name": "A"},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()["id"]
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "reissue.race", "branch_id": branch},
            headers={"Origin": ORIGIN, "X-CSRF-Token": m},
        ).json()
        ident = UUID(issued["account_id"])
        token = urlsplit(issued["setup_link"]).fragment[6:]
        service = app.state.iam_service
        nonce, pre = service.csrf(None, None)
        hashed = threading.Event()
        release = threading.Event()
        outcomes = []
        original = Passwords.create

        def create(engine: Passwords, value: str, identifier: str) -> str:
            encoded = original(engine, value, identifier)
            hashed.set()
            assert release.wait(10)
            return encoded

        pw = SyntheticSecret("링크 재발급 경합 " + secrets.token_urlsafe(24))

        def complete() -> None:
            try:
                service.complete(token, pw, pre, nonce)
                outcomes.append(204)
            except Rejected as e:
                outcomes.append(e.status)

        with monkeypatch.context() as patch:
            patch.setattr(Passwords, "create", create)
            worker = threading.Thread(target=complete)
            worker.start()
            try:
                assert hashed.wait(10)
                account, new_setup = service.reissue(
                    master.cookies.get("__Host-y3-auth"), m, ident, 1
                )
                assert account.version == 2
            finally:
                release.set()
                worker.join(10)
        assert outcomes == [400]
        with db.session() as s:
            assert s.execute(
                text("SELECT state,password_hash,row_version FROM iam_accounts WHERE id=:a"),
                {"a": ident},
            ).one() == ("PENDING_SETUP", None, 2)
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='setup_complete'")
                ).scalar_one()
                == 0
            )
        service.complete(new_setup.token, pw, pre, nonce)
        with pytest.raises(Rejected) as stale:
            service.reissue(master.cookies.get("__Host-y3-auth"), m, ident, 2)
        assert stale.value.status == 409


@pytest.mark.parametrize("first_action", ["login", "setup_complete"])
def test_business_commit_precedes_waiting_management(
    iam: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
    first_action: str,
) -> None:
    """Observe the real losing PostgreSQL backend blocked by the winning UoW."""
    import concurrent.futures
    import threading

    from sqlalchemy import event as sql_event
    from sqlalchemy.engine import Connection

    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import Event
    from y3management.contracts import Rejected
    from y3management.use_cases import Service

    settings, db, password = iam
    app = create_app(settings, database=db)
    with TestClient(app, base_url=ORIGIN) as master:
        nonce = login(master, "master.test", password)
        headers = {"Origin": ORIGIN, "X-CSRF-Token": nonce}
        branch = master.post(
            "/api/v1/admin/branches", json={"code": "A", "name": "A"}, headers=headers
        ).json()["id"]
        issued = master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "winner.test", "branch_id": branch},
            headers=headers,
        ).json()
        ident = UUID(issued["account_id"])
        token = urlsplit(issued["setup_link"]).fragment[6:]
        service: Service = app.state.iam_service
        pw = SyntheticSecret("실제 잠금 선행 경합 " + secrets.token_urlsafe(24))
        setup_nonce, setup_pre = service.csrf(None, None)
        if first_action == "login":
            service.complete(token, pw, setup_pre, setup_nonce)
        request_nonce, request_pre = service.csrf(None, None)
        auth = master.cookies.get("__Host-y3-auth")
        held, release, entered = threading.Event(), threading.Event(), threading.Event()
        holder_pids: list[int] = []
        waiter_pids: list[int] = []
        original = Audit.append

        def append(adapter: Audit, value: Event) -> None:
            original(adapter, value)
            if value.action == first_action and value.target_id == ident:
                holder_pids.append(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
                held.set()
                assert release.wait(10), "Winning transaction release timeout"

        def observe(
            connection: Connection,
            cursor: object,
            statement: str,
            parameters: object,
            context: object,
            many: bool,
        ) -> None:
            if (
                threading.current_thread().name.startswith("management-waiter")
                and "iam_accounts" in statement
                and "FOR UPDATE" in statement
            ):
                driver = connection.connection.driver_connection
                assert driver is not None
                waiter_pids.append(driver.info.backend_pid)
                entered.set()

        def first() -> str | None:
            if first_action == "login":
                return service.login("winner.test", pw, request_pre, request_nonce, None)
            service.complete(token, pw, setup_pre, setup_nonce)
            return None

        def management() -> int:
            try:
                if first_action == "login":
                    service.change(auth, nonce, ident, 2, disable=True)
                else:
                    service.reissue(auth, nonce, ident, 1)
                return 200
            except Rejected as error:
                return error.status

        with monkeypatch.context() as patch:
            patch.setattr(Audit, "append", append)
            sql_event.listen(db.engine, "before_cursor_execute", observe)
            try:
                with (
                    concurrent.futures.ThreadPoolExecutor(max_workers=1) as winner_pool,
                    concurrent.futures.ThreadPoolExecutor(
                        max_workers=1, thread_name_prefix="management-waiter"
                    ) as waiter_pool,
                ):
                    winner = winner_pool.submit(first)
                    try:
                        assert held.wait(5), "Business transaction did not acquire locks"
                        waiter = waiter_pool.submit(management)
                        assert entered.wait(5), "Management did not reach account lock"
                        deadline = time.monotonic() + 3
                        blocked_by_winner = False
                        while time.monotonic() < deadline:
                            with db.session() as inspector:
                                blockers = inspector.execute(
                                    text("SELECT pg_blocking_pids(:p)"), {"p": waiter_pids[-1]}
                                ).scalar_one()
                            if holder_pids[0] in blockers:
                                blocked_by_winner = True
                                break
                            time.sleep(0.01)
                        assert blocked_by_winner, "Expected PostgreSQL blocking relation absent"
                        assert not waiter.done()
                    finally:
                        release.set()
                    issued_cookie = winner.result(timeout=10)
                    assert waiter.result(timeout=10) == (200 if first_action == "login" else 409)
            finally:
                release.set()
                sql_event.remove(db.engine, "before_cursor_execute", observe)
        if first_action == "login":
            assert issued_cookie is not None
            assert (
                master.get(
                    "/api/v1/auth/me", headers={"Cookie": "__Host-y3-auth=" + issued_cookie}
                ).status_code
                == 401
            )
            with db.session() as s:
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"
                        ),
                        {"a": ident},
                    ).scalar_one()
                    == 0
                )
        else:
            with db.session() as s:
                assert s.execute(
                    text("SELECT state,row_version FROM iam_accounts WHERE id=:a"), {"a": ident}
                ).one() == ("ACTIVE", 2)
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM audit_events WHERE target_id=:a "
                            "AND action='setup_reissue'"
                        ),
                        {"a": ident},
                    ).scalar_one()
                    == 0
                )
        assert master.get("/api/v1/auth/me").status_code == 200
