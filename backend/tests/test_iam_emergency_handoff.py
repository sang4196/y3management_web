# ruff: noqa: F811
"""Real normal MFA authority continuing durable emergency cases."""

import json
import secrets
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import (  # noqa: F401
    activate,
    call,
    link_token,
    login_password,
    password_app,
    protect,
    provision,
)
from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_emergency import issue, operator, request
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.public import EmergencyRequest, OperatingRecoveryAuthority
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


@dataclass(repr=False)
class Scene:
    db: Database
    target: TestClient
    actor: TestClient
    service: Service
    principal: OperatingRecoveryAuthority
    ident: UUID
    actor_id: str
    password: str

    @property
    def route(self) -> str:
        return f"/admin/master-accounts/{self.ident}/emergency-recovery"

    def operating(self, *, expire: bool = True) -> EmergencyRequest:
        req = request(self.service, self.principal, self.ident)
        issue(self.service, self.principal, req)
        if expire:
            expire_case(self.db, req.operation_id)
        return req

    def state(self, operation: UUID | None = None) -> dict[str, Any]:
        suffix = "/" + str(operation) if operation else ""
        response = self.actor.get("/api/v1" + self.route + suffix)
        assert response.status_code == 200
        return dict(response.json())

    def body(self) -> dict[str, Any]:
        state = self.state()
        return {
            "operation_id": str(uuid4()),
            "supersedes_case_id": state["operation_id"],
            "expected": state["snapshot"],
            "identity_confirmed": True,
        }

    def send(self, body: dict[str, Any], nonce: str | None = None) -> Any:
        return call(
            self.actor, self.route + "/handoff", csrf(self.actor) if nonce is None else nonce, body
        )


def expire_case(db: Database, operation: UUID) -> None:
    # One statement shifts all three bound expiries; every FK is still enforced.
    with db.session() as session:
        session.execute(
            text("""WITH c AS (
          UPDATE iam_password_emergency_cases SET issued_at=issued_at-interval '31 minutes',
          checked_at=checked_at-interval '31 minutes',expires_at=expires_at-interval '31 minutes'
          WHERE id=:i RETURNING id,expires_at), a AS (
          UPDATE iam_security_states s SET expires_at=c.expires_at
          FROM iam_password_emergency_credentials e JOIN c ON c.id=e.case_id
          WHERE s.id=e.id RETURNING s.id,s.expires_at)
          UPDATE iam_password_emergency_credentials e SET expires_at=a.expires_at
          FROM a WHERE e.id=a.id"""),
            {"i": operation},
        )
        session.commit()


@pytest.fixture
def scene(password_app: tuple[Settings, Database, str], tmp_path: Path) -> Iterator[Scene]:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as target:
        login_password(target, password)
        with closing(TestClient(target.app, base_url=ORIGIN)) as actor:
            actor_id = provision(target, actor, password)
            service, principal, ident = operator(settings, db, tmp_path / "operator")
            yield Scene(db, target, actor, service, principal, ident, actor_id, password)


def complete(s: Scene, raw: str) -> str:
    password = SyntheticSecret("Handoff password " + secrets.token_urlsafe(24))
    response = call(
        s.target,
        "/auth/emergency-recovery/password/complete",
        csrf(s.target),
        {"emergency_token": raw, "new_password": password},
    )
    assert response.status_code == 204
    return password


