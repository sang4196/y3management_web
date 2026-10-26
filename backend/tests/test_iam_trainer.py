# ruff: noqa: F811
"""Real W0-to-IAM lifecycle, current facts, replay and atomic identity audit."""

import secrets
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa  # noqa: F401
from tests.test_workforce import Scene, scene  # noqa: F401
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres


@dataclass
class TrainerScene:
    base: Scene
    trainer: str
    recipient: TestClient
    password: str
    login: str

    def issue(self, operation: str | None = None) -> Any:
        return call(
            self.base.client,
            "/admin/trainers/" + self.trainer + "/login-account",
            csrf(self.base.client),
            {"operation_id": operation or str(uuid4()), "login_id": self.login},
        )

    def complete(self, token: str) -> Any:
        return call(
            self.recipient,
            "/auth/trainer-credentials/complete",
            csrf(self.recipient),
            {"setup_token": token, "new_password": self.password},
        )

    def signin(self, client: TestClient | None = None, password: str | None = None) -> Any:
        c = client or self.recipient
        return call(
            c,
            "/auth/login",
            csrf(c),
            {"login_id": self.login, "password": password or self.password},
        )

    def state(self) -> Any:
        return self.base.client.get(
            "/api/v1/admin/trainers/" + self.trainer + "/login-account"
        ).json()

    def reissue(self, version: int | None = None, operation: str | None = None) -> Any:
        return call(
            self.base.client,
            "/admin/trainers/" + self.trainer + "/initial-setup",
            csrf(self.base.client),
            {
                "operation_id": operation or str(uuid4()),
                "expected_account_version": version or self.state()["account_version"],
            },
        )

    def active(self, active: bool) -> None:
        with self.base.db.session() as s:
            s.execute(
                text(
                    "UPDATE workforce_trainers SET active=:a,row_version=row_version+1 WHERE id=:i"
                ),
                {"a": active, "i": self.trainer},
            )
            s.commit()


@pytest.fixture
def trainer(scene: Scene) -> Iterator[TrainerScene]:
    r = scene.send(scene.body())
    assert r.status_code == 201
    with closing(TestClient(scene.client.app, base_url=ORIGIN)) as recipient:
        yield TrainerScene(
            scene,
            r.json()["trainer"]["id"],
            recipient,
            SyntheticSecret(secrets.token_urlsafe(24)),
            "trainer_" + uuid4().hex,
        )


def source(response: Any) -> SyntheticSecret:
    assert response.status_code == 201
    return SyntheticSecret(response.json()["setup_link"].split("#token=")[1])


def counts(t: TrainerScene) -> tuple[int, ...]:
    with t.base.db.session() as s:
        return tuple(
            int(s.execute(text("SELECT count(*) FROM " + name)).scalar_one())
            for name in (
                "iam_trainer_bindings",
                "iam_trainer_account_operations",
                "iam_trainer_setup_credentials",
                "audit_trainer_identity_events",
            )
        )


def test_actual_w0_setup_login_self_change_logout(trainer: TrainerScene) -> None:
    t = trainer
    token = source(t.issue())
    assert t.complete(token).status_code == 204
    assert t.complete(token).status_code == 400
    assert t.signin().status_code == 204
    old = SyntheticSecret(t.recipient.cookies.get("__Host-y3-auth") or "")
    me = t.recipient.get("/api/v1/auth/me").json()
    assert me["roles"] == [
        {"role": "TRAINER", "trainer_id": t.trainer, "home_branch_id": t.base.branch}
    ]
    assert me["capabilities"] == []
    assert t.recipient.get("/api/v1/branches").status_code == 401
    assert t.recipient.get("/api/v1/auth/passkeys").status_code == 401
    new = SyntheticSecret(secrets.token_urlsafe(24))
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as second:
        assert t.signin(second).status_code == 204
        assert (
            call(
                t.recipient,
                "/auth/password",
                csrf(t.recipient),
                {"current_password": t.password, "new_password": new},
            ).status_code
            == 204
        )
        assert second.get("/api/v1/auth/me").status_code == 401
    t.recipient.cookies.set("__Host-y3-auth", old)
    assert t.recipient.get("/api/v1/auth/me").status_code == 401
    t.recipient.cookies.clear()
    assert t.signin(password=t.password).status_code == 401
    assert t.signin(password=new).status_code == 204
    old = SyntheticSecret(t.recipient.cookies.get("__Host-y3-auth") or "")
    assert call(t.recipient, "/auth/logout", csrf(t.recipient), {}).status_code == 204
    t.recipient.cookies.set("__Host-y3-auth", old)
    assert t.recipient.get("/api/v1/auth/me").status_code == 401
    assert t.base.client.get("/api/v1/auth/me").status_code == 200


def test_replay_and_reissue_never_reveal_old_token(trainer: TrainerScene) -> None:
    t = trainer
    op = str(uuid4())
    old = source(t.issue(op))
    replay = t.issue(op)
    assert replay.status_code == 200 and set(replay.json()) == {"operation"}
    assert t.issue().status_code == 409
    result = t.base.client.get("/api/v1/admin/trainer-account-operations/" + op)
    assert result.status_code == 200 and "setup_link" not in result.json()
    newop = str(uuid4())
    version = t.state()["account_version"]
    new = source(t.reissue(version, newop))
    replay = t.reissue(version, newop)
    assert replay.status_code == 200 and set(replay.json()) == {"operation"}
    assert t.complete(old).status_code == 400
    assert t.complete(new).status_code == 204
    assert t.reissue().status_code == 409
    assert counts(t)[:2] == (1, 2)


