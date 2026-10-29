# ruff: noqa: F811
"""Actual Trainer role lifecycle; preserve accounts, factors and immutable identities."""

from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_workforce import Scene, scene  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def state(t: TrainerScene) -> dict[str, Any]:
    r = t.base.client.get("/api/v1/admin/trainers/" + t.trainer + "/role")
    assert r.status_code == 200
    return dict(r.json())


def body(t: TrainerScene, granted: bool) -> dict[str, Any]:
    current = state(t)
    detail = t.base.client.get("/api/v1/admin/trainers/" + t.trainer).json()
    return dict(
        operation_id=str(uuid4()),
        account_id=current["account_id"],
        desired_granted=granted,
        expected_account_version=current["account_version"],
        expected_role_version=current["role_version"],
        expected_trainer_version=detail["version"],
        identity_confirmed=True,
    )


def change(t: TrainerScene, payload: dict[str, Any]) -> Any:
    return call(
        t.base.client, "/admin/trainers/" + t.trainer + "/role", csrf(t.base.client), payload
    )


def test_pending_withdraw_regrant_explicit_new_source(trainer: TrainerScene) -> None:
    t = trainer
    old = source(t.issue())
    assert change(t, body(t, False)).status_code == 200
    assert t.complete(old).status_code == 400
    assert t.reissue().status_code == 409
    assert change(t, body(t, True)).status_code == 200
    assert t.complete(old).status_code == 400
    new = source(t.reissue())
    assert t.complete(new).status_code == 204
    assert t.signin().status_code == 204
    assert t.recipient.get("/api/v1/auth/me").json()["roles"][0]["role"] == "TRAINER"


