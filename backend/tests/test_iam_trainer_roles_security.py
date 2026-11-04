# ruff: noqa: F811
"""Current Home authorization and preserved administrator recovery sources."""

from contextlib import closing
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import (  # noqa: F401
    call,
    complete,
    link_token,
    login_password,
    password_app,
    provision,
    reset_request,
)
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body, change, state
from tests.test_workforce import Scene, scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def link(t: TrainerScene, ident: str, identifier: str) -> dict[str, Any]:
    candidate = call(
        t.base.client,
        "/admin/trainers/" + t.trainer + "/role-account-lookup",
        csrf(t.base.client),
        {"login_id": identifier},
    )
    assert candidate.status_code == 200
    request = body(t, True)
    request.update(account_id=ident, expected_account_version=candidate.json()["account_version"])
    return request


def test_current_branch_scope_unbound_revoke_confirmation_and_binding(
    trainer: TrainerScene, password_app: tuple[Settings, Database, str]
) -> None:
    t = trainer
    with closing(branch_actor(t.base, password_app[2])) as branch:
        master = t.base.client.get("/api/v1/auth/me").json()["account_id"]
        request = link(t, master, "MASTER.TEST")
        endpoint = "/admin/trainers/" + t.trainer + "/role"
        assert (
            call(branch, endpoint, csrf(branch), {**request, "desired_granted": False}).status_code
            == 404
        )
        assert (
            call(
                branch, endpoint, csrf(branch), {**request, "identity_confirmed": False}
            ).status_code
            == 422
        )
        with t.base.db.session() as s:
            assert (
                s.execute(text("SELECT count(*) FROM iam_trainer_role_operations")).scalar_one()
                == 0
            )
            s.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:b"
                ),
                {"b": t.base.branch},
            )
            s.commit()
        assert call(branch, endpoint, csrf(branch), request).status_code == 200
        assert branch.get("/api/v1/auth/me").status_code == 200
        assert t.base.client.get("/api/v1/auth/me").status_code == 401
        with t.base.db.session() as s:
            s.execute(
                text("UPDATE organization_branches SET active=true WHERE id=:b"),
                {"b": t.base.branch},
            )
            s.commit()
        other = Scene(branch, t.base.db, t.base.branch).send(t.base.body()).json()["trainer"]
        candidate = call(
            branch,
            "/admin/trainers/" + other["id"] + "/role-account-lookup",
            csrf(branch),
            {"login_id": "master.test"},
        )
        assert candidate.status_code == 409
        second = {
            **request,
            "operation_id": str(uuid4()),
            "expected_trainer_version": other["version"],
        }
        assert (
            call(
                branch, "/admin/trainers/" + other["id"] + "/role", csrf(branch), second
            ).status_code
            == 409
        )
        # Move only the test-owned current Home fact: old BA loses all read/write access.
        with t.base.db.session() as s:
            foreign = uuid4()
            s.execute(
                text(
                    "INSERT INTO organization_branches(id,organization_id,code,name) "
                    "SELECT :i,organization_id,'OTHER','다른 가상지점' FROM organization_branches "
                    "WHERE id=:b"
                ),
                {"i": foreign, "b": t.base.branch},
            )
            s.execute(
                text(
                    "UPDATE workforce_trainers SET home_branch_id=:b,row_version=row_version+1 "
                    "WHERE id=:t"
                ),
                {"b": foreign, "t": t.trainer},
            )
            s.commit()
        assert branch.get("/api/v1" + endpoint).status_code == 404
        assert (
            call(
                branch,
                "/admin/trainers/" + t.trainer + "/role-account-lookup",
                csrf(branch),
                {"login_id": "master.test"},
            ).status_code
            == 404
        )
        assert (
            branch.get(
                "/api/v1/admin/trainer-role-operations/" + request["operation_id"]
            ).status_code
            == 404
        )
        assert call(branch, endpoint, csrf(branch), request).status_code == 404


