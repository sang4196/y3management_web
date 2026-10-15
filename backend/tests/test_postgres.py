"""Real PostgreSQL transactions; only a UUID-named test-owned table is created/dropped."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, MetaData, Table, insert, select, text
from sqlalchemy.pool import QueuePool

from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_commit_rollback_and_session_cleanup(postgres_database: Database) -> None:
    database = postgres_database
    pool = database.engine.pool
    assert isinstance(pool, QueuePool)
    table = Table("foundation002_" + uuid4().hex, MetaData(), Column("value", Integer))
    table.create(database.engine)
    try:
        with database.session() as first:
            with first.begin():
                first.execute(insert(table).values(value=1))
        assert pool.checkedout() == 0
        with database.session() as second:
            assert first is not second
            assert second.scalars(select(table.c.value)).all() == [1]
        with pytest.raises(RuntimeError, match="intentional"), database.session() as failed:
            failed.execute(insert(table).values(value=2))
            raise RuntimeError("intentional rollback")
        assert pool.checkedout() == 0
        with database.session() as after_failure:
            assert after_failure is not failed
            assert after_failure.scalars(select(table.c.value)).all() == [1]
            assert after_failure.execute(text("SELECT 1")).scalar_one() == 1
        assert pool.checkedout() == 0
    finally:
        table.drop(database.engine)
    assert pool.checkedout() == 0


def test_real_database_health(postgres_database: Database, settings: Settings) -> None:
    with TestClient(create_app(settings, database=postgres_database)) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}


def test_alembic_online_environment(postgres_database: Database) -> None:
    env = {key: value for key, value in os.environ.items() if not key.startswith("Y3_")}
    env["Y3_ENVIRONMENT"] = "test"
    env["Y3_DATABASE_URL"] = postgres_database.engine.url.render_as_string(hide_password=False)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"],
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode:
        pytest.fail("Alembic online current failed", pytrace=False)
    # Foundation target is untouched; IAM revisions are tested in owned schemas.
    assert result.stdout.strip() == ""
