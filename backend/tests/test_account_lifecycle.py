# ruff: noqa: F811
"""Current public lifecycle commands and explicit cutover boundaries on owned schemas."""

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.legacy_helpers import legacy_database, legacy_master  # noqa: F401
from tests.password_helpers import call
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body, change
from tests.test_password_transition import fingerprint, migrate
from tests.test_workforce import scene  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres
OLD = "0014_password_only"
HEAD = "0015_account_lifecycle"


def mutate(
    t: TrainerScene, row: dict[str, Any], action: str, *, nonce: str | None = None, **fields: str
) -> Any:
    actor = t.base.client
    return actor.request(
        "POST" if action == "restore" else "PATCH",
        f"/api/v1/admin/accounts/{row['account_id']}/{action}",
        headers={"Origin": ORIGIN, "X-CSRF-Token": nonce or csrf(actor)},
        json={"expected_version": row["version"], **fields},
    )


def lifecycle_fingerprints(db: Database) -> dict[str, str]:
    # Only digests leave Postgres, including for failed comparisons.
    with db.session() as session:
        tables = list(
            session.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname=current_schema()")
            ).scalars()
        )
        return {
            name: session.execute(
                text(
                    f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,"
                    f"',' ORDER BY row_to_json(t)::text),'')) FROM {name} t"
                )
            ).scalar_one()
            for name in tables
        }


@pytest.mark.parametrize("kind", ["trainer", "inactive", "role0"])
def test_pending_trainer_lifecycle(trainer: TrainerScene, kind: str) -> None:
    t = trainer
    actor = t.base.client
    original = source(t.issue())
    if kind == "role0":
        assert change(t, body(t, False)).status_code == 200
    if kind == "inactive":
        t.active(False)
    lookup = "/admin/account-lifecycle/lookup"
    row = call(actor, lookup, csrf(actor), {"login_id": t.login.upper()}).json()
    assert row["admin_scope"] is None and row["trainer_id"] == t.trainer
    assert row["trainer_granted"] == (kind != "role0")
    assert bool(row["setup_route"]) == (kind == "trainer")
    hidden = call(actor, "/admin/accounts/lookup", csrf(actor), {"login_id": t.login})
    assert hidden.status_code == 404
    denied = call(
        actor,
        "/admin/accounts/" + row["account_id"] + "/activation",
        csrf(actor),
        {"expected_version": row["version"]},
    )
    assert denied.status_code == 404
    first = mutate(t, row, "status", status="DISABLED")
    assert first.status_code == 200
    disabled = first.json()
    assert disabled["state"] == "DISABLED" and disabled["restore_state"] == "PENDING_SETUP"
    assert disabled["version"] == row["version"] + 1 and disabled["admin_scope"] is None
    assert mutate(t, disabled, "status", status="DISABLED").status_code == 409
    assert mutate(t, row, "login-id", login_id=t.login.upper()).status_code == 409
    nonce = csrf(actor)
    before_noop = lifecycle_fingerprints(t.base.db)
    assert mutate(t, disabled, "login-id", nonce=nonce, login_id=t.login.upper()).json() == disabled
    assert lifecycle_fingerprints(t.base.db) == before_noop
    renamed = mutate(t, disabled, "login-id", login_id="trainer.renamed").json()
    assert renamed["restore_state"] == disabled["restore_state"] and renamed["admin_scope"] is None
    assert call(actor, lookup, csrf(actor), {"login_id": t.login}).status_code == 404
    assert actor.get("/api/v1/admin/account-lifecycle/" + row["account_id"]).json() == renamed
    restored = mutate(t, renamed, "restore").json()
    assert restored["state"] == "PENDING_SETUP" and restored["restore_state"] is None
    assert restored["version"] == renamed["version"] + 1
    assert bool(restored["setup_route"]) == (kind == "trainer")
    assert t.complete(original).status_code == 400
    if kind == "trainer":
        assert t.complete(source(t.reissue())).status_code == 204
        t.login = "trainer.renamed"
        assert t.signin().status_code == 204
    else:
        assert t.reissue().status_code == 409


