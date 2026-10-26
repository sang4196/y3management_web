# ruff: noqa: F811
"""Current authority, final database time and rollback of identity transitions."""

from contextlib import closing
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.test_iam import csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, counts, source, trainer  # noqa: F401
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerIdentityEvent
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_current_home_authority_and_no_login_id_reuse(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
) -> None:
    t = trainer
    with closing(branch_actor(t.base, mfa[2])) as other:
        path = "/admin/trainers/" + t.trainer + "/login-account"
        response = call(
            other, path, csrf(other), {"operation_id": str(uuid4()), "login_id": "master.test"}
        )
        assert response.status_code == 409 and counts(t) == (0, 0, 0, 0)
        response = call(
            other, path, csrf(other), {"operation_id": str(uuid4()), "login_id": t.login}
        )
        assert response.status_code == 201
        foreign = call(
            t.base.client,
            "/admin/branches",
            csrf(t.base.client),
            {"code": "I1OTHER", "name": "다른 가상 지점"},
        ).json()["id"]
        with t.base.db.session() as s:
            s.execute(
                text(
                    "UPDATE workforce_trainers SET home_branch_id=:h,"
                    "row_version=row_version+1 WHERE id=:i"
                ),
                {"h": foreign, "i": t.trainer},
            )
            s.commit()
        assert other.get("/api/v1" + path).status_code == 404
        assert (
            call(
                other,
                "/admin/trainers/" + t.trainer + "/initial-setup",
                csrf(other),
                {"operation_id": str(uuid4()), "expected_account_version": 1},
            ).status_code
            == 404
        )
        assert t.complete(source(t.reissue())).status_code == 204


