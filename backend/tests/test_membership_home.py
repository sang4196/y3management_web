# ruff: noqa: F811
"""Real PostgreSQL Home transitions, bounded receipts, and loss-safe actual23 inverse."""

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from threading import Event
from typing import Any
from uuid import UUID, uuid4

import pytest
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from tests.historical_backend import archive_backend, execute_original
from tests.membership_seed import (
    assert_revision_loss_guard,
    full_shape,
    prepare_revision_guard,
    projected,
)
from tests.password_helpers import call
from tests.test_iam import ORIGIN, csrf
from tests.test_membership import body, edit, get, grant_operator, headers, receipt, send
from tests.test_operator_management import role_headers
from tests.test_password_transition import migrate
from tests.test_workforce import Scene, activity, scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres
PARENT23 = "21935b70116c30f1add1443f520f3f425af30394"


def destination(s: Scene) -> str:
    result = call(
        s.client,
        "/admin/branches",
        csrf(s.client),
        {"code": "MEM-TARGET", "name": "가상 목적 지점"},
    )
    assert result.status_code == 201
    return str(result.json()["id"])


def command(target: str, version: int = 1) -> dict[str, Any]:
    return {
        "operation_id": str(uuid4()),
        "expected_member_version": version,
        "target_home_branch_id": target,
    }


def move(s: Scene, ident: str, payload: dict[str, Any], client: Any = None) -> Any:
    return send(s, payload, "/" + ident + "/home", client)


def operation(s: Scene, ident: str, client: Any = None) -> Any:
    c = client or s.client
    return c.get("/api/v1/admin/member-home-operations/" + ident, headers=headers(c))


def test_source_ba_inactive_member_and_branch_minimal_ack_loses_scope(
    scene: Scene, password_app: Any
) -> None:
    s = scene
    target = destination(s)
    with closing(branch_actor(s, password_app[2])) as ba:
        original = body(s)
        ident = send(s, original, client=ba).json()["committed_member"]["id"]
        assert (
            send(
                s,
                {"operation_id": str(uuid4()), "expected_member_version": 1},
                "/" + ident + "/deactivate",
                ba,
            ).status_code
            == 200
        )
        with s.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": s.branch},
            )
        candidates = get(s, "/" + ident + "/home-candidates", ba)
        assert candidates.status_code == 200
        assert candidates.json() == [{"id": target, "name": "가상 목적 지점", "version": 1}]
        # Ordinary Member assignment remains limited to the BA's own (now inactive) Branch.
        assert ba.get("/api/v1/admin/member-branches", headers=headers(ba)).json() == []
        payload = command(target, 2)
        ack = move(s, ident, payload, ba)
        assert ack.status_code == 200
        assert ack.json() == {
            "operation_id": payload["operation_id"],
            "kind": "move_home",
            "changed": True,
            "member_id": ident,
            "committed_member_version": 3,
        }
        assert get(s, client=ba).json()["total"] == 0
        assert get(s, "/" + ident, ba).status_code == 404
        assert get(s, "/" + ident + "/home-candidates", ba).status_code == 404
        before = projected(s.db)
        assert operation(s, payload["operation_id"], ba).status_code == 404
        assert move(s, ident, payload, ba).status_code == 404
        assert operation(s, payload["operation_id"]).status_code == 404  # other Actor, even Master
        assert projected(s.db) == before
        current = get(s, "/" + ident).json()
        assert not current["active"] and current["home_branch_id"] == target
        assert current["values"] == {"name": "가상 회원", "phone": "01020000000"}
        with s.db.session() as db:
            assert (
                db.scalar(text("SELECT count(*) FROM audit_member_events WHERE kind='move_home'"))
                == 1
            )
            assert db.execute(
                text(
                    "SELECT actor_branch,home_branch_id,before_version,after_version "
                    "FROM audit_member_events WHERE kind='move_home'"
                )
            ).one() == (UUID(s.branch), UUID(target), 2, 3)