@pytest.mark.parametrize("reset", [False, True])
def test_migrate_disabled_and_roundtrip(
    legacy_master: tuple[Settings, Database], reset: bool
) -> None:
    settings, db = legacy_master
    migrate(settings, "upgrade", OLD)
    from y3management.contracts import Rejected
    from y3management.iam.policy import current_policy

    with db.session() as session, pytest.raises(Rejected) as rejected:
        current_policy(session)
    assert rejected.value.detail == "authentication_policy_unavailable"
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings, database=db), base_url=ORIGIN),
    ):
        pytest.fail("Unmigrated runtime started")
    with db.engine.begin() as conn:
        conn.execute(
            text("""UPDATE iam_accounts SET state='DISABLED',
            password_hash=CASE WHEN :reset THEN NULL ELSE password_hash END,
            password_reset_pending=:reset, reset_generation=CAST(:reset AS int)"""),
            {"reset": reset},
        )
        conn.execute(
            text("""INSERT INTO audit_events(id,action,success,before_state,after_state,
            request_id) VALUES(:id,'account_disable',false,'PENDING_SETUP','DISABLED',:req)"""),
            {"id": uuid4(), "req": uuid4()},
        )
    original = fingerprint(db)
    migrate(settings, "upgrade", HEAD)
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings, database=db), base_url=ORIGIN),
    ):
        pytest.fail("0016 runtime accepted 0015")
    migrate(settings, "upgrade", "0016_operator_onboarding")
    with TestClient(create_app(settings, database=db), base_url=ORIGIN):
        with db.session() as session:
            assert current_policy(session).version == 2
    migrate(settings, "downgrade", HEAD)
    with db.session() as session:
        assert (
            session.execute(text("SELECT restore_state FROM iam_accounts")).scalar_one() == "ACTIVE"
        )
    with db.engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(text("UPDATE iam_accounts SET restore_state=NULL"))
    with db.engine.begin() as conn, pytest.raises(IntegrityError):
        conn.execute(text("UPDATE iam_accounts SET restore_state='PENDING_SETUP'"))
    head = fingerprint(db)
    migrate(settings, "downgrade", "0013_workforce_trainer_state", success=False)
    assert fingerprint(db) == head
    migrate(settings, "downgrade", OLD)
    assert fingerprint(db) == original
    with db.engine.begin() as conn:
        conn.execute(text("UPDATE audit_events SET success=true"))
    contradicted = fingerprint(db)
    migrate(settings, "upgrade", HEAD, success=False)
    assert fingerprint(db) == contradicted


def test_pending_downgrade_guards(legacy_master: tuple[Settings, Database]) -> None:
    settings, db = legacy_master
    migrate(settings, "upgrade", HEAD)
    with db.engine.begin() as conn:
        conn.execute(
            text("""UPDATE iam_accounts SET state='DISABLED', password_hash=NULL,
                    restore_state='PENDING_SETUP'""")
        )
    before = fingerprint(db)
    migrate(settings, "downgrade", OLD, success=False)
    assert fingerprint(db) == before
    with db.engine.begin() as conn:
        conn.execute(text("UPDATE iam_accounts SET state=restore_state,restore_state=NULL"))
        conn.execute(
            text("""INSERT INTO audit_events(id,action,success,before_state,after_state,
             request_id) VALUES(:id,'account_restore',true,'DISABLED','PENDING_SETUP',:req)"""),
            {"id": uuid4(), "req": uuid4()},
        )
    before = fingerprint(db)
    migrate(settings, "downgrade", OLD, success=False)
    assert fingerprint(db) == before
    migrate(settings, "upgrade", "0016_operator_onboarding")
    current = fingerprint(db)
    migrate(settings, "downgrade", OLD, success=False)
    assert fingerprint(db) == current


@pytest.mark.parametrize("cycle", ["disable_restore", "rename_back"])
def test_prepared_setup_after_lifecycle_cycle(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, cycle: str
) -> None:
    from y3management.iam.infrastructure import IAM
    from y3management.iam.public import TrainerSetupProof

    t = trainer
    old = source(t.issue())
    actor = t.base.client
    row = call(actor, "/admin/account-lifecycle/lookup", csrf(actor), {"login_id": t.login}).json()
    prepare = IAM.prepare_trainer_setup
    committed: list[int] = []

    def prepare_then_change(iam: IAM, token: str, password: str) -> TrainerSetupProof:
        proof = prepare(iam, token, password)
        if cycle == "disable_restore":
            first = mutate(t, row, "status", status="DISABLED")
            assert first.status_code == 200
            final = mutate(t, first.json(), "restore")
        else:
            first = mutate(t, row, "login-id", login_id="temporary.name")
            assert first.status_code == 200
            final = mutate(t, first.json(), "login-id", login_id=row["login_id"])
        assert final.status_code == 200
        committed.append(final.json()["version"])
        return proof

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "prepare_trainer_setup", prepare_then_change)
        assert t.complete(old).status_code == 400
    assert committed == [row["version"] + 2]
    assert t.complete(source(t.reissue())).status_code == 204
    assert mutate(t, row, "status", status="DISABLED").status_code == 409


