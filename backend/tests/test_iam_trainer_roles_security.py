# ruff: noqa: F811
"""Current Home authorization and preserved administrator recovery sources."""

from contextlib import closing
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, login_mfa, mfa  # noqa: F401
from tests.test_iam_mfa_management import link_token, recovery_options, recovery_request
from tests.test_iam_mfa_management_races import provision
from tests.test_iam_password_reset import complete, reset_request
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
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str]
) -> None:
    t = trainer
    with closing(branch_actor(t.base, mfa[2])) as branch:
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


@pytest.mark.parametrize("purpose", ["reset", "recovery"])
def test_long_source_preserved_old_context_rejected_fresh_ceremony_succeeds(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str], purpose: str
) -> None:
    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident, key = provision(t.base.client, target, mfa[2])
        assert change(t, link(t, ident, "second.master")).status_code == 200
        assert target.get("/api/v1/auth/me").status_code == 401
        target.cookies.clear()
        login_mfa(target, mfa[2], key, "second.master")
        if purpose == "reset":
            issued = reset_request(t.base.client, ident)
            token = link_token(issued.json()["reset_link"])
            table = "iam_reset_credentials"
        else:
            issued = recovery_request(t.base.client, ident)
            token = link_token(issued.json()["recovery_link"])
            table = "iam_recovery_credentials"
            options = recovery_options(target, token).json()
            replacement = Authenticator()
            payload = {"credential": replacement.registration(options["publicKey"])}
        with t.base.db.session() as s:
            before = s.execute(
                text("SELECT row_to_json(x)::text FROM " + table + " x WHERE account_id=:a"),
                {"a": ident},
            ).scalar_one()
        assert change(t, body(t, False)).status_code == 200
        with t.base.db.session() as s:
            assert (
                s.execute(
                    text("SELECT row_to_json(x)::text FROM " + table + " x WHERE account_id=:a"),
                    {"a": ident},
                ).scalar_one()
                == before
            )
        if purpose == "reset":
            assert complete(target, token, mfa[2]).status_code == 204
            login_mfa(target, mfa[2], key, "second.master")
        else:
            assert (
                call(
                    target, "/auth/passkeys/recovery/verify", options["csrf_token"], payload
                ).status_code
                == 401
            )
            fresh = recovery_options(target, token)
            assert fresh.status_code == 200
            data = fresh.json()
            assert (
                call(
                    target,
                    "/auth/passkeys/recovery/verify",
                    data["csrf_token"],
                    {"credential": replacement.registration(data["publicKey"])},
                ).status_code
                == 204
            )
            login_mfa(target, mfa[2], replacement, "second.master")
        profile = target.get("/api/v1/auth/me").json()
        assert [x["role"] for x in profile["roles"]] == ["ADMIN"]
        assert profile["trainer_binding"]["granted"] is False
        assert state(t)["granted"] is False


def test_all_target_sessions_pending_uv_and_other_account_preserved(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str]
) -> None:
    from tests.test_iam_mfa import begin

    t = trainer
    with (
        closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target,
        closing(TestClient(t.base.client.app, base_url=ORIGIN)) as second,
        closing(TestClient(t.base.client.app, base_url=ORIGIN)) as pending,
    ):
        ident, key = provision(t.base.client, target, mfa[2])
        assert change(t, link(t, ident, "second.master")).status_code == 200
        assert target.get("/api/v1/auth/me").status_code == 401
        target.cookies.clear()
        login_mfa(target, mfa[2], key, "second.master")
        login_mfa(second, mfa[2], key, "second.master")
        options = begin(pending, mfa[2], "second.master")
        with t.base.db.session() as s:
            before_budget = s.execute(
                text("SELECT key,cooldown FROM iam_budgets ORDER BY key")
            ).all()
            before_keys = s.execute(
                text("SELECT key_id,revoked_at FROM iam_passkeys ORDER BY key_id")
            ).all()
            active_sessions = s.execute(
                text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
                {"a": ident},
            ).scalar_one()
        assert active_sessions == 2
        assert change(t, body(t, False)).status_code == 200
        with t.base.db.session() as s:
            assert (
                s.execute(text("SELECT key,cooldown FROM iam_budgets ORDER BY key")).all()
                == before_budget
            )
            assert (
                s.execute(text("SELECT key_id,revoked_at FROM iam_passkeys ORDER BY key_id")).all()
                == before_keys
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
                    {"a": ident},
                ).scalar_one()
                == 0
            )
            assert (
                s.execute(
                    text(
                        "SELECT count(*) FROM iam_mfa_contexts WHERE account_id=:a "
                        "AND (NOT consumed OR password_hash IS NOT NULL)"
                    ),
                    {"a": ident},
                ).scalar_one()
                == 0
            )
        assert target.get("/api/v1/auth/me").status_code == 401
        assert second.get("/api/v1/auth/me").status_code == 401
        assert (
            call(
                pending,
                "/auth/login/passkey/verify",
                options["csrf_token"],
                {"credential": key.assertion(options["publicKey"])},
            ).status_code
            == 401
        )
        assert t.base.client.get("/api/v1/auth/me").status_code == 200


def test_prepared_reset_proof_rejected_but_original_source_still_usable(
    trainer: TrainerScene, mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.iam.mfa import MFA
    from y3management.iam.public import ResetProof

    t = trainer
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as target:
        ident, _ = provision(t.base.client, target, mfa[2])
        assert change(t, link(t, ident, "second.master")).status_code == 200
        issued = reset_request(t.base.client, ident)
        token = link_token(issued.json()["reset_link"])
        original = MFA.prepare_reset
        changed = False

        def prepare(self: MFA, token: str, password: str) -> ResetProof:
            nonlocal changed
            proof = original(self, token, password)
            assert change(t, body(t, False)).status_code == 200
            changed = True
            return proof

        with monkeypatch.context() as patch:
            patch.setattr(MFA, "prepare_reset", prepare)
            assert complete(target, token, mfa[2]).status_code == 401
        assert changed
        assert complete(target, token, mfa[2]).status_code == 204
