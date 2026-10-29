# ruff: noqa: F811
"""Independent connections serialize reset source consumption and management authority."""

import secrets
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier, Event, local
from typing import Any, cast
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import add, keys, link_token
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_password_reset import reset_request
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.mfa import MFA
from y3management.iam.public import Authentication, LoginProof, ResetProof
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("case", ["cross", "same", "recovery", "delete"])
def test_reset_management_races(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, other = provision(first, second, password)
            if case == "delete":
                add(second, Authenticator())
                key_list = keys(second)
            actor = first.get("/api/v1/auth/me").json()["account_id"]
            target_state = first.get("/api/v1/admin/accounts/" + ident + "/password-reset").json()
            actor_state = second.get("/api/v1/admin/accounts/" + actor + "/password-reset").json()
            recovery = first.get("/api/v1/admin/accounts/" + ident + "/passkey-recovery").json()
            a, b = (SyntheticSecret(c.cookies.get("__Host-y3-auth") or "") for c in (first, second))
            an, bn = csrf(first), csrf(second)
            service: Service = cast(FastAPI, first.app).state.iam_service
            original, barrier = IAM.authenticate, Barrier(2)
            phase = local()
            reached: list[int] = []

            def auth(adapter: IAM, token: str | None, **kwargs: Any) -> Authentication:
                if kwargs.get("management"):
                    phase.calls += 1
                    # Reset now preserves the original deadline with touch=False in BOTH
                    # preflight and main. Synchronize main entry, not the touch option.
                    final_reset = phase.reset and phase.calls == 2
                    final_other = not phase.reset and kwargs.get("touch") is not False
                    if final_reset or final_other:
                        reached.append(phase.index)
                        barrier.wait(timeout=15)
                return original(adapter, token, **kwargs)

            def worker(index: int) -> int:
                phase.index = index
                phase.calls = 0
                phase.reset = index == 0 or case in ("same", "cross")
                try:
                    if index == 0 or case == "same":
                        service.reset_password(
                            a,
                            an,
                            UUID(ident),
                            target_state["account_version"],
                            target_state["generation"],
                            True,
                            reissue=False,
                        )
                    elif case == "cross":
                        service.reset_password(
                            b,
                            bn,
                            UUID(actor),
                            actor_state["account_version"],
                            actor_state["generation"],
                            True,
                            reissue=False,
                        )
                    elif case == "recovery":
                        service.recover(
                            a,
                            an,
                            UUID(ident),
                            recovery["account_version"],
                            recovery["key_set_version"],
                            True,
                            reissue=False,
                        )
                    else:
                        service.delete_passkey(
                            b, bn, UUID(key_list["items"][0]["key_id"]), key_list["key_set_version"]
                        )
                    return 204
                except Rejected as error:
                    return error.status

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
                patch.setattr(IAM, "authenticate", auth)
                futures = [pool.submit(worker, i) for i in range(2)]
                results = sorted(f.result(timeout=25) for f in futures)
            assert sorted(reached) == [0, 1]
            assert results in ([204, 401], [204, 409])
            with db.session() as s:
                assert (
                    s.execute(
                        text("SELECT count(*) FROM iam_accounts WHERE password_reset_pending")
                    ).scalar_one()
                    <= 1
                )
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM iam_accounts WHERE "
                            "password_reset_pending AND recovery_pending"
                        )
                    ).scalar_one()
                    == 0
                )


