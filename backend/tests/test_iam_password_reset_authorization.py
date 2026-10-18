# ruff: noqa: F811
"""Current actor, actual other organization and purpose-specific management denial."""

from contextlib import closing
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import keys, link_token
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_password_reset import complete, reset_request
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.public import Authentication

pytestmark = pytest.mark.postgres


def test_reset_authorization_and_other_organization(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            # Existing management is still Branch Admin-only for real Master target.
            for suffix, body in [
                ("/activation", {"expected_version": 2}),
                ("/restore", {"expected_version": 2}),
            ]:
                assert (
                    call(first, "/admin/accounts/" + ident + suffix, csrf(first), body).status_code
                    == 404
                )
            assert (
                first.patch(
                    "/api/v1/admin/accounts/" + ident + "/login-id",
                    headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(first)},
                    json={"expected_version": 2, "login_id": "rename.master"},
                ).status_code
                == 404
            )
            assert (
                second.get("/api/v1/admin/accounts/" + ident + "/password-reset").status_code == 404
            )
            state = first.get("/api/v1/admin/accounts/" + ident + "/password-reset").json()
            body = {
                "expected_account_version": state["account_version"],
                "expected_generation": state["generation"],
                "identity_confirmed": False,
            }
            assert (
                call(
                    first, "/admin/accounts/" + ident + "/password-reset", csrf(first), body
                ).status_code
                == 422
            )
            # Move this actually provisioned and login-capable master to a real other org,
            # only inside the owned test schema. No fake Caller/session is introduced.
            other = uuid4()
            with db.session() as s:
                s.execute(
                    text("INSERT INTO organization_organizations VALUES(:id,:name)"),
                    {"id": other, "name": "Other synthetic organization"},
                )
                s.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": ident})
                s.execute(
                    text("UPDATE iam_accounts SET organization_id=:o WHERE id=:a"),
                    {"o": other, "a": ident},
                )
                s.execute(
                    text("INSERT INTO iam_admin_grants VALUES(:a,:o,'ORGANIZATION',NULL)"),
                    {"a": ident, "o": other},
                )
                s.commit()
            assert second.get("/api/v1/auth/me").status_code == 200
            assert first.get("/api/v1/admin/master-accounts/" + ident).status_code == 404
            assert (
                first.get("/api/v1/admin/accounts/" + ident + "/password-reset").status_code == 404
            )
            assert (
                call(
                    first,
                    "/admin/master-accounts/lookup",
                    csrf(first),
                    {"login_id": "second.master"},
                ).status_code
                == 404
            )
            foreign_key = keys(second)["items"][0]["key_id"]
            assert (
                first.request(
                    "DELETE",
                    "/api/v1/auth/passkeys/" + foreign_key,
                    headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(first)},
                    json={"expected_key_set_version": 1},
                ).status_code
                == 404
            )


@pytest.mark.parametrize("expiry", ["idle", "absolute", "revoked"])
def test_final_reset_actor_rechecked(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, expiry: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            original = IAM.authenticate
            count = 0

            def authenticate(adapter: IAM, token: str | None, **kwargs: Any) -> Authentication:
                nonlocal count
                if kwargs.get("management") and kwargs.get("target") == UUID(ident):
                    count += 1
                    if count == 3:  # state GET, preflight, then final business authorization
                        field = {
                            "idle": "created_at=clock_timestamp()-interval '1 hour',"
                            "last_activity=clock_timestamp()-interval '30 minutes'",
                            "absolute": "expires_at=clock_timestamp()",
                            "revoked": "revoked=true",
                        }[expiry]
                        with db.session() as s:
                            if expiry == "absolute":
                                s.execute(
                                    text(
                                        "WITH shifted AS (UPDATE iam_security_states SET "
                                        "expires_at=clock_timestamp()-interval '1 second' "
                                        "WHERE id IN "
                                        "(SELECT id FROM iam_sessions WHERE account_id=(SELECT id "
                                        "FROM iam_accounts WHERE login_id='master.test')) "
                                        "RETURNING id,expires_at) UPDATE iam_sessions s SET "
                                        "expires_at=shifted.expires_at,"
                                        "created_at=shifted.expires_at-interval '8 hours',"
                                        "last_activity=shifted.expires_at-interval '1 minute' "
                                        "FROM shifted WHERE s.id=shifted.id"
                                    )
                                )
                            else:
                                s.execute(
                                    text(
                                        "UPDATE iam_sessions SET "
                                        + field
                                        + " WHERE account_id=(SELECT id FROM iam_accounts "
                                        "WHERE login_id='master.test')"
                                    )
                                )
                            s.commit()
                return original(adapter, token, **kwargs)

            with monkeypatch.context() as patch:
                patch.setattr(IAM, "authenticate", authenticate)
                result = reset_request(first, ident)
            assert result.status_code == 401
            with db.session() as s:
                assert s.execute(
                    text("SELECT NOT password_reset_pending FROM iam_accounts WHERE id=:a"),
                    {"a": ident},
                ).scalar_one()
                assert (
                    s.execute(
                        text(
                            "SELECT count(*) FROM audit_events WHERE action='password_reset_start'"
                        )
                    ).scalar_one()
                    == 0
                )


def test_reset_self_branch_actor_and_unsupported_target_states(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        actor = first.get("/api/v1/auth/me").json()["account_id"]
        body = {"expected_account_version": 1, "expected_generation": 0, "identity_confirmed": True}
        path = "/admin/accounts/" + actor + "/password-reset"
        assert call(first, path, csrf(first), body).status_code == 404
        branch = call(first, "/admin/branches", csrf(first), {"code": "A", "name": "A"}).json()
        issued = call(
            first,
            "/admin/accounts",
            csrf(first),
            {"login_id": "branch.test", "branch_id": branch["id"]},
        ).json()
        ident = issued["account_id"]
        assert (
            call(
                first, "/admin/accounts/" + ident + "/password-reset", csrf(first), body
            ).status_code
            == 409
        )
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            other = Authenticator()
            enroll(second, link_token(issued["setup_link"]), other, password)
            login_mfa(second, password, other, "branch.test")
            assert call(second, path, csrf(second), body).status_code == 403
            current = first.get("/api/v1/admin/accounts/" + ident).json()
            assert (
                first.patch(
                    "/api/v1/admin/accounts/" + ident + "/status",
                    headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(first)},
                    json={"expected_version": current["version"], "status": "DISABLED"},
                ).status_code
                == 200
            )
            assert (
                call(
                    first, "/admin/accounts/" + ident + "/password-reset", csrf(first), body
                ).status_code
                == 409
            )
        with db.session() as s:
            assert s.execute(text("SELECT count(*) FROM iam_reset_credentials")).scalar_one() == 0


def test_reset_preserves_existing_c2_cooldown(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            assert call(second, "/auth/logout", csrf(second), {}).status_code == 204
            for _ in range(5):
                assert (
                    call(
                        second,
                        "/auth/login",
                        csrf(second),
                        {"login_id": "second.master", "password": "incorrect"},
                    ).status_code
                    == 401
                )
            assert (
                call(
                    second,
                    "/auth/login",
                    csrf(second),
                    {"login_id": "second.master", "password": password},
                ).status_code
                == 429
            )
            issued = reset_request(first, ident)
            assert (
                complete(second, link_token(issued.json()["reset_link"]), password).status_code
                == 204
            )
            assert (
                call(
                    second,
                    "/auth/login",
                    csrf(second),
                    {"login_id": "second.master", "password": password},
                ).status_code
                == 429
            )
