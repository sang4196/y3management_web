# ruff: noqa: F811
"""Legacy recovery evidence and durable origin semantics at the policy boundary."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.legacy_helpers import legacy_database, legacy_master  # noqa: F401
from tests.test_password_transition import fingerprint, migrate
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("state", ["ACTIVE", "DISABLED"])
@pytest.mark.parametrize(
    "evidence", ["start", "reissue", "missing", "completed", "wrong_generation", "missing_before"]
)
def test_key_pending_requires_latest_complete_evidence(
    legacy_master: tuple[Settings, Database], state: str, evidence: str
) -> None:
    settings, db = legacy_master
    with db.session() as session:
        account = session.execute(text("SELECT id,organization_id FROM iam_accounts")).one()
        session.execute(
            text(
                "UPDATE iam_accounts SET state=:s,recovery_pending=true,"
                "recovery_generation=1,key_set_version=1,row_version=2,security_version=2"
            ),
            {"s": state},
        )
        if evidence != "missing":
            session.execute(
                text(
                    "INSERT INTO audit_events(id,organization_id,target_id,action,success,"
                    "request_id,before_version,after_version,before_key_set_version,"
                    "after_key_set_version,"
                    "before_recovery_generation,after_recovery_generation) "
                    "VALUES(:i,:o,:a,:action,true,:i,1,2,0,1,:b,:g)"
                ),
                {
                    "i": uuid4(),
                    "o": account.organization_id,
                    "a": account.id,
                    "action": "recovery_complete"
                    if evidence == "completed"
                    else "recovery_reissue"
                    if evidence == "reissue"
                    else "recovery_start",
                    "b": None if evidence == "missing_before" else 0,
                    "g": 2 if evidence == "wrong_generation" else 1,
                },
            )
        session.commit()
    before = fingerprint(db)
    valid = evidence in ("start", "reissue")
    migrate(settings, "upgrade", "0014_password_only", success=valid)
    if not valid:
        assert fingerprint(db) == before
        return
    with db.session() as session:
        assert (
            session.execute(text("SELECT recovery_pending FROM iam_accounts")).scalar_one() is False
        )
        row = session.execute(
            text(
                "SELECT classification,retirement_kind,before_recovery_pending,"
                "after_recovery_pending,before_state,after_state FROM "
                "iam_policy_account_transitions"
            )
        ).one()
        assert tuple(row) == (
            "disabled" if state == "DISABLED" else "key_only_retired",
            "retired_feature",
            True,
            False,
            state,
            state,
        )


def seed_case(db: Database, *, completed: bool = False, factors: str = "both") -> dict[str, Any]:
    """FK-valid original case and audit facts; not a replacement for user setup."""
    with db.session() as session:
        account = session.execute(text("SELECT id,organization_id FROM iam_accounts")).one()
        now = datetime.now(UTC) - timedelta(hours=1)
        key = factors in ("passkey", "both")
        password = factors in ("password", "both")
        session.execute(
            text(
                "UPDATE iam_accounts SET password_hash=:h,password_reset_pending=:p,"
                "reset_generation=:r,recovery_pending=:k,recovery_generation=:g,key_set_version=:v,"
                "row_version=2,security_version=2"
            ),
            {
                "h": None if password else "synthetic-migration-hash",
                "p": password,
                "r": int(password),
                "k": key,
                "g": int(key),
                "v": 1,
            },
        )
        if not key:
            session.execute(
                text(
                    "INSERT INTO iam_passkeys(credential_id,account_id,public_key,"
                    "sign_count,device_type,backed_up) VALUES(:k,:a,:k,0,'single_device',false)"
                ),
                {"k": b"synthetic-original-key", "a": account.id},
            )
        case = dict(
            id=uuid4(),
            organization_id=account.organization_id,
            account_id=account.id,
            factors=factors,
            approval_ref="synthetic-approval",
            owner_ref="synthetic-owner",
            executor_ref="synthetic-executor",
            executor_uid=0,
            checked_at=now - timedelta(seconds=1),
            approval_valid_until=now + timedelta(hours=2),
            issued_at=now,
            expires_at=now + timedelta(minutes=30),
            completed_at=now + timedelta(minutes=1) if completed else None,
            row_version=2,
            security_version=2,
            key_set_version=1,
            reset_generation=int(password),
            recovery_generation=int(key),
            expected_row_version=1,
            expected_security_version=1,
            expected_key_set_version=0 if key else 1,
            expected_reset_generation=0,
            expected_recovery_generation=0,
            expected_password_reset_pending=False,
            expected_recovery_pending=False,
            expected_password_ready=True,
            expected_key_ready=True,
        )
        session.execute(
            text(
                "INSERT INTO iam_emergency_cases("
                + ",".join(case)
                + ") VALUES ("
                + ",".join(":" + k for k in case)
                + ")"
            ),
            case,
        )
        session.execute(
            text(
                "INSERT INTO audit_events(id,organization_id,target_id,action,success,request_id,"
                "actor_role,actor_scope,emergency_case_id,emergency_factors,executor_ref,"
                "approval_mode,"
                "before_version,after_version,before_key_set_version,after_key_set_version,"
                "before_recovery_generation,after_recovery_generation) "
                "VALUES(:i,:o,:a,'emergency_issue',true,:i,'SYSTEM_RECOVERY_OPERATOR',"
                "'EMERGENCY_RECOVERY',"
                ":c,:f,'synthetic-executor','manual',1,2,0,1,0,:g)"
            ),
            {
                "i": uuid4(),
                "o": account.organization_id,
                "a": account.id,
                "c": case["id"],
                "f": factors,
                "g": int(key),
            },
        )
        session.commit()
    return case


@pytest.mark.parametrize("factors", ["password", "both", "passkey"])
def test_original_factors_preserved_and_only_pending_password_continues(
    legacy_master: tuple[Settings, Database], factors: str
) -> None:
    settings, db = legacy_master
    case = seed_case(db, factors=factors)
    with db.session() as session:
        original = session.execute(
            text("SELECT row_to_json(c)::text FROM iam_emergency_cases c")
        ).scalar_one()
    migrate(settings, "upgrade", "0014_password_only")
    with db.session() as session:
        assert (
            session.execute(
                text("SELECT row_to_json(c)::text FROM iam_emergency_cases c")
            ).scalar_one()
            == original
        )
        row = session.execute(
            text(
                "SELECT legacy_password_continuation_eligible,legacy_parent_id,"
                "legacy_origin_id,legacy_factors FROM iam_policy_account_transitions"
            )
        ).one()
        assert tuple(row) == (
            (True, case["id"], case["id"], factors)
            if factors != "passkey"
            else (False, None, None, None)
        )


@pytest.mark.parametrize("invalid", ["completed", "stale_version"])
def test_ineligible_original_case_never_rebased(
    legacy_master: tuple[Settings, Database], invalid: str
) -> None:
    settings, db = legacy_master
    seed_case(db, factors="password", completed=invalid == "completed")
    if invalid == "stale_version":
        with db.session() as session:
            session.execute(
                text(
                    "UPDATE iam_accounts SET row_version=row_version+1,"
                    "security_version=security_version+1"
                )
            )
            session.commit()
    migrate(settings, "upgrade", "0014_password_only")
    with db.session() as session:
        assert (
            session.execute(
                text(
                    "SELECT legacy_password_continuation_eligible FROM "
                    "iam_policy_account_transitions"
                )
            ).scalar_one()
            is False
        )


@pytest.mark.parametrize("variant", ["valid", "parent_completed", "security_gap", "not_due"])
def test_original_handoff_chain_requires_semantic_ancestry(
    legacy_master: tuple[Settings, Database], variant: str
) -> None:
    settings, db = legacy_master
    parent = seed_case(db, factors="password")
    issuer = uuid4()
    issued = parent["issued_at"] + timedelta(minutes=20 if variant == "not_due" else 40)
    child = {
        **parent,
        "id": uuid4(),
        "issued_at": issued,
        "expires_at": issued + timedelta(minutes=30),
        "row_version": 3,
        "security_version": 4 if variant == "security_gap" else 3,
        "reset_generation": 2,
        "expected_row_version": 2,
        "expected_security_version": 2,
        "expected_reset_generation": 1,
        "expected_password_reset_pending": True,
        "expected_password_ready": False,
        "issuer_kind": "master_handoff",
        "issuer_account_id": issuer,
        "approval_mode": "current_master",
        "approval_origin_case_id": parent["id"],
        "handoff_parent_id": parent["id"],
        "supersedes": parent["id"],
        **dict.fromkeys(
            (
                "approval_ref",
                "owner_ref",
                "executor_ref",
                "executor_uid",
                "checked_at",
                "approval_valid_until",
            )
        ),
    }
    with db.session() as session:
        session.execute(
            text(
                "INSERT INTO iam_accounts(id,organization_id,login_id,state,password_hash) "
                "VALUES(:i,:o,'legacy.issuer','ACTIVE','synthetic-history-hash')"
            ),
            {"i": issuer, "o": parent["organization_id"]},
        )
        session.execute(text("INSERT INTO iam_login_ids VALUES('legacy.issuer',:i)"), {"i": issuer})
        session.execute(
            text("INSERT INTO iam_admin_grants VALUES(:i,:o,'ORGANIZATION',NULL)"),
            {"i": issuer, "o": parent["organization_id"]},
        )
        session.execute(
            text(
                "INSERT INTO iam_emergency_cases("
                + ",".join(child)
                + ") VALUES ("
                + ",".join(":" + k for k in child)
                + ")"
            ),
            child,
        )
        session.execute(
            text(
                "UPDATE iam_accounts SET row_version=3,security_version=:s,"
                "reset_generation=2 WHERE id=:i"
            ),
            {"s": child["security_version"], "i": parent["account_id"]},
        )
        if variant == "parent_completed":
            session.execute(
                text("UPDATE iam_emergency_cases SET completed_at=issued_at WHERE id=:i"),
                {"i": parent["id"]},
            )
        session.commit()
    before = fingerprint(db)
    migrate(settings, "upgrade", "0014_password_only", success=variant == "valid")
    if variant != "valid":
        assert fingerprint(db) == before
    else:
        with db.session() as session:
            assert tuple(
                session.execute(
                    text(
                        "SELECT legacy_password_continuation_eligible,"
                        "legacy_parent_id,legacy_origin_id "
                        "FROM iam_policy_account_transitions WHERE account_id=:a"
                    ),
                    {"a": parent["account_id"]},
                ).one()
            ) == (True, child["id"], parent["id"])
        from y3management.iam.emergency import Emergency
        from y3management.uow import UnitOfWork

        # Check the historical transition and case lineage across the schema-only upgrade.
        def history_digests() -> tuple[str, ...]:
            with db.session() as session:
                return tuple(
                    session.execute(
                        text(
                            f"SELECT md5(string_agg(row_to_json(t)::text, ',' "
                            f"ORDER BY row_to_json(t)::text)) FROM {table} t"
                        )
                    ).scalar_one()
                    for table in (
                        "iam_policy_transitions",
                        "iam_policy_account_transitions",
                        "iam_emergency_cases",
                    )
                )

        history = history_digests()
        migrate(settings, "upgrade", "0017_operator_management")
        assert history_digests() == history
        with UnitOfWork(db, settings).open() as work:
            assert isinstance(work.emergency, Emergency)
            assert work.emergency.legacy_lineage(child["id"], parent["id"]) == parent["id"]
