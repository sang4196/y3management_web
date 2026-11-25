# ruff: noqa: F811
"""PT-001 actual PostgreSQL policy, exact values, immutable history and Actor proof."""

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg.errors import ForeignKeyViolation
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError

from tests.password_helpers import activate, call, link_token, login_password
from tests.pt_catalog_seed import projected
from tests.test_iam import ORIGIN, csrf
from tests.test_operator_management import role_headers
from tests.test_workforce import Scene, activity, scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor, wait_for_owned_block
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres
BASE = "/api/v1/admin/products"


def body(**extra: Any) -> dict[str, Any]:
    return {
        "operation_id": str(uuid4()),
        "name": "가상 PT 상품",
        "price_won": "0",
        "session_count": "1",
        "payment_type": "RATE",
        "is_service": False,
        **extra,
    }


def send(s: Scene, payload: dict[str, Any], suffix: str = "", client: Any = None) -> Any:
    c = client or s.client
    return c.post(
        BASE + suffix,
        headers={**role_headers(c), "Origin": ORIGIN, "X-CSRF-Token": csrf(c)},
        json=payload,
    )


def get(s: Scene, suffix: str = "", client: Any = None) -> Any:
    c = client or s.client
    return c.get(BASE + suffix, headers=role_headers(c))


def receipt(s: Scene, operation: str, client: Any = None) -> Any:
    c = client or s.client
    return c.get("/api/v1/admin/product-operations/" + operation, headers=role_headers(c))


def test_complete_history_stop_edit_noop_replay_and_exact_large_values(scene: Scene) -> None:
    s = scene
    original = body(name="한" * 200, price_won="9" * 1024, session_count="9223372036854775807")
    response = send(s, original)
    assert response.status_code == 200
    first = response.json()["committed_product"]
    ident = first["id"]
    assert first["values"]["session_count"] == original["session_count"]
    assert first["values"]["price_won"] == original["price_won"] and first["selling"]
    assert first["version"] == 1
    headers = role_headers(s.client)
    nonce = csrf(s.client)
    before = activity(s.db)
    assert get(s, "/" + ident).json() == first
    assert get(s).json() == {"items": [first], "total": 1}
    assert send(s, original).json()["committed_product"] == first
    assert activity(s.db) == before
    with s.db.session() as db:
        version1 = db.execute(
            text("SELECT to_jsonb(v) FROM pt_product_versions v WHERE version=1")
        ).scalar_one()
    edit = body(
        expected_product_version=1,
        name="고정 일반",
        price_won="0",
        session_count="9007199254740993",
        payment_type="FIXED_AMOUNT",
    )
    second = send(s, edit, "/" + ident).json()["committed_product"]
    assert second["version"] == 2 and second["values"]["is_service"] is False
    stop = {"operation_id": str(uuid4()), "expected_product_version": 2}
    third = send(s, stop, "/" + ident + "/stop").json()["committed_product"]
    assert third["selling"] is False and third["version"] == 3
    fourth = send(
        s,
        body(
            expected_product_version=3, name="서비스", is_service=True, payment_type="FIXED_AMOUNT"
        ),
        "/" + ident,
    ).json()["committed_product"]
    assert fourth["version"] == 4 and fourth["selling"] is False
    old = receipt(s, original["operation_id"]).json()
    assert old["committed_product"] == first and old["current_product"] == fourth
    assert send(s, original).json() == old
    for payload, path in [
        (body(**fourth["values"], expected_product_version=4), "/" + ident),
        ({"operation_id": str(uuid4()), "expected_product_version": 4}, "/" + ident + "/stop"),
    ]:
        before = activity(s.db)
        result = send(s, payload, path)
        assert result.status_code == 200 and result.json()["changed"] is False
        assert activity(s.db) == before
    assert (
        send(s, body(**fourth["values"], expected_product_version=3), "/" + ident).status_code
        == 409
    )
    assert send(s, {**original, "price_won": "1"}).status_code == 409
    with s.db.session() as db:
        assert db.execute(text("SELECT count(*) FROM pt_products")).scalar_one() == 1
        assert db.execute(text("SELECT count(*) FROM pt_product_versions")).scalar_one() == 4
        assert db.execute(text("SELECT count(*) FROM audit_product_events")).scalar_one() == 4
        assert db.execute(text("SELECT count(*) FROM pt_product_operations")).scalar_one() == 6
        assert (
            db.execute(
                text("SELECT count(*) FROM pt_product_operations WHERE validated_at IS NULL")
            ).scalar_one()
            == 0
        )
        assert (
            db.execute(
                text("SELECT to_jsonb(v) FROM pt_product_versions v WHERE version=1")
            ).scalar_one()
            == version1
        )
    assert (
        s.client.post(
            BASE,
            headers={**headers, "Origin": ORIGIN, "X-CSRF-Token": nonce},
            json={**body(), "selling": True},
        ).status_code
        == 422
    )


