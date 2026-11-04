"""Reject incomplete browser evidence, including vacuous all([]) success."""

import json
from collections.abc import Collection
from pathlib import Path


def load_required(path: Path) -> frozenset[str]:
    names = json.loads(path.read_text())
    if (
        not isinstance(names, list)
        or not names
        or any(not isinstance(name, str) or not name for name in names)
        or len(set(names)) != len(names)
    ):
        raise AssertionError("BROWSER_MANIFEST_INVALID")
    return frozenset(names)


REQUIRED = load_required(Path(__file__).parent / "browser/required-checks.json")


def validate_browser_report(report: object, required: Collection[str] = REQUIRED) -> None:
    if not required or len(set(required)) != len(required):
        raise AssertionError("BROWSER_MANIFEST_INVALID")
    if not isinstance(report, dict) or not isinstance(report.get("checks"), dict):
        raise AssertionError("BROWSER_REPORT_INVALID")
    checks = report["checks"]
    if set(checks) != set(required) or any(value is not True for value in checks.values()):
        raise AssertionError("BROWSER_REPORT_INCOMPLETE")