@pytest.mark.parametrize("phase", ["issue", "reissue", "complete"])
def test_active_at_all_three_phases(trainer: TrainerScene, phase: str) -> None:
    t = trainer
    token = source(t.issue()) if phase != "issue" else None
    t.active(False)
    before = counts(t)
    r = (
        t.issue()
        if phase == "issue"
        else t.reissue()
        if phase == "reissue"
        else t.complete(str(token))
    )
    assert r.status_code == (400 if phase == "complete" else 409)
    assert counts(t) == before
    t.active(True)
    if token is not None:
        assert t.complete(token).status_code == 204


def test_inactive_home_allows_all_initial_phases_and_login(trainer: TrainerScene) -> None:
    t = trainer
    with t.base.db.session() as s:
        s.execute(text("UPDATE organization_branches SET active=false,row_version=row_version+1"))
        s.commit()
    source(t.issue())
    token = source(t.reissue())
    assert t.complete(token).status_code == 204 and t.signin().status_code == 204
    assert t.recipient.get("/api/v1/auth/me").status_code == 200


def test_inactive_cookie_is_rejected_on_every_self_path(trainer: TrainerScene) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    nonce = csrf(t.recipient)
    t.active(False)
    assert t.recipient.get("/api/v1/auth/me").status_code == 401
    assert (
        call(
            t.recipient,
            "/auth/password",
            nonce,
            {"current_password": t.password, "new_password": secrets.token_urlsafe(24)},
        ).status_code
        == 401
    )
    assert call(t.recipient, "/auth/logout", nonce, {}).status_code == 403
    anonymous_nonce = csrf(t.recipient)
    assert anonymous_nonce != nonce
    assert call(t.recipient, "/auth/logout", anonymous_nonce, {}).status_code == 204
    assert t.signin().status_code == 401
    assert t.base.client.get("/api/v1/auth/me").status_code == 200


def test_purpose_and_management_bypass_rejected(trainer: TrainerScene) -> None:
    t = trainer
    token = source(t.issue())
    for path in ["/auth/credentials/complete", "/auth/passkeys/enrollment/options"]:
        r = call(
            t.recipient, path, csrf(t.recipient), {"setup_token": token, "new_password": t.password}
        )
        assert r.status_code in (400, 403)
    assert t.complete(token).status_code == 204 and t.signin().status_code == 204
    for path in [
        "/admin/trainers",
        "/admin/trainers/" + t.trainer,
        "/admin/trainers/" + t.trainer + "/login-account",
    ]:
        assert t.recipient.get("/api/v1" + path).status_code == 401
    r = call(
        t.recipient,
        "/admin/trainers/" + t.trainer + "/login-account",
        csrf(t.recipient),
        {"operation_id": str(uuid4()), "login_id": "forbidden"},
    )
    assert r.status_code == 401


def test_issue_audit_rollback(trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: Any) -> None:
        raise Rejected(503, "unavailable")

    monkeypatch.setattr(Audit, "append_trainer_identity", fail)
    assert trainer.issue().status_code == 503
    assert counts(trainer) == (0, 0, 0, 0)


def test_actual_commit_ack_loss_reconciles_without_token(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Session.commit
    fired = False

    def commit(s: Session) -> None:
        nonlocal fired
        count = s.execute(text("SELECT count(*) FROM iam_trainer_account_operations")).scalar_one()
        original(s)
        if count and not fired:
            fired = True
            raise OperationalError("commit", {}, Exception("synthetic ack loss"))

    monkeypatch.setattr(Session, "commit", commit)
    op = str(uuid4())
    assert trainer.issue(op).status_code == 503
    assert counts(trainer) == (1, 1, 1, 1)
    assert trainer.issue(op).status_code == 200
    assert trainer.complete(source(trainer.reissue())).status_code == 204


@pytest.mark.parametrize(
    "bad",
    [
        {"setup_token": {"private": "secret-marker"}},
        {"new_password": ["secret-marker"]},
        {"extra": "secret-marker"},
        {"new_password": "secret-marker" * 50},
    ],
)
def test_setup_validation_never_echoes(trainer: TrainerScene, bad: dict[str, Any]) -> None:
    response = call(
        trainer.recipient,
        "/auth/trainer-credentials/complete",
        csrf(trainer.recipient),
        {"setup_token": "secret-marker" * 4, "new_password": "secret-marker", **bad},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid_request"}


def test_login_commit_ack_loss_revokes_unreturned_session(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert trainer.complete(source(trainer.issue())).status_code == 204
    original = Session.commit
    fired = False

    def commit(s: Session) -> None:
        nonlocal fired
        exists = s.execute(
            text(
                "SELECT count(*) FROM iam_sessions s JOIN "
                "iam_trainer_bindings b ON b.account_id=s.account_id WHERE NOT s.revoked"
            )
        ).scalar_one()
        original(s)
        if exists and not fired:
            fired = True
            raise OperationalError("commit", {}, Exception("synthetic ack loss"))

    monkeypatch.setattr(Session, "commit", commit)
    assert trainer.signin().status_code == 503 and fired
    with trainer.base.db.session() as s:
        assert (
            s.execute(
                text(
                    "SELECT count(*) FROM iam_sessions s JOIN "
                    "iam_trainer_bindings b ON b.account_id=s.account_id WHERE NOT s.revoked"
                )
            ).scalar_one()
            == 0
        )
    assert trainer.recipient.get("/api/v1/auth/me").status_code == 401
