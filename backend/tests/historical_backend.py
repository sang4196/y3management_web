"""Pinned original backend executable for original-revision acceptance inputs.

Uses the existing pytest tmp_path/schema ownership and the archived lock file.
No current application fixtures, policies, dependencies or processes are substituted.
"""

import re
import subprocess
import tarfile
from pathlib import Path

from tests.test_iam import child_env
from y3management.config import Settings


def archive_backend(tmp_path: Path, revision: str) -> Path:
    archive = tmp_path / "original-backend.tar"
    with archive.open("wb") as output:
        result = subprocess.run(
            ["git", "archive", revision, "backend"],
            cwd=Path.cwd().parent,
            stdout=output,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    assert result.returncode == 0, "Pinned original backend archive failed"
    archive.chmod(0o600)
    with tarfile.open(archive) as saved:
        saved.extractall(tmp_path, filter="data")
    old = tmp_path / "backend"
    result = subprocess.run(
        ["uv", "sync", "--locked", "--project", str(old)], capture_output=True, timeout=120
    )
    assert result.returncode == 0, "Pinned original backend locked environment failed"
    return old


def execute_original(old: Path, settings: Settings, script: str) -> None:
    source = old / "owned-fixture.py"
    source.write_text(script)
    source.chmod(0o600)
    env = child_env(settings)
    env["Y3_IAM_MODE"] = "mfa"
    # The original ownership guard derives Compose ownership from its module path.
    # Verify the guard code is identical, then point only its location metadata at the
    # actual checkout. Do not bypass/replace guard checks or mutate Compose/the target.
    owner = Path.cwd() / "src/y3management/ownership.py"
    archived_owner = old / "src/y3management/ownership.py"
    assert archived_owner.read_bytes() == owner.read_bytes(), "Ownership guard changed"
    startup = old / "sitecustomize.py"
    startup.write_text(
        "import y3management.ownership as ownership\n"
        + "ownership.__file__ = "
        + repr(str(owner))
        + "\n"
    )
    startup.chmod(0o600)
    env["PYTHONPATH"] = str(old) + ":" + str(old / "src")
    result = subprocess.run(
        [str(old / ".venv/bin/python"), str(source)],
        cwd=old,
        env=env,
        capture_output=True,
        timeout=90,
    )
    if result.returncode:
        # Report only stack locations and exception type, never values/source lines/secrets.
        error = result.stderr.decode(errors="replace")
        frames = re.findall(r'File "([^"\n]+)", line (\d+), in ([^\n]+)', error)
        locations = [(Path(file).name, line, symbol) for file, line, symbol in frames]
        kinds = re.findall(r"^([A-Za-z_][A-Za-z_0-9]*(?:Error|Exception)):", error, re.M)
        raise AssertionError(f"Original lifecycle failed: {locations}; types={kinds}")
