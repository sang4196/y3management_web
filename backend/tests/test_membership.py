# ruff: noqa: F811
"""Actual PG: scoped minimum reads, inactive updates, receipts and complete rollback."""

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import event, text

from tests.membership_seed import projected
from tests.password_helpers import PrivateResponse, activate, call, link_token, login_password
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_operator_management import call as role_call
from tests.test_operator_management import role_headers
from tests.test_workforce import Scene, activity, scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres
BASE = "/api/v1/admin/members"


def body(s: Scene, **extra: Any) -> dict[str, Any]:
    return {
        "operation_id": str(uuid4()),
        "name": "가상 회원",
        "phone": "010-2000-0000",
        "home_branch_id": s.branch,
        **extra,
    }


def headers(c: Any) -> dict[str, str]:
    return {**role_headers(c), "Origin": ORIGIN, "X-CSRF-Token": csrf(c)}


def send(
    s: Scene, payload: dict[str, Any], suffix: str = "", client: Any = None
) -> PrivateResponse:
    c = client or s.client
    return PrivateResponse(c.post(BASE + suffix, headers=headers(c), json=payload))


def get(s: Scene, suffix: str = "", client: Any = None) -> PrivateResponse:
    c = client or s.client
    return PrivateResponse(c.get(BASE + suffix, headers=role_headers(c)))


def receipt(s: Scene, operation: str, client: Any = None) -> PrivateResponse:
    c = client or s.client
    return PrivateResponse(
        c.get("/api/v1/admin/member-operations/" + operation, headers=role_headers(c))
    )


def edit(version: int, **extra: Any) -> dict[str, Any]:
    return {
        "operation_id": str(uuid4()),
        "expected_member_version": version,
        "name": "가상 수정",
        "phone": "+82 10 2000 0000",
        **extra,
    }


def test_create_duplicate_canonical_state_noop_replay_and_fresh_current(scene: Scene) -> None:
    s = scene
    original = body(s)
    first = send(s, original)
    assert first.status_code == 200
    member = first.json()["committed_member"]
    ident = member["id"]
    assert (
        member["version"] == 1 and member["active"] and member["values"]["phone"] == "01020000000"
    )
    duplicate = send(s, body(s)).json()["committed_member"]
    assert duplicate["id"] != ident and get(s).json()["total"] == 2
    before = activity(s.db)
    assert send(s, original).json()["committed_member"] == member
    assert activity(s.db) == before
    stopped = send(
        s, {"operation_id": str(uuid4()), "expected_member_version": 1}, "/" + ident + "/deactivate"
    )
    assert stopped.status_code == 200 and not stopped.json()["current_member"]["active"]
    updated = send(s, edit(2), "/" + ident)
    assert updated.status_code == 200
    current = updated.json()["current_member"]
    assert current["version"] == 3 and not current["active"]
    old = receipt(s, original["operation_id"]).json()
    assert old["committed_member"] == member and old["current_member"] == current
    before = activity(s.db)
    noop = send(s, edit(3), "/" + ident)
    assert noop.status_code == 200 and not noop.json()["changed"]
    assert activity(s.db) == before
    assert send(s, edit(2), "/" + ident).status_code == 409
    assert send(s, {**original, "name": "다른 명령"}).status_code == 409
    assert send(
        s, {"operation_id": str(uuid4()), "expected_member_version": 3}, "/" + ident + "/reactivate"
    ).json()["current_member"]["active"]
    with s.db.session() as db:
        assert db.scalar(text("SELECT count(*) FROM membership_members")) == 2
        assert db.scalar(text("SELECT count(*) FROM membership_member_versions")) == 5
        assert db.scalar(text("SELECT count(*) FROM audit_member_events")) == 5
        assert (
            db.scalar(
                text("SELECT count(*) FROM membership_member_operations WHERE validated_at IS NULL")
            )
            == 0
        )


@pytest.mark.parametrize("member_active", [True, False])
@pytest.mark.parametrize("home_active", [True, False])
def test_inactive_member_and_home_edit_preserves_both_states(
    scene: Scene, member_active: bool, home_active: bool
) -> None:
    s = scene
    ident = send(s, body(s)).json()["committed_member"]["id"]
    version = 1
    if not member_active:
        assert (
            send(
                s,
                {"operation_id": str(uuid4()), "expected_member_version": 1},
                "/" + ident + "/deactivate",
            ).status_code
            == 200
        )
        version = 2
    if not home_active:
        with s.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": s.branch},
            )
    result = send(s, edit(version), "/" + ident)
    assert result.status_code == 200
    current = result.json()["current_member"]
    assert current["active"] is member_active and current["home_active"] is home_active
    assert current["home_branch_id"] == s.branch
    assert send(s, body(s)).status_code == (200 if home_active else 409)


