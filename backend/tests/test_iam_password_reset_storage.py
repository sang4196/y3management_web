# ruff: noqa: F811
"""New revision preserves old data and refuses destructive reset-history downgrade."""

import hashlib
import json
import subprocess
import sys
from contextlib import closing
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from tests.test_iam import ORIGIN, child_env
from tests.test_iam_mfa import Authenticator, enroll, login_mfa, mfa, protect  # noqa: F401
from tests.test_iam_mfa_management_migration import migrate
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_password_reset import reset_request
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.security import Security

pytestmark = pytest.mark.postgres


def fingerprint(db: Database) -> str:
    with db.session() as s:
        data = protect(
            {
                t: sorted(s.execute(text(f"SELECT row_to_json(t)::text FROM {t} t")).scalars())
                for t in (
                    "iam_accounts",
                    "iam_passkeys",
                    "iam_admin_grants",
                    "iam_login_ids",
                    "iam_reset_credentials",
                    "iam_security_states",
                    "audit_events",
                    "alembic_version",
                )
            }
        )
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def test_reset_empty_roundtrip(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, _, _ = mfa
    before = fingerprint(db)
    assert migrate(settings, "downgrade", "0006_iam_mfa_management") == 0
    assert migrate(settings, "upgrade", "head") == 0
    assert fingerprint(db) == before


@pytest.mark.parametrize(
    "seed",
    ["pending", "generation", "source", "parent", "start", "reissue", "complete", "metadata"],
)
def test_reset_each_downgrade_guard(mfa: tuple[Settings, Database, str, str], seed: str) -> None:
    settings, db, _, _ = mfa
    with db.session() as s:
        account = s.execute(text("SELECT id,organization_id FROM iam_accounts")).one()
        if seed == "pending":
            s.execute(
                text(
                    "UPDATE iam_accounts SET password_reset_pending=true,"
                    "password_hash=NULL,reset_generation=1"
                )
            )
        elif seed == "generation":
            s.execute(text("UPDATE iam_accounts SET reset_generation=1"))
        elif seed in ("source", "parent"):
            ident = uuid4()
            s.execute(
                text(
                    "INSERT INTO iam_security_states(id,kind,expires_at) VALUES(:i,"
                    "'password_reset',clock_timestamp()+interval '30 minutes')"
                ),
                {"i": ident},
            )
            if seed == "source":
                s.execute(
                    text(
                        "INSERT INTO iam_reset_credentials(id,account_id,digest,"
                        "row_version,security_version,generation,expires_at) "
                        "VALUES(:i,:a,:d,1,1,1,clock_timestamp())"
                    ),
                    {"i": ident, "a": account.id, "d": b"x" * 32},
                )
        else:
            s.execute(
                text(
                    "INSERT INTO audit_events(id,organization_id,target_id,action,"
                    "success,request_id,before_password_ready) VALUES(:id,:o,:a,"
                    ":action,true,:r,:ready)"
                ),
                {
                    "id": uuid4(),
                    "o": account.organization_id,
                    "a": account.id,
                    "action": "login" if seed == "metadata" else "password_reset_" + seed,
                    "r": uuid4(),
                    "ready": True if seed == "metadata" else None,
                },
            )
        s.commit()
    before = fingerprint(db)
    assert migrate(settings, "downgrade", "0006_iam_mfa_management") != 0
    assert fingerprint(db) == before


@pytest.mark.parametrize(
    "change",
    [
        "password_hash=NULL",
        "password_reset_pending=true",
        "reset_generation=-1",
        "state='PENDING_SETUP'",
    ],
)
def test_reset_readiness_constraints(mfa: tuple[Settings, Database, str, str], change: str) -> None:
    _, db, _, _ = mfa
    with db.session() as s, pytest.raises(IntegrityError):
        s.execute(text("UPDATE iam_accounts SET " + change))
        s.commit()


def test_reset_gc_locked_source_then_cleanup_preserves_pending(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            assert reset_request(first, ident).status_code == 201
            with db.session() as s:
                source = s.execute(
                    text("SELECT id FROM iam_reset_credentials WHERE account_id=:a"), {"a": ident}
                ).scalar_one()
                s.execute(
                    text(
                        "UPDATE iam_reset_credentials SET expires_at=clock_timestamp() WHERE id=:id"
                    ),
                    {"id": source},
                )
                s.commit()
            with db.session() as business:
                business.execute(
                    text("SELECT id FROM iam_reset_credentials WHERE id=:id FOR UPDATE"),
                    {"id": source},
                ).one()
                with db.session() as gc:
                    gc.execute(text("SET LOCAL lock_timeout='300ms'"))
                    blocked = False
                    try:
                        Security(gc, settings.iam_key.get_secret_value(), 2048, 128).allocate("mfa")
                        gc.commit()
                    except DBAPIError:
                        blocked = True
                        gc.rollback()
                    assert not blocked, "GC waited on a locked reset source"
                assert (
                    business.execute(
                        text("SELECT count(*) FROM iam_reset_credentials WHERE id=:id"),
                        {"id": source},
                    ).scalar_one()
                    == 1
                )
            with db.session() as gc:
                Security(gc, settings.iam_key.get_secret_value(), 2048, 128).allocate("mfa")
                gc.commit()
                assert (
                    gc.execute(
                        text("SELECT count(*) FROM iam_reset_credentials WHERE id=:id"),
                        {"id": source},
                    ).scalar_one()
                    == 0
                )
                assert gc.execute(
                    text(
                        "SELECT password_reset_pending AND password_hash IS NULL "
                        "FROM iam_accounts WHERE id=:a"
                    ),
                    {"a": ident},
                ).scalar_one()
            state = first.get("/api/v1/admin/accounts/" + ident + "/password-reset").json()
            assert state["password_reset_pending"] and state["expires_at"] is None
            assert reset_request(first, ident, reissue=True).status_code == 201


@pytest.mark.parametrize("mfa", [False], indirect=True)
def test_reset_downgrade_waits_for_inflight_allocation(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    import time

    from tests.conftest import qa_register_process, qa_stop_process
    from y3management.iam.security import Security

    settings, db, _, _ = mfa
    with db.session() as allocation:
        security = Security(allocation, settings.iam_key.get_secret_value(), 2048, 128)
        security.allocate("password_reset")
        allocator_pid = allocation.execute(text("SELECT pg_backend_pid()")).scalar_one()
        migration_app = "reset-downgrade-" + uuid4().hex
        env = child_env(settings)
        env["PGAPPNAME"] = migration_app
        process = subprocess.Popen(
            [sys.executable, "-m", "alembic", "downgrade", "0006_iam_mfa_management"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        qa_register_process(process)
        try:
            deadline = time.monotonic() + 5
            waiting = False
            while time.monotonic() < deadline and process.poll() is None:
                with db.session() as observer:
                    waiting = bool(
                        observer.execute(
                            text(
                                "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
                                "WHERE datname=current_database() AND wait_event_type='Lock' "
                                "AND application_name=:application_name "
                                "AND pid<>:allocator_pid "
                                "AND :allocator_pid=ANY(pg_blocking_pids(pid)))"
                            ),
                            {"application_name": migration_app, "allocator_pid": allocator_pid},
                        ).scalar_one()
                    )
                if waiting:
                    break
                time.sleep(0.02)
            assert waiting, "Migration did not wait on the real allocation transaction"
            allocation.commit()
            expected = fingerprint(db)
            process.communicate(timeout=10)
            assert process.returncode != 0
            assert fingerprint(db) == expected
        finally:
            qa_stop_process(process)
