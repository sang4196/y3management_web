# ruff: noqa: F811
"""0011 actual lifecycle backfill, preserved sources/sessions and typed constraints."""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.test_iam import ORIGIN, SyntheticSecret, child_env, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body, change
from tests.test_workforce import Scene, scene  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def migrate(settings: Settings, direction: str, revision: str) -> int:
    return subprocess.run(
        [sys.executable, "-m", "alembic", direction, revision],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    ).returncode


@pytest.mark.parametrize(
    "assignment",
    [
        "after_epoch=before_epoch",
        "after_granted=before_granted",
        "after_account_version=before_account_version+1",
        "actor_role='TRAINER'",
        "trainer_id=gen_random_uuid()",
    ],
)
def test_role_audit_rejects_invalid_facts(trainer: TrainerScene, assignment: str) -> None:
    source(trainer.issue())
    assert change(trainer, body(trainer, False)).status_code == 200
    with trainer.base.db.session() as s, pytest.raises(IntegrityError):
        s.execute(text("UPDATE audit_trainer_role_events SET " + assignment))
        s.commit()


@pytest.mark.parametrize(
    "assignment",
    [
        "role_version=role_version+1",
        "role_version=0",
        "trainer_id=gen_random_uuid()",
        "origin='unknown'",
    ],
)
def test_role_grant_constraints(trainer: TrainerScene, assignment: str) -> None:
    source(trainer.issue())
    with trainer.base.db.session() as s, pytest.raises(IntegrityError):
        s.execute(text("UPDATE iam_trainer_role_grants SET " + assignment))
        s.commit()


def test_actual_0011_backfill_roundtrip_preserves_live_auth_and_source(
    mfa: tuple[Settings, Database, str, str],
    tmp_path: Path,
) -> None:
    settings, db, password, token = mfa
    assert migrate(settings, "downgrade", "0011_iam_trainer_login") == 0
    archive = tmp_path / "old.tar"
    with archive.open("wb") as out:
        result = subprocess.run(
            ["git", "archive", "08f2ef5a26fbe8f91058bf3767efe4b1b382d1a5", "backend"],
            cwd=Path.cwd().parent,
            stdout=out,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    assert result.returncode == 0
    with tarfile.open(archive) as saved:
        saved.extractall(tmp_path, filter="data")
    old = tmp_path / "backend"
    private = old / "input.json"
    private.write_text(json.dumps({"password": password, "token": token}))
    private.chmod(0o600)
    script = old / "prepare_i1.py"
    script.write_text("""import json
from contextlib import closing
from pathlib import Path
from fastapi.testclient import TestClient
from tests.test_iam import ORIGIN,csrf
from tests.test_iam_mfa import Authenticator,call,enroll,login_mfa
from tests.test_workforce import Scene
from tests.test_iam_trainer import TrainerScene,source
from y3management.config import load_settings
from y3management.database import Database
from y3management.application import create_app
cfg=load_settings(); db=Database(cfg); data=json.loads(Path("input.json").read_text())
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as admin:
 key=Authenticator();enroll(admin,data["token"],key);login_mfa(admin,data["password"],key)
 branch=call(admin,"/admin/branches",csrf(admin),
  {"code":"OLD","name":"가상 이전 지점"}).json()["id"]
 scene=Scene(admin,db,branch); result={"branch":branch}
 for index in range(2):
  fact=scene.send(scene.body()).json()["trainer"]
  with closing(TestClient(admin.app,base_url=ORIGIN)) as recipient:
   t=TrainerScene(scene,fact["id"],recipient,data["password"],"old.trainer."+str(index))
   token=source(t.issue())
   if index==0: result.update(pending=fact["id"],token=token)
   else:
    assert t.complete(token).status_code==204 and t.signin().status_code==204
    result.update(active=fact["id"],cookie=recipient.cookies.get("__Host-y3-auth"))
 Path("result.json").write_text(json.dumps(result));Path("result.json").chmod(0o600)
""")
    env = child_env(settings)
    env["PYTHONPATH"] = str(old / "src")
    result = subprocess.run(
        [sys.executable, str(script)], cwd=old, env=env, capture_output=True, timeout=60
    )
    assert result.returncode == 0, "Actual retained 0011 lifecycle preparation failed"
    private_data = json.loads((old / "result.json").read_text())
    tables = ("iam_accounts", "iam_sessions", "iam_mfa_contexts", "iam_trainer_setup_credentials")
    with db.session() as s:
        before = {
            table: sorted(
                s.execute(text("SELECT row_to_json(x)::jsonb::text FROM " + table + " x")).scalars()
            )
            for table in tables
        }
    fingerprints = {
        table: hashlib.sha256(str(rows).encode()).hexdigest() for table, rows in before.items()
    }
    assert migrate(settings, "upgrade", "head") == 0
    with db.session() as s:
        for table in tables:
            after = sorted(
                s.execute(
                    text("SELECT (to_jsonb(x)-'trainer_role_epoch')::text FROM " + table + " x")
                ).scalars()
            )
            assert hashlib.sha256(str(after).encode()).hexdigest() == fingerprints[table]
        assert (
            s.execute(
                text(
                    "SELECT count(*) FROM iam_trainer_role_grants WHERE origin='backfill' "
                    "AND granted AND role_version=1"
                )
            ).scalar_one()
            == 2
        )
    assert migrate(settings, "downgrade", "0011_iam_trainer_login") == 0
    assert migrate(settings, "upgrade", "head") == 0
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        client.cookies.set("__Host-y3-auth", SyntheticSecret(private_data["cookie"]))
        assert client.get("/api/v1/auth/me").status_code == 200
        with closing(TestClient(client.app, base_url=ORIGIN)) as pending:
            t = TrainerScene(
                Scene(client, db, private_data["branch"]),
                private_data["pending"],
                pending,
                password,
                "old.trainer.0",
            )
            assert t.complete(SyntheticSecret(private_data["token"])).status_code == 204
            assert t.signin().status_code == 204
    # The test fixture removes the private child source, credentials and schema after execution.
    os.chmod(archive, 0o600)


@pytest.mark.parametrize("table", ["iam_sessions", "iam_mfa_contexts"])
def test_downgrade_rejects_epoch_facts_that_would_revive_auth(
    scene: Scene, mfa: tuple[Settings, Database, str, str], table: str
) -> None:
    if table == "iam_mfa_contexts":
        assert (
            call(scene.client, "/auth/passkeys/options", csrf(scene.client), {}).status_code == 200
        )
    with scene.db.session() as s:
        assert s.execute(text("SELECT count(*) FROM " + table)).scalar_one() > 0
        s.execute(text("UPDATE " + table + " SET trainer_role_epoch=1"))
        s.commit()
    assert migrate(mfa[0], "downgrade", "0011_iam_trainer_login") != 0
    with scene.db.session() as s:
        assert (
            s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0012_iam_trainer_roles"
        )
        assert s.execute(text("SELECT min(trainer_role_epoch) FROM " + table)).scalar_one() == 1
