# ruff: noqa: F811
"""Reset readiness, hash admission and immutable credential/identity facts."""

from contextlib import closing

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import (
    activate,
    call,
    complete,
    fingerprint,
    link_token,
    login_password,
    provision,
    reset_request,
)
from tests.test_iam import ORIGIN, csrf
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import HashAdmissionRejected
from y3management.database import Database
from y3management.iam.passwords import Passwords

pytestmark = pytest.mark.postgres


def test_reset_hash_capacity_preserves_pending(
    password_app: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident = provision(first, second, password)
            raw = link_token(reset_request(first, ident).json()["reset_link"])
            nonce = csrf(second)
            baseline = fingerprint(db)

            def denied(adapter: Passwords, value: str, login_id: str) -> str:
                raise HashAdmissionRejected()

            with monkeypatch.context() as patch:
                patch.setattr(Passwords, "create", denied)
                assert (
                    call(
                        second,
                        "/auth/password-reset/complete",
                        nonce,
                        {"reset_token": raw, "new_password": password},
                    ).status_code
                    == 503
                )
            assert fingerprint(db) == baseline
            assert complete(second, raw, password).status_code == 204
            login_password(second, password, "second.master")


def test_reset_disabled_restore_requires_fresh_reissue(
    password_app: tuple[Settings, Database, str],
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
        branch = call(first, "/admin/branches", csrf(first), {"code": "A", "name": "A"}).json()
        issued = call(
            first,
            "/admin/accounts",
            csrf(first),
            {"login_id": "target.test", "branch_id": branch["id"]},
        ).json()
        ident = issued["account_id"]
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            activate(second, link_token(issued["setup_link"]), password)
            raw = link_token(reset_request(first, ident).json()["reset_link"])
            current = first.get("/api/v1/admin/accounts/" + ident).json()
            disabled = first.patch(
                "/api/v1/admin/accounts/" + ident + "/status",
                headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(first)},
                json={"expected_version": current["version"], "status": "DISABLED"},
            )
            assert disabled.status_code == 200
            assert complete(second, raw, password).status_code == 401
            assert (
                call(
                    first,
                    "/admin/accounts/" + ident + "/restore",
                    csrf(first),
                    {"expected_version": disabled.json()["version"]},
                ).status_code
                == 200
            )
            assert complete(second, raw, password).status_code == 401
            with db.session() as s:
                assert s.execute(
                    text(
                        "SELECT password_reset_pending AND password_hash IS NULL "
                        "FROM iam_accounts WHERE id=:a"
                    ),
                    {"a": ident},
                ).scalar_one()
            fresh = reset_request(first, ident, reissue=True)
            assert fresh.status_code == 201
            assert (
                complete(second, link_token(fresh.json()["reset_link"]), password).status_code
                == 204
            )
            login_password(second, password, "target.test")
