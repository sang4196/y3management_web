"""Actual trusted HTTPS Trainer setup, login, self service and administrator separation."""

from pathlib import Path

import pytest

from tests.test_iam_browser import run_browser
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_trainer_native(password_app: tuple[Settings, Database, str], tmp_path: Path) -> None:
    settings, _, password = password_app
    run_browser(settings, password, tmp_path, trainer=True)
