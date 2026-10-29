# ruff: noqa: F811
"""Exact public error boundary and expired initial source preservation."""

from typing import Any

import pytest
from sqlalchemy import text

from tests.test_iam import csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_state import change, request

pytestmark = pytest.mark.postgres


def test_receipt_uuid_never_echoes_input(trainer: TrainerScene) -> None:
    marker = "synthetic-private-marker"
    response = trainer.base.client.get("/api/v1/admin/trainer-state-operations/" + marker)
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid_request"}
    assert marker not in response.text


def test_original_source_expiry_not_extended(trainer: TrainerScene) -> None:
    t = trainer
    token = source(t.issue())
    assert change(t, request(t, False)).status_code == 200
    payload = request(t, True)
    nonce = csrf(t.base.client)
    with t.base.db.session() as s:
        s.execute(
            text(
                "UPDATE iam_trainer_setup_credentials SET "
                "expires_at=clock_timestamp()-interval '1 second'"
            )
        )
        original: Any = s.execute(
            text(
                "SELECT account_version,security_version,binding_version,"
                "trainer_role_epoch,expires_at,consumed FROM iam_trainer_setup_credentials"
            )
        ).one()
        s.commit()
    assert (
        call(t.base.client, "/admin/trainers/" + t.trainer + "/state", nonce, payload).status_code
        == 200
    )
    with t.base.db.session() as s:
        assert (
            s.execute(
                text(
                    "SELECT account_version,security_version,binding_version,"
                    "trainer_role_epoch,expires_at,consumed FROM iam_trainer_setup_credentials"
                )
            ).one()
            == original
        )
    # Existing GC may remove expired sources during preparation; it does not renew them.
    assert t.complete(token).status_code == 400
    assert t.state()["state"] == "PENDING_SETUP"
    assert t.state()["initial_setup_expires_at"] is None


def test_current_scope_direct_id_trainer_and_csrf_denials(
    trainer: TrainerScene, mfa: tuple[Any, Any, str, str]
) -> None:
    from contextlib import closing
    from uuid import uuid4

    from tests.test_workforce_integrity import branch_actor

    t = trainer
    foreign_id = str(uuid4())
    foreign_org = str(uuid4())
    foreign_branch = str(uuid4())
    with t.base.db.session() as s:
        s.execute(
            text("INSERT INTO organization_organizations(id,name) VALUES(:o,'가상 외부 조직')"),
            {"o": foreign_org},
        )
        s.execute(
            text(
                "INSERT INTO organization_branches(id,organization_id,code,name) "
                "VALUES(:b,:o,'FOREIGN','가상 외부 지점')"
            ),
            {"b": foreign_branch, "o": foreign_org},
        )
        s.execute(
            text(
                "INSERT INTO workforce_trainers(id,organization_id,home_branch_id,name,phone,"
                "active,row_version,rate_percent,fixed_amount_won,base_salary_won,"
                "base_salary_start_month) "
                "VALUES(:i,:o,:b,'가상 외부 Trainer','가상',true,1,0,0,0,'2026-10-01')"
            ),
            {"i": foreign_id, "o": foreign_org, "b": foreign_branch},
        )
        s.commit()
    payload = request(t, False)
    assert (
        call(
            t.base.client, "/admin/trainers/" + t.trainer + "/state", "bad-csrf", payload
        ).status_code
        == 403
    )
    for ident in (foreign_id, str(uuid4())):
        r = call(t.base.client, "/admin/trainers/" + ident + "/state", csrf(t.base.client), payload)
        assert r.status_code == 404 and r.json() == {"detail": "not_found"}
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    assert (
        call(
            t.recipient, "/admin/trainers/" + t.trainer + "/state", csrf(t.recipient), payload
        ).status_code
        == 401
    )
    with closing(branch_actor(t.base, mfa[2])) as other:
        # Home BA succeeds, then cannot touch another Home's existing Trainer.
        assert (
            call(other, "/admin/trainers/" + t.trainer + "/state", csrf(other), payload).status_code
            == 200
        )
        branch = call(
            t.base.client, "/admin/branches", csrf(t.base.client), {"code": "ELSE", "name": "가상"}
        ).json()
        another = t.base.send({**t.base.body(), "home_branch_id": branch["id"]}).json()["trainer"]
        bad = {
            **payload,
            "operation_id": str(uuid4()),
            "expected_trainer_version": another["version"],
        }
        assert (
            call(other, "/admin/trainers/" + another["id"] + "/state", csrf(other), bad).status_code
            == 404
        )
    with t.base.db.session() as s:
        assert (
            s.execute(text("SELECT count(*) FROM workforce_trainer_state_operations")).scalar_one()
            == 1
        )
        assert s.execute(text("SELECT count(*) FROM audit_trainer_state_events")).scalar_one() == 1
        assert s.execute(
            text("SELECT active FROM workforce_trainers WHERE id=:i"), {"i": foreign_id}
        ).scalar_one()
