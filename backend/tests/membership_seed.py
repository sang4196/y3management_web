"""Membership-local actual23 inverse, preserving every original migration/helper."""

from pathlib import Path

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError

from tests.pt_catalog_seed import prepare_revision_guard as original_prepare
from y3management.database import Database


def prepare_revision_guard(connection: Connection, target: str) -> None:
    context = MigrationContext.configure(connection)
    if context.get_current_revision() == target:
        return
    if context.get_current_revision() == "0023_membership_basics":
        scripts = ScriptDirectory.from_config(Config("alembic.ini"))
        script = scripts.get_revision("0023_membership_basics")
        assert script is not None
        with Operations.context(context):
            script.module.downgrade()
            context.stamp(scripts, "0022_pt_product_catalog")
    if context.get_current_revision() == target:
        return
    original_prepare(connection, target)


def assert_revision_loss_guard(db: Database, filename: str, expected: str) -> None:
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    script = next(s for s in scripts.walk_revisions() if Path(s.path).name == filename)
    with db.engine.connect() as connection:
        transaction = connection.begin()
        try:
            prepare_revision_guard(connection, script.revision)
            with pytest.raises((ValueError, DBAPIError), match=expected):
                with Operations.context(MigrationContext.configure(connection)):
                    script.module.downgrade()
        finally:
            transaction.rollback()


def password_downgrade_guard(db: Database, application_name: str) -> str:
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    script = scripts.get_revision("0014_password_only")
    assert script is not None
    with db.engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                text("SELECT set_config('application_name',:n,true)"), {"n": application_name}
            )
            prepare_revision_guard(connection, script.revision)
            with Operations.context(MigrationContext.configure(connection)):
                with pytest.raises(
                    ValueError, match="PASSWORD_DOWNGRADE_REQUIRES_GLOBAL_EMPTY"
                ) as error:
                    script.module.downgrade()
                return str(error.value)
        finally:
            transaction.rollback()


def projected(db: Database) -> dict[str, str]:
    """Full raw-row projection; deliberately does not drop compensation_version."""
    with db.session() as s:
        tables = list(
            s.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname=current_schema()")
            ).scalars()
        )
        return {
            table: s.execute(
                text(
                    "SELECT md5(COALESCE(string_agg(to_jsonb(t)::text,',' "
                    "ORDER BY to_jsonb(t)::text),'')) FROM " + table + " t"
                )
            ).scalar_one()
            for table in tables
        }


def full_shape(db: Database) -> tuple[object, ...]:
    from tests.test_operator_withdrawn_move import shape

    with db.session() as session:
        indexes = session.execute(
            text(
                "SELECT tablename,indexname,indexdef FROM pg_indexes "
                "WHERE schemaname=current_schema() ORDER BY 1,2"
            )
        ).all()
        columns = session.execute(
            text(
                "SELECT table_name,column_name,data_type,is_nullable,"
                "column_default,is_generated,generation_expression FROM information_schema.columns "
                "WHERE table_schema=current_schema() ORDER BY table_name,ordinal_position"
            )
        ).all()
    return shape(db), indexes, columns
