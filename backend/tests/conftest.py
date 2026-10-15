import hashlib
import json
import os
import shutil
import signal
import subprocess
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.engine import make_url

from y3management.config import Settings
from y3management.database import Database

_db_tests: set[str] = set()
_db_passed: set[str] = set()
_db_incomplete: set[str] = set()
_qa_path: Path | None = None
_qa_failures: set[str] = set()
_qa_passed = 0
_qa_processes: dict[int, dict[str, object]] = {}
_repository = Path(__file__).resolve().parents[2]


def qa_root() -> Path:
    """Existing pytest runner's private scratch root; never follow a redirected root."""
    root = _repository / ".local" / "qa"
    for path in (root.parent, root):
        if path.is_symlink():
            raise ValueError("QA_ROOT_SYMLINK")
        path.mkdir(mode=0o700, exist_ok=True)
    return root


def _qa_write(path: Path, value: dict[str, object]) -> None:
    temporary = path.with_name(".qa-write-" + uuid4().hex)
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            os.chmod(temporary, 0o600)
            json.dump(value, stream, indent=2)
            stream.write("\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _process_identity(pid: int) -> dict[str, object] | None:
    try:
        proc = Path("/proc") / str(pid)
        fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            return None
        return {
            "pid": pid,
            "start_ticks": fields[19],
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        }
    except (OSError, IndexError):
        return None


def qa_create(mode: str = "auto") -> Path:
    if mode not in {"auto", "manual"}:
        raise ValueError("QA_INVALID_MODE")
    path = qa_root() / (mode + "-" + uuid4().hex)
    path.mkdir(mode=0o700)
    st = path.stat()
    _qa_write(
        path / "run.json",
        {
            "marker": "y3management-pytest-v1",
            "project": str(_repository),
            "run_id": path.name,
            "mode": mode,
            "state": "active",
            "created_at": datetime.now(UTC).isoformat(),
            "device": st.st_dev,
            "inode": st.st_ino,
            "uid": st.st_uid,
            "owner": _process_identity(os.getpid()),
            "processes": [],
            "retain_reason": "manual review pending" if mode == "manual" else "",
        },
    )
    return path


def qa_read(path: Path) -> dict[str, object]:
    root = qa_root()
    if path.parent != root or path.is_symlink() or path.resolve() != path:
        raise ValueError("QA_OUTSIDE_OWNED_ROOT")
    marker = path / "run.json"
    if marker.is_symlink():
        raise ValueError("QA_MARKER_SYMLINK")
    value = json.loads(marker.read_text())
    st = path.stat()
    if (
        not isinstance(value, dict)
        or value.get("marker") != "y3management-pytest-v1"
        or value.get("project") != str(_repository)
        or value.get("run_id") != path.name
        or value.get("mode") not in {"auto", "manual"}
        or (value.get("device"), value.get("inode"), value.get("uid"))
        != (st.st_dev, st.st_ino, os.getuid())
    ):
        raise ValueError("QA_OWNERSHIP_MISMATCH")
    owner = value.get("owner")
    value["observed_state"] = (
        "interrupted"
        if value.get("state") == "active"
        and isinstance(owner, dict)
        and _process_identity(int(owner["pid"])) != owner
        else value.get("state")
    )
    return cast(dict[str, object], value)


def qa_finish(path: Path, state: str, reason: str = "") -> None:
    if state not in {"complete", "failed", "review-complete", "retained"}:
        raise ValueError("QA_INVALID_STATE")
    if state == "retained" and not reason.strip():
        raise ValueError("QA_RETAIN_REASON_REQUIRED")
    value = qa_read(path)
    value.update(
        state=state,
        retain_reason=reason,
        cleanup_condition="review/reproduction resolved and no live process",
    )
    _qa_write(path / "run.json", value)


def qa_cleanup(
    path: Path, *, dry_run: bool = True, expected_plan: str | None = None
) -> dict[str, object]:
    # A missing previously named run is an idempotent no-op; never inspect a different root.
    if path.parent != qa_root() or path.is_symlink():
        raise ValueError("QA_OUTSIDE_OWNED_ROOT")
    if not path.exists():
        return {"path": str(path), "removed": False, "absent": True}
    value = qa_read(path)
    owner = value.get("owner")
    live_owner = (
        isinstance(owner, dict)
        and owner.get("pid") != os.getpid()
        and _process_identity(int(owner["pid"])) == owner
    )
    children = cast(list[dict[str, object]], value.get("processes", []))
    live = any(_process_identity(int(cast(int, p["pid"]))) == p for p in children)
    resources = cast(dict[str, bool], value.get("test_schemas", {}))
    live = live or any(resources.values())
    # Also protect a manually started server whose certificate/profile path is in this run.
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            if str(path).encode() in (proc / "cmdline").read_bytes():
                live = True
            if os.readlink(proc / "cwd").startswith(str(path) + "/"):
                live = True
            for descriptor in (proc / "fd").iterdir():
                try:
                    if os.readlink(descriptor).startswith(str(path) + "/"):
                        live = True
                except OSError:
                    continue
        except OSError:
            continue
    state = value.get("state")
    if (
        live_owner
        or live
        or state == "retained"
        or (value.get("mode") == "manual" and state != "review-complete")
        or state not in {"complete", "failed", "review-complete"}
    ):
        return {
            "path": str(path),
            "removed": False,
            "held": True,
            "reason": "active, pending review, retained, or unresolved ownership",
        }
    entries: list[str] = []
    for parent, directories, files in os.walk(path, followlinks=False):
        for name in [*directories, *files]:
            entry = Path(parent) / name
            entries.append(str(entry.relative_to(path)))
        directories[:] = [n for n in directories if not (Path(parent) / n).is_symlink()]
    digest = hashlib.sha256(json.dumps(sorted(entries)).encode()).hexdigest()
    result: dict[str, object] = {
        "path": str(path),
        "plan": digest,
        "entries": len(entries),
        "removed": False,
    }
    if not dry_run:
        if expected_plan != digest:
            raise ValueError("QA_CLEANUP_PLAN_CHANGED")
        if not shutil.rmtree.avoids_symlink_attacks:
            raise ValueError("QA_SAFE_RMTREE_UNAVAILABLE")
        qa_read(path)
        shutil.rmtree(path)
        result["removed"] = True
    return result


def qa_register_process(
    process: subprocess.Popen[bytes], run: Path | None = None, port: int | None = None
) -> None:
    identity = _process_identity(process.pid)
    if identity is None:
        return
    _qa_processes[process.pid] = identity
    destination = run if run is not None else _qa_path
    if destination is not None:
        value = qa_read(destination)
        children = cast(list[dict[str, object]], value.get("processes", []))
        value["processes"] = [p for p in children if p.get("pid") != process.pid] + [identity]
        if port is not None:
            ports = cast(list[int], value.get("ports", []))
            value["ports"] = sorted({*ports, port})
        _qa_write(destination / "run.json", value)


def qa_record_schema(name: str, active: bool) -> None:
    """Record only verified fixture-owned schema identity, never a database URL."""
    if _qa_path is not None:
        value = qa_read(_qa_path)
        resources = cast(dict[str, bool], value.get("test_schemas", {}))
        resources[name] = active
        value["test_schemas"] = resources
        _qa_write(_qa_path / "run.json", value)


def qa_stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    descriptor = os.pidfd_open(process.pid)
    try:
        if _process_identity(process.pid) != _qa_processes.get(process.pid):
            raise ValueError("QA_PROCESS_IDENTITY_CHANGED")
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            process.wait(timeout=5)
    finally:
        os.close(descriptor)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-postgres",
        action="store_true",
        help="Require collected PostgreSQL tests and real passes",
    )


