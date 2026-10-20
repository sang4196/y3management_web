# ruff: noqa: F811
"""Real provisioned account, hash and WebAuthn through emergency contracts."""

import json
import os
import secrets
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa, protect  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.public import EmergencyRequest, OperatingRecoveryAuthority, Setup
from y3management.operating import authority
from y3management.uow import UnitOfWork
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


def operator(
    settings: Settings, db: Database, path: Path
) -> tuple[Service, OperatingRecoveryAuthority, UUID]:
    with db.session() as s:
        row = s.execute(
            text("SELECT id,organization_id FROM iam_accounts WHERE login_id='master.test'")
        ).one()
    path.mkdir(mode=0o700)
    descriptor = path / "authority.json"
    descriptor.write_text(
        json.dumps(
            {
                "uid": os.getuid(),
                "executor_ref": "qa-executor",
                "environment": "test",
                "database": "y3management_test",
                "database_schema": settings.database_schema,
                "organizations": [str(row.organization_id)],
                "operations": ["inspect", "execute", "status"],
            }
        )
    )
    descriptor.chmod(0o600)
    configured = settings.model_copy(
        update={"emergency_authority_file": str(descriptor), "emergency_test_authority": True}
    )
    return (
        Service(UnitOfWork(db, configured)),
        authority(configured, row.organization_id, "execute"),
        row.id,
    )


def request(
    service: Service,
    principal: OperatingRecoveryAuthority,
    ident: UUID,
    factors: Literal["password", "passkey", "both"] = "both",
    supersedes: UUID | None = None,
) -> EmergencyRequest:
    return EmergencyRequest(
        uuid4(),
        principal.organization_id,
        ident,
        factors,
        service.emergency_inspect(principal, ident),
        "approval-" + uuid4().hex,
        "qa-owner",
        datetime.now(UTC) - timedelta(seconds=1),
        datetime.now(UTC) + timedelta(hours=1),
        supersedes,
    )


def issue(service: Service, principal: OperatingRecoveryAuthority, req: EmergencyRequest) -> str:
    captured: list[str] = []

    def delivery(setup: Setup) -> None:
        captured.append(SyntheticSecret(setup.token))

    service.emergency_issue(principal, req, delivery)
    assert len(captured) == 1
    return captured[0]


def facts(db: Database) -> dict[str, Any]:
    with db.session() as s:
        row = (
            s.execute(
                text(
                    "SELECT password_reset_pending,recovery_pending,"
                    "password_hash IS NOT NULL AS ready,"
                    "row_version,security_version,key_set_version,"
                    "reset_generation,recovery_generation "
                    "FROM iam_accounts WHERE login_id='master.test'"
                )
            )
            .mappings()
            .one()
        )
        return dict(row)


