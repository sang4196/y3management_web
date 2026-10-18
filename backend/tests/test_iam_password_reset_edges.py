# ruff: noqa: F811
"""Reset readiness, hash admission and immutable credential/identity facts."""

from contextlib import closing

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import (
    add,
    delete,
    keys,
    link_token,
    recovery_options,
    recovery_request,
)
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_password_reset import complete, fingerprint, reset_request
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import HashAdmissionRejected
from y3management.database import Database
from y3management.iam.passwords import Passwords

pytestmark = pytest.mark.postgres


def key_facts(db: Database, ident: str) -> str:
    with db.session() as s:
        return str(
            s.execute(
                text(
                    "SELECT md5(string_agg(row_to_json(k)::text,',' ORDER BY credential_id)) "
                    "FROM iam_passkeys k WHERE account_id=:a"
                ),
                {"a": ident},
            ).scalar_one()
        )


@pytest.mark.parametrize("old_first", [True, False], ids=["old-first", "remaining-first"])
def test_reset_hash_capacity_and_key_tombstones_preserved(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, old_first: bool
) -> None:
    from uuid import UUID

    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, old = provision(first, second, password)
            original = keys(second)
            assert len(original["items"]) == 1
            old_key_id = original["items"][0]["key_id"]
            remaining = Authenticator()
            # Test-only surrogate UUID extremes force both orders around the real old UUID4.
            remaining_key_id = UUID(int=(1 << 128) - 1 if old_first else 0)
            with monkeypatch.context() as patch:
                patch.setattr("y3management.iam.mfa.uuid4", lambda: remaining_key_id)
                add(second, remaining)
            snapshot = keys(second)
            expected_ids = (
                [old_key_id, str(remaining_key_id)]
                if old_first
                else [str(remaining_key_id), old_key_id]
            )
            assert [item["key_id"] for item in snapshot["items"]] == expected_ids
            assert delete(second, old_key_id, snapshot["key_set_version"]) == 204
            before = key_facts(db, ident)
            issued = reset_request(first, ident)
            raw = link_token(issued.json()["reset_link"])
            assert key_facts(db, ident) == before
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
            assert key_facts(db, ident) == before
            login_mfa(second, password, remaining, "second.master")
            options = call(second, "/auth/passkeys/options", csrf(second), {}).json()
            assert (
                call(
                    second,
                    "/auth/passkeys/verify",
                    options["csrf_token"],
                    {"credential": old.registration(options["publicKey"])},
                ).status_code
                == 409
            )


def test_reset_disabled_restore_requires_fresh_reissue(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        branch = call(first, "/admin/branches", csrf(first), {"code": "A", "name": "A"}).json()
        issued = call(
            first,
            "/admin/accounts",
            csrf(first),
            {"login_id": "target.test", "branch_id": branch["id"]},
        ).json()
        ident = issued["account_id"]
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            target_key = Authenticator()
            enroll(second, link_token(issued["setup_link"]), target_key, password)
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
            login_mfa(second, password, target_key, "target.test")


def test_recovery_then_reset_without_intermediate_login(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            recovery = recovery_request(first, ident)
            raw = link_token(recovery.json()["recovery_link"])
            assert complete(second, raw, password).status_code == 401
            assert reset_request(first, ident).status_code == 409
            options = recovery_options(second, raw).json()
            fresh = Authenticator()
            assert (
                call(
                    second,
                    "/auth/passkeys/recovery/verify",
                    options["csrf_token"],
                    {"credential": fresh.registration(options["publicKey"])},
                ).status_code
                == 204
            )
            reset = reset_request(first, ident)
            assert reset.status_code == 201
            assert (
                complete(second, link_token(reset.json()["reset_link"]), password).status_code
                == 204
            )
            login_mfa(second, password, fresh, "second.master")
