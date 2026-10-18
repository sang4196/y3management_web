# ruff: noqa: F811
"""Independent PostgreSQL connection ordering for new MFA paths (no injected Caller)."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier, Event
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from webauthn import verify_authentication_response

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import Authenticator, begin, call, enroll, login_mfa, mfa  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam import mfa as mfa_module
from y3management.iam.mfa import MFA
from y3management.iam.public import RegistrationProof
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


def test_single_enrollment_consumption_race(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        result = call(
            client, "/auth/passkeys/enrollment/options", csrf(client), {"setup_token": token}
        ).json()
        payload = Authenticator().registration(result["publicKey"])
        raw = SyntheticSecret(client.cookies.get("__Host-y3-ceremony") or "")
        service: Service = cast(FastAPI, client.app).state.iam_service
        barrier = Barrier(2)
        original = MFA.verify_registration

        def verify(
            adapter: MFA, raw: str | None, nonce: str | None, body: str
        ) -> RegistrationProof:
            verified = original(adapter, raw, nonce, body)
            barrier.wait(timeout=10)
            return verified

        def worker() -> int:
            import json

            try:
                service.register_passkey(
                    raw, result["csrf_token"], json.dumps(payload), None, additional=False
                )
                return 204
            except Rejected as error:
                return error.status

        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=2) as pool:
            patch.setattr(MFA, "verify_registration", verify)
            futures = [pool.submit(worker) for _ in range(2)]
            assert sorted(f.result(timeout=15) for f in futures) == [204, 401]
        with db.session() as s:
            assert s.execute(text("SELECT count(*) FROM iam_passkeys")).scalar_one() == 1
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='passkey_register'")
                ).scalar_one()
                == 1
            )


@pytest.mark.parametrize("competitor", ["reissue", "disable", "scope", "rename", "password"])
def test_registration_or_login_orders_security_changes(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, competitor: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as master:
        key = Authenticator()
        enroll(master, token, key)
        login_mfa(master, password, key)
        a = call(master, "/admin/branches", csrf(master), {"code": "A", "name": "A"}).json()
        b = call(master, "/admin/branches", csrf(master), {"code": "B", "name": "B"}).json()
        issued = call(
            master,
            "/admin/accounts",
            csrf(master),
            {"login_id": "branch.test", "branch_id": a["id"]},
        ).json()
        with closing(TestClient(master.app, base_url=ORIGIN)) as client:
            branch_key = Authenticator()
            if competitor == "reissue":
                result = call(
                    client,
                    "/auth/passkeys/enrollment/options",
                    csrf(client),
                    {
                        "setup_token": issued["setup_link"].split("#token=")[1],
                        "new_password": password,
                    },
                ).json()
                payload = branch_key.registration(result["publicKey"])
                version = 1
            else:
                enroll(client, issued["setup_link"].split("#token=")[1], branch_key, password)
                if competitor == "password":
                    login_mfa(client, password, branch_key, "branch.test")
                # A separate browser starts pending MFA; the branch session stays valid.
                pending = TestClient(master.app, base_url=ORIGIN)
                result = begin(pending, password, "branch.test")
                payload = branch_key.assertion(result["publicKey"])
                version = 2
            raw = SyntheticSecret(
                (client if competitor == "reissue" else pending).cookies.get("__Host-y3-ceremony")
                or ""
            )
            service: Service = cast(FastAPI, master.app).state.iam_service
            entered, release = Event(), Event()
            registration = MFA.verify_registration
            assertion = verify_authentication_response

            def held_registration(
                adapter: MFA, raw: str | None, nonce: str | None, body: str
            ) -> RegistrationProof:
                proof = registration(adapter, raw, nonce, body)
                entered.set()
                assert release.wait(10)
                return proof

            def held_assertion(**kwargs: Any) -> Any:
                verified = assertion(**kwargs)
                entered.set()
                assert release.wait(10)
                return verified

            def worker() -> int:
                import json

                try:
                    if competitor == "reissue":
                        service.register_passkey(
                            raw, result["csrf_token"], json.dumps(payload), None, additional=False
                        )
                    else:
                        service.finish_mfa_login(raw, result["csrf_token"], json.dumps(payload))
                    return 204
                except Rejected as error:
                    return error.status

            with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
                patch.setattr(MFA, "verify_registration", held_registration)
                patch.setattr(mfa_module, "verify_authentication_response", held_assertion)
                future = pool.submit(worker)
                try:
                    assert entered.wait(10), "Verifier barrier not reached"
                    if competitor == "reissue":
                        response = call(
                            master,
                            "/admin/accounts/" + issued["account_id"] + "/activation",
                            csrf(master),
                            {"expected_version": version},
                        )
                        assert response.status_code == 201
                    elif competitor == "password":
                        response = call(
                            client,
                            "/auth/password",
                            csrf(client),
                            {"current_password": password, "new_password": password + " changed"},
                        )
                        assert response.status_code == 204
                    else:
                        suffix = {"disable": "status", "scope": "access", "rename": "login-id"}[
                            competitor
                        ]
                        body = {
                            "expected_version": version,
                            **(
                                {"status": "DISABLED"}
                                if competitor == "disable"
                                else {"branch_id": b["id"]}
                                if competitor == "scope"
                                else {"login_id": "renamed.test"}
                            ),
                        }
                        response = master.patch(
                            "/api/v1/admin/accounts/" + issued["account_id"] + "/" + suffix,
                            json=body,
                            headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(master)},
                        )
                        assert response.status_code == 200
                finally:
                    release.set()
                assert future.result(timeout=15) == 401
            if competitor != "reissue":
                pending.close()
            with db.session() as s:
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"
                        ),
                        {"a": issued["account_id"]},
                    ).scalar_one()
                    == 0
                )
                if competitor == "rename":
                    assert s.execute(
                        text(
                            "SELECT a.login_budget_key=b.key FROM iam_accounts a "
                            "JOIN iam_mfa_contexts c ON c.account_id=a.id JOIN iam_attempts b "
                            "ON b.id=c.attempt_id WHERE a.id=:a"
                        ),
                        {"a": issued["account_id"]},
                    ).scalar_one()
            # The denied old context does not prevent a legitimate new ceremony.
            client.cookies.clear()
            if competitor == "reissue":
                enroll(
                    client, response.json()["setup_link"].split("#token=")[1], branch_key, password
                )
            elif competitor == "disable":
                assert (
                    call(
                        master,
                        "/admin/accounts/" + issued["account_id"] + "/restore",
                        csrf(master),
                        {"expected_version": 3},
                    ).status_code
                    == 200
                )
            login_mfa(
                client,
                password + " changed" if competitor == "password" else password,
                branch_key,
                "renamed.test" if competitor == "rename" else "branch.test",
            )
