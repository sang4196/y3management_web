# ruff: noqa: F811
"""Installation COMMIT ambiguity and non-destructive migration guard tests."""

import getpass
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.legacy_helpers import (  # noqa: F401
    assert_revision_loss_guard,
    legacy_allocation,
    legacy_database,
    legacy_master,
)
from tests.password_helpers import login_password
from tests.test_iam import ORIGIN, SyntheticSecret, child_env
from y3management import cli
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("password_app", [False], indirect=True)
@pytest.mark.parametrize("failure", ["audit", "commit_ack"])
def test_cli_failed_or_unknown_commit(
    password_app: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    settings, db, password = password_app
    private = tmp_path / "delivery"
    private.mkdir(mode=0o700)
    output = private / "capability"
    if failure == "audit":
        with db.session() as s:
            s.execute(
                text(
                    "CREATE FUNCTION reject_audit() RETURNS trigger LANGUAGE plpgsql "
                    "AS $$ BEGIN RAISE EXCEPTION 'injected'; END $$"
                )
            )
            s.execute(
                text(
                    "CREATE TRIGGER reject_audit BEFORE INSERT ON audit_events "
                    "FOR EACH ROW EXECUTE FUNCTION reject_audit()"
                )
            )
            s.commit()
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import Event

    original, append = Session.commit, Audit.append

    def marked(adapter: Audit, event: Event) -> None:
        append(adapter, event)
        if event.action == "bootstrap":
            adapter.s.info["bootstrap_ack"] = True

    def commit(session: Session) -> None:
        original(session)
        if session.info.pop("bootstrap_ack", False):
            raise OperationalError("COMMIT", None, RuntimeError("ack lost"))

    with monkeypatch.context() as patch:
        patch.setattr(cli, "load_settings", lambda: settings)
        patch.setattr(sys.stdin, "isatty", lambda: True)
        patch.setattr(getpass, "getpass", lambda prompt: password)
        patch.setattr(
            sys,
            "argv",
            [
                "cli",
                "bootstrap-initial-master",
                "--organization",
                "MFA Test",
                "--login-id",
                "master.test",
                "--confirm-database",
                "y3management_test",
            ],
        )
        if failure == "commit_ack":
            patch.setattr(Audit, "append", marked)
            patch.setattr(Session, "commit", commit)
        code = cli.main()
    captured = capsys.readouterr()
    output_text = SyntheticSecret(captured.out + captured.err)
    del captured
    assert password not in output_text
    with db.session() as s:
        count = s.execute(text("SELECT count(*) FROM iam_accounts")).scalar_one()
    if failure == "audit":
        assert code == 1 and count == 0 and not output.exists()
    else:
        assert code == 2 and count == 1 and not output.exists()
        assert "INSTALLATION_COMMIT_UNKNOWN_VERIFY_EXISTING_INSTALLATION" in output_text
        with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
            login_password(client, password)


def fingerprint(db: Database) -> str:
    tables = [
        "iam_accounts",
        "iam_login_ids",
        "iam_sessions",
        "iam_passkeys",
        "iam_mfa_contexts",
        "iam_security_states",
        "iam_attempts",
        "audit_events",
        "alembic_version",
    ]
    with db.session() as s:
        rows = {
            t: sorted(
                str(v) for v in s.execute(text(f"SELECT row_to_json(t)::text FROM {t} t")).scalars()
            )
            for t in tables
        }
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize("legacy_master", ["0005_iam_mfa"], indirect=True)
@pytest.mark.parametrize("seed", ["empty", "orphan"])
def test_empty_roundtrip_and_orphan_guard(
    legacy_master: tuple[Settings, Database], seed: str
) -> None:
    settings, db = legacy_master
    if seed == "orphan":
        legacy_allocation(db, "mfa")
    before = fingerprint(db)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0004_iam_login_id"],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    )
    assert (result.returncode == 0) == (seed == "empty")
    if seed == "empty":
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "0005_iam_mfa"],
            env=child_env(settings),
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0
    assert fingerprint(db) == before