def test_explicit_validation_no_echo_and_rejected_requests_preserve(scene: Scene) -> None:
    s = scene
    valid = body()
    role_headers(s.client)
    csrf(s.client)
    before = projected(s.db)
    bad = [
        {k: v for k, v in valid.items() if k != field}
        for field in ["name", "price_won", "session_count", "payment_type", "is_service"]
    ]
    invalid_values: dict[str, list[Any]] = {
        "name": ["", " ", "bad\nname", "한" * 201, None],
        "price_won": [None, 0, True, "-1", "1.0", "01", "1e2", "NaN", "9" * 1025],
        "session_count": [None, 1, True, "0", "-1", "1.1", "01", "9223372036854775808"],
        "payment_type": [None, "secret-marker"],
        "is_service": [None, 1, "true"],
    }
    for field, values in invalid_values.items():
        bad.extend({**valid, field: value} for value in values)
    bad.extend(
        [{**valid, "is_service": True}, {**valid, "rate_percent": 50}, {**valid, "selling": False}]
    )
    for payload in bad:
        r = send(s, payload)
        assert r.status_code == 422 and r.json() == {"detail": "invalid_request"}
    assert get(s, "?unexpected=secret").status_code == 422
    assert get(s, "?offset=-1").status_code == 422
    assert get(s, "?limit=101").status_code == 422
    assert s.client.get(BASE).status_code == 422
    assert s.client.post(BASE, headers=role_headers(s.client), json=valid).status_code == 403
    assert (
        s.client.post(
            BASE, headers={**role_headers(s.client), "Origin": ORIGIN}, json=valid
        ).status_code
        == 403
    )
    assert (
        s.client.post(
            BASE,
            headers={
                "X-Y3-Expected-Actor": str(uuid4()),
                "Origin": ORIGIN,
                "X-CSRF-Token": csrf(s.client),
            },
            json=valid,
        ).status_code
        == 409
    )
    assert projected(s.db) == before


