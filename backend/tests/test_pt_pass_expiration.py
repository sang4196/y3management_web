# ruff: noqa: F811
"""Dedicated PG: manual expiration preserves original facts and current Issued admin scope."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import event, text

from tests.membership_seed import projected
from tests.password_helpers import call, link_token, login_password
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_membership import grant_operator, headers
from tests.test_membership import send as member_send
from tests.test_pt_catalog import send as product_send
from tests.test_pt_pass_issuance import issue, setup
from tests.test_pt_pass_issuance import receipt as issue_receipt
from tests.test_workforce import Scene, activity, scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres
BASE = "/api/v1/admin/pass-management/passes"


def created(
    t: TrainerScene, *, issued_source: bool = False
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    command = setup(t, session_count="5")
    if issued_source:
        command["issued_branch_id"] = t.base.branch
    result = issue(t.base, command)
    assert result.status_code == 200
    return result.json()["pass_record"]["id"], command, result.json()


def body(version: int, expired: bool = True, reason: str = "가상 수동 처리") -> dict[str, Any]:
    return {
        "operation_id": str(uuid4()),
        "expected_state_version": version,
        "desired_expired": expired,
        "reason": reason,
    }


def change(s: Scene, ident: str, payload: dict[str, Any], client: Any = None) -> Any:
    c = client or s.client
    return c.post(BASE + "/" + ident + "/expiration", headers=headers(c), json=payload)


def detail(s: Scene, ident: str, client: Any = None) -> Any:
    c = client or s.client
    return c.get(BASE + "/" + ident, headers=headers(c))


def receipt(s: Scene, operation: str, client: Any = None) -> Any:
    c = client or s.client
    return c.get("/api/v1/admin/pass-state-operations/" + operation, headers=headers(c))


def old_rows(s: Scene) -> dict[str, str]:
    return {
        k: v
        for k, v in projected(s.db).items()
        if not k.startswith("pt_pass_state_")
        and k not in {"audit_pass_state_events", "iam_sessions"}
    }


def test_expire_release_history_reason_time_and_original_receipt_are_preserved(
    trainer: TrainerScene,
) -> None:
    t = trainer
    s = t.base
    ident, issued, original = created(t)
    first = detail(s, ident).json()
    assert (
        first["version"] == 1 and not first["manual_expired"] and first["remaining_sessions"] == "5"
    )
    before = old_rows(s)
    commands = [body(1), body(2, False, "가상 만료 해제"), body(3, True, "🧩" * 200)]
    results = []
    for c in commands:
        r = change(s, ident, c)
        assert r.status_code == 200
        results.append(r.json())
        assert r.json()["committed_state"]["remaining_sessions"] == "5"
    assert old_rows(s) == before and issue_receipt(s, issued["operation_id"]).json() == original
    with s.db.session() as db:
        rows = db.execute(
            text(
                "SELECT version,manual_expired,recorded_at FROM "
                "pt_pass_state_versions ORDER BY version"
            )
        ).all()
        assert [r[:2] for r in rows] == [(1, False), (2, True), (3, False), (4, True)]
        assert [r[2] for r in rows] == sorted(r[2] for r in rows)
        assert rows[0][2].isoformat().replace("+00:00", "Z") == original["pass_record"][
            "issued_at"
        ].replace("+00:00", "Z")
        assert db.scalar(text("SELECT count(*) FROM audit_pass_state_events")) == 3
        assert db.scalar(
            text(
                "SELECT bool_and(v.recorded_at=o.recorded_at AND o.recorded_at=a.recorded_at) "
                "FROM pt_pass_state_versions v JOIN pt_pass_state_operations o "
                "ON o.operation_id=v.source_operation_id "
                "JOIN audit_pass_state_events a ON a.operation_id=o.operation_id"
            )
        )
    before = projected(s.db)
    before_activity = activity(s.db)
    old = receipt(s, commands[0]["operation_id"]).json()
    assert old["committed_state"] == results[0]["committed_state"]
    assert old["current_state"]["version"] == 4
    assert change(s, ident, commands[0]).json() == old
    assert projected(s.db) == before and activity(s.db) == before_activity
    noop = change(s, ident, body(4))
    assert noop.status_code == 200 and not noop.json()["changed"]
    assert activity(s.db) == before_activity and old_rows(s) == {
        k: v
        for k, v in before.items()
        if not k.startswith("pt_pass_state_")
        and k not in {"audit_pass_state_events", "iam_sessions"}
    }
    before = projected(s.db)
    assert change(s, ident, body(3)).status_code == 409  # stale no-op still conflicts
    assert change(s, ident, {**commands[0], "reason": "다른 전체 명령"}).status_code == 409
    assert projected(s.db) == before


def test_inactive_branch_member_trainer_stopped_product_do_not_block_existing_state_management(
    trainer: TrainerScene, password_app: Any
) -> None:
    t = trainer
    s = t.base
    ident, issued, _ = created(t, issued_source=True)
    with closing(branch_actor(s, password_app[2])) as ba:
        assert (
            member_send(
                s,
                {"operation_id": str(uuid4()), "expected_member_version": 1},
                "/" + issued["member_id"] + "/deactivate",
            ).status_code
            == 200
        )
        t.active(False)
        assert (
            product_send(
                s,
                {"operation_id": str(uuid4()), "expected_product_version": 1},
                "/" + issued["product_id"] + "/stop",
            ).status_code
            == 200
        )
        with s.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET "
                    "active=false,row_version=row_version+1 WHERE id=:i"
                ),
                {"i": s.branch},
            )
        before = old_rows(s)
        assert change(s, ident, body(1), ba).status_code == 200
        assert change(s, ident, body(2, False), ba).status_code == 200
        assert detail(s, ident, ba).json()["remaining_sessions"] == "5" and old_rows(s) == before
        assert issue(s, {**issued, "operation_id": str(uuid4())}, ba).status_code == 409


def test_ba_a_operator_b_manages_only_a_and_loses_own_b_receipt_after_scope_change(
    trainer: TrainerScene, password_app: Any
) -> None:
    t = trainer
    s = t.base
    pass_b, issued, _ = created(t)
    second = {**issued, "operation_id": str(uuid4()), "issued_branch_id": s.branch}
    pass_a = issue(s, second).json()["pass_record"]["id"]
    with closing(branch_actor(s, password_app[2])) as ba:
        grant_operator(s, "workforce.branch", issued["issued_branch_id"])
        login_password(ba, password_app[2], "workforce.branch")
        page = ba.get(BASE, headers=headers(ba)).json()
        assert [p["pass_id"] for p in page["items"]] == [pass_a]
        assert (
            detail(s, pass_b, ba).status_code == 404
            and change(s, pass_b, body(1), ba).status_code == 404
        )
        own_a = body(1)
        assert change(s, pass_a, own_a, ba).status_code == 200
        actor = headers(ba)["X-Y3-Expected-Actor"]

        def move_admin_scope(branch: str) -> None:
            current = s.client.get("/api/v1/admin/accounts/" + actor)
            assert current.status_code == 200
            moved = s.client.patch(
                "/api/v1/admin/accounts/" + actor + "/access",
                headers=headers(s.client),
                json={"expected_version": current.json()["version"], "branch_id": branch},
            )
            assert moved.status_code == 200
            assert ba.get("/api/v1/auth/me").status_code == 401
            ba.cookies.clear()
            login_password(ba, password_app[2], "workforce.branch")

        move_admin_scope(issued["issued_branch_id"])
        own_b = body(1)
        assert change(s, pass_b, own_b, ba).status_code == 200
        move_admin_scope(s.branch)
        before = projected(s.db)
        assert receipt(s, own_b["operation_id"], ba).status_code == 404
        assert change(s, pass_b, own_b, ba).status_code == 404
        assert receipt(s, own_a["operation_id"], ba).status_code == 200
        assert receipt(s, own_a["operation_id"]).status_code == 404  # another Actor, even Master
        assert projected(s.db) == before
        # A separate real Operator-only account proves role exclusion without corrupting IAM facts.
        issued_operator = call(
            s.client,
            "/admin/operator-accounts",
            csrf(s.client),
            {"login_id": t.login, "branch_id": issued["issued_branch_id"]},
        )
        assert issued_operator.status_code == 201
        completed = call(
            t.recipient,
            "/auth/operator-credentials/complete",
            csrf(t.recipient),
            {
                "setup_token": link_token(issued_operator.json()["setup_link"]),
                "new_password": t.password,
            },
        )
        assert completed.status_code == 204
        login_password(t.recipient, t.password, t.login)
        assert issue(s, {**issued, "operation_id": str(uuid4())}, t.recipient).status_code == 200
        before = projected(s.db)
        assert t.recipient.get(BASE, headers=headers(t.recipient)).status_code == 403
        assert detail(s, pass_b, t.recipient).status_code == 403
        assert change(s, pass_b, body(2, False), t.recipient).status_code == 403
        assert receipt(s, own_b["operation_id"], t.recipient).status_code == 403
        assert projected(s.db) == before


@pytest.mark.parametrize("failure", ["audit", "actor"])
def test_state_audit_and_final_actor_failure_roll_back_every_fact(
    trainer: TrainerScene, monkeypatch: Any, failure: str
) -> None:
    t = trainer
    s = t.base
    ident, _, _ = created(t)
    h = headers(s.client)
    before = projected(s.db)
    original = Audit.append_pass_state

    def fail(self: Any, event: Any) -> None:
        original(self, event)
        if failure == "audit":
            raise Rejected(503, "unavailable")
        self.s.execute(
            text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": event.actor_id}
        )

    monkeypatch.setattr(Audit, "append_pass_state", fail)
    r = s.client.post(BASE + "/" + ident + "/expiration", headers=h, json=body(1))
    assert r.status_code == (503 if failure == "audit" else 401) and projected(s.db) == before


@pytest.mark.parametrize(
    "bad",
    [
        {"reason": ""},
        {"reason": " "},
        {"reason": "private-marker" * 30},
        {"desired_expired": 1},
        {"expected_state_version": True},
        {"extra": "private-marker"},
    ],
)
def test_strict_reason_command_no_echo_no_partial_facts(
    trainer: TrainerScene, bad: dict[str, Any]
) -> None:
    s = trainer.base
    ident, _, _ = created(trainer)
    before = projected(s.db)
    r = change(s, ident, {**body(1), **bad})
    assert r.status_code == 422 and "private-marker" not in r.text and projected(s.db) == before


@pytest.mark.parametrize("mode", ["duplicate", "operation_conflict", "stale_noop"])
def test_state_installation_gate_serializes_exact_duplicate_or_cas(
    trainer: TrainerScene, monkeypatch: Any, mode: str
) -> None:
    s = trainer.base
    ident, _, _ = created(trainer)
    h = headers(s.client)
    leading = body(1)
    trailing = (
        leading
        if mode == "duplicate"
        else ({**leading, "reason": "다른 명령"} if mode == "operation_conflict" else body(1))
    )
    entered, release = Event(), Event()
    holders = []
    waiters = []
    original = Audit.append_pass_state

    def pause(self: Any, e: Any) -> None:
        original(self, e)
        holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        entered.set()
        assert release.wait(10)

    def observe(conn: Any, _cursor: Any, sql: str, *args: Any) -> None:
        pid = conn.connection.driver_connection.info.backend_pid
        if (
            entered.is_set()
            and not release.is_set()
            and pid not in holders
            and "pg_blocking_pids" not in sql
        ):
            waiters.append(pid)

    monkeypatch.setattr(Audit, "append_pass_state", pause)
    event.listen(s.db.engine, "before_cursor_execute", observe)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                s.client.post, BASE + "/" + ident + "/expiration", headers=h, json=leading
            )
            try:
                assert entered.wait(5)
                second = pool.submit(
                    s.client.post, BASE + "/" + ident + "/expiration", headers=h, json=trailing
                )
                wait_for_owned_block(s.db, holders[0], waiters)
            finally:
                release.set()
            a, b = first.result(timeout=10), second.result(timeout=10)
            assert a.status_code == 200 and b.status_code == (200 if mode == "duplicate" else 409)
            if mode == "duplicate":
                assert a.json() == b.json()
    finally:
        event.remove(s.db.engine, "before_cursor_execute", observe)
    assert detail(s, ident).json()["version"] == 2
    with s.db.session() as db:
        assert db.scalar(text("SELECT count(*) FROM pt_pass_state_versions")) == 2
        assert db.scalar(text("SELECT count(*) FROM pt_pass_state_operations")) == 1
        assert db.scalar(text("SELECT count(*) FROM audit_pass_state_events")) == 1


@pytest.mark.parametrize("absolute", [False, True])
def test_state_original_deadline_crossing_rolls_back_without_touch_rescue(
    trainer: TrainerScene, monkeypatch: Any, absolute: bool
) -> None:
    t = trainer
    s = t.base
    ident, _, _ = created(t)
    payload = body(1)
    actor = headers(s.client)["X-Y3-Expected-Actor"]
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
    original = Audit.append_pass_state

    def delay(self: Any, e: Any) -> None:
        original(self, e)
        q = text("""SELECT last_activity+interval '30 minutes'>clock_timestamp(),
          expires_at>clock_timestamp()
          FROM iam_sessions WHERE account_id=:a""")
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))

    monkeypatch.setattr(Audit, "append_pass_state", delay)
    r = s.client.post(
        BASE + "/" + ident + "/expiration",
        headers={"X-Y3-Expected-Actor": actor, "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=payload,
    )
    assert r.status_code == 401 and observed[0] == (True, True)
    assert observed[1][int(absolute)] is False
    assert projected(s.db) == before
