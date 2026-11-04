# ruff: noqa: F811
"""Real password proofs and management commits in both causal orders."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from tests.password_helpers import (
    call,
    complete,
    link_token,
    login_password,
    provision,
    reset_request,
)
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_master_management import command, state
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.password_reset import PasswordReset
from y3management.iam.public import Authentication, LoginProof, Reservation, ResetProof

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("operation", ["status", "login-id"])
@pytest.mark.parametrize("factor", ["c3", "login", "reset_complete", "reset"])
def test_management_wins_before_factor_final_lock(
    password_app: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    factor: str,
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as pending,
        ):
            ident = provision(first, second, password)
            nonce = csrf(second)
            raw = (
                link_token(reset_request(first, ident).json()["reset_link"])
                if factor == "reset_complete"
                else ""
            )
            if factor == "reset":
                path = "/admin/accounts/" + ident + "/password-reset"
                current = first.get("/api/v1" + path).json()
                factor_body = {
                    "expected_account_version": current["account_version"],
                    "identity_confirmed": True,
                    "expected_generation": current["generation"],
                }
                actor_nonce = csrf(first)
            version = state(first, ident)["version"]
            held, release, verified, committed = Event(), Event(), Event(), Event()
            original_c3, original_login = IAM.prepare_password_change, IAM.verify_login
            original_reset, original_auth = PasswordReset.prepare_reset, IAM.authenticate
            auth_calls = 0

            def hold() -> None:
                held.set()
                assert release.wait(20)

            def prepare(adapter: IAM, ident: UUID, current: str, new: str) -> LoginProof:
                proof = original_c3(adapter, ident, current, new)
                hold()
                return proof

            def verify(
                adapter: IAM, identifier: str, password: str, reservation: Reservation
            ) -> LoginProof | None:
                proof = original_login(adapter, identifier, password, reservation)
                assert proof is not None
                verified.set()
                hold()
                assert committed.is_set()
                return proof

            def reset(adapter: PasswordReset, token: str, password: str) -> ResetProof:
                proof = original_reset(adapter, token, password)
                hold()
                return proof

            def authenticate(adapter: IAM, token: str | None, **kwargs: Any) -> Authentication:
                nonlocal auth_calls
                if kwargs.get("management"):
                    auth_calls += 1
                    if auth_calls == 2:
                        hold()
                return original_auth(adapter, token, **kwargs)

            def worker() -> int:
                if factor == "c3":
                    return int(
                        call(
                            second,
                            "/auth/password",
                            nonce,
                            {"current_password": password, "new_password": password},
                        ).status_code
                    )
                if factor == "login":
                    return int(
                        call(
                            pending,
                            "/auth/login",
                            csrf(pending),
                            {"login_id": "second.master", "password": password},
                        ).status_code
                    )
                if factor == "reset_complete":
                    return int(complete(second, raw, password).status_code)
                return int(call(first, path, actor_nonce, factor_body).status_code)

            with (
                monkeypatch.context() as patch,
                ThreadPoolExecutor(max_workers=1, thread_name_prefix="credential-worker") as pool,
            ):
                if factor == "c3":
                    patch.setattr(IAM, "prepare_password_change", prepare)
                elif factor == "login":
                    patch.setattr(IAM, "verify_login", verify)
                elif factor == "reset_complete":
                    patch.setattr(PasswordReset, "prepare_reset", reset)
                else:
                    patch.setattr(IAM, "authenticate", authenticate)
                future = pool.submit(worker)
                assert held.wait(20)
                try:
                    with closing(TestClient(first.app, base_url=ORIGIN)) as manager:
                        manager.cookies.update(first.cookies)
                        assert command(manager, ident, operation, version).status_code == 200
                        committed.set()
                finally:
                    release.set()
                assert future.result(timeout=25) == (409 if factor == "reset" else 401)
            if factor == "login":
                assert verified.is_set() and committed.is_set()
                assert pending.get("/api/v1/auth/me").status_code == 401
            assert first.get("/api/v1/auth/me").status_code == 200
            if operation == "status":
                assert command(first, ident, "restore", version + 1).status_code == 200
            assert second.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("operation", ["status", "login-id"])
@pytest.mark.parametrize("factor", ["c3", "login", "reset"])
def test_factor_commit_before_management(
    password_app: tuple[Settings, Database, str], operation: str, factor: str
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as pending,
        ):
            ident = provision(first, second, password)
            version = state(first, ident)["version"]
            if factor == "c3":
                assert (
                    call(
                        second,
                        "/auth/password",
                        csrf(second),
                        {"current_password": password, "new_password": password},
                    ).status_code
                    == 204
                )
            elif factor == "login":
                login_password(pending, password, "second.master")
            else:
                assert reset_request(first, ident).status_code == 201
            expected = 200 if factor == "login" else 409
            assert command(first, ident, operation, version).status_code == expected
            if expected == 409:
                assert (
                    command(first, ident, operation, state(first, ident)["version"]).status_code
                    == 200
                )
            assert second.get("/api/v1/auth/me").status_code == 401
            if factor == "login":
                assert pending.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("loss", ["status", "login-id", "reset", "c3"])
def test_actor_actual_authority_loss_before_command(
    password_app: tuple[Settings, Database, str], loss: str
) -> None:
    from tests.test_iam_master_management import snapshot

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident = provision(first, second, password)
            actor = first.get("/api/v1/auth/me").json()["account_id"]
            version, nonce = state(first, ident)["version"], csrf(first)
            if loss in ("status", "login-id"):
                assert (
                    command(second, actor, loss, state(second, actor)["version"]).status_code == 200
                )
            elif loss == "reset":
                assert reset_request(second, actor).status_code == 201
            else:
                assert (
                    call(
                        first,
                        "/auth/password",
                        nonce,
                        {"current_password": password, "new_password": password},
                    ).status_code
                    == 204
                )
            before = snapshot(db)
            assert command(first, ident, "status", version, nonce=nonce).status_code == 401
            assert snapshot(db) == before
            assert second.get("/api/v1/auth/me").status_code == 200
