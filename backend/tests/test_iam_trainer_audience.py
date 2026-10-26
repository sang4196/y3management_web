# ruff: noqa: F811
"""Actual sessions retain authentication-before-audience rejection and no-touch denial."""

from typing import Literal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, iam, login  # noqa: F401
from tests.test_iam_master_management import snapshot
from tests.test_iam_mfa import Authenticator, enroll, login_mfa, mfa  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.uow import UnitOfWork

pytestmark = pytest.mark.postgres


def assert_roleless_denials(
    settings: Settings, db: Database, token: str, expected_admin: int
) -> None:
    before = snapshot(db)
    audiences: tuple[Literal["admin", "account"], ...] = ("admin", "account")
    for audience in audiences:
        # Catch within the UoW so accidental last_activity writes would commit and
        # be detected instead of being hidden by exception rollback.
        with UnitOfWork(db, settings).open() as work:
            with pytest.raises(Rejected) as rejected:
                work.iam.authenticate(token, management=True, touch=True, audience=audience)
            assert rejected.value.status == (expected_admin if audience == "admin" else 401)
        assert snapshot(db) == before


@pytest.mark.parametrize(
    "invalid",
    [
        "valid",
        "revoked",
        "absolute",
        "idle",
        "weak",
        "key",
        "epoch",
        "recovery",
        "reset",
        "disabled",
        "cookie",
    ],
)
def test_roleless_real_uv_session_audience_and_validity(
    mfa: tuple[Settings, Database, str, str], invalid: str
) -> None:
    settings, db, password, setup = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, setup, key)
        login_mfa(client, password, key)
        ident = client.get("/api/v1/auth/me").json()["account_id"]
        token = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
        assert token
        mutations = {
            "revoked": "UPDATE iam_sessions SET revoked=true WHERE account_id=:a",
            "absolute": (
                "WITH shifted AS (UPDATE iam_security_states SET "
                "expires_at=clock_timestamp()-interval '1 second' "
                "WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a) "
                "RETURNING id,expires_at) "
                "UPDATE iam_sessions s SET expires_at=shifted.expires_at,"
                "created_at=shifted.expires_at-interval '8 hours',"
                "last_activity=shifted.expires_at-interval '1 minute' "
                "FROM shifted WHERE s.id=shifted.id"
            ),
            "idle": (
                "UPDATE iam_sessions SET created_at=created_at-interval '1 hour', "
                "last_activity=last_activity-interval '31 minutes' WHERE account_id=:a"
            ),
            "weak": "UPDATE iam_sessions SET assurance='password' WHERE account_id=:a",
            "key": "UPDATE iam_passkeys SET revoked_at=clock_timestamp() WHERE account_id=:a",
            "epoch": "UPDATE iam_accounts SET security_version=security_version+1 WHERE id=:a",
            "recovery": "UPDATE iam_accounts SET recovery_pending=true WHERE id=:a",
            "reset": (
                "UPDATE iam_accounts SET password_reset_pending=true,password_hash=NULL,"
                "reset_generation=reset_generation+1 WHERE id=:a"
            ),
            "disabled": "UPDATE iam_accounts SET state='DISABLED' WHERE id=:a",
        }
        with db.session() as session:
            session.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": ident})
            if invalid in mutations:
                session.execute(text(mutations[invalid]), {"a": ident})
            session.commit()
        if invalid == "cookie":
            token = SyntheticSecret("invalid-synthetic-cookie")
        assert_roleless_denials(settings, db, token, 403 if invalid == "valid" else 401)


@pytest.mark.parametrize("revoked", [False, True])
def test_roleless_real_s1_session_does_not_require_uv(
    iam: tuple[Settings, Database, str], revoked: bool
) -> None:
    settings, db, password = iam
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        login(client, "master.test", password)
        ident = client.get("/api/v1/auth/me").json()["account_id"]
        token = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
        assert token
        with db.session() as session:
            session.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": ident})
            if revoked:
                session.execute(
                    text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"), {"a": ident}
                )
            session.commit()
        assert_roleless_denials(settings, db, token, 401 if revoked else 403)
