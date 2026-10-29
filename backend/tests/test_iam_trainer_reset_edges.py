# ruff: noqa: F811
"""Trainer reset final source checks, concurrency and real commit acknowledgement loss."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token
from tests.test_iam_password_reset import complete, fingerprint, reset_request
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_iam_trainer_reset import ready
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected
from y3management.iam.mfa import MFA

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("action", ["start", "reissue", "complete"])
@pytest.mark.parametrize("failure", ["audit", "ack"])
def test_trainer_reset_atomicity(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, action: str, failure: str
) -> None:
    t = trainer
    ident = ready(t)
    token = ""
    if action != "start":
        token = link_token(reset_request(t.base.client, ident).json()["reset_link"])
    state = t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset").json()
    client = t.recipient if action == "complete" else t.base.client
    nonce = csrf(client)
    before = fingerprint(t.base.db)
    append, commit = Audit.append, Session.commit

    def audit(adapter: Audit, event: Any) -> None:
        if event.action == "password_reset_" + action:
            if failure == "audit":
                raise Rejected(503, "unavailable")
            adapter.s.info["trainer_reset_ack"] = True
        append(adapter, event)

    def acknowledged(session: Session) -> None:
        commit(session)
        if session.info.pop("trainer_reset_ack", False):
            raise OperationalError("synthetic acknowledgement loss", {}, RuntimeError("lost"))

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", audit)
        patch.setattr(Session, "commit", acknowledged)
        response = (
            call(
                client,
                "/auth/password-reset/complete",
                nonce,
                {"reset_token": token, "new_password": t.password},
            )
            if action == "complete"
            else call(
                client,
                f"/admin/accounts/{ident}/password-reset"
                + ("/reissue" if action == "reissue" else ""),
                nonce,
                {
                    "expected_account_version": state["account_version"],
                    "expected_generation": state["generation"],
                    "identity_confirmed": True,
                },
            )
        )
    assert response.status_code == 503
    if failure == "audit":
        assert fingerprint(t.base.db) == before
    else:
        assert response.json() == {"detail": "commit_outcome_unknown"}
        with t.base.db.session() as s:
            assert s.execute(
                text("SELECT password_reset_pending FROM iam_accounts WHERE id=:a"), {"a": ident}
            ).scalar_one() is (action != "complete")
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_events WHERE target_id=:a AND action=:act"),
                    {"a": ident, "act": "password_reset_" + action},
                ).scalar_one()
                == 1
            )
        if action == "complete":
            assert complete(t.recipient, token, t.password).status_code == 401
            assert t.signin().status_code == 204
        else:
            fresh = reset_request(t.base.client, ident, reissue=True)
            assert fresh.status_code == 201
            assert (
                complete(
                    t.recipient, link_token(fresh.json()["reset_link"]), t.password
                ).status_code
                == 204
            )


def test_two_prepared_completions_consume_once(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    ident = ready(t)
    token = link_token(reset_request(t.base.client, ident).json()["reset_link"])
    barrier = Barrier(2)
    original = MFA.prepare_reset

    def prepare(adapter: MFA, raw: str, password: str) -> Any:
        proof = original(adapter, raw, password)
        barrier.wait(timeout=10)
        return proof

    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as other:
        nonces = [csrf(t.recipient), csrf(other)]

        def finish(pair: tuple[TestClient, str]) -> int:
            client, nonce = pair
            return int(
                call(
                    client,
                    "/auth/password-reset/complete",
                    nonce,
                    {"reset_token": token, "new_password": t.password},
                ).status_code
            )

        with monkeypatch.context() as patch:
            patch.setattr(MFA, "prepare_reset", prepare)
            with ThreadPoolExecutor(max_workers=2) as pool:
                statuses = list(pool.map(finish, [(t.recipient, nonces[0]), (other, nonces[1])]))
    assert sorted(statuses) == [204, 401]
    with t.base.db.session() as s:
        assert (
            s.execute(
                text(
                    "SELECT count(*) FROM audit_events WHERE target_id=:a AND "
                    "action='password_reset_complete'"
                ),
                {"a": ident},
            ).scalar_one()
            == 1
        )
    assert t.signin().status_code == 204


def test_hash_expiry_gc_and_inactive_home(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    ident = ready(t)
    with t.base.db.session() as s:
        s.execute(
            text(
                "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                "WHERE id=:b"
            ),
            {"b": t.base.branch},
        )
        s.commit()
    issued = reset_request(t.base.client, ident)
    assert issued.status_code == 201
    token = link_token(issued.json()["reset_link"])
    original = MFA.prepare_reset

    def expired(adapter: MFA, raw: str, password: str) -> Any:
        proof = original(adapter, raw, password)
        with t.base.db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_reset_credentials SET "
                    "expires_at=clock_timestamp()-interval '1 second' WHERE account_id=:a"
                ),
                {"a": ident},
            )
            s.commit()
        return proof

    with monkeypatch.context() as patch:
        patch.setattr(MFA, "prepare_reset", expired)
        assert complete(t.recipient, token, t.password).status_code == 401
    # Existing preparation performs GC; neither expiry nor GC restores the old password.
    csrf(t.recipient)
    state = t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset").json()
    assert state["password_reset_pending"] is True
    assert state["expires_at"] is None
    assert t.signin().status_code == 401
    fresh = reset_request(t.base.client, ident, reissue=True)
    assert fresh.status_code == 201
    assert (
        complete(t.recipient, link_token(fresh.json()["reset_link"]), t.password).status_code == 204
    )
    assert t.signin().status_code == 204


def test_branch_admin_cannot_reset_issued_trainer(
    trainer: TrainerScene, mfa: tuple[Any, Any, str, str]
) -> None:
    t = trainer
    ident = ready(t)
    with closing(branch_actor(t.base, mfa[2])) as branch:
        state = t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset").json()
        assert branch.get(f"/api/v1/admin/accounts/{ident}/password-reset").status_code == 403
        assert (
            call(
                branch,
                f"/admin/accounts/{ident}/password-reset",
                csrf(branch),
                {
                    "expected_account_version": state["account_version"],
                    "expected_generation": state["generation"],
                    "identity_confirmed": True,
                },
            ).status_code
            == 403
        )
    assert reset_request(t.base.client, ident).status_code == 201


def test_c3_prepared_hash_cannot_undo_trainer_reset(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.iam.infrastructure import IAM

    t = trainer
    ident = ready(t)
    assert t.signin().status_code == 204
    original = IAM.prepare_password_change
    issued = []

    def prepare(adapter: IAM, account: Any, current: str, new: str) -> Any:
        proof = original(adapter, account, current, new)
        response = reset_request(t.base.client, ident)
        assert response.status_code == 201
        issued.append(link_token(response.json()["reset_link"]))
        return proof

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "prepare_password_change", prepare)
        assert (
            call(
                t.recipient,
                "/auth/password",
                csrf(t.recipient),
                {"current_password": t.password, "new_password": t.password},
            ).status_code
            == 401
        )
    assert len(issued) == 1
    with t.base.db.session() as s:
        assert s.execute(
            text(
                "SELECT password_hash IS NULL AND password_reset_pending FROM iam_accou"
                "nts WHERE id=:a"
            ),
            {"a": ident},
        ).scalar_one()
    assert complete(t.recipient, issued[0], t.password).status_code == 204


def test_confirm_actor_default_and_self_touch_restriction(trainer: TrainerScene) -> None:
    t = trainer
    service = cast(FastAPI, t.base.client.app).state.iam_service
    cookie = t.base.client.cookies.get("__Host-y3-auth")
    with service.uow.open() as w:
        auth = w.iam.authenticate(cookie, management=True, touch=False)
        snapshot = w.roles.snapshot(auth)
        w.roles.confirm_actor(snapshot, self_change=False)
        # No UPDATE may precede rejection; the snapshot remains usable afterward.
        with pytest.raises(ValueError, match="self-revoked"):
            w.roles.confirm_actor(snapshot, self_change=True, touch=True)
        w.roles.confirm_actor(snapshot, self_change=False)
    with t.base.db.session() as s:
        assert (
            s.execute(
                text("SELECT last_activity FROM iam_sessions WHERE id=:i"), {"i": auth.session_id}
            ).scalar_one()
            == snapshot.last_activity
        )


def test_bound_admin_keeps_uv_with_inactive_or_withdrawn_trainer(
    trainer: TrainerScene, mfa: tuple[Any, Any, str, str]
) -> None:
    from tests.test_iam_mfa import login_mfa
    from tests.test_iam_mfa_management_races import provision
    from tests.test_iam_trainer_roles import body as role_body
    from tests.test_iam_trainer_roles import change as role_change
    from tests.test_iam_trainer_roles_security import link
    from tests.test_workforce_state import change as state_change
    from tests.test_workforce_state import request as state_request

    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident, key = provision(t.base.client, target, mfa[2])
        assert role_change(t, link(t, ident, "second.master")).status_code == 200
        with t.base.db.session() as s:
            original_keys = s.execute(
                text("SELECT * FROM iam_passkeys WHERE account_id=:a"), {"a": ident}
            ).all()
        assert state_change(t, state_request(t, False)).status_code == 200
        for granted in (True, False):
            if not granted:
                assert role_change(t, role_body(t, False)).status_code == 200
            issued = reset_request(t.base.client, ident)
            assert issued.status_code == 201
            assert (
                complete(target, link_token(issued.json()["reset_link"]), mfa[2]).status_code == 204
            )
            login_mfa(target, mfa[2], key, "second.master")
            assert target.get("/api/v1/auth/me").json()["roles"] == [
                {"role": "ADMIN", "scope": "ORGANIZATION", "branch_id": None}
            ]
        with t.base.db.session() as s:
            # Counter/last-use can move during UV; key identities and revocation cannot.
            current_keys = s.execute(
                text("SELECT * FROM iam_passkeys WHERE account_id=:a"), {"a": ident}
            ).all()
            assert [row.key_id for row in current_keys] == [row.key_id for row in original_keys]
            assert all(row.revoked_at is None for row in current_keys)


def test_no_admin_no_binding_is_unsupported_and_db_failure_is_not_401(
    trainer: TrainerScene, mfa: tuple[Any, Any, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_iam_mfa_management_races import provision
    from y3management.iam.infrastructure import IAM

    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident, _ = provision(t.base.client, target, mfa[2])
        token = link_token(reset_request(t.base.client, ident).json()["reset_link"])
        with t.base.db.session() as s:
            organization = s.execute(
                text("SELECT organization_id FROM iam_accounts WHERE id=:a"), {"a": ident}
            ).scalar_one()
            s.execute(text("DELETE FROM iam_admin_grants WHERE account_id=:a"), {"a": ident})
            s.commit()
        assert (
            t.base.client.get(f"/api/v1/admin/accounts/{ident}/password-reset").status_code == 404
        )
        assert complete(target, token, mfa[2]).status_code == 401
        with t.base.db.session() as s:
            s.execute(
                text("INSERT INTO iam_admin_grants VALUES(:a,:o,'ORGANIZATION',NULL)"),
                {"a": ident, "o": organization},
            )
            s.commit()
        original = IAM.account_roles

        def unavailable(adapter: IAM, account: Any) -> Any:
            if str(account) == ident:
                raise OperationalError(
                    "synthetic database unavailable", {}, RuntimeError("unavailable")
                )
            return original(adapter, account)

        nonce = csrf(target)
        with monkeypatch.context() as patch:
            patch.setattr(IAM, "account_roles", unavailable)
            assert (
                call(
                    target,
                    "/auth/password-reset/complete",
                    nonce,
                    {"reset_token": token, "new_password": mfa[2]},
                ).status_code
                == 503
            )
        assert complete(target, token, mfa[2]).status_code == 204
