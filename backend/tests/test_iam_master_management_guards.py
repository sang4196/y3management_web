# ruff: noqa: F811
"""Isolated authorization preconditions and competing real administrator sessions."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier, local
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_master_management import command, snapshot, state
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token
from tests.test_iam_mfa_management_races import provision
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.public import Authentication
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("operation", ["status", "restore", "login-id"])
def test_target_guards_and_existing_branch_routes(
    mfa: tuple[Settings, Database, str, str], operation: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            actor_id = first.get("/api/v1/auth/me").json()["account_id"]
            assert command(first, actor_id, operation, 1).status_code == 404
            assert command(first, str(uuid4()), operation, 1).status_code == 404
            pending = call(
                first, "/admin/master-accounts", csrf(first), {"login_id": "pending.master"}
            ).json()
            assert (
                command(first, pending["account_id"], operation, pending["version"]).status_code
                == 409
            )
            branch = call(first, "/admin/branches", csrf(first), {"code": "A", "name": "A"}).json()
            issued = call(
                first,
                "/admin/accounts",
                csrf(first),
                {"login_id": "branch.test", "branch_id": branch["id"]},
            ).json()
            assert (
                command(first, issued["account_id"], operation, issued["version"]).status_code
                == 404
            )
            # Existing BA routes must continue rejecting a real Master target.
            body = {"expected_version": state(first, ident)["version"]}
            if operation == "status":
                body["status"] = "DISABLED"
            if operation == "login-id":
                body["login_id"] = "changed.master"
            response = first.request(
                "POST" if operation == "restore" else "PATCH",
                "/api/v1/admin/accounts/" + ident + "/" + operation,
                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(first)},
                json=body,
            )
            assert response.status_code == 404
            # A genuinely provisioned Branch Admin is authenticated but not authorized.
            with closing(TestClient(first.app, base_url=ORIGIN)) as branch_actor:
                branch_key = Authenticator()
                enroll(branch_actor, link_token(issued["setup_link"]), branch_key, password)
                login_mfa(branch_actor, password, branch_key, "branch.test")
                assert command(branch_actor, ident, operation, 2).status_code == 403
            with db.session() as s:
                organization = uuid4()
                s.execute(
                    text("INSERT INTO organization_organizations(id,name) VALUES(:i,:n)"),
                    {"i": organization, "n": "Other"},
                )
                s.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": ident})
                s.execute(
                    text("UPDATE iam_accounts SET organization_id=:o WHERE id=:a"),
                    {"o": organization, "a": ident},
                )
                s.execute(
                    text(
                        "INSERT INTO iam_admin_grants(account_id,organization_id,scope) "
                        "VALUES(:a,:o,'ORGANIZATION')"
                    ),
                    {"a": ident, "o": organization},
                )
                s.commit()
            assert command(first, ident, operation, 2).status_code == 404


@pytest.mark.parametrize("operation", ["status", "restore", "login-id"])
@pytest.mark.parametrize("invalid", ["csrf", "weak", "revoked", "idle", "grant", "key"])
def test_actor_guard(
    mfa: tuple[Settings, Database, str, str], operation: str, invalid: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            version = state(first, ident)["version"]
            if operation == "restore":
                assert command(first, ident, "status", version).status_code == 200
                version += 1
            actor_id = first.get("/api/v1/auth/me").json()["account_id"]
            nonce = csrf(first)
            with db.session() as s:
                changes = {
                    "weak": "UPDATE iam_sessions SET assurance='password' WHERE account_id=:a",
                    "revoked": "UPDATE iam_sessions SET revoked=true WHERE account_id=:a",
                    "idle": (
                        "UPDATE iam_sessions SET created_at=created_at-interval '1 hour',"
                        "last_activity=last_activity-interval '31 minutes' WHERE account_id=:a"
                    ),
                    "grant": "DELETE FROM iam_admin_grants WHERE account_id=:a",
                    "key": "UPDATE iam_passkeys SET revoked_at=now() WHERE account_id=:a",
                }
                if invalid in changes:
                    s.execute(text(changes[invalid]), {"a": actor_id})
                    s.commit()
            before = snapshot(db)
            assert command(
                first, ident, operation, version, nonce="bad" if invalid == "csrf" else nonce
            ).status_code == (403 if invalid in ("csrf", "grant") else 401)
            assert snapshot(db) == before


@pytest.mark.parametrize("operation", ["status", "login-id"])
@pytest.mark.parametrize("cross", [True, False])
def test_management_race(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    cross: bool,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            actor = first.get("/api/v1/auth/me").json()["account_id"]
            clients = (first, second if cross else first)
            tokens = [SyntheticSecret(c.cookies.get("__Host-y3-auth") or "") for c in clients]
            nonces = [SyntheticSecret(csrf(c)) for c in clients]
            targets = [UUID(ident), UUID(actor if cross else ident)]
            versions = [
                state(first, ident)["version"],
                state(first, actor if cross else ident)["version"],
            ]
            service: Service = cast(FastAPI, first.app).state.iam_service
            original = IAM.authenticate
            barrier = Barrier(2)
            seen = local()

            def authenticate(adapter: IAM, token: str | None, **kwargs: Any) -> Authentication:
                if kwargs.get("management") and not getattr(seen, "entered", False):
                    seen.entered = True
                    barrier.wait(timeout=10)
                return original(adapter, token, **kwargs)

            def worker(index: int) -> int:
                try:
                    service.manage_master(
                        tokens[index],
                        nonces[index],
                        targets[index],
                        versions[index],
                        "account_disable" if operation == "status" else "login_id_change",
                        "changed." + str(index),
                    )
                    return 200
                except Rejected as error:
                    return error.status

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
                patch.setattr(IAM, "authenticate", authenticate)
                futures = [pool.submit(worker, i) for i in range(2)]
                assert sorted(f.result(timeout=20) for f in futures) == [200, 401 if cross else 409]
            with db.session() as s:
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM iam_accounts WHERE state='ACTIVE' "
                            "AND NOT recovery_pending AND NOT password_reset_pending"
                        )
                    ).scalar_one()
                    >= 1
                )
                assert (
                    s.execute(
                        text("SELECT count(*) FROM audit_events WHERE action=:x"),
                        {"x": "account_disable" if operation == "status" else "login_id_change"},
                    ).scalar_one()
                    == 1
                )


@pytest.mark.parametrize("operation", ["status", "restore", "login-id"])
@pytest.mark.parametrize("expiry", ["idle", "absolute"])
def test_final_actor_expiry_rolls_back(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    expiry: str,
) -> None:
    from datetime import datetime, timedelta

    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            version = state(first, ident)["version"]
            if operation == "restore":
                assert command(first, ident, "status", version).status_code == 200
                version += 1
            nonce = csrf(first)
            actor = first.get("/api/v1/auth/me").json()["account_id"]
            with db.session() as s:
                deadline = s.execute(
                    text("SELECT expires_at FROM iam_sessions WHERE account_id=:a"), {"a": actor}
                ).scalar_one()
                if expiry == "absolute":
                    s.execute(
                        text(
                            "UPDATE iam_sessions SET last_activity=expires_at-interval '1 minute' "
                            "WHERE account_id=:a"
                        ),
                        {"a": actor},
                    )
                    s.commit()
            before = snapshot(db)
            original = IAM.now
            reads = 0

            def now(adapter: IAM) -> datetime:
                nonlocal reads
                reads += 1
                if expiry == "absolute":
                    return cast(datetime, deadline) + (
                        timedelta(seconds=1) if reads == 2 else -timedelta(seconds=30)
                    )
                return original(adapter) + (timedelta(minutes=31) if reads == 2 else timedelta())

            with monkeypatch.context() as patch:
                patch.setattr(IAM, "now", now)
                assert command(first, ident, operation, version, nonce=nonce).status_code == 401
            assert reads == 2
            assert snapshot(db) == before


def test_dto_collision_and_minimal_response(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            version = state(first, ident)["version"]
            nonce = csrf(first)
            before = snapshot(db)
            for body in (
                {"expected_version": True, "login_id": "valid.master"},
                {"expected_version": str(version), "login_id": "valid.master"},
                {"expected_version": version, "login_id": "ab"},
                {"expected_version": version, "login_id": "a" * 65},
                {"expected_version": version, "login_id": " valid.master"},
                {
                    "expected_version": version,
                    "login_id": "valid.master",
                    "organization_id": str(uuid4()),
                },
            ):
                assert (
                    first.patch(
                        "/api/v1/admin/master-accounts/" + ident + "/login-id",
                        headers={"Origin": ORIGIN, "X-CSRF-Token": nonce},
                        json=body,
                    ).status_code
                    == 422
                )
            assert (
                command(first, ident, "login-id", version, "master.test", nonce).status_code == 409
            )
            assert snapshot(db) == before
            response = command(first, ident, "login-id", version, nonce=nonce)
            assert response.status_code == 200
            assert set(response.json()) == {
                "account_id",
                "login_id",
                "state",
                "version",
                "admin_scope",
            }
