# ruff: noqa: F811
"""Source cleanup never cascades into a skipped, business-locked ceremony."""

from contextlib import closing

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token, recovery_options, recovery_request
from tests.test_iam_mfa_management_races import provision
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.security import Security

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("purpose", ["setup", "recovery"])
def test_gc_skips_source_with_locked_child_then_cleans(
    mfa: tuple[Settings, Database, str, str],
    purpose: str,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as target:
            if purpose == "recovery":
                ident, _ = provision(first, target, password)
                issued = recovery_request(first, ident)
                assert (
                    recovery_options(target, link_token(issued.json()["recovery_link"])).status_code
                    == 200
                )
                table, field = "iam_recovery_credentials", "recovery_id"
            else:
                issued = call(
                    first, "/admin/master-accounts", csrf(first), {"login_id": "setup.master"}
                )
                ident = issued.json()["account_id"]
                assert (
                    call(
                        target,
                        "/auth/passkeys/enrollment/options",
                        csrf(target),
                        {
                            "setup_token": link_token(issued.json()["setup_link"]),
                            "new_password": password,
                        },
                    ).status_code
                    == 200
                )
                table, field = "iam_credentials", "source_id"
            with db.session() as s:
                row = s.execute(
                    text(
                        f"SELECT id,{field} AS source FROM iam_mfa_contexts "
                        "WHERE account_id=:a AND NOT consumed"
                    ),
                    {"a": ident},
                ).one()
                s.execute(
                    text("UPDATE iam_mfa_contexts SET expires_at=clock_timestamp() WHERE id=:id"),
                    {"id": row.id},
                )
                s.execute(
                    text(f"UPDATE {table} SET expires_at=clock_timestamp() WHERE id=:id"),
                    {"id": row.source},
                )
                s.commit()
            with db.session() as business:
                business.execute(
                    text("SELECT id FROM iam_mfa_contexts WHERE id=:id FOR UPDATE"), {"id": row.id}
                ).one()
                with db.session() as gc:
                    gc.execute(text("SET LOCAL lock_timeout='300ms'"))
                    blocked = False
                    try:
                        Security(gc, settings.iam_key.get_secret_value(), 2048, 128).allocate("mfa")
                        gc.commit()
                    except DBAPIError:
                        blocked = True
                        gc.rollback()
                    assert not blocked, "GC cascaded into locked child while holding global guard"
                assert (
                    business.execute(
                        text(f"SELECT count(*) FROM {table} WHERE id=:id"), {"id": row.source}
                    ).scalar_one()
                    == 1
                )
            with db.session() as gc:
                Security(gc, settings.iam_key.get_secret_value(), 2048, 128).allocate("mfa")
                gc.commit()
                assert (
                    gc.execute(
                        text("SELECT count(*) FROM iam_mfa_contexts WHERE id=:id"), {"id": row.id}
                    ).scalar_one()
                    == 0
                )
                assert (
                    gc.execute(
                        text(f"SELECT count(*) FROM {table} WHERE id=:id"), {"id": row.source}
                    ).scalar_one()
                    == 0
                )
