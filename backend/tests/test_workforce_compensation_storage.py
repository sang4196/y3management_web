# ruff: noqa: F811
"""Actual19 origins, exact20 inverse, runtime boundaries and original Home guards."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.password_helpers import password_app  # noqa: F401
from tests.test_account_lifecycle import lifecycle_fingerprints
from tests.test_iam_trainer import (
    TrainerScene,
    trainer,  # noqa: F401
)
from tests.test_password_transition import migrate
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_compensation import body, change
from y3management.application import create_app

pytestmark = pytest.mark.postgres
PARENT = "7d9e5d05f8bccd27b0038a407ddab962b25da847"


def seed19(settings: Any, password: str, tmp_path: Path) -> Path:
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
from tests.password_helpers import login_password,call
from tests.test_iam import ORIGIN,csrf
from tests.test_workforce import Scene
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();db=Database(cfg)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as c:
 login_password(c,json.loads(Path('seed-input.json').read_text())['password'])
 branch=call(c,'/admin/branches',csrf(c),{'code':'ORIGINAL19','name':'가상 초기설정'}).json()['id']
 scene=Scene(c,db,branch);command=scene.body();r=scene.send(command);assert r.status_code==201
 assert call(c,'/admin/master-accounts',csrf(c),{'login_id':'other.creator'}).status_code==201
 Path('seed-output.json').write_text(json.dumps({'trainer':r.json()['trainer'],'command':command}))
 Path('seed-output.json').chmod(0o600)
""",
    )
    return old


def projected(db: Any) -> dict[str, str]:
    with db.session() as s:
        tables = list(
            s.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname=current_schema()")
            ).scalars()
        )
        return {
            table: s.execute(
                text(
                    "SELECT md5(COALESCE(string_agg("
                    "(to_jsonb(t)-'compensation_version')::text,',' ORDER BY "
                    "(to_jsonb(t)-'compensation_version')::text),'')) FROM " + table + " t"
                )
            ).scalar_one()
            for table in tables
        }


