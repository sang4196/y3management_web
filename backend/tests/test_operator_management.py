# ruff: noqa: F811
"""Operator management through public commands, receipts and independent role routes."""

from contextlib import closing
from typing import Any, cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from tests.password_helpers import PrivateResponse, password_app  # noqa: F401
from tests.password_helpers import call as password_call
from tests.test_iam import csrf
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_workforce import scene  # noqa: F401

pytestmark = pytest.mark.postgres
BASE = "/admin/operator-roles"


def role_headers(client: Any) -> dict[str, str]:
    if not hasattr(client, "operator_actor"):
        client.operator_actor = client.get("/api/v1/auth/me").json()["account_id"]
    return {"X-Y3-Expected-Actor": client.operator_actor}


def call(client: Any, path: str, nonce: str, body: dict[str, Any]) -> Any:
    if path.startswith(BASE):
        return PrivateResponse(
            client.post(
                "/api/v1" + path,
                headers={
                    **role_headers(client),
                    "X-CSRF-Token": nonce,
                    "Origin": str(client.base_url).rstrip("/"),
                },
                json=body,
            )
        )
    return password_call(client, path, nonce, body)


def role_get(client: Any, path: str, **kwargs: Any) -> Any:
    return client.get(path, headers=role_headers(client), **kwargs)


def candidate(t: TrainerScene, identifier: str, branch: str | None = None) -> Any:
    return call(
        t.base.client,
        BASE + "/lookup",
        csrf(t.base.client),
        {"login_id": identifier, "branch_id": branch or t.base.branch},
    )


def command(
    t: TrainerScene,
    row: dict[str, Any],
    desired: bool = True,
    move: str | None = None,
    operation: str | None = None,
) -> Any:
    grant = row["operator_grant"]
    body: dict[str, Any] = {
        "operation_id": operation or str(uuid4()),
        "expected_account_version": row["account_version"],
        "expected_operator_version": grant["scope"]["version"] if grant else 0,
        "branch_id": move or row["branch_id"],
    }
    if move is None:
        body["desired_granted"] = desired
    return call(
        t.base.client,
        BASE + "/" + row["account_id"] + ("/branch" if move else "/changes"),
        csrf(t.base.client),
        body,
    )


def test_operator_role_receipts_move_and_raw_history(trainer: TrainerScene) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    row = candidate(t, t.login).json()
    operation = str(uuid4())
    added = command(t, row, operation=operation)
    assert added.status_code == 200
    current = added.json()["current"]
    assert current["account_version"] == row["account_version"]
    assert current["operator_grant"]["scope"]["version"] == 1
    assert command(t, row, operation=operation).json()["committed_version"] == 1
    revoked = command(t, current, False)
    assert revoked.status_code == 200
    replay = command(t, row, operation=operation)
    assert replay.status_code == 200
    assert replay.json()["granted"] is True
    assert replay.json()["current"]["operator_grant"]["granted"] is False
    restored = command(t, revoked.json()["current"])
    assert restored.status_code == 200
    assert command(t, row).status_code == 409
    branch = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "B" + uuid4().hex[:8], "name": "Work branch"},
    ).json()["id"]
    moved = command(t, restored.json()["current"], move=branch)
    assert moved.status_code == 200
    final = moved.json()["current"]
    assert final["account_version"] == row["account_version"]
    assert final["operator_grant"]["scope"]["version"] == 4
    with t.base.db.session() as reader:
        assert reader.scalar(text("SELECT count(*) FROM audit_operator_role_events")) == 4
    assert t.signin().status_code == 204
    me = t.recipient.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert t.recipient.get("/api/v1/operator/branches/" + branch).status_code == 200


def test_pending_move_keeps_tuple_rejects_old_setup_and_stale_reissue(
    trainer: TrainerScene,
) -> None:
    t = trainer
    issued = call(
        t.base.client,
        "/admin/operator-accounts",
        csrf(t.base.client),
        {"login_id": t.login, "branch_id": t.base.branch},
    )
    assert issued.status_code == 201
    old = source(issued)
    row = candidate(t, t.login).json()
    branch = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "DEST", "name": "Destination"},
    ).json()["id"]
    with t.base.db.session() as reader:
        before = tuple(
            reader.execute(
                text(
                    "SELECT row_version,security_version,reset_generation,"
                    "state,restore_state FROM iam_accounts WHERE id=:a"
                ),
                {"a": row["account_id"]},
            ).one()
        )
    moved = command(t, row, move=branch)
    assert moved.status_code == 200
    with t.base.db.session() as reader:
        after = tuple(
            reader.execute(
                text(
                    "SELECT row_version,security_version,reset_generation,"
                    "state,restore_state FROM iam_accounts WHERE id=:a"
                ),
                {"a": row["account_id"]},
            ).one()
        )
        assert before == after
        assert (
            reader.scalar(
                text("SELECT consumed FROM iam_operator_setup_credentials WHERE account_id=:a"),
                {"a": row["account_id"]},
            )
            is True
        )
    path = "/admin/operator-accounts/" + row["account_id"] + "/initial-setup"
    stale = call(
        t.base.client,
        path,
        csrf(t.base.client),
        {"expected_version": row["account_version"], "expected_operator_version": 1},
    )
    assert stale.status_code == 409
    assert (
        call(
            t.recipient,
            "/auth/operator-credentials/complete",
            csrf(t.recipient),
            {"setup_token": old, "new_password": t.password},
        ).status_code
        == 400
    )
    fresh = call(
        t.base.client,
        path,
        csrf(t.base.client),
        {"expected_version": row["account_version"], "expected_operator_version": 2},
    )
    assert fresh.status_code == 201
    assert (
        call(
            t.recipient,
            "/auth/operator-credentials/complete",
            csrf(t.recipient),
            {"setup_token": source(fresh), "new_password": t.password},
        ).status_code
        == 204
    )


