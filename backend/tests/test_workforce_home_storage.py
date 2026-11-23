# ruff: noqa: F811
"""Actual18 data and runtime, observation origins and lossless inverse guards."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.password_helpers import password_app  # noqa: F401
from tests.test_account_lifecycle import lifecycle_fingerprints
from tests.test_password_transition import migrate
from y3management.application import create_app

pytestmark = pytest.mark.postgres
PARENT = "e66a4a1291207f85dd6407427945ad16090bdc0a"


def seed18(settings: Any, password: str, tmp_path: Path) -> Path:
    from tests.historical_backend import archive_backend, execute_original

    old = archive_backend(tmp_path, PARENT)
    secret = old / "seed-input.json"
    secret.write_text(json.dumps({"password": password}))
    secret.chmod(0o600)
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
from tests.password_helpers import call
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
settings=load_settings();db=Database(settings)
with TestClient(create_app(settings,database=db),base_url=ORIGIN) as c:
 login_password(c,json.loads(Path('seed-input.json').read_text())['password'])
 assert call(c,'/admin/master-accounts',csrf(c),{'login_id':'other.creator'}).status_code==201
 branch=call(c,'/admin/branches',csrf(c),{'code':'OLD18','name':'가상관측'}).json()['id']
 scene=Scene(c,db,branch);command=scene.body();r=scene.send(command);assert r.status_code==201
 Path('seed-output.json').write_text(json.dumps({'trainer':r.json()['trainer'],'command':command}))
 Path('seed-output.json').chmod(0o600)
""",
    )
    return old


