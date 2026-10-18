# ruff: noqa: F811
"""Management through actual onboarding and MFA, never injected callers."""

import secrets
from contextlib import closing
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import Authenticator, begin, call, enroll, login_mfa, mfa  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def link_token(link: str) -> SyntheticSecret:
    link = SyntheticSecret(link)
    return SyntheticSecret(link.rsplit("#token=", 1)[1])


def private_account_fingerprint(db: Database, ident: str) -> str:
    with db.session() as s:
        return str(
            s.execute(
                text(
                    "SELECT md5(concat(password_hash,login_id,encode(login_budget_key,'hex'))) "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": ident},
            ).scalar_one()
        )


def add(client: TestClient, key: Authenticator) -> None:
    options = call(client, "/auth/passkeys/options", csrf(client), {}).json()
    assert (
        call(
            client,
            "/auth/passkeys/verify",
            options["csrf_token"],
            {"credential": key.registration(options["publicKey"])},
        ).status_code
        == 204
    )


def keys(client: TestClient) -> dict[str, Any]:
    response = client.get("/api/v1/auth/passkeys")
    assert response.status_code == 200
    return dict(response.json())


def delete(client: TestClient, key_id: str, version: int) -> int:
    response = client.request(
        "DELETE",
        "/api/v1/auth/passkeys/" + key_id,
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(client)},
        json={"expected_key_set_version": version},
    )
    return int(response.status_code)


def test_delete_revokes_every_session_and_preserves_last_key(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        original, remaining = Authenticator(), Authenticator()
        enroll(first, token, original)
        login_mfa(first, password, original)
        old_id = keys(first)["items"][0]["key_id"]
        assert delete(first, old_id, 1) == 409
        add(first, remaining)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            login_mfa(second, password, remaining)
            assert delete(first, old_id, 1) == 409
            assert delete(first, old_id, 2) == 204
            assert "__Host-y3-auth" not in first.cookies
            assert second.get("/api/v1/auth/me").status_code == 401
            login_mfa(first, password, remaining)
            result = keys(first)
            assert len(result["items"]) == 1 and result["key_set_version"] == 3
            assert delete(first, result["items"][0]["key_id"], 3) == 409
            assert first.get("/api/v1/auth/me").status_code == 200
        with db.session() as s:
            audit = s.execute(
                text(
                    "SELECT key_id,before_key_set_version,after_key_set_version "
                    "FROM audit_events WHERE action='passkey_delete'"
                )
            ).one()
            assert str(audit.key_id) == old_id
            assert (audit.before_key_set_version, audit.after_key_set_version) == (2, 3)
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_passkeys WHERE revoked_at IS NOT NULL")
                ).scalar_one()
                == 1
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE action='passkey_delete'")
                ).scalar_one()
                == 1
            )


