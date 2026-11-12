# ruff: noqa: F811
"""OP-7 retained false assignments and actual 17/18 compatibility boundaries."""

from collections.abc import Iterator
from contextlib import closing, contextmanager
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from tests.password_helpers import login_password, password_app  # noqa: F401
from tests.test_iam import csrf
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_operator_management import BASE, call, candidate, command, role_get
from tests.test_workforce import scene  # noqa: F401

pytestmark = pytest.mark.postgres


@contextmanager
def owned_trainer(password_app: Any) -> Iterator[TrainerScene]:
    # Reuse existing fixtures but end the actual app lifespan before CLI/archive checks.
    with closing(cast(Any, scene).__wrapped__(password_app)) as scenes:
        with closing(cast(Any, trainer).__wrapped__(next(scenes))) as trainers:
            yield next(trainers)


def destination(t: TrainerScene) -> str:
    result = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "D" + uuid4().hex[:8], "name": "Retained work destination"},
    )
    assert result.status_code == 201
    return str(result.json()["id"])


def withdrawn(t: TrainerScene) -> dict[str, Any]:
    assert t.complete(source(t.issue())).status_code == 204
    added = command(t, candidate(t, t.login).json())
    assert added.status_code == 200
    result = command(t, added.json()["current"], False)
    assert result.status_code == 200
    return dict(result.json()["current"])


def facts(t: TrainerScene) -> Any:
    with t.base.db.session() as s:
        return s.execute(
            text("""SELECT 'account',id::text,md5(row_to_json(a)::text)
            FROM iam_accounts a UNION ALL
            SELECT 'admin',account_id::text,md5(row_to_json(a)::text) FROM iam_admin_grants a
            UNION ALL SELECT 'trainer',account_id::text,md5(row_to_json(a)::text)
            FROM iam_trainer_bindings a
            UNION ALL SELECT 'workforce',id::text,md5(row_to_json(a)::text)
            FROM workforce_trainers a
            UNION ALL SELECT 'initial',trainer_id::text,md5(row_to_json(a)::text)
            FROM workforce_initial_snapshots a
            UNION ALL SELECT 'budget',encode(key,'hex'),md5(row_to_json(a)::text)
            FROM iam_budgets a
            UNION ALL SELECT 'attempt',id::text,md5(row_to_json(a)::text)
            FROM iam_attempts a ORDER BY 1,2""")
        ).all()


def shape(db: Any) -> Any:
    with db.session() as s:
        return s.execute(
            text("""SELECT conrelid::regclass::text,conname,
            pg_get_constraintdef(oid),convalidated FROM pg_constraint
            WHERE connamespace=current_schema()::regnamespace ORDER BY 1,2""")
        ).all()


