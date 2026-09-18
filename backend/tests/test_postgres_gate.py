"""Subprocess verification of exit policy; synthetic tests do not claim DB coverage."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "case,expected",
    [
        ("pass", 0),
        ("missing", 4),
        ("empty", 4),
        ("skip", 1),
        ("xfail", 1),
        ("xpass", 1),
        ("fail", 1),
        ("connection", 1),
    ],
)
def test_required_postgres_exit_policy(tmp_path: Path, case: str, expected: int) -> None:
    (tmp_path / "conftest.py").write_bytes(Path(__file__).with_name("conftest.py").read_bytes())
    bodies = {
        "pass": "pass",
        "missing": "pass",
        "empty": "pass",
        "skip": "pytest.skip('synthetic skip')",
        "xfail": "pytest.xfail('synthetic xfail')",
        "xpass": "pass",
        "fail": "assert False",
        "connection": "pass",
    }
    decorators = "" if case == "empty" else "@pytest.mark.postgres\n"
    if case == "xpass":
        decorators += "@pytest.mark.xfail\n"
    body = "import pytest\n" + decorators + "def test_case():\n    " + bodies[case] + "\n"
    if case == "connection":
        body = """import socket
import pytest
from sqlalchemy import text
from y3management.config import Settings
from y3management.database import Database

@pytest.mark.postgres
def test_connection_failure():
    with socket.socket() as reserved:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            reserved.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
        settings = Settings.model_validate({"environment": "test", "database_url":
            f"postgresql+psycopg://y3management_test:synthetic@127.0.0.1:{port}/y3management_test",
            "db_connect_timeout_seconds": 2})
        database = Database(settings)
        try:
            try:
                with database.session() as session:
                    session.execute(text("SELECT 1"))
            except Exception:
                pytest.fail("Controlled driver connection failure", pytrace=False)
        finally:
            database.close()
"""
    (tmp_path / "test_synthetic.py").write_text(body, encoding="utf-8")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("Y3_") and key != "PYTEST_ADDOPTS"
    }
    if case != "missing":
        env["Y3_TEST_DATABASE_URL"] = "synthetic-policy-test-only"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--require-postgres",
            "-m",
            "postgres",
            "--confcutdir",
            str(tmp_path),
            str(tmp_path),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == expected, result.stdout + result.stderr
