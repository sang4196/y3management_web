"""Protected password recovery; explicit approval, immutable case, single-use source."""

import hashlib
import json
import secrets
from dataclasses import asdict
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import text

from y3management.contracts import Rejected
from y3management.iam.infrastructure import IAM, digest
from y3management.iam.public import (
    EmergencyChange,
    EmergencyPasswordProof,
    EmergencyRequest,
    EmergencySnapshot,
    EmergencyView,
    OperatingRecoveryAuthority,
    Setup,
)


class Emergency:
    def __init__(self, iam: IAM) -> None:
        self.iam = iam
        self.s = iam.s

    def authorize(self, authority: OperatingRecoveryAuthority, action: str) -> None:
        self.iam.policy()
        if action not in authority.operations:
            raise Rejected(403, "operating_authority_required")

    def target(self, ident: UUID, org: UUID, *, lock: bool = False) -> dict[str, Any]:
        row = (
            self.s.execute(
                text("SELECT * FROM iam_accounts WHERE id=:id" + (" FOR UPDATE" if lock else "")),
                {"id": ident},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise Rejected(404, "not_found")
        grant = self.iam._account(ident)
        if grant.organization_id != org or grant.state != "ACTIVE" or not grant.master:
            raise Rejected(409, "ineligible_target")
        return dict(row)

    def snapshot(self, row: dict[str, Any]) -> EmergencySnapshot:
        return EmergencySnapshot(
            row["row_version"],
            row["security_version"],
            row["reset_generation"],
            row["password_reset_pending"],
            row["password_hash"] is not None,
        )

    def inspect(self, authority: OperatingRecoveryAuthority, ident: UUID) -> EmergencySnapshot:
        self.authorize(authority, "inspect")
        return self.snapshot(self.target(ident, authority.organization_id))

    def preflight(self, authority: OperatingRecoveryAuthority, ident: UUID) -> None:
        self.authorize(authority, "execute")
        self.target(ident, authority.organization_id)

    def latest(self, ident: UUID) -> UUID | None:
        return self.s.execute(
            text(
                "SELECT id FROM iam_password_emergency_cases "
                "WHERE account_id=:a ORDER BY row_version DESC LIMIT 1"
            ),
            {"a": ident},
        ).scalar_one_or_none()

    def status(self, authority: OperatingRecoveryAuthority, operation: UUID) -> EmergencyView:
        self.authorize(authority, "status")
        case = (
            self.s.execute(
                text(
                    "SELECT * FROM iam_password_emergency_cases WHERE id=:i AND organization_id=:o"
                ),
                {"i": operation, "o": authority.organization_id},
            )
            .mappings()
            .first()
        )
        if case is None:
            raise Rejected(404, "not_found")
        return EmergencyView(
            operation, "password", case["expires_at"], self.case_status(dict(case))
        )

    def case_status(self, case: dict[str, Any]) -> str:
        if case["completed_at"] is not None:
            return "completed"
        if self.latest(case["account_id"]) != case["id"]:
            return "superseded"
        if case["expires_at"] <= self.iam.now():
            return "expired"
        source = self.s.execute(
            text("SELECT id FROM iam_password_emergency_credentials WHERE case_id=:i"),
            {"i": case["id"]},
        ).scalar_one_or_none()
        try:
            if source is None:
                return "stale"
            self.source_id(source)
        except Rejected:
            return "stale"
        return "issued"

    def lock_target(self, ident: UUID, org: UUID) -> dict[str, Any]:
        self.iam.installation_lock()
        row = self.target(ident, org, lock=True)
        self.s.execute(
            text("SELECT id FROM iam_sessions WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": ident},
        ).all()
        return row

    def revoke(self, ident: UUID) -> None:
        self.iam.revoke_management_sources(ident)

    def allocation(self, slot: UUID) -> datetime:
        expiry = self.s.execute(
            text(
                "SELECT expires_at FROM iam_security_states "
                "WHERE id=:i AND kind='emergency' AND policy_version=2"
            ),
            {"i": slot},
        ).scalar_one_or_none()
        if expiry is None or expiry <= self.iam.now():
            raise Rejected(409, "expired_allocation")
        return cast(datetime, expiry)

    def issue(
        self, authority: OperatingRecoveryAuthority, request: EmergencyRequest, slot: UUID
    ) -> tuple[Setup, EmergencyChange]:
        self.authorize(authority, "execute")
        if request.organization_id != authority.organization_id:
            raise Rejected(403, "operating_authority_required")
        before = self.lock_target(request.account_id, request.organization_id)
        now = self.iam.now()
        if (
            request.checked_at > now
            or request.approval_valid_until <= now
            or request.checked_at >= request.approval_valid_until
            or request.owner_ref == authority.executor_ref
        ):
            raise Rejected(409, "approval_invalid")
        if self.snapshot(before) != request.expected:
            raise Rejected(409, "stale_snapshot")
        if request.supersedes != self.latest(request.account_id):
            raise Rejected(409, "explicit_reissue_required")
        if self.s.execute(
            text(
                "SELECT 1 FROM iam_password_emergency_cases WHERE id=:i "
                "OR (organization_id=:o AND approval_ref=:r)"
            ),
            {"i": request.operation_id, "o": request.organization_id, "r": request.approval_ref},
        ).first():
            raise Rejected(409, "execution_already_used")
        expiry = self.allocation(slot)
        self.revoke(request.account_id)
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=NULL,password_reset_pending=true,"
                "reset_generation=reset_generation+1,row_version=row_version+1,"
                "security_version=security_version+1 WHERE id=:a"
            ),
            {"a": request.account_id},
        )
        after = self.target(request.account_id, request.organization_id)
        case = self.case_values(request.operation_id, after, now, expiry, asdict(request))
        case.update(
            kind="operating",
            approval_mode="manual",
            approval_ref=request.approval_ref,
            owner_ref=request.owner_ref,
            executor_ref=authority.executor_ref,
            executor_uid=authority.executor_uid,
            checked_at=request.checked_at,
            approval_valid_until=request.approval_valid_until,
        )
        setup = self.store(case, slot)
        return setup, self.event(before, after, case, "issue", None)

    def case_values(
        self,
        ident: UUID,
        account: dict[str, Any],
        now: datetime,
        expiry: datetime,
        fingerprint: dict[str, Any],
    ) -> dict[str, Any]:
        return dict(
            id=ident,
            organization_id=account["organization_id"],
            account_id=account["id"],
            policy_version=2,
            purpose="password",
            source_purpose="emergency_password",
            fingerprint=hashlib.sha256(
                json.dumps(fingerprint, sort_keys=True, default=str, separators=(",", ":")).encode()
            ).digest(),
            issued_at=now,
            expires_at=expiry,
            row_version=account["row_version"],
            security_version=account["security_version"],
            reset_generation=account["reset_generation"],
        )

    def store(self, case: dict[str, Any], slot: UUID) -> Setup:
        self.s.execute(
            text(
                "INSERT INTO iam_password_emergency_cases ("
                + ",".join(case)
                + ") VALUES ("
                + ",".join(":" + k for k in case)
                + ")"
            ),
            case,
        )
        raw = secrets.token_urlsafe(32)
        self.s.execute(
            text("""INSERT INTO iam_password_emergency_credentials
          (id,case_id,organization_id,account_id,policy_version,allocator_kind,purpose,digest,expires_at)
          VALUES(:s,:id,:organization_id,:account_id,2,'emergency','emergency_password',:d,:expires_at)"""),
            {**case, "s": slot, "d": digest(raw)},
        )
        return Setup(raw, case["expires_at"])

    def legacy_lineage(self, ident: UUID, expected_origin: UUID) -> UUID:
        seen: set[UUID] = set()
        child: dict[str, Any] | None = None
        while True:
            if ident in seen:
                raise Rejected(409, "invalid_lineage")
            seen.add(ident)
            found = (
                self.s.execute(text("SELECT * FROM iam_emergency_cases WHERE id=:i"), {"i": ident})
                .mappings()
                .first()
            )
            if found is None or found["completed_at"] is not None:
                raise Rejected(409, "invalid_lineage")
            case = dict(found)
            if child is not None:
                increments = {
                    "row_version": 1,
                    "security_version": 1,
                    "reset_generation": int(child["factors"] in ("password", "both")),
                    "key_set_version": int(child["factors"] in ("passkey", "both")),
                    "recovery_generation": int(child["factors"] in ("passkey", "both")),
                }
                if (
                    any(case[k] != child[k] for k in ("organization_id", "account_id", "factors"))
                    or any(case[k] + delta != child[k] for k, delta in increments.items())
                    or case["issued_at"] > child["issued_at"]
                    or (
                        case["issuer_kind"] == "operating"
                        and case["expires_at"] > child["issued_at"]
                    )
                ):
                    raise Rejected(409, "invalid_lineage")
            if case["issuer_kind"] == "operating":
                if case["id"] != expected_origin or case["approval_mode"] != "manual":
                    raise Rejected(409, "invalid_lineage")
                return cast(UUID, case["id"])
            if (
                case["issuer_kind"] != "master_handoff"
                or case["approval_origin_case_id"] != expected_origin
                or case["handoff_parent_id"] is None
                or case["handoff_parent_id"] != case["supersedes"]
            ):
                raise Rejected(409, "invalid_lineage")
            child, ident = case, case["handoff_parent_id"]

    def lineage(self, ident: UUID) -> UUID:
        """Verify semantic ancestry independently of the structural foreign keys."""
        seen: set[UUID] = set()
        child: dict[str, Any] | None = None
        while True:
            if ident in seen:
                raise Rejected(409, "invalid_lineage")
            seen.add(ident)
            found = (
                self.s.execute(
                    text("SELECT * FROM iam_password_emergency_cases WHERE id=:i"), {"i": ident}
                )
                .mappings()
                .first()
            )
            if found is None:
                raise Rejected(409, "invalid_lineage")
            case = dict(found)
            if child is not None and (
                case["organization_id"] != child["organization_id"]
                or case["account_id"] != child["account_id"]
                or case["completed_at"] is not None
                or any(
                    case[k] + 1 != child[k]
                    for k in ("row_version", "security_version", "reset_generation")
                )
                or case["issued_at"] > child["issued_at"]
                or (case["kind"] == "operating" and case["expires_at"] > child["issued_at"])
            ):
                raise Rejected(409, "invalid_lineage")
            if case["kind"] == "operating":
                return cast(UUID, case["id"])
            if case["kind"] == "legacy_handoff":
                policy = self.iam.policy()
                transition = (
                    self.s.execute(
                        text("""SELECT * FROM iam_policy_account_transitions
                  WHERE transition_id=:p AND organization_id=:o AND account_id=:a
                  AND legacy_parent_id=:l AND legacy_origin_id=:r
                  AND legacy_password_continuation_eligible"""),
                        {
                            "p": policy.transition_id,
                            "o": case["organization_id"],
                            "a": case["account_id"],
                            "l": case["legacy_parent_id"],
                            "r": case["legacy_origin_id"],
                        },
                    )
                    .mappings()
                    .first()
                )
                if (
                    transition is None
                    or case["policy_transition_id"] != policy.transition_id
                    or any(
                        case[k] != transition["after_" + k] + 1
                        for k in ("row_version", "security_version", "reset_generation")
                    )
                ):
                    raise Rejected(409, "invalid_lineage")
                legacy = (
                    self.s.execute(
                        text("SELECT * FROM iam_emergency_cases WHERE id=:i"),
                        {"i": case["legacy_parent_id"]},
                    )
                    .mappings()
                    .first()
                )
                if (
                    legacy is None
                    or legacy["completed_at"] is not None
                    or legacy["factors"] != transition["legacy_factors"]
                    or any(
                        legacy[k] != transition["before_" + k]
                        for k in (
                            "row_version",
                            "security_version",
                            "key_set_version",
                            "reset_generation",
                            "recovery_generation",
                        )
                    )
                    or (
                        legacy["issuer_kind"] == "operating"
                        and legacy["expires_at"] > case["issued_at"]
                    )
                ):
                    raise Rejected(409, "invalid_lineage")
                return self.legacy_lineage(case["legacy_parent_id"], case["legacy_origin_id"])
            if case["kind"] != "handoff" or case["parent_id"] is None:
                raise Rejected(409, "invalid_lineage")
            child, ident = case, case["parent_id"]

    def source_id(self, ident: UUID, *, lock: bool = False) -> dict[str, Any]:
        row = (
            self.s.execute(
                text(
                    """SELECT e.*,c.row_version,c.security_version,c.reset_generation,
          c.completed_at,c.kind,c.approval_mode FROM iam_password_emergency_credentials e
          JOIN iam_password_emergency_cases c ON c.id=e.case_id
          WHERE e.id=:i AND e.policy_version=2"""
                    + (" FOR UPDATE OF e,c" if lock else "")
                ),
                {"i": ident},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise Rejected(401, "invalid_recovery")
        try:
            self.lineage(row["case_id"])
            account = self.target(row["account_id"], row["organization_id"])
        except Rejected:
            raise Rejected(401, "invalid_recovery") from None
        if (
            row["consumed"]
            or row["completed_at"] is not None
            or row["expires_at"] <= self.iam.now()
            or self.latest(account["id"]) != row["case_id"]
            or not account["password_reset_pending"]
            or account["password_hash"] is not None
            or any(
                account[k] != row[k]
                for k in ("row_version", "security_version", "reset_generation")
            )
        ):
            raise Rejected(401, "invalid_recovery")
        return dict(row)

    def source(self, token: str) -> dict[str, Any]:
        ident = self.s.execute(
            text(
                "SELECT id FROM iam_password_emergency_credentials "
                "WHERE digest=:d AND policy_version=2"
            ),
            {"d": digest(token)},
        ).scalar_one_or_none()
        if ident is None:
            raise Rejected(401, "invalid_recovery")
        return self.source_id(ident)

    def recipient(self, token: str) -> EmergencyView:
        source = self.source(token)
        return EmergencyView(source["case_id"], "password", source["expires_at"], "issued")

    def prepare_password(self, token: str, password: str) -> EmergencyPasswordProof:
        policy = self.iam.policy()
        source = self.source(token)
        account = self.target(source["account_id"], source["organization_id"])
        encoded = self.iam.passwords.create(password, account["login_id"])
        return EmergencyPasswordProof(
            source["id"],
            source["case_id"],
            source["organization_id"],
            source["account_id"],
            source["row_version"],
            source["security_version"],
            source["reset_generation"],
            account["trainer_role_epoch"],
            source["expires_at"],
            policy,
            encoded,
        )

    def complete_password(self, proof: EmergencyPasswordProof) -> EmergencyChange:
        before = self.lock_target(proof.account_id, proof.organization_id)
        self.iam.check_policy(proof.policy)
        source = self.source_id(proof.source_id, lock=True)
        if (
            source["case_id"] != proof.case_id
            or source["account_id"] != proof.account_id
            or source["organization_id"] != proof.organization_id
            or source["expires_at"] != proof.expires_at
            or before["trainer_role_epoch"] != proof.trainer_role_epoch
            or any(
                before[k] != getattr(proof, k)
                for k in ("row_version", "security_version", "reset_generation")
            )
        ):
            raise Rejected(401, "invalid_recovery")
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=:h,password_reset_pending=false,"
                "row_version=row_version+1,security_version=security_version+1 WHERE id=:a"
            ),
            {"h": proof.password_hash, "a": proof.account_id},
        )
        self.revoke(proof.account_id)
        self.s.execute(
            text(
                "UPDATE iam_password_emergency_cases SET completed_at=clock_timestamp() WHERE id=:i"
            ),
            {"i": proof.case_id},
        )
        after = self.target(proof.account_id, proof.organization_id)
        return self.event(
            before, after, {**source, "id": proof.case_id}, "complete", proof.account_id
        )

    def confirm_complete(self, proof: EmergencyPasswordProof) -> None:
        self.iam.check_policy(proof.policy)
        if proof.expires_at <= self.iam.now():
            raise Rejected(401, "invalid_recovery")

    def event(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
        case: dict[str, Any],
        action: str,
        actor: UUID | None,
    ) -> EmergencyChange:
        return EmergencyChange(
            case["id"],
            before["organization_id"],
            before["id"],
            actor,
            action,
            {
                "issue": "SYSTEM_RECOVERY_OPERATOR",
                "handoff": "MASTER",
                "complete": "RECOVERY_RECIPIENT",
            }[action],
            case["approval_mode"],
            before["row_version"],
            after["row_version"],
            before["security_version"],
            after["security_version"],
            before["reset_generation"],
            after["reset_generation"],
            2,
            self.iam.now(),
        )
