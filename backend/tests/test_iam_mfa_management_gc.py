# ruff: noqa: F811
"""Retired source cleanup must preserve a locked legacy child until a later bounded GC."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.legacy_helpers import legacy_allocation, legacy_database, legacy_master  # noqa: F401
from tests.test_password_transition import migrate
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.security import Security

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("purpose", ["setup", "recovery"])
def test_gc_skips_source_with_locked_child_then_cleans(
    legacy_master: tuple[Settings, Database],
    purpose: str,
) -> None:
    settings, db = legacy_master
    source = legacy_allocation(db, "credential" if purpose == "setup" else "recovery")
    child = legacy_allocation(db, "mfa")
    table, field = (
        ("iam_credentials", "source_id")
        if purpose == "setup"
        else ("iam_recovery_credentials", "recovery_id")
    )
    with db.session() as session:
        account = session.execute(text("SELECT id FROM iam_accounts")).scalar_one()
        if purpose == "setup":
            session.execute(
                text("UPDATE iam_accounts SET state='PENDING_SETUP',password_hash=NULL")
            )
        session.execute(
            text(
                f"INSERT INTO {table}(id,account_id,digest,row_version,expires_at"
                + (",generation" if purpose == "recovery" else "")
                + ") SELECT :i,:a,:d,1,expires_at"
                + (",1" if purpose == "recovery" else "")
                + " FROM iam_security_states WHERE id=:i"
            ),
            {"i": source, "a": account, "d": uuid4().bytes * 2},
        )
        session.execute(
            text(
                "INSERT INTO iam_mfa_contexts(id,digest,csrf,account_id,purpose,"
                f"security_version,row_version,expires_at,{field},password_hash) "
                "SELECT :i,:d,'synthetic',:a,:p,1,1,expires_at,:s,:h FROM iam_security_states "
                "WHERE id=:i"
            ),
            {
                "i": child,
                "d": uuid4().bytes * 2,
                "a": account,
                "p": purpose,
                "s": source,
                "h": "synthetic-staged-hash" if purpose == "setup" else None,
            },
        )
        session.commit()
    migrate(settings, "upgrade", "head")
    with db.session() as business:
        row = business.execute(
            text(
                "SELECT consumed,password_hash,policy_version FROM iam_mfa_contexts WHERE "
                "id=:i FOR UPDATE"
            ),
            {"i": child},
        ).one()
        assert tuple(row) == (True, None, 1)
        with db.session() as gc:
            gc.execute(text("SET LOCAL lock_timeout='300ms'"))
            Security(gc, settings.iam_key.get_secret_value(), 2048, 128).allocate("preparation")
            gc.commit()
        assert (
            business.execute(
                text(f"SELECT count(*) FROM {table} WHERE id=:i"), {"i": source}
            ).scalar_one()
            == 1
        )
    with db.session() as gc:
        Security(gc, settings.iam_key.get_secret_value(), 2048, 128).allocate("preparation")
        gc.commit()
        assert (
            gc.execute(
                text("SELECT count(*) FROM iam_mfa_contexts WHERE id=:i"), {"i": child}
            ).scalar_one()
            == 0
        )
        assert (
            gc.execute(
                text(f"SELECT count(*) FROM {table} WHERE id=:i"), {"i": source}
            ).scalar_one()
            == 0
        )
        assert (
            gc.execute(text("SELECT count(*) FROM iam_policy_account_transitions")).scalar_one()
            == 1
        )