def test_actual_additional_master_and_legacy_scope(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        original = Authenticator()
        enroll(first, token, original)
        login_mfa(first, password, original)
        issued = call(first, "/admin/master-accounts", csrf(first), {"login_id": "second.master"})
        assert issued.status_code == 201
        ident = issued.json()["account_id"]
        assert first.get("/api/v1/admin/accounts/" + ident).status_code == 404
        refreshed = call(
            first,
            "/admin/master-accounts/" + ident + "/activation",
            csrf(first),
            {"expected_version": 1},
        )
        assert refreshed.status_code == 201
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            other = Authenticator()
            enroll(second, link_token(refreshed.json()["setup_link"]), other, password)
            login_mfa(second, password, other, "second.master")
            assert second.get("/api/v1/auth/me").status_code == 200
        assert (
            call(
                first,
                "/admin/master-accounts/" + ident + "/activation",
                csrf(first),
                {"expected_version": 3},
            ).status_code
            == 409
        )


def recovery_request(client: TestClient, ident: str, *, reissue: bool = False) -> Any:
    state = client.get("/api/v1/admin/accounts/" + ident + "/passkey-recovery")
    assert state.status_code == 200
    data = state.json()
    return call(
        client,
        "/admin/accounts/" + ident + "/passkey-recovery" + ("/reissue" if reissue else ""),
        csrf(client),
        {
            "expected_account_version": data["account_version"],
            "expected_key_set_version": data["key_set_version"],
            "identity_confirmed": True,
        },
    )


def recovery_options(client: TestClient, token: str) -> Any:
    return call(client, "/auth/passkeys/recovery/options", csrf(client), {"recovery_token": token})


@pytest.mark.parametrize("master_target", [True, False])
def test_recovery_preserves_password_scope_and_revokes_old_authority(
    mfa: tuple[Settings, Database, str, str],
    master_target: bool,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        if master_target:
            issued = call(first, "/admin/master-accounts", csrf(first), {"login_id": "target.test"})
        else:
            branch = call(first, "/admin/branches", csrf(first), {"code": "A", "name": "A"}).json()
            issued = call(
                first,
                "/admin/accounts",
                csrf(first),
                {"login_id": "target.test", "branch_id": branch["id"]},
            )
        assert issued.status_code == 201
        ident = issued.json()["account_id"]
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as target,
            closing(TestClient(first.app, base_url=ORIGIN)) as duplicate,
        ):
            old, other, new = Authenticator(), Authenticator(), Authenticator()
            enroll(target, link_token(issued.json()["setup_link"]), old, password)
            login_mfa(target, password, old, "target.test")
            add(target, other)
            login_mfa(duplicate, password, other, "target.test")
            before_hash = private_account_fingerprint(db, ident)
            pending = call(target, "/auth/passkeys/options", csrf(target), {}).json()
            recovery = recovery_request(first, ident)
            assert recovery.status_code == 201
            assert target.get("/api/v1/auth/me").status_code == 401
            assert duplicate.get("/api/v1/auth/me").status_code == 401
            assert (
                call(
                    target,
                    "/auth/passkeys/verify",
                    pending["csrf_token"],
                    {"credential": Authenticator().registration(pending["publicKey"])},
                ).status_code
                == 401
            )
            raw = link_token(recovery.json()["recovery_link"])
            options = recovery_options(target, raw)
            assert options.status_code == 200
            data = options.json()
            payload = {"credential": new.registration(data["publicKey"])}
            assert (
                call(
                    target, "/auth/passkeys/enrollment/verify", data["csrf_token"], payload
                ).status_code
                == 401
            )
            assert (
                call(
                    target, "/auth/passkeys/recovery/verify", data["csrf_token"], payload
                ).status_code
                == 204
            )
            assert "__Host-y3-auth" not in target.cookies
            assert recovery_options(target, raw).status_code == 401
            login_mfa(target, password, new, "target.test")
            assert len(keys(target)["items"]) == 1
            added = call(target, "/auth/passkeys/options", csrf(target), {}).json()
            assert (
                call(
                    target,
                    "/auth/passkeys/verify",
                    added["csrf_token"],
                    {"credential": old.registration(added["publicKey"])},
                ).status_code
                == 409
            )
            assert call(target, "/auth/logout", csrf(target), {}).status_code == 204
            old_login = begin(target, password, "target.test")
            assert (
                call(
                    target,
                    "/auth/login/passkey/verify",
                    old_login["csrf_token"],
                    {"credential": old.assertion(old_login["publicKey"])},
                ).status_code
                == 401
            )

            assert before_hash == private_account_fingerprint(db, ident), (
                "Recovery changed credential or stable budget"
            )
            with db.session() as s:
                audit = s.execute(
                    text(
                        "SELECT action,key_id,before_key_set_version,"
                        "after_key_set_version,before_recovery_generation,"
                        "after_recovery_generation FROM audit_events "
                        "WHERE target_id=:a AND action IN "
                        "('recovery_start','recovery_complete') ORDER BY happened_at"
                    ),
                    {"a": ident},
                ).all()
                assert len(audit) == 2
                assert audit[0].key_id is None and audit[1].key_id is not None
                assert tuple(audit[0][2:]) == (2, 3, 0, 1)
                assert tuple(audit[1][2:]) == (3, 4, 1, 1)
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM iam_passkeys "
                            "WHERE account_id=:a AND revoked_at IS NOT NULL"
                        ),
                        {"a": ident},
                    ).scalar_one()
                    == 2
                )


def test_mfa_current_password_change_preserves_key_and_revokes_all_sessions(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        before_keys = keys(first)
        before_scope = first.get("/api/v1/auth/me").json()
        old_cookie = SyntheticSecret(first.cookies.get("__Host-y3-auth") or "")
        new_password = SyntheticSecret("MFA 본인 변경 검증 " + secrets.token_urlsafe(24))
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            login_mfa(second, password, key)
            result = call(
                first,
                "/auth/password",
                csrf(first),
                {"current_password": password, "new_password": new_password},
            )
            assert result.status_code == 204
            assert "__Host-y3-auth" not in first.cookies
            assert second.get("/api/v1/auth/me").status_code == 401
            assert (
                first.get(
                    "/api/v1/auth/me",
                    headers={"Cookie": SyntheticSecret("__Host-y3-auth=" + old_cookie)},
                ).status_code
                == 401
            )
            assert (
                call(
                    first,
                    "/auth/login",
                    csrf(first),
                    {"login_id": "master.test", "password": password},
                ).status_code
                == 401
            )
            login_mfa(first, new_password, key)
            assert keys(first) == before_keys
            assert first.get("/api/v1/auth/me").json() == before_scope
            with db.session() as s:
                assert (
                    s.execute(
                        text("SELECT count(*) FROM audit_events WHERE action='password_change'")
                    ).scalar_one()
                    == 1
                )
                assert (
                    s.execute(
                        text("SELECT count(*) FROM iam_passkeys WHERE revoked_at IS NULL")
                    ).scalar_one()
                    == 1
                )