def test_master_self_roles_auth_audit_and_receipt(trainer: TrainerScene, password_app: Any) -> None:
    from tests.password_helpers import login_password

    t = trainer
    client = t.base.client
    me = client.get("/api/v1/auth/me").json()
    row = role_get(
        client,
        "/api/v1/admin/operator-roles/" + me["account_id"],
        params={"branch_id": t.base.branch},
    ).json()
    operation = str(uuid4())
    result = command(t, row, operation=operation)
    assert result.status_code == 200 and result.json()["reauthentication_required"]
    assert client.get("/api/v1/auth/me").status_code == 401
    login_password(client, password_app[2])
    assert client.get("/api/v1/auth/me").status_code == 200
    receipt = role_get(client, "/api/v1/admin/operator-role-operations/" + operation)
    assert receipt.status_code == 200 and receipt.json()["committed_version"] == 1
    assert client.get("/api/v1/branches").status_code == 200
    assert client.get("/api/v1/operator/branches/" + t.base.branch).status_code == 200
    assert call(client, "/auth/logout", csrf(client), {}).status_code == 204
    with t.base.db.session() as reader:
        roles = (
            reader.execute(
                text(
                    "SELECT actor_role FROM audit_operator_account_events "
                    "WHERE kind IN ('login','logout')"
                )
            )
            .scalars()
            .all()
        )
        assert roles == ["MASTER", "MASTER"]


@pytest.mark.parametrize("state", ["ACTIVE", "PENDING_SETUP", "DISABLED"])
def test_operator_withdrawn_lifecycle_and_regrant_boundaries(
    trainer: TrainerScene, state: str
) -> None:
    from tests.test_account_lifecycle import mutate

    t = trainer
    issued = call(
        t.base.client,
        "/admin/operator-accounts",
        csrf(t.base.client),
        {"login_id": t.login, "branch_id": t.base.branch},
    )
    assert issued.status_code == 201
    if state == "ACTIVE":
        assert (
            call(
                t.recipient,
                "/auth/operator-credentials/complete",
                csrf(t.recipient),
                {"setup_token": source(issued), "new_password": t.password},
            ).status_code
            == 204
        )
    if state == "DISABLED":
        disabled = mutate(t, issued.json(), "status", status="DISABLED")
        assert disabled.status_code == 200
    row = candidate(t, t.login).json()
    revoked = command(t, row, False)
    assert revoked.status_code == 200
    managed = call(
        t.base.client, "/admin/account-lifecycle/lookup", csrf(t.base.client), {"login_id": t.login}
    )
    assert managed.status_code == 200 and managed.json()["state"] == state
    branch = call(
        t.base.client, "/admin/branches", csrf(t.base.client), {"code": "MOVE", "name": "Other"}
    ).json()["id"]
    moved = command(t, revoked.json()["current"], move=branch)
    assert moved.status_code == 200 and moved.json()["granted"] is False
    result = command(t, moved.json()["current"])
    assert result.status_code == (409 if state == "DISABLED" else 200)
    if state == "ACTIVE":
        assert command(t, result.json()["current"], False).status_code == 200
        from tests.password_helpers import link_token
        from tests.test_iam_password_reset import complete, reset_request

        reset = reset_request(t.base.client, row["account_id"])
        assert reset.status_code == 201
        assert (
            complete(
                t.recipient, link_token(reset.json()["reset_link"]), t.password + " changed"
            ).status_code
            == 204
        )
        assert (
            call(
                t.recipient,
                "/auth/login",
                csrf(t.recipient),
                {"login_id": t.login, "password": t.password + " changed"},
            ).status_code
            == 401
        )


