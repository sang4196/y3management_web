# ruff: noqa: F811
"""Independent connections and actual provisioned Master sessions."""

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import add, keys, link_token, recovery_options, recovery_request
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.mfa import MFA
from y3management.iam.public import Authentication, RegistrationProof
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


def provision(first: TestClient, second: TestClient, password: str) -> tuple[str, Authenticator]:
    issued = call(first, "/admin/master-accounts", csrf(first), {"login_id": "second.master"})
    assert issued.status_code == 201
    key = Authenticator()
    enroll(second, link_token(issued.json()["setup_link"]), key, password)
    login_mfa(second, password, key, "second.master")
    return str(issued.json()["account_id"]), key


@pytest.mark.parametrize("same_key", [True, False])
def test_concurrent_key_deletion(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, same_key: bool
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        one, two = Authenticator(), Authenticator()
        enroll(client, token, one)
        login_mfa(client, password, one)
        add(client, two)
        items = keys(client)
        raw = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
        nonce = SyntheticSecret(csrf(client))
        service: Service = cast(FastAPI, client.app).state.iam_service
        original = IAM.authenticate
        barrier = Barrier(2)

        def authenticate(adapter: IAM, token: str | None, **kwargs: Any) -> Authentication:
            if kwargs.get("management"):
                barrier.wait(timeout=10)
            return original(adapter, token, **kwargs)

        def worker(index: int) -> int:
            try:
                service.delete_passkey(
                    raw,
                    nonce,
                    UUID(items["items"][0 if same_key else index]["key_id"]),
                    items["key_set_version"],
                )
                return 204
            except Rejected as e:
                return e.status

        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
            patch.setattr(IAM, "authenticate", authenticate)
            results = [pool.submit(worker, i) for i in range(2)]
            assert sorted(f.result(timeout=20) for f in results) == [204, 401]
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_passkeys WHERE revoked_at IS NULL")
                ).scalar_one()
                == 1
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='passkey_delete'")
                ).scalar_one()
                == 1
            )


def test_cross_recovery_preserves_one_normal_master(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident_b, _ = provision(first, second, password)
            with db.session() as s:
                ident_a = s.execute(
                    text("SELECT id FROM iam_accounts WHERE login_id='master.test'")
                ).scalar_one()
            raw = [SyntheticSecret(c.cookies.get("__Host-y3-auth") or "") for c in (first, second)]
            nonce = [SyntheticSecret(csrf(c)) for c in (first, second)]
            target = [UUID(ident_b), ident_a]
            versions = [2, 1]
            service: Service = cast(FastAPI, first.app).state.iam_service
            original = IAM.authenticate
            barrier = Barrier(2)

            def authenticate(adapter: IAM, token: str | None, **kwargs: Any) -> Authentication:
                if kwargs.get("management"):
                    barrier.wait(timeout=10)
                return original(adapter, token, **kwargs)

            def worker(i: int) -> int:
                try:
                    service.recover(
                        raw[i], nonce[i], target[i], versions[i], 1, True, reissue=False
                    )
                    return 201
                except Rejected as e:
                    return e.status

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
                patch.setattr(IAM, "authenticate", authenticate)
                results = [pool.submit(worker, i) for i in range(2)]
                assert sorted(f.result(timeout=20) for f in results) == [201, 401]
            with db.session() as s:
                assert (
                    s.execute(
                        text("SELECT count(*) FROM iam_accounts WHERE recovery_pending")
                    ).scalar_one()
                    == 1
                )
                assert (
                    s.execute(
                        text("SELECT count(*) FROM iam_passkeys WHERE revoked_at IS NULL")
                    ).scalar_one()
                    == 1
                )
                assert (
                    s.execute(
                        text("SELECT count(*) FROM audit_events WHERE action='recovery_start'")
                    ).scalar_one()
                    == 1
                )


def test_different_credentials_race_for_single_recovery_source(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            issued = recovery_request(first, ident)
            options = recovery_options(second, link_token(issued.json()["recovery_link"])).json()
            payloads = [Authenticator().registration(options["publicKey"]) for _ in range(2)]
            raw = SyntheticSecret(second.cookies.get("__Host-y3-ceremony") or "")
            service: Service = cast(FastAPI, first.app).state.iam_service
            original = MFA.verify_registration
            barrier = Barrier(2)

            def verify(
                adapter: MFA, token: str | None, nonce: str | None, payload: str
            ) -> RegistrationProof:
                proof = original(adapter, token, nonce, payload)
                barrier.wait(timeout=10)
                return proof

            def worker(i: int) -> int:
                try:
                    service.register_passkey(
                        raw,
                        options["csrf_token"],
                        json.dumps(payloads[i]),
                        None,
                        additional=False,
                        recovery=True,
                    )
                    return 204
                except Rejected as e:
                    return e.status

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
                patch.setattr(MFA, "verify_registration", verify)
                results = [pool.submit(worker, i) for i in range(2)]
                assert sorted(f.result(timeout=20) for f in results) == [204, 401]
            with db.session() as s:
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM iam_passkeys "
                            "WHERE account_id=:a AND revoked_at IS NULL"
                        ),
                        {"a": ident},
                    ).scalar_one()
                    == 1
                )
                assert (
                    s.execute(
                        text("SELECT count(*) FROM audit_events WHERE action='recovery_complete'")
                    ).scalar_one()
                    == 1
                )