def test_real18_observation_runtime_and_state_only_inverse(
    password_app: Any, tmp_path: Path
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0018_withdrawn_operator_move")
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current19 accepted18")
    old = seed18(settings, password, tmp_path)
    before = lifecycle_fingerprints(db)
    migrate(settings, "upgrade", "head")
    after = lifecycle_fingerprints(db)
    assert all(after[k] == v for k, v in before.items() if k != "alembic_version")
    with db.session() as s:
        row = s.execute(
            text(
                "SELECT origin,home_branch_id,trainer_version,"
                "registration_operation_id,recorded_at FROM "
                "workforce_trainer_home_origins"
            )
        ).one()
        assert row.origin == "legacy_observation" and row.registration_operation_id is None
        registered = s.execute(
            text("SELECT created_at FROM workforce_initial_snapshots")
        ).scalar_one()
        assert row.recorded_at > registered
        # A legal W1-only version advance cannot be mistaken for Home history.
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
    with db.session() as s:
        s.execute(text("UPDATE workforce_trainers SET active=false,row_version=row_version+1"))
        s.commit()
    migrate(settings, "downgrade", "0018_withdrawn_operator_move")
    migrate(settings, "upgrade", "head")
    with db.session() as s:
        assert (
            s.execute(
                text("SELECT trainer_version FROM workforce_trainer_home_origins")
            ).scalar_one()
            == 2
        )


@pytest.mark.parametrize(
    "damage",
    [
        "missing_snapshot",
        "wrong_timestamp",
        "missing_audit",
        "wrong_audit_home",
        "wrong_audit_actor",
    ],
)
def test_observation_preflight_rejects_missing_originals(
    password_app: Any, tmp_path: Path, damage: str
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0018_withdrawn_operator_move")
    seed18(settings, password, tmp_path)
    with db.session() as s:
        if damage == "missing_snapshot":
            s.execute(text("DELETE FROM workforce_initial_snapshots"))
        elif damage == "wrong_timestamp":
            s.execute(
                text(
                    "UPDATE workforce_initial_snapshots "
                    "SET created_at=created_at+interval '1 second'"
                )
            )
        if damage == "missing_audit":
            s.execute(
                text(
                    "DELETE FROM audit_workforce_initial_events "
                    "WHERE event_kind='trainer_registered'"
                )
            )
        elif damage == "wrong_audit_home":
            s.execute(
                text("""INSERT INTO organization_branches(id,organization_id,code,name)
                SELECT gen_random_uuid(),organization_id,'BADHOME','가상모순'
                FROM workforce_trainers""")
            )
            s.execute(
                text("""UPDATE audit_workforce_initial_events SET target_home=
                (SELECT id FROM organization_branches WHERE code='BADHOME')
                WHERE event_kind='trainer_registered'""")
            )
        elif damage == "wrong_audit_actor":
            s.execute(
                text("""UPDATE audit_workforce_initial_events SET actor_id=
                (SELECT id FROM iam_accounts WHERE login_id='other.creator')
                WHERE event_kind='trainer_registered'""")
            )
        s.commit()
    before = lifecycle_fingerprints(db)
    migrate(settings, "upgrade", "head", success=False)
    assert lifecycle_fingerprints(db) == before


def test_transition_and_audit_composite_identity_constraints(password_app: Any) -> None:
    from contextlib import closing

    from tests.password_helpers import call, login_password
    from tests.test_iam import ORIGIN, csrf
    from tests.test_iam_trainer import TrainerScene
    from tests.test_workforce import Scene
    from tests.test_workforce_home import body, destination, move

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        login_password(client, password)
        branch = call(
            client, "/admin/branches", csrf(client), {"code": "FK", "name": "가상제약"}
        ).json()["id"]
        scene = Scene(client, db, branch)
        ident = scene.send(scene.body()).json()["trainer"]["id"]
        with closing(TestClient(client.app, base_url=ORIGIN)) as recipient:
            t = TrainerScene(scene, ident, recipient, "unused", "unused")
            assert move(t, body(t, destination(t))).status_code == 200
    before = lifecycle_fingerprints(db)
    with db.session() as s:
        attacks = [
            "UPDATE workforce_trainer_home_operations SET changed=false",
            "UPDATE workforce_trainer_home_operations SET after_home_branch_id=NULL",
            "UPDATE workforce_trainer_home_transitions SET changed=false",
            "UPDATE workforce_trainer_home_transitions SET actor_id=gen_random_uuid()",
            "UPDATE audit_trainer_home_events SET actor_role='BRANCH_ADMIN'",
            "UPDATE audit_trainer_home_events SET actor_branch=before_home_branch_id",
            "UPDATE audit_trainer_home_events SET recorded_at=recorded_at+interval '1 second'",
            "UPDATE audit_trainer_home_events SET after_home_branch_id=before_home_branch_id",
        ]
        for statement in attacks:
            with pytest.raises(IntegrityError), s.begin_nested():
                s.execute(text(statement))
    assert lifecycle_fingerprints(db) == before


@pytest.mark.parametrize(
    "kind", ["registered_exact", "registered_mismatch", "missing_origin", "noop", "move"]
)
def test_registered_inverse_and_actual_home_information_loss_guard(
    password_app: Any, kind: str
) -> None:
    from contextlib import closing

    from tests.password_helpers import login_password
    from tests.test_iam import ORIGIN
    from tests.test_iam_trainer import TrainerScene
    from tests.test_workforce import Scene
    from tests.test_workforce_home import body, destination, move

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        login_password(client, password)
        from tests.password_helpers import call
        from tests.test_iam import csrf

        branch = call(
            client, "/admin/branches", csrf(client), {"code": "NEW19", "name": "가상등록"}
        ).json()["id"]
        scene = Scene(client, db, branch)
        registered = scene.send(scene.body())
        ident = registered.json()["trainer"]["id"]
        with closing(TestClient(client.app, base_url=ORIGIN)) as recipient:
            t = TrainerScene(scene, ident, recipient, "unused", "unused")
            if kind in ("noop", "move"):
                home = branch if kind == "noop" else destination(t)
                assert move(t, body(t, home)).status_code == 200
    with db.session() as s:
        if kind == "registered_mismatch":
            s.execute(
                text(
                    "UPDATE workforce_trainer_home_origins "
                    "SET recorded_at=recorded_at+interval '1 second'"
                )
            )
        elif kind == "missing_origin":
            s.execute(text("DELETE FROM workforce_trainer_home_origins"))
        s.commit()
    before = lifecycle_fingerprints(db)
    migrate(
        settings, "downgrade", "0018_withdrawn_operator_move", success=kind == "registered_exact"
    )
    after = lifecycle_fingerprints(db)
    if kind == "registered_exact":
        assert all(
            after[k] == v
            for k, v in before.items()
            if k
            not in {
                "alembic_version",
                "workforce_trainer_home_origins",
                "workforce_trainer_home_operations",
                "workforce_trainer_home_transitions",
                "audit_trainer_home_events",
            }
        )
    else:
        assert after == before
