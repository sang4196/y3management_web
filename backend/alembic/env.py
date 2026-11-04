"""Explicit migration entry point; IAM revisions run only on an operator-selected target."""

from alembic.util import CommandError

from alembic import context
from y3management.config import load_settings
from y3management.database import Database
from y3management.runtime import ProcessGuard


def run_migrations() -> None:
    settings = load_settings()
    if context.is_offline_mode():
        context.configure(
            url=settings.database_url.get_secret_value(),
            target_metadata=None,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
        return
    guard = ProcessGuard(settings)
    database = None
    try:
        database = Database(settings)
        with database.engine.connect() as connection:
            context.configure(connection=connection, target_metadata=None)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        try:
            if database is not None:
                database.close()
        finally:
            guard.close()


try:
    run_migrations()
except Exception:
    raise CommandError(
        "Migration environment failed; verify configuration and database access"
    ) from None
