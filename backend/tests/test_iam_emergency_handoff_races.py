# ruff: noqa: F811
"""Final authorization, actual crypto barriers and atomic failures."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier
from threading import Event as Signal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import (  # noqa: F401
    activate,
    call,
    link_token,
    login_password,
    password_app,
)
from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_emergency import facts
from tests.test_iam_emergency_handoff import Scene, fingerprint, scene  # noqa: F401
from y3management.audit.infrastructure import Audit
from y3management.audit.public import PasswordEmergencyEvent as Event
from y3management.contracts import Rejected
from y3management.iam.emergency import Emergency
from y3management.iam.public import EmergencyPasswordProof, EmergencySnapshot, HandoffRequest

pytestmark = pytest.mark.postgres


def test_audit_delay_cannot_rescue_idle_actor(
    scene: Scene, monkeypatch: pytest.MonkeyPatch
) -> None:
    scene.operating()
    body = scene.body()
    nonce = csrf(scene.actor)
    with scene.db.session() as db:
        db.execute(
            text(
                "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',"
                "last_activity=clock_timestamp()"
                "-interval '29 minutes 58 seconds' "
                "WHERE account_id=:a"
            ),
            {"a": scene.actor_id},
        )
        db.commit()
    before = fingerprint(scene)
    original = Audit.append_password_emergency
    reached = []

    def delayed(adapter: Audit, event: Event) -> None:
        original(adapter, event)
        if event.action == "handoff":
            reached.append(True)
            adapter.s.execute(text("SELECT pg_sleep(1.1)"))
            adapter.s.execute(text("SELECT pg_sleep(1.1)"))

    monkeypatch.setattr(Audit, "append_password_emergency", delayed)
    assert scene.send(body, nonce).status_code == 401
    assert reached == [True]
    assert fingerprint(scene) == before


def test_audit_failure_rolls_back_all_business_effects(
    scene: Scene, monkeypatch: pytest.MonkeyPatch
) -> None:
    scene.operating()
    body = scene.body()
    nonce = csrf(scene.actor)
    before = fingerprint(scene)
    original = Audit.append_password_emergency

    def fail(adapter: Audit, event: Event) -> None:
        original(adapter, event)
        if event.action == "handoff":
            raise Rejected(503, "unavailable")

    monkeypatch.setattr(Audit, "append_password_emergency", fail)
    assert scene.send(body, nonce).status_code == 503
    assert fingerprint(scene) == before


def test_concurrent_same_parent_only_one_child(scene: Scene) -> None:
    with closing(TestClient(scene.actor.app, base_url=ORIGIN)) as third:
        created = call(
            scene.actor, "/admin/master-accounts", csrf(scene.actor), {"login_id": "third.master"}
        )
        assert created.status_code == 201

        activate(third, link_token(created.json()["setup_link"]), scene.password)
        login_password(third, scene.password, "third.master")
        actors = [scene.actor_id, str(created.json()["account_id"])]
        assert actors[0] != actors[1]
        scene.operating()
        bodies = [scene.body(), scene.body()]
        credentials = [
            (
                SyntheticSecret(client.cookies.get("__Host-y3-auth") or ""),
                SyntheticSecret(csrf(client)),
            )
            for client in (scene.actor, third)
        ]
        with scene.db.session() as db:
            activity: dict[UUID, object] = {
                row[0]: row[1]
                for row in db.execute(
                    text(
                        "SELECT account_id,last_activity FROM iam_sessions "
                        "WHERE account_id IN (:b,:c)"
                    ),
                    {"b": actors[0], "c": actors[1]},
                ).all()
            }
        barrier = Barrier(2)

        def worker(index: int) -> int:
            body = bodies[index]
            auth, nonce = credentials[index]
            barrier.wait(timeout=10)
            try:
                scene.service.handoff(
                    auth,
                    nonce,
                    scene.ident,
                    HandoffRequest(
                        UUID(body["operation_id"]),
                        UUID(body["supersedes_case_id"]),
                        EmergencySnapshot(**body["expected"]),
                    ),
                    True,
                )
                return 201
            except Rejected as error:
                return error.status

        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(worker, index) for index in range(2)]
            results = [job.result(timeout=20) for job in jobs]
        assert sorted(results) == [201, 409]
        winner, loser = actors[results.index(201)], actors[results.index(409)]
        with scene.db.session() as db:
            assert (
                db.execute(
                    text("SELECT count(*) FROM iam_password_emergency_cases WHERE kind='handoff'")
                ).scalar_one()
                == 1
            )
            assert (
                db.execute(
                    text(
                        "SELECT count(*) FROM iam_password_emergency_credentials e "
                        "JOIN iam_password_emergency_cases c ON c.id=e.case_id "
                        "WHERE c.kind='handoff'"
                    )
                ).scalar_one()
                == 1
            )
            assert db.execute(
                text("SELECT actor_id FROM audit_password_emergency_events WHERE action='handoff'")
            ).scalar_one() == UUID(winner)
            assert (
                db.execute(
                    text("SELECT last_activity FROM iam_sessions WHERE account_id=:a"), {"a": loser}
                ).scalar_one()
                == activity[UUID(loser)]
            )


def test_password_proof_loses_to_reissue(scene: Scene, monkeypatch: pytest.MonkeyPatch) -> None:
    scene.operating()
    issued = scene.send(scene.body())
    assert issued.status_code == 201
    raw = link_token(issued.json()["recipient_link"])
    nonce = csrf(scene.target)
    verified, proceed = Signal(), Signal()
    original = Emergency.prepare_password

    def paused(adapter: Emergency, token: str, password: str) -> EmergencyPasswordProof:
        proof = original(adapter, token, password)
        verified.set()
        assert proceed.wait(timeout=15)
        return proof

    monkeypatch.setattr(Emergency, "prepare_password", paused)
    with ThreadPoolExecutor(max_workers=1) as pool:
        job = pool.submit(
            call,
            scene.target,
            "/auth/emergency-recovery/password/complete",
            nonce,
            {"emergency_token": raw, "new_password": scene.password},
        )
        try:
            assert verified.wait(timeout=10)
            assert scene.send(scene.body()).status_code == 201
            before = facts(scene.db)
        finally:
            proceed.set()
        assert job.result(timeout=15).status_code == 401
    assert facts(scene.db) == before
    assert (
        before["password_reset_pending"] and not before["recovery_pending"] and not before["ready"]
    )


def test_db_lease_expiry_after_audit_rolls_back(
    scene: Scene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    import y3management.use_cases as application
    from y3management.iam.security import Security

    scene.operating()
    body = scene.body()
    nonce = csrf(scene.actor)
    before = fingerprint(scene)
    allocate = Security.allocate
    append = Audit.append_password_emergency
    reached = []

    # An application clock behind DB must never govern authorization/lease validity.
    monkeypatch.setattr(
        application,
        "datetime",
        SimpleNamespace(now=lambda *args: datetime.now(UTC) - timedelta(hours=1)),
        raising=False,
    )

    def short(adapter: Security, kind: str, *, collect: bool = True) -> UUID:
        slot = allocate(adapter, kind, collect=collect)
        if kind == "emergency":
            adapter.s.execute(
                text(
                    "UPDATE iam_security_states SET expires_at="
                    "clock_timestamp()+interval '1 second' WHERE id=:i"
                ),
                {"i": slot},
            )
        return slot

    def delay(adapter: Audit, event: Event) -> None:
        append(adapter, event)
        if event.action == "handoff":
            reached.append(True)
            adapter.s.execute(text("SELECT pg_sleep(1.2)"))

    monkeypatch.setattr(Security, "allocate", short)
    monkeypatch.setattr(Audit, "append_password_emergency", delay)
    response = scene.send(body, nonce)
    assert response.status_code in (401, 409)
    assert "recipient_link" not in response.json()
    assert reached == [True]
    assert fingerprint(scene) == before
    assert scene.actor.get("/api/v1/auth/me").status_code == 200