def test_real19_origin_clocks_full_preservation_runtime_and_empty_inverse(
    password_app: Any, tmp_path: Path
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0019_workforce_trainer_home")
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current20 accepted19")
    old = seed19(settings, password, tmp_path)
    before = projected(db)
    with db.session() as s:
        clocks = s.execute(
            text(
                "SELECT t.created_at,s.created_at,r.created_at,a.created_at "
                "FROM workforce_trainers t JOIN workforce_initial_snapshots s ON s.trainer_id=t.id "
                "JOIN workforce_registration_operations r ON r.trainer_id=t.id "
                "JOIN audit_workforce_initial_events a ON a.trainer_id=t.id "
                "WHERE a.event_kind='initial_compensation'"
            )
        ).one()
        assert clocks[0] == clocks[1] and len(set(clocks)) > 1
    migrate(settings, "upgrade", "head")
    after = projected(db)
    assert all(after[k] == v for k, v in before.items() if k != "alembic_version")
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
    # Only independent W1/Home metadata changes; compensation remains representable at19.
    with db.session() as s:
        s.execute(text("UPDATE workforce_trainers SET active=false,row_version=row_version+1"))
        s.commit()
    before = projected(db)
    migrate(settings, "downgrade", "0019_workforce_trainer_home")
    after = projected(db)
    assert all(
        after[k] == v
        for k, v in before.items()
        if k
        not in {"alembic_version", "workforce_compensation_operations", "audit_compensation_events"}
    )
    migrate(settings, "upgrade", "head")


@pytest.mark.parametrize(
    "damage",
    [
        "missing_initial",
        "wrong_initial_value",
        "wrong_creator",
        "wrong_context",
        "snapshot_time",
        "current_rate",
    ],
)
def test_preflight_rejects_original_contradictions_without_ddl(
    password_app: Any, tmp_path: Path, damage: str
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0019_workforce_trainer_home")
    seed19(settings, password, tmp_path)
    statements = {
        "missing_initial": (
            "DELETE FROM audit_workforce_initial_events WHERE event_kind='initial_compensation'"
        ),
        "wrong_initial_value": (
            "UPDATE audit_workforce_initial_events SET after_rate=1 "
            "WHERE event_kind='initial_compensation'"
        ),
        "wrong_creator": (
            "UPDATE audit_workforce_initial_events SET actor_id="
            "(SELECT id FROM iam_accounts WHERE login_id='other.creator') "
            "WHERE event_kind='initial_compensation'"
        ),
        "wrong_context": (
            "UPDATE audit_workforce_initial_events "
            "SET actor_role='BRANCH_ADMIN',actor_branch=target_home "
            "WHERE event_kind='initial_compensation'"
        ),
        "snapshot_time": (
            "UPDATE workforce_initial_snapshots SET created_at=created_at+interval '1 second'"
        ),
        "current_rate": "UPDATE workforce_trainers SET rate_percent=1",
    }
    with db.session() as s:
        s.execute(text(statements[damage]))
        s.commit()
    before = lifecycle_fingerprints(db)
    migrate(settings, "upgrade", "head", success=False)
    assert lifecycle_fingerprints(db) == before


@pytest.mark.parametrize("kind", ["noop", "changed", "version_only", "initial_mismatch"])
def test_compensation_information_loss_is_blocked(trainer: TrainerScene, kind: str) -> None:
    t = trainer
    if kind in {"noop", "changed"}:
        assert change(t, body(t, 0 if kind == "noop" else 1, "0")).status_code == 200
    else:
        with t.base.db.session() as s:
            s.execute(
                text(
                    "UPDATE workforce_trainers SET compensation_version=2"
                    if kind == "version_only"
                    else "UPDATE workforce_trainers SET rate_percent=1"
                )
            )
            s.commit()
    before = lifecycle_fingerprints(t.base.db)
    from tests.workforce_compensation_seed import assert_revision_loss_guard

    assert_revision_loss_guard(
        t.base.db,
        "0020_workforce_compensation.py",
        "COMPENSATION_ORIGINAL_INCONSISTENT"
        if kind == "initial_mismatch"
        else "COMPENSATION_HISTORY_PRESENT",
    )
    assert lifecycle_fingerprints(t.base.db) == before


def test_actual0019_guard_retains_home_receipt(trainer: TrainerScene) -> None:
    from tests.test_workforce_home import body as home_body
    from tests.test_workforce_home import destination, move
    from tests.workforce_compensation_seed import assert_revision_loss_guard

    t = trainer
    assert move(t, home_body(t, destination(t))).status_code == 200
    before = lifecycle_fingerprints(t.base.db)
    assert_revision_loss_guard(
        t.base.db, "0019_workforce_trainer_home.py", "TRAINER_HOME_HISTORY_PRESENT"
    )
    assert lifecycle_fingerprints(t.base.db) == before


def test_nonnullable_audit_identity_and_noop_cannot_be_audited(trainer: TrainerScene) -> None:
    t = trainer
    assert change(t, body(t)).status_code == 200
    before = lifecycle_fingerprints(t.base.db)
    attacks = [
        "UPDATE audit_compensation_events SET actor_role='BRANCH_ADMIN',actor_branch=target_home",
        "UPDATE audit_compensation_events SET actor_branch=target_home",
        "UPDATE audit_compensation_events SET actor_id=gen_random_uuid()",
        "UPDATE audit_compensation_events SET target_home=NULL",
        "UPDATE audit_compensation_events SET after_rate=before_rate,after_fixed=before_fixed",
        "UPDATE audit_compensation_events SET changed=false",
        "UPDATE audit_compensation_events SET before_fixed='NaN'::numeric",
    ]
    with t.base.db.session() as s:
        for statement in attacks:
            with pytest.raises(IntegrityError), s.begin_nested():
                s.execute(text(statement))
    assert lifecycle_fingerprints(t.base.db) == before