@pytest.mark.parametrize("damage", ["audit", "account", "grant", "budget"])
def test_required_operator_audit_rolls_back_unexpected_change(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorRoleEvent
    from y3management.contracts import Rejected

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    row = candidate(t, t.login).json()
    original = Audit.append_operator_role

    def fail(self: Audit, event: OperatorRoleEvent) -> None:
        original(self, event)
        if damage == "audit":
            raise Rejected(503, "unavailable")
        if damage == "account":
            self.s.execute(
                text("UPDATE iam_accounts SET row_version=row_version+1 WHERE id=:a"),
                {"a": event.account_id},
            )
        elif damage == "grant":
            self.s.execute(
                text("UPDATE iam_operator_grants SET version=version+1 WHERE account_id=:a"),
                {"a": event.account_id},
            )
        else:
            self.s.execute(
                text("UPDATE iam_accounts SET login_budget_key=:k WHERE id=:a"),
                {"a": event.account_id, "k": b"x" * 32},
            )

    monkeypatch.setattr(Audit, "append_operator_role", fail)
    result = command(t, row)
    assert result.status_code == (503 if damage == "audit" else 409)
    assert candidate(t, t.login).json()["operator_grant"] is None
    with t.base.db.session() as reader:
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 0
        assert reader.scalar(text("SELECT count(*) FROM audit_operator_role_events")) == 0


@pytest.mark.parametrize("withdrawn", [False, True])
def test_emergency_move_keeps_original_case_and_handoff(
    password_app: Any, tmp_path: Any, withdrawn: bool
) -> None:
    from tests.password_helpers import link_token
    from tests.test_iam_emergency_handoff import complete
    from tests.test_iam_emergency_handoff import scene as emergency_scene

    with closing(cast(Any, emergency_scene).__wrapped__(password_app, tmp_path)) as fixture:
        recovery = next(fixture)
        client = recovery.actor
        branch = call(
            client, "/admin/branches", csrf(client), {"code": "REC", "name": "Recovery work"}
        ).json()["id"]
        target = str(recovery.ident)

        def read() -> dict[str, Any]:
            response = role_get(
                client, "/api/v1/admin/operator-roles/" + target, params={"branch_id": branch}
            )
            assert response.status_code == 200
            return dict(response.json())

        def send(row: dict[str, Any], move: str | None = None, desired: bool = True) -> Any:
            body = {
                "operation_id": str(uuid4()),
                "expected_account_version": row["account_version"],
                "expected_operator_version": row["operator_grant"]["scope"]["version"]
                if row["operator_grant"]
                else 0,
                "branch_id": move or branch,
            }
            if move is None:
                body["desired_granted"] = desired
            return call(
                client,
                BASE + "/" + target + ("/branch" if move else "/changes"),
                csrf(client),
                body,
            )

        assert send(read()).status_code == 200
        if withdrawn:
            assert send(read(), desired=False).status_code == 200
        original = recovery.operating()
        with recovery.db.session() as reader:
            fingerprint = reader.scalar(
                text(
                    "SELECT md5(row_to_json(c)::text) "
                    "FROM iam_password_emergency_cases c WHERE id=:i"
                ),
                {"i": original.operation_id},
            )
        destination = call(
            client,
            "/admin/branches",
            csrf(client),
            {"code": "REC2", "name": "Recovery destination"},
        ).json()["id"]
        moved = send(read(), destination)
        assert moved.status_code == 200 and moved.json()["granted"] is (not withdrawn)
        with recovery.db.session() as reader:
            assert (
                reader.scalar(
                    text(
                        "SELECT md5(row_to_json(c)::text) "
                        "FROM iam_password_emergency_cases c WHERE id=:i"
                    ),
                    {"i": original.operation_id},
                )
                == fingerprint
            )
        handoff = recovery.send(recovery.body())
        assert handoff.status_code == 201
        complete(recovery, link_token(handoff.json()["recipient_link"]))
        from tests.password_helpers import reset_request
        from tests.test_iam_password_reset import complete as reset_complete

        old_reset = reset_request(client, target)
        assert old_reset.status_code == 201
        assert send(read(), branch).status_code == 200
        assert (
            reset_complete(
                recovery.target,
                link_token(old_reset.json()["reset_link"]),
                recovery.password + " reset",
            ).status_code
            == 401
        )
        fresh_reset = reset_request(client, target, reissue=True)
        assert fresh_reset.status_code == 201
        assert (
            reset_complete(
                recovery.target,
                link_token(fresh_reset.json()["reset_link"]),
                recovery.password + " reset",
            ).status_code
            == 204
        )


def test_emergency_role_change_rejects_old_proof_allows_fresh(
    password_app: Any, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from contextlib import closing

    from tests.password_helpers import link_token
    from tests.test_iam_emergency_handoff import complete
    from tests.test_iam_emergency_handoff import scene as emergency_scene
    from y3management.contracts import Rejected

    with closing(cast(Any, emergency_scene).__wrapped__(password_app, tmp_path)) as fixture:
        recovery = next(fixture)
        actor = recovery.actor
        branch = call(
            actor, "/admin/branches", csrf(actor), {"code": "PRF", "name": "Proof"}
        ).json()["id"]
        target = str(recovery.ident)
        row = role_get(
            actor, "/api/v1/admin/operator-roles/" + target, params={"branch_id": branch}
        ).json()
        body = {
            "operation_id": str(uuid4()),
            "expected_account_version": row["account_version"],
            "expected_operator_version": 0,
            "desired_granted": True,
            "branch_id": branch,
        }
        assert call(actor, BASE + "/" + target + "/changes", csrf(actor), body).status_code == 200
        recovery.operating()
        response = recovery.send(recovery.body())
        token = link_token(response.json()["recipient_link"])
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event

        from y3management.iam.passwords import Passwords

        reached, release = Event(), Event()
        original_hash = Passwords.create

        def slow_hash(self: Passwords, password: str, login: str) -> str:
            result = original_hash(self, password, login)
            reached.set()
            assert release.wait(8)
            return result

        def prepare() -> Any:
            with recovery.service.uow.open() as w:
                return w.emergency.prepare_password(token, recovery.password + " fresh")

        row = role_get(actor, "/api/v1/admin/operator-roles/" + target).json()
        body.update(
            operation_id=str(uuid4()),
            expected_account_version=row["account_version"],
            expected_operator_version=1,
            desired_granted=False,
        )
        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
            patch.setattr(Passwords, "create", slow_hash)
            future = pool.submit(prepare)
            try:
                assert reached.wait(5)
                assert (
                    call(actor, BASE + "/" + target + "/changes", csrf(actor), body).status_code
                    == 200
                )
            finally:
                release.set()
            proof = future.result(timeout=5)
        with pytest.raises(Rejected):
            with recovery.service.uow.open() as w:
                w.emergency.complete_password(proof)
        complete(recovery, token)


def test_previous16_current17_roundtrip_and_full_rows(password_app: Any, tmp_path: Any) -> None:
    from fastapi.testclient import TestClient

    from tests.historical_backend import archive_backend, execute_original
    from tests.test_account_lifecycle import lifecycle_fingerprints
    from tests.test_password_transition import migrate
    from y3management.application import create_app

    settings, db, _ = password_app
    migrate(settings, "downgrade", "0016_operator_onboarding")
    baseline = lifecycle_fingerprints(db)
    old = archive_backend(tmp_path, "33c9e20ea36a7ce35833dbc1864b03d0b2c08355")
    script = """import os
os.environ['Y3_IAM_MODE']='password'
from y3management.config import load_settings
from y3management.application import create_app
from fastapi.testclient import TestClient
try:
    with TestClient(create_app(load_settings())):
        started=True
except ValueError as error:
    assert str(error)=='APPLICATION_STARTUP_FAILED'
    started=False
assert started==EXPECTED
"""
    execute_original(old, settings, script.replace("EXPECTED", "True"))
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current runtime accepted16")
    migrate(settings, "upgrade", "0017_operator_management")
    (tmp_path / "original17").mkdir()
    original17 = archive_backend(
        tmp_path / "original17", "7b64f5731ed993f5f8473a1476f27fb6c4931513"
    )
    execute_original(original17, settings, script.replace("EXPECTED", "True"))
    with (
        pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
        TestClient(create_app(settings)),
    ):
        pytest.fail("Current runtime accepted17")
    execute_original(old, settings, script.replace("EXPECTED", "False"))
    current = lifecycle_fingerprints(db)
    assert {k: v for k, v in current.items() if k in baseline and k != "alembic_version"} == {
        k: v for k, v in baseline.items() if k != "alembic_version"
    }
    assert set(current) - set(baseline) == {
        "iam_operator_role_operations",
        "audit_operator_role_events",
    }
    migrate(settings, "downgrade", "0016_operator_onboarding")
    assert lifecycle_fingerprints(db) == baseline
    migrate(settings, "upgrade", "head")


def test_operator_receipt_audit_identity_fk_and_downgrade_guard(trainer: TrainerScene) -> None:
    from sqlalchemy.exc import IntegrityError

    from tests.legacy_helpers import assert_revision_loss_guard

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    result = command(t, candidate(t, t.login).json())
    assert result.status_code == 200
    with t.base.db.session() as session:
        original = dict(
            session.execute(text("SELECT * FROM audit_operator_role_events")).mappings().one()
        )
        session.execute(text("DELETE FROM audit_operator_role_events"))
        original["account_id"] = original["actor_id"]
        with pytest.raises(IntegrityError):
            session.execute(
                text(
                    "INSERT INTO audit_operator_role_events ("
                    + ",".join(original)
                    + ") VALUES ("
                    + ",".join(":" + key for key in original)
                    + ")"
                ),
                original,
            )
        session.rollback()
    assert_revision_loss_guard(
        t.base.db, "0017_operator_management.py", "OPERATOR_MANAGEMENT_HISTORY_PRESENT"
    )


@pytest.mark.parametrize(
    "state", ["pending", "disabled_pending", "active", "disabled_active", "reset"]
)
@pytest.mark.parametrize("withdrawn", [False, True])
def test_move_state_matrix_and_source_gc(
    trainer: TrainerScene, state: str, withdrawn: bool
) -> None:
    from tests.password_helpers import link_token, reset_request
    from tests.test_account_lifecycle import mutate
    from tests.test_iam_password_reset import complete
    from y3management.iam.security import Security

    t = trainer
    issued = call(
        t.base.client,
        "/admin/operator-accounts",
        csrf(t.base.client),
        {"login_id": t.login, "branch_id": t.base.branch},
    )
    assert issued.status_code == 201
    ident = issued.json()["account_id"]
    if state in ("active", "disabled_active", "reset"):
        assert (
            call(
                t.recipient,
                "/auth/operator-credentials/complete",
                csrf(t.recipient),
                {"setup_token": source(issued), "new_password": t.password},
            ).status_code
            == 204
        )
    if state.startswith("disabled"):
        current = t.base.client.get("/api/v1/admin/operator-accounts/" + ident).json()
        assert mutate(t, current, "status", status="DISABLED").status_code == 200
    old_reset = None
    if state == "reset":
        old_reset = link_token(reset_request(t.base.client, ident).json()["reset_link"])
    if withdrawn:
        assert command(t, candidate(t, t.login).json(), False).status_code == 200
    destination = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "DEST", "name": "Destination"},
    ).json()["id"]
    with t.base.db.engine.begin() as writer:
        writer.execute(
            text(
                "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                "WHERE id=:b"
            ),
            {"b": t.base.branch},
        )
    with t.base.db.session() as reader:
        before = reader.scalar(
            text("SELECT md5(row_to_json(a)::text) FROM iam_accounts a WHERE id=:a"), {"a": ident}
        )
        sources = reader.execute(
            text(
                "SELECT id,branch_id,grant_version,expires_at "
                "FROM iam_operator_setup_credentials WHERE account_id=:a"
            ),
            {"a": ident},
        ).all()
    moved = command(t, candidate(t, t.login).json(), move=destination)
    assert moved.status_code == 200
    assert moved.json()["granted"] is (not withdrawn)
    assert moved.json()["current"]["can_move"] is True
    with t.base.db.session() as reader:
        assert (
            reader.scalar(
                text("SELECT md5(row_to_json(a)::text) FROM iam_accounts a WHERE id=:a"),
                {"a": ident},
            )
            == before
        )
        assert (
            reader.execute(
                text(
                    "SELECT id,branch_id,grant_version,expires_at "
                    "FROM iam_operator_setup_credentials WHERE account_id=:a"
                ),
                {"a": ident},
            ).all()
            == sources
        )
        Security(reader, "synthetic-key", 2048, 128)._guard()
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_grants")) == 1
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == (
            2 if withdrawn else 1
        )
        assert reader.scalar(text("SELECT count(*) FROM audit_operator_role_events")) == (
            2 if withdrawn else 1
        )
        reader.rollback()
    if old_reset:
        assert complete(t.recipient, old_reset, t.password + " new").status_code == 401
        fresh = reset_request(t.base.client, ident, reissue=True)
        assert fresh.status_code == 201
        assert (
            complete(
                t.recipient, link_token(fresh.json()["reset_link"]), t.password + " new"
            ).status_code
            == 204
        )