def grant_operator(s: Scene, login: str, branch: str) -> None:
    row = role_call(
        s.client,
        "/admin/operator-roles/lookup",
        csrf(s.client),
        {"login_id": login, "branch_id": branch},
    ).json()
    grant = row["operator_grant"]
    result = role_call(
        s.client,
        "/admin/operator-roles/" + row["account_id"] + "/changes",
        csrf(s.client),
        {
            "operation_id": str(uuid4()),
            "expected_account_version": row["account_version"],
            "expected_operator_version": grant["scope"]["version"] if grant else 0,
            "branch_id": branch,
            "desired_granted": True,
        },
    )
    assert result.status_code == 200


def test_branch_admin_operator_union_and_kind_current_receipt(
    scene: Scene, password_app: Any
) -> None:
    s = scene
    password = password_app[2]
    b = call(
        s.client, "/admin/branches", csrf(s.client), {"code": "OTHER", "name": "가상 다른 지점"}
    ).json()["id"]
    foreign = call(
        s.client, "/admin/branches", csrf(s.client), {"code": "HIDDEN", "name": "가상 비허용 지점"}
    ).json()["id"]
    with closing(branch_actor(s, password)) as other:
        grant_operator(s, "workforce.branch", b)
        login_password(other, password, "workforce.branch")
        a = send(s, body(s), client=other).json()["committed_member"]
        op = send(s, body(s, home_branch_id=b), client=other).json()["committed_member"]
        denied = send(s, body(s, home_branch_id=foreign)).json()["committed_member"]
        assert get(s, client=other).json()["total"] == 2
        assert get(s, "/" + denied["id"], client=other).status_code == 404
        assert send(s, edit(1), "/" + op["id"], client=other).status_code == 200
        assert (
            send(
                s,
                {"operation_id": str(uuid4()), "expected_member_version": 2},
                "/" + op["id"] + "/deactivate",
                other,
            ).status_code
            == 404
        )
        command = {"operation_id": str(uuid4()), "expected_member_version": 1}
        assert send(s, command, "/" + a["id"] + "/deactivate", other).status_code == 200
        row = role_call(
            s.client,
            "/admin/operator-roles/lookup",
            csrf(s.client),
            {"login_id": "workforce.branch", "branch_id": b},
        ).json()
        moved = role_call(
            s.client,
            "/admin/operator-roles/" + row["account_id"] + "/branch",
            csrf(s.client),
            {
                "operation_id": str(uuid4()),
                "expected_account_version": row["account_version"],
                "expected_operator_version": row["operator_grant"]["scope"]["version"],
                "branch_id": s.branch,
            },
        )
        assert moved.status_code == 200
        login_password(other, password, "workforce.branch")
        with s.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": s.branch},
            )
        inactive_edit = send(s, edit(2, name="비활성 Home BA 수정"), "/" + a["id"], other)
        assert inactive_edit.status_code == 200
        assert not inactive_edit.json()["current_member"]["active"]
        assert not inactive_edit.json()["current_member"]["home_active"]
        with s.db.engine.begin() as db:
            actor = role_headers(other)["X-Y3-Expected-Actor"]
            db.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": actor})
        # Operator(A) still edits A; it cannot recover the former administrator state command.
        assert receipt(s, str(command["operation_id"]), other).status_code == 404
        assert send(s, command, "/" + a["id"] + "/deactivate", other).status_code == 404
        assert send(s, edit(3, name="현재 Operator 수정"), "/" + a["id"], other).status_code == 200
        assert get(s, "/" + op["id"], other).status_code == 404
        with s.db.session() as db:
            assert (
                db.scalar(
                    text(
                        "SELECT count(*) FROM audit_member_events WHERE member_id=:i "
                        "AND actor_role='OPERATOR' AND actor_branch=:b"
                    ),
                    {"i": op["id"], "b": b},
                )
                == 2
            )


