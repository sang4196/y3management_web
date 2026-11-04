# ruff: noqa: F811
"""Durable variant constraints, preservation and commit reconciliation."""

import hashlib
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.legacy_helpers import (  # noqa: F401
    assert_revision_loss_guard,
    legacy_database,
    legacy_master,
    migration_status,
)
from tests.password_helpers import link_token
from tests.test_iam import csrf
from tests.test_iam_emergency import issue, request
from tests.test_iam_emergency_handoff import Scene, scene  # noqa: F401
from tests.test_password_transition_legacy import seed_case
from y3management.config import Settings
from y3management.contracts import CommitUncertain
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_variants_nulls_parent_factors_and_history_downgrade(scene: Scene) -> None:
    original = scene.operating()
    body = scene.body()
    assert scene.send(body).status_code == 201
    operation = body["operation_id"]
    for field in ("issuer_account_id", "parent_id"):
        with scene.db.session() as db, pytest.raises(IntegrityError):
            db.execute(
                text(f"UPDATE iam_password_emergency_cases SET {field}=NULL WHERE id=:i"),
                {"i": operation},
            )
    for field in (
        "approval_ref",
        "owner_ref",
        "executor_ref",
        "executor_uid",
        "checked_at",
        "approval_valid_until",
    ):
        with scene.db.session() as db, pytest.raises(IntegrityError):
            db.execute(
                text(f"UPDATE iam_password_emergency_cases SET {field}=NULL WHERE id=:i"),
                {"i": original.operation_id},
            )
    for update in (
        "purpose='both'",
        "issuer_account_id=account_id",
        "approval_ref='fabricated'",
        "approval_mode='manual'",
        "parent_id=id",
    ):
        with scene.db.session() as db, pytest.raises(IntegrityError):
            db.execute(
                text(f"UPDATE iam_password_emergency_cases SET {update} WHERE id=:i"),
                {"i": operation},
            )
    for field in ("actor_id", "case_id", "approval_mode", "actor_role"):
        with scene.db.session() as db, pytest.raises(IntegrityError):
            db.execute(
                text(f"UPDATE audit_password_emergency_events SET {field}=NULL WHERE case_id=:i"),
                {"i": operation},
            )
    assert_revision_loss_guard(
        scene.db, "0014_password_only.py", "PASSWORD_DOWNGRADE_REQUIRES_GLOBAL_EMPTY"
    )
    assert scene.state()["operation_id"] == operation


@pytest.mark.parametrize("legacy_master", ["0009_iam_emergency_handoff"], indirect=True)
def test_operating_history_roundtrip(legacy_master: tuple[Settings, Database]) -> None:
    settings, db = legacy_master
    seed_case(db, factors="password")
    with db.session() as session:
        before = session.execute(
            text("SELECT row_to_json(c)::text FROM iam_emergency_cases c")
        ).scalar_one()
    assert migration_status(settings, "downgrade", "0008_iam_emergency_recovery") == 0
    assert migration_status(settings, "upgrade", "0009_iam_emergency_handoff") == 0
    with db.session() as session:
        assert (
            session.execute(
                text("SELECT row_to_json(c)::text FROM iam_emergency_cases c")
            ).scalar_one()
            == before
        )


def test_fresh_operating_reissue_after_handoff(scene: Scene) -> None:
    original = scene.operating()
    body = scene.body()
    assert scene.send(body).status_code == 201
    req = request(scene.service, scene.principal, scene.ident, UUID(body["operation_id"]))
    issue(scene.service, scene.principal, req)
    state = scene.state()
    assert state["issuer_kind"] == "operating" and state["factors"] == "password"
    assert scene.state(original.operation_id)["status"] == "superseded"


