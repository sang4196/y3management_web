"""Password-only additional Master activation and self-change session revocation."""

import secrets
from contextlib import closing

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import activate, call, link_token, login_password
from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_actual_additional_master_and_legacy_scope(
    password_app: tuple[Settings, Database, str],
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
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
            activate(second, link_token(refreshed.json()["setup_link"]), password)
            login_password(second, password, "second.master")
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


def test_password_change_preserves_scope_and_revokes_all_sessions(
    password_app: tuple[Settings, Database, str],
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
        before_scope = first.get("/api/v1/auth/me").json()
        old_cookie = SyntheticSecret(first.cookies.get("__Host-y3-auth") or "")
        new_password = SyntheticSecret("MFA 본인 변경 검증 " + secrets.token_urlsafe(24))
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            login_password(second, password)
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
            login_password(first, new_password)
            assert first.get("/api/v1/auth/me").json() == before_scope
            with db.session() as s:
                assert (
                    s.execute(
                        text("SELECT count(*) FROM audit_events WHERE action='password_change'")
                    ).scalar_one()
                    == 1
                )
