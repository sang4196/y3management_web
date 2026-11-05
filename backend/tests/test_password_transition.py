"""Owned-schema cutover tests. SQL seeds exercise migration input, never user login."""

import json
import secrets
import subprocess
import sys
from collections.abc import Iterator
from contextlib import ExitStack
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.conftest import qa_record_schema
from tests.test_iam import ORIGIN, child_env
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


@pytest.fixture
def legacy_database(postgres_database: Database) -> Iterator[tuple[Settings, Database]]:
    schema = "iam_test_" + uuid4().hex
    qa_record_schema(schema, True)

    def drop() -> None:
        with postgres_database.engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        qa_record_schema(schema, False)

    with ExitStack() as cleanup:
        with postgres_database.engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        cleanup.callback(drop)
        settings = Settings(
            environment="test",
            database_url=postgres_database.engine.url.render_as_string(hide_password=False),
            database_schema=schema,
            iam_enabled=True,
            iam_mode="password",
            canonical_origin=ORIGIN,
            iam_key=secrets.token_urlsafe(32),
            security_state_capacity=2048,
            auth_session_capacity=128,
        )
        db = Database(settings)
        cleanup.callback(db.close)
        migrate(settings, "upgrade", "0013_workforce_trainer_state")
        yield settings, db


def migrate(settings: Settings, action: str, revision: str, *, success: bool = True) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", action, revision],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    )
    assert (result.returncode == 0) == success, "Owned migration outcome mismatch"


def fingerprint(db: Database) -> str:
    with db.session() as s:
        tables = list(
            s.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname=current_schema() ORDER BY tablename"
                )
            ).scalars()
        )
        data = {
            t: sorted(s.execute(text(f"SELECT row_to_json(x)::text FROM {t} x")).scalars())
            for t in tables
        }
        return json.dumps(data, sort_keys=True)


def test_password_transition_globally_empty_roundtrip(
    legacy_database: tuple[Settings, Database],
) -> None:
    settings, db = legacy_database
    before = fingerprint(db)
    migrate(settings, "upgrade", "0014_password_only")
    with db.session() as s:
        row = s.execute(text("SELECT summary FROM iam_policy_transitions")).scalar_one()
        assert len(row) == 33 and all(v == 0 for v in row.values())
        assert s.execute(text("SELECT auth_policy_version FROM iam_installation")).scalar_one() == 2
    migrate(settings, "downgrade", "0013_workforce_trainer_state")
    assert fingerprint(db) == before
    migrate(settings, "upgrade", "0014_password_only")


@pytest.mark.parametrize(
    "bad",
    [{}, {"unexpected": 0}, {"iam_accounts": -1}, {"iam_accounts": 0.5}, {"iam_accounts": "0"}],
)
def test_summary_rejects_missing_extra_negative_fractional_or_string(
    legacy_database: tuple[Settings, Database], bad: dict[str, object]
) -> None:
    settings, db = legacy_database
    migrate(settings, "upgrade", "0014_password_only")
    before = fingerprint(db)
    with db.session() as s:
        original = s.execute(text("SELECT summary FROM iam_policy_transitions")).scalar_one()
        candidate = {} if not bad else {**original, **bad}
        with pytest.raises(IntegrityError):
            s.execute(
                text("UPDATE iam_policy_transitions SET summary=CAST(:s AS jsonb)"),
                {"s": json.dumps(candidate)},
            )
    assert fingerprint(db) == before


def test_nonzero_transition_summary_rejects_downgrade_before_ddl(
    legacy_database: tuple[Settings, Database],
) -> None:
    settings, db = legacy_database
    migrate(settings, "upgrade", "0014_password_only")
    with db.session() as s:
        s.execute(
            text(
                "UPDATE iam_policy_transitions SET summary=jsonb_set(summary,"
                "'{iam_accounts}','1'::jsonb)"
            )
        )
        s.commit()
    before = fingerprint(db)
    migrate(settings, "downgrade", "0013_workforce_trainer_state", success=False)
    from tests.legacy_helpers import assert_revision_loss_guard

    assert_revision_loss_guard(db, "0014_password_only.py", "PASSWORD_DOWNGRADE_")
    assert fingerprint(db) == before


@pytest.mark.parametrize(
    "state,pending,classification",
    [
        ("ACTIVE", False, "unchanged_password"),
        ("ACTIVE", True, "password_pending"),
        ("DISABLED", False, "disabled"),
        ("DISABLED", True, "disabled"),
        ("PENDING_SETUP", False, "pending_setup"),
    ],
)
def test_transition_preserves_account_business_facts_and_rejects_nonempty_downgrade(
    legacy_database: tuple[Settings, Database], state: str, pending: bool, classification: str
) -> None:
    settings, db = legacy_database
    org, ident = uuid4(), uuid4()
    password = None if pending or state == "PENDING_SETUP" else "synthetic-migration-hash"
    with db.session() as s:
        s.execute(
            text("INSERT INTO organization_organizations VALUES(:o,'Migration fixture')"),
            {"o": org},
        )
        s.execute(
            text(
                "INSERT INTO iam_accounts(id,organization_id,login_id,state,password_hash,"
                "password_reset_pending,reset_generation) VALUES(:a,:o,'migration.test',:s,:h,"
                ":p,:g)"
            ),
            {"a": ident, "o": org, "s": state, "h": password, "p": pending, "g": int(pending)},
        )
        s.execute(text("INSERT INTO iam_login_ids VALUES('migration.test',:a)"), {"a": ident})
        s.execute(
            text("INSERT INTO iam_admin_grants VALUES(:a,:o,'ORGANIZATION',NULL)"),
            {"a": ident, "o": org},
        )
        s.execute(text("UPDATE iam_installation SET organization_id=:o"), {"o": org})
        s.commit()
    migrate(settings, "upgrade", "0014_password_only")
    with db.session() as s:
        row = (
            s.execute(text("SELECT * FROM iam_accounts WHERE id=:a"), {"a": ident}).mappings().one()
        )
        assert row["state"] == state and row["password_hash"] == password
        assert row["password_reset_pending"] == pending
        assert (row["row_version"], row["security_version"], row["reset_generation"]) == (
            2,
            2,
            int(pending),
        )
        assert (
            s.execute(
                text(
                    "SELECT classification FROM iam_policy_account_transitions WHERE account_id=:a"
                ),
                {"a": ident},
            ).scalar_one()
            == classification
        )
    before = fingerprint(db)
    migrate(settings, "downgrade", "0013_workforce_trainer_state", success=False)
    from tests.legacy_helpers import assert_revision_loss_guard

    assert_revision_loss_guard(db, "0014_password_only.py", "PASSWORD_DOWNGRADE_")
    assert fingerprint(db) == before