def test_master_receipt_noop_cas_and_historical_home_metadata(scene: Scene) -> None:
    s = scene
    target = destination(s)
    original = body(s)
    ident = send(s, original).json()["committed_member"]["id"]
    payload = command(target)
    ack = move(s, ident, payload)
    assert ack.status_code == 200
    before = projected(s.db)
    assert operation(s, payload["operation_id"]).json() == ack.json()
    assert move(s, ident, payload).json() == ack.json()
    assert projected(s.db) == before
    historical = receipt(s, original["operation_id"]).json()
    assert historical["committed_member"]["home_branch_id"] == s.branch
    assert historical["committed_member"]["home_branch_name"] is None
    assert historical["committed_member"]["home_active"] is None
    assert historical["current_member"]["home_branch_name"] == "가상 목적 지점"
    assert send(s, original).json() == historical
    before_activity = activity(s.db)
    same = move(s, ident, command(target, 2))
    assert same.status_code == 200 and not same.json()["changed"]
    assert same.json()["committed_member_version"] == 2 and activity(s.db) == before_activity
    assert move(s, ident, command(target, 1)).status_code == 409
    assert move(s, ident, {**payload, "target_home_branch_id": s.branch}).status_code == 409
    assert send(s, edit(2), "/" + ident).status_code == 200


def test_move_scope_not_operator_union_and_destination_must_be_active_same_org(
    scene: Scene, password_app: Any
) -> None:
    s = scene
    target = destination(s)
    ident = send(s, body(s)).json()["committed_member"]["id"]
    with closing(branch_actor(s, password_app[2])) as ba:
        grant_operator(s, "workforce.branch", target)
        # BA(source)+Operator(target) may move from source, but Operator alone cannot move back.
        from tests.password_helpers import login_password

        login_password(ba, password_app[2], "workforce.branch")
        assert move(s, ident, command(target), ba).status_code == 200
        assert send(s, edit(2), "/" + ident, ba).status_code == 200
        before = projected(s.db)
        assert move(s, ident, command(s.branch, 3), ba).status_code == 404
        assert operation(s, str(uuid4()), ba).status_code == 404
        assert projected(s.db) == before
    with s.db.engine.begin() as db:
        db.execute(
            text(
                "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                "WHERE id=:i"
            ),
            {"i": s.branch},
        )
    foreign_org, foreign_branch = str(uuid4()), str(uuid4())
    with s.db.engine.begin() as db:
        db.execute(
            text("INSERT INTO organization_organizations(id,name) VALUES(:i,'가상 타 조직')"),
            {"i": foreign_org},
        )
        db.execute(
            text(
                "INSERT INTO organization_branches(id,organization_id,code,name) "
                "VALUES(:i,:o,'FOREIGN','가상 타 지점')"
            ),
            {"i": foreign_branch, "o": foreign_org},
        )
    before = projected(s.db)
    assert move(s, ident, command(foreign_branch, 3)).status_code == 404
    assert move(s, ident, command(s.branch, 3)).status_code == 409
    assert move(s, ident, command(str(uuid4()), 3)).status_code == 404
    assert projected(s.db) == before


@pytest.mark.parametrize("failure", ["audit", "actor", "target"])
def test_move_audit_and_original_actor_final_proof_rollback_all_rows(
    scene: Scene, monkeypatch: Any, failure: str
) -> None:
    s = scene
    target = destination(s)
    ident = send(s, body(s)).json()["committed_member"]["id"]
    h = headers(s.client)
    before = projected(s.db)
    original = Audit.append_member

    def fail(self: Any, member_event: Any) -> None:
        original(self, member_event)
        if failure == "audit":
            raise Rejected(503, "unavailable")
        if failure == "target":
            self.s.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": target},
            )
        else:
            self.s.execute(
                text("DELETE FROM iam_admin_grants WHERE account_id=:a"),
                {"a": member_event.actor_id},
            )

    monkeypatch.setattr(Audit, "append_member", fail)
    response = s.client.post(
        "/api/v1/admin/members/" + ident + "/home", headers=h, json=command(target)
    )
    assert response.status_code == {"audit": 503, "actor": 401, "target": 409}[failure]
    assert projected(s.db) == before


def test_actual23_member_rows_checks_and_lossless_inverse(
    password_app: Any, tmp_path: Path
) -> None:
    settings, db, password = password_app
    migrate(settings, "downgrade", "0023_membership_basics")
    old = archive_backend(tmp_path, PARENT23)
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
from tests.test_membership import body,edit,send
from y3management.application import create_app
from y3management.config import load_settings
from y3management.database import Database
cfg=load_settings();db=Database(cfg)
with TestClient(create_app(cfg,database=db),base_url=ORIGIN) as client:
 login_password(client,json.loads(Path('seed-input.json').read_text())['password'])
 branch=call(client,'/admin/branches',csrf(client),
  {'code':'ORIGINAL23','name':'가상 원23'}).json()['id']
 s=Scene(client,db,branch)
 ident=send(s,body(s)).json()['committed_member']['id']
 assert send(s,edit(1),'/' + ident).status_code==200
 from uuid import uuid4
 assert send(s,{'operation_id':str(uuid4()),'expected_member_version':2},
  '/' + ident+'/deactivate').status_code==200
 assert send(s,{'operation_id':str(uuid4()),'expected_member_version':3},
  '/' + ident+'/reactivate').status_code==200
 assert send(s,edit(4),'/' + ident).json()['changed'] is False