def test_current_master_actor_bound_receipts_cross_org_and_nonmaster(
    scene: Scene, password_app: Any
) -> None:
    s = scene
    command = body()
    ident = send(s, command).json()["committed_product"]["id"]
    with closing(branch_actor(s, password_app[2])) as branch:
        for suffix in ["", "/" + ident]:
            assert get(s, suffix, branch).status_code == 403
        assert send(s, body(), client=branch).status_code == 403
        assert receipt(s, command["operation_id"], branch).status_code == 403
        assert branch.get("/products").status_code == 403
    with closing(TestClient(s.client.app, base_url=ORIGIN)) as other:
        issued = call(
            s.client, "/admin/master-accounts", csrf(s.client), {"login_id": "catalog.other"}
        )
        assert issued.status_code == 201
        activate(other, link_token(issued.json()["setup_link"]), password_app[2])
        login_password(other, password_app[2], "catalog.other")
        assert get(s, "/" + ident, other).status_code == 200
        assert receipt(s, command["operation_id"], other).status_code == 404
        assert send(s, command, client=other).status_code == 409
        assert (
            send(
                s, body(expected_product_version=1, name="다른 Master"), "/" + ident, other
            ).status_code
            == 200
        )
    # Real foreign rows, consistently related through actual composite FKs.
    org, product, operation, actor = [str(uuid4()) for _ in range(4)]
    with s.db.session() as db:
        db.execute(
            text("INSERT INTO organization_organizations VALUES(:o,'foreign synthetic')"),
            {"o": org},
        )
        db.execute(
            text("""INSERT INTO iam_accounts SELECT (jsonb_populate_record(NULL::iam_accounts,
          to_jsonb(a)||CAST(:j AS jsonb))).* FROM iam_accounts a LIMIT 1"""),
            {
                "j": json.dumps(
                    {
                        "id": actor,
                        "organization_id": org,
                        "login_id": "catalog.foreign.synthetic",
                        "login_budget_key": None,
                    }
                )
            },
        )
        db.execute(
            text(
                "INSERT INTO iam_login_ids(login_id,account_id) "
                "VALUES('catalog.foreign.synthetic',:a)"
            ),
            {"a": actor},
        )
        db.execute(
            text("""INSERT INTO iam_admin_grants(account_id,organization_id,scope,branch_id)
          VALUES(:a,:o,'ORGANIZATION',NULL)"""),
            {"a": actor, "o": org},
        )
        changes = {
            "organization_id": org,
            "product_id": product,
            "actor_id": actor,
            "operation_id": operation,
        }
        clones: list[tuple[str, dict[str, Any], str]] = [
            ("pt_products", {"id": product, "current_version": 1}, ""),
            ("pt_product_versions", {"source_operation_id": operation}, " WHERE version=1"),
            ("pt_product_operations", {}, " WHERE kind='create'"),
        ]
        for table, extra, where in clones:
            patch = changes | extra
            db.execute(
                text(
                    "INSERT INTO "
                    + table
                    + " SELECT (jsonb_populate_record(NULL::"
                    + table
                    + ",to_jsonb(t)||CAST(:j AS jsonb))).* FROM "
                    + table
                    + " t"
                    + where
                    + " LIMIT 1"
                ),
                {"j": json.dumps(patch)},
            )
        db.commit()
    assert get(s, "/" + product).status_code == 404
    assert receipt(s, operation).status_code == 404
    assert get(s).json()["total"] == 1