def test_withdrawn_move_noop_replay_preserves_facts_and_new_sessions(trainer: TrainerScene) -> None:
    t = trainer
    row = withdrawn(t)
    dest = destination(t)
    assert row["can_move"] is True
    assert t.signin().status_code == 204  # Independent Trainer, despite false Operator.
    before = facts(t)
    op = str(uuid4())
    moved = command(t, row, move=dest, operation=op)
    assert moved.status_code == 200 and moved.json()["granted"] is False
    current = moved.json()["current"]
    assert current["operator_grant"]["scope"]["version"] == 3
    assert facts(t) == before
    assert t.recipient.get("/api/v1/auth/me").status_code == 401
    assert t.signin().status_code == 204
    assert t.recipient.get("/api/v1/operator/branches/" + dest).status_code == 404
    nonce = csrf(t.base.client)
    payload = {
        "operation_id": op,
        "expected_account_version": row["account_version"],
        "expected_operator_version": 2,
        "branch_id": dest,
    }
    path = BASE + "/" + row["account_id"] + "/branch"

    def untouched() -> Any:
        with t.base.db.session() as s:
            return (
                s.execute(
                    text("SELECT id,revoked,last_activity FROM iam_sessions ORDER BY id")
                ).all(),
                s.scalar(text("SELECT count(*) FROM audit_operator_role_events")),
            )

    saved = untouched()
    replay = call(t.base.client, path, nonce, payload)
    assert replay.status_code == 200 and replay.json()["granted"] is False
    assert untouched() == saved
    with t.base.db.engine.begin() as writer:
        writer.execute(
            text(
                "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                "WHERE id=:b"
            ),
            {"b": dest},
        )
    noop = call(
        t.base.client,
        path,
        nonce,
        {**payload, "operation_id": str(uuid4()), "expected_operator_version": 3},
    )
    assert noop.status_code == 200 and not noop.json()["changed"] and not noop.json()["granted"]
    assert untouched() == saved
    assert (
        call(t.base.client, path, nonce, {**payload, "branch_id": row["branch_id"]}).status_code
        == 409
    )
    assert command(t, row, move=dest).status_code == 409
    with t.base.db.engine.begin() as writer:
        writer.execute(
            text(
                "UPDATE organization_branches SET active=true,row_version=row_version+1 WHERE id=:b"
            ),
            {"b": dest},
        )
    added = command(t, current)
    assert added.status_code == 200
    receipt = role_get(t.base.client, "/api/v1/admin/operator-role-operations/" + op)
    assert receipt.status_code == 200 and receipt.json()["granted"] is False
    assert receipt.json()["current"]["operator_grant"]["granted"] is True
    assert receipt.json()["current"]["branch_id"] == dest


def test_withdrawn_master_self_move_preserves_master_and_revokes_login(
    trainer: TrainerScene, password_app: Any
) -> None:
    t = trainer
    c = t.base.client
    actor = c.get("/api/v1/auth/me").json()["account_id"]
    row = role_get(
        c, "/api/v1/admin/operator-roles/" + actor, params={"branch_id": t.base.branch}
    ).json()
    first = command(t, row)
    assert first.status_code == 200
    login_password(c, password_app[2])
    revoked = command(t, first.json()["current"], False)
    assert revoked.status_code == 200
    login_password(c, password_app[2])
    dest = destination(t)
    before = facts(t)
    moved = command(t, revoked.json()["current"], move=dest)
    assert moved.status_code == 200 and moved.json()["reauthentication_required"]
    assert moved.json()["granted"] is False and facts(t) == before
    assert c.get("/api/v1/auth/me").status_code == 401
    login_password(c, password_app[2])
    assert c.get("/api/v1/branches").status_code == 200
    receipt = role_get(c, "/api/v1/admin/operator-role-operations/" + moved.json()["operation_id"])
    assert receipt.status_code == 200 and receipt.json()["granted"] is False