def preserved(scene: Scene) -> list[str]:
    with scene.db.session() as db:
        values = []
        for table in (
            "iam_accounts",
            "iam_admin_grants",
            "iam_login_ids",
            "iam_passkeys",
            "iam_credentials",
            "iam_recovery_credentials",
            "iam_reset_credentials",
            "iam_mfa_contexts",
        ):
            column = "id" if table == "iam_accounts" else "account_id"
            values.append(
                str(
                    db.execute(
                        text(
                            "SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                            "ORDER BY row_to_json(t)::text),'')) "
                            f"FROM {table} t WHERE {column}<>:a"
                        ),
                        {"a": scene.ident},
                    ).scalar_one()
                )
            )
        # Only the acting session's activity timestamp is an explicit allowed exception.
        values.append(
            str(
                db.execute(
                    text(
                        "SELECT md5(COALESCE(string_agg("
                        "(CASE WHEN digest=:d THEN to_jsonb(s)-'last_activity' "
                        "ELSE to_jsonb(s) END)::text,',' ORDER BY id),'')) "
                        "FROM iam_sessions s "
                        "WHERE account_id<>:a"
                    ),
                    {
                        "a": scene.ident,
                        "d": hashlib.sha256(
                            (scene.actor.cookies.get("__Host-y3-auth") or "").encode()
                        ).digest(),
                    },
                ).scalar_one()
            )
        )
        for table in ("iam_budgets", "iam_attempts"):
            values.append(
                str(
                    db.execute(
                        text(
                            "SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                            "ORDER BY row_to_json(t)::text),'')) "
                            f"FROM {table} t"
                        )
                    ).scalar_one()
                )
            )
        return values


def test_target_only_preservation_and_read_no_touch(scene: Scene) -> None:
    scene.operating()
    body = scene.body()
    nonce = csrf(scene.actor)
    before = preserved(scene)
    with scene.db.session() as db:
        activity = db.execute(
            text("SELECT last_activity FROM iam_sessions WHERE account_id=:a"),
            {"a": scene.actor_id},
        ).scalar_one()
    scene.state()
    with scene.db.session() as db:
        assert (
            db.execute(
                text("SELECT last_activity FROM iam_sessions WHERE account_id=:a"),
                {"a": scene.actor_id},
            ).scalar_one()
            == activity
        )
    assert scene.send(body, nonce).status_code == 201
    assert preserved(scene) == before


def test_commit_ack_loss_status_and_explicit_reissue(
    scene: Scene, monkeypatch: pytest.MonkeyPatch
) -> None:
    scene.operating()
    body = scene.body()
    nonce = csrf(scene.actor)
    original = Session.commit
    failed: list[bool] = []

    def commit(session: Session) -> None:
        hit = (
            session.execute(
                text("SELECT 1 FROM iam_password_emergency_cases WHERE id=:i"),
                {"i": body["operation_id"]},
            ).first()
            is not None
        )
        original(session)
        if hit and not failed:
            failed.append(True)
            raise CommitUncertain()

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", commit)
        response = scene.send(body, nonce)
    assert response.status_code == 503
    assert response.json()["detail"] == "commit_outcome_unknown"
    assert "recipient_link" not in response.json()
    assert scene.state(UUID(body["operation_id"]))["status"] == "issued"
    next_response = scene.send(scene.body())
    assert next_response.status_code == 201
    assert len(link_token(next_response.json()["recipient_link"])) >= 40
    assert scene.state(UUID(body["operation_id"]))["status"] == "superseded"


@pytest.mark.parametrize(
    "mutation",
    [
        "completed_at=issued_at",
        "row_version=row_version+1",
        "security_version=security_version+1",
        "reset_generation=reset_generation+1",
    ],
)
def test_durable_parent_semantics_checked_for_issuer_and_recipient(
    scene: Scene, mutation: str
) -> None:
    from tests.password_helpers import call

    original = scene.operating()
    issued = scene.send(scene.body())
    assert issued.status_code == 201
    token = link_token(issued.json()["recipient_link"])
    next_body = scene.body()
    with scene.db.session() as session:
        session.execute(
            text("UPDATE iam_password_emergency_cases SET " + mutation + " WHERE id=:i"),
            {"i": original.operation_id},
        )
        session.commit()
    assert scene.send(next_body).status_code == 409
    assert (
        call(
            scene.target,
            "/auth/emergency-recovery/password/complete",
            csrf(scene.target),
            {"emergency_token": token, "new_password": scene.password},
        ).status_code
        == 401
    )
    with scene.db.session() as session:
        assert (
            session.execute(
                text("SELECT password_reset_pending FROM iam_accounts WHERE id=:i"),
                {"i": scene.ident},
            ).scalar_one()
            is True
        )
