"""Actual setup/CLI paths and real library verification; synthetic keys stay in owned QA."""

import base64
import hashlib
import json
import secrets
import subprocess
import sys
from collections.abc import Iterator
from contextlib import ExitStack, closing
from pathlib import Path
from typing import Any
from uuid import uuid4

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.conftest import qa_record_schema
from tests.test_iam import ORIGIN, SyntheticSecret, child_env, cli_bootstrap, csrf
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


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


class Authenticator:
    """Test signing only. Product verification always uses the pinned WebAuthn library."""

    def __init__(self) -> None:
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.id = secrets.token_bytes(32)
        self.counter = 0
        self.user = ""

    def registration(
        self,
        options: dict[str, Any],
        *,
        uv: bool = True,
        origin: str = ORIGIN,
        flags: int | None = None,
    ) -> dict[str, Any]:
        self.user = options["user"]["id"]
        numbers = self.key.public_key().public_numbers()
        cose = cbor2.dumps(
            {1: 2, 3: -7, -1: 1, -2: numbers.x.to_bytes(32), -3: numbers.y.to_bytes(32)}
        )
        data = (
            hashlib.sha256(options["rp"]["id"].encode()).digest()
            + bytes([flags if flags is not None else 0x41 | (4 if uv else 0)])
            + bytes(4)
            + bytes(16)
            + len(self.id).to_bytes(2)
            + self.id
            + cose
        )
        return PrivateDict(
            id=b64(self.id),
            rawId=b64(self.id),
            type="public-key",
            response={
                "clientDataJSON": b64(
                    json.dumps(
                        dict(
                            type="webauthn.create",
                            challenge=options["challenge"],
                            origin=origin,
                            crossOrigin=False,
                        )
                    ).encode()
                ),
                "attestationObject": b64(cbor2.dumps(dict(fmt="none", attStmt={}, authData=data))),
            },
        )

    def assertion(
        self,
        options: dict[str, Any],
        *,
        uv: bool = True,
        up: bool = True,
        origin: str = ORIGIN,
        rp: str = "localhost",
        user: str | None = None,
        flags: int | None = None,
    ) -> dict[str, Any]:
        self.counter += 1
        client = json.dumps(
            dict(
                type="webauthn.get",
                challenge=options["challenge"],
                origin=origin,
                crossOrigin=False,
            )
        ).encode()
        data = hashlib.sha256(rp.encode()).digest() + bytes(
            [flags if flags is not None else (int(up) | (4 if uv else 0))]
        )
        data += self.counter.to_bytes(4)
        signature = self.key.sign(data + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
        return PrivateDict(
            id=b64(self.id),
            rawId=b64(self.id),
            type="public-key",
            response={
                "clientDataJSON": b64(client),
                "authenticatorData": b64(data),
                "signature": b64(signature),
                "userHandle": self.user if user is None else user,
            },
        )


@pytest.fixture
def mfa(
    postgres_database: Database, tmp_path: Path, request: pytest.FixtureRequest
) -> Iterator[tuple[Settings, Database, str, str]]:
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
            iam_mode="mfa",
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
        assert result.returncode == 0, "MFA migration failed"
        private = tmp_path / "installer"
        private.mkdir(mode=0o700)
        output = private / "enrollment"
        password = SyntheticSecret("MFA 가상 검증 " + secrets.token_urlsafe(24))
        if getattr(request, "param", True) is False:
            yield settings, db, password, ""
            return
        cli_bootstrap(settings, password, enrollment_file=output)
        assert output.stat().st_mode & 0o777 == 0o600
        token = SyntheticSecret(output.read_text().strip().split("#token=")[1])
        yield settings, db, password, token


def call(client: TestClient, path: str, nonce: str, body: dict[str, Any]) -> Any:
    return PrivateResponse(
        client.post("/api/v1" + path, headers={"Origin": ORIGIN, "X-CSRF-Token": nonce}, json=body)
    )


def enroll(client: TestClient, token: str, key: Authenticator, password: str | None = None) -> None:
    body = {"setup_token": token, **({"new_password": password} if password else {})}
    response = call(client, "/auth/passkeys/enrollment/options", csrf(client), body)
    assert response.status_code == 200, "Enrollment options failed"
    result = response.json()
    response = call(
        client,
        "/auth/passkeys/enrollment/verify",
        result["csrf_token"],
        {"credential": key.registration(result["publicKey"])},
    )
    assert response.status_code == 204, "Registration failed"
    assert "__Host-y3-auth" not in client.cookies


def begin(client: TestClient, password: str, identifier: str = "master.test") -> dict[str, Any]:
    r = call(client, "/auth/login", csrf(client), {"login_id": identifier, "password": password})
    assert r.status_code == 200, "Password stage failed"
    assert "__Host-y3-auth" not in client.cookies
    assert client.get("/api/v1/auth/me").status_code == 401
    value: dict[str, Any] = r.json()
    return value


def login_mfa(
    client: TestClient, password: str, key: Authenticator, identifier: str = "master.test"
) -> None:
    result = begin(client, password, identifier)
    r = call(
        client,
        "/auth/login/passkey/verify",
        result["csrf_token"],
        {"credential": key.assertion(result["publicKey"])},
    )
    assert r.status_code == 204, "Assertion failed"
    assert client.get("/api/v1/auth/me").status_code == 200


def test_actual_cli_setup_two_keys_and_branch(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as master:
        key = Authenticator()
        enroll(master, token, key)
        login_mfa(master, password, key)
        result = call(master, "/auth/passkeys/options", csrf(master), {}).json()
        second = Authenticator()
        assert (
            call(
                master,
                "/auth/passkeys/verify",
                result["csrf_token"],
                {"credential": second.registration(result["publicKey"])},
            ).status_code
            == 204
        )
        assert call(master, "/auth/logout", csrf(master), {}).status_code == 204
        login_mfa(master, password, second)
        branch = call(master, "/admin/branches", csrf(master), {"code": "A", "name": "A"}).json()
        issued = call(
            master,
            "/admin/accounts",
            csrf(master),
            {"login_id": "branch.test", "branch_id": branch["id"]},
        ).json()
        with closing(TestClient(master.app, base_url=ORIGIN)) as branch_client:
            branch_key = Authenticator()
            enroll(branch_client, issued["setup_link"].split("#token=")[1], branch_key, password)
            login_mfa(branch_client, password, branch_key, "branch.test")
            assert branch_client.get("/api/v1/branches").status_code == 200
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_sessions WHERE assurance='password_uv'")
                ).scalar_one()
                == 2
            )
            assert s.execute(text("SELECT count(*) FROM iam_passkeys")).scalar_one() == 3


