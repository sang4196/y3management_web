# ruff: noqa: F811
"""Installation COMMIT ambiguity and non-destructive migration guard tests."""

import getpass
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, SyntheticSecret, child_env
from tests.test_iam_mfa import Authenticator, begin, enroll, login_mfa, mfa  # noqa: F401
from y3management import cli
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.uow import UnitOfWork

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("mfa", [False], indirect=True)
@pytest.mark.parametrize("failure", ["audit", "commit_ack"])
def test_cli_failed_or_unknown_commit(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    settings, db, password, _ = mfa
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
    original = Session.commit
    commits = 0

    def commit(session: Session) -> None:
        nonlocal commits
        commits += 1
        original(session)
        if commits == 2:
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
                "--enrollment-file",
                str(output),
            ],
        )
        if failure == "commit_ack":
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
        assert code == 2 and count == 1 and output.is_file()
        assert "INSTALLATION_COMMIT_UNKNOWN_RETAIN_PRIVATE_FILE" in output_text
        token = SyntheticSecret(output.read_text().strip().split("#token=")[1])
        assert token not in output_text
        with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
            enroll(client, token, Authenticator())


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


@pytest.mark.parametrize("mfa", [False], indirect=True)
@pytest.mark.parametrize("seed", ["empty", "orphan"])
def test_empty_roundtrip_and_orphan_guard(
    mfa: tuple[Settings, Database, str, str], seed: str
) -> None:
    settings, db, _, _ = mfa
    if seed == "orphan":
        with UnitOfWork(db, settings).open() as w:
            w.security.allocate("mfa")
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
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=child_env(settings),
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0
    assert fingerprint(db) == before


@pytest.mark.parametrize("seed", ["context", "key", "audit", "assurance", "attempt"])
def test_mfa_downgrade_preserves_each_fact(
    mfa: tuple[Settings, Database, str, str], seed: str
) -> None:
    settings, db, password, token = mfa
    if seed != "context":
        with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
            key = Authenticator()
            enroll(client, token, key)
            if seed == "assurance":
                login_mfa(client, password, key)
            elif seed == "attempt":
                begin(client, password)
        # Isolate each preservation guard in this owned disposable schema only.
        with db.session() as s:
            s.execute(text("DELETE FROM iam_security_states WHERE kind='mfa'"))
            if seed != "audit":
                s.execute(text("DELETE FROM audit_events WHERE action='passkey_register'"))
            if seed != "key":
                s.execute(text("DELETE FROM iam_passkeys"))
            s.commit()
    before = fingerprint(db)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0004_iam_login_id"],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert fingerprint(db) == before


@pytest.mark.parametrize("mfa", [False], indirect=True)
def test_downgrade_waits_for_inflight_mfa_allocation(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    import time

    from tests.conftest import qa_register_process, qa_stop_process
    from y3management.iam.security import Security

    settings, db, _, _ = mfa
    with db.session() as allocation:
        security = Security(allocation, settings.iam_key.get_secret_value(), 2048, 128)
        security.allocate("mfa")
        process = subprocess.Popen(
            [sys.executable, "-m", "alembic", "downgrade", "0004_iam_login_id"],
            env=child_env(settings),
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
                                "AND query LIKE 'LOCK TABLE iam_accounts%')"
                            )
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
