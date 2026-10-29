# ruff: noqa: F811
"""Reset final checks use the original deadline after all actor facts and audit."""

from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import text

from tests.test_iam import csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_password_reset import fingerprint, reset_request
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_iam_trainer_reset import ready
from tests.test_workforce import scene  # noqa: F401
from y3management.audit.infrastructure import Audit
from y3management.iam.infrastructure import IAM
from y3management.iam.roles import TrainerRoles

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("operation", ["get", "start", "reissue"])
@pytest.mark.parametrize("clock", ["idle", "absolute"])
def test_final_actor_deadline_after_last_fact_rolls_back(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, operation: str, clock: str
) -> None:
    t = trainer
    ident = ready(t)
    if operation == "reissue":
        assert reset_request(t.base.client, ident).status_code == 201
    path = f"/admin/accounts/{ident}/password-reset"
    state = t.base.client.get("/api/v1" + path).json()
    nonce = csrf(t.base.client)
    with t.base.db.session() as s:
        sid = s.execute(
            text(
                "SELECT id FROM iam_sessions WHERE account_id=(SELECT id FROM iam_accounts "
                "WHERE login_id='master.test') AND NOT revoked"
            )
        ).scalar_one()
        if clock == "absolute":
            s.execute(
                text("""WITH shifted AS (UPDATE iam_security_states
                SET expires_at=clock_timestamp()+interval '1 minute' WHERE id=:id
                RETURNING id,expires_at)
                UPDATE iam_sessions s SET expires_at=shifted.expires_at,
                created_at=shifted.expires_at-interval '8 hours'
                FROM shifted WHERE s.id=shifted.id"""),
                {"id": sid},
            )
        activity, expiry = s.execute(
            text("SELECT last_activity,expires_at FROM iam_sessions WHERE id=:id"), {"id": sid}
        ).one()
        s.commit()
    final_time = activity + timedelta(minutes=30) if clock == "idle" else expiry
    assert (
        (final_time < expiry)
        if clock == "idle"
        else (final_time < activity + timedelta(minutes=30))
    )
    before = fingerprint(t.base.db)
    original_stable, original_now, original_audit = TrainerRoles.stable_actor, IAM.now, Audit.append
    reads = 0
    audited = False

    def stable(adapter: TrainerRoles, auth: Any) -> bytes:
        nonlocal reads
        value = original_stable(adapter, auth)
        reads += 1
        if reads == 2 and operation != "get":
            assert audited
        return value

    def now(adapter: IAM) -> Any:
        return final_time if reads >= 2 else original_now(adapter)

    def audit(adapter: Audit, event: Any) -> None:
        nonlocal audited
        original_audit(adapter, event)
        audited = True

    with monkeypatch.context() as patch:
        patch.setattr(TrainerRoles, "stable_actor", stable)
        patch.setattr(IAM, "now", now)
        patch.setattr(Audit, "append", audit)
        response = (
            t.base.client.get("/api/v1" + path)
            if operation == "get"
            else call(
                t.base.client,
                path + ("/reissue" if operation == "reissue" else ""),
                nonce,
                {
                    "expected_account_version": state["account_version"],
                    "expected_generation": state["generation"],
                    "identity_confirmed": True,
                },
            )
        )
    assert response.status_code == 401 and reads == 2
    assert fingerprint(t.base.db) == before
    with t.base.db.session() as s:
        assert (
            s.execute(
                text("SELECT last_activity FROM iam_sessions WHERE id=:id"), {"id": sid}
            ).scalar_one()
            == activity
        )
    # Positive control: the very same current state is usable before the original deadline.
    response = (
        t.base.client.get("/api/v1" + path)
        if operation == "get"
        else call(
            t.base.client,
            path + ("/reissue" if operation == "reissue" else ""),
            nonce,
            {
                "expected_account_version": state["account_version"],
                "expected_generation": state["generation"],
                "identity_confirmed": True,
            },
        )
    )
    assert response.status_code == (200 if operation == "get" else 201)


@pytest.mark.parametrize("operation", ["get", "start", "reissue"])
def test_success_touches_exact_final_clock(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    t = trainer
    ident = ready(t)
    if operation == "reissue":
        assert reset_request(t.base.client, ident).status_code == 201
    path = f"/admin/accounts/{ident}/password-reset"
    state = t.base.client.get("/api/v1" + path).json()
    nonce = csrf(t.base.client)
    original_stable, original_now = TrainerRoles.stable_actor, IAM.now
    reads = 0
    final_ticks = []

    def stable(adapter: TrainerRoles, auth: Any) -> bytes:
        nonlocal reads
        value = original_stable(adapter, auth)
        reads += 1
        return value

    def now(adapter: IAM) -> Any:
        value = original_now(adapter)
        if reads >= 2:
            final_ticks.append(value)
        return value

    with monkeypatch.context() as patch:
        patch.setattr(TrainerRoles, "stable_actor", stable)
        patch.setattr(IAM, "now", now)
        result = (
            t.base.client.get("/api/v1" + path)
            if operation == "get"
            else call(
                t.base.client,
                path + ("/reissue" if operation == "reissue" else ""),
                nonce,
                {
                    "expected_account_version": state["account_version"],
                    "expected_generation": state["generation"],
                    "identity_confirmed": True,
                },
            )
        )
    assert result.status_code == (200 if operation == "get" else 201)
    assert reads == 2 and len(final_ticks) == 1
    with t.base.db.session() as s:
        assert (
            s.execute(
                text(
                    "SELECT last_activity FROM iam_sessions WHERE account_id=(SELECT id "
                    "FROM iam_accounts WHERE login_id='master.test') AND NOT revoked"
                )
            ).scalar_one()
            == final_ticks[0]
        )