@pytest.mark.parametrize("proof_kind", ["login", "add"])
def test_deletion_orders_after_crypto_before_final_authority(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    proof_kind: str,
) -> None:
    from threading import Event

    from webauthn import verify_authentication_response

    from tests.test_iam_mfa import begin
    from y3management.iam import mfa as module

    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        old, remaining = Authenticator(), Authenticator()
        enroll(first, token, old)
        login_mfa(first, password, old)
        old_id = UUID(keys(first)["items"][0]["key_id"])
        add(first, remaining)
        auth = SyntheticSecret(first.cookies.get("__Host-y3-auth") or "")
        csrf_token = SyntheticSecret(csrf(first))
        service: Service = cast(FastAPI, first.app).state.iam_service
        with closing(TestClient(first.app, base_url=ORIGIN)) as pending:
            if proof_kind == "login":
                options = begin(pending, password)
                payload = old.assertion(options["publicKey"])
                raw = SyntheticSecret(pending.cookies.get("__Host-y3-ceremony") or "")
            else:
                options = call(first, "/auth/passkeys/options", csrf_token, {}).json()
                payload = Authenticator().registration(options["publicKey"])
                raw = SyntheticSecret(first.cookies.get("__Host-y3-ceremony") or "")
            entered, release = Event(), Event()
            registration = MFA.verify_registration
            assertion = verify_authentication_response

            def held_registration(
                adapter: MFA, token: str | None, nonce: str | None, body: str
            ) -> RegistrationProof:
                proof = registration(adapter, token, nonce, body)
                entered.set()
                assert release.wait(10)
                return proof

            def held_assertion(**kwargs: Any) -> Any:
                proof = assertion(**kwargs)
                entered.set()
                assert release.wait(10)
                return proof

            def worker() -> int:
                try:
                    if proof_kind == "login":
                        service.finish_mfa_login(raw, options["csrf_token"], json.dumps(payload))
                    else:
                        service.register_passkey(
                            raw, options["csrf_token"], json.dumps(payload), auth, additional=True
                        )
                    return 204
                except Rejected as e:
                    return e.status

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
                if proof_kind == "login":
                    patch.setattr(module, "verify_authentication_response", held_assertion)
                else:
                    patch.setattr(MFA, "verify_registration", held_registration)
                result = pool.submit(worker)
                try:
                    assert entered.wait(10)
                    deleted = pool.submit(service.delete_passkey, auth, csrf_token, old_id, 2)
                    deleted.result(timeout=10)
                finally:
                    release.set()
                assert result.result(timeout=10) == 401
            with db.session() as s:
                assert (
                    s.execute(
                        text("SELECT count(*) FROM iam_passkeys WHERE revoked_at IS NULL")
                    ).scalar_one()
                    == 1
                )
                assert (
                    s.execute(
                        text("SELECT count(*) FROM iam_sessions WHERE NOT revoked")
                    ).scalar_one()
                    == 0
                )