def test_long_reset_source_preserved_across_role_withdrawal(
    trainer: TrainerScene, password_app: tuple[Settings, Database, str]
) -> None:
    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident = provision(t.base.client, target, password_app[2])
        assert change(t, link(t, ident, "second.master")).status_code == 200
        assert target.get("/api/v1/auth/me").status_code == 401
        target.cookies.clear()
        login_password(target, password_app[2], "second.master")
        issued = reset_request(t.base.client, ident)
        token = link_token(issued.json()["reset_link"])
        with t.base.db.session() as s:
            before = s.execute(
                text(
                    "SELECT row_to_json(x)::text FROM iam_reset_credentials x WHERE account_id=:a"
                ),
                {"a": ident},
            ).scalar_one()
        assert change(t, body(t, False)).status_code == 200
        with t.base.db.session() as s:
            assert (
                s.execute(
                    text(
                        "SELECT row_to_json(x)::text FROM iam_reset_credentials x "
                        "WHERE account_id=:a"
                    ),
                    {"a": ident},
                ).scalar_one()
                == before
            )
        assert complete(target, token, password_app[2]).status_code == 204
        login_password(target, password_app[2], "second.master")
        profile = target.get("/api/v1/auth/me").json()
        assert [x["role"] for x in profile["roles"]] == ["ADMIN"]
        assert profile["trainer_binding"]["granted"] is False
        assert state(t)["granted"] is False


def test_all_target_sessions_and_prepared_password_rejected_other_account_preserved(
    trainer: TrainerScene, password_app: tuple[Settings, Database, str]
) -> None:
    from y3management.contracts import Rejected
    from y3management.use_cases import Service

    t = trainer
    with (
        closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target,
        closing(TestClient(t.base.client.app, base_url=ORIGIN)) as second,
    ):
        ident = provision(t.base.client, target, password_app[2])
        assert change(t, link(t, ident, "second.master")).status_code == 200
        target.cookies.clear()
        login_password(target, password_app[2], "second.master")
        login_password(second, password_app[2], "second.master")
        service: Service = cast(FastAPI, t.base.client.app).state.iam_service
        with service.uow.open() as w:
            reservation = w.security.reserve("second.master")
        with service.uow.open() as w:
            proof = w.iam.verify_login("second.master", password_app[2], reservation)
        assert proof is not None
        with t.base.db.session() as s:
            before_budget = s.execute(
                text("SELECT key,cooldown FROM iam_budgets ORDER BY key")
            ).all()
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
                    {"a": ident},
                ).scalar_one()
                == 2
            )
        assert change(t, body(t, False)).status_code == 200
        with t.base.db.session() as s:
            assert (
                s.execute(text("SELECT key,cooldown FROM iam_budgets ORDER BY key")).all()
                == before_budget
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
                    {"a": ident},
                ).scalar_one()
                == 0
            )
        with service.uow.open() as w:
            preparation = w.security.preparation(None)
            slot = w.security.allocate("session_slot")
        try:
            with pytest.raises(Rejected) as denied, service.uow.open() as w:
                w.iam.lock_login(proof.account_id)
                w.iam.login(proof, slot, preparation.token, preparation.csrf, reservation)
            assert denied.value.status == 401
        finally:
            with service.uow.open() as w:
                w.security.release(slot, collect=False)
        assert target.get("/api/v1/auth/me").status_code == 401
        assert second.get("/api/v1/auth/me").status_code == 401
        assert t.base.client.get("/api/v1/auth/me").status_code == 200


def test_prepared_reset_proof_rejected_but_original_source_still_usable(
    trainer: TrainerScene,
    password_app: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from y3management.iam.password_reset import PasswordReset
    from y3management.iam.public import ResetProof

    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident = provision(t.base.client, target, password_app[2])
        assert change(t, link(t, ident, "second.master")).status_code == 200
        issued = reset_request(t.base.client, ident)
        token = link_token(issued.json()["reset_link"])
        original = PasswordReset.prepare_reset
        changed = False

        def prepare(self: PasswordReset, token: str, password: str) -> ResetProof:
            nonlocal changed
            proof = original(self, token, password)
            assert change(t, body(t, False)).status_code == 200
            changed = True
            return proof

        with monkeypatch.context() as patch:
            patch.setattr(PasswordReset, "prepare_reset", prepare)
            assert complete(target, token, password_app[2]).status_code == 401
        assert changed
        assert complete(target, token, password_app[2]).status_code == 204
