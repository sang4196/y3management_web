# ruff: noqa: F811
"""Emergency isolation, durable history, real crypto races and commit failures."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from threading import Event as Signal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_emergency import facts, issue, operator, request
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management_races import provision
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import CommitUncertain, Rejected
from y3management.database import Database
from y3management.iam.mfa import MFA
from y3management.iam.public import RegistrationProof, Setup
from y3management.runtime import ProcessGuard

pytestmark = pytest.mark.postgres


def test_permissions_and_causal_reissue(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        first = request(service, principal, ident)
        with pytest.raises(Rejected):
            issue(service, replace(principal, operations=frozenset({"inspect"})), first)
        execute_only = replace(principal, operations=frozenset({"execute"}))
        issue(service, execute_only, first)
        second = request(service, principal, ident, supersedes=first.operation_id)
        issue(service, execute_only, second)
        # Simulate equal database timestamps without changing causal row versions.
        with db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_emergency_cases SET issued_at=(SELECT min(issued_at) "
                    "FROM iam_emergency_cases),checked_at=(SELECT min(checked_at) "
                    "FROM iam_emergency_cases),expires_at=(SELECT min(expires_at) "
                    "FROM iam_emergency_cases)"
                )
            )
            s.commit()
        third = request(service, principal, ident, supersedes=second.operation_id)
        issue(service, execute_only, third)
        assert service.emergency_status(principal, third.operation_id).status == "issued"


def test_other_account_and_c2_unchanged(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        login_mfa(client, password, key)
        with closing(TestClient(client.app, base_url=ORIGIN)) as other:
            other_id, _ = provision(client, other, password)
            service, principal, ident = operator(settings, db, tmp_path / "operator")
            req = request(service, principal, ident)
            with db.session() as s:
                # The other account also has expired state. AB5 must not collect it.
                s.execute(
                    text(
                        "UPDATE iam_mfa_contexts "
                        "SET expires_at=clock_timestamp()-interval '1 second' "
                        "WHERE account_id=:a"
                    ),
                    {"a": other_id},
                )
                s.commit()

            def snapshot() -> tuple[str, ...]:
                with db.session() as s:
                    values = []
                    for table in (
                        "iam_sessions",
                        "iam_mfa_contexts",
                        "iam_credentials",
                        "iam_recovery_credentials",
                        "iam_reset_credentials",
                        "iam_passkeys",
                    ):
                        values.append(
                            str(
                                s.execute(
                                    text(
                                        f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                                        f"ORDER BY row_to_json(t)::text),'')) FROM {table} t "
                                        "WHERE account_id=:a"
                                    ),
                                    {"a": other_id},
                                ).scalar_one()
                            )
                        )
                    for table in ("iam_budgets", "iam_attempts", "iam_accounts"):
                        condition = " WHERE id=:a" if table == "iam_accounts" else ""
                        values.append(
                            str(
                                s.execute(
                                    text(
                                        f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                                        f"ORDER BY row_to_json(t)::text),'')) FROM {table} t"
                                        + condition
                                    ),
                                    {"a": other_id},
                                ).scalar_one()
                            )
                        )
                    return tuple(values)

            before = snapshot()
            issue(service, principal, req)
            assert snapshot() == before


@pytest.mark.parametrize("failure", ["audit", "db", "ack"])
def test_atomic_issue_failures(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident)
        before = facts(db)
        original, commit = Audit.append, Session.commit

        def audit(adapter: Audit, event: Event) -> None:
            if event.action == "emergency_issue":
                if failure == "audit":
                    raise Rejected(503, "unavailable")
                if failure == "db":
                    adapter.s.execute(text("SELECT * FROM synthetic_missing_emergency_table"))
                adapter.s.info["emergency_ack"] = True
            original(adapter, event)

        def committed(s: Session) -> None:
            commit(s)
            if s.info.pop("emergency_ack", False):
                raise OperationalError("synthetic ACK loss", {}, RuntimeError("ack lost"))

        with monkeypatch.context() as patch:
            patch.setattr(Audit, "append", audit)
            patch.setattr(Session, "commit", committed)
            with pytest.raises(CommitUncertain if failure == "ack" else Rejected):
                issue(service, principal, req)
        if failure == "ack":
            assert service.emergency_status(principal, req.operation_id).status == "issued"
            assert facts(db)["recovery_pending"]
            with pytest.raises(Rejected):
                issue(service, principal, req)
        else:
            assert facts(db) == before
            with db.session() as s:
                assert s.execute(text("SELECT count(*) FROM iam_emergency_cases")).scalar_one() == 0


def test_real_uv_then_reissue_rejects_old_completion(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident, "passkey")
        raw = issue(service, principal, req)
        result = call(
            client, "/auth/emergency-recovery/options", csrf(client), {"emergency_token": raw}
        ).json()
        credential = Authenticator().registration(result["publicKey"])
        verified, release = Signal(), Signal()
        original = MFA.verify_registration

        def held(
            adapter: MFA, token: str | None, nonce: str | None, payload: str
        ) -> RegistrationProof:
            proof = original(adapter, token, nonce, payload)
            verified.set()
            assert release.wait(15)
            return proof

        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
            patch.setattr(MFA, "verify_registration", held)
            pending = pool.submit(
                call,
                client,
                "/auth/emergency-recovery/verify",
                result["csrf_token"],
                {"credential": credential},
            )
            try:
                assert verified.wait(10)
                next_req = request(service, principal, ident, "passkey", req.operation_id)
                issue(service, principal, next_req)
            finally:
                release.set()
            assert pending.result(timeout=15).status_code == 401
        assert facts(db)["recovery_pending"]
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_passkeys WHERE revoked_at IS NULL")
                ).scalar_one()
                == 0
            )


def test_gc_preserves_case_and_locked_child(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident, "passkey")
        raw = issue(service, principal, req)
        assert (
            call(
                client, "/auth/emergency-recovery/options", csrf(client), {"emergency_token": raw}
            ).status_code
            == 200
        )
        with db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_emergency_credentials "
                    "SET expires_at=clock_timestamp()-interval '1 second'"
                )
            )
            s.execute(text("UPDATE iam_mfa_contexts SET consumed=true WHERE purpose='emergency'"))
            s.commit()
        with db.session() as locked:
            locked.execute(
                text("SELECT id FROM iam_mfa_contexts WHERE purpose='emergency' FOR UPDATE")
            ).one()
            with service.uow.open() as w:
                slot = w.security.allocate("mfa")
            with db.session() as s:
                assert (
                    s.execute(text("SELECT count(*) FROM iam_emergency_credentials")).scalar_one()
                    == 1
                )
            locked.rollback()
        with service.uow.open() as w:
            w.security.release(slot)
        with db.session() as s:
            assert (
                s.execute(text("SELECT count(*) FROM iam_emergency_credentials")).scalar_one() == 0
            )
            assert s.execute(text("SELECT count(*) FROM iam_emergency_cases")).scalar_one() == 1
        with pytest.raises(Rejected):
            issue(
                service,
                principal,
                replace(
                    request(service, principal, ident, "passkey", req.operation_id),
                    approval_ref=req.approval_ref,
                ),
            )


@pytest.mark.parametrize("normal", ["password", "passkey"])
def test_normal_pending_requires_explicit_both_scope(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
    normal: str,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            provision(first, second, password)
            service, principal, ident = operator(settings, db, tmp_path / "operator")
            snapshot = service.emergency_inspect(principal, ident)
            if normal == "password":
                path = f"/admin/accounts/{ident}/password-reset"
                payload = {
                    "expected_account_version": snapshot.row_version,
                    "expected_generation": snapshot.reset_generation,
                    "identity_confirmed": True,
                }
                opposite = "passkey"
            else:
                path = f"/admin/accounts/{ident}/passkey-recovery"
                payload = {
                    "expected_account_version": snapshot.row_version,
                    "expected_key_set_version": snapshot.key_set_version,
                    "identity_confirmed": True,
                }
                opposite = "password"
            assert call(second, path, csrf(second), payload).status_code == 201
            before = facts(db)
            from typing import Literal, cast

            with pytest.raises(Rejected):
                issue(
                    service,
                    principal,
                    request(
                        service, principal, ident, cast(Literal["password", "passkey"], opposite)
                    ),
                )
            assert facts(db) == before
            req = request(service, principal, ident)
            issue(service, principal, req)
            assert facts(db)["password_reset_pending"] and facts(db)["recovery_pending"]


@pytest.mark.parametrize("failure", ["audit", "expired", "purpose"])
def test_both_completion_failure_preserves_two_pending(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    import secrets

    from tests.test_iam import SyntheticSecret

    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident)
        raw = issue(service, principal, req)
        password = SyntheticSecret("Emergency validation " + secrets.token_urlsafe(24))
        result = call(
            client,
            "/auth/emergency-recovery/options",
            csrf(client),
            {"emergency_token": raw, "new_password": password},
        ).json()
        before = facts(db)
        credential = Authenticator().registration(result["publicKey"])
        original = Audit.append

        def audit(adapter: Audit, event: Event) -> None:
            if event.action == "emergency_complete":
                raise Rejected(503, "unavailable")
            original(adapter, event)

        if failure == "expired":
            with db.session() as s:
                s.execute(
                    text(
                        "UPDATE iam_mfa_contexts SET expires_at=clock_timestamp() "
                        "WHERE purpose='emergency'"
                    )
                )
                s.commit()
        with monkeypatch.context() as patch:
            if failure == "audit":
                patch.setattr(Audit, "append", audit)
            path = (
                "/auth/passkeys/recovery/verify"
                if failure == "purpose"
                else "/auth/emergency-recovery/verify"
            )
            response = call(client, path, result["csrf_token"], {"credential": credential})
        assert response.status_code == (503 if failure == "audit" else 401)
        assert facts(db) == before
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_passkeys WHERE revoked_at IS NULL")
                ).scalar_one()
                == 0
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_emergency_cases WHERE completed_at IS NOT NULL")
                ).scalar_one()
                == 0
            )


@pytest.mark.parametrize(
    "failure",
    [
        "delivery",
        "ack",
        "close",
        "stdout_write",
        "stdout_flush",
        "db_close",
        "guard_close",
        "ack_stderr",
        "interrupt",
        "system_exit",
    ],
)
def test_cli_actual_commit_unknown_keeps_private_output(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    import json
    import sys
    from dataclasses import asdict

    from y3management import cli

    settings, db, _, token = mfa
    private = tmp_path / "operator"
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, private)
        req = request(service, principal, ident)
    body = asdict(req)
    body.update(
        environment="test",
        database="y3management_test",
        database_schema=settings.database_schema,
        revocation_scope="target_only",
        manual_checks="owner_authority_original_current_recipient_all_masters_unavailable",
        approval_conditions="issuance_only_no_additional_conditions",
    )
    source, output = private / "request", private / "delivery"
    source.write_text(json.dumps(body, default=str))
    source.chmod(0o600)
    configured = settings.model_copy(
        update={
            "emergency_authority_file": str(private / "authority.json"),
            "emergency_test_authority": True,
        }
    )
    original, commit, deliver = Audit.append, Session.commit, cli.PrivateEnrollmentFile.deliver
    close = cli.PrivateEnrollmentFile.close
    db_close, guard_close = Database.close, ProcessGuard.close

    def audit(adapter: Audit, event: Event) -> None:
        original(adapter, event)
        if event.action == "emergency_issue":
            adapter.s.info["emergency_ack"] = True

    def committed(s: Session) -> None:
        commit(s)
        if s.info.pop("emergency_ack", False):
            if failure == "interrupt":
                raise KeyboardInterrupt()
            if failure == "system_exit":
                raise SystemExit(130)
            raise OperationalError("synthetic ACK loss", {}, RuntimeError("ack lost"))

    def delivery(adapter: cli.PrivateEnrollmentFile, setup: Setup) -> None:
        deliver(adapter, setup)
        raise OSError("synthetic fsync failure after write")

    def close_failed(adapter: cli.PrivateEnrollmentFile, *, remove: bool) -> None:
        close(adapter, remove=remove)
        raise OSError("synthetic close failure")

    def database_close_failed(adapter: Database) -> None:
        db_close(adapter)
        raise OSError("synthetic database close failure")

    def guard_close_failed(adapter: ProcessGuard) -> None:
        guard_close(adapter)
        raise OSError("synthetic guard close failure")

    def broken_stream(*args: object, **kwargs: object) -> None:
        raise BrokenPipeError("synthetic receipt or diagnostic sink failure")

    before = facts(db)
    with monkeypatch.context() as patch:
        patch.setattr(cli, "load_settings", lambda: configured)
        patch.setattr(sys.stdin, "isatty", lambda: True)
        patch.setattr(
            sys,
            "argv",
            [
                "cli",
                "emergency-recovery",
                "execute",
                "--organization-id",
                str(req.organization_id),
                "--confirm-database",
                "y3management_test",
                "--confirm-schema",
                settings.database_schema,
                "--request-file",
                str(source),
                "--output-file",
                str(output),
            ],
        )
        if failure in ("ack", "ack_stderr", "interrupt", "system_exit"):
            patch.setattr(Audit, "append", audit)
            patch.setattr(Session, "commit", committed)
            if failure == "ack_stderr":
                patch.setattr(sys.stderr, "write", broken_stream)
        elif failure == "stdout_write":
            patch.setattr(sys.stdout, "write", broken_stream)
        elif failure == "stdout_flush":
            patch.setattr(sys.stdout, "flush", broken_stream)
        elif failure == "db_close":
            patch.setattr(Database, "close", database_close_failed)
        elif failure == "guard_close":
            patch.setattr(ProcessGuard, "close", guard_close_failed)
        elif failure == "close":
            patch.setattr(cli.PrivateEnrollmentFile, "close", close_failed)
        else:
            patch.setattr(cli.PrivateEnrollmentFile, "deliver", delivery)
        assert cli.main() == (1 if failure == "delivery" else 2)
    captured = capsys.readouterr()
    assert "#token=" not in captured.out + captured.err
    if failure != "delivery":
        assert output.exists() and output.stat().st_mode & 0o777 == 0o600
        assert service.emergency_status(principal, req.operation_id).status == "issued"
    else:
        assert not output.exists() and facts(db) == before


def test_migration_roundtrip_and_durable_history_guard(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
) -> None:
    import subprocess
    import sys

    from tests.test_iam import child_env

    settings, db, _, token = mfa
    for arguments in [("downgrade", "0007_iam_password_reset"), ("upgrade", "head")]:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            env=child_env(settings),
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, "Emergency empty migration roundtrip failed"
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        raw = issue(service, principal, request(service, principal, ident, "passkey"))
        assert (
            call(
                client, "/auth/emergency-recovery/options", csrf(client), {"emergency_token": raw}
            ).status_code
            == 200
        )
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError), db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_mfa_contexts SET password_hash='synthetic-invalid' "
                    "WHERE purpose='emergency'"
                )
            )
            s.commit()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0007_iam_password_reset"],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    )
    assert result.returncode != 0
    with db.session() as s:
        assert (
            s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0010_workforce_initial"
        )
        assert s.execute(text("SELECT count(*) FROM iam_emergency_cases")).scalar_one() == 1
