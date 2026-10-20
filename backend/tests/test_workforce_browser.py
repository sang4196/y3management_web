# ruff: noqa: F811
"""Native trusted HTTPS registration with existing owned fixture cleanup."""

from pathlib import Path

import pytest

from tests.test_iam_browser import run_browser
from tests.test_iam_mfa import mfa  # noqa: F401
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_workforce_native(mfa: tuple[Settings, Database, str, str], tmp_path: Path) -> None:
    settings, _, password, token = mfa
    run_browser(settings, password, tmp_path, token, workforce=True)
