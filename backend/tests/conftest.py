import json
import os
import subprocess
from collections.abc import Iterator

import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url

from y3management.config import Settings
from y3management.database import Database

_db_tests: set[str] = set()
_db_passed: set[str] = set()
_db_incomplete: set[str] = set()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-postgres",
        action="store_true",
        help="Require collected PostgreSQL tests and real passes",
    )


def pytest_configure() -> None:
    _db_tests.clear()
    _db_passed.clear()
    _db_incomplete.clear()


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    _db_tests.update(item.nodeid for item in items if item.get_closest_marker("postgres"))
    if config.getoption("--require-postgres") and not _db_tests:
        raise pytest.UsageError("Required PostgreSQL suite selected no postgres tests")
    if _db_tests and not os.environ.get("Y3_TEST_DATABASE_URL"):
        raise pytest.UsageError("Y3_TEST_DATABASE_URL is required; no development DB fallback")


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.nodeid in _db_tests:
        if report.skipped or hasattr(report, "wasxfail"):
            _db_incomplete.add(report.nodeid)
        if report.when == "call" and report.passed:
            _db_passed.add(report.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if exitstatus == 0 and (_db_incomplete or _db_tests - _db_passed):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_line("Required PostgreSQL verification incomplete (skip/xfail/no pass)")


@pytest.fixture
def postgres_database() -> Iterator[Database]:
    """Check the project's Compose port owner before any database connection or DDL."""
    try:
        settings = Settings.model_validate(
            {
                "environment": "test",
                "database_url": os.environ.get("Y3_TEST_DATABASE_URL"),
            }
        )
        url = make_url(settings.database_url.get_secret_value())
        if url.host != "127.0.0.1" or url.port != 55433 or url.query:
            raise ValueError("Not the project Compose test target")
        context = "desktop-linux" if os.name == "nt" else "wsl-ubuntu"
        expected_endpoint = (
            "npipe:////./pipe/dockerDesktopLinuxEngine"
            if os.name == "nt"
            else "unix:///run/docker-wsl.sock"
        )
        endpoint = subprocess.check_output(
            [
                "docker",
                "context",
                "inspect",
                context,
                "--format",
                "{{.Endpoints.docker.Host}}",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).strip()
        if endpoint != expected_endpoint:
            raise ValueError("Unverified Docker endpoint")
        docker = ["docker", "--context", context]
        identity = subprocess.check_output(
            [*docker, "compose", "-f", "compose.yaml", "ps", "-q", "postgres-test"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).strip()
        if not identity or "\n" in identity:
            raise ValueError("Dedicated test service is not running")
        details = (
            subprocess.check_output(
                [
                    *docker,
                    "inspect",
                    "--format",
                    '{{ index .Config.Labels "com.docker.compose.project" }}|'
                    '{{ index .Config.Labels "com.docker.compose.service" }}|'
                    "{{json .NetworkSettings.Ports}}",
                    identity,
                ],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            .strip()
            .split("|", 2)
        )
        if details[:2] != ["y3management-foundation", "postgres-test"]:
            raise ValueError("Wrong Compose owner")
        bindings = json.loads(details[2])["5432/tcp"]
        if {"HostIp": "127.0.0.1", "HostPort": "55433"} not in bindings:
            raise ValueError("Wrong test port binding")
    except Exception:
        raise pytest.fail.Exception(
            "PostgreSQL target/configuration preflight failed; no DB accessed", pytrace=False
        ) from None
    database = Database(settings)
    try:
        try:
            with database.session() as db_session:
                identity_row = db_session.execute(
                    text("SELECT current_database(), current_user, inet_server_port()")
                ).one()
                assert tuple(identity_row) == ("y3management_test", "y3management_test", 5432)
        except Exception:
            raise pytest.fail.Exception(
                "Dedicated PostgreSQL connection/identity check failed", pytrace=False
            ) from None
        print("Verified target: 127.0.0.1:55433 / y3management_test / postgres-test")
        yield database
    finally:
        database.close()


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep only the explicit integration-test opt-in, never use ambient app settings.
    for key in list(os.environ):
        if key.startswith("Y3_") and key != "Y3_TEST_DATABASE_URL":
            monkeypatch.delenv(key)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        database_url=SecretStr(
            "postgresql+psycopg://y3management_test:unit-example-only@127.0.0.1:55433/"
            "y3management_test"
        ),
    )
