# ruff: noqa: F811
"""Actual committed 0012 W0 seed, distinct from current acceptance source."""

import json
import secrets
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.test_iam import ORIGIN, SyntheticSecret
from tests.test_iam_trainer import TrainerScene
from tests.test_iam_trainer_roles_storage import migrate
from tests.test_password_transition import legacy_database  # noqa: F401
from tests.test_workforce import Scene
from y3management.config import Settings
from y3management.database import Database

PARENT = "d55db2ef1e60d9ad8efa92b656545b348d8ab61a"


def register_legacy(settings: Settings, tmp_path: Path, password: str) -> dict[str, Any]:
    from tests.historical_backend import archive_backend, execute_original

    old = archive_backend(tmp_path, PARENT)
    private = old / "seed-input.json"
    private.write_text(json.dumps({"password": password}))
    private.chmod(0o600)
    execute_original(
        old,
        settings,
        """import json
from pathlib import Path
from fastapi.testclient import TestClient
from tests.test_iam import ORIGIN,csrf,cli_bootstrap
from tests.test_iam_mfa import Authenticator,call,enroll,login_mfa
from tests.test_workforce import Scene
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();data=json.loads(Path('seed-input.json').read_text())
private=Path('installer').absolute();private.mkdir(mode=0o700);output=private/'enrollment'
cli_bootstrap(cfg,data['password'],enrollment_file=output)
token=output.read_text().strip().split('#token=')[1]
db=Database(cfg)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as client:
 key=Authenticator();enroll(client,token,key);login_mfa(client,data['password'],key)
 branch=call(client,'/admin/branches',csrf(client),
  {'code':'OLD','name':'가상 이전 지점'}).json()['id']
 scene=Scene(client,db,branch); response=scene.send(scene.body());assert response.status_code==201
 result={'trainer':response.json()['trainer'],'branch':branch}
 Path('seed-output.json').write_text(json.dumps(result));Path('seed-output.json').chmod(0o600)
""",
    )
    return dict(json.loads((old / "seed-output.json").read_text()))


@pytest.fixture
def legacy_trainer(
    legacy_database: tuple[Settings, Database],
    tmp_path: Path,
) -> Iterator[TrainerScene]:
    from tests.password_helpers import login_password
    from y3management.application import create_app

    settings, db = legacy_database
    assert migrate(settings, "downgrade", "0012_iam_trainer_roles") == 0
    password = SyntheticSecret("Legacy test " + secrets.token_urlsafe(24))
    result = register_legacy(settings, tmp_path, password)
    assert migrate(settings, "upgrade", "head") == 0
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        login_password(client, password)
        with closing(TestClient(client.app, base_url=ORIGIN)) as recipient:
            yield TrainerScene(
                Scene(client, db, result["branch"]),
                result["trainer"]["id"],
                recipient,
                SyntheticSecret(secrets.token_urlsafe(24)),
                "legacy." + secrets.token_hex(8),
            )


def assert_loss_guard(db: Database, revisions: list[str], expected: str) -> None:
    """Execute actual revision functions in order, observe DB guard, then roll back all DDL."""
    import importlib.util

    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy.exc import DBAPIError

    with db.engine.connect() as connection:
        transaction = connection.begin()
        try:
            with pytest.raises(DBAPIError, match=expected):
                with Operations.context(MigrationContext.configure(connection)):
                    for name in revisions:
                        path = Path("alembic/versions") / name
                        spec = importlib.util.spec_from_file_location("guard_revision", path)
                        assert spec is not None and spec.loader is not None
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        module.downgrade()
        finally:
            transaction.rollback()