@pytest.mark.parametrize("damage", ["audit", "account", "grant"])
def test_withdrawn_move_audit_rollback(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    from tests.test_account_lifecycle import lifecycle_fingerprints
    from y3management.audit.infrastructure import Audit

    t = trainer
    row = withdrawn(t)
    dest = destination(t)
    nonce = csrf(t.base.client)
    before = lifecycle_fingerprints(t.base.db)
    original = Audit.append_operator_role

    def corrupt(self: Any, value: Any) -> None:
        if damage == "audit":
            raise ValueError("synthetic required audit failure")
        original(self, value)
        sql = (
            "UPDATE iam_accounts SET security_version=security_version+1 WHERE id=:a"
            if damage == "account"
            else "UPDATE iam_operator_grants SET granted=true,version=version+1 WHERE account_id=:a"
        )
        self.s.execute(text(sql), {"a": row["account_id"]})

    monkeypatch.setattr(Audit, "append_operator_role", corrupt)
    response = call(
        t.base.client,
        BASE + "/" + row["account_id"] + "/branch",
        nonce,
        {
            "operation_id": str(uuid4()),
            "expected_account_version": row["account_version"],
            "expected_operator_version": 2,
            "branch_id": dest,
        },
    )
    assert response.status_code == (500 if damage == "audit" else 409)
    assert lifecycle_fingerprints(t.base.db) == before


@pytest.mark.parametrize("history", ["both", "receipt_only", "audit_only"])
def test_withdrawn_history_blocks18_downgrade_before_ddl(
    trainer: TrainerScene, history: str
) -> None:
    from tests.legacy_helpers import assert_revision_loss_guard
    from tests.test_account_lifecycle import lifecycle_fingerprints

    t = trainer
    row = withdrawn(t)
    receipt_only = history == "receipt_only"
    moved = command(t, row, move=row["branch_id"] if receipt_only else destination(t))
    assert moved.status_code == 200
    assert moved.json()["changed"] is (not receipt_only)
    assert (
        command(t, moved.json()["current"]).status_code == 200
    )  # Later regrant cannot erase history.
    if history == "audit_only":
        # Isolated migration storage input, not an application receipt edit/public flow.
        with t.base.db.engine.begin() as writer:
            writer.execute(
                text(
                    "UPDATE iam_operator_role_operations SET action='role',granted=true "
                    "WHERE action='move'"
                )
            )
    before, constraints = lifecycle_fingerprints(t.base.db), shape(t.base.db)
    ddl = []

    def observe(_c: Any, _cursor: Any, sql: str, *_args: Any) -> None:
        if sql.lstrip().split()[0].upper() in {"CREATE", "DROP", "ALTER"}:
            ddl.append(sql)

    event.listen(t.base.db.engine, "before_cursor_execute", observe)
    try:
        assert_revision_loss_guard(
            t.base.db, "0018_withdrawn_operator_move.py", "WITHDRAWN_OPERATOR_MOVE_HISTORY_PRESENT"
        )
    finally:
        event.remove(t.base.db.engine, "before_cursor_execute", observe)
    assert ddl == []
    assert lifecycle_fingerprints(t.base.db) == before and shape(t.base.db) == constraints


@pytest.mark.parametrize("before,after", [(True, False), (False, True)])
def test_move_check_rejects_grant_change(trainer: TrainerScene, before: bool, after: bool) -> None:
    t = trainer
    row = withdrawn(t)
    moved = command(t, row, move=destination(t))
    assert moved.status_code == 200
    with t.base.db.session() as s, pytest.raises(IntegrityError):
        s.execute(
            text("""UPDATE audit_operator_role_events SET before_granted=:b,after_granted=:a
            WHERE kind='move'"""),
            {"b": before, "a": after},
        )


def test_actual17_18_roundtrip_with_withdrawn_rows_and_runtime_matrix(
    password_app: Any, tmp_path: Any
) -> None:
    from fastapi.testclient import TestClient

    from tests.historical_backend import archive_backend, execute_original
    from tests.test_account_lifecycle import lifecycle_fingerprints
    from tests.test_password_transition import migrate
    from y3management.application import create_app

    with owned_trainer(password_app) as t:
        withdrawn(t)  # Existing false grant and ordinary revoke are representable at17.
    settings, db, _ = password_app
    baseline, constraints = lifecycle_fingerprints(db), shape(db)
    old = archive_backend(tmp_path, "7b64f5731ed993f5f8473a1476f27fb6c4931513")
    script = """import os
os.environ['Y3_IAM_MODE']='password'
from y3management.config import load_settings
from y3management.application import create_app
from fastapi.testclient import TestClient
try:
    with TestClient(create_app(load_settings())):
        started=True
except ValueError as error:
    assert str(error)=='APPLICATION_STARTUP_FAILED'
    started=False
assert started==EXPECTED
"""
    execute_original(old, settings, script.replace("EXPECTED", "False"))
    migrate(settings, "downgrade", "0017_operator_management")
    original = lifecycle_fingerprints(db)
    assert {k: v for k, v in original.items() if k != "alembic_version"} == {
        k: v for k, v in baseline.items() if k != "alembic_version"
    }
    execute_original(old, settings, script.replace("EXPECTED", "True"))
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current18 accepted original17")
    migrate(settings, "upgrade", "head")
    with TestClient(create_app(settings)):
        pass
    assert lifecycle_fingerprints(db) == baseline and shape(db) == constraints


@pytest.mark.parametrize("damage", ["missing", "duplicate", "weakened"])
def test_upgrade_rejects_unexpected17_transition_shape(password_app: Any, damage: str) -> None:
    from tests.legacy_helpers import migration_status
    from tests.test_account_lifecycle import lifecycle_fingerprints
    from tests.test_password_transition import migrate

    settings, db, _ = password_app
    migrate(settings, "downgrade", "0017_operator_management")
    with db.engine.begin() as s:
        name, definition = s.execute(
            text("""SELECT conname,pg_get_constraintdef(oid)
            FROM pg_constraint WHERE conrelid='audit_operator_role_events'::regclass
            AND contype='c' AND pg_get_constraintdef(oid) LIKE '%before_version = 0%'
            AND pg_get_constraintdef(oid) LIKE '%before_granted%'""")
        ).one()
        quoted = s.dialect.identifier_preparer.quote(name)
        if damage == "duplicate":
            s.execute(
                text(
                    "ALTER TABLE audit_operator_role_events ADD CONSTRAINT duplicate_transition "
                    + definition
                )
            )
        else:
            s.execute(text("ALTER TABLE audit_operator_role_events DROP CONSTRAINT " + quoted))
            if damage == "weakened":
                s.execute(
                    text(
                        "ALTER TABLE audit_operator_role_events ADD CONSTRAINT "
                        "weakened_transition CHECK (before_granted IS NOT NULL)"
                    )
                )
    before, constraints = lifecycle_fingerprints(db), shape(db)
    from alembic.config import Config
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from alembic.script import ScriptDirectory

    revision = ScriptDirectory.from_config(Config("alembic.ini")).get_revision(
        "0018_withdrawn_operator_move"
    )
    assert revision is not None
    with db.engine.connect() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            with pytest.raises(ValueError, match="WITHDRAWN_OPERATOR_TRANSITION_CHECK_MISMATCH"):
                revision.module.upgrade()
        connection.rollback()
    assert migration_status(settings, "upgrade", "head") != 0
    assert lifecycle_fingerprints(db) == before and shape(db) == constraints


@pytest.mark.parametrize("move_first", [True, False])
def test_false_move_regrant_race_uses_current_epoch(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, move_first: bool
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from tests.test_workforce_integrity import wait_for_owned_block
    from y3management.audit.infrastructure import Audit

    t = trainer
    row = withdrawn(t)
    dest = destination(t)
    nonce = csrf(t.base.client)
    base = {"expected_account_version": row["account_version"], "expected_operator_version": 2}
    move = (
        BASE + "/" + row["account_id"] + "/branch",
        {**base, "operation_id": str(uuid4()), "branch_id": dest},
    )
    grant = (
        BASE + "/" + row["account_id"] + "/changes",
        {
            **base,
            "operation_id": str(uuid4()),
            "branch_id": row["branch_id"],
            "desired_granted": True,
        },
    )
    first, second = (move, grant) if move_first else (grant, move)
    reached, release = Event(), Event()
    holders, waiters = [], []
    original = Audit.append_operator_role

    def append(self: Any, value: Any) -> None:
        original(self, value)
        holders.append(self.s.scalar(text("SELECT pg_backend_pid()")))
        reached.set()
        assert release.wait(8)

    def observe(conn: Any, _cursor: Any, sql: str, *_args: Any) -> None:
        pid = conn.connection.driver_connection.info.backend_pid
        if (
            reached.is_set()
            and not release.is_set()
            and pid not in holders
            and "pg_blocking_pids" not in sql
        ):
            waiters.append(pid)

    monkeypatch.setattr(Audit, "append_operator_role", append)
    event.listen(t.base.db.engine, "before_cursor_execute", observe)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            leading = pool.submit(call, t.base.client, first[0], nonce, first[1])
            try:
                assert reached.wait(5)
                trailing = pool.submit(call, t.base.client, second[0], nonce, second[1])
                wait_for_owned_block(t.base.db, holders[0], waiters)
            finally:
                release.set()
            assert leading.result(timeout=5).status_code == 200
            assert trailing.result(timeout=5).status_code == 409
    finally:
        event.remove(t.base.db.engine, "before_cursor_execute", observe)
    with t.base.db.session() as s:
        assert s.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 3
        granted, branch, version = s.execute(
            text("SELECT granted,branch_id,version FROM iam_operator_grants")
        ).one()
        assert granted is (not move_first) and version == 3
        assert str(branch) == (dest if move_first else row["branch_id"])


def test_original17_move_receipt_exact_replay_on18(password_app: Any, tmp_path: Any) -> None:
    from tests.historical_backend import archive_backend, execute_original
    from tests.test_password_transition import migrate

    with owned_trainer(password_app) as t:
        row = withdrawn(t)
        regranted = command(t, row)
        assert regranted.status_code == 200
        row = regranted.json()["current"]
        dest = destination(t)
        next_dest = destination(t)
    settings, _, password = password_app
    operation = str(uuid4())
    payload = {
        "operation_id": operation,
        "expected_account_version": row["account_version"],
        "expected_operator_version": 3,
        "branch_id": dest,
    }
    path = BASE + "/" + row["account_id"] + "/branch"
    old = archive_backend(tmp_path, "7b64f5731ed993f5f8473a1476f27fb6c4931513")
    migrate(settings, "downgrade", "0017_operator_management")
    script = """import os
os.environ['Y3_IAM_MODE']='password'
from y3management.config import load_settings
from y3management.application import create_app
from fastapi.testclient import TestClient
from tests.password_helpers import login_password
from tests.test_iam import ORIGIN,csrf
from tests.test_operator_management import call
with TestClient(create_app(load_settings()),base_url=ORIGIN) as client:
    login_password(client,PASSWORD)
    result=call(client,PATH,csrf(client),PAYLOAD)
    assert result.status_code==200 and result.json()['granted'] is True
"""
    execute_original(
        old,
        settings,
        script.replace("PASSWORD", repr(str(password)))
        .replace("PATH", repr(path))
        .replace("PAYLOAD", repr(payload)),
    )
    migrate(settings, "upgrade", "head")
    from fastapi.testclient import TestClient

    from tests.test_iam import ORIGIN
    from tests.test_workforce import Scene
    from y3management.application import create_app

    with TestClient(create_app(settings), base_url=ORIGIN) as client:
        login_password(client, password)
        t = TrainerScene(
            Scene(client, password_app[1], t.base.branch), t.trainer, client, t.password, t.login
        )
        replay = call(t.base.client, path, csrf(t.base.client), payload)
        assert replay.status_code == 200 and replay.json()["committed_version"] == 4
        assert replay.json()["granted"] is True
        revoked = command(t, replay.json()["current"], False)
        assert revoked.status_code == 200
        moved = command(t, revoked.json()["current"], move=next_dest)
        assert moved.status_code == 200 and moved.json()["granted"] is False
        replay = call(t.base.client, path, csrf(t.base.client), payload)
        assert replay.status_code == 200 and replay.json()["granted"] is True
        assert replay.json()["current"]["branch_id"] == next_dest
        assert replay.json()["current"]["operator_grant"]["granted"] is False
        from contextlib import closing

        from tests.test_workforce_integrity import branch_actor

        with closing(branch_actor(Scene(t.base.client, t.base.db, next_dest), password)) as other:
            assert (
                role_get(other, "/api/v1/admin/operator-roles/" + row["account_id"]).status_code
                == 200
            )
            assert (
                role_get(other, "/api/v1/admin/operator-role-operations/" + operation).status_code
                == 404
            )


def test_pending_false_move_requires_new_branch_regrant_and_explicit_reissue(
    trainer: TrainerScene, password_app: Any
) -> None:
    from contextlib import closing

    from tests.test_workforce import Scene
    from tests.test_workforce_integrity import branch_actor

    t = trainer
    issued = call(
        t.base.client,
        "/admin/operator-accounts",
        csrf(t.base.client),
        {"login_id": t.login, "branch_id": t.base.branch},
    )
    assert issued.status_code == 201
    old = source(issued)
    revoked = command(t, candidate(t, t.login).json(), False)
    assert revoked.status_code == 200
    dest = destination(t)
    moved = command(t, revoked.json()["current"], move=dest)
    assert moved.status_code == 200 and moved.json()["granted"] is False
    target = moved.json()["current"]["account_id"]
    setup_path = "/admin/operator-accounts/" + target + "/initial-setup"
    with closing(branch_actor(Scene(t.base.client, t.base.db, dest), password_app[2])) as ba:
        bt = TrainerScene(Scene(ba, t.base.db, dest), t.trainer, t.recipient, t.password, t.login)
        current = candidate(bt, t.login).json()
        assert current["can_move"] is False
        assert command(bt, current, move=t.base.branch).status_code == 403
        assert (
            call(
                ba,
                setup_path,
                csrf(ba),
                {
                    "expected_version": current["account_version"],
                    "expected_operator_version": current["operator_grant"]["scope"]["version"],
                },
            ).status_code
            == 404
        )
        regranted = command(bt, current)
        assert regranted.status_code == 200
        fresh = regranted.json()["current"]
        reissued = call(
            ba,
            setup_path,
            csrf(ba),
            {
                "expected_version": fresh["account_version"],
                "expected_operator_version": fresh["operator_grant"]["scope"]["version"],
            },
        )
        assert reissued.status_code == 201
    assert (
        call(
            t.recipient,
            "/auth/operator-credentials/complete",
            csrf(t.recipient),
            {"setup_token": old, "new_password": t.password},
        ).status_code
        == 400
    )
    assert (
        call(
            t.recipient,
            "/auth/operator-credentials/complete",
            csrf(t.recipient),
            {"setup_token": source(reissued), "new_password": t.password},
        ).status_code
        == 204
    )
    assert t.signin().status_code == 204
    assert t.recipient.get("/api/v1/operator/branches/" + dest).status_code == 200
    assert t.recipient.get("/api/v1/operator/branches/" + t.base.branch).status_code == 404


@pytest.mark.parametrize("writer_first", [True, False])
def test_false_move_and_actual18_downgrade_installation_gate(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, writer_first: bool
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from alembic.config import Config
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from alembic.script import ScriptDirectory

    from tests.test_workforce_integrity import wait_for_owned_block
    from y3management.audit.infrastructure import Audit

    t = trainer
    row = withdrawn(t)
    dest = destination(t)
    nonce = csrf(t.base.client)
    payload = {
        "operation_id": str(uuid4()),
        "expected_account_version": row["account_version"],
        "expected_operator_version": 2,
        "branch_id": dest,
    }
    reached, release = Event(), Event()
    pids: dict[str, int] = {}
    waiters: list[int] = []
    original = Audit.append_operator_role
    gate = "LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE"

    def pause(self: Any, value: Any) -> None:
        original(self, value)
        pids["writer"] = self.s.scalar(text("SELECT pg_backend_pid()"))
        if writer_first:
            reached.set()
            assert release.wait(10)

    def after(conn: Any, _cursor: Any, sql: str, *_args: Any) -> None:
        if sql.strip() == gate and not writer_first:
            pids["migration"] = conn.connection.driver_connection.info.backend_pid
            reached.set()
            assert release.wait(10)

    def before(conn: Any, _cursor: Any, sql: str, *_args: Any) -> None:
        pid = conn.connection.driver_connection.info.backend_pid
        if (
            reached.is_set()
            and not release.is_set()
            and pid not in pids.values()
            and "pg_blocking_pids" not in sql
        ):
            waiters.append(pid)

    def migrate() -> str:
        scripts = ScriptDirectory.from_config(Config("alembic.ini"))
        script = scripts.get_revision("0018_withdrawn_operator_move")
        assert script is not None
        with t.base.db.engine.begin() as conn:
            context = MigrationContext.configure(conn)
            with Operations.context(context):
                if writer_first:
                    with pytest.raises(ValueError, match="WITHDRAWN_OPERATOR_MOVE_HISTORY_PRESENT"):
                        script.module.downgrade()
                    return "history-preserved"
                script.module.downgrade()
                context.stamp(scripts, "0017_operator_management")
        return "downgraded"

    def move() -> Any:
        return call(t.base.client, BASE + "/" + row["account_id"] + "/branch", nonce, payload)

    monkeypatch.setattr(Audit, "append_operator_role", pause)
    event.listen(t.base.db.engine, "before_cursor_execute", before)
    event.listen(t.base.db.engine, "after_cursor_execute", after)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            leading = pool.submit(move if writer_first else migrate)
            try:
                assert reached.wait(5)
                trailing = pool.submit(migrate if writer_first else move)
                wait_for_owned_block(
                    t.base.db, pids["writer" if writer_first else "migration"], waiters
                )
                if writer_first:
                    with t.base.db.session() as s:
                        blocked = s.scalar(
                            text("SELECT query FROM pg_stat_activity WHERE pid=:p"),
                            {"p": waiters[-1]},
                        )
                        assert "iam_installation" in blocked
            finally:
                release.set()
            if writer_first:
                assert leading.result(timeout=10).status_code == 200
                assert trailing.result(timeout=10) == "history-preserved"
            else:
                assert leading.result(timeout=10) == "downgraded"
                assert trailing.result(timeout=10).status_code == 503
    finally:
        event.remove(t.base.db.engine, "after_cursor_execute", after)
        event.remove(t.base.db.engine, "before_cursor_execute", before)
    with t.base.db.session() as s:
        assert s.scalar(
            text("SELECT count(*) FROM audit_operator_role_events WHERE kind='move'")
        ) == int(writer_first)
        assert s.scalar(text("SELECT version FROM iam_operator_grants")) == (
            3 if writer_first else 2
        )
        assert s.scalar(text("SELECT granted FROM iam_operator_grants")) is False
        assert s.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0018_withdrawn_operator_move" if writer_first else "0017_operator_management"
        )


@pytest.mark.parametrize(
    "boundary", ["absent_grant", "inactive_destination", "foreign_destination"]
)
def test_move_rejects_missing_grant_or_unassignable_destination(
    trainer: TrainerScene, boundary: str
) -> None:
    from tests.test_account_lifecycle import lifecycle_fingerprints

    t = trainer
    if boundary == "absent_grant":
        assert t.complete(source(t.issue())).status_code == 204
        row = candidate(t, t.login).json()
        assert row["can_move"] is False and row["operator_grant"] is None
    else:
        row = withdrawn(t)
    dest = destination(t)
    if boundary == "inactive_destination":
        with t.base.db.engine.begin() as s:
            s.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:b"
                ),
                {"b": dest},
            )
    elif boundary == "foreign_destination":
        org, branch = uuid4(), uuid4()
        with t.base.db.engine.begin() as s:
            s.execute(
                text(
                    "INSERT INTO organization_organizations(id,name) VALUES(:o,'Other synthetic')"
                ),
                {"o": org},
            )
            s.execute(
                text(
                    "INSERT INTO organization_branches(id,organization_id,code,name) "
                    "VALUES(:b,:o,'OTHER','Other')"
                ),
                {"b": branch, "o": org},
            )
        dest = str(branch)
    nonce = csrf(t.base.client)
    before = lifecycle_fingerprints(t.base.db)
    response = call(
        t.base.client,
        BASE + "/" + row["account_id"] + "/branch",
        nonce,
        {
            "operation_id": str(uuid4()),
            "expected_account_version": row["account_version"],
            "expected_operator_version": 1 if boundary == "absent_grant" else 2,
            "branch_id": dest,
        },
    )
    assert response.status_code == (404 if boundary == "foreign_destination" else 409)
    assert lifecycle_fingerprints(t.base.db) == before