@pytest.mark.parametrize("kind", ["setup_complete", "login", "password_change", "logout"])
def test_identity_audit_failure_rolls_back(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    t = trainer
    token = source(t.issue())
    if kind != "setup_complete":
        assert t.complete(token).status_code == 204
    if kind in ("password_change", "logout"):
        assert t.signin().status_code == 204
    original = Audit.append_trainer_identity

    def fail(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == kind:
            from y3management.contracts import Rejected

            raise Rejected(503, "unavailable")

    csrf(t.recipient)  # Settle disposable consumed-source GC before rollback baseline.
    before = counts(t)
    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append_trainer_identity", fail)
        if kind == "setup_complete":
            response = t.complete(token)
        elif kind == "login":
            response = t.signin()
        elif kind == "password_change":
            response = call(
                t.recipient,
                "/auth/password",
                csrf(t.recipient),
                {"current_password": t.password, "new_password": t.password + " changed"},
            )
        else:
            response = call(t.recipient, "/auth/logout", csrf(t.recipient), {})
        assert response.status_code == 503 and counts(t) == before
    if kind == "setup_complete":
        assert t.complete(token).status_code == 204
    elif kind == "login":
        assert t.recipient.get("/api/v1/auth/me").status_code == 401
    else:
        assert t.recipient.get("/api/v1/auth/me").status_code == 200


def test_source_actual_expiry_after_audit_rolls_back(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    t = trainer
    token = source(t.issue())
    nonce = csrf(t.recipient)
    with t.base.db.session() as s:
        expiry = s.execute(text("SELECT clock_timestamp()+interval '1.5 seconds'")).scalar_one()
        s.execute(text("UPDATE iam_trainer_setup_credentials SET expires_at=:e"), {"e": expiry})
        s.execute(
            text(
                "UPDATE iam_security_states SET expires_at=:e WHERE id IN "
                "(SELECT id FROM iam_trainer_setup_credentials)"
            ),
            {"e": expiry},
        )
        s.commit()
    original = Audit.append_trainer_identity
    observed: list[bool] = []

    def delay(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == "setup_complete":
            observed.append(
                bool(
                    self.s.execute(text("SELECT clock_timestamp()<:e"), {"e": expiry}).scalar_one()
                )
            )
            self.s.execute(text("SELECT pg_sleep(1.6)"))
            observed.append(
                bool(
                    self.s.execute(text("SELECT clock_timestamp()>:e"), {"e": expiry}).scalar_one()
                )
            )

    monkeypatch.setattr(Audit, "append_trainer_identity", delay)
    response = call(
        t.recipient,
        "/auth/trainer-credentials/complete",
        nonce,
        {"setup_token": token, "new_password": t.password},
    )
    assert response.status_code == 400 and observed == [True, True]
    assert t.state()["state"] == "PENDING_SETUP" and counts(t) == (1, 1, 1, 1)


def test_single_password_proof_and_reservation(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from y3management.iam.passwords import Passwords
    from y3management.iam.security import Security

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    calls = {"verify": 0, "reserve": 0}
    original_verify, original_reserve = Passwords.verify, Security.reserve

    def verify(self: Passwords, value: str, encoded: str | None) -> tuple[bool, str | None]:
        calls["verify"] += 1
        return original_verify(self, value, encoded)

    def reserve(self: Security, identifier: str) -> Any:
        calls["reserve"] += 1
        return original_reserve(self, identifier)

    monkeypatch.setattr(Passwords, "verify", verify)
    monkeypatch.setattr(Security, "reserve", reserve)
    assert t.signin().status_code == 204
    assert calls == {"verify": 1, "reserve": 1}


def test_admin_source_cannot_complete_trainer_setup(trainer: TrainerScene) -> None:
    t = trainer
    issued = call(
        t.base.client,
        "/admin/accounts",
        csrf(t.base.client),
        {"login_id": "purpose.branch", "branch_id": t.base.branch},
    )
    assert issued.status_code == 201
    from tests.test_iam import SyntheticSecret

    token = SyntheticSecret(issued.json()["setup_link"].split("#token=")[1])
    assert t.complete(token).status_code == 400
    assert counts(t) == (0, 0, 0, 0)


def test_oversized_setup_body_keeps_8192_budget(trainer: TrainerScene) -> None:
    response = call(
        trainer.recipient,
        "/auth/trainer-credentials/complete",
        csrf(trainer.recipient),
        {"setup_token": "secret-marker" * 4, "new_password": "secret-marker" * 1000},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "invalid_request"}


def test_all_issue_write_boundaries_rollback(trainer: TrainerScene) -> None:
    t = trainer
    for table in [
        "iam_accounts",
        "iam_login_ids",
        "iam_trainer_bindings",
        "iam_trainer_setup_credentials",
        "iam_trainer_account_operations",
        "audit_trainer_identity_events",
    ]:
        with t.base.db.session() as s:
            s.execute(
                text(
                    "CREATE OR REPLACE FUNCTION trainer_test_failure() RETURNS trigger "
                    "LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION "
                    "'synthetic persisted failure'; END $$"
                )
            )
            s.execute(
                text(
                    "CREATE TRIGGER trainer_test_failure BEFORE INSERT ON "
                    + table
                    + " FOR EACH ROW EXECUTE FUNCTION trainer_test_failure()"
                )
            )
            s.commit()
        assert t.issue().status_code == 503
        assert counts(t) == (0, 0, 0, 0)
        with t.base.db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_accounts WHERE login_id=:i"), {"i": t.login}
                ).scalar_one()
                == 0
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_login_ids WHERE login_id=:i"), {"i": t.login}
                ).scalar_one()
                == 0
            )
            s.execute(text("DROP TRIGGER trainer_test_failure ON " + table))
            s.commit()
    assert t.issue().status_code == 201


@pytest.mark.parametrize("kind", ["password_change", "logout"])
def test_self_transition_cannot_rescue_expired_session_after_audit(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204 and t.signin().status_code == 204
    nonce = csrf(t.recipient)
    with t.base.db.session() as s:
        expiry = s.execute(text("SELECT clock_timestamp()+interval '1.5 seconds'")).scalar_one()
        s.execute(
            text(
                "UPDATE iam_sessions SET created_at=CAST(:e AS timestamptz)-interval '31 minutes',"
                "last_activity=CAST(:e AS timestamptz)-interval '30 minutes' WHERE account_id IN "
                "(SELECT account_id FROM iam_trainer_bindings)"
            ),
            {"e": expiry},
        )
        before = s.execute(
            text(
                "SELECT a.row_version,a.security_version FROM iam_accounts a "
                "JOIN iam_trainer_bindings b ON b.account_id=a.id"
            )
        ).one()
        s.commit()
    original = Audit.append_trainer_identity
    observed: list[bool] = []

    def delay(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == kind:
            observed.append(
                bool(
                    self.s.execute(text("SELECT clock_timestamp()<:e"), {"e": expiry}).scalar_one()
                )
            )
            self.s.execute(text("SELECT pg_sleep(1.6)"))
            observed.append(
                bool(
                    self.s.execute(text("SELECT clock_timestamp()>:e"), {"e": expiry}).scalar_one()
                )
            )

    monkeypatch.setattr(Audit, "append_trainer_identity", delay)
    response = call(
        t.recipient,
        "/auth/password" if kind == "password_change" else "/auth/logout",
        nonce,
        {"current_password": t.password, "new_password": t.password + " changed"}
        if kind == "password_change"
        else {},
    )
    assert response.status_code in (401, 403) and observed == [True, True]
    with t.base.db.session() as s:
        assert (
            s.execute(
                text(
                    "SELECT a.row_version,a.security_version FROM iam_accounts a "
                    "JOIN iam_trainer_bindings b ON b.account_id=a.id"
                )
            ).one()
            == before
        )
        assert (
            s.execute(
                text("SELECT count(*) FROM audit_trainer_identity_events WHERE kind=:k"),
                {"k": kind},
            ).scalar_one()
            == 0
        )
        assert (
            s.execute(
                text(
                    "SELECT s.revoked FROM iam_sessions s JOIN iam_trainer_bindings b "
                    "ON b.account_id=s.account_id"
                )
            ).scalar_one()
            is False
        )
