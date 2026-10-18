# ruff: noqa: F811
"""Hold real proofs before their final locks, then commit Master management."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from webauthn import verify_authentication_response

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_master_management import command, state
from tests.test_iam_mfa import Authenticator, begin, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import (
    add,
    delete,
    keys,
    link_token,
    recovery_options,
    recovery_request,
)
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_password_reset import complete, reset_request
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.iam import mfa as mfa_module
from y3management.iam.infrastructure import IAM
from y3management.iam.mfa import MFA
from y3management.iam.public import Authentication, LoginProof, RegistrationProof, ResetProof

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("operation", ["status", "login-id"])
@pytest.mark.parametrize(
    "factor",
    ["c3", "add", "login", "reset_complete", "recovery_complete", "reset", "recovery", "delete"],
)
def test_management_wins_before_factor_final_lock(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    factor: str,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor = Authenticator()
        enroll(first, token, actor)
        login_mfa(first, password, actor)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as pending,
        ):
            ident, key = provision(first, second, password)
            nonce = csrf(second)
            if factor == "add":
                options = call(second, "/auth/passkeys/options", nonce, {}).json()
                payload = Authenticator().registration(options["publicKey"])
            if factor == "login":
                options = begin(pending, password, "second.master")
                payload = key.assertion(options["publicKey"])
            if factor == "reset_complete":
                raw = link_token(reset_request(first, ident).json()["reset_link"])
                nonce = csrf(second)
            if factor == "recovery_complete":
                raw = link_token(recovery_request(first, ident).json()["recovery_link"])
                options = recovery_options(second, raw).json()
                payload = Authenticator().registration(options["publicKey"])
            if factor == "delete":
                # Bind identity before adding a second authenticator; no UUID ordering assumption.
                old = keys(second)["items"][0]["key_id"]
                add(second, Authenticator())
                keyset = keys(second)["key_set_version"]
            if factor in ("reset", "recovery"):
                suffix = "password-reset" if factor == "reset" else "passkey-recovery"
                path = "/admin/accounts/" + ident + "/" + suffix
                current = first.get("/api/v1" + path).json()
                factor_body = {
                    "expected_account_version": current["account_version"],
                    "identity_confirmed": True,
                    (
                        "expected_generation" if factor == "reset" else "expected_key_set_version"
                    ): current["generation" if factor == "reset" else "key_set_version"],
                }
                actor_nonce = csrf(first)
            version = state(first, ident)["version"]
            held, release = Event(), Event()
            verified_success, management_committed = Event(), Event()
            original_c3, original_register = IAM.prepare_password_change, MFA.verify_registration
            original_login, original_reset, original_auth = (
                verify_authentication_response,
                MFA.prepare_reset,
                IAM.authenticate,
            )

            def hold() -> None:
                held.set()
                assert release.wait(20)

            def prepare(adapter: IAM, ident: UUID, current: str, new: str) -> LoginProof:
                proof = original_c3(adapter, ident, current, new)
                hold()
                return proof

            def registration(adapter: MFA, *args: Any, **kwargs: Any) -> RegistrationProof:
                proof = original_register(adapter, *args, **kwargs)
                hold()
                return proof

            def held_assertion(**kwargs: Any) -> Any:
                verified = original_login(**kwargs)
                verified_success.set()
                hold()
                assert management_committed.is_set()
                return verified

            def reset(adapter: MFA, *args: Any, **kwargs: Any) -> ResetProof:
                proof = original_reset(adapter, *args, **kwargs)
                hold()
                return proof

            def authenticate(adapter: IAM, token: str | None, **kwargs: Any) -> Authentication:
                # New management command uses touch=False; competing factor uses default touch.
                if kwargs.get("management") and kwargs.get("touch") is not False:
                    hold()
                return original_auth(adapter, token, **kwargs)

            def worker() -> Any:
                if factor == "c3":
                    return call(
                        second,
                        "/auth/password",
                        nonce,
                        {"current_password": password, "new_password": password},
                    ).status_code
                if factor in ("add", "recovery_complete"):
                    return call(
                        second,
                        "/auth/passkeys/verify"
                        if factor == "add"
                        else "/auth/passkeys/recovery/verify",
                        options["csrf_token"],
                        {"credential": payload},
                    ).status_code
                if factor == "login":
                    return call(
                        pending,
                        "/auth/login/passkey/verify",
                        options["csrf_token"],
                        {"credential": payload},
                    ).status_code
                if factor == "reset_complete":
                    return complete(second, raw, password).status_code
                if factor == "delete":
                    return delete(second, old, keyset)
                return call(first, path, actor_nonce, factor_body).status_code

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
                if factor == "c3":
                    patch.setattr(IAM, "prepare_password_change", prepare)
                elif factor in ("add", "recovery_complete"):
                    patch.setattr(MFA, "verify_registration", registration)
                elif factor == "login":
                    patch.setattr(mfa_module, "verify_authentication_response", held_assertion)
                elif factor == "reset_complete":
                    patch.setattr(MFA, "prepare_reset", reset)
                else:
                    patch.setattr(IAM, "authenticate", authenticate)
                future = pool.submit(worker)
                assert held.wait(20)
                if factor == "login":
                    assert verified_success.is_set() and not release.is_set()
                try:
                    # Avoid sharing a client with the held reset/recovery request.
                    with closing(TestClient(first.app, base_url=ORIGIN)) as manager:
                        manager.cookies.update(first.cookies)
                        # Final management recheck must not enter the competitor hook.
                        with monkeypatch.context() as inner:
                            if factor in ("reset", "recovery", "delete"):
                                inner.setattr(IAM, "authenticate", original_auth)
                            assert command(manager, ident, operation, version).status_code == 200
                            management_committed.set()
                finally:
                    release.set()
                assert future.result(timeout=25) == (
                    409 if factor in ("reset", "recovery") else 401
                )
            if factor == "login":
                assert verified_success.is_set() and management_committed.is_set()
                assert pending.get("/api/v1/auth/me").status_code == 401
            assert first.get("/api/v1/auth/me").status_code == 200
            if operation == "status":
                assert command(first, ident, "restore", version + 1).status_code == 200
            assert second.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("operation", ["status", "login-id"])
@pytest.mark.parametrize("factor", ["c3", "add", "login", "reset", "recovery", "delete"])
def test_factor_commit_before_management(
    mfa: tuple[Settings, Database, str, str], operation: str, factor: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor = Authenticator()
        enroll(first, token, actor)
        login_mfa(first, password, actor)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as pending,
        ):
            ident, key = provision(first, second, password)
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
            elif factor == "add":
                add(second, Authenticator())
            elif factor == "login":
                login_mfa(pending, password, key, "second.master")
            elif factor == "delete":
                old = keys(second)["items"][0]["key_id"]
                add(second, Authenticator())
                assert delete(second, old, keys(second)["key_set_version"]) == 204
            else:
                assert (reset_request if factor == "reset" else recovery_request)(
                    first, ident
                ).status_code == 201
            # Login and key addition do not alter row_version; other factor mutations do.
            expected = 200 if factor in ("add", "login") else 409
            assert command(first, ident, operation, version).status_code == expected
            if expected == 409:
                assert (
                    command(first, ident, operation, state(first, ident)["version"]).status_code
                    == 200
                )
            assert second.get("/api/v1/auth/me").status_code == 401
            if factor == "login":
                assert pending.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("loss", ["status", "login-id", "reset", "recovery", "c3", "delete"])
def test_actor_actual_authority_loss_before_command(
    mfa: tuple[Settings, Database, str, str], loss: str
) -> None:
    from tests.test_iam_master_management import snapshot

    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor = Authenticator()
        enroll(first, token, actor)
        login_mfa(first, password, actor)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            actor_id = first.get("/api/v1/auth/me").json()["account_id"]
            version = state(first, ident)["version"]
            nonce = csrf(first)
            if loss in ("status", "login-id"):
                assert (
                    command(second, actor_id, loss, state(second, actor_id)["version"]).status_code
                    == 200
                )
            elif loss in ("reset", "recovery"):
                assert (reset_request if loss == "reset" else recovery_request)(
                    second, actor_id
                ).status_code == 201
            elif loss == "c3":
                assert (
                    call(
                        first,
                        "/auth/password",
                        nonce,
                        {"current_password": password, "new_password": password},
                    ).status_code
                    == 204
                )
            else:
                old = keys(first)["items"][0]["key_id"]
                add(first, Authenticator())
                assert delete(first, old, keys(first)["key_set_version"]) == 204
            before = snapshot(db)
            assert command(first, ident, "status", version, nonce=nonce).status_code == 401
            assert snapshot(db) == before
            assert second.get("/api/v1/auth/me").status_code == 200
