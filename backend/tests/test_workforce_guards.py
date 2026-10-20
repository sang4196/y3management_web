# ruff: noqa: F811
"""Persisted failure boundaries, actual Home authority and late authentication."""

import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_workforce import Scene, activity, counts, scene  # noqa: F401
from tests.test_workforce_integrity import (
    branch_actor,
    late_audit_proof,
    observe_waiter,
    wait_for_owned_block,
)
from y3management.audit.infrastructure import Audit
from y3management.audit.public import InitialCompensationSet
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_each_persisted_step_failure(scene: Scene) -> None:
    """Owned fixture triggers throw actual database errors at each write boundary."""
    stages = [
        ("workforce_trainers", "true"),
        ("workforce_initial_snapshots", "true"),
        ("workforce_registration_operations", "true"),
        ("audit_workforce_initial_events", "NEW.event_kind='trainer_registered'"),
        ("audit_workforce_initial_events", "NEW.event_kind='initial_compensation'"),
    ]
    for table, condition in stages:
        with scene.db.session() as s:
            s.execute(
                text(
                    "CREATE OR REPLACE FUNCTION wf_test_failure() RETURNS trigger LANGUAGE "
                    "plpgsql AS $$ BEGIN IF "
                    + condition
                    + " THEN RAISE EXCEPTION 'synthetic persisted failure'; "
                    "END IF; RETURN NEW; END $$"
                )
            )
            s.execute(
                text(
                    "CREATE TRIGGER wf_test_failure BEFORE INSERT ON "
                    + table
                    + " FOR EACH ROW EXECUTE FUNCTION wf_test_failure()"
                )
            )
            s.commit()
        before = activity(scene.db)
        assert scene.send(scene.body()).status_code == 503
        assert counts(scene.db) == (0, 0, 0, 0) and activity(scene.db) == before
        with scene.db.session() as s:
            s.execute(text("DROP TRIGGER wf_test_failure ON " + table))
            s.commit()


def history(db: Database) -> list[Any]:
    with db.session() as s:
        return [
            s.execute(text("SELECT * FROM " + table + " ORDER BY 1")).all()
            for table in [
                "workforce_initial_snapshots",
                "workforce_registration_operations",
                "audit_workforce_initial_events",
            ]
        ]


def test_exact_all_stores_and_typed_constraints(scene: Scene) -> None:
    body = scene.body()
    body["fixed_amount_won"] = "9007199254740993"
    assert scene.send(body).status_code == 201
    with scene.db.session() as s:
        for table, cols, where in [
            ("workforce_trainers", "fixed_amount_won,base_salary_won", ""),
            ("workforce_initial_snapshots", "fixed_amount_won,base_salary_won", ""),
            (
                "audit_workforce_initial_events",
                "after_fixed,after_base",
                " WHERE event_kind='initial_compensation'",
            ),
        ]:
            row = s.execute(text("SELECT " + cols + " FROM " + table + where)).one()
            assert tuple(str(v) for v in row) == (body["fixed_amount_won"], body["base_salary_won"])
    original = history(scene.db)
    assert scene.send(body).status_code == 200
    assert history(scene.db) == original
    statements = [
        "UPDATE workforce_trainers SET home_branch_id=:missing",
        "UPDATE workforce_initial_snapshots SET organization_id=:missing",
        "UPDATE workforce_registration_operations SET creator_account_id=:missing",
        "UPDATE workforce_trainers SET base_salary_start_month=DATE '0001-01-02'",
        "UPDATE workforce_trainers SET base_salary_start_month=DATE '10000-01-01'",
        "UPDATE workforce_trainers SET base_salary_start_month='infinity'::date",
        "UPDATE workforce_trainers SET rate_percent=101",
        "UPDATE workforce_initial_snapshots SET base_salary_won=NULL",
        "UPDATE audit_workforce_initial_events SET after_fixed=NULL WHERE "
        "event_kind='initial_compensation'",
        "UPDATE audit_workforce_initial_events SET after_fixed=0 WHERE "
        "event_kind='trainer_registered'",
        "UPDATE audit_workforce_initial_events SET before_rate=0",
        "UPDATE audit_workforce_initial_events SET actor_id=:missing",
        "UPDATE audit_workforce_initial_events SET after_base='NaN'::numeric "
        "WHERE event_kind='initial_compensation'",
    ]
    for statement in statements:
        with scene.db.session() as s:
            with pytest.raises(IntegrityError):
                s.execute(text(statement), {"missing": uuid4()})
            s.rollback()
    assert history(scene.db) == original


def test_exact_body_budget_valid_json(scene: Scene) -> None:
    body = scene.body()
    nonce = csrf(scene.client)
    payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()
    padded = payload + b" " * (8192 - len(payload))
    headers = {"Origin": ORIGIN, "Content-Type": "application/json", "X-CSRF-Token": nonce}
    assert len(padded) == 8192
    assert (
        scene.client.post("/api/v1/admin/trainers", content=padded, headers=headers).status_code
        == 201
    )
    before = activity(scene.db)
    assert (
        scene.client.post(
            "/api/v1/admin/trainers", content=padded + b" ", headers=headers
        ).status_code
        == 413
    )
    assert activity(scene.db) == before and counts(scene.db) == (1, 1, 1, 2)


