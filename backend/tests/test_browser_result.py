"""Both JS and Python evidence aggregators fail on missing/false/non-boolean checks."""

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.browser_result import load_required, validate_browser_report

MANIFESTS = sorted((Path(__file__).parent / "browser").glob("*checks.json"))


@pytest.mark.parametrize(
    "case", ["valid", "empty", "missing", "extra", "false", "integer", "wrong_type"]
)
@pytest.mark.parametrize("manifest", MANIFESTS, ids=lambda path: path.name)
def test_browser_evidence_strict_collection(case: str, manifest: Path) -> None:
    required = load_required(manifest)
    checks: dict[str, object] = dict.fromkeys(required, True)
    name = next(iter(required))
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
        validate_browser_report({"checks": value}, required)
    else:
        with pytest.raises(AssertionError):
            validate_browser_report({"checks": value}, required)
    root = Path(__file__).parent / "browser"
    env = {
        **os.environ,
        "Y3_BROWSER_RUN": str(root),
        "Y3_BROWSER_MANIFEST": manifest.name,
        "Y3_BROWSER_VALIDATE_ONLY": json.dumps(value),
    }
    result = subprocess.run(
        ["node", str(root / "s1.cjs")], env=env, capture_output=True, timeout=10
    )
    assert result.returncode == (0 if case == "valid" else 1)
    assert result.stdout == b"" and result.stderr == b""


@pytest.mark.parametrize("names", [[], ["duplicate", "duplicate"], [1], [""], {}])
def test_browser_manifest_rejects_invalid_names(names: object, tmp_path: Path) -> None:
    manifest = tmp_path / "required-checks.json"
    manifest.write_text(json.dumps(names))
    with pytest.raises(AssertionError, match="BROWSER_MANIFEST_INVALID"):
        load_required(manifest)
