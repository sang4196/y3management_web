# ruff: noqa: F811
"""Original-revision migration fixtures, separate from password-only application setup."""

import subprocess
import sys
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Connection

from tests.test_iam import child_env
from tests.test_password_transition import legacy_database as legacy_database
from y3management.config import Settings
from y3management.database import Database


def migration_status(settings: Settings, direction: str, revision: str) -> int:
    return subprocess.run(
        [sys.executable, "-m", "alembic", direction, revision],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    ).returncode


@pytest.fixture
def legacy_master(
    legacy_database: tuple[Settings, Database], request: pytest.FixtureRequest
) -> tuple[Settings, Database]:
    settings, db = legacy_database
    revision = getattr(request, "param", "0013_workforce_trainer_state")
    if revision != "0013_workforce_trainer_state":
        assert migration_status(settings, "downgrade", revision) == 0
    org, account = uuid4(), uuid4()
    with db.session() as s:
        s.execute(
            text("INSERT INTO organization_organizations VALUES(:o,'Legacy migration fixture')"),
            {"o": org},
        )
        s.execute(
            text(
                "INSERT INTO iam_accounts(id,organization_id,login_id,state,password_hash) "
                "VALUES(:a,:o,'legacy.master','ACTIVE','synthetic-migration-hash')"
            ),
            {"a": account, "o": org},
        )
        s.execute(text("INSERT INTO iam_login_ids VALUES('legacy.master',:a)"), {"a": account})
        s.execute(
            text("INSERT INTO iam_admin_grants VALUES(:a,:o,'ORGANIZATION',NULL)"),
            {"a": account, "o": org},
        )
        s.execute(text("UPDATE iam_installation SET organization_id=:o"), {"o": org})
        s.commit()
    return settings, db


def prepare_password_guard(connection: Connection) -> None:
    """Walk to the actual 0014 shape inside the caller's rollback-only transaction."""
    context = MigrationContext.configure(connection)
    current = context.get_current_revision()
    if current == "0014_password_only":
        return
    assert current == "0015_account_lifecycle"
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    script = scripts.get_revision(current)
    assert script is not None
    with Operations.context(context):
        script.module.downgrade()
        context.stamp(scripts, "0014_password_only")


def assert_revision_loss_guard(db: Database, filename: str, expected: str) -> None:
    """Prove the DDL function reaches its specific DB guard, not a process/config rejection."""
    import importlib.util
    from pathlib import Path

    from sqlalchemy.exc import DBAPIError

    spec = importlib.util.spec_from_file_location(
        "owned_revision_guard", Path("alembic/versions") / filename
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with db.engine.connect() as connection:
        transaction = connection.begin()
        try:
            if filename == "0014_password_only.py":
                prepare_password_guard(connection)
            with pytest.raises((ValueError, DBAPIError), match=expected):
                with Operations.context(MigrationContext.configure(connection)):
                    module.downgrade()
        finally:
            transaction.rollback()


def legacy_allocation(db: Database, kind: str) -> UUID:
    """Historical migration input only; never used to prepare a current user session."""
    ident = uuid4()
    with db.session() as session:
        session.execute(
            text(
                "INSERT INTO iam_security_states(id,kind,expires_at) "
                "VALUES(:i,:k,clock_timestamp()+interval '30 minutes')"
            ),
            {"i": ident, "k": kind},
        )
        session.commit()
    return ident


def password_downgrade_guard(db: Database, application_name: str) -> str:
    """Run the actual 0014 DB guard on an independent connection, separate from CLI exclusion."""
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "owned_password_loss_guard", Path("alembic/versions/0014_password_only.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with db.engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                text("SELECT set_config('application_name',:n,true)"), {"n": application_name}
            )
            prepare_password_guard(connection)
            with Operations.context(MigrationContext.configure(connection)):
                with pytest.raises(
                    ValueError, match="PASSWORD_DOWNGRADE_REQUIRES_GLOBAL_EMPTY"
                ) as error:
                    module.downgrade()
                return str(error.value)
        finally:
            transaction.rollback()
