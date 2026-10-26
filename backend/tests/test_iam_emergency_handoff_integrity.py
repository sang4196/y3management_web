# ruff: noqa: F811
"""Durable variant constraints, preservation and commit reconciliation."""

import hashlib
import subprocess
import sys
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.test_iam import child_env, csrf
from tests.test_iam_emergency import issue, request
from tests.test_iam_emergency_handoff import Scene, scene  # noqa: F401
from tests.test_iam_mfa import mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token
from y3management.contracts import CommitUncertain

pytestmark = pytest.mark.postgres


def test_variants_nulls_parent_factors_and_history_downgrade(scene: Scene) -> None:
    original = scene.operating()
    body = scene.body()
    assert scene.send(body).status_code == 201
    operation = body["operation_id"]
    for field in (
        "issuer_account_id",
        "approval_origin_case_id",
        "handoff_parent_id",
        "supersedes",
    ):
        with scene.db.session() as db, pytest.raises(IntegrityError):
            db.execute(
                text(f"UPDATE iam_emergency_cases SET {field}=NULL WHERE id=:i"), {"i": operation}
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
                text(f"UPDATE iam_emergency_cases SET {field}=NULL WHERE id=:i"),
                {"i": original.operation_id},
            )
    for update in (
        "factors='password'",
        "issuer_account_id=account_id",
        "approval_ref='fabricated'",
        "approval_mode='manual'",
        "supersedes=id,handoff_parent_id=id",
    ):
        with scene.db.session() as db, pytest.raises(IntegrityError):
            db.execute(
                text(f"UPDATE iam_emergency_cases SET {update} WHERE id=:i"), {"i": operation}
            )
    for field in (
        "actor_id",
        "approval_origin_case_id",
        "previous_case_id",
        "handoff_kind",
        "approval_mode",
    ):
        with scene.db.session() as db, pytest.raises(IntegrityError):
            db.execute(
                text(f"UPDATE audit_events SET {field}=NULL WHERE emergency_case_id=:i"),
                {"i": operation},
            )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "0008_iam_emergency_recovery"],
        env=child_env(scene.service.uow.settings),
        capture_output=True,
        timeout=30,
    )
    assert result.returncode != 0
    # env.py deliberately suppresses database exception detail; verify retained revision/history.
    with scene.db.session() as db:
        assert (
            db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0011_iam_trainer_login"
        )
    assert scene.state()["operation_id"] == operation


def test_operating_history_roundtrip_and_fresh_operating_reissue(scene: Scene) -> None:
    original = scene.operating("password")
    for command in (("downgrade", "0008_iam_emergency_recovery"), ("upgrade", "head")):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *command],
            env=child_env(scene.service.uow.settings),
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, "Operating-only history migration roundtrip failed"
    body = scene.body()
    assert scene.send(body).status_code == 201
    # New current manual approval can change factor scope under the old operator contract.
    req = request(scene.service, scene.principal, scene.ident, "both", UUID(body["operation_id"]))
    issue(scene.service, scene.principal, req)
    state = scene.state()
    assert state["issuer_kind"] == "operating" and state["factors"] == "both"
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
                text("SELECT 1 FROM iam_emergency_cases WHERE id=:i"), {"i": body["operation_id"]}
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