@pytest.mark.parametrize(
    "attack", ["uv", "up", "origin", "rp", "user", "owner", "signature", "backup"]
)
def test_crypto_rejection(mfa: tuple[Settings, Database, str, str], attack: str) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        result = begin(client, password)
        kwargs: dict[str, Any] = {"uv": False} if attack == "uv" else {}
        if attack == "up":
            kwargs["up"] = False
        if attack == "origin":
            kwargs["origin"] = "https://other.invalid"
        if attack == "rp":
            kwargs["rp"] = "other.invalid"
        if attack == "user":
            kwargs["user"] = b64(uuid4().bytes)
        if attack == "backup":
            kwargs["flags"] = 0x15  # BS without BE
        payload = key.assertion(result["publicKey"], **kwargs)
        if attack == "owner":
            payload["id"] = payload["rawId"] = b64(secrets.token_bytes(32))
        if attack == "signature":
            payload["response"]["signature"] = b64(bytes(64))
        response = call(
            client, "/auth/login/passkey/verify", result["csrf_token"], {"credential": payload}
        )
        assert response.status_code == 401
        assert "__Host-y3-auth" not in client.cookies
        with db.session() as s:
            assert s.execute(text("SELECT count(*) FROM iam_sessions")).scalar_one() == 0
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
                ).scalar_one()
                == 1
            )