""",
    )
    before, shape23 = projected(db), full_shape(db)
    # Upgrade itself validates the actual PG-generated original kind/actor CHECK names.
    migrate(settings, "upgrade", "head")
    assert all(projected(db)[k] == v for k, v in before.items() if k != "alembic_version")
    with db.session() as session:
        assert session.scalar(text("SELECT count(*) FROM membership_member_versions")) == 4
        assert session.scalar(text("SELECT count(*) FROM membership_member_operations")) == 5
    migrate(settings, "downgrade", "0023_membership_basics")
    assert projected(db) == before and full_shape(db) == shape23
    migrate(settings, "upgrade", "head")


@pytest.mark.parametrize("noop", [False, True])
def test_move_receipt_including_noop_blocks_lossy_24_inverse(scene: Scene, noop: bool) -> None:
    s = scene
    ident = send(s, body(s)).json()["committed_member"]["id"]
    target = s.branch if noop else destination(s)
    assert move(s, ident, command(target)).status_code == 200
    before, shape24 = projected(s.db), full_shape(s.db)
    assert_revision_loss_guard(s.db, "0024_membership_home_move.py", "MEMBER_HOME_HISTORY_PRESENT")
    assert projected(s.db) == before and full_shape(s.db) == shape24


@pytest.mark.parametrize("damage", ["head", "policy", "checks"])
def test_24_preflight_has_no_target_ddl(scene: Scene, damage: str) -> None:
    db = scene.db
    before, shape24 = projected(db), full_shape(db)
    scripts = ScriptDirectory.from_config(Config("alembic.ini"))
    revision = scripts.get_revision("0024_membership_home_move")
    assert revision is not None
    observed: list[str] = []

    def observe(_conn: Any, _cursor: Any, sql: str, *args: Any) -> None:
        if sql.lstrip().upper().startswith(("CREATE ", "ALTER ", "DROP ")):
            observed.append(sql)

    with db.engine.connect() as conn:
        tx = conn.begin()
        try:
            prepare_revision_guard(conn, "0024_membership_home_move")
            context = MigrationContext.configure(conn)
            if damage == "checks":
                with Operations.context(context):
                    revision.module.downgrade()
                    context.stamp(scripts, "0023_membership_basics")
                conn.execute(
                    text(
                        "ALTER TABLE membership_member_versions RENAME CONSTRAINT "
                        "membership_member_versions_kind_check TO altered_kind_check"
                    )
                )
            elif damage == "head":
                conn.execute(
                    text("UPDATE alembic_version SET version_num='0023_membership_basics'")
                )
            else:
                conn.execute(
                    text(
                        "UPDATE iam_policy_transitions SET target_schema_revision='invalid-target'"
                    )
                )
            event.listen(conn, "before_cursor_execute", observe)
            try:
                error = {"head": "SCHEMA", "policy": "POLICY", "checks": "CONSTRAINT"}[damage]
                with pytest.raises(ValueError, match="MEMBER_HOME_" + error + "_MISMATCH"):
                    with Operations.context(context):
                        if damage == "checks":
                            revision.module.upgrade()
                        else:
                            revision.module.downgrade()
            finally:
                event.remove(conn, "before_cursor_execute", observe)
            assert not observed
        finally:
            tx.rollback()
    assert projected(db) == before and full_shape(db) == shape24


def test_move_source_before_fk_rejects_destination_as_actor_scope(
    scene: Scene, password_app: Any
) -> None:
    s = scene
    target = destination(s)
    ident = send(s, body(s)).json()["committed_member"]["id"]
    with closing(branch_actor(s, password_app[2])) as ba:
        payload = command(target)
        assert move(s, ident, payload, ba).status_code == 200
    before = projected(s.db)
    with pytest.raises(IntegrityError):
        with s.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE membership_member_operations SET actor_branch=:b WHERE operation_id=:o"
                ),
                {"b": target, "o": payload["operation_id"]},
            )
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert projected(s.db) == before


@pytest.mark.parametrize(
    "bad",
    [
        {"expected_member_version": True},
        {"expected_member_version": 0},
        {"expected_member_version": "1"},
        {"target_home_branch_id": None},
        {"name": "sensitive-input-marker"},
        {"phone": "sensitive-input-marker"},
    ],
)
def test_move_strict_command_has_no_sensitive_echo_or_partial_facts(
    scene: Scene, bad: dict[str, Any]
) -> None:
    s = scene
    target = destination(s)
    ident = send(s, body(s)).json()["committed_member"]["id"]
    before = projected(s.db)
    response = move(s, ident, {**command(target), **bad})
    assert response.status_code == 422
    assert "sensitive-input-marker" not in response.response.text
    assert projected(s.db) == before


@pytest.mark.parametrize("duplicate", [False, True])
def test_move_installation_gate_serializes_duplicate_or_cas(
    scene: Scene, monkeypatch: Any, duplicate: bool
) -> None:
    s = scene
    ident = send(s, body(s)).json()["committed_member"]["id"]
    target = destination(s)
    leading = command(target)
    trailing = leading if duplicate else command(target)
    headers = {**role_headers(s.client), "Origin": ORIGIN, "X-CSRF-Token": csrf(s.client)}
    entered = Event()
    release = Event()
    holder = []
    waiters = []
    original = Audit.append_member

    def pause(self: Any, e: Any) -> None:
        original(self, e)
        holder.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        entered.set()
        assert release.wait(10)

    def before(conn: Any, _cursor: Any, sql: str, *args: Any) -> None:
        pid = conn.connection.driver_connection.info.backend_pid
        if (
            entered.is_set()
            and not release.is_set()
            and pid not in holder
            and "pg_blocking_pids" not in sql
        ):
            waiters.append(pid)

    monkeypatch.setattr(Audit, "append_member", pause)
    event.listen(s.db.engine, "before_cursor_execute", before)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                s.client.post,
                "/api/v1/admin/members/" + ident + "/home",
                headers=headers,
                json=leading,
            )
            try:
                assert entered.wait(5)
                second = pool.submit(
                    s.client.post,
                    "/api/v1/admin/members/" + ident + "/home",
                    headers=headers,
                    json=trailing,
                )
                wait_for_owned_block(s.db, holder[0], waiters)
                with s.db.session() as db:
                    assert (
                        "iam_installation"
                        in db.execute(
                            text("SELECT query FROM pg_stat_activity WHERE pid=:p"),
                            {"p": waiters[-1]},
                        ).scalar_one()
                    )
            finally:
                release.set()
            assert first.result(timeout=10).status_code == 200
            assert second.result(timeout=10).status_code == (200 if duplicate else 409)
    finally:
        event.remove(s.db.engine, "before_cursor_execute", before)
    assert get(s, "/" + ident).json()["version"] == 2
    with s.db.session() as db:
        assert db.execute(text("SELECT count(*) FROM audit_member_events")).scalar_one() == 2


@pytest.mark.parametrize("absolute", [False, True])
def test_move_original_deadline_crossing_rolls_back_without_touch_rescue(
    scene: Scene, monkeypatch: Any, absolute: bool
) -> None:
    s = scene
    target = destination(s)
    ident = send(s, body(s)).json()["committed_member"]["id"]
    actor = role_headers(s.client)["X-Y3-Expected-Actor"]
    nonce = csrf(s.client)
    with s.db.session() as db:
        if absolute:
            db.execute(
                text("""WITH shifted AS (UPDATE iam_security_states
              SET expires_at=clock_timestamp()+interval '2 seconds'
              WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a) RETURNING id,expires_at)
              UPDATE iam_sessions s SET expires_at=shifted.expires_at,
                created_at=shifted.expires_at-interval '8 hours',
                last_activity=shifted.expires_at-interval '1 minute'
              FROM shifted WHERE s.id=shifted.id"""),
                {"a": actor},
            )
        else:
            db.execute(
                text("""UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',

              last_activity=clock_timestamp()-interval '29 minutes 58 seconds'
              WHERE account_id=:a"""),
                {"a": actor},
            )
        db.commit()
    before = projected(s.db)
    observed = []
    original = Audit.append_member

    def delay(self: Any, e: Any) -> None:
        original(self, e)
        q = text("""SELECT last_activity+interval '30 minutes'>clock_timestamp(),
          expires_at>clock_timestamp()
          FROM iam_sessions WHERE account_id=:a""")
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))

    monkeypatch.setattr(Audit, "append_member", delay)
    r = s.client.post(
        "/api/v1/admin/members/" + ident + "/home",
        headers={"X-Y3-Expected-Actor": actor, "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=command(target),
    )
    assert r.status_code == 401 and observed[0] == (True, True)
    assert observed[1][int(absolute)] is False
    assert projected(s.db) == before
