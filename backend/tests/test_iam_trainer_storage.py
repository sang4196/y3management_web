# ruff: noqa: F811
"""Typed audit constraints, source GC and forward migration preservation."""

import subprocess
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.test_iam import child_env
from tests.test_iam_mfa import mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, counts, source, trainer  # noqa: F401
from tests.test_workforce import scene  # noqa: F401
from y3management.config import Settings
from y3management.database import Database
from y3management.uow import UnitOfWork

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize(
    "assignment",
    [
        "actor_id=NULL",
        "actor_role='TRAINER'",
        "operation_id=NULL",
        "after_security_version=NULL",
        "before_version=1",
        "after_state='ACTIVE'",
    ],
)
def test_issue_audit_rejects_null_or_wrong_transition(
    trainer: TrainerScene, assignment: str
) -> None:
    source(trainer.issue())
    with trainer.base.db.session() as s, pytest.raises(IntegrityError):
        s.execute(
            text("UPDATE audit_trainer_identity_events SET " + assignment + " WHERE kind='issue'")
        )
    assert counts(trainer) == (1, 1, 1, 1)


def test_gc_preserves_operation_and_binding(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str]
) -> None:
    source(trainer.issue())
    with trainer.base.db.session() as s:
        s.execute(text("UPDATE iam_trainer_setup_credentials SET consumed=true"))
        s.commit()
    with UnitOfWork(trainer.base.db, mfa[0]).open() as w:
        slot = w.security.allocate("credential")
        w.security.release(slot)
    assert counts(trainer) == (1, 1, 0, 1)
    assert trainer.complete(source(trainer.reissue())).status_code == 204


def test_identity_history_blocks_downgrade(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str]
) -> None:
    source(trainer.issue())
    before = counts(trainer)
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0010_workforce_initial"],
        env=child_env(mfa[0]),
        capture_output=True,
        timeout=30,
    )
    assert r.returncode != 0 and counts(trainer) == before
    with trainer.base.db.session() as s:
        assert (
            s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0011_iam_trainer_login"
        )


def test_blank_identity_tables_roundtrip(mfa: tuple[Settings, Database, str, str]) -> None:
    for direction, revision in [("downgrade", "0010_workforce_initial"), ("upgrade", "head")]:
        r = subprocess.run(
            [sys.executable, "-m", "alembic", direction, revision],
            env=child_env(mfa[0]),
            capture_output=True,
            timeout=30,
        )
        assert r.returncode == 0
    with mfa[1].session() as s:
        assert s.execute(text("SELECT count(*) FROM iam_trainer_bindings")).scalar_one() == 0


def test_unique_trainer_and_account_bindings(trainer: TrainerScene) -> None:
    source(trainer.issue())
    with trainer.base.db.session() as s, pytest.raises(IntegrityError):
        s.execute(text("INSERT INTO iam_trainer_bindings SELECT * FROM iam_trainer_bindings"))
    assert counts(trainer) == (1, 1, 1, 1)


def test_gc_skips_owned_locked_source(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str]
) -> None:
    source(trainer.issue())
    with trainer.base.db.session() as s:
        s.execute(text("UPDATE iam_trainer_setup_credentials SET consumed=true"))
        s.commit()
    with trainer.base.db.session() as holder:
        holder.execute(text("SELECT id FROM iam_trainer_setup_credentials FOR UPDATE")).one()
        with UnitOfWork(trainer.base.db, mfa[0]).open() as w:
            w.security.allocate("credential")
        assert (
            holder.execute(text("SELECT count(*) FROM iam_trainer_setup_credentials")).scalar_one()
            == 1
        )
        holder.commit()
    with UnitOfWork(trainer.base.db, mfa[0]).open() as w:
        w.security.allocate("credential")
    assert counts(trainer) == (1, 1, 0, 1)