def test_previous_runtime_rejects_current_revision(
    legacy_master: tuple[Settings, Database], tmp_path: Path
) -> None:
    from tests.historical_backend import archive_backend, execute_original

    settings, _ = legacy_master
    old = archive_backend(tmp_path, "af9de549a5511eae28e66ba092c84cd98d2c8ef5")
    script = """from y3management.config import load_settings
from y3management.database import Database
from y3management.iam.policy import current_policy
from y3management.contracts import Rejected
import os
os.environ["Y3_IAM_MODE"]="password"
db=Database(load_settings())
try:
    with db.session() as s:
        try:
            stamp=current_policy(s)
            accepted=stamp.version==2
        except Rejected as error:
            assert error.status==503
            accepted=False
        assert accepted==EXPECTED
finally:
    db.close()
"""
    migrate(settings, "upgrade", OLD)
    execute_original(old, settings, script.replace("EXPECTED", "True"))
    migrate(settings, "upgrade", HEAD)
    execute_original(old, settings, script.replace("EXPECTED", "False"))
    directory = tmp_path / "original-0015"
    directory.mkdir()
    original_15 = archive_backend(directory, "f54b89fd5991eee52969f7fd6e07fa916f6af9e4")
    script += """
from fastapi.testclient import TestClient
from y3management.application import create_app
try:
    with TestClient(create_app(load_settings())):
        started=True
except ValueError as error:
    assert str(error)=="APPLICATION_STARTUP_FAILED"
    started=False
assert started==EXPECTED
"""
    execute_original(original_15, settings, script.replace("EXPECTED", "True"))
    migrate(settings, "upgrade", "0016_operator_onboarding")
    execute_original(original_15, settings, script.replace("EXPECTED", "False"))


def test_dual_admin_reset_pending_cycle(trainer: TrainerScene) -> None:
    from contextlib import closing

    from tests.password_helpers import complete, link_token, reset_request
    from tests.test_iam_trainer_roles_security import link
    from tests.test_workforce_integrity import branch_actor

    t = trainer
    actor = t.base.client
    with closing(branch_actor(t.base, t.password)) as branch:
        ident = branch.get("/api/v1/auth/me").json()["account_id"]
        path = "/api/v1/admin/account-lifecycle/" + ident
        assert branch.get(path).status_code == 403
        assert branch.get("/account-lifecycle").status_code == 403
        assert change(t, link(t, ident, "workforce.branch")).status_code == 200
        issued = reset_request(actor, ident)
        assert issued.status_code == 201
        old = link_token(issued.json()["reset_link"])
        row = actor.get(path).json()
        assert row["trainer_id"] == t.trainer and row["trainer_granted"]
        assert row["admin_scope"] == {"kind": "BRANCH", "branch_id": t.base.branch}
        disable = mutate(t, row, "status", status="DISABLED").json()
        assert disable["restore_state"] == "ACTIVE"
        renamed = mutate(t, disable, "login-id", login_id="dual.renamed").json()
        restored = mutate(t, renamed, "restore").json()
        assert restored["state"] == "ACTIVE" and restored["setup_route"] is None
        assert restored["admin_scope"] == row["admin_scope"] and restored["trainer_granted"]
        with t.base.db.session() as session:
            assert session.execute(
                text("""SELECT password_hash IS NULL,password_reset_pending,
                    reset_generation FROM iam_accounts WHERE id=:i"""),
                {"i": ident},
            ).one() == (True, True, 1)
        assert complete(t.recipient, old, t.password).status_code == 401
        fresh = reset_request(actor, ident, reissue=True)
        assert fresh.status_code == 201
        assert (
            complete(t.recipient, link_token(fresh.json()["reset_link"]), t.password).status_code
            == 204
        )
