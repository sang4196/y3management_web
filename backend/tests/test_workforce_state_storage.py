# ruff: noqa: F811
"""Actual parent seed, forward preservation and precise loss-guard branches."""

import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.test_iam import child_env
from tests.test_iam_mfa import mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_iam_trainer_roles_storage import migrate
from tests.test_workforce import Scene, scene  # noqa: F401
from tests.test_workforce_state import change, request
from tests.workforce_state_seed import register_legacy
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_parent_forward_origin_and_loss_guard(
    scene: Scene, mfa: tuple[Settings, Database, str, str], tmp_path: Path
) -> None:
    settings, db, _, _ = mfa
    assert migrate(settings, "downgrade", "0012_iam_trainer_roles") == 0
    fact = register_legacy(scene, settings, tmp_path)
    with db.session() as s:
        before = {
            table: s.execute(
                text("SELECT row_to_json(x)::text FROM " + table + " x ORDER BY 1")
            ).all()
            for table in (
                "iam_accounts",
                "iam_sessions",
                "iam_security_states",
                "workforce_trainers",
                "workforce_registration_operations",
                "audit_workforce_initial_events",
            )
        }
    assert migrate(settings, "upgrade", "head") == 0
    with db.session() as s:
        for table, rows in before.items():
            assert (
                s.execute(text("SELECT row_to_json(x)::text FROM " + table + " x ORDER BY 1")).all()
                == rows
            )
        row = s.execute(
            text(
                "SELECT origin,active,trainer_version,registration_operation_id "
                "FROM workforce_trainer_state_origins"
            )
        ).one()
        assert tuple(row) == ("legacy_observation", True, 1, None)
        assert s.execute(text("SELECT count(*) FROM audit_trainer_state_events")).scalar_one() == 0
    # Positive control: only observed baseline can be removed losslessly.
    assert migrate(settings, "downgrade", "0012_iam_trainer_roles") == 0
    assert migrate(settings, "upgrade", "head") == 0
    from contextlib import closing

    from fastapi.testclient import TestClient

    from tests.test_iam import ORIGIN

    with closing(TestClient(scene.client.app, base_url=ORIGIN)) as recipient:
        t = TrainerScene(scene, fact["id"], recipient, "unused", "unused")
        assert change(t, request(t, False)).status_code == 200
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0012_iam_trainer_roles"],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    )
    assert r.returncode != 0
    from tests.workforce_state_seed import assert_loss_guard

    assert_loss_guard(
        db, ["0013_workforce_trainer_state.py"], "trainer state facts must be preserved"
    )
    with db.session() as s:
        assert s.execute(text("SELECT active FROM workforce_trainers")).scalar_one() is False
        assert s.execute(text("SELECT count(*) FROM audit_trainer_state_events")).scalar_one() == 1


@pytest.mark.parametrize(
    "assignment",
    [
        "after_version=before_version",
        "after_active=before_active",
        "actor_role='TRAINER'",
        "account_id=gen_random_uuid()",
    ],
)
def test_typed_state_constraints(trainer: TrainerScene, assignment: str) -> None:
    assert change(trainer, request(trainer, False)).status_code == 200
    with trainer.base.db.session() as s, pytest.raises(IntegrityError):
        s.execute(text("UPDATE audit_trainer_state_events SET " + assignment))
        s.commit()


def test_noop_cannot_have_transition_and_registration_guard(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str]
) -> None:
    t = trainer
    payload = request(t, True)
    assert change(t, payload).json()["changed"] is False
    with t.base.db.session() as s, pytest.raises(IntegrityError):
        s.execute(
            text(
                "INSERT INTO workforce_trainer_state_transitions "
                "(organization_id,operation_id,trainer_id,before_active,after_active,before_version,"
                "after_version,recorded_at) SELECT organization_id,operation_id,"
                "trainer_id,true,false,"
                "before_version,before_version+1,recorded_at "
                "FROM workforce_trainer_state_operations"
            )
        )
        s.commit()
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0012_iam_trainer_roles"],
        env=child_env(mfa[0]),
        capture_output=True,
        timeout=30,
    )
    assert r.returncode != 0
    from tests.workforce_state_seed import assert_loss_guard

    assert_loss_guard(
        t.base.db, ["0013_workforce_trainer_state.py"], "trainer state facts must be preserved"
    )


def test_registration_origin_failure_rolls_back_all_initial_facts(scene: Scene) -> None:
    from tests.test_workforce import activity, counts

    with scene.db.session() as session:
        session.execute(
            text(
                "CREATE FUNCTION state_origin_failure() RETURNS trigger "
                "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic origin failure'; END $$"
            )
        )
        session.execute(
            text(
                "CREATE TRIGGER state_origin_failure BEFORE INSERT ON "
                "workforce_trainer_state_origins FOR EACH ROW "
                "EXECUTE FUNCTION state_origin_failure()"
            )
        )
        session.commit()
    before = activity(scene.db)
    assert scene.send(scene.body()).status_code == 503
    assert counts(scene.db) == (0, 0, 0, 0)
    assert activity(scene.db) == before
    with scene.db.session() as session:
        assert (
            session.execute(
                text("SELECT count(*) FROM workforce_trainer_state_origins")
            ).scalar_one()
            == 0
        )
        session.execute(
            text("DROP TRIGGER state_origin_failure ON workforce_trainer_state_origins")
        )
        session.execute(text("DROP FUNCTION state_origin_failure()"))
        session.commit()