@pytest.mark.parametrize("clock", ["idle", "absolute"])
@pytest.mark.parametrize("withdrawn", [False, True])
def test_operator_required_audit_wait_crosses_original_deadline(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    clock: str,
    withdrawn: bool,
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic

    from tests.test_admin_actor_clock import expire_soon
    from tests.test_workforce_integrity import wait_for_owned_block
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorRoleEvent

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    row = candidate(t, t.login).json()
    if withdrawn:
        added = command(t, row)
        assert added.status_code == 200
        revoked = command(t, added.json()["current"], False)
        assert revoked.status_code == 200
        row = revoked.json()["current"]
    actor = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    nonce = csrf(t.base.client)
    payload = {
        "operation_id": str(uuid4()),
        "expected_account_version": row["account_version"],
        "expected_operator_version": 0,
        "desired_granted": True,
        "branch_id": t.base.branch,
    }
    path = BASE + "/" + row["account_id"] + "/changes"
    if withdrawn:
        from tests.test_operator_withdrawn_move import destination

        payload.pop("desired_granted")
        payload.update(expected_operator_version=2, branch_id=destination(t))
        path = BASE + "/" + row["account_id"] + "/branch"
    expire_soon(t.base.db, actor, clock)
    with t.base.db.session() as reader:
        deadline = reader.scalar(
            text(
                "SELECT least(last_activity+interval '30 minutes',expires_at) "
                "FROM iam_sessions WHERE account_id=:a AND NOT revoked"
            ),
            {"a": actor},
        )
    reached = Event()
    waiters = []
    original = Audit.append_operator_role

    def append(self: Audit, value: OperatorRoleEvent) -> None:
        while True:
            now = self.s.scalar(text("SELECT clock_timestamp()"))
            if (deadline - now).total_seconds() <= 0.7:
                assert now < deadline
                break
            self.s.execute(text("SELECT pg_sleep(0.05)"))
        waiters.append(self.s.scalar(text("SELECT pg_backend_pid()")))
        reached.set()
        original(self, value)

    monkeypatch.setattr(Audit, "append_operator_role", append)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with t.base.db.session() as holder:
            holder.execute(text("LOCK TABLE audit_operator_role_events IN SHARE MODE"))
            pid = holder.scalar(text("SELECT pg_backend_pid()"))
            future = pool.submit(call, t.base.client, path, nonce, payload)
            try:
                assert reached.wait(5)
                wait_for_owned_block(t.base.db, pid, waiters)
                end = monotonic() + 2
                while holder.scalar(text("SELECT clock_timestamp()")) <= deadline:
                    assert monotonic() < end
                    holder.execute(text("SELECT pg_sleep(0.02)"))
            finally:
                holder.rollback()
        assert future.result(timeout=5).status_code == 401
    with t.base.db.session() as reader:
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_grants")) == int(withdrawn)
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == (
            2 if withdrawn else 0
        )
        assert reader.scalar(text("SELECT count(*) FROM audit_operator_role_events")) == (
            2 if withdrawn else 0
        )


def test_concurrent_first_grant_is_one_effect(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy import event

    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorRoleEvent

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    row = candidate(t, t.login).json()
    nonce = csrf(t.base.client)
    payload = {
        "operation_id": str(uuid4()),
        "expected_account_version": row["account_version"],
        "expected_operator_version": 0,
        "desired_granted": True,
        "branch_id": t.base.branch,
    }
    reached, release = Event(), Event()
    holders = []
    waiters = []
    original = Audit.append_operator_role

    def append(self: Audit, value: OperatorRoleEvent) -> None:
        original(self, value)
        holders.append(self.s.scalar(text("SELECT pg_backend_pid()")))
        reached.set()
        assert release.wait(8)

    def observe(conn: Any, cursor: Any, sql: str, params: Any, context: Any, many: bool) -> None:
        pid = conn.connection.driver_connection.info.backend_pid
        if (
            reached.is_set()
            and not release.is_set()
            and pid not in holders
            and "pg_blocking_pids" not in sql
        ):
            waiters.append(pid)

    def second() -> Any:
        return call(
            t.base.client,
            BASE + "/" + row["account_id"] + "/changes",
            nonce,
            {**payload, "operation_id": str(uuid4())},
        )

    monkeypatch.setattr(Audit, "append_operator_role", append)
    event.listen(t.base.db.engine, "before_cursor_execute", observe)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                call, t.base.client, BASE + "/" + row["account_id"] + "/changes", nonce, payload
            )
            try:
                assert reached.wait(5)
                other = pool.submit(second)
                from tests.test_workforce_integrity import wait_for_owned_block

                wait_for_owned_block(t.base.db, holders[0], waiters)

            finally:
                release.set()
            assert first.result(timeout=5).status_code == 200
            assert other.result(timeout=5).status_code == 409
    finally:
        event.remove(t.base.db.engine, "before_cursor_execute", observe)
    with t.base.db.session() as reader:
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 1
        assert reader.scalar(text("SELECT version FROM iam_operator_grants")) == 1


def test_branch_admin_operator_trainer_scopes_and_real_auth(
    trainer: TrainerScene, password_app: Any
) -> None:
    from tests.password_helpers import login_password
    from tests.test_workforce import Scene
    from tests.test_workforce_integrity import branch_actor

    t = trainer
    master = t.base.client
    work = call(master, "/admin/branches", csrf(master), {"code": "WORK", "name": "Work"}).json()[
        "id"
    ]
    home = call(master, "/admin/branches", csrf(master), {"code": "HOME", "name": "Home"}).json()[
        "id"
    ]
    home_scene = Scene(master, t.base.db, home)
    trainer_row = home_scene.send(home_scene.body()).json()["trainer"]
    with closing(branch_actor(t.base, password_app[2])) as admin:
        row = candidate(t, "workforce.branch", work).json()
        added = command(t, row)
        assert added.status_code == 200
        lookup = call(
            master,
            "/admin/trainers/" + trainer_row["id"] + "/role-account-lookup",
            csrf(master),
            {"login_id": "workforce.branch"},
        ).json()
        bound = call(
            master,
            "/admin/trainers/" + trainer_row["id"] + "/role",
            csrf(master),
            {
                "operation_id": str(uuid4()),
                "account_id": row["account_id"],
                "desired_granted": True,
                "expected_account_version": lookup["account_version"],
                "expected_role_version": 0,
                "expected_trainer_version": trainer_row["version"],
                "identity_confirmed": True,
            },
        )
        assert bound.status_code == 200
        login_password(admin, password_app[2], "workforce.branch")
        profile = admin.get("/api/v1/auth/me").json()
        assert [(v["role"]) for v in profile["roles"]] == ["ADMIN", "OPERATOR", "TRAINER"]
        assert profile["roles"][0]["branch_id"] == t.base.branch
        assert profile["roles"][1]["branch_id"] == work
        assert profile["roles"][2]["home_branch_id"] == home
        assert admin.get("/api/v1/branches/" + t.base.branch).status_code == 200
        assert admin.get("/api/v1/branches/" + work).status_code == 404
        assert admin.get("/api/v1/operator/branches/" + work).status_code == 200
        assert admin.get("/api/v1/operator/branches/" + home).status_code == 404
        assert (
            role_get(admin, "/api/v1/admin/operator-roles/" + row["account_id"]).status_code == 404
        )
        next_password = password_app[2] + " rotated"
        assert (
            call(
                admin,
                "/auth/password",
                csrf(admin),
                {"current_password": password_app[2], "new_password": next_password},
            ).status_code
            == 204
        )
        login_password(admin, next_password, "workforce.branch")
        assert call(admin, "/auth/logout", csrf(admin), {}).status_code == 204
        with t.base.db.session() as reader:
            events = reader.execute(
                text(
                    "SELECT actor_role,actor_branch,branch_id FROM audit_operator_account_events "
                    "WHERE account_id=:a"
                ),
                {"a": row["account_id"]},
            ).all()
            assert len(events) == 4
            assert all(
                tuple(v) == ("BRANCH_ADMIN", UUID(t.base.branch), UUID(work)) for v in events
            )


@pytest.mark.parametrize("damage", ["account", "admin", "trainer", "budget", "case"])
def test_self_expected_delta_rejects_audit_corruption(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorRoleEvent

    t = trainer
    client = t.base.client
    actor = client.get("/api/v1/auth/me").json()["account_id"]
    row = role_get(
        client, "/api/v1/admin/operator-roles/" + actor, params={"branch_id": t.base.branch}
    ).json()
    original = Audit.append_operator_role

    def corrupt(self: Audit, value: OperatorRoleEvent) -> None:
        original(self, value)
        statements = {
            "account": "UPDATE iam_accounts SET security_version=security_version+1 WHERE id=:a",
            "admin": "DELETE FROM iam_admin_grants WHERE account_id=:a",
            "trainer": (
                "UPDATE iam_accounts SET trainer_role_epoch=trainer_role_epoch+1 WHERE id=:a"
            ),
            "budget": ("UPDATE iam_budgets SET cooldown=clock_timestamp()+interval '5 minutes' "),
        }
        if damage == "case":
            # A changed account recovery intent is also outside the permitted role delta.
            self.s.execute(
                text(
                    "UPDATE iam_accounts SET recovery_generation=recovery_generation+1 WHERE id=:a"
                ),
                {"a": actor},
            )
        else:
            self.s.execute(text(statements[damage]), {"a": actor})

    monkeypatch.setattr(Audit, "append_operator_role", corrupt)
    result = command(t, row)
    assert result.status_code == 409
    assert client.get("/api/v1/auth/me").status_code == 200
    with t.base.db.session() as reader:
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 0


def test_first_role0_and_noop_replay_preserve_new_auth(trainer: TrainerScene) -> None:
    from tests.test_iam_trainer_roles import body, change

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert change(t, body(t, False)).status_code == 200
    assert t.signin().status_code == 401
    row = candidate(t, t.login).json()
    op = str(uuid4())
    added = command(t, row, operation=op)
    assert added.status_code == 200
    assert t.signin().status_code == 204
    nonce = csrf(t.base.client)
    actor = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    payload = {
        "operation_id": op,
        "expected_account_version": row["account_version"],
        "expected_operator_version": 0,
        "desired_granted": True,
        "branch_id": row["branch_id"],
    }

    def sessions() -> Any:
        with t.base.db.session() as reader:
            return reader.execute(
                text("SELECT id,revoked,last_activity FROM iam_sessions ORDER BY id")
            ).all()

    before = sessions()
    path = BASE + "/" + row["account_id"] + "/changes"
    replay = call(t.base.client, path, nonce, payload)
    assert replay.status_code == 200 and replay.json()["committed_version"] == 1
    assert sessions() == before
    payload.update(operation_id=str(uuid4()), expected_operator_version=1)
    noop = call(t.base.client, path, nonce, payload)
    assert noop.status_code == 200 and noop.json()["changed"] is False
    assert sessions() == before
    assert t.recipient.get("/api/v1/auth/me").status_code == 200
    assert (
        call(t.base.client, path, nonce, {**payload, "desired_granted": False}).status_code == 409
    )
    assert actor != row["account_id"]


@pytest.mark.parametrize("withdrawn_move", [False, True])
def test_operator_aba_rejects_prepared_login_and_c3(
    trainer: TrainerScene, withdrawn_move: bool
) -> None:
    from tests.password_helpers import assert_prepared_rejected, prepare_login
    from y3management.contracts import Rejected
    from y3management.use_cases import Service

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    row = candidate(t, t.login).json()
    assert command(t, row).status_code == 200
    if withdrawn_move:
        assert command(t, candidate(t, t.login).json(), False).status_code == 200
    prepared = prepare_login(t.recipient, t.login, t.password)
    service: Service = cast(Any, t.base.client.app).state.iam_service
    with service.uow.open() as w:
        proof = w.iam.prepare_password_change(
            UUID(row["account_id"]), t.password, t.password + " next"
        )
    original = candidate(t, t.login).json()
    if withdrawn_move:
        from tests.test_operator_withdrawn_move import destination

        moved = command(t, original, move=destination(t))
        assert moved.status_code == 200
        returned = command(t, moved.json()["current"], move=original["branch_id"])
        assert returned.status_code == 200 and returned.json()["granted"] is False
    else:
        revoked = command(t, original, False)
        assert revoked.status_code == 200
        assert command(t, revoked.json()["current"]).status_code == 200
    assert_prepared_rejected(t.recipient, prepared)
    with pytest.raises(Rejected), service.uow.open() as w:
        w.iam.lock_login(proof.account_id)
        w.iam.change_password(proof)
    assert t.signin().status_code == 204


@pytest.mark.parametrize("retirement", ["consumed", "expired"])
def test_move_waits_for_locked_retired_source_and_gc_preserves_history(
    trainer: TrainerScene,
    retirement: str,
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    from tests.test_operator_onboarding import source_deadline_sql
    from tests.test_workforce_integrity import wait_for_owned_block
    from y3management.iam.security import Security

    t = trainer
    issued = call(
        t.base.client,
        "/admin/operator-accounts",
        csrf(t.base.client),
        {"login_id": t.login, "branch_id": t.base.branch},
    )
    assert issued.status_code == 201
    row = candidate(t, t.login).json()
    destination = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "GC", "name": "GC destination"},
    ).json()["id"]
    with t.base.db.engine.begin() as writer:
        if retirement == "expired":
            writer.execute(text(source_deadline_sql("0 seconds")))
        else:
            writer.execute(text("UPDATE iam_operator_setup_credentials SET consumed=true"))
    nonce = csrf(t.base.client)
    payload = {
        "operation_id": str(uuid4()),
        "expected_account_version": row["account_version"],
        "expected_operator_version": 1,
        "branch_id": destination,
    }
    with ThreadPoolExecutor(max_workers=1) as pool:
        with t.base.db.session() as holder:
            source_row = holder.execute(
                text(
                    "SELECT id,branch_id,grant_version,expires_at FROM "
                    "iam_operator_setup_credentials WHERE account_id=:a FOR UPDATE"
                ),
                {"a": row["account_id"]},
            ).one()
            pid = holder.scalar(text("SELECT pg_backend_pid()"))
            with t.base.db.session() as gc:
                Security(gc, "synthetic", 2048, 128)._guard()
                assert gc.scalar(text("SELECT count(*) FROM iam_operator_setup_credentials")) == 1
                assert (
                    gc.scalar(
                        text("SELECT count(*) FROM iam_security_states WHERE id=:i"),
                        {"i": source_row.id},
                    )
                    == 1
                )
                gc.commit()
            future = pool.submit(
                call, t.base.client, BASE + "/" + row["account_id"] + "/branch", nonce, payload
            )
            try:
                from time import monotonic, sleep

                end = monotonic() + 1.5
                waiters: list[int] = []
                while monotonic() < end and not waiters:
                    waiters = list(
                        holder.execute(
                            text(
                                "SELECT pid FROM pg_stat_activity "
                                "WHERE :h=ANY(pg_blocking_pids(pid))"
                            ),
                            {"h": pid},
                        ).scalars()
                    )
                    if not waiters:
                        sleep(0.01)
                wait_for_owned_block(t.base.db, pid, waiters)
            finally:
                holder.rollback()
        assert future.result(timeout=5).status_code == 200
    with t.base.db.session() as reader:
        assert (
            reader.execute(
                text(
                    "SELECT id,branch_id,grant_version,expires_at FROM "
                    "iam_operator_setup_credentials WHERE account_id=:a"
                ),
                {"a": row["account_id"]},
            ).one()
            == source_row
        )
        security = Security(reader, "synthetic", 2048, 128)
        security.release(source_row.id, collect=False)
        assert (
            reader.scalar(
                text("SELECT count(*) FROM iam_security_states WHERE id=:i"), {"i": source_row.id}
            )
            == 1
        )
        security._guard()
        assert (
            reader.scalar(
                text("SELECT count(*) FROM iam_security_states WHERE id=:i"), {"i": source_row.id}
            )
            == 0
        )
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_grants")) == 1
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 1
        assert reader.scalar(text("SELECT count(*) FROM audit_operator_role_events")) == 1
        reader.commit()


@pytest.mark.parametrize(
    "boundary", ["pending", "disabled", "reset", "inactive_branch", "foreign_org"]
)
def test_first_operator_grant_enforces_readiness_and_assignment(
    trainer: TrainerScene, boundary: str
) -> None:
    from tests.password_helpers import reset_request
    from tests.test_account_lifecycle import mutate

    t = trainer
    issued = t.issue()
    assert issued.status_code == 201
    if boundary != "pending":
        assert t.complete(source(issued)).status_code == 204
    row = candidate(t, t.login).json()
    if boundary == "disabled":
        managed = call(
            t.base.client,
            "/admin/account-lifecycle/lookup",
            csrf(t.base.client),
            {"login_id": t.login},
        ).json()
        assert mutate(t, managed, "status", status="DISABLED").status_code == 200
        row = candidate(t, t.login).json()
    if boundary == "reset":
        assert reset_request(t.base.client, row["account_id"]).status_code == 201
        row = candidate(t, t.login).json()
    if boundary == "inactive_branch":
        with t.base.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:b"
                ),
                {"b": t.base.branch},
            )
    if boundary == "foreign_org":
        with t.base.db.engine.begin() as db:
            org, branch = uuid4(), uuid4()
            db.execute(
                text("INSERT INTO organization_organizations(id,name) VALUES(:i,:n)"),
                {"i": org, "n": "Foreign synthetic"},
            )
            db.execute(
                text(
                    "INSERT INTO organization_branches(id,organization_id,code,name) "
                    "VALUES(:i,:o,:c,:n)"
                ),
                {"i": branch, "o": org, "c": "FOREIGN", "n": "Foreign synthetic"},
            )
        row["branch_id"] = str(branch)
    result = command(t, row)
    assert result.status_code == (404 if boundary == "foreign_org" else 409)
    with t.base.db.session() as reader:
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_grants")) == 0
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 0


