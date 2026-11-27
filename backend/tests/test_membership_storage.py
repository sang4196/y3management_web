# ruff: noqa: F811
"""Real22 origin facts, actual23 inverse and loss-safe typed relations."""

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
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from tests.historical_backend import archive_backend, execute_original
from tests.membership_seed import assert_revision_loss_guard, prepare_revision_guard, projected
from tests.membership_seed import full_shape as shape
from tests.password_helpers import password_app  # noqa: F401
from tests.test_membership import body, edit, send
from tests.test_password_transition import migrate
from tests.test_workforce import Scene, scene  # noqa: F401
from y3management.application import create_app

pytestmark = pytest.mark.postgres
PARENT = "62857f75cca460d28465dc7fb8db61060dcfc80f"


def test_actual22_old_rows_catalog_and_both_runtime_heads_empty_inverse(
    password_app: Any, tmp_path: Path
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0022_pt_product_catalog")
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current23 accepted22")
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
 b=call(c,'/admin/branches',csrf(c),{'code':'ORIGINAL22','name':'가상원본22'}).json()['id']
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
 from tests.test_workforce_state import change as state_change,request as state_request
 assert state_change(t,state_request(t,False)).status_code==200
 assert state_change(t,state_request(t,True)).status_code==200
 pending=call(c,'/admin/master-accounts',csrf(c),{'login_id':'catalog.pending.original'})
 assert pending.status_code==201
 from tests.test_pt_catalog import body as catalog_body,send as catalog_send
 original=catalog_body();created=catalog_send(s,original);assert created.status_code==200
 product=created.json()['committed_product']['id']
 assert catalog_send(s,
  catalog_body(name='원본22변경',expected_product_version=1),'/'+product).status_code==200
 assert catalog_send(s,{'operation_id':str(__import__('uuid').uuid4()),
  'expected_product_version':2},'/'+product+'/stop').status_code==200
 assert catalog_send(s,
  catalog_body(name='원본22변경',expected_product_version=3),'/'+product).json()['changed'] is False
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
        assert s.execute(text("SELECT count(*) FROM pt_products")).scalar_one() == 1
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
    migrate(settings, "downgrade", "0022_pt_product_catalog")
    assert projected(db) == before
    migrate(settings, "upgrade", "head")


@pytest.mark.parametrize("kind", ["create", "update", "deactivate", "reactivate", "noop"])
def test_each_new_membership_fact_blocks_lossy_inverse(scene: Scene, kind: str) -> None:
    s = scene
    ident = send(s, body(s)).json()["committed_member"]["id"]
    if kind == "update":
        assert send(s, edit(1), "/" + ident).status_code == 200
    if kind in {"deactivate", "reactivate"}:
        assert (
            send(
                s,
                {"operation_id": str(uuid4()), "expected_member_version": 1},
                "/" + ident + "/deactivate",
            ).status_code
            == 200
        )
    if kind == "reactivate":
        assert (
            send(
                s,
                {"operation_id": str(uuid4()), "expected_member_version": 2},
                "/" + ident + "/reactivate",
            ).status_code
            == 200
        )
    if kind == "noop":
        assert not send(s, edit(1, name="가상 회원"), "/" + ident).json()["changed"]
    before = projected(s.db)
    before_shape = shape(s.db)
    assert_revision_loss_guard(s.db, "0023_membership_basics.py", "MEMBERSHIP_HISTORY_PRESENT")
    assert projected(s.db) == before
    assert shape(s.db) == before_shape


@pytest.mark.parametrize("damage", ["head", "policy"])
def test_exact_head_policy_preflight_has_no_ddl(scene: Scene, damage: str) -> None:
    db = scene.db
    with db.engine.begin() as conn:
        if damage == "head":
            conn.execute(text("UPDATE alembic_version SET version_num='0022_pt_product_catalog'"))
        else:
            conn.execute(
                text("UPDATE iam_policy_transitions SET target_schema_revision='invalid-target'")
            )
    before = projected(db)
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    revision = scripts.get_revision("0023_membership_basics")
    assert revision is not None
    observed = []

    def observe(_conn: Any, _cursor: Any, sql: str, *args: Any) -> None:
        if sql.lstrip().upper().startswith(("CREATE ", "ALTER ", "DROP ")):
            observed.append(sql)

    with db.engine.connect() as conn:
        tx = conn.begin()
        event.listen(conn, "before_cursor_execute", observe)
        try:
            with pytest.raises(
                ValueError,
                match="MEMBERSHIP_SCHEMA_MISMATCH"
                if damage == "head"
                else "MEMBERSHIP_POLICY_MISMATCH",
            ):
                with Operations.context(MigrationContext.configure(conn)):
                    revision.module.downgrade()
        finally:
            event.remove(conn, "before_cursor_execute", observe)
            tx.rollback()
    assert not observed and projected(db) == before


def test_empty23_adapter_preserves_actual22_catalog_guard_before_target_ddl(scene: Scene) -> None:
    from tests.test_pt_catalog import body as catalog_body
    from tests.test_pt_catalog import send as catalog_send

    s = scene
    assert catalog_send(s, catalog_body()).status_code == 200
    before = projected(s.db)
    before_shape = shape(s.db)
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    revision = scripts.get_revision("0022_pt_product_catalog")
    assert revision is not None
    observed = []

    def observe(_conn: Any, _cursor: Any, sql: str, *args: Any) -> None:
        if sql.lstrip().upper().startswith(("CREATE ", "ALTER ", "DROP ")):
            observed.append(sql)

    with s.db.engine.connect() as conn:
        tx = conn.begin()
        try:
            prepare_revision_guard(conn, "0022_pt_product_catalog")
            assert (
                MigrationContext.configure(conn).get_current_revision() == "0022_pt_product_catalog"
            )
            assert conn.scalar(text("SELECT to_regclass('membership_members')")) is None
            event.listen(conn, "before_cursor_execute", observe)
            try:
                with pytest.raises(ValueError, match="CATALOG_HISTORY_PRESENT"):
                    with Operations.context(MigrationContext.configure(conn)):
                        revision.module.downgrade()
            finally:
                event.remove(conn, "before_cursor_execute", observe)
        finally:
            tx.rollback()
    assert not observed and projected(s.db) == before
    assert shape(s.db) == before_shape


@pytest.mark.parametrize("damage", ["core_actor", "before", "nullable_core", "role_branch"])
def test_small_typed_identity_and_nullable_before_do_not_bypass_core(
    scene: Scene, damage: str
) -> None:
    s = scene
    ident = send(s, body(s)).json()["committed_member"]["id"]
    assert send(s, edit(1), "/" + ident).status_code == 200
    before = projected(s.db)
    before_shape = shape(s.db)
    with pytest.raises(IntegrityError):
        with s.db.engine.begin() as conn:
            if damage == "core_actor":
                conn.execute(
                    text("UPDATE audit_member_events SET actor_id=:a WHERE before_version IS NULL"),
                    {"a": uuid4()},
                )
            elif damage == "before":
                conn.execute(
                    text("UPDATE audit_member_events SET before_version=2 WHERE before_version=1")
                )
            elif damage == "nullable_core":
                conn.execute(
                    text("UPDATE membership_member_versions SET actor_id=:a WHERE version=1"),
                    {"a": uuid4()},
                )
            else:
                conn.execute(
                    text(
                        "UPDATE audit_member_events SET actor_role='OPERATOR',actor_branch=:b "
                        "WHERE before_version IS NULL"
                    ),
                    {"b": s.branch},
                )
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert projected(s.db) == before
    assert shape(s.db) == before_shape
