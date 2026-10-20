# ruff: noqa: F811
"""Actual MFA registration, G1 reads, exact values and transactional failures."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


@dataclass
class Scene:
    client: TestClient
    db: Database
    branch: str

    def body(self) -> dict[str, Any]:
        return dict(
            operation_id=str(uuid4()),
            name="가상 트레이너",
            phone="+99 (000) example",
            home_branch_id=self.branch,
            rate_percent=0,
            fixed_amount_won="0",
            base_salary_won="9" * 1024,
            base_salary_start_month="9999-12",
        )

    def send(self, body: dict[str, Any]) -> Any:
        return call(self.client, "/admin/trainers", csrf(self.client), body)


@pytest.fixture
def scene(mfa: tuple[Settings, Database, str, str]) -> Iterator[Scene]:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        login_mfa(client, password, key)
        b = call(client, "/admin/branches", csrf(client), {"code": "W0", "name": "가상지점"})
        assert b.status_code == 201
        yield Scene(client, db, str(b.json()["id"]))


def counts(db: Database) -> tuple[int, ...]:
    with db.session() as s:
        return tuple(
            int(s.execute(text("SELECT count(*) FROM " + t)).scalar_one())
            for t in [
                "workforce_trainers",
                "workforce_initial_snapshots",
                "workforce_registration_operations",
                "audit_workforce_initial_events",
            ]
        )


def activity(db: Database) -> Any:
    with db.session() as s:
        return s.execute(text("SELECT id,last_activity FROM iam_sessions ORDER BY id")).all()


def test_exact_registration_inactive_g1_and_replay(scene: Scene) -> None:
    c, db = scene.client, scene.db
    body = scene.body()
    r = scene.send(body)
    assert r.status_code == 201
    ident = r.json()["trainer"]["id"]
    assert set(r.json()["trainer"]) == {"id", "name", "home_branch_id", "active", "version"}
    with db.session() as s:
        row = s.execute(
            text(
                "SELECT fixed_amount_won,base_salary_won,base_salary_start_month "
                "FROM workforce_trainers"
            )
        ).one()
        assert (
            str(row[0]) == "0"
            and str(row[1]) == body["base_salary_won"]
            and str(row[2]) == "9999-12-01"
        )
        s.execute(
            text(
                "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                "WHERE id=:i"
            ),
            {"i": scene.branch},
        )
        s.commit()
    before = activity(db)
    for path in [
        "/admin/trainers/" + ident,
        "/admin/trainers",
        "/admin/trainer-registrations/" + body["operation_id"],
    ]:
        response = c.get("/api/v1" + path)
        assert response.status_code == 200
        assert "base_salary" not in response.text and "phone" not in response.text
    assert activity(db) == before
    assert c.get("/api/v1/admin/trainer-home-candidates").json() == {"items": []}
    assert scene.send(body).status_code == 200
    before = activity(db)
    assert scene.send({**body, "name": "다른값"}).status_code == 409
    assert activity(db) == before
    assert scene.send(scene.body()).status_code == 409
    assert counts(db) == (1, 1, 1, 2)


@pytest.mark.parametrize(
    "bad",
    [
        {"rate_percent": True},
        {"phone": None},
        {"fixed_amount_won": "secret-invalid.25"},
        {"extra": "sensitive-marker"},
        {"base_salary_start_month": "0000-01"},
    ],
)
def test_validation_sanitized(scene: Scene, bad: dict[str, Any]) -> None:
    r = scene.send({**scene.body(), **bad})
    assert r.status_code == 422 and r.json() == {"detail": "invalid_request"}
    assert counts(scene.db) == (0, 0, 0, 0)


@pytest.mark.parametrize("method", ["append_trainer_registered", "append_initial_compensation"])
def test_audit_failure_rolls_everything_back(
    scene: Scene, monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    from y3management.contracts import Rejected

    def fail(*args: Any) -> None:
        raise Rejected(503, "unavailable")

    monkeypatch.setattr(Audit, method, fail)
    before = activity(scene.db)
    assert scene.send(scene.body()).status_code == 503
    assert counts(scene.db) == (0, 0, 0, 0) and activity(scene.db) == before


def test_same_phone_distinct_operations(scene: Scene) -> None:
    assert scene.send(scene.body()).status_code == 201
    assert scene.send(scene.body()).status_code == 201
    assert counts(scene.db) == (2, 2, 2, 4)


def test_transport_and_csrf(scene: Scene) -> None:
    c = scene.client
    body = scene.body()
    nonce = csrf(c)
    r = c.post(
        "/api/v1/admin/trainers",
        content=b" " * 8193,
        headers={"Origin": ORIGIN, "Content-Type": "application/json", "X-CSRF-Token": nonce},
    )
    assert r.status_code == 413 and r.json() == {"detail": "invalid_request"}
    assert call(c, "/admin/trainers", "wrong", body).status_code == 403
    assert counts(scene.db) == (0, 0, 0, 0)
