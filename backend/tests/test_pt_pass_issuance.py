# ruff: noqa: F811
"""Dedicated PG: issuance invariants, independent Trainer eligibility and exact replay."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import event, text

from tests.membership_seed import projected
from tests.password_helpers import call, reset_request
from tests.test_account_lifecycle import mutate
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body as role_body
from tests.test_iam_trainer_roles import change as role_change
from tests.test_membership import body as member_body
from tests.test_membership import grant_operator, headers
from tests.test_membership import send as member_send
from tests.test_pt_catalog import body as product_body
from tests.test_pt_catalog import send as product_send
from tests.test_workforce import Scene, activity, scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres
BASE = "/api/v1/admin"


def setup(t: TrainerScene, **values: Any) -> dict[str, Any]:
    s = t.base
    branch = call(
        s.client, "/admin/branches", csrf(s.client), {"code": "ISSUED", "name": "가상 발급 지점"}
    ).json()["id"]
    member = member_send(s, member_body(s)).json()["committed_member"]
    product = product_send(s, product_body(**values)).json()["committed_product"]
    return {
        "operation_id": str(uuid4()),
        "issued_branch_id": branch,
        "expected_branch_version": 1,
        "member_id": member["id"],
        "expected_member_version": member["version"],
        "trainer_id": t.trainer,
        "expected_trainer_version": 1,
        "product_id": product["id"],
        "expected_product_version": product["version"],
    }


def issue(s: Scene, command: dict[str, Any], client: Any = None) -> Any:
    c = client or s.client
    return c.post(BASE + "/passes", headers=headers(c), json=command)


def receipt(s: Scene, op: str, client: Any = None) -> Any:
    c = client or s.client
    return c.get(BASE + "/pass-operations/" + op, headers=headers(c))


def search(s: Scene, branch: str, query: str, client: Any = None) -> Any:
    c = client or s.client
    return c.post(
        BASE + "/pass-issuance/members/search",
        headers=headers(c),
        json={"issued_branch_id": branch, "query": query},
    )


@pytest.mark.parametrize("home_active", [True, False])
@pytest.mark.parametrize(
    "login_state", ["none", "pending", "active", "blocked", "recovery", "revoked"]
)
def test_active_trainer_home_and_login_are_independent(
    trainer: TrainerScene, home_active: bool, login_state: str
) -> None:
    t = trainer
    s = t.base
    command = setup(t)
    if login_state != "none":
        token = source(t.issue())
        if login_state != "pending":
            assert t.complete(token).status_code == 204
        if login_state == "blocked":
            row = call(
                s.client, "/admin/account-lifecycle/lookup", csrf(s.client), {"login_id": t.login}
            ).json()
            assert mutate(t, row, "status", status="DISABLED").status_code == 200
        if login_state == "recovery":
            assert reset_request(s.client, t.state()["account_id"]).status_code == 201
        if login_state == "revoked":
            assert role_change(t, role_body(t, False)).status_code == 200
    if not home_active:
        with s.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": s.branch},
            )
    before = projected(s.db)
    candidates = s.client.get(
        BASE + "/pass-issuance/trainers",
        headers=headers(s.client),
        params={"issued_branch_id": command["issued_branch_id"]},
    )
    assert candidates.status_code == 200 and candidates.json()["items"][0]["id"] == t.trainer
    result = issue(s, command)
    assert result.status_code == 200
    p = result.json()["pass_record"]
    assert p["initial_trainer_id"] == t.trainer and p["member_id"] == command["member_id"]
    assert (
        p["initial_remaining_sessions"] == p["purchased_sessions"] == p["product"]["session_count"]
    )
    after = projected(s.db)
    assert all(
        after[k] == v for k, v in before.items() if k.startswith("iam_") and k != "iam_sessions"
    )
    assert t.signin().status_code == (204 if login_state == "active" else 401)


def test_exact_snapshot_large_price_count_and_replay_never_reseals(trainer: TrainerScene) -> None:
    t = trainer
    s = t.base
    command = setup(t, price_won="9" * 1024, session_count="9223372036854775807")
    first = issue(s, command)
    assert first.status_code == 200
    result = first.json()
    p = result["pass_record"]
    assert (
        p["product"]["price_won"] == "9" * 1024
        and p["initial_remaining_sessions"] == "9223372036854775807"
    )
    before = projected(s.db)
    before_activity = activity(s.db)
    assert receipt(s, command["operation_id"]).json() == result
    assert issue(s, command).json() == result
    assert projected(s.db) == before and activity(s.db) == before_activity
    changed = product_body(
        name="새 상품 조건", price_won="1", session_count="2", expected_product_version=1
    )
    assert product_send(s, changed, "/" + command["product_id"]).status_code == 200
    assert receipt(s, command["operation_id"]).json() == result
    with s.db.session() as db:
        assert db.execute(
            text(
                "SELECT p.issued_at=o.recorded_at AND o.recorded_at=a.recorded_at "
                "AND o.validated_at=p.issued_at FROM pt_passes p JOIN pt_pass_issue_operations o "
                "ON o.pass_id=p.id JOIN audit_pass_issue_events a ON a.operation_id=o.operation_id"
            )
        ).scalar_one()
        assert db.scalar(text("SELECT count(*) FROM pt_passes")) == 1
        assert db.scalar(text("SELECT count(*) FROM audit_pass_issue_events")) == 1


def test_issuer_union_scoped_search_literal_duplicate_selection_and_no_general_read(
    trainer: TrainerScene, password_app: Any
) -> None:
    t = trainer
    s = t.base
    command = setup(t)
    foreign = call(
        s.client, "/admin/branches", csrf(s.client), {"code": "OTHER-HOME", "name": "가상 타 소속"}
    ).json()["id"]
    member = member_send(s, member_body(s, home_branch_id=foreign)).json()["committed_member"]
    duplicate = member_send(s, member_body(s, home_branch_id=foreign)).json()["committed_member"]
    command = {**command, "member_id": member["id"]}
    with closing(branch_actor(s, password_app[2])) as ba:
        grant_operator(s, "workforce.branch", command["issued_branch_id"])
        from tests.password_helpers import login_password

        login_password(ba, password_app[2], "workforce.branch")
        candidates = search(s, command["issued_branch_id"], "가상 회원", ba)
        assert candidates.status_code == 200
        assert {member["id"], duplicate["id"]} <= {m["id"] for m in candidates.json()["items"]}
        assert set(candidates.json()["items"][0]) == {
            "id",
            "version",
            "name",
            "phone",
            "home_branch_id",
            "home_branch_name",
        }
        assert search(s, command["issued_branch_id"], "%", ba).json()["items"] == []
        assert search(s, command["issued_branch_id"], "_", ba).json()["items"] == []
        assert search(s, command["issued_branch_id"], "   ", ba).status_code == 422
        assert ba.get(BASE + "/members/" + member["id"], headers=headers(ba)).status_code == 404
        assert ba.get(BASE + "/products", headers=headers(ba)).status_code == 403
        result = issue(s, command, ba)
        assert (
            result.status_code == 200 and result.json()["pass_record"]["member_id"] == member["id"]
        )
        assert receipt(s, command["operation_id"]).status_code == 404
        with s.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE iam_operator_grants SET granted=false,version=version+1 "
                    "WHERE account_id=:i"
                ),
                {"i": headers(ba)["X-Y3-Expected-Actor"]},
            )
        assert receipt(s, command["operation_id"], ba).status_code == 401
        login_password(ba, password_app[2], "workforce.branch")
        before = projected(s.db)
        assert receipt(s, command["operation_id"], ba).status_code == 404
        assert issue(s, command, ba).status_code == 404
        assert projected(s.db) == before


@pytest.mark.parametrize("damage", ["member", "trainer", "branch", "product", "stale", "foreign"])
def test_current_eligibility_and_cas_rejection_preserve_all_rows(
    trainer: TrainerScene, damage: str
) -> None:
    t = trainer
    s = t.base
    command = setup(t)
    with s.db.engine.begin() as db:
        if damage == "member":
            pass
        elif damage == "trainer":
            db.execute(
                text(
                    "UPDATE workforce_trainers SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": t.trainer},
            )
        elif damage == "branch":
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:i"
                ),
                {"i": command["issued_branch_id"]},
            )
    if damage == "member":
        assert (
            member_send(
                s,
                {"operation_id": str(uuid4()), "expected_member_version": 1},
                "/" + command["member_id"] + "/deactivate",
            ).status_code
            == 200
        )
    if damage == "product":
        assert (
            product_send(
                s,
                {"operation_id": str(uuid4()), "expected_product_version": 1},
                "/" + command["product_id"] + "/stop",
            ).status_code
            == 200
        )
    if damage == "stale":
        command["expected_member_version"] = 2
    if damage == "foreign":
        command["trainer_id"] = str(uuid4())
    before = projected(s.db)
    assert issue(s, command).status_code == (404 if damage == "foreign" else 409)
    assert projected(s.db) == before


@pytest.mark.parametrize("failure", ["audit", "actor"])
def test_issue_audit_and_final_actor_failure_roll_back_all_facts(
    trainer: TrainerScene, monkeypatch: Any, failure: str
) -> None:
    t = trainer
    s = t.base
    command = setup(t)
    h = headers(s.client)
    before = projected(s.db)
    original = Audit.append_pass_issue

    def fail(self: Any, e: Any) -> None:
        original(self, e)
        if failure == "audit":
            raise Rejected(503, "unavailable")
        self.s.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:i"), {"i": e.actor_id})

    monkeypatch.setattr(Audit, "append_pass_issue", fail)
    result = s.client.post(BASE + "/passes", headers=h, json=command)
    assert result.status_code == (503 if failure == "audit" else 401)
    assert projected(s.db) == before


@pytest.mark.parametrize("same", [False, True])
def test_concurrent_same_uuid_is_one_issue_with_exact_binding(
    trainer: TrainerScene, monkeypatch: Any, same: bool
) -> None:
    t = trainer
    s = t.base
    payload = setup(t)
    h = headers(s.client)
    other = payload if same else {**payload, "expected_member_version": 2}
    entered, release = Event(), Event()
    holders = []
    waiters = []
    original = Audit.append_pass_issue

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

    monkeypatch.setattr(Audit, "append_pass_issue", pause)
    event.listen(s.db.engine, "before_cursor_execute", observe)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(s.client.post, BASE + "/passes", headers=h, json=payload)
            try:
                assert entered.wait(5)
                second = pool.submit(s.client.post, BASE + "/passes", headers=h, json=other)
                wait_for_owned_block(s.db, holders[0], waiters)
            finally:
                release.set()
            a, b = first.result(timeout=10), second.result(timeout=10)
            assert a.status_code == 200 and b.status_code == (200 if same else 409)
            if same:
                assert a.json() == b.json()
    finally:
        event.remove(s.db.engine, "before_cursor_execute", observe)
    with s.db.session() as db:
        assert db.scalar(text("SELECT count(*) FROM pt_passes")) == 1
        assert db.scalar(text("SELECT count(*) FROM audit_pass_issue_events")) == 1


@pytest.mark.parametrize("absolute", [False, True])
def test_issue_original_deadline_crossing_rolls_back_without_touch_rescue(
    trainer: TrainerScene, monkeypatch: Any, absolute: bool
) -> None:
    t = trainer
    s = t.base
    payload = setup(t)
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
    original = Audit.append_pass_issue

    def delay(self: Any, e: Any) -> None:
        original(self, e)
        q = text("""SELECT last_activity+interval '30 minutes'>clock_timestamp(),
          expires_at>clock_timestamp()
          FROM iam_sessions WHERE account_id=:a""")
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))

    monkeypatch.setattr(Audit, "append_pass_issue", delay)
    r = s.client.post(
        BASE + "/passes",
        headers={"X-Y3-Expected-Actor": actor, "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=payload,
    )
    assert r.status_code == 401 and observed[0] == (True, True)
    assert observed[1][int(absolute)] is False
    assert projected(s.db) == before
