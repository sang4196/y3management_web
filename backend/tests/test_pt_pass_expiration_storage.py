# ruff: noqa: F811
"""Actual25 issuance origin and loss-safe independent state history migration."""

import json
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.historical_backend import archive_backend, execute_original
from tests.membership_seed import assert_revision_loss_guard, full_shape, projected
from tests.password_helpers import password_app  # noqa: F401
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_password_transition import migrate
from tests.test_pt_pass_expiration import body, change, created
from tests.test_workforce import scene  # noqa: F401
from y3management.application import create_app

pytestmark = pytest.mark.postgres
PARENT = "5d76593d0b2d8cc6fa116c754f277d26a83c8409"


def test_actual25_issued_pass_backfill_and_lossless26_inverse(
    password_app: Any, tmp_path: Path
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0025_pt_pass_issuance")
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current26 accepted25")
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
from tests.test_iam_trainer import TrainerScene
from tests.test_pt_pass_issuance import setup,issue
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();db=Database(cfg)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as c:
 login_password(c,json.loads(Path('seed-input.json').read_text())['password'])
 b=call(c,'/admin/branches',csrf(c),{'code':'OLD25','name':'가상 원25'}).json()['id']
 s=Scene(c,db,b);tr=s.send(s.body()).json()['trainer']['id']
 t=TrainerScene(s,tr,c,'unused','unused');command=setup(t,price_won='9'*1024,session_count='7')
 r=issue(s,command);assert r.status_code==200
 assert issue(s,command).json()==r.json()
""",
    )
    before, shape25 = projected(db), full_shape(db)
    migrate(settings, "upgrade", "head")
    assert all(projected(db)[k] == v for k, v in before.items() if k != "alembic_version")
    with db.session() as session:
        assert session.scalar(text("SELECT count(*) FROM pt_pass_state_heads")) == 1
        assert (
            session.scalar(
                text(
                    "SELECT count(*) FROM pt_pass_state_versions s JOIN pt_passes p "
                    "ON p.id=s.pass_id WHERE s.version=1 AND NOT "
                    "s.manual_expired AND s.recorded_at=p.issued_at"
                )
            )
            == 1
        )
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
    migrate(settings, "downgrade", "0025_pt_pass_issuance")
    assert projected(db) == before and full_shape(db) == shape25
    migrate(settings, "upgrade", "head")


@pytest.mark.parametrize("kind", ["expire", "release", "noop"])
def test_state_or_receipt_blocks_lossy_inverse(trainer: TrainerScene, kind: str) -> None:
    s = trainer.base
    ident, _, _ = created(trainer)
    if kind != "noop":
        assert change(s, ident, body(1)).status_code == 200
    if kind == "release":
        assert change(s, ident, body(2, False)).status_code == 200
    if kind == "noop":
        assert not change(s, ident, body(1, False)).json()["changed"]
    before, shape26 = projected(s.db), full_shape(s.db)
    assert_revision_loss_guard(s.db, "0026_pt_pass_expiration.py", "PASS_STATE_HISTORY_PRESENT")
    assert projected(s.db) == before and full_shape(s.db) == shape26


@pytest.mark.parametrize(
    "damage",
    ["audit_branch_alias", "audit_reason", "audit_before", "version_nullable_core", "version_time"],
)
def test_typed_actor_reason_before_and_time_cannot_bypass_original_command(
    trainer: TrainerScene, damage: str
) -> None:
    s = trainer.base
    ident, _, _ = created(trainer)
    assert change(s, ident, body(1)).status_code == 200
    before = projected(s.db)
    with pytest.raises(IntegrityError):
        with s.db.engine.begin() as db:
            if damage == "audit_branch_alias":
                db.execute(
                    text("UPDATE audit_pass_state_events SET actor_branch=:b"), {"b": UUID(int=0)}
                )
            elif damage == "audit_reason":
                db.execute(text("UPDATE audit_pass_state_events SET reason='다른 사유'"))
            elif damage == "audit_before":
                db.execute(text("UPDATE audit_pass_state_events SET before_version=after_version"))
            elif damage == "version_nullable_core":
                db.execute(
                    text(
                        "UPDATE pt_pass_state_versions SET source_operation_id=NULL WHERE version=2"
                    )
                )
            else:
                db.execute(
                    text(
                        "UPDATE pt_pass_state_versions SET "
                        "recorded_at=before_recorded_at-interval '1 second' "
                        "WHERE version=2"
                    )
                )
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert projected(s.db) == before