def test_handoff_real_completion_and_immutable_origin(scene: Scene) -> None:
    original = scene.operating()
    with scene.db.session() as db:
        before = db.execute(
            text(
                "SELECT md5(row_to_json(c)::text) FROM iam_password_emergency_cases c WHERE id=:i"
            ),
            {"i": original.operation_id},
        ).scalar_one()
    body = scene.body()
    response = scene.send(body)
    assert response.status_code == 201
    raw = link_token(response.json()["recipient_link"])
    state = scene.state()
    assert state["issuer_kind"] == "handoff"
    assert state["approval_origin_case_id"] == str(original.operation_id)
    password = complete(scene, raw)
    assert scene.target.get("/api/v1/auth/me").status_code == 401
    login_password(scene.target, password)
    assert scene.state()["status"] == "completed"
    with scene.db.session() as db:
        assert (
            db.execute(
                text(
                    "SELECT md5(row_to_json(c)::text) "
                    "FROM iam_password_emergency_cases c WHERE id=:i"
                ),
                {"i": original.operation_id},
            ).scalar_one()
            == before
        )
        audit = db.execute(
            text(
                "SELECT action,actor_id,actor_role,approval_mode "
                "FROM audit_password_emergency_events WHERE case_id=:i ORDER BY action"
            ),
            {"i": body["operation_id"]},
        ).all()
        assert [(a.action, a.actor_role, a.approval_mode) for a in audit] == [
            ("complete", "RECOVERY_RECIPIENT", "current_master"),
            ("handoff", "MASTER", "current_master"),
        ]
        assert str(audit[1].actor_id) == scene.actor_id
        assert audit[0].actor_id == scene.ident


def test_expired_source_gc_then_live_explicit_reissue(scene: Scene) -> None:
    original = scene.operating()
    with scene.service.uow.open() as w:
        slot = w.security.allocate("credential")
        w.security.release(slot)
    with scene.db.session() as db:
        assert not db.execute(
            text("SELECT 1 FROM iam_password_emergency_credentials WHERE case_id=:i"),
            {"i": original.operation_id},
        ).first()
    first_body = scene.body()
    first = scene.send(first_body)
    assert first.status_code == 201
    token = link_token(first.json()["recipient_link"])
    with scene.service.uow.open() as work:
        proof = work.emergency.prepare_password(token, scene.password)
    second_body = scene.body()
    second = scene.send(second_body)
    assert second.status_code == 201
    assert scene.state()["approval_origin_case_id"] == str(original.operation_id)
    assert scene.state(UUID(first_body["operation_id"]))["status"] == "superseded"
    assert scene.send(first_body).status_code == 409
    from y3management.contracts import Rejected

    with pytest.raises(Rejected) as stale, scene.service.uow.open() as work:
        work.emergency.complete_password(proof)
    assert stale.value.status == 401
    complete(scene, link_token(second.json()["recipient_link"]))
    assert scene.send(scene.body()).status_code == 409


def test_not_due_no_confirmation_csrf_and_self(scene: Scene) -> None:
    req = scene.operating(expire=False)
    body = scene.body()
    assert scene.send(body).status_code == 409
    expire_case(scene.db, req.operation_id)
    assert scene.send(body, nonce="wrong").status_code == 403
    assert scene.send({**body, "identity_confirmed": False}).status_code == 422
    assert scene.send({**body, "factors": "password"}).status_code == 422
    assert (
        scene.actor.get(
            f"/api/v1/admin/master-accounts/{scene.actor_id}/emergency-recovery"
        ).status_code
        == 404
    )
    assert scene.actor.get("/api/v1" + scene.route + "/" + str(uuid4())).status_code == 404


@pytest.mark.parametrize(
    "column",
    [
        "row_version",
        "security_version",
        "reset_generation",
    ],
)
def test_every_target_epoch_stales_case(scene: Scene, column: str) -> None:
    scene.operating()
    body = scene.body()
    with scene.db.session() as db:
        db.execute(
            text(f"UPDATE iam_accounts SET {column}={column}+1 WHERE id=:a"), {"a": scene.ident}
        )
        db.commit()
    assert scene.send(body).status_code == 409
    # Fresh request snapshot cannot launder an obsolete parent epoch.
    assert scene.send(scene.body()).status_code == 409


