# ruff: noqa: F811
"""Base calendar ledger, receipts and immutable registration facts in real PostgreSQL."""

from datetime import UTC
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.password_helpers import PrivateResponse
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_operator_management import role_headers
from tests.test_workforce import Scene, activity, scene  # noqa: F401

pytestmark = pytest.mark.postgres


def register(s: Scene, start: str = "2020-01") -> str:
    r = s.send({**s.body(), "base_salary_start_month": start, "base_salary_won": "100"})
    assert r.status_code == 201
    return str(r.json()["trainer"]["id"])


def read(s: Scene, ident: str, query: str = "basis_month=2090-06") -> Any:
    return s.client.get(
        "/api/v1/admin/trainers/" + ident + "/base-schedule?" + query,
        headers=role_headers(s.client),
    )


def command(s: Scene, ident: str, **extra: Any) -> dict[str, Any]:
    v = read(s, ident).json()
    return dict(
        operation_id=str(uuid4()),
        expected_trainer_version=v["trainer_version"],
        expected_base_ledger_version=v["base_ledger_version"],
        **extra,
    )


def send(s: Scene, ident: str, b: dict[str, Any], suffix: str = "") -> Any:
    return PrivateResponse(
        s.client.post(
            "/api/v1/admin/trainers/" + ident + "/base-schedule/changes" + suffix,
            headers={**role_headers(s.client), "Origin": ORIGIN, "X-CSRF-Token": csrf(s.client)},
            json=b,
        )
    )


def test_calendar_create_edit_cancel_receipts_and_initial_overlay(scene: Scene) -> None:
    s = scene
    ident = register(s)
    initial = read(s, ident).json()
    assert initial["general_setting"]["planned_amount_won"] == "100"
    assert initial["anchor"]["is_initial"] and initial["items"] == []
    assert read(s, ident, "basis_month=2019-12").json()["general_setting"] is None
    b = command(s, ident, start_month="2090-01", planned_amount_won="100")
    first = send(s, ident, b)
    assert first.status_code == 200
    assert first.json()["changed"] and first.json()["committed_base_ledger_version"] == 2
    change = first.json()["committed_change"]
    assert change["revision"] == 1
    noop = command(s, ident, expected_change_revision=1, planned_amount_won="100")
    before = activity(s.db)
    assert send(s, ident, noop, "/" + change["change_id"] + "/edit").json()["changed"] is False
    assert activity(s.db) == before
    edit = command(s, ident, expected_change_revision=1, planned_amount_won="0")
    assert send(s, ident, edit, "/" + change["change_id"] + "/edit").status_code == 200
    cancel = command(s, ident, expected_change_revision=2)
    assert send(s, ident, cancel, "/" + change["change_id"] + "/cancel").status_code == 200
    current = read(s, ident).json()
    assert current["base_ledger_version"] == 4
    assert current["general_setting"]["planned_amount_won"] == "100"
    assert current["items"][0]["planned_amount_won"] == "0"
    assert current["items"][0]["active"] is False
    assert current["items"][0]["cancellable"] is False
    assert (
        send(
            s,
            ident,
            command(s, ident, expected_change_revision=3),
            "/" + change["change_id"] + "/cancel",
        ).status_code
        == 409
    )
    recreate = send(s, ident, command(s, ident, start_month="2090-01", planned_amount_won="7"))
    assert recreate.status_code == 200
    assert recreate.json()["committed_change"]["change_id"] != change["change_id"]
    assert recreate.json()["committed_change"]["revision"] == 1
    replay = send(s, ident, b)
    assert replay.status_code == 200
    assert replay.json()["committed_base_ledger_version"] == 2
    assert replay.json()["current_base_ledger_version"] == 5
    history = s.client.get(
        "/api/v1/admin/trainers/" + ident + "/base-schedule-history", headers=role_headers(s.client)
    ).json()
    assert [x["ledger_version"] for x in history["items"]] == [1, 2, 3, 4, 5]
    assert [x["kind"] for x in history["items"]] == [
        "initial",
        "create",
        "edit",
        "cancel",
        "create",
    ]
    with s.db.session() as db:
        row = db.execute(
            text(
                "SELECT base_salary_won,base_salary_start_month,row_version,"
                "compensation_version FROM workforce_trainers WHERE id=:i"
            ),
            {"i": ident},
        ).one()
        assert tuple(map(str, row)) == ("100", "2020-01-01", "1", "1")
    overlay = register(s, "9999-12")
    assert (
        send(
            s, overlay, command(s, overlay, start_month="9999-11", planned_amount_won="1")
        ).status_code
        == 409
    )
    result = send(s, overlay, command(s, overlay, start_month="9999-12", planned_amount_won="2"))
    assert result.status_code == 200
    cid = result.json()["committed_change"]["change_id"]
    assert (
        read(s, overlay, "basis_month=9999-12").json()["general_setting"]["planned_amount_won"]
        == "2"
    )
    assert (
        send(
            s, overlay, command(s, overlay, expected_change_revision=1), "/" + cid + "/cancel"
        ).status_code
        == 200
    )
    assert (
        read(s, overlay, "basis_month=9999-12").json()["general_setting"]["planned_amount_won"]
        == "100"
    )


