# ruff: noqa: F811
"""Bound Trainer reset is credential repair, not restoration of business access."""

import secrets
from contextlib import closing
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token
from tests.test_iam_password_reset import complete, fingerprint, reset_request
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body as role_body
from tests.test_iam_trainer_roles import change as role_change
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_state import change as state_change
from tests.test_workforce_state import request as state_request
from y3management.contracts import Rejected
from y3management.iam.mfa import MFA

pytestmark = pytest.mark.postgres


def ready(t: TrainerScene) -> str:
    assert t.complete(source(t.issue())).status_code == 204
    return str(t.state()["account_id"])


def preserved(t: TrainerScene) -> tuple[Any, ...]:
    with t.base.db.session() as s:
        return tuple(
            s.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all()
            for table in (
                "iam_trainer_bindings",
                "iam_trainer_role_grants",
                "iam_passkeys",
                "iam_admin_grants",
                "workforce_trainers",
                "workforce_initial_snapshots",
            )
        )


@pytest.mark.parametrize(
    "active,granted", [(True, True), (False, True), (True, False), (False, False)]
)
def test_bound_trainer_credential_repair_state_matrix(
    trainer: TrainerScene, active: bool, granted: bool
) -> None:
    t = trainer
    ident = ready(t)
    assert t.signin().status_code == 204
    old_cookie = SyntheticSecret(t.recipient.cookies.get("__Host-y3-auth") or "")
    if not granted:
        assert role_change(t, role_body(t, False)).status_code == 200
    if not active:
        assert state_change(t, state_request(t, False)).status_code == 200
    before = preserved(t)
    issued = reset_request(t.base.client, ident)
    assert issued.status_code == 201
    token = link_token(issued.json()["reset_link"])
    assert t.signin().status_code == 401
    assert (
        t.recipient.get(
            "/api/v1/auth/me", headers={"Cookie": "__Host-y3-auth=" + old_cookie}
        ).status_code
        == 401
    )
    new = SyntheticSecret(secrets.token_urlsafe(24))
    assert complete(t.recipient, token, new).status_code == 204
    assert not t.recipient.cookies.get("__Host-y3-auth")
    assert complete(t.recipient, token, new).status_code == 401
    assert preserved(t) == before
    assert t.signin(password=new).status_code == (204 if active and granted else 401)
    if not active:
        assert state_change(t, state_request(t, True)).status_code == 200
    if not granted:
        assert role_change(t, role_body(t, True)).status_code == 200
    if not (active and granted):
        assert t.signin(password=new).status_code == 204
    assert t.recipient.get("/api/v1/auth/passkeys").status_code == 401
    assert call(t.recipient, "/auth/passkeys/options", csrf(t.recipient), {}).status_code == 401
    with t.base.db.session() as s:
        assert (
            s.execute(
                text("SELECT count(*) FROM iam_passkeys WHERE account_id=:a"), {"a": ident}
            ).scalar_one()
            == 0
        )
        assert (
            s.execute(
                text(
                    "SELECT count(*) FROM audit_events WHERE target_id=:a AND action LIKE "
                    "'password_reset_%'"
                ),
                {"a": ident},
            ).scalar_one()
            == 2
        )


def test_pending_disabled_self_and_mfa_boundaries(trainer: TrainerScene) -> None:
    t = trainer
    token = source(t.issue())
    ident = str(t.state()["account_id"])
    assert t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset").status_code == 409
    assert t.complete(token).status_code == 204
    assert t.signin().status_code == 204
    # A Trainer recipient is not an administrator for any normal MFA/recovery path.
    assert t.recipient.get(f"/api/v1/admin/accounts/{ident}/password-reset").status_code == 401
    assert t.base.client.get(f"/api/v1/admin/accounts/{ident}/passkey-recovery").status_code == 404
    master = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    assert t.base.client.get(f"/api/v1/admin/accounts/{master}/password-reset").status_code == 404
    with t.base.db.session() as s:
        s.execute(
            text(
                "UPDATE iam_accounts SET "
                "state='DISABLED',row_version=row_version+1,security_version=security_v"
                "ersion+1 WHERE id=:a"
            ),
            {"a": ident},
        )
        s.commit()
    assert t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset").status_code == 409


def test_reset_source_survives_w1_and_rejects_old_role_proof(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    ident = ready(t)
    issued = reset_request(t.base.client, ident)
    token = link_token(issued.json()["reset_link"])
    with t.base.db.session() as s:
        original = s.execute(
            text("SELECT * FROM iam_reset_credentials WHERE account_id=:a"), {"a": ident}
        ).all()
    assert state_change(t, state_request(t, False)).status_code == 200
    assert state_change(t, state_request(t, True)).status_code == 200
    with t.base.db.session() as s:
        assert (
            s.execute(
                text("SELECT * FROM iam_reset_credentials WHERE account_id=:a"), {"a": ident}
            ).all()
            == original
        )
    original_prepare = MFA.prepare_reset
    new = SyntheticSecret(secrets.token_urlsafe(24))

    def prepare(adapter: MFA, raw: str, password: str) -> Any:
        proof = original_prepare(adapter, raw, password)
        assert role_change(t, role_body(t, False)).status_code == 200
        assert role_change(t, role_body(t, True)).status_code == 200
        return proof

    with monkeypatch.context() as patch:
        patch.setattr(MFA, "prepare_reset", prepare)
        assert complete(t.recipient, token, new).status_code == 401
    with t.base.db.session() as s:
        assert (
            s.execute(
                text("SELECT * FROM iam_reset_credentials WHERE account_id=:a"), {"a": ident}
            ).all()
            == original
        )
    assert complete(t.recipient, token, new).status_code == 204
    assert t.signin(password=new).status_code == 204


def test_trainer_reset_audit_rollback_and_reissue(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.audit.infrastructure import Audit

    t = trainer
    ident = ready(t)
    before = fingerprint(t.base.db)
    original = Audit.append

    def deny(adapter: Audit, event: Any) -> None:
        if event.action == "password_reset_start":
            raise Rejected(503, "unavailable")
        original(adapter, event)

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", deny)
        assert reset_request(t.base.client, ident).status_code == 503
    assert fingerprint(t.base.db) == before
    assert t.signin().status_code == 204
    old = link_token(reset_request(t.base.client, ident).json()["reset_link"])
    fresh = link_token(reset_request(t.base.client, ident, reissue=True).json()["reset_link"])
    assert complete(t.recipient, old, t.password).status_code == 401
    assert complete(t.recipient, fresh, t.password).status_code == 204


def test_trainer_reset_two_sessions_immediately_revoked(trainer: TrainerScene) -> None:
    t = trainer
    ident = ready(t)
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as second:
        assert t.signin().status_code == 204
        assert t.signin(second).status_code == 204
        assert reset_request(t.base.client, ident).status_code == 201
        for client in (t.recipient, second):
            assert client.get("/api/v1/auth/me").status_code == 401
    with t.base.db.session() as s:
        assert (
            s.execute(
                text("SELECT bool_and(revoked) FROM iam_sessions WHERE account_id=:a"),
                {"a": UUID(ident)},
            ).scalar_one()
            is True
        )