@pytest.mark.parametrize("withdrawn", [False, True])
def test_ba_role_scope_receipt_and_self_reauthentication(
    trainer: TrainerScene, password_app: Any, withdrawn: bool
) -> None:
    from tests.password_helpers import login_password
    from tests.test_workforce import Scene
    from tests.test_workforce_integrity import branch_actor

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    master = t.base.client
    destination = call(
        master, "/admin/branches", csrf(master), {"code": "BADEST", "name": "Destination"}
    ).json()["id"]
    with closing(branch_actor(t.base, password_app[2])) as ba:
        bt = TrainerScene(
            Scene(ba, t.base.db, t.base.branch), t.trainer, t.recipient, t.password, t.login
        )
        first = command(bt, candidate(bt, t.login).json())
        assert first.status_code == 200
        op = first.json()["operation_id"]
        assert role_get(master, "/api/v1/admin/operator-role-operations/" + op).status_code == 404
        revoked = command(bt, first.json()["current"], False)
        assert revoked.status_code == 200
        assert candidate(bt, t.login, destination).json()["branch_id"] == t.base.branch
        wrong = {**revoked.json()["current"], "branch_id": destination}
        assert command(bt, wrong).status_code == 409
        assert command(bt, revoked.json()["current"], move=destination).status_code == 403
        regrant = command(bt, revoked.json()["current"])
        assert regrant.status_code == 200
        assert role_get(ba, "/api/v1/admin/operator-role-operations/" + op).status_code == 200
        current = regrant.json()["current"]
        if withdrawn:
            revoked = command(bt, current, False)
            assert revoked.status_code == 200
            current = revoked.json()["current"]
        moved = command(t, current, move=destination)
        assert moved.status_code == 200 and moved.json()["granted"] is (not withdrawn)
        assert candidate(bt, t.login, t.base.branch).status_code == 404
        assert role_get(ba, "/api/v1/admin/operator-role-operations/" + op).status_code == 404
        assert command(bt, moved.json()["current"], False).status_code == 404
        result = command(bt, candidate(bt, "workforce.branch").json())
        assert result.status_code == 200 and result.json()["reauthentication_required"]
        assert ba.get("/api/v1/auth/me").status_code == 401
        login_password(ba, password_app[2], "workforce.branch")
        assert (
            role_get(
                ba, "/api/v1/admin/operator-role-operations/" + result.json()["operation_id"]
            ).status_code
            == 200
        )


