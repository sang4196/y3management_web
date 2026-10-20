# ruff: noqa: F811
"""Actual trusted HTTPS, stopped web / operating CLI / restarted web recipient."""

from pathlib import Path

import pytest

from tests.test_iam_browser import run_browser
from tests.test_iam_mfa import mfa  # noqa: F401
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_actual_emergency_https_browser(
    mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    settings, db, password, token = mfa
    run_browser(settings, password, tmp_path, token, emergency_db=db)
