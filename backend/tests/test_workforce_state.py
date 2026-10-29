# ruff: noqa: F811
"""W1 actual commands preserve independent identity and atomic state facts."""

from contextlib import closing
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body as role_body
from tests.test_iam_trainer_roles import change as role_change
from tests.test_workforce import scene  # noqa: F401
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerStateEvent
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres


def request(t: TrainerScene, active: bool) -> dict[str, Any]:
    r = t.base.client.get("/api/v1/admin/trainers/" + t.trainer)
    assert r.status_code == 200
    return dict(
        operation_id=str(uuid4()),
        desired_active=active,
        expected_trainer_version=r.json()["version"],
    )


def change(t: TrainerScene, body: dict[str, Any]) -> Any:
    return call(t.base.client, "/admin/trainers/" + t.trainer + "/state", csrf(t.base.client), body)


def facts(t: TrainerScene) -> tuple[Any, ...]:
    with t.base.db.session() as s:
        return tuple(
            s.execute(text("SELECT * FROM " + table + " ORDER BY 1")).all()
            for table in (
                "iam_accounts",
                "iam_trainer_bindings",
                "iam_trainer_role_grants",
                "iam_trainer_setup_credentials",
                "workforce_initial_snapshots",
            )
        )


def test_pending_source_paused_then_original_reused(trainer: TrainerScene) -> None:
    t = trainer
    token = source(t.issue())
    original = facts(t)
    assert change(t, request(t, False)).status_code == 200
    assert facts(t) == original
    assert t.complete(token).status_code == 400
    assert facts(t) == original
    assert change(t, request(t, True)).status_code == 200
    assert facts(t) == original
    assert t.complete(token).status_code == 204
    assert t.signin().status_code == 204


def test_old_cookies_never_revive_replay_preserves_new_login(trainer: TrainerScene) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    original = facts(t)
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as second:
        assert t.signin(second).status_code == 204
        off = request(t, False)
        result = change(t, off)
        assert result.status_code == 200
        assert result.json()["committed_trainer_version"] == off["expected_trainer_version"] + 1
        assert t.signin().status_code == 401
        assert change(t, request(t, True)).status_code == 200
        assert second.get("/api/v1/auth/me").status_code == 401
        assert t.signin().status_code == 204
        assert change(t, off).json()["current_state"]["active"] is True
        assert change(t, request(t, True)).json()["changed"] is False
        assert t.recipient.get("/api/v1/auth/me").status_code == 200
        assert facts(t) == original
    with t.base.db.session() as s:
        for table in ("audit_trainer_state_events", "workforce_trainer_state_transitions"):
            assert s.execute(text("SELECT count(*) FROM " + table)).scalar_one() == 2


def test_unbound_inactive_home_and_receipt_conflicts(trainer: TrainerScene) -> None:
    t = trainer
    with t.base.db.session() as s:
        s.execute(
            text("UPDATE organization_branches SET active=false WHERE id=:b"), {"b": t.base.branch}
        )
        s.commit()
    off = request(t, False)
    assert change(t, off).status_code == 200
    assert t.state()["account_id"] is None
    assert change(t, {**off, "operation_id": str(uuid4())}).status_code == 409
    assert change(t, {**off, "desired_active": True}).status_code == 409
    result = t.base.client.get("/api/v1/admin/trainer-state-operations/" + off["operation_id"])
    assert result.status_code == 200
    assert result.json()["committed_active"] is False
    assert change(t, request(t, True)).status_code == 200
    with t.base.db.session() as s:
        origin = s.execute(
            text("SELECT origin,active,trainer_version FROM workforce_trainer_state_origins")
        ).one()
        assert tuple(origin) == ("registered", True, 1)
        assert (
            s.execute(
                text("SELECT account_id FROM audit_trainer_state_events LIMIT 1")
            ).scalar_one()
            is None
        )


def test_grant_and_disabled_independent_blockers(trainer: TrainerScene) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert role_change(t, role_body(t, False)).status_code == 200
    original = facts(t)
    assert change(t, request(t, False)).status_code == 200
    assert change(t, request(t, True)).status_code == 200
    assert facts(t) == original
    ident = t.state()["account_id"]
    with t.base.db.session() as s:
        s.execute(text("UPDATE iam_accounts SET state='DISABLED' WHERE id=:a"), {"a": ident})
        s.commit()
    original = facts(t)
    assert change(t, request(t, False)).status_code == 200
    assert change(t, request(t, True)).status_code == 200
    assert facts(t) == original
    assert t.state()["state"] == "DISABLED"


def test_audit_failure_rolls_back_state_session_receipt(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    off = request(t, False)

    def fail(self: Audit, event: TrainerStateEvent) -> None:
        raise Rejected(503, "unavailable")

    monkeypatch.setattr(Audit, "append_trainer_state", fail)
    assert change(t, off).status_code == 503
    assert t.recipient.get("/api/v1/auth/me").status_code == 200
    assert request(t, False)["expected_trainer_version"] == off["expected_trainer_version"]
    assert (
        t.base.client.get(
            "/api/v1/admin/trainer-state-operations/" + off["operation_id"]
        ).status_code
        == 404
    )
    with t.base.db.session() as s:
        assert (
            s.execute(text("SELECT count(*) FROM workforce_trainer_state_transitions")).scalar_one()
            == 0
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("desired_active", 1),
        ("expected_trainer_version", True),
        ("expected_trainer_version", 0),
        ("unknown", "secret"),
    ],
)
def test_strict_state_input(trainer: TrainerScene, field: str, value: Any) -> None:
    assert change(trainer, {**request(trainer, False), field: value}).status_code == 422