@pytest.mark.parametrize("legacy_master", ["0005_iam_mfa"], indirect=True)
@pytest.mark.parametrize("seed", ["context", "key", "audit", "assurance", "attempt"])
def test_mfa_downgrade_preserves_each_fact(
    legacy_master: tuple[Settings, Database], seed: str
) -> None:
    settings, db = legacy_master
    with db.session() as session:
        account = session.execute(text("SELECT id FROM iam_accounts")).scalar_one()
    if seed == "context":
        slot = legacy_allocation(db, "mfa")
        with db.session() as session:
            session.execute(
                text(
                    "INSERT INTO iam_mfa_contexts(id,digest,csrf,account_id,purpose,"
                    "security_version,row_version,expires_at) SELECT :i,:d,'synthetic',:a,"
                    "'install',1,1,"
                    "expires_at FROM iam_security_states WHERE id=:i"
                ),
                {"i": slot, "d": bytes(32), "a": account},
            )
            session.commit()
    elif seed == "key":
        with db.session() as session:
            session.execute(
                text(
                    "INSERT INTO iam_passkeys(credential_id,account_id,public_key,"
                    "sign_count,device_type,backed_up) VALUES(:k,:a,:k,0,'single_device',false)"
                ),
                {"k": b"synthetic-key", "a": account},
            )
            session.commit()
    elif seed == "audit":
        with db.session() as session:
            session.execute(
                text(
                    "INSERT INTO audit_events(id,action,success,request_id) "
                    "VALUES(:i,'passkey_register',true,:i)"
                ),
                {"i": uuid4()},
            )
            session.commit()
    elif seed == "assurance":
        slot = legacy_allocation(db, "session_slot")
        with db.session() as session:
            session.execute(
                text(
                    "INSERT INTO iam_sessions(id,account_id,digest,csrf,security_version,"
                    "created_at,last_activity,expires_at,assurance) SELECT :i,:a,:d,'synthetic',1,"
                    "created_at,created_at,expires_at,'password_uv' FROM iam_security_states "
                    "WHERE id=:i"
                ),
                {"i": slot, "a": account, "d": bytes(32)},
            )
            session.commit()
    else:
        budget, slot = legacy_allocation(db, "budget"), legacy_allocation(db, "attempt")
        with db.session() as session:
            session.execute(
                text("INSERT INTO iam_budgets(key,state_id) VALUES(:k,:i)"),
                {"k": bytes(32), "i": budget},
            )
            session.execute(
                text(
                    "INSERT INTO iam_attempts(id,key,outcome,lease_until,stage) "
                    "VALUES(:i,:k,'pending',clock_timestamp()+interval '5 minutes','waiting')"
                ),
                {"i": slot, "k": bytes(32)},
            )
            session.commit()
    before = fingerprint(db)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0004_iam_login_id"],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert_revision_loss_guard(db, "0005_iam_mfa.py", "MFA state or history")
    assert fingerprint(db) == before


@pytest.mark.parametrize("legacy_master", ["0005_iam_mfa"], indirect=True)
def test_downgrade_waits_for_inflight_mfa_allocation(
    legacy_master: tuple[Settings, Database],
) -> None:
    import time

    from tests.conftest import qa_register_process, qa_stop_process

    settings, db = legacy_master
    with db.session() as allocation:
        allocation.execute(
            text(
                "INSERT INTO iam_security_states(id,kind,expires_at) "
                "VALUES(:i,'mfa',clock_timestamp()+interval '30 minutes')"
            ),
            {"i": uuid4()},
        )
        allocator_pid = allocation.execute(text("SELECT pg_backend_pid()")).scalar_one()
        migration_app = "mfa-downgrade-" + uuid4().hex
        env = child_env(settings)
        env["PGAPPNAME"] = migration_app
        process = subprocess.Popen(
            [sys.executable, "-m", "alembic", "downgrade", "0004_iam_login_id"],
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
            assert_revision_loss_guard(db, "0005_iam_mfa.py", "MFA state or history")
            assert fingerprint(db) == expected
        finally:
            qa_stop_process(process)