def test_actual_home_reauthorization(
    scene: Scene, mfa: tuple[Settings, Database, str, str]
) -> None:
    with closing(branch_actor(scene, mfa[2])) as other:
        body = scene.body()
        result = scene.send(body).json()
        ident = result["trainer"]["id"]
        original = history(scene.db)
        foreign = call(
            scene.client,
            "/admin/branches",
            csrf(scene.client),
            {"code": "MOVED", "name": "가상다른지점"},
        ).json()["id"]
        # Controlled fact change is not an implemented Home-movement use case.
        with scene.db.session() as s:
            s.execute(
                text("UPDATE workforce_trainers SET home_branch_id=:b,row_version=2 WHERE id=:i"),
                {"b": foreign, "i": ident},
            )
            s.commit()
        assert other.get("/api/v1/admin/trainers/" + ident).status_code == 404
        assert (
            other.get("/api/v1/admin/trainer-registrations/" + body["operation_id"]).status_code
            == 404
        )
        assert other.get("/api/v1/admin/trainers").json()["total"] == 0
        assert call(other, "/admin/trainers", csrf(other), body).status_code == 404
        assert scene.send(body).status_code == 200
        assert history(scene.db) == original


def test_late_absolute_only(scene: Scene, monkeypatch: pytest.MonkeyPatch) -> None:
    nonce = csrf(scene.client)
    with scene.db.session() as s:
        s.execute(
            text("""WITH shifted AS (UPDATE iam_security_states
          SET expires_at=clock_timestamp()+interval '1.5 seconds'
          WHERE id IN (SELECT id FROM iam_sessions) RETURNING id,expires_at)
          UPDATE iam_sessions s SET expires_at=shifted.expires_at,
          created_at=shifted.expires_at-interval '8 hours',
          last_activity=shifted.expires_at-interval '1 minute'
          FROM shifted WHERE s.id=shifted.id""")
        )
        s.commit()
    before = activity(scene.db)
    observed: dict[str, bool] = {}
    original = Audit.append_initial_compensation

    def delayed(self: Audit, event: InitialCompensationSet) -> None:
        original(self, event)
        late_audit_proof(self, True, observed)

    monkeypatch.setattr(Audit, "append_initial_compensation", delayed)
    assert call(scene.client, "/admin/trainers", nonce, scene.body()).status_code == 401
    assert observed == {"reached": True, "writes": True, "only_selected_deadline_expired": True}
    assert activity(scene.db) == before and counts(scene.db) == (0, 0, 0, 0)


@pytest.mark.parametrize("registration_first", [True, False])
def test_actor_revocation_order(
    scene: Scene, monkeypatch: pytest.MonkeyPatch, registration_first: bool
) -> None:
    nonce = csrf(scene.client)
    body = scene.body()
    reached, release = Event(), Event()
    holder: list[int] = []
    from sqlalchemy import event as sa_event

    original = Audit.append_initial_compensation

    def delayed(self: Audit, event: InitialCompensationSet) -> None:
        original(self, event)
        holder.append(int(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
        reached.set()
        assert release.wait(5)

    if registration_first:
        monkeypatch.setattr(Audit, "append_initial_compensation", delayed)

    def revoke() -> None:
        with scene.db.session() as s:
            # Same account lock as current IAM mutation; raw fixture only supplies competing fact.
            s.execute(
                text(
                    "UPDATE iam_accounts SET "
                    "state='DISABLED',security_version=security_version+1 WHERE "
                    "login_id='master.test'"
                )
            )
            if not registration_first:
                holder.append(int(s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
                reached.set()
                assert release.wait(5)
            s.commit()

    def register() -> int:
        return int(call(scene.client, "/admin/trainers", nonce, body).status_code)

    before = activity(scene.db)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(register if registration_first else revoke)
        capture = None
        try:
            assert reached.wait(5)
            waiters: list[int] = []
            capture = observe_waiter(scene.db, waiters)
            second = pool.submit(revoke if registration_first else register)
            wait_for_owned_block(scene.db, holder[0], waiters)
            assert not second.done()
        finally:
            release.set()
            if capture is not None:
                sa_event.remove(scene.db.engine, "before_cursor_execute", capture)
        a, b = first.result(timeout=10), second.result(timeout=10)
    assert (a if registration_first else b) == (201 if registration_first else 401)
    assert counts(scene.db) == ((1, 1, 1, 2) if registration_first else (0, 0, 0, 0))
    if not registration_first:
        assert activity(scene.db) == before


def test_c2_other_accounts_and_sources_preserved(
    scene: Scene, mfa: tuple[Settings, Database, str, str]
) -> None:
    import hashlib

    with closing(branch_actor(scene, mfa[2])):
        from fastapi.testclient import TestClient

        with closing(TestClient(scene.client.app, base_url=ORIGIN)) as unknown:
            assert (
                call(
                    unknown,
                    "/auth/login",
                    csrf(unknown),
                    {"login_id": "unknown.workforce", "password": "fictional failed login input"},
                ).status_code
                == 401
            )
        nonce = csrf(scene.client)
        digest = hashlib.sha256(scene.client.cookies["__Host-y3-auth"].encode()).digest()

        def preserved() -> list[str]:
            values = []
            with scene.db.session() as s:
                for table in [
                    "iam_accounts",
                    "iam_admin_grants",
                    "iam_passkeys",
                    "iam_budgets",
                    "iam_attempts",
                    "iam_security_states",
                ]:
                    values.append(
                        str(
                            s.execute(
                                text(
                                    "SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                                    "ORDER BY row_to_json(t)::text),'')) FROM " + table + " t"
                                )
                            ).scalar_one()
                        )
                    )
                values.append(
                    str(
                        s.execute(
                            text(
                                "SELECT md5(COALESCE(string_agg((CASE WHEN digest=:d THEN "
                                "to_jsonb(t)-'last_activity' ELSE to_jsonb(t) END)::text,',' "
                                "ORDER BY id),'')) FROM iam_sessions t"
                            ),
                            {"d": digest},
                        ).scalar_one()
                    )
                )
            return values

        before = preserved()
        assert call(scene.client, "/admin/trainers", nonce, scene.body()).status_code == 201
        assert preserved() == before