def test_operator_expected_actor_precondition_all_routes(
    trainer: TrainerScene, password_app: Any
) -> None:
    from tests.test_workforce_integrity import branch_actor

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    a = t.base.client
    expected_a = role_headers(a)["X-Y3-Expected-Actor"]
    first = command(t, candidate(t, t.login).json())
    assert first.status_code == 200
    row = first.json()["current"]
    with closing(branch_actor(t.base, password_app[2])) as b:
        headers = {
            "Origin": str(b.base_url).rstrip("/"),
            "X-CSRF-Token": csrf(b),
            "X-Y3-Expected-Actor": expected_a,
        }
        ident = row["account_id"]
        body = {
            "operation_id": str(uuid4()),
            "expected_account_version": row["account_version"],
            "expected_operator_version": row["operator_grant"]["scope"]["version"],
            "branch_id": t.base.branch,
        }
        for method, path, payload in [
            ("POST", BASE + "/lookup", {"login_id": t.login, "branch_id": t.base.branch}),
            ("GET", BASE + "/" + ident, None),
            ("POST", BASE + "/" + ident + "/changes", {**body, "desired_granted": False}),
            ("POST", BASE + "/" + ident + "/branch", body),
            ("GET", "/admin/operator-role-operations/" + first.json()["operation_id"], None),
        ]:
            assert (
                b.request(method, "/api/v1" + path, headers=headers, json=payload).status_code
                == 409
            )
            for invalid in [None, "not-a-uuid"]:
                bad = {k: v for k, v in headers.items() if k != "X-Y3-Expected-Actor"}
                if invalid:
                    bad["X-Y3-Expected-Actor"] = invalid
                assert (
                    b.request(method, "/api/v1" + path, headers=bad, json=payload).status_code
                    == 422
                )
        assert (
            role_get(
                b, "/api/v1/admin/operator-role-operations/" + first.json()["operation_id"]
            ).status_code
            == 404
        )
        assert role_get(b, "/api/v1" + BASE + "/" + ident).status_code == 200
    with t.base.db.session() as reader:
        assert reader.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 1
        assert reader.scalar(text("SELECT count(*) FROM audit_operator_role_events")) == 1
        assert reader.scalar(text("SELECT version FROM iam_operator_grants")) == 1


