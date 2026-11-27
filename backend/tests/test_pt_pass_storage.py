# ruff: noqa: F811
"""Actual24 origin, original Member/Product histories, and bounded25 inverse."""

import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.historical_backend import archive_backend, execute_original
from tests.membership_seed import assert_revision_loss_guard, full_shape, projected
from tests.password_helpers import password_app  # noqa: F401
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_password_transition import migrate
from tests.test_pt_pass_issuance import issue, setup
from tests.test_workforce import scene  # noqa: F401
from y3management.application import create_app

pytestmark = pytest.mark.postgres
PARENT = "bfa1e1dec5c136ece20b8ed1e968db8715ac2de4"


def test_actual24_rows_and_shape_lossless25_inverse(password_app: Any, tmp_path: Path) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0024_membership_home_move")
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current25 accepted24")
    old = archive_backend(tmp_path, PARENT)
    (old / "seed-input.json").write_text(json.dumps({"password": password}))
    (old / "seed-input.json").chmod(0o600)
    execute_original(
        old,
        settings,
        """import json,os
os.environ['Y3_IAM_MODE']='password'
from pathlib import Path
from fastapi.testclient import TestClient
from tests.password_helpers import call,login_password
from tests.test_iam import ORIGIN,csrf
from tests.test_workforce import Scene
from tests.test_membership import body,send
from tests.test_membership_home import command,move
from tests.test_pt_catalog import body as catalog_body,send as catalog_send
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
from uuid import UUID, uuid4
cfg=load_settings();db=Database(cfg)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as c:
 login_password(c,json.loads(Path('seed-input.json').read_text())['password'])
 a=call(c,'/admin/branches',csrf(c),{'code':'OLD24-A','name':'원24 출발'}).json()['id']
 b=call(c,'/admin/branches',csrf(c),{'code':'OLD24-B','name':'원24 도착'}).json()['id']
 s=Scene(c,db,a);assert s.send(s.body()).status_code==201
 ident=send(s,body(s)).json()['committed_member']['id']
 assert send(s,{'operation_id':str(uuid4()),'expected_member_version':1},
  '/' + ident+'/deactivate').status_code==200
 assert move(s,ident,command(b,2)).status_code==200
 p=catalog_send(s,catalog_body(price_won='9'*1024)).json()['committed_product']['id']
 assert catalog_send(s,catalog_body(name='원24 상품 변경',expected_product_version=1),
  '/' + p).status_code==200
 assert catalog_send(s,{'operation_id':str(uuid4()),'expected_product_version':2},
  '/' + p+'/stop').status_code==200
""",
    )
    before, shape24 = projected(db), full_shape(db)
    migrate(settings, "upgrade", "head")
    assert all(projected(db)[k] == v for k, v in before.items() if k != "alembic_version")
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
    migrate(settings, "downgrade", "0024_membership_home_move")
    assert projected(db) == before and full_shape(db) == shape24
    migrate(settings, "upgrade", "head")


def test_issued_pass_receipt_audit_blocks_lossy_inverse(trainer: TrainerScene) -> None:
    s = trainer.base
    assert issue(s, setup(trainer)).status_code == 200
    before, shape25 = projected(s.db), full_shape(s.db)
    assert_revision_loss_guard(s.db, "0025_pt_pass_issuance.py", "PASS_ISSUANCE_HISTORY_PRESENT")
    assert projected(s.db) == before and full_shape(s.db) == shape25


@pytest.mark.parametrize(
    "damage", ["snapshot", "audit_actor", "audit_clock", "operation_member", "audit_branch_alias"]
)
def test_snapshot_and_typed_audit_exact_identity_cannot_be_tampered(
    trainer: TrainerScene, damage: str
) -> None:
    s = trainer.base
    assert issue(s, setup(trainer)).status_code == 200
    before = projected(s.db)
    with pytest.raises(IntegrityError):
        with s.db.engine.begin() as db:
            if damage == "snapshot":
                db.execute(text("UPDATE pt_passes SET price_won=price_won+1"))
            elif damage == "audit_actor":
                db.execute(text("UPDATE audit_pass_issue_events SET actor_id=:i"), {"i": uuid4()})
            elif damage == "audit_branch_alias":
                db.execute(
                    text("UPDATE audit_pass_issue_events SET actor_branch=:b"), {"b": UUID(int=0)}
                )
            elif damage == "audit_clock":
                db.execute(
                    text(
                        "UPDATE audit_pass_issue_events "
                        "SET recorded_at=recorded_at+interval '1 second'"
                    )
                )
            else:
                db.execute(text("UPDATE pt_pass_issue_operations SET member_id=:i"), {"i": uuid4()})
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert projected(s.db) == before


def test_zero_issued_operator_audit_cannot_alias_null(
    trainer: TrainerScene, password_app: Any
) -> None:
    from contextlib import closing

    from tests.password_helpers import login_password
    from tests.test_membership import grant_operator
    from tests.test_workforce_integrity import branch_actor

    t = trainer
    s = t.base
    command = setup(t)
    zero = str(UUID(int=0))
    with s.db.engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO organization_branches(id,organization_id,code,name) "
                "SELECT :z,organization_id,'ZERO-ISSUED','가상 영 지점' "
                "FROM organization_branches WHERE id=:b"
            ),
            {"z": UUID(int=0), "b": s.branch},
        )
    with closing(branch_actor(s, password_app[2])) as operator:
        grant_operator(s, "workforce.branch", zero)
        login_password(operator, password_app[2], "workforce.branch")
        command["issued_branch_id"] = zero
        result = issue(s, command, operator)
        assert result.status_code == 200
        before = projected(s.db)
        with pytest.raises(IntegrityError):
            with s.db.engine.begin() as db:
                db.execute(text("UPDATE audit_pass_issue_events SET actor_branch=NULL"))
                db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        assert projected(s.db) == before
