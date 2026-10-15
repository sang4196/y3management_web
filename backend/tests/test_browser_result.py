"""Both JS and Python evidence aggregators fail on missing/false/non-boolean checks."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.browser_result import REQUIRED, validate_browser_report


@pytest.mark.parametrize(
    "case", ["valid", "empty", "missing", "extra", "false", "integer", "wrong_type"]
)
def test_browser_evidence_strict_collection(case: str) -> None:
    checks: dict[str, object] = dict.fromkeys(REQUIRED, True)
    name = next(iter(REQUIRED))
    if case == "empty":
        checks.clear()
    if case == "missing":
        checks.pop(name)
    if case == "extra":
        checks["unexpected"] = True
    if case == "false":
        checks[name] = False
    if case == "integer":
        checks[name] = 1
    value: object = [] if case == "wrong_type" else checks
    if case == "valid":
        validate_browser_report({"checks": value})
    else:
        with pytest.raises(AssertionError):
            validate_browser_report({"checks": value})
    root = Path(__file__).parent / "browser"
    env = {**os.environ, "Y3_BROWSER_RUN": str(root), "Y3_BROWSER_VALIDATE_ONLY": json.dumps(value)}
    result = subprocess.run(
        ["node", str(root / "s1.cjs")], env=env, capture_output=True, timeout=10
    )
    assert result.returncode == (0 if case == "valid" else 1)
    assert result.stdout == b"" and result.stderr == b""
