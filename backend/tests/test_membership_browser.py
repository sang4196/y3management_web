"""Short independent Membership profiles of the existing trusted native runner."""

from pathlib import Path

import pytest

from tests.test_iam_browser import run_browser
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_membership_native(password_app: tuple[Settings, Database, str], tmp_path: Path) -> None:
    settings, _, password = password_app
    run_browser(settings, password, tmp_path, membership=True)


def test_membership_races_native(
    password_app: tuple[Settings, Database, str], tmp_path: Path
) -> None:
    settings, _, password = password_app
    run_browser(settings, password, tmp_path, membership_races=True)


def test_membership_scope_native(
    password_app: tuple[Settings, Database, str], tmp_path: Path
) -> None:
    settings, _, password = password_app
    run_browser(settings, password, tmp_path, membership_scope=True)


def test_membership_home_native(
    password_app: tuple[Settings, Database, str], tmp_path: Path
) -> None:
    settings, _, password = password_app
    run_browser(settings, password, tmp_path, membership_home=True)
