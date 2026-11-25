# ruff: noqa: F811
"""Actual parent21 runtime/data preservation,22 inverse and original lower guards."""

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.historical_backend import archive_backend, execute_original
from tests.password_helpers import password_app  # noqa: F401
from tests.pt_catalog_seed import assert_revision_loss_guard, prepare_revision_guard, projected
from tests.test_password_transition import migrate
from tests.test_pt_catalog import body, send
from tests.test_workforce import Scene, scene  # noqa: F401
from y3management.application import create_app

pytestmark = pytest.mark.postgres
PARENT = "538c7b7955e49a694da595d38d69c8940787b984"


def test_real21_rf_base_home_iam_preservation_empty_inverse_and_both_runtime_rejections(
    password_app: Any, tmp_path: Path
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0021_workforce_base_schedule")
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current22 accepted21")
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
from tests.password_helpers import login_password,call
from tests.test_iam import ORIGIN,csrf
from tests.test_workforce import Scene
from tests.test_iam_trainer import TrainerScene
from tests.test_workforce_compensation import body,change
from tests.test_workforce_base import command,send
from tests.test_workforce_home import destination,body as home_body,move
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();db=Database(cfg)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as c:
 login_password(c,json.loads(Path('seed-input.json').read_text())['password'])
 b=call(c,'/admin/branches',csrf(c),{'code':'ORIGINAL21','name':'가상원본21'}).json()['id']
 s=Scene(c,db,b)
 reg=s.send({**s.body(),'base_salary_won':'100','base_salary_start_month':'2020-01'})
 assert reg.status_code==201
 ident=reg.json()['trainer']['id'];t=TrainerScene(s,ident,c,'unused','unused')
 assert change(t,body(t,50,'7')).status_code==200
 planned=send(s,ident,command(s,ident,start_month='2090-01',planned_amount_won='3'))
 assert planned.status_code==200
 change_id=planned.json()['committed_change']['change_id']
 assert send(s,ident,command(s,ident,
  expected_change_revision=1,planned_amount_won='4'),'/'+change_id+'/edit').status_code==200
 assert send(s,ident,command(s,ident,
  expected_change_revision=2,planned_amount_won='4'),'/'+change_id+'/edit').status_code==200
 assert send(s,ident,command(s,ident,
  expected_change_revision=2),'/'+change_id+'/cancel').status_code==200
 assert send(s,ident,command(s,ident,start_month='2091-01',planned_amount_won='5')).status_code==200
 assert move(t,home_body(t,destination(t))).status_code==200
 pending=call(c,'/admin/master-accounts',csrf(c),{'login_id':'catalog.pending.original'})
 assert pending.status_code==201
""",
    )
    before = projected(db)
    migrate(settings, "upgrade", "head")
    after = projected(db)
    assert all(after[k] == v for k, v in before.items() if k != "alembic_version")
    with db.session() as s:
        assert (
            s.execute(text("SELECT compensation_version FROM workforce_trainers")).scalar_one() == 2
        )
        assert (
            s.execute(text("SELECT ledger_version FROM workforce_base_ledgers")).scalar_one() == 5
        )
        assert s.execute(text("SELECT count(*) FROM pt_products")).scalar_one() == 0
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
    migrate(settings, "downgrade", "0021_workforce_base_schedule")
    assert projected(db) == before
    migrate(settings, "upgrade", "head")


@pytest.mark.parametrize("kind", ["create", "update", "stop", "noop"])
def test_each_catalog_fact_blocks_destructive_inverse(scene: Scene, kind: str) -> None:
    s = scene
    r = send(s, body())
    assert r.status_code == 200
    ident = r.json()["committed_product"]["id"]
    if kind == "update":
        assert (
            send(s, body(expected_product_version=1, name="changed"), "/" + ident).status_code
            == 200
        )
    if kind == "stop":
        assert (
            send(
                s,
                {"operation_id": str(uuid4()), "expected_product_version": 1},
                "/" + ident + "/stop",
            ).status_code
            == 200
        )
    if kind == "noop":
        assert send(s, body(expected_product_version=1), "/" + ident).json()["changed"] is False
    before = projected(s.db)
    assert_revision_loss_guard(s.db, "0022_pt_product_catalog.py", "CATALOG_HISTORY_PRESENT")
    assert projected(s.db) == before


@pytest.mark.parametrize("damage", ["head", "policy"])
def test_schema_policy_preflight_before_ddl_leaves_every_row(scene: Scene, damage: str) -> None:
    db = scene.db
    with db.session() as s:
        if damage == "head":
            s.execute(text("UPDATE alembic_version SET version_num='0021_workforce_base_schedule'"))
        else:
            s.execute(
                text(
                    "UPDATE iam_policy_transitions "
                    "SET target_schema_revision='synthetic_policy_mismatch'"
                )
            )
        s.commit()
    before = projected(db)
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    script = scripts.get_revision("0022_pt_product_catalog")
    assert script is not None
    with db.engine.connect() as conn:
        tx = conn.begin()
        try:
            with pytest.raises(
                ValueError,
                match="CATALOG_SCHEMA_MISMATCH" if damage == "head" else "CATALOG_POLICY_MISMATCH",
            ):
                with Operations.context(MigrationContext.configure(conn)):
                    script.module.downgrade()
        finally:
            tx.rollback()
    assert projected(db) == before


def test_empty_catalog_adapter_reaches_actual21_and_keeps_original_base_guard(scene: Scene) -> None:
    s = scene
    reg = s.send({**s.body(), "base_salary_won": "100", "base_salary_start_month": "2020-01"})
    assert reg.status_code == 201
    from tests.test_workforce_base import command
    from tests.test_workforce_base import send as send_base

    ident = reg.json()["trainer"]["id"]
    assert (
        send_base(
            s, ident, command(s, ident, start_month="2090-01", planned_amount_won="1")
        ).status_code
        == 200
    )
    before = projected(s.db)
    with s.db.engine.connect() as conn:
        tx = conn.begin()
        try:
            prepare_revision_guard(conn, "0021_workforce_base_schedule")
            assert (
                MigrationContext.configure(conn).get_current_revision()
                == "0021_workforce_base_schedule"
            )
            assert not conn.execute(text("SELECT to_regclass('pt_products')")).scalar_one()
        finally:
            tx.rollback()
    assert_revision_loss_guard(
        s.db, "0021_workforce_base_schedule.py", "BASE_SCHEDULE_HISTORY_PRESENT"
    )
    assert projected(s.db) == before
