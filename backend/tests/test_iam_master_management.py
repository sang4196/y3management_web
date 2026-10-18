# ruff: noqa: F811
"""Actual provisioned other-Master lifecycle and identity commands."""

import hashlib
import json
from contextlib import closing
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import (  # noqa: F401
    Authenticator,
    PrivateResponse,
    begin,
    call,
    enroll,
    login_mfa,
    mfa,
)
from tests.test_iam_mfa_management import link_token, recovery_options, recovery_request
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_password_reset import complete, reset_request
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database

pytestmark = pytest.mark.postgres


def state(client: TestClient, ident: str) -> dict[str, Any]:
    response = client.get("/api/v1/admin/master-accounts/" + ident)
    assert response.status_code == 200
    return dict(response.json())


def command(
    client: TestClient,
    ident: str,
    operation: str,
    version: int,
    identifier: str = "renamed.master",
    nonce: str | None = None,
) -> PrivateResponse:
    body: dict[str, Any] = {"expected_version": version}
    if operation == "status":
        body["status"] = "DISABLED"
    elif operation == "login-id":
        body["login_id"] = identifier
    return PrivateResponse(
        client.request(
            "POST" if operation == "restore" else "PATCH",
            "/api/v1/admin/master-accounts/" + ident + "/" + operation,
            headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(client) if nonce is None else nonce},
            json=body,
        )
    )


def snapshot(db: Database) -> str:
    # Comparison digests only cross the DB boundary, including on helper errors.
    with db.session() as s:
        data = {
            t: s.execute(
                text(
                    f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text, ',' "
                    f"ORDER BY row_to_json(t)::text),'')) FROM {t} t"
                )
            ).scalar_one()
            for t in (
                "iam_accounts",
                "iam_passkeys",
                "iam_admin_grants",
                "iam_login_ids",
                "iam_credentials",
                "iam_mfa_contexts",
                "iam_recovery_credentials",
                "iam_reset_credentials",
                "iam_sessions",
                "audit_events",
            )
        }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def factors(db: Database, ident: str) -> str:
    with db.session() as s:
        account = s.execute(
            text(
                "SELECT md5(row_to_json(a)::text) FROM (SELECT password_hash,key_set_version,"
                "recovery_pending,recovery_generation,password_reset_pending,reset_generation "
                "FROM iam_accounts WHERE id=:a) a"
            ),
            {"a": ident},
        ).scalar_one()
        rows = [account]
        for table in ("iam_passkeys", "iam_admin_grants"):
            rows.append(
                s.execute(
                    text(
                        f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                        f"ORDER BY row_to_json(t)::text),'')) FROM {table} t WHERE account_id=:a"
                    ),
                    {"a": ident},
                ).scalar_one()
            )
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def test_master_lifecycle_id_and_proof_revocation(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor = Authenticator()
        enroll(first, token, actor)
        login_mfa(first, password, actor)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as third,
            closing(TestClient(first.app, base_url=ORIGIN)) as pending,
        ):
            ident, key = provision(first, second, password)
            login_mfa(third, password, key, "second.master")
            proof = begin(pending, password, "second.master")
            add = call(second, "/auth/passkeys/options", csrf(second), {}).json()
            before = factors(db, ident)
            version = state(first, ident)["version"]
            assert command(first, ident, "status", version).status_code == 200
            assert factors(db, ident) == before
            assert first.get("/api/v1/auth/me").status_code == 200
            for client in (second, third):
                assert client.get("/api/v1/auth/me").status_code == 401
            assert (
                call(
                    pending,
                    "/auth/login/passkey/verify",
                    proof["csrf_token"],
                    {"credential": key.assertion(proof["publicKey"])},
                ).status_code
                == 401
            )
            assert (
                call(
                    second,
                    "/auth/passkeys/verify",
                    add["csrf_token"],
                    {"credential": Authenticator().registration(add["publicKey"])},
                ).status_code
                == 401
            )
            assert command(first, ident, "status", version + 1).status_code == 409
            assert command(first, ident, "restore", version + 1).status_code == 200
            assert command(first, ident, "restore", version + 2).status_code == 409
            assert factors(db, ident) == before
            assert second.get("/api/v1/auth/me").status_code == 401
            second.cookies.clear()
            login_mfa(second, password, key, "second.master")
            nonce = csrf(first)
            same = snapshot(db)
            assert (
                command(first, ident, "login-id", version + 2, "SECOND.MASTER", nonce).status_code
                == 200
            )
            assert snapshot(db) == same
            assert (
                command(first, ident, "login-id", version, "SECOND.MASTER", nonce).status_code
                == 409
            )
            assert snapshot(db) == same
            before = factors(db, ident)
            assert command(first, ident, "login-id", version + 2).status_code == 200
            assert factors(db, ident) == before
            assert second.get("/api/v1/auth/me").status_code == 401
            assert (
                call(
                    pending,
                    "/auth/login",
                    csrf(pending),
                    {"login_id": "second.master", "password": password},
                ).status_code
                == 401
            )
            second.cookies.clear()
            login_mfa(second, password, key, "renamed.master")
            assert (
                call(
                    first, "/admin/master-accounts", csrf(first), {"login_id": "second.master"}
                ).status_code
                == 409
            )
            before = factors(db, ident)
            assert (
                command(first, ident, "login-id", version + 3, "second.master").status_code == 200
            )
            assert factors(db, ident) == before
            second.cookies.clear()
            login_mfa(second, password, key, "second.master")


