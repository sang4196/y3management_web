"""Actual HTTPS normal Master issuance and recipient password completion."""

from pathlib import Path

import pytest

from tests.test_iam_browser import run_browser
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_actual_handoff_https_browser(
    password_app: tuple[Settings, Database, str], tmp_path: Path
) -> None:
    settings, db, password = password_app
    run_browser(settings, password, tmp_path, handoff_db=db)
