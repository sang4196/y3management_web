"""Reject incomplete browser evidence, including vacuous all([]) success."""

import json
from pathlib import Path

REQUIRED: frozenset[str] = frozenset(
    json.loads((Path(__file__).parent / "browser/required-checks.json").read_text())
)


def validate_browser_report(report: object) -> None:
    if not isinstance(report, dict) or not isinstance(report.get("checks"), dict):
        raise AssertionError("BROWSER_REPORT_INVALID")
    checks = report["checks"]
    if set(checks) != REQUIRED or any(value is not True for value in checks.values()):
        raise AssertionError("BROWSER_REPORT_INCOMPLETE")