@pytest.mark.parametrize("factors", ["password", "passkey", "both"])
def test_factors_real_uv_atomic_completion(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
    factors: Literal["password", "passkey", "both"],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        old = Authenticator()
        enroll(client, token, old)
        login_mfa(client, password, old)
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident, factors)
        raw = issue(service, principal, req)
        assert client.get("/api/v1/auth/me").status_code == 401
        issued = facts(db)
        assert issued["password_reset_pending"] == (factors in ("password", "both"))
        assert issued["recovery_pending"] == (factors in ("passkey", "both"))
        new = SyntheticSecret("Emergency new password " + secrets.token_urlsafe(24))
        nonce = csrf(client)
        assert (
            call(
                client, "/auth/emergency-recovery/inspect", nonce, {"emergency_token": raw}
            ).status_code
            == 200
        )
        key = Authenticator()
        if factors == "password":
            response = call(
                client,
                "/auth/emergency-recovery/password/complete",
                nonce,
                {"emergency_token": raw, "new_password": new},
            )
        else:
            body = {"emergency_token": raw, **({"new_password": new} if factors == "both" else {})}
            response = call(client, "/auth/emergency-recovery/options", nonce, body)
            assert response.status_code == 200
            options = response.json()
            assert facts(db) == issued
            assert (
                call(
                    client,
                    "/auth/emergency-recovery/verify",
                    options["csrf_token"],
                    {"credential": key.registration(options["publicKey"], uv=False)},
                ).status_code
                == 401
            )
            assert facts(db) == issued
            response = call(
                client,
                "/auth/emergency-recovery/verify",
                options["csrf_token"],
                {"credential": key.registration(options["publicKey"])},
            )
        assert response.status_code == 204
        after = facts(db)
        assert (
            not after["password_reset_pending"] and not after["recovery_pending"] and after["ready"]
        )
        assert client.get("/api/v1/auth/me").status_code == 401
        assert service.emergency_status(principal, req.operation_id).status == "completed"
        assert (
            call(
                client, "/auth/emergency-recovery/inspect", csrf(client), {"emergency_token": raw}
            ).status_code
            == 401
        )
        # Preserve revoked cookie through the real password+UV flow.
        login = call(
            client,
            "/auth/login",
            csrf(client),
            {"login_id": "master.test", "password": password if factors == "passkey" else new},
        )
        assert login.status_code == 200
        data = login.json()
        assert (
            call(
                client,
                "/auth/login/passkey/verify",
                data["csrf_token"],
                {
                    "credential": (old if factors == "password" else key).assertion(
                        data["publicKey"]
                    )
                },
            ).status_code
            == 204
        )
        assert client.get("/api/v1/auth/me").status_code == 200
        with db.session() as s:
            assert (
                s.execute(
                    text(
                        "SELECT count(*) FROM audit_events WHERE action IN "
                        "('emergency_issue','emergency_complete')"
                    )
                ).scalar_one()
                == 2
            )


def test_issue_stale_approval_reissue_and_rollback(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident)
        before = facts(db)
        for invalid in (
            replace(req, approval_valid_until=datetime.now(UTC) - timedelta(seconds=1)),
            replace(req, expected=replace(req.expected, row_version=999)),
            replace(req, owner_ref=principal.executor_ref),
        ):
            with pytest.raises(Rejected):
                issue(service, principal, invalid)
            assert facts(db) == before

        def failed_delivery(setup: Setup) -> None:
            raise OSError("synthetic delivery failure")

        with pytest.raises(OSError):
            service.emergency_issue(principal, req, failed_delivery)
        assert facts(db) == before
        first = issue(service, principal, req)
        with pytest.raises(Rejected):
            issue(service, principal, request(service, principal, ident))
        with pytest.raises(Rejected):
            issue(
                service, principal, request(service, principal, ident, "password", req.operation_id)
            )
        next_req = request(service, principal, ident, supersedes=req.operation_id)
        second = issue(service, principal, next_req)
        assert first != second
        assert service.emergency_status(principal, req.operation_id).status == "superseded"
        assert (
            call(
                client, "/auth/emergency-recovery/inspect", csrf(client), {"emergency_token": first}
            ).status_code
            == 401
        )


@pytest.mark.parametrize(
    "column",
    ["organization_id", "target_id", "approval_mode", "actor_role", "actor_scope", "actor_id"],
)
def test_audit_null_metadata_rejected(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path, column: str
) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident, "password")
        raw = issue(service, principal, req)
        response = call(
            client,
            "/auth/emergency-recovery/password/complete",
            csrf(client),
            {
                "emergency_token": raw,
                "new_password": SyntheticSecret("Audit validation " + secrets.token_urlsafe(24)),
            },
        )
        assert response.status_code == 204
        with pytest.raises(IntegrityError), db.session() as s:
            s.execute(
                text(f"UPDATE audit_events SET {column}=NULL WHERE action='emergency_complete'")
            )
            s.commit()


