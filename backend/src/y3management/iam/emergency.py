"""IAM-owned emergency state transitions; no fabricated business caller/session."""

import secrets
from dataclasses import asdict
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from y3management.contracts import Rejected
from y3management.iam.infrastructure import digest
from y3management.iam.mfa import MFA
from y3management.iam.public import (
    Ceremony,
    EmergencyChange,
    EmergencyRequest,
    EmergencySnapshot,
    EmergencyView,
    OperatingRecoveryAuthority,
    RegistrationProof,
    Setup,
)


class Emergency:
    def __init__(self, mfa: MFA) -> None:
        self.mfa = mfa
        self.iam = mfa.iam
        self.s = mfa.s

    def authorize(self, authority: OperatingRecoveryAuthority, action: str) -> None:
        self.mfa.enabled()
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
            row["key_set_version"],
            row["reset_generation"],
            row["recovery_generation"],
            row["password_reset_pending"],
            row["recovery_pending"],
            row["password_hash"] is not None,
            self.s.execute(
                text("SELECT 1 FROM iam_passkeys WHERE account_id=:a AND revoked_at IS NULL"),
                {"a": row["id"]},
            ).first()
            is not None,
        )

    def inspect(self, authority: OperatingRecoveryAuthority, ident: UUID) -> EmergencySnapshot:
        self.authorize(authority, "inspect")
        return self.snapshot(self.target(ident, authority.organization_id))

    def preflight(self, authority: OperatingRecoveryAuthority, ident: UUID) -> None:
        self.authorize(authority, "execute")
        self.target(ident, authority.organization_id)

    def status(self, authority: OperatingRecoveryAuthority, operation: UUID) -> EmergencyView:
        self.authorize(authority, "status")
        case = (
            self.s.execute(
                text("SELECT * FROM iam_emergency_cases WHERE id=:id AND organization_id=:org"),
                {"id": operation, "org": authority.organization_id},
            )
            .mappings()
            .first()
        )
        if case is None:
            raise Rejected(404, "not_found")
        state = "issued"
        if case["completed_at"] is not None:
            state = "completed"
        elif self.s.execute(
            text("SELECT 1 FROM iam_emergency_cases WHERE supersedes=:id"), {"id": operation}
        ).first():
            state = "superseded"
        elif case["expires_at"] <= self.iam.now():
            state = "expired"
        else:
            source = self.s.execute(
                text("SELECT id FROM iam_emergency_credentials WHERE case_id=:id"),
                {"id": operation},
            ).scalar_one_or_none()
            try:
                if source is None:
                    raise Rejected(401, "invalid_recovery")
                self.mfa.emergency_source(source)
            except Rejected:
                state = "stale"
        return EmergencyView(operation, case["factors"], case["expires_at"], state)

    def lock_target(self, ident: UUID, org: UUID) -> dict[str, Any]:
        self.iam.installation_lock()
        row = self.target(ident, org, lock=True)
        for table, key in (("iam_sessions", "id"), ("iam_passkeys", "key_id")):
            self.s.execute(
                text(f"SELECT {key} FROM {table} WHERE account_id=:a ORDER BY {key} FOR UPDATE"),
                {"a": ident},
            ).all()
        return row

    def revoke(self, ident: UUID) -> None:
        for table in (
            "iam_credentials",
            "iam_recovery_credentials",
            "iam_reset_credentials",
            "iam_emergency_credentials",
        ):
            self.s.execute(
                text(f"SELECT id FROM {table} WHERE account_id=:a ORDER BY id FOR UPDATE"),
                {"a": ident},
            ).all()
            self.s.execute(
                text(f"UPDATE {table} SET consumed=true WHERE account_id=:a"), {"a": ident}
            )
        self.s.execute(
            text("SELECT id FROM iam_mfa_contexts WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": ident},
        ).all()
        self.s.execute(
            text(
                "UPDATE iam_mfa_contexts SET consumed=true,password_hash=NULL WHERE account_id=:a"
            ),
            {"a": ident},
        )
        self.s.execute(
            text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"), {"a": ident}
        )

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
        if request.factors == "password" and (
            before["recovery_pending"] or not request.expected.key_ready
        ):
            raise Rejected(409, "insufficient_scope")
        if request.factors == "passkey" and (
            before["password_reset_pending"] or not request.expected.password_ready
        ):
            raise Rejected(409, "insufficient_scope")
        previous = self.s.execute(
            text(
                "SELECT id FROM iam_emergency_cases WHERE account_id=:a "
                "ORDER BY row_version DESC LIMIT 1"
            ),
            {"a": request.account_id},
        ).scalar_one_or_none()
        if request.supersedes != previous:
            raise Rejected(409, "explicit_reissue_required")
        if self.s.execute(
            text(
                "SELECT 1 FROM iam_emergency_cases WHERE id=:id OR "
                "(organization_id=:org AND approval_ref=:ref)"
            ),
            {
                "id": request.operation_id,
                "org": request.organization_id,
                "ref": request.approval_ref,
            },
        ).first():
            raise Rejected(409, "execution_already_used")
        expiry = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:id AND kind='emergency'"),
            {"id": slot},
        ).scalar_one()
        if expiry <= now:
            raise Rejected(409, "expired_allocation")
        self.revoke(request.account_id)
        changes = ["row_version=row_version+1", "security_version=security_version+1"]
        if request.factors in ("password", "both"):
            changes += [
                "password_hash=NULL",
                "password_reset_pending=true",
                "reset_generation=reset_generation+1",
            ]
        if request.factors in ("passkey", "both"):
            changes += [
                "recovery_pending=true",
                "recovery_generation=recovery_generation+1",
                "key_set_version=key_set_version+1",
            ]
            self.s.execute(
                text(
                    "UPDATE iam_passkeys SET revoked_at=:n WHERE account_id=:a "
                    "AND revoked_at IS NULL"
                ),
                {"a": request.account_id, "n": now},
            )
        self.s.execute(
            text("UPDATE iam_accounts SET " + ",".join(changes) + " WHERE id=:a"),
            {"a": request.account_id},
        )
        after = self.mfa.account(request.account_id)
        params = {
            "id": request.operation_id,
            "org": request.organization_id,
            "a": request.account_id,
            "f": request.factors,
            "ref": request.approval_ref,
            "owner": request.owner_ref,
            "executor": authority.executor_ref,
            "uid": authority.executor_uid,
            "checked": request.checked_at,
            "approval": request.approval_valid_until,
            "issued": now,
            "expiry": expiry,
            "supersedes": request.supersedes,
            **{
                k: after[k]
                for k in (
                    "row_version",
                    "security_version",
                    "key_set_version",
                    "reset_generation",
                    "recovery_generation",
                )
            },
        }
        params.update({"expected_" + k: v for k, v in asdict(request.expected).items()})
        self.s.execute(
            text("""INSERT INTO iam_emergency_cases
          (id,organization_id,account_id,factors,approval_ref,owner_ref,executor_ref,executor_uid,
           checked_at,approval_valid_until,issued_at,expires_at,supersedes,row_version,
           security_version,key_set_version,reset_generation,recovery_generation,
           expected_row_version,expected_security_version,expected_key_set_version,
           expected_reset_generation,expected_recovery_generation,expected_password_reset_pending,
           expected_recovery_pending,expected_password_ready,expected_key_ready)
          VALUES(:id,:org,:a,:f,:ref,:owner,:executor,:uid,:checked,:approval,:issued,:expiry,
                 :supersedes,:row_version,:security_version,:key_set_version,:reset_generation,
                 :recovery_generation,:expected_row_version,:expected_security_version,:expected_key_set_version,
                 :expected_reset_generation,:expected_recovery_generation,:expected_password_reset_pending,
                 :expected_recovery_pending,:expected_password_ready,:expected_key_ready)"""),
            params,
        )
        raw = secrets.token_urlsafe(32)
        self.s.execute(
            text(
                "INSERT INTO iam_emergency_credentials "
                "(id,case_id,account_id,factors,digest,expires_at) VALUES(:id,:case,:a,:f,:d,:e)"
            ),
            {
                "id": slot,
                "case": request.operation_id,
                "f": request.factors,
                "a": request.account_id,
                "d": digest(raw),
                "e": expiry,
            },
        )
        return Setup(raw, expiry), self.event(
            before, after, request.operation_id, request.factors, authority.executor_ref, issue=True
        )

    def source(self, token: str, *, lock: bool = False) -> dict[str, Any]:
        row = self.s.execute(
            text("SELECT id,account_id FROM iam_emergency_credentials WHERE digest=:d"),
            {"d": digest(token)},
        ).first()
        if row is None:
            raise Rejected(401, "invalid_recovery")
        if lock:
            account = self.mfa.account(row.account_id, lock=False)
            self.lock_target(row.account_id, account["organization_id"])
            self.s.execute(
                text("SELECT id FROM iam_emergency_credentials WHERE id=:id FOR UPDATE"),
                {"id": row.id},
            ).one()
        return self.mfa.emergency_source(row.id)

    def recipient(self, token: str) -> EmergencyView:
        row = self.source(token)
        return EmergencyView(row["case_id"], row["factors"], row["expires_at"], "issued")

    def begin(self, token: str, password: str | None, slot: UUID) -> Ceremony:
        before = self.source(token)
        if before["factors"] == "password" or (
            (before["factors"] == "both") != (password is not None)
        ):
            raise Rejected(422, "invalid_request")
        account = self.iam._account(before["account_id"])
        encoded = (
            self.iam.passwords.create(password, account.login_id) if password is not None else None
        )
        source = self.source(token, lock=True)
        if source["case_id"] != before["case_id"]:
            raise Rejected(401, "invalid_recovery")
        self.s.execute(
            text(
                "UPDATE iam_mfa_contexts SET consumed=true,password_hash=NULL "
                "WHERE emergency_id=:id"
            ),
            {"id": source["id"]},
        )
        raw = self.mfa.create(
            account.id,
            slot,
            "emergency",
            emergency_id=source["id"],
            emergency_factors=source["factors"],
            password_hash=encoded,
            deadline=source["expires_at"],
        )
        return self.mfa.options(raw)

    def password(self, token: str, password: str) -> EmergencyChange:
        source = self.source(token)
        if source["factors"] != "password":
            raise Rejected(401, "invalid_recovery")
        account = self.iam._account(source["account_id"])
        encoded = self.iam.passwords.create(password, account.login_id)
        source = self.source(token, lock=True)
        before = self.mfa.account(account.id)
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=:h,password_reset_pending=false,"
                "row_version=row_version+1,security_version=security_version+1 WHERE id=:a"
            ),
            {"h": encoded, "a": account.id},
        )
        return self.finish(source, before)

    def complete(
        self, token: str | None, nonce: str | None, proof: RegistrationProof
    ) -> EmergencyChange:
        hint = self.mfa.context(token, nonce or "")
        if hint["purpose"] != "emergency" or proof.purpose != "emergency":
            raise Rejected(401, "invalid_ceremony")
        source = self.mfa.emergency_source(hint["emergency_id"])
        before = self.lock_target(source["account_id"], source["organization_id"])
        self.s.execute(
            text("SELECT id FROM iam_emergency_credentials WHERE id=:id FOR UPDATE"),
            {"id": source["id"]},
        ).one()
        source = self.mfa.emergency_source(source["id"])
        row = self.mfa.context(token, nonce or "", lock=True)
        if (
            row["id"] != proof.context_id
            or bytes(row["challenge"] or b"") != proof.challenge
            or source["factors"] not in ("passkey", "both")
            or ((source["factors"] == "both") != (row["password_hash"] is not None))
        ):
            raise Rejected(401, "invalid_ceremony")
        if self.snapshot(before).key_ready:
            raise Rejected(409, "conflict")
        self.s.execute(
            text(
                "INSERT INTO iam_passkeys "
                "(key_id,credential_id,account_id,public_key,sign_count,device_type,backed_up) "
                "VALUES(:key_id,:id,:a,:key,:count,:device,:backup)"
            ),
            {
                "key_id": uuid4(),
                "id": proof.credential_id,
                "a": before["id"],
                "key": proof.public_key,
                "count": proof.sign_count,
                "device": proof.device_type,
                "backup": proof.backed_up,
            },
        )
        change = (
            "password_hash=:h,password_reset_pending=false," if source["factors"] == "both" else ""
        )
        self.s.execute(
            text(
                "UPDATE iam_accounts SET " + change + "recovery_pending=false,"
                "key_set_version=key_set_version+1,row_version=row_version+1,"
                "security_version=security_version+1 WHERE id=:a"
            ),
            {"h": row["password_hash"], "a": before["id"]},
        )
        return self.finish(source, before)

    def finish(self, source: dict[str, Any], before: dict[str, Any]) -> EmergencyChange:
        self.revoke(before["id"])
        self.s.execute(
            text("UPDATE iam_emergency_cases SET completed_at=clock_timestamp() WHERE id=:id"),
            {"id": source["case_id"]},
        )
        return self.event(
            before,
            self.mfa.account(before["id"]),
            source["case_id"],
            source["factors"],
            source["executor_ref"],
            issue=False,
        )

    def event(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
        case: UUID,
        factors: str,
        executor: str,
        *,
        issue: bool,
    ) -> EmergencyChange:
        return EmergencyChange(
            "emergency_issue" if issue else "emergency_complete",
            before["organization_id"],
            None if issue else before["id"],
            before["id"],
            actor_role="SYSTEM_RECOVERY_OPERATOR" if issue else "RECOVERY_RECIPIENT",
            actor_scope="EMERGENCY_RECOVERY",
            before_state=before["state"],
            after_state=after["state"],
            before_version=before["row_version"],
            after_version=after["row_version"],
            before_key_set_version=before["key_set_version"],
            after_key_set_version=after["key_set_version"],
            before_recovery_generation=before["recovery_generation"],
            after_recovery_generation=after["recovery_generation"],
            before_reset_generation=before["reset_generation"],
            after_reset_generation=after["reset_generation"],
            before_password_ready=before["password_hash"] is not None,
            after_password_ready=after["password_hash"] is not None,
            emergency_case_id=case,
            emergency_factors=factors,
            executor_ref=executor,
            approval_mode="manual",
        )
