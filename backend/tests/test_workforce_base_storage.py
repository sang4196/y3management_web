# ruff: noqa: F811
"""Actual20/21 provenance, runtime and information-loss boundary."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import password_app  # noqa: F401
from tests.pt_catalog_seed import assert_revision_loss_guard
from tests.test_password_transition import migrate
from tests.test_workforce import Scene, scene  # noqa: F401
from tests.test_workforce_base import command, register, send
from tests.test_workforce_compensation_storage import projected
from y3management.application import create_app

pytestmark = pytest.mark.postgres
PARENT = "34ac47eb4324e57175b3663dc2457d6d122392d6"


def seed20(settings: Any, password: str, tmp_path: Path) -> Path:
    from tests.historical_backend import archive_backend, execute_original

    old = archive_backend(tmp_path, PARENT)
    private = old / "seed-input.json"
    private.write_text(json.dumps({"password": password}))
    private.chmod(0o600)
    execute_original(
        old,
        settings,
        """import json,os
os.environ['Y3_IAM_MODE']='password'
from pathlib import Path
from fastapi.testclient import TestClient
from tests.password_helpers import login_password
from tests.test_iam import ORIGIN,csrf
from tests.test_workforce import Scene
from tests.test_iam_trainer import TrainerScene
from tests.test_workforce_compensation import body,change
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();db=Database(cfg)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as c:
 login_password(c,json.loads(Path('seed-input.json').read_text())['password'])
 from tests.password_helpers import call
 branch=call(c,'/admin/branches',csrf(c),{'code':'BASE20','name':'가상20'}).json()['id']
 scene=Scene(c,db,branch);r=scene.send({**scene.body(),'base_salary_won':'100','base_salary_start_month':'2020-01'})
 assert r.status_code==201
 t=TrainerScene(scene,r.json()['trainer']['id'],c,'unused','unused')
 assert change(t,body(t,50,'7')).status_code==200
""",
    )
    return old


def test_real20_rf_history_survives_upgrade_inverse_and_runtime(
    password_app: Any, tmp_path: Path
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0020_workforce_compensation")
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current21 accepted20")
    old = seed20(settings, password, tmp_path)
    before = projected(db)
    migrate(settings, "upgrade", "head")
    after = projected(db)
    assert all(after[k] == value for k, value in before.items() if k != "alembic_version")
    with db.session() as s:
        assert (
            s.execute(text("SELECT compensation_version FROM workforce_trainers")).scalar_one() == 2
        )
        assert (
            s.execute(text("SELECT ledger_version FROM workforce_base_ledgers")).scalar_one() == 1
        )
    from tests.historical_backend import execute_original

    execute_original(
        old,
        settings,
        """import os
os.environ['Y3_IAM_MODE']='password'
from fastapi.testclient import TestClient
from y3management.application import create_app
from y3management.config import load_settings
try:
 with TestClient(create_app(load_settings())): started=True
except ValueError as e:
 assert str(e)=='APPLICATION_STARTUP_FAILED';started=False
assert not started
""",
    )
    migrate(settings, "downgrade", "0020_workforce_compensation")
    inverse = projected(db)
    assert all(inverse[k] == value for k, value in before.items())
    migrate(settings, "upgrade", "head")


@pytest.mark.parametrize(
    "damage",
    ["missing_initial", "snapshot_base", "current_base", "missing_ledger", "ledger_version"],
)
def test_preflight_and_inverse_fail_closed(password_app: Any, tmp_path: Path, damage: str) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0020_workforce_compensation")
    seed20(settings, password, tmp_path)
    if damage in {"missing_ledger", "ledger_version"}:
        migrate(settings, "upgrade", "head")
    statements = {
        "missing_initial": (
            "DELETE FROM audit_workforce_initial_events WHERE event_kind='initial_compensation'"
        ),
        "snapshot_base": "UPDATE workforce_initial_snapshots SET base_salary_won=101",
        "current_base": "UPDATE workforce_trainers SET base_salary_won=101",
        "missing_ledger": "DELETE FROM workforce_base_ledgers",
        "ledger_version": "UPDATE workforce_base_ledgers SET ledger_version=2",
    }
    with db.session() as s:
        s.execute(text(statements[damage]))
        s.commit()
    before = projected(db)
    if damage in {"missing_ledger", "ledger_version"}:
        migrate(settings, "downgrade", "0020_workforce_compensation", success=False)
    else:
        migrate(settings, "upgrade", "head", success=False)
    assert projected(db) == before


@pytest.mark.parametrize("kind", ["create", "edit", "cancel", "noop"])
def test_each_new_fact_blocks_inverse(scene: Scene, kind: str) -> None:
    ident = register(scene)
    result = send(
        scene, ident, command(scene, ident, start_month="2090-01", planned_amount_won="100")
    )
    assert result.status_code == 200
    cid = result.json()["committed_change"]["change_id"]
    if kind in {"edit", "cancel", "noop"}:
        extra: dict[str, Any] = {"expected_change_revision": 1}
        if kind != "cancel":
            extra["planned_amount_won"] = "100" if kind == "noop" else "1"
        assert (
            send(
                scene,
                ident,
                command(scene, ident, **extra),
                "/" + cid + "/" + ("cancel" if kind == "cancel" else "edit"),
            ).status_code
            == 200
        )
    before = projected(scene.db)
    assert_revision_loss_guard(
        scene.db, "0021_workforce_base_schedule.py", "BASE_SCHEDULE_HISTORY_PRESENT"
    )
    assert projected(scene.db) == before