def test_cas_month_pages_and_anchor_are_explicit(scene: Scene) -> None:
    s = scene
    ident = register(s)
    first = read(s, ident).json()
    current_month = first["server_business_month"]
    assert (
        send(
            s, ident, command(s, ident, start_month=current_month, planned_amount_won="0")
        ).status_code
        == 409
    )
    stale = command(s, ident, start_month="2091-01", planned_amount_won="2")
    assert (
        send(s, ident, command(s, ident, start_month="2090-01", planned_amount_won="1")).status_code
        == 200
    )
    assert send(s, ident, stale).status_code == 409
    assert read(s, ident, "basis_month=2090-01&offset=1").status_code == 422
    query = (
        "basis_month=2090-01&offset=1&expected_base_ledger_version=1"
        "&expected_basis_month=2090-01&expected_server_business_month=" + current_month
    )
    assert read(s, ident, query).status_code == 409
    assert (
        send(
            s, ident, command(s, ident, expected_change_revision=1), "/" + ident + "/cancel"
        ).status_code
        == 409
    )
    before = activity(s.db)
    assert (
        s.client.get(
            "/api/v1/admin/trainers/" + ident + "/base-schedule?basis_month=2090-01"
        ).status_code
        == 422
    )
    assert activity(s.db) == before


def test_final_proof_month_rollback_replay_and_typed_constraints(
    scene: Scene, monkeypatch: Any
) -> None:
    from datetime import datetime

    from psycopg.errors import ForeignKeyViolation
    from sqlalchemy.exc import IntegrityError

    from y3management.audit.infrastructure import Audit
    from y3management.iam.roles import TrainerRoles

    s = scene
    ident = register(s)
    original_proof = TrainerRoles.confirm_actor

    def next_month(self: Any, *args: Any, **kwargs: Any) -> Any:
        original_proof(self, *args, **kwargs)
        return datetime(2090, 1, 1, tzinfo=UTC)

    b = command(s, ident, start_month="2090-01", planned_amount_won="100")
    before = activity(s.db)
    with monkeypatch.context() as m:
        m.setattr(TrainerRoles, "confirm_actor", next_month)
        assert send(s, ident, b).status_code == 409
    assert activity(s.db) == before
    assert read(s, ident).json()["base_ledger_version"] == 1
    with s.db.session() as db:
        assert db.execute(text("SELECT count(*) FROM audit_base_schedule_events")).scalar_one() == 0
    assert send(s, ident, b).status_code == 200
    with monkeypatch.context() as m:
        m.setattr(TrainerRoles, "confirm_actor", next_month)
        assert send(s, ident, b).status_code == 200
    # An audit-free, valid no-op isolates the logical-start FK from Audit FKs.
    change_id = read(s, ident).json()["items"][0]["change_id"]
    noop = command(s, ident, expected_change_revision=1, planned_amount_won="100")
    noop_result = send(s, ident, noop, "/" + change_id + "/edit")
    assert noop_result.status_code == 200 and noop_result.json()["changed"] is False
    with s.db.session() as db:
        start_fk = db.execute(
            text("""SELECT conname FROM pg_constraint
          WHERE conrelid='workforce_base_operations'::regclass AND contype='f'
          AND pg_get_constraintdef(oid) LIKE
            'FOREIGN KEY (organization_id, trainer_id, change_id, start_month)%'""")
        ).scalar_one()
        assert (
            db.execute(
                text("SELECT count(*) FROM audit_base_schedule_events WHERE operation_id=:op"),
                {"op": noop["operation_id"]},
            ).scalar_one()
            == 0
        )
        original_noop = db.execute(
            text("SELECT to_jsonb(o) FROM workforce_base_operations o WHERE operation_id=:op"),
            {"op": noop["operation_id"]},
        ).scalar_one()
        assert not original_noop["changed"] and original_noop["kind"] == "edit"
        with pytest.raises(IntegrityError) as error:
            db.execute(
                text(
                    "UPDATE workforce_base_operations SET start_month='2091-01-01' "
                    "WHERE operation_id=:op"
                ),
                {"op": noop["operation_id"]},
            )
        assert isinstance(error.value.orig, ForeignKeyViolation)
        assert error.value.orig.sqlstate == "23503"
        assert error.value.orig.diag.constraint_name == start_fk
        db.rollback()
        restored = db.execute(
            text("SELECT to_jsonb(o) FROM workforce_base_operations o WHERE operation_id=:op"),
            {"op": noop["operation_id"]},
        ).scalar_one()
        assert restored == original_noop
    # A deferred core mismatch must reach the explicit constraint boundary.
    with s.db.session() as db:
        db.execute(text("UPDATE audit_base_schedule_events SET after_amount=999"))
        with pytest.raises(IntegrityError):
            db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        db.rollback()
    edit = command(s, ident, expected_change_revision=1, planned_amount_won="0")
    assert send(s, ident, edit, "/" + change_id + "/edit").status_code == 200
    # Only before_amount changes: valid edit CHECK and every nonnull core fact stay valid.
    # Both immediate forcing and actual commit reject the separate deferred before FK.
    for boundary in ["immediate", "commit"]:
        with s.db.session() as db:
            before_fk = db.execute(
                text("""SELECT conname FROM pg_constraint
              WHERE conrelid='audit_base_schedule_events'::regclass AND contype='f'
              AND pg_get_constraintdef(oid) LIKE
                'FOREIGN KEY (organization_id, operation_id, before_amount,%'""")
            ).scalar_one()
            original_edit = db.execute(
                text("SELECT to_jsonb(a) FROM audit_base_schedule_events a WHERE operation_id=:op"),
                {"op": edit["operation_id"]},
            ).scalar_one()
            assert original_edit["kind"] == "edit"
            assert original_edit["before_amount"] == 100 and original_edit["after_amount"] == 0
            db.execute(
                text(
                    "UPDATE audit_base_schedule_events SET before_amount=999 WHERE operation_id=:op"
                ),
                {"op": edit["operation_id"]},
            )
            mutated = db.execute(
                text("SELECT to_jsonb(a) FROM audit_base_schedule_events a WHERE operation_id=:op"),
                {"op": edit["operation_id"]},
            ).scalar_one()
            assert mutated == {**original_edit, "before_amount": 999}
            with pytest.raises(IntegrityError) as error:
                if boundary == "immediate":
                    db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
                else:
                    db.commit()
            assert isinstance(error.value.orig, ForeignKeyViolation)
            assert error.value.orig.sqlstate == "23503"
            assert error.value.orig.diag.constraint_name == before_fk
            db.rollback()
            restored = db.execute(
                text("SELECT to_jsonb(a) FROM audit_base_schedule_events a WHERE operation_id=:op"),
                {"op": edit["operation_id"]},
            ).scalar_one()
            assert restored == original_edit
    next_command = command(s, ident, start_month="2091-01", planned_amount_won="2")

    def fail_audit(self: Any, event: Any) -> None:
        raise RuntimeError("synthetic audit rejection")

    with monkeypatch.context() as m:
        m.setattr(Audit, "append_base_schedule", fail_audit)
        assert send(s, ident, next_command).status_code == 500
    assert read(s, ident).json()["base_ledger_version"] == 3