def cli_execute(
    settings: Settings,
    private: Path,
    req: EmergencyRequest,
    *,
    success: bool = True,
    broken_stdout: bool = False,
    broken_stderr: bool = False,
    expected_code: int | None = None,
) -> Path:
    import pty
    import subprocess
    import sys
    from dataclasses import asdict

    from tests.conftest import qa_register_process, qa_stop_process
    from tests.test_iam import child_env

    body = asdict(req)
    body.update(
        environment="test",
        database="y3management_test",
        database_schema=settings.database_schema,
        revocation_scope="target_only",
        manual_checks="owner_authority_original_current_recipient_all_masters_unavailable",
        approval_conditions="issuance_only_no_additional_conditions",
    )
    request_file = private / ("request-" + req.operation_id.hex + ".json")
    request_file.write_text(json.dumps(body, default=str))
    request_file.chmod(0o600)
    output = private / ("delivery-" + req.operation_id.hex)
    master, slave = pty.openpty()
    env = protect(child_env(settings))
    env["Y3_CANONICAL_ORIGIN"] = settings.canonical_origin
    env["Y3_EMERGENCY_AUTHORITY_FILE"] = str(private / "authority.json")
    env["Y3_EMERGENCY_TEST_AUTHORITY"] = "true"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "y3management.cli",
            "emergency-recovery",
            "execute",
            "--organization-id",
            str(req.organization_id),
            "--confirm-database",
            "y3management_test",
            "--confirm-schema",
            settings.database_schema,
            "--request-file",
            str(request_file),
            "--output-file",
            str(output),
        ],
        stdin=slave,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    qa_register_process(process)
    os.close(slave)
    try:
        if broken_stdout:
            assert process.stdout is not None
            process.stdout.close()
            process.stdout = None
        if broken_stderr:
            assert process.stderr is not None
            process.stderr.close()
            process.stderr = None
        stdout, stderr = process.communicate(timeout=30)
        wanted = expected_code if expected_code is not None else (0 if success else 1)
        assert process.returncode == wanted, "Emergency CLI outcome mismatch"
        assert b"#token=" not in (stdout or b"") + (stderr or b"")
    finally:
        qa_stop_process(process)
        os.close(master)
    return output


def test_real_cli_process_guard_and_protected_delivery(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    settings, db, _, token = mfa
    private = tmp_path / "operator"
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        service, principal, ident = operator(settings, db, private)
        req = request(service, principal, ident)
        before = facts(db)
        assert not cli_execute(settings, private, req, success=False).exists()
        assert facts(db) == before
    descriptor = private / "authority.json"
    policy = json.loads(descriptor.read_text())
    policy["operations"] = ["inspect"]
    descriptor.write_text(json.dumps(policy))
    assert not cli_execute(settings, private, req, success=False).exists()
    assert facts(db) == before
    policy["operations"] = ["execute"]
    descriptor.write_text(json.dumps(policy))
    output = cli_execute(settings, private, req)
    assert output.stat().st_mode & 0o777 == 0o600
    delivery_text = SyntheticSecret(output.read_text())
    assert "/emergency-recover#token=" in delivery_text
    assert service.emergency_status(principal, req.operation_id).status == "issued"


@pytest.mark.parametrize("broken_stderr", [False, True])
def test_real_cli_closed_stdout_pipe_preserves_commit(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
    broken_stderr: bool,
) -> None:
    settings, db, password, token = mfa
    private = tmp_path / "operator"
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        login_mfa(client, password, key)
        service, principal, ident = operator(settings, db, private)
        req = request(service, principal, ident)
    output = cli_execute(
        settings, private, req, broken_stdout=True, broken_stderr=broken_stderr, expected_code=2
    )
    assert output.is_file() and output.stat().st_mode & 0o777 == 0o600
    assert service.emergency_status(principal, req.operation_id).status == "issued"
    assert facts(db)["password_reset_pending"] and facts(db)["recovery_pending"]
    with db.session() as s:
        assert s.execute(
            text("SELECT count(*)>0 AND bool_and(revoked) FROM iam_sessions")
        ).scalar_one()