def test_pending_scope_and_target_state(scene: Scene) -> None:
    scene.operating()
    body = scene.body()
    with scene.db.session() as db:
        db.execute(
            text(
                "UPDATE iam_accounts SET password_reset_pending=false,"
                "password_hash='synthetic' WHERE id=:a"
            ),
            {"a": scene.ident},
        )
        db.commit()
    assert scene.send(scene.body()).status_code == 409
    with scene.db.session() as db:
        db.execute(text("UPDATE iam_accounts SET state='DISABLED' WHERE id=:a"), {"a": scene.ident})
        db.commit()
    assert scene.send(body).status_code == 409


def fingerprint(scene: Scene) -> str:
    with scene.db.session() as db:
        values = [
            db.execute(
                text(
                    f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                    f"ORDER BY row_to_json(t)::text),'')) FROM {table} t"
                )
            ).scalar_one()
            for table in (
                "iam_accounts",
                "iam_sessions",
                "iam_passkeys",
                "iam_mfa_contexts",
                "iam_password_emergency_cases",
                "iam_password_emergency_credentials",
                "audit_events",
            )
        ]
    return json.dumps(values)


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("UPDATE iam_sessions SET revoked=true WHERE account_id=:a", 401),
        (
            "UPDATE iam_accounts SET password_reset_pending=true,password_hash=NULL,"
            "reset_generation=reset_generation+1 WHERE id=:a",
            401,
        ),
        ("DELETE FROM iam_admin_grants WHERE account_id=:a", 403),
    ],
)
def test_current_actor_authority(scene: Scene, mutation: str, expected: int) -> None:
    scene.operating()
    body = scene.body()
    nonce = csrf(scene.actor)
    with scene.db.session() as db:
        db.execute(text(mutation), {"a": scene.actor_id})
        db.commit()
    before = fingerprint(scene)
    assert scene.send(body, nonce).status_code == expected
    assert fingerprint(scene) == before


def test_normal_opposite_pending_guards_remain(scene: Scene) -> None:
    from tests.password_helpers import reset_request

    scene.operating()
    assert reset_request(scene.actor, str(scene.ident)).status_code == 409
    assert scene.send(scene.body()).status_code == 201


def test_any_current_master_reissues_and_recipient_outlives_issuer_role(scene: Scene) -> None:
    with closing(TestClient(scene.actor.app, base_url=ORIGIN)) as third:
        created = call(
            scene.actor, "/admin/master-accounts", csrf(scene.actor), {"login_id": "third.master"}
        )
        assert created.status_code == 201

        activate(third, link_token(created.json()["setup_link"]), scene.password)
        login_password(third, scene.password, "third.master")
        scene.operating()
        assert scene.send(scene.body()).status_code == 201
        with scene.db.session() as db:
            db.execute(
                text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": scene.actor_id}
            )
            db.commit()
        original_actor = scene.actor
        scene.actor = third
        response = scene.send(scene.body())
        scene.actor = original_actor
        assert response.status_code == 201
        with scene.db.session() as db:
            db.execute(
                text("DELETE FROM iam_admin_grants WHERE account_id=:a"),
                {"a": str(created.json()["account_id"])},
            )
            db.commit()
        complete(scene, link_token(response.json()["recipient_link"]))


def test_cross_organization_case_not_disclosed(scene: Scene) -> None:
    scene.operating()
    body = scene.body()
    nonce = csrf(scene.actor)
    other = uuid4()
    with scene.db.session() as db:
        db.execute(
            text("INSERT INTO organization_organizations(id,name) VALUES(:o,'Other QA')"),
            {"o": other},
        )
        # Existing real MFA principal moved only in the controlled authorization fixture.
        db.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": scene.actor_id})
        db.execute(
            text("UPDATE iam_accounts SET organization_id=:o WHERE id=:a"),
            {"o": other, "a": scene.actor_id},
        )
        db.execute(
            text(
                "INSERT INTO iam_admin_grants(account_id,organization_id,scope) "
                "VALUES(:a,:o,'ORGANIZATION')"
            ),
            {"o": other, "a": scene.actor_id},
        )
        db.commit()
    assert scene.actor.get("/api/v1" + scene.route).status_code == 404
    assert scene.send(body, nonce).status_code == 404