def test_last_role_preserves_password_and_replay_new_login(trainer: TrainerScene) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    ident = state(t)["account_id"]
    with t.base.db.session() as s:
        original = s.execute(
            text(
                "SELECT md5(password_hash),row_version,security_version,state "
                "FROM iam_accounts WHERE id=:a"
            ),
            {"a": ident},
        ).one()
    request = body(t, False)
    assert change(t, request).status_code == 200
    assert t.recipient.get("/api/v1/auth/me").status_code == 401
    assert t.signin().status_code == 401
    assert change(t, body(t, True)).status_code == 200
    assert t.signin().status_code == 204
    assert change(t, request).status_code == 200
    assert t.recipient.get("/api/v1/auth/me").status_code == 200
    assert change(t, body(t, True)).json()["changed"] is False
    assert t.recipient.get("/api/v1/auth/me").status_code == 200
    with t.base.db.session() as s:
        assert (
            s.execute(
                text(
                    "SELECT md5(password_hash),row_version,security_version,state "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": ident},
            ).one()
            == original
        )
        assert s.execute(text("SELECT count(*) FROM audit_trainer_role_events")).scalar_one() == 2


def test_first_link_self_requires_new_uv_and_preserves_admin(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as c:
        key = Authenticator()
        enroll(c, token, key)
        login_mfa(c, password, key)
        actor = c.get("/api/v1/auth/me").json()["account_id"]
        b = call(c, "/admin/branches", csrf(c), {"code": "R", "name": "역할 가상지점"}).json()
        s = Scene(c, db, b["id"])
        t = s.send(s.body()).json()["trainer"]
        lookup = call(
            c,
            "/admin/trainers/" + t["id"] + "/role-account-lookup",
            csrf(c),
            {"login_id": "master.test"},
        )
        assert lookup.status_code == 200
        assert set(lookup.json()) == {
            "account_id",
            "login_id",
            "state",
            "account_version",
            "role_version",
            "eligible",
        }
        request = dict(
            operation_id=str(uuid4()),
            account_id=actor,
            desired_granted=True,
            expected_account_version=lookup.json()["account_version"],
            expected_role_version=0,
            expected_trainer_version=t["version"],
            identity_confirmed=True,
        )
        r = call(c, "/admin/trainers/" + t["id"] + "/role", csrf(c), request)
        assert r.status_code == 200 and r.json()["reauthentication_required"] is True
        assert c.get("/api/v1/auth/me").status_code == 401
        login_mfa(c, password, key)
        profile = c.get("/api/v1/auth/me").json()
        assert [x["role"] for x in profile["roles"]] == ["ADMIN", "TRAINER"]
        assert c.get("/api/v1/branches").status_code == 200
        assert call(c, "/admin/trainers/" + t["id"] + "/role", csrf(c), request).status_code == 200
        assert c.get("/api/v1/auth/me").status_code == 200


@pytest.mark.parametrize("absolute", [False, True])
def test_final_actor_snapshot_read_crosses_original_deadline(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, absolute: bool
) -> None:
    from y3management.iam.public import Authentication
    from y3management.iam.roles import TrainerRoles

    t = trainer
    source(t.issue())
    request = body(t, False)
    nonce = csrf(t.base.client)
    actor = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    with t.base.db.session() as s:
        if absolute:
            s.execute(
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
            s.execute(
                text(
                    "UPDATE iam_sessions SET "
                    "created_at=clock_timestamp()-interval '31 minutes',"
                    "last_activity=clock_timestamp()-interval '29 minutes 58 seconds' "
                    "WHERE account_id=:a"
                ),
                {"a": actor},
            )
        s.commit()
    original = TrainerRoles.stable_actor
    observations: list[tuple[bool, bool]] = []
    reads = 0

    def delayed(self: TrainerRoles, authentication: Authentication) -> bytes:
        nonlocal reads
        reads += 1
        value = original(self, authentication)
        if reads == 2:
            query = text(
                "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
                "expires_at>clock_timestamp() FROM iam_sessions WHERE id=:i"
            )
            row = self.s.execute(query, {"i": authentication.session_id}).one()
            observations.append((bool(row[0]), bool(row[1])))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            row = self.s.execute(query, {"i": authentication.session_id}).one()
            observations.append((bool(row[0]), bool(row[1])))
        return value

    monkeypatch.setattr(TrainerRoles, "stable_actor", delayed)
    response = call(t.base.client, "/admin/trainers/" + t.trainer + "/role", nonce, request)
    assert response.status_code == 401
    assert observations[0] == (True, True)
    assert observations[1][1 if absolute else 0] is False
    with t.base.db.session() as s:
        assert s.execute(text("SELECT granted FROM iam_trainer_role_grants")).scalar_one()
        assert s.execute(text("SELECT count(*) FROM iam_trainer_role_operations")).scalar_one() == 0
        assert s.execute(text("SELECT count(*) FROM audit_trainer_role_events")).scalar_one() == 0
        assert not s.execute(
            text("SELECT consumed FROM iam_trainer_setup_credentials")
        ).scalar_one()


@pytest.mark.parametrize("account_state", ["PENDING_SETUP", "ACTIVE", "DISABLED"])
@pytest.mark.parametrize("active", [False, True])
def test_revoke_any_state_regrant_only_eligible(
    trainer: TrainerScene, account_state: str, active: bool
) -> None:
    t = trainer
    token = source(t.issue())
    if account_state != "PENDING_SETUP":
        assert t.complete(token).status_code == 204
    if account_state == "DISABLED":
        ident = state(t)["account_id"]
        with t.base.db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_accounts SET state='DISABLED',row_version=row_version+1 WHERE id=:a"
                ),
                {"a": ident},
            )
            s.commit()
    t.active(active)
    assert change(t, body(t, False)).status_code == 200
    assert change(t, body(t, True)).status_code == (
        200 if active and account_state != "DISABLED" else 409
    )


def test_audit_failure_rolls_back_role_source_and_receipt(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import TrainerRoleEvent
    from y3management.contracts import Rejected

    t = trainer
    token = source(t.issue())
    request = body(t, False)
    original = Audit.append_trainer_role

    def fail(self: Audit, event: TrainerRoleEvent) -> None:
        original(self, event)
        raise Rejected(409, "conflict")

    monkeypatch.setattr(Audit, "append_trainer_role", fail)
    assert change(t, request).status_code == 409
    assert state(t)["granted"] is True
    result = t.base.client.get("/api/v1/admin/trainer-role-operations/" + request["operation_id"])
    assert result.status_code == 404
    assert t.complete(token).status_code == 204
    with t.base.db.session() as s:
        assert s.execute(text("SELECT count(*) FROM audit_trainer_role_events")).scalar_one() == 0


def test_stale_versions_conflicting_operation_and_status(trainer: TrainerScene) -> None:
    t = trainer
    source(t.issue())
    request = body(t, False)
    for field in ("expected_account_version", "expected_role_version", "expected_trainer_version"):
        assert change(t, {**request, field: request[field] + 1}).status_code == 409
    assert change(t, request).status_code == 200
    assert change(t, {**request, "desired_granted": True}).status_code == 409
    result = t.base.client.get("/api/v1/admin/trainer-role-operations/" + request["operation_id"])
    assert result.status_code == 200
    assert result.json()["committed_granted"] is False
    assert set(result.json()) == {
        "operation_id",
        "changed",
        "committed_granted",
        "committed_role_version",
        "current_state",
        "reauthentication_required",
    }