@pytest.mark.parametrize(
    "bad",
    [
        {"name": ""},
        {"phone": None},
        {"phone": "sensitive-marker"},
        {"phone": "0212345678"},
        {"phone": 1234},
        {"home_branch_id": None},
        {"active": False},
    ],
)
def test_required_strict_values_no_echo_no_partial_facts(scene: Scene, bad: dict[str, Any]) -> None:
    s = scene
    before = projected(s.db)
    r = send(s, body(s, **bad))
    assert r.status_code == 422 and "sensitive-marker" not in r.response.text
    assert projected(s.db) == before


@pytest.mark.parametrize("failure", ["audit", "actor"])
def test_audit_and_final_actor_failure_roll_back_every_fact(
    scene: Scene, monkeypatch: Any, failure: str
) -> None:
    s = scene
    h = headers(s.client)
    before = projected(s.db)
    original = Audit.append_member

    def fail(self: Any, event: Any) -> None:
        original(self, event)
        if failure == "audit":
            raise Rejected(503, "unavailable")
        self.s.execute(
            text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": event.actor_id}
        )

    monkeypatch.setattr(Audit, "append_member", fail)
    result = s.client.post(BASE, headers=h, json=body(s))
    assert result.status_code == (503 if failure == "audit" else 401)
    assert projected(s.db) == before


def test_expected_actor_csrf_and_direct_unknown_member(scene: Scene) -> None:
    s = scene
    h = headers(s.client)
    before = projected(s.db)
    assert (
        s.client.post(
            BASE, headers={**h, "X-Y3-Expected-Actor": str(uuid4())}, json=body(s)
        ).status_code
        == 409
    )
    assert (
        s.client.post(BASE, headers={**h, "X-CSRF-Token": "invalid"}, json=body(s)).status_code
        == 403
    )
    assert get(s, "/" + str(uuid4())).status_code == 404
    assert s.client.get(BASE).status_code == 422
    assert projected(s.db) == before


@pytest.mark.parametrize("absolute", [False, True])
def test_original_deadline_crossing_after_audit_does_not_touch_rescue(
    scene: Scene, monkeypatch: Any, absolute: bool
) -> None:
    s = scene
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
        BASE,
        headers={"X-Y3-Expected-Actor": actor, "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=body(s),
    )
    assert r.status_code == 401 and observed[0] == (True, True)
    assert observed[1][int(absolute)] is False
    assert projected(s.db) == before