@pytest.mark.parametrize("failure", ["audit", "actor"])
def test_audit_or_changed_actor_rolls_all_catalog_and_activity_back(
    scene: Scene, monkeypatch: Any, failure: str
) -> None:
    s = scene
    role_headers(s.client)
    nonce = csrf(s.client)
    before = projected(s.db)
    original = Audit.append_product

    def fail(self: Any, e: Any) -> None:
        original(self, e)
        if failure == "audit":
            raise Rejected(503, "unavailable")
        self.s.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": e.actor_id})

    monkeypatch.setattr(Audit, "append_product", fail)
    r = s.client.post(
        BASE,
        headers={**role_headers(s.client), "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=body(),
    )
    assert r.status_code == (503 if failure == "audit" else 401)
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
    original = Audit.append_product

    def delay(self: Any, e: Any) -> None:
        original(self, e)
        q = text("""SELECT last_activity+interval '30 minutes'>clock_timestamp(),
          expires_at>clock_timestamp()
          FROM iam_sessions WHERE account_id=:a""")
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        observed.append(tuple(self.s.execute(q, {"a": actor}).one()))

    monkeypatch.setattr(Audit, "append_product", delay)
    r = s.client.post(
        BASE,
        headers={"X-Y3-Expected-Actor": actor, "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=body(),
    )
    assert r.status_code == 401 and observed[0] == (True, True)
    assert observed[1][int(absolute)] is False
    assert projected(s.db) == before


@pytest.mark.parametrize("duplicate", [False, True])
def test_actual_installation_gate_serializes_duplicate_or_cas(
    scene: Scene, monkeypatch: Any, duplicate: bool
) -> None:
    s = scene
    ident = send(s, body()).json()["committed_product"]["id"]
    leading = body(expected_product_version=1, name="leading")
    trailing = leading if duplicate else body(expected_product_version=1, name="trailing")
    headers = {**role_headers(s.client), "Origin": ORIGIN, "X-CSRF-Token": csrf(s.client)}
    entered = Event()
    release = Event()
    holder = []
    waiters = []
    original = Audit.append_product

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

    monkeypatch.setattr(Audit, "append_product", pause)
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
        assert db.execute(text("SELECT count(*) FROM audit_product_events")).scalar_one() == 2


def test_postgresql_typed_constraints_and_nullable_core_proofs(scene: Scene) -> None:
    s = scene
    first = send(s, body()).json()["committed_product"]
    ident = first["id"]
    result = send(s, body(expected_product_version=1, name="next"), "/" + ident).json()
    before = projected(s.db)
    statements = [
        ("UPDATE pt_product_versions SET is_service=true WHERE version=1", None),
        ("UPDATE pt_product_versions SET selling=false WHERE version=2", None),
        ("UPDATE pt_product_versions SET session_count=0 WHERE version=1", None),
        ("UPDATE pt_product_versions SET price_won='NaN' WHERE version=1", None),
        ("UPDATE pt_product_operations SET before_version=NULL WHERE kind='update'", None),
        (
            "UPDATE audit_product_events SET actor_id=:random WHERE kind='create'",
            "audit_product_core_fk",
        ),
        (
            """UPDATE audit_product_events SET before_version=2,
          after_version=3 WHERE kind='update'""",
            "audit_product_core_fk",
        ),
    ]
    for sql, constraint in statements:
        with s.db.session() as db:
            with pytest.raises(IntegrityError) as caught:
                db.execute(text(sql), {"random": uuid4()})
                db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            if constraint:
                assert isinstance(caught.value.orig, ForeignKeyViolation)
                assert (
                    caught.value.orig.sqlstate == "23503"
                    and caught.value.orig.diag.constraint_name == constraint
                )
        assert projected(s.db) == before
    # Before-only corruption keeps the nonnull core identical; its deferred FK catches it.
    with s.db.session() as db:
        with pytest.raises(IntegrityError) as caught:
            db.execute(
                text("UPDATE audit_product_events SET before_version=7 WHERE operation_id=:i"),
                {"i": result["operation_id"]},
            )
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        assert isinstance(caught.value.orig, ForeignKeyViolation)
        assert caught.value.orig.diag.constraint_name == "audit_product_before_fk"
    assert projected(s.db) == before


@pytest.mark.parametrize("kind", ["read", "receipt", "noop", "replay"])
def test_final_original_proof_on_non_audited_paths(
    scene: Scene, monkeypatch: Any, kind: str
) -> None:
    from y3management.iam.roles import TrainerRoles

    s = scene
    command = body()
    ident = send(s, command).json()["committed_product"]["id"]
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
            "/api/v1/admin/product-operations/" + command["operation_id"], headers=headers
        )
    else:
        r = s.client.post(
            BASE + ("/" + ident if kind == "noop" else ""),
            headers=headers,
            json=body(expected_product_version=1) if kind == "noop" else command,
        )
    assert r.status_code == 401 and observed == [True, False]
    assert projected(s.db) == before


def test_independent_master_remains_catalog_actor_when_own_trainer_inactive(
    scene: Scene, password_app: Any
) -> None:
    from tests.test_iam_trainer import TrainerScene
    from tests.test_iam_trainer_roles import change as grant
    from tests.test_iam_trainer_roles_security import link
    from tests.test_workforce_state import change as state_change
    from tests.test_workforce_state import request as state_request

    s = scene
    registered = s.send({**s.body(), "base_salary_won": "0", "base_salary_start_month": "2020-01"})
    assert registered.status_code == 201
    t = TrainerScene(s, registered.json()["trainer"]["id"], s.client, "unused", "unused")
    actor = s.client.get("/api/v1/auth/me").json()["account_id"]
    assert grant(t, link(t, actor, "master.test")).status_code == 200
    login_password(s.client, password_app[2], "master.test")
    assert state_change(t, state_request(t, False)).status_code == 200
    assert s.client.get("/api/v1/admin/trainers/" + t.trainer).json()["active"] is False
    before = projected(s.db)
    assert send(s, body()).status_code == 200
    assert get(s).json()["total"] == 1
    assert s.client.get("/products").status_code == 200
    after = projected(s.db)
    assert all(
        after[k] == v
        for k, v in before.items()
        if not k.startswith("pt_") and k not in {"audit_product_events", "iam_sessions"}
    )
    assert s.client.get("/api/v1/admin/trainers/" + t.trainer).json()["active"] is False