@pytest.mark.parametrize("kind", ["revoke", "regrant", "move"])
@pytest.mark.parametrize("invalid", ["null_branch", "zero_version"])
def test_operator_noninitial_audit_requires_prior_grant(
    trainer: TrainerScene, kind: str, invalid: str
) -> None:
    from sqlalchemy.exc import IntegrityError

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert command(t, candidate(t, t.login).json()).status_code == 200
    dest = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "AUDDEST", "name": "Destination"},
    ).json()["id"]
    with t.base.db.session() as db:
        row = dict(db.execute(text("SELECT * FROM audit_operator_role_events")).mappings().one())
        # Retain valid receipt identity; only the typed before-state is invalid.
        db.execute(text("DELETE FROM audit_operator_role_events"))
        row.update(
            kind=kind,
            before_branch=row["after_branch"],
            before_version=1,
            after_version=2,
            before_granted=kind != "regrant",
            after_granted=kind != "revoke",
        )
        if kind == "move":
            row["after_branch"] = UUID(dest)
        if invalid == "null_branch":
            row["before_branch"] = None
        else:
            row.update(before_version=0, after_version=1)
        with pytest.raises(IntegrityError) as error:
            db.execute(
                text(
                    "INSERT INTO audit_operator_role_events ("
                    + ",".join(row)
                    + ") VALUES ("
                    + ",".join(":" + k for k in row)
                    + ")"
                ),
                row,
            )
        assert getattr(error.value.orig, "sqlstate", None) == "23514"
        db.rollback()