@pytest.mark.parametrize("pending_kind", ["reset", "recovery"])
@pytest.mark.parametrize("operation", ["status", "login-id"])
def test_pending_preserved_requires_reissue(
    mfa: tuple[Settings, Database, str, str], pending_kind: str, operation: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor = Authenticator()
        enroll(first, token, actor)
        login_mfa(first, password, actor)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, key = provision(first, second, password)
            request = reset_request if pending_kind == "reset" else recovery_request
            issued = request(first, ident)
            assert issued.status_code == 201
            raw = link_token(issued.json()[pending_kind + "_link"])
            options = recovery_options(second, raw).json() if pending_kind == "recovery" else None
            version = state(first, ident)["version"]
            saved = factors(db, ident)
            nonce = csrf(first)
            noop_before = snapshot(db)
            assert (
                command(first, ident, "login-id", version, "SECOND.MASTER", nonce).status_code
                == 200
            )
            assert snapshot(db) == noop_before
            assert command(first, ident, operation, version).status_code == 200
            if operation == "status":
                assert command(first, ident, "restore", version + 1).status_code == 200
            assert factors(db, ident) == saved
            if pending_kind == "reset":
                assert complete(second, raw, password).status_code == 401
            else:
                assert options is not None
                assert (
                    call(
                        second,
                        "/auth/passkeys/recovery/verify",
                        options["csrf_token"],
                        {"credential": Authenticator().registration(options["publicKey"])},
                    ).status_code
                    == 401
                )
                assert recovery_options(second, raw).status_code == 401
            reissued = request(first, ident, reissue=True)
            assert reissued.status_code == 201
            new = link_token(reissued.json()[pending_kind + "_link"])
            if pending_kind == "reset":
                assert complete(second, new, password).status_code == 204
            else:
                options = recovery_options(second, new).json()
                key = Authenticator()
                assert (
                    call(
                        second,
                        "/auth/passkeys/recovery/verify",
                        options["csrf_token"],
                        {"credential": key.registration(options["publicKey"])},
                    ).status_code
                    == 204
                )
            login_mfa(
                second,
                password,
                key,
                "renamed.master" if operation == "login-id" else "second.master",
            )


@pytest.mark.parametrize("operation", ["status", "restore", "login-id"])
@pytest.mark.parametrize("failure", ["audit", "db", "ack"])
def test_master_atomicity(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    failure: str,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor = Authenticator()
        enroll(first, token, actor)
        login_mfa(first, password, actor)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            version = state(first, ident)["version"]
            if operation == "restore":
                assert command(first, ident, "status", version).status_code == 200
                version += 1
            nonce = csrf(first)
            before = snapshot(db)
            original, commit = Audit.append, Session.commit
            action = {
                "status": "account_disable",
                "restore": "account_restore",
                "login-id": "login_id_change",
            }[operation]

            def append(adapter: Audit, event: Event) -> None:
                if event.action == action:
                    if failure == "audit":
                        raise Rejected(503, "unavailable")
                    if failure == "db":
                        adapter.s.execute(text("SELECT * FROM synthetic_missing_table"))
                    adapter.s.info["master_ack"] = True
                original(adapter, event)

            def committed(s: Session) -> None:
                commit(s)
                if s.info.pop("master_ack", False):
                    raise OperationalError("synthetic ACK loss", {}, RuntimeError("ack lost"))

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", append)
                patch.setattr(Session, "commit", committed)
                response = command(first, ident, operation, version, nonce=nonce)
            assert response.status_code == 503
            if failure != "ack":
                assert snapshot(db) == before
            else:
                assert response.json()["detail"] == "commit_outcome_unknown"
                result = state(first, ident)
                assert result["version"] == version + 1
                assert result["state"] == ("DISABLED" if operation == "status" else "ACTIVE")
                assert result["login_id"] == (
                    "renamed.master" if operation == "login-id" else "second.master"
                )
                with db.session() as s:
                    assert (
                        s.execute(
                            text("SELECT count(*) FROM audit_events WHERE action=:x"), {"x": action}
                        ).scalar_one()
                        == 1
                    )


def test_master_rename_preserves_c2_cooldown(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor = Authenticator()
        enroll(first, token, actor)
        login_mfa(first, password, actor)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as pending,
        ):
            ident, _ = provision(first, second, password)
            for _ in range(5):
                assert (
                    call(
                        pending,
                        "/auth/login",
                        csrf(pending),
                        {"login_id": "second.master", "password": "synthetic wrong password"},
                    ).status_code
                    == 401
                )

            def budget() -> str:
                with db.session() as s:
                    return str(
                        s.execute(
                            text(
                                "SELECT md5(string_agg(row_to_json(b)::text,',' ORDER BY key)) "
                                "FROM iam_budgets b"
                            )
                        ).scalar_one()
                    )

            before = budget()
            version = state(first, ident)["version"]
            assert command(first, ident, "login-id", version).status_code == 200
            assert budget() == before
            assert (
                call(
                    pending,
                    "/auth/login",
                    csrf(pending),
                    {"login_id": "renamed.master", "password": password},
                ).status_code
                == 429
            )
            assert (
                command(first, ident, "login-id", version + 1, "second.master").status_code == 200
            )
            assert (
                call(
                    pending,
                    "/auth/login",
                    csrf(pending),
                    {"login_id": "second.master", "password": password},
                ).status_code
                == 429
            )