def test_home_authority_receipts_and_independent_axes(scene: Scene, password_app: Any) -> None:
    from contextlib import closing

    from tests.test_iam_trainer import TrainerScene
    from tests.test_workforce_compensation import (
        body as compensation_body,
    )
    from tests.test_workforce_compensation import (
        change as compensation_change,
    )
    from tests.test_workforce_home import body as home_body
    from tests.test_workforce_home import destination, move
    from tests.test_workforce_integrity import branch_actor
    from tests.test_workforce_state import change as state_change
    from tests.test_workforce_state import request as state_request

    s = scene
    ident = register(s)
    t = TrainerScene(s, ident, s.client, "unused", "unused")
    with closing(branch_actor(s, password_app[2])) as ba:
        branch_scene = Scene(ba, s.db, s.branch)
        b = command(branch_scene, ident, start_month="2090-01", planned_amount_won="0")
        assert send(branch_scene, ident, b).status_code == 200
        assert compensation_change(t, compensation_body(t, 50, "7")).status_code == 200
        assert read(s, ident).json()["base_ledger_version"] == 2
        assert state_change(t, state_request(t, False)).status_code == 200
        assert (
            send(
                s, ident, command(s, ident, start_month="2091-01", planned_amount_won="1")
            ).status_code
            == 200
        )
        dest = destination(t)
        assert move(t, home_body(t, dest)).status_code == 200
        assert read(branch_scene, ident).status_code == 404
        assert (
            ba.get(
                "/api/v1/admin/trainers/" + ident + "/base-schedule-history",
                headers=role_headers(ba),
            ).status_code
            == 404
        )
        assert send(branch_scene, ident, b).status_code == 404
        receipt_path = "/api/v1/admin/trainer-base-operations/" + b["operation_id"]
        assert ba.get(receipt_path, headers=role_headers(ba)).status_code == 404
        assert s.client.get(receipt_path, headers=role_headers(s.client)).status_code == 404
    current = read(s, ident).json()
    assert current["base_ledger_version"] == 3 and current["trainer_version"] == 3
    assert current["home_branch_id"] == dest
    with s.db.session() as db:
        assert (
            db.execute(text("SELECT compensation_version FROM workforce_trainers")).scalar_one()
            == 2
        )


