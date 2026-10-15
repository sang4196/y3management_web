"""Destructive cleanup is exercised only on fresh, explicitly owned test runs."""

import json
import os
import re
import select
import signal
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest

from tests import conftest
from tests.conftest import (
    _qa_processes,
    qa_cleanup,
    qa_create,
    qa_finish,
    qa_read,
    qa_register_process,
    qa_root,
    qa_stop_process,
)


def child_result(result: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    matches = re.findall(rb"QA result: (\{[^\n]+\})", result.stdout)
    assert matches, "Owned child pytest did not report its result"
    return cast(dict[str, Any], json.loads(matches[-1]))


@pytest.fixture
def runs() -> Iterator[Callable[[str], Path]]:
    made: list[Path] = []

    def create(mode: str = "auto") -> Path:
        path = qa_create(mode)
        made.append(path)
        return path

    yield create
    for path in made:
        if path.exists():
            qa_finish(path, "review-complete")
            plan = qa_cleanup(path)
            assert not plan.get("held"), "Fresh test run still owns live resources"
            qa_cleanup(path, dry_run=False, expected_plan=str(plan["plan"]))


def test_completed_run_dry_run_and_idempotent_cleanup(runs: Callable[[str], Path]) -> None:
    run = runs("auto")
    (run / "temporary.db").write_text("synthetic data")
    qa_finish(run, "complete")
    plan = qa_cleanup(run)
    assert run.exists() and not plan["removed"]
    actual = qa_cleanup(run, dry_run=False, expected_plan=str(plan["plan"]))
    assert actual["plan"] == plan["plan"] and actual["removed"] and not run.exists()
    assert qa_cleanup(run, dry_run=False)["absent"]


def test_failed_reproduction_and_manual_review_are_preserved(
    runs: Callable[[str], Path],
) -> None:
    failure = runs("auto")
    qa_finish(failure, "retained", "unresolved synthetic reproduction")
    assert qa_cleanup(failure).get("held") and failure.exists()
    assert qa_read(failure)["cleanup_condition"]
    manual = runs("manual")
    qa_finish(manual, "complete")
    assert qa_cleanup(manual).get("held") and manual.exists()


def test_uncleared_owned_database_resource_preserves_run(
    runs: Callable[[str], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = runs("auto")
    with monkeypatch.context() as patch:
        patch.setattr(conftest, "_qa_path", run)
        conftest.qa_record_schema("iam_test_" + "0" * 32, True)
        qa_finish(run, "failed")
        assert qa_cleanup(run).get("held") and run.exists()
        conftest.qa_record_schema("iam_test_" + "0" * 32, False)
        assert not qa_cleanup(run).get("held")


def test_other_runs_original_and_symlink_target_are_protected(
    runs: Callable[[str], Path],
    tmp_path: Path,
) -> None:
    target, other = runs("auto"), runs("manual")
    original = tmp_path / "original-media"
    original.mkdir()
    (original / "keep").write_text("original")
    (target / "external").symlink_to(original, target_is_directory=True)
    qa_finish(target, "complete")
    plan = qa_cleanup(target)
    qa_cleanup(target, dry_run=False, expected_plan=str(plan["plan"]))
    assert (original / "keep").read_text() == "original" and other.exists()
    with pytest.raises(ValueError, match="QA_OUTSIDE_OWNED_ROOT"):
        qa_cleanup(original, dry_run=False)


def test_unknown_marker_redirect_and_changed_plan_fail_closed(
    runs: Callable[[str], Path],
    tmp_path: Path,
) -> None:
    run = runs("auto")
    qa_finish(run, "complete")
    plan = qa_cleanup(run)
    (run / "new-file").touch()
    with pytest.raises(ValueError, match="QA_CLEANUP_PLAN_CHANGED"):
        qa_cleanup(run, dry_run=False, expected_plan=str(plan["plan"]))
    alias = qa_root() / (run.name + "-alias")
    alias.symlink_to(run, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="QA_OUTSIDE_OWNED_ROOT"):
            qa_cleanup(alias, dry_run=False)
        assert run.exists()
    finally:
        alias.unlink()
    original_marker = (run / "run.json").read_bytes()
    (run / "run.json").write_text("{}")
    try:
        with pytest.raises(ValueError, match="QA_OWNERSHIP_MISMATCH"):
            qa_cleanup(run, dry_run=False)
        assert run.exists()
    finally:
        (run / "run.json").write_bytes(original_marker)


def test_owned_process_stop_and_reused_identity_protection(runs: Callable[[str], Path]) -> None:
    run = runs("auto")
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    qa_register_process(process, run)
    identity = _qa_processes[process.pid].copy()
    try:
        qa_finish(run, "complete")
        assert qa_cleanup(run).get("held")
        _qa_processes[process.pid]["start_ticks"] = "mismatched"
        with pytest.raises(ValueError, match="QA_PROCESS_IDENTITY_CHANGED"):
            qa_stop_process(process)
        assert process.poll() is None
    finally:
        _qa_processes[process.pid] = identity
        qa_stop_process(process)
    assert process.poll() is not None and not qa_cleanup(run).get("held")


def test_forced_interruption_is_discoverable(runs: Callable[[str], Path]) -> None:
    code = (
        "from tests.conftest import qa_create; import time; "
        "print(qa_create().name, flush=True); time.sleep(30)"
    )
    process = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE)
    qa_register_process(process)
    assert process.stdout is not None
    descriptor = os.pidfd_open(process.pid)
    run: Path | None = None
    try:
        assert select.select([process.stdout], [], [], 5)[0]
        run = qa_root() / process.stdout.readline().decode().strip()
        signal.pidfd_send_signal(descriptor, signal.SIGKILL)
        process.wait(timeout=5)
        assert qa_read(run)["observed_state"] == "interrupted"
        assert qa_cleanup(run).get("held")
    finally:
        os.close(descriptor)
        if process.poll() is None:
            qa_stop_process(process)
        process.stdout.close()
        if run is not None and run.exists():
            qa_finish(run, "failed")
            plan = qa_cleanup(run)
            qa_cleanup(run, dry_run=False, expected_plan=str(plan["plan"]))


@pytest.mark.parametrize("fail", [False, True])
def test_pytest_completion_keeps_minimal_result_and_removes_environment(
    tmp_path: Path,
    fail: bool,
) -> None:
    script = tmp_path / "test_synthetic_qa.py"
    script.write_text("def test_result(tmp_path):\n    assert " + str(not fail) + "\n")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--noconftest",
            "-p",
            "tests.conftest",
            "--rootdir",
            str(tmp_path),
            "-q",
            str(script),
        ],
        env={k: v for k, v in os.environ.items() if not k.startswith("Y3_")},
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == (1 if fail else 0), "Synthetic pytest exit changed"
    summary = child_result(result)
    assert summary["exit_code"] == (1 if fail else 0) and summary["cleanup"]["removed"]
    assert not (qa_root() / summary["run_id"]).exists()
    assert bool(summary["failed_tests"]) == fail


def test_cleanup_failure_keeps_environment_and_preceding_evidence(tmp_path: Path) -> None:
    (tmp_path / "test_synthetic.py").write_text("def test_result():\n    pass\n")
    (tmp_path / "qa_failure_plugin.py").write_text(
        "def pytest_sessionstart(session):\n"
        "    import json\n"
        "    import tests.conftest as qa\n"
        "    run = qa._qa_path\n"
        "    original = qa.qa_cleanup\n"
        "    def failed_cleanup(path, *, dry_run=True, expected_plan=None):\n"
        "        if dry_run:\n"
        "            return original(path)\n"
        "        result = json.loads((run / 'result.json').read_text())\n"
        "        assert result['run_id'] == path.name\n"
        "        raise OSError('synthetic cleanup fault')\n"
        "    qa.qa_cleanup = failed_cleanup\n"
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("Y3_")}
    env["PYTHONPATH"] = str(tmp_path) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--noconftest",
            "-p",
            "tests.conftest",
            "-p",
            "qa_failure_plugin",
            "--rootdir",
            str(tmp_path),
            "-q",
            str(tmp_path / "test_synthetic.py"),
        ],
        env=env,
        capture_output=True,
        timeout=20,
    )
    summary = child_result(result)
    run = qa_root() / summary["run_id"]
    try:
        assert result.returncode == 1 and summary["exit_code"] == 1
        assert not summary["cleanup"]["removed"] and run.exists()
        assert summary["cleanup"]["path"] == str(run)
    finally:
        qa_finish(run, "failed")
        plan = qa_cleanup(run)
        qa_cleanup(run, dry_run=False, expected_plan=str(plan["plan"]))