@pytest.mark.parametrize("cause", ["admin_auth", "source_branch"])
def test_operator17_isolated_synthetic_loss_guards(trainer: TrainerScene, cause: str) -> None:
    """Synthetic migration input, not public mixed-role login reachability."""
    from tests.legacy_helpers import assert_revision_loss_guard
    from tests.test_account_lifecycle import lifecycle_fingerprints

    t = trainer
    issued = call(
        t.base.client,
        "/admin/operator-accounts",
        csrf(t.base.client),
        {"login_id": t.login, "branch_id": t.base.branch},
    )
    assert issued.status_code == 201
    destination = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "LOSS", "name": "Synthetic destination"},
    ).json()["id"]
    query = (
        "SELECT conrelid::regclass::text,conname,pg_get_constraintdef(oid) "
        "FROM pg_constraint WHERE connamespace=current_schema()::regnamespace ORDER BY 1,2"
    )
    with t.base.db.session() as db:
        if cause == "admin_auth":
            original = dict(
                db.execute(text("SELECT * FROM audit_operator_account_events")).mappings().one()
            )
            original.update(
                id=uuid4(),
                kind="login",
                actor_id=original["account_id"],
                actor_role="MASTER",
                actor_branch=None,
                before_state="ACTIVE",
                after_state="ACTIVE",
                before_version=1,
                after_version=1,
            )
            db.execute(
                text(
                    "INSERT INTO audit_operator_account_events ("
                    + ",".join(original)
                    + ") VALUES ("
                    + ",".join(":" + k for k in original)
                    + ")"
                ),
                original,
            )
        else:
            db.execute(
                text("UPDATE iam_operator_grants SET branch_id=:b,version=version+1"),
                {"b": destination},
            )
        db.commit()
        assert db.scalar(text("SELECT count(*) FROM iam_operator_role_operations")) == 0
        assert db.scalar(text("SELECT count(*) FROM audit_operator_role_events")) == 0
        auth = db.scalar(
            text(
                "SELECT count(*) FROM audit_operator_account_events "
                "WHERE kind='login' AND actor_role='MASTER'"
            )
        )
        snapshots = db.scalar(
            text(
                "SELECT count(*) FROM iam_operator_setup_credentials c "
                "JOIN iam_operator_grants g USING(account_id) "
                "WHERE c.branch_id<>g.branch_id"
            )
        )
        assert (auth, snapshots) == ((1, 0) if cause == "admin_auth" else (0, 1))
        shape = db.execute(text(query)).all()
    from tests.legacy_helpers import prepare_revision_guard

    with t.base.db.engine.begin() as connection:
        prepare_revision_guard(connection, "0017_operator_management")
    with t.base.db.session() as db:
        shape = db.execute(text(query)).all()
    before = lifecycle_fingerprints(t.base.db)
    from sqlalchemy import event

    ddl: list[str] = []

    def observe(_c: Any, _cursor: Any, statement: str, *_args: Any) -> None:
        if statement.lstrip().split()[0].upper() in {"DROP", "ALTER", "CREATE"}:
            ddl.append(statement)

    event.listen(t.base.db.engine, "before_cursor_execute", observe)
    try:
        assert_revision_loss_guard(
            t.base.db, "0017_operator_management.py", "OPERATOR_MANAGEMENT_HISTORY_PRESENT"
        )
    finally:
        event.remove(t.base.db.engine, "before_cursor_execute", observe)
    assert ddl == []
    assert lifecycle_fingerprints(t.base.db) == before
    with t.base.db.session() as db:
        assert db.execute(text(query)).all() == shape