@pytest.mark.parametrize(
    "case", ["two_passwords", "reissue", "expiry", "disable", "scope", "rename"]
)
def test_reset_final_after_hash(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as third,
        ):
            if case in ("disable", "scope", "rename"):
                branch = call(
                    first, "/admin/branches", csrf(first), {"code": "A", "name": "A"}
                ).json()
                next_branch = call(
                    first, "/admin/branches", csrf(first), {"code": "B", "name": "B"}
                ).json()
                issued = call(
                    first,
                    "/admin/accounts",
                    csrf(first),
                    {"login_id": "target.test", "branch_id": branch["id"]},
                ).json()
                ident = issued["account_id"]
                target_key = Authenticator()
                enroll(second, link_token(issued["setup_link"]), target_key, password)
            else:
                ident, target_key = provision(first, second, password)
            raw = link_token(reset_request(first, ident).json()["reset_link"])
            # Fresh preauth in two independent clients and distinct new passwords.
            second.cookies.clear()
            third.cookies.clear()
            nonces = [csrf(c) for c in (second, third)]
            passwords = [
                SyntheticSecret("독립 암호 검증 " + secrets.token_urlsafe(24)) for _ in range(2)
            ]
            barrier, held, release = Barrier(2), Event(), Event()
            original = MFA.prepare_reset

            def prepare(adapter: MFA, token: str, password: str) -> ResetProof:
                proof = original(adapter, token, password)
                if case == "two_passwords":
                    barrier.wait(timeout=15)
                else:
                    held.set()
                    assert release.wait(15)
                return proof

            def worker(index: int) -> int:
                return int(
                    call(
                        (second, third)[index],
                        "/auth/password-reset/complete",
                        nonces[index],
                        {"reset_token": raw, "new_password": passwords[index]},
                    ).status_code
                )

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
                patch.setattr(MFA, "prepare_reset", prepare)
                futures = [pool.submit(worker, 0)]
                if case == "two_passwords":
                    futures.append(pool.submit(worker, 1))
                else:
                    assert held.wait(15)
                    try:
                        if case == "reissue":
                            assert reset_request(first, ident, reissue=True).status_code == 201
                        elif case == "expiry":
                            with db.session() as s:
                                s.execute(
                                    text(
                                        "UPDATE iam_reset_credentials SET "
                                        "expires_at=clock_timestamp() WHERE account_id=:a"
                                    ),
                                    {"a": ident},
                                )
                                s.commit()
                        else:
                            current = first.get("/api/v1/admin/accounts/" + ident).json()
                            path, body = (
                                ("/status", {"status": "DISABLED"})
                                if case == "disable"
                                else ("/access", {"branch_id": next_branch["id"]})
                                if case == "scope"
                                else ("/login-id", {"login_id": "renamed.test"})
                            )
                            response = first.patch(
                                "/api/v1/admin/accounts/" + ident + path,
                                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(first)},
                                json={"expected_version": current["version"], **body},
                            )
                            assert response.status_code in (200, 204)
                    finally:
                        release.set()
                results = [f.result(timeout=25) for f in futures]
            assert sorted(results) == ([204, 401] if case == "two_passwords" else [401])
            with db.session() as s:
                assert s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='password_reset_complete'")
                ).scalar_one() == (1 if case == "two_passwords" else 0)
            if case == "two_passwords":
                winner = results.index(204)
                with closing(TestClient(first.app, base_url=ORIGIN)) as fresh:
                    login_mfa(fresh, passwords[winner], target_key, "second.master")


def test_c3_hash_cannot_restore_reset_password(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            nonce = csrf(second)
            held, release = Event(), Event()
            original = IAM.prepare_password_change

            def prepare(adapter: IAM, ident: UUID, current: str, new: str) -> LoginProof:
                proof = original(adapter, ident, current, new)
                held.set()
                assert release.wait(15)
                return proof

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
                patch.setattr(IAM, "prepare_password_change", prepare)
                pending = pool.submit(
                    call,
                    second,
                    "/auth/password",
                    nonce,
                    {"current_password": password, "new_password": password},
                )
                assert held.wait(15)
                try:
                    assert reset_request(first, ident).status_code == 201
                finally:
                    release.set()
                assert pending.result(timeout=25).status_code == 401
            with db.session() as s:
                assert s.execute(
                    text(
                        "SELECT password_hash IS NULL AND password_reset_pending "
                        "FROM iam_accounts WHERE id=:a"
                    ),
                    {"a": ident},
                ).scalar_one()