@pytest.mark.parametrize("duplicate", [False, True])
def test_actual_installation_gate_serializes_duplicate_or_cas(
    scene: Scene, monkeypatch: Any, duplicate: bool
) -> None:
    s = scene
    ident = send(s, body(s)).json()["committed_member"]["id"]
    leading = edit(1, name="leading")
    trailing = leading if duplicate else edit(1, name="trailing")
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
            first = pool.submit(s.client.post, BASE + "/" + ident, headers=headers, json=leading)
            try:
                assert entered.wait(5)
                second = pool.submit(
                    s.client.post, BASE + "/" + ident, headers=headers, json=trailing
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


@pytest.mark.parametrize("kind", ["read", "receipt", "noop", "replay"])
def test_final_original_proof_on_non_audited_paths(
    scene: Scene, monkeypatch: Any, kind: str
) -> None:
    from y3management.iam.roles import TrainerRoles

    s = scene
    command = body(s)
    ident = send(s, command).json()["committed_member"]["id"]
    headers = {**role_headers(s.client), "Origin": ORIGIN, "X-CSRF-Token": csrf(s.client)}
    actor = headers["X-Y3-Expected-Actor"]
    with s.db.session() as db:
        db.execute(
            text("""UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',
          last_activity=clock_timestamp()-interval '29 minutes 58 seconds' WHERE account_id=:a"""),
            {"a": actor},
        )
        db.commit()
    before = projected(s.db)
    original = TrainerRoles.confirm_actor
    observed = []

    def delayed(self: Any, *args: Any, **kwargs: Any) -> Any:
        q = text(
            "SELECT last_activity+interval '30 minutes'>clock_timestamp() "
            "FROM iam_sessions WHERE account_id=:a"
        )
        observed.append(self.s.execute(q, {"a": actor}).scalar_one())
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        observed.append(self.s.execute(q, {"a": actor}).scalar_one())
        return original(self, *args, **kwargs)

    monkeypatch.setattr(TrainerRoles, "confirm_actor", delayed)
    if kind == "read":
        r = s.client.get(BASE + "/" + ident, headers=headers)
    elif kind == "receipt":
        r = s.client.get(
            "/api/v1/admin/member-operations/" + command["operation_id"], headers=headers
        )
    else:
        r = s.client.post(
            BASE + ("/" + ident if kind == "noop" else ""),
            headers=headers,
            json=edit(1, name="가상 회원") if kind == "noop" else command,
        )
    assert r.status_code == 401 and observed == [True, False]
    assert projected(s.db) == before


def test_trainer_only_and_foreign_organization_direct_ids_are_denied(trainer: TrainerScene) -> None:
    t = trainer
    s = t.base
    member = send(s, body(s)).json()["committed_member"]
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    assert get(s, client=t.recipient).status_code == 403
    assert get(s, "/" + member["id"], t.recipient).status_code == 403
    assert send(s, body(s), client=t.recipient).status_code == 403
    other, foreign_branch, foreign_member, foreign_actor, foreign_op = [
        str(uuid4()) for _ in range(5)
    ]
    with s.db.engine.begin() as db:
        db.execute(
            text("INSERT INTO organization_organizations(id,name) VALUES(:i,:n)"),
            {"i": other, "n": "가상 타 조직"},
        )
        db.execute(
            text(
                "INSERT INTO organization_branches(id,organization_id,code,name) "
                "VALUES(:i,:o,:c,:n)"
            ),
            {"i": foreign_branch, "o": other, "c": "FOREIGN", "n": "가상 타 조직 지점"},
        )
        db.execute(
            text(
                "INSERT INTO iam_accounts SELECT (jsonb_populate_record(NULL::iam_accounts,"
                "to_jsonb(a)||CAST(:j AS jsonb))).* FROM iam_accounts a LIMIT 1"
            ),
            {
                "j": json.dumps(
                    {
                        "id": foreign_actor,
                        "organization_id": other,
                        "login_id": "member.foreign",
                        "login_budget_key": None,
                    }
                )
            },
        )
        db.execute(
            text("INSERT INTO iam_login_ids(login_id,account_id) VALUES('member.foreign',:a)"),
            {"a": foreign_actor},
        )
        changes = {
            "organization_id": other,
            "member_id": foreign_member,
            "actor_id": foreign_actor,
            "operation_id": foreign_op,
            "home_branch_id": foreign_branch,
        }
        for table, extra in [
            ("membership_members", {"id": foreign_member}),
            ("membership_member_versions", {"source_operation_id": foreign_op}),
            ("membership_member_operations", {}),
        ]:
            columns = list(
                db.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns WHERE "
                        "table_schema=current_schema() AND table_name=:t AND is_generated='NEVER' "
                        "ORDER BY ordinal_position"
                    ),
                    {"t": table},
                ).scalars()
            )
            names = ",".join(columns)
            db.execute(
                text(
                    "INSERT INTO "
                    + table
                    + "("
                    + names
                    + ") SELECT "
                    + names
                    + " FROM (SELECT (jsonb_populate_record(NULL::"
                    + table
                    + ",to_jsonb(t)||CAST(:j AS jsonb))).* FROM "
                    + table
                    + " t LIMIT 1) copy"
                ),
                {"j": json.dumps(changes | extra)},
            )
    assert send(s, body(s, home_branch_id=foreign_branch)).status_code == 404
    assert get(s, "/" + foreign_member).status_code == 404
    assert receipt(s, foreign_op).status_code == 404
    assert get(s).json()["total"] == 1


def test_other_current_master_cannot_reuse_or_read_original_actor_receipt(
    scene: Scene, password_app: Any
) -> None:
    from fastapi.testclient import TestClient

    s = scene
    original = body(s)
    ident = send(s, original).json()["committed_member"]["id"]
    with closing(TestClient(s.client.app, base_url=ORIGIN)) as other:
        issued = call(
            s.client, "/admin/master-accounts", csrf(s.client), {"login_id": "member.other"}
        )
        assert issued.status_code == 201
        activate(other, link_token(issued.json()["setup_link"]), password_app[2])
        login_password(other, password_app[2], "member.other")
        assert get(s, "/" + ident, other).status_code == 200
        assert receipt(s, original["operation_id"], other).status_code == 404
        assert send(s, original, client=other).status_code == 409
        assert send(s, edit(1), "/" + ident, other).status_code == 200
