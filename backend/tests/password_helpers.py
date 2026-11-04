"""Real password CLI bootstrap and HTTP activation/login, with private failure values."""

import hashlib
import json
import secrets
import subprocess
import sys
from collections.abc import Iterator
from contextlib import ExitStack
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.conftest import password_app as password_app
from tests.conftest import qa_record_schema
from tests.test_iam import ORIGIN, SyntheticSecret, child_env, cli_bootstrap, csrf
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.public import LoginProof, Reservation
from y3management.use_cases import Service


class PrivateDict(dict[str, Any]):
    def __repr__(self) -> str:
        return "<synthetic-private-payload>"


def protect(value: Any) -> Any:
    if isinstance(value, dict):
        return PrivateDict({k: protect(v) for k, v in value.items()})
    if isinstance(value, list):
        return [protect(v) for v in value]
    if isinstance(value, str):
        return SyntheticSecret(value)
    return value


class PrivateResponse:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.status_code = response.status_code

    def json(self) -> Any:
        return protect(self.response.json())


def password_environment(
    postgres_database: Database, tmp_path: Path, request: pytest.FixtureRequest
) -> Iterator[tuple[Settings, Database, str]]:
    schema = "iam_test_" + uuid4().hex
    qa_record_schema(schema, True)

    def drop() -> None:
        with postgres_database.engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        qa_record_schema(schema, False)

    with ExitStack() as cleanup:
        with postgres_database.engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        cleanup.callback(drop)
        settings = Settings(
            environment="test",
            database_url=postgres_database.engine.url.render_as_string(hide_password=False),
            database_schema=schema,
            iam_enabled=True,
            iam_mode="password",
            canonical_origin=ORIGIN,
            iam_key=secrets.token_urlsafe(32),
            security_state_capacity=2048,
            auth_session_capacity=128,
        )
        db = Database(settings)
        cleanup.callback(db.close)
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            env=child_env(settings),
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, "Password policy migration failed"
        password = SyntheticSecret("비밀번호 가상 검증 " + secrets.token_urlsafe(24))
        if getattr(request, "param", True) is not False:
            cli_bootstrap(settings, password)
        yield settings, db, password


def call(client: TestClient, path: str, nonce: str, body: dict[str, Any]) -> Any:
    return PrivateResponse(
        client.post("/api/v1" + path, headers={"Origin": ORIGIN, "X-CSRF-Token": nonce}, json=body)
    )


def activate(client: TestClient, token: str, password: str) -> None:
    response = call(
        client,
        "/auth/credentials/complete",
        csrf(client),
        {"setup_token": token, "new_password": password},
    )
    assert response.status_code == 204, "Actual recipient password setup failed"
    assert "__Host-y3-auth" not in client.cookies


def login_password(client: TestClient, password: str, identifier: str = "master.test") -> None:
    response = call(
        client, "/auth/login", csrf(client), {"login_id": identifier, "password": password}
    )
    assert response.status_code == 204, "Actual password login failed"
    assert client.get("/api/v1/auth/me").status_code == 200


def link_token(link: str) -> SyntheticSecret:
    return SyntheticSecret(link.split("#token=")[1])


def provision(first: TestClient, second: TestClient, password: str) -> str:
    issued = call(first, "/admin/master-accounts", csrf(first), {"login_id": "second.master"})
    assert issued.status_code == 201
    activate(second, link_token(issued.json()["setup_link"]), password)
    login_password(second, password, "second.master")
    return str(issued.json()["account_id"])


def reset_request(client: TestClient, ident: str, *, reissue: bool = False) -> Any:
    state = client.get("/api/v1/admin/accounts/" + ident + "/password-reset")
    assert state.status_code == 200
    data = state.json()
    return call(
        client,
        "/admin/accounts/" + ident + "/password-reset" + ("/reissue" if reissue else ""),
        csrf(client),
        {
            "expected_account_version": data["account_version"],
            "expected_generation": data["generation"],
            "identity_confirmed": True,
        },
    )


def complete(client: TestClient, raw: str, password: str) -> Any:
    return call(
        client,
        "/auth/password-reset/complete",
        csrf(client),
        {"reset_token": raw, "new_password": password},
    )


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
                    "audit_events",
                )
            }
        )
        data["sessions"] = sorted(
            str(r) for r in s.execute(text("SELECT id,revoked,security_version FROM iam_sessions"))
        )
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def prepare_login(
    client: TestClient, identifier: str, password: str
) -> tuple[Reservation, LoginProof]:
    """Prepare a real admitted password proof for causal stale-proof tests."""
    service: Service = cast(FastAPI, client.app).state.iam_service
    with service.uow.open() as work:
        reservation = work.security.reserve(identifier)
    with service.uow.open() as work:
        proof = work.iam.verify_login(identifier, password, reservation)
    assert proof is not None
    return reservation, proof


def assert_prepared_rejected(client: TestClient, prepared: tuple[Reservation, LoginProof]) -> None:
    from y3management.contracts import Rejected

    reservation, proof = prepared
    service: Service = cast(FastAPI, client.app).state.iam_service
    with service.uow.open() as work:
        prep = work.security.preparation(None)
        slot = work.security.allocate("session_slot")
    try:
        with pytest.raises(Rejected) as error, service.uow.open() as work:
            work.iam.lock_login(proof.account_id)
            work.iam.login(proof, slot, prep.token, prep.csrf, reservation)
        assert error.value.status == 401
    finally:
        with service.uow.open() as work:
            work.security.release(slot, collect=False)