def pytest_configure(config: pytest.Config) -> None:
    global _qa_path, _qa_passed
    _db_tests.clear()
    _db_passed.clear()
    _db_incomplete.clear()
    _qa_failures.clear()
    _qa_processes.clear()
    _qa_passed = 0
    # Synthetic copied conftest probes and explicit caller basetemp remain caller-owned.
    if (
        _repository.joinpath("backend", "pyproject.toml").is_file()
        and not config.option.basetemp
        and os.name == "posix"
    ):
        _qa_path = qa_create()
        config.option.basetemp = str(_qa_path / "pytest")


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    _db_tests.update(item.nodeid for item in items if item.get_closest_marker("postgres"))
    if config.getoption("--require-postgres") and not _db_tests:
        raise pytest.UsageError("Required PostgreSQL suite selected no postgres tests")
    if _db_tests and not os.environ.get("Y3_TEST_DATABASE_URL"):
        raise pytest.UsageError("Y3_TEST_DATABASE_URL is required; no development DB fallback")


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    global _qa_passed
    if report.failed:
        _qa_failures.add(report.nodeid.split("[", 1)[0])
    if report.when == "call" and report.passed:
        _qa_passed += 1
    if report.nodeid in _db_tests:
        if report.skipped or hasattr(report, "wasxfail"):
            _db_incomplete.add(report.nodeid)
        if report.when == "call" and report.passed:
            _db_passed.add(report.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    global _qa_path
    if exitstatus == 0 and (_db_incomplete or _db_tests - _db_passed):
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_line("Required PostgreSQL verification incomplete (skip/xfail/no pass)")
    if _qa_path is not None:
        path, _qa_path = _qa_path, None
        summary: dict[str, object] = {
            "run_id": path.name,
            "finished_at": datetime.now(UTC).isoformat(),
            "exit_code": int(session.exitstatus),
            "passed": _qa_passed,
            "failed_tests": sorted(_qa_failures),
            "cleanup": {"removed": False, "state": "pending"},
        }
        try:
            # Publish the minimal failure/pass evidence before removing any run files.
            _qa_write(path / "result.json", summary)
            _qa_write(qa_root() / "latest-auto.json", summary)
            qa_finish(path, "complete" if session.exitstatus == 0 else "failed")
            plan = qa_cleanup(path)
            summary["cleanup"] = qa_cleanup(
                path, dry_run=False, expected_plan=cast(str, plan.get("plan"))
            )
            if not cast(dict[str, object], summary["cleanup"]).get("removed"):
                session.exitstatus = pytest.ExitCode.TESTS_FAILED
        except Exception:
            summary["cleanup"] = {
                "removed": False,
                "path": str(path),
                "error": "QA_CLEANUP_FAILED_INSPECT_OWNED_RUN",
            }
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
        summary["exit_code"] = int(session.exitstatus)
        _qa_write(qa_root() / "latest-auto.json", summary)
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_line("QA result: " + json.dumps(summary))


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
