"""WF5-local actual21 -> original20 migration acceptance adapter.

Original shared fixture/harness and original migration files remain unchanged. Every
walk executes real DDL inside the caller's rollback-only transaction; marker-only
substitution cannot stand in for the original shape.
"""

from pathlib import Path

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError

from tests.workforce_compensation_seed import prepare_revision_guard as original_prepare
from y3management.database import Database


def prepare_revision_guard(connection: Connection, target: str) -> None:
    context = MigrationContext.configure(connection)
    if context.get_current_revision() == target:
        return
    if context.get_current_revision() == "0021_workforce_base_schedule":
        scripts = ScriptDirectory.from_config(Config("alembic.ini"))
        script = scripts.get_revision("0021_workforce_base_schedule")
        assert script is not None
        with Operations.context(context):
            script.module.downgrade()
            context.stamp(scripts, "0020_workforce_compensation")
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