@pytest.mark.parametrize("absolute", [False, True])
def test_base_original_auth_deadline_after_audit(
    scene: Scene, monkeypatch: Any, absolute: bool
) -> None:
    from y3management.audit.infrastructure import Audit

    s = scene
    ident = register(s)
    payload = command(s, ident, start_month="2090-01", planned_amount_won="1")
    nonce = csrf(s.client)
    actor = role_headers(s.client)["X-Y3-Expected-Actor"]
    with s.db.session() as db:
        if absolute:
            db.execute(
                text("""WITH shifted AS (UPDATE iam_security_states
             SET expires_at=clock_timestamp()+interval '2 seconds'
             WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a)
             RETURNING id,expires_at)
             UPDATE iam_sessions s SET expires_at=shifted.expires_at,
             created_at=shifted.expires_at-interval '8 hours',
             last_activity=shifted.expires_at-interval '1 minute'
             FROM shifted WHERE s.id=shifted.id"""),
                {"a": actor},
            )
        else:
            db.execute(
                text(
                    "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',"
                    "last_activity=clock_timestamp()-interval '29 minutes 58 seconds' "
                    "WHERE account_id=:a"
                ),
                {"a": actor},
            )
        db.commit()
    original = Audit.append_base_schedule
    observations = []

    def delayed(self: Any, event: Any) -> None:
        original(self, event)
        query = text(
            "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
            "expires_at>clock_timestamp() FROM iam_sessions WHERE account_id=:a"
        )
        observations.append(tuple(self.s.execute(query, {"a": actor}).one()))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        self.s.execute(text("SELECT pg_sleep(1.1)"))
        observations.append(tuple(self.s.execute(query, {"a": actor}).one()))

    monkeypatch.setattr(Audit, "append_base_schedule", delayed)
    r = s.client.post(
        "/api/v1/admin/trainers/" + ident + "/base-schedule/changes",
        headers={**role_headers(s.client), "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=payload,
    )
    assert r.status_code == 401
    assert observations[0] == (True, True) and observations[1][1 if absolute else 0] is False
    with s.db.session() as db:
        assert (
            db.execute(text("SELECT ledger_version FROM workforce_base_ledgers")).scalar_one() == 1
        )
        assert db.execute(text("SELECT count(*) FROM workforce_base_changes")).scalar_one() == 0
        assert db.execute(text("SELECT count(*) FROM workforce_base_operations")).scalar_one() == 0
        assert db.execute(text("SELECT count(*) FROM audit_base_schedule_events")).scalar_one() == 0


@pytest.mark.parametrize("microseconds,expected", [(-1, 200), (0, 409), (1, 409)])
def test_same_actor_proof_clock_korean_month_boundary_fault_injection(
    scene: Scene, monkeypatch: Any, microseconds: int, expected: int
) -> None:
    from datetime import UTC, datetime, timedelta

    from y3management.iam.roles import TrainerRoles

    s = scene
    ident = register(s)
    payload = command(s, ident, start_month="2090-01", planned_amount_won="1")
    actor = role_headers(s.client)["X-Y3-Expected-Actor"]
    clock = datetime(2089, 12, 31, 15, tzinfo=UTC) + timedelta(microseconds=microseconds)
    with s.db.session() as db:
        db.execute(
            text("""WITH shifted AS (UPDATE iam_security_states
          SET expires_at=TIMESTAMPTZ '2089-12-31 16:00:00+00'
          WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a)
          RETURNING id,expires_at)
          UPDATE iam_sessions s SET expires_at=shifted.expires_at,
          created_at=shifted.expires_at-interval '8 hours',
          last_activity=TIMESTAMPTZ '2089-12-31 14:59:00+00'
          FROM shifted WHERE s.id=shifted.id"""),
            {"a": actor},
        )
        db.commit()
    before = activity(s.db)
    original = TrainerRoles.confirm_actor
    returned = []

    def proof(self: Any, *args: Any, **kwargs: Any) -> Any:
        with monkeypatch.context() as m:
            m.setattr(self.iam, "now", lambda: clock)
            result = original(self, *args, **kwargs)
            returned.append(result)
            return result

    monkeypatch.setattr(TrainerRoles, "confirm_actor", proof)
    assert send(s, ident, payload).status_code == expected
    assert returned == [clock]
    with s.db.session() as db:
        pg_month = db.execute(
            text(
                "SELECT date_trunc('month',CAST(:clock AS timestamptz) "
                "AT TIME ZONE 'Asia/Seoul')::date"
            ),
            {"clock": clock},
        ).scalar_one()
        assert str(pg_month) == ("2089-12-01" if microseconds < 0 else "2090-01-01")
        if expected == 200:
            sealed = db.execute(
                text(
                    "SELECT o.validated_at,s.last_activity FROM workforce_base_operations o "
                    "JOIN iam_sessions s ON s.account_id=o.actor_id"
                )
            ).one()
            assert sealed.validated_at == sealed.last_activity == clock
        else:
            assert (
                db.execute(text("SELECT ledger_version FROM workforce_base_ledgers")).scalar_one()
                == 1
            )
            for table in [
                "workforce_base_operations",
                "workforce_base_changes",
                "audit_base_schedule_events",
            ]:
                assert db.execute(text("SELECT count(*) FROM " + table)).scalar_one() == 0
    if expected == 409:
        assert activity(s.db) == before


def test_base_actual_global_gate_serializes_current_cas(
    scene: Scene, password_app: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import closing
    from threading import Event

    from sqlalchemy import event as sa_event

    from tests.test_iam_trainer import TrainerScene
    from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
    from y3management.audit.infrastructure import Audit

    t = TrainerScene(scene, register(scene), scene.client, "unused", "unused")
    payload = command(scene, t.trainer, start_month="2090-01", planned_amount_won="1")
    reached, release = Event(), Event()
    holders = []
    original = Audit.append_base_schedule

    def paused(self: Audit, *args: Any) -> None:
        original(self, *args)
        holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        reached.set()
        assert release.wait(15)

    with closing(branch_actor(t.base, password_app[2])) as ba:
        headers_a = {
            **role_headers(t.base.client),
            "Origin": ORIGIN,
            "X-CSRF-Token": csrf(t.base.client),
        }
        headers_b = {**role_headers(ba), "Origin": ORIGIN, "X-CSRF-Token": csrf(ba)}
        monkeypatch.setattr(Audit, "append_base_schedule", paused)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                t.base.client.post,
                "/api/v1/admin/trainers/" + t.trainer + "/base-schedule/changes",
                headers=headers_a,
                json=payload,
            )
            capture = None
            try:
                assert reached.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(
                    ba.post,
                    "/api/v1/admin/trainers/" + t.trainer + "/base-schedule/changes",
                    headers=headers_b,
                    json={**payload, "operation_id": str(uuid4())},
                )
                wait_for_owned_block(t.base.db, holders[0], waiters)
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            assert first.result(timeout=10).status_code == 200
            assert second.result(timeout=10).status_code == 409
    assert read(scene, t.trainer).json()["base_ledger_version"] == 2
    with scene.db.session() as db:
        assert db.execute(text("SELECT count(*) FROM audit_base_schedule_events")).scalar_one() == 1


@pytest.mark.parametrize("kind", ["master", "branch"])
def test_base_independent_admin_self_scope(scene: Scene, password_app: Any, kind: str) -> None:
    from contextlib import closing

    from tests.password_helpers import login_password
    from tests.test_iam_trainer import TrainerScene
    from tests.test_iam_trainer_roles import change as grant
    from tests.test_iam_trainer_roles_security import link
    from tests.test_workforce_integrity import branch_actor
    from tests.test_workforce_state import change as state_change
    from tests.test_workforce_state import request as state_request

    s = scene
    ident = register(s)
    t = TrainerScene(s, ident, s.client, "unused", "unused")
    if kind == "branch":
        with closing(branch_actor(s, password_app[2])) as ba:
            actor = ba.get("/api/v1/auth/me").json()["account_id"]
            assert grant(t, link(t, actor, "workforce.branch")).status_code == 200
            login_password(ba, password_app[2], "workforce.branch")
            assert state_change(t, state_request(t, False)).status_code == 200
            admin = Scene(ba, s.db, s.branch)
            assert (
                send(
                    admin,
                    ident,
                    command(admin, ident, start_month="2090-01", planned_amount_won="0"),
                ).status_code
                == 200
            )
            assert ba.get("/api/v1/auth/me").status_code == 200
    else:
        actor = s.client.get("/api/v1/auth/me").json()["account_id"]
        assert grant(t, link(t, actor, "master.test")).status_code == 200
        login_password(s.client, password_app[2], "master.test")
        assert state_change(t, state_request(t, False)).status_code == 200
        assert (
            send(
                s, ident, command(s, ident, start_month="2090-01", planned_amount_won="0")
            ).status_code
            == 200
        )
        assert s.client.get("/api/v1/auth/me").status_code == 200


def test_base_pending_source_preservation_and_denied_principals(trainer: TrainerScene) -> None:
    from tests.test_account_lifecycle import lifecycle_fingerprints
    from tests.test_iam_trainer import source
    from tests.test_operator_management import candidate
    from tests.test_operator_management import command as operator_command

    t = trainer
    s = t.base
    token = source(t.issue())
    before = lifecycle_fingerprints(s.db)
    b = command(s, t.trainer, start_month="9999-12", planned_amount_won="9" * 1024)
    saved = send(s, t.trainer, b)
    assert saved.status_code == 200
    after = lifecycle_fingerprints(s.db)
    changed = {
        "iam_sessions",
        "workforce_base_ledgers",
        "workforce_base_changes",
        "workforce_base_operations",
        "audit_base_schedule_events",
    }
    assert {k: v for k, v in before.items() if k not in changed} == {
        k: v for k, v in after.items() if k not in changed
    }
    assert t.complete(token).status_code == 204 and t.signin().status_code == 204
    for expected in [401, 403]:
        c = t.recipient
        headers = role_headers(c)
        for suffix in ["base-schedule?basis_month=9999-12", "base-schedule-history"]:
            assert (
                c.get(
                    "/api/v1/admin/trainers/" + t.trainer + "/" + suffix, headers=headers
                ).status_code
                == expected
            )
        assert (
            c.get(
                "/api/v1/admin/trainer-base-operations/" + b["operation_id"], headers=headers
            ).status_code
            == expected
        )
        assert send(Scene(c, s.db, s.branch), t.trainer, b).status_code == expected
        if expected == 401:
            assert operator_command(t, candidate(t, t.login).json()).status_code == 200
            assert t.signin().status_code == 204
    path = "/api/v1/admin/trainers/" + t.trainer + "/base-schedule?basis_month=9999-12"
    assert s.client.get(path, headers={"X-Y3-Expected-Actor": str(uuid4())}).status_code == 409
    foreign_org, foreign_branch, foreign_trainer = uuid4(), uuid4(), uuid4()
    with s.db.session() as db:
        db.execute(
            text("INSERT INTO organization_organizations(id,name) VALUES(:o,'가상 외부')"),
            {"o": foreign_org},
        )
        db.execute(
            text(
                "INSERT INTO organization_branches(id,organization_id,code,name) "
                "VALUES(:b,:o,'FOREIGNBASE','가상 외부')"
            ),
            {"b": foreign_branch, "o": foreign_org},
        )
        db.execute(
            text("""INSERT INTO workforce_trainers(id,organization_id,home_branch_id,
          name,phone,active,row_version,rate_percent,fixed_amount_won,base_salary_won,
          base_salary_start_month) VALUES(:i,:o,:b,'가상','가상',true,1,0,0,0,'2026-01-01')"""),
            {"i": foreign_trainer, "o": foreign_org, "b": foreign_branch},
        )
        db.commit()
    for suffix in ["base-schedule?basis_month=9999-12", "base-schedule-history"]:
        assert (
            s.client.get(
                "/api/v1/admin/trainers/" + str(foreign_trainer) + "/" + suffix,
                headers=role_headers(s.client),
            ).status_code
            == 404
        )
    assert send(s, str(foreign_trainer), b).status_code == 404
