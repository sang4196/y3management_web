"""Actual committed 0012 W0 seed, distinct from current acceptance source."""

import json
import os
import secrets
import subprocess
import sys
import tarfile
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.test_iam import ORIGIN, SyntheticSecret, child_env, csrf
from tests.test_iam_trainer import TrainerScene
from tests.test_iam_trainer_roles_storage import migrate
from tests.test_workforce import Scene
from y3management.config import Settings
from y3management.database import Database

PARENT = "d55db2ef1e60d9ad8efa92b656545b348d8ab61a"


def register_legacy(scene: Scene, settings: Settings, tmp_path: Path) -> dict[str, Any]:
    archive = tmp_path / "parent.tar"
    with archive.open("wb") as out:
        r = subprocess.run(
            ["git", "archive", PARENT, "backend"],
            cwd=Path.cwd().parent,
            stdout=out,
            capture_output=False,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    assert r.returncode == 0
    with tarfile.open(archive) as saved:
        saved.extractall(tmp_path, filter="data")
    old = tmp_path / "backend"
    private = old / "seed-input.json"
    private.write_text(
        json.dumps(
            {
                "cookie": scene.client.cookies.get("__Host-y3-auth"),
                "branch": scene.branch,
                "nonce": csrf(scene.client),
                "body": scene.body(),
            }
        )
    )
    private.chmod(0o600)
    script = old / "seed.py"
    script.write_text("""import json
from pathlib import Path
from fastapi.testclient import TestClient
from tests.test_iam import ORIGIN, csrf
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();db=Database(cfg);data=json.loads(Path('seed-input.json').read_text())
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as client:
 client.cookies.set('__Host-y3-auth',data['cookie'])
 response=client.post('/api/v1/admin/trainers',json=data['body'],
  headers={'Origin':ORIGIN,'X-CSRF-Token':csrf(client)})
 assert response.status_code==201
 Path('seed-output.json').write_text(json.dumps(response.json()['trainer']))
""")
    env = child_env(settings)
    env["PYTHONPATH"] = str(old / "src")
    # Sequential real app lifespans: never overlap the parent and current ProcessGuard.
    scene.client.__exit__(None, None, None)
    try:
        r = subprocess.run(
            [sys.executable, str(script)], cwd=old, env=env, capture_output=True, timeout=60
        )
    finally:
        scene.client.__enter__()
    assert r.returncode == 0, "Actual IAM012 parent HTTP seed failed (private output suppressed)"
    os.chmod(old / "seed-output.json", 0o600)
    return dict(json.loads((old / "seed-output.json").read_text()))


@pytest.fixture
def legacy_trainer(
    scene: Scene, mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> Iterator[TrainerScene]:
    assert migrate(mfa[0], "downgrade", "0012_iam_trainer_roles") == 0
    fact = register_legacy(scene, mfa[0], tmp_path)
    assert migrate(mfa[0], "upgrade", "head") == 0
    with closing(TestClient(scene.client.app, base_url=ORIGIN)) as recipient:
        yield TrainerScene(
            scene,
            fact["id"],
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
