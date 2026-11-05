"""Password reset with current principal, source and policy revalidation."""

import secrets
from typing import Any
from uuid import UUID

from sqlalchemy import text

from y3management.contracts import Rejected
from y3management.iam.infrastructure import IAM, digest
from y3management.iam.public import (
    Account,
    AccountRoles,
    Caller,
    ResetChange,
    ResetProof,
    ResetState,
    Setup,
)


class PasswordReset:
    def __init__(self, iam: IAM) -> None:
        self.iam = iam
        self.s = iam.s

    @staticmethod
    def _reset_supported(roles: AccountRoles) -> bool:
        return (
            roles.admin
            or roles.operator is not None
            or (
                roles.binding is not None
                and roles.binding.organization_id == roles.account.organization_id
            )
        )

    def _reset_target(self, caller: Caller, ident: UUID) -> Account:
        self.iam.policy()
        self.iam.require_master(caller)
        roles = self.iam.account_roles(ident)
        account = roles.account
        if (
            account.organization_id != caller.organization_id
            or ident == caller.account_id
            or not self._reset_supported(roles)
        ):
            raise Rejected(404, "not_found")
        if account.state != "ACTIVE":
            raise Rejected(409, "conflict")
        return account

    def _reset_account(self, ident: UUID, *, lock: bool = True) -> dict[str, Any]:
        row = (
            self.s.execute(
                text("SELECT * FROM iam_accounts WHERE id=:id" + (" FOR UPDATE" if lock else "")),
                {"id": ident},
            )
            .mappings()
            .first()
        )
        if row is None or not self._reset_supported(self.iam.account_roles(ident)):
            raise Rejected(401, "invalid_reset")
        return dict(row)

    def reset_state(self, caller: Caller, ident: UUID) -> ResetState:
        target = self._reset_target(caller, ident)
        account = self._reset_account(ident)
        expiry = self.s.execute(
            text(
                "SELECT expires_at FROM iam_reset_credentials WHERE policy_version=2 AND "
                "account_id=:a "
                "AND generation=:g AND row_version=:v AND NOT consumed"
            ),
            {"a": ident, "g": account["reset_generation"], "v": target.version},
        ).scalar_one_or_none()
        return ResetState(
            ident,
            target.version,
            account["password_reset_pending"],
            account["reset_generation"],
            expiry,
        )

    def reset_change(self, before: dict[str, Any]) -> ResetChange:
        after = self._reset_account(before["id"])
        return ResetChange(
            before["reset_generation"],
            after["reset_generation"],
            before["password_hash"] is not None,
            after["password_hash"] is not None,
        )

    def start_reset(
        self,
        caller: Caller,
        ident: UUID,
        version: int,
        generation: int,
        slot: UUID,
        *,
        reissue: bool,
    ) -> tuple[Account, Account, Setup, ResetChange]:
        before = self._reset_target(caller, ident)
        account = self._reset_account(ident)
        if (
            before.version != version
            or account["reset_generation"] != generation
            or account["recovery_pending"]
            or account["password_reset_pending"] != reissue
        ):
            raise Rejected(409, "conflict")
        # The current password-authenticated Master is distinct from the target, and remains usable.
        # Installation + ordered Accounts/Sessions were acquired by authenticate.
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=NULL,password_reset_pending=true,"
                "reset_generation=reset_generation+1,row_version=row_version+1,"
                "security_version=security_version+1 WHERE id=:a"
            ),
            {"a": ident},
        )
        self.iam.revoke_management_sources(ident)
        self.s.execute(
            text("UPDATE iam_credentials SET consumed=true WHERE account_id=:a"), {"a": ident}
        )
        self.s.execute(
            text("UPDATE iam_reset_credentials SET consumed=true WHERE account_id=:a"), {"a": ident}
        )
        current = self._reset_account(ident)
        expiry = self.s.execute(
            text(
                "SELECT expires_at FROM iam_security_states WHERE id=:id AND kind='password_reset'"
            ),
            {"id": slot},
        ).scalar_one()
        if expiry <= self.iam.now():
            raise Rejected(503, "unavailable")
        raw = secrets.token_urlsafe(32)
        self.s.execute(
            text(
                "INSERT INTO iam_reset_credentials "
                "(id,account_id,digest,row_version,security_version,generation,"
                "expires_at,policy_version) "
                "VALUES(:id,:a,:d,:v,:s,:g,:e,2)"
            ),
            {
                "id": slot,
                "a": ident,
                "d": digest(raw),
                "v": current["row_version"],
                "s": current["security_version"],
                "g": current["reset_generation"],
                "e": expiry,
            },
        )
        return before, self.iam._account(ident), Setup(raw, expiry), self.reset_change(account)

    def reset_source(self, ident: UUID, account: dict[str, Any], *, lock: bool) -> dict[str, Any]:
        source = (
            self.s.execute(
                text(
                    "SELECT * FROM iam_reset_credentials WHERE policy_version=2 AND id=:id"
                    + (" FOR UPDATE" if lock else "")
                ),
                {"id": ident},
            )
            .mappings()
            .first()
        )
        if (
            source is None
            or source["consumed"]
            or source["expires_at"] <= self.iam.now()
            or source["account_id"] != account["id"]
            or source["row_version"] != account["row_version"]
            or source["security_version"] != account["security_version"]
            or source["generation"] != account["reset_generation"]
            or not account["password_reset_pending"]
            or account["recovery_pending"]
            or account["state"] != "ACTIVE"
        ):
            raise Rejected(401, "invalid_reset")
        if not self._reset_supported(self.iam.account_roles(account["id"])):
            raise Rejected(401, "invalid_reset")
        return dict(source)

    def prepare_reset(self, token: str, password: str) -> ResetProof:
        policy = self.iam.policy()
        hint = self.s.execute(
            text(
                "SELECT id,account_id FROM iam_reset_credentials WHERE policy_version=2 AND "
                "digest=:d"
            ),
            {"d": digest(token)},
        ).first()
        if hint is None:
            raise Rejected(401, "invalid_reset")
        account = self._reset_account(hint.account_id, lock=False)
        source = self.reset_source(hint.id, account, lock=False)
        scope = self.iam.account_roles(hint.account_id).operator_grant
        # Bounded Argon2 with no business row locks; final proof revalidation below.
        self.iam._upgrades[hint.account_id] = self.iam.passwords.create(
            password, account["login_id"]
        )
        return ResetProof(
            hint.id,
            hint.account_id,
            account["security_version"],
            account["reset_generation"],
            account["trainer_role_epoch"],
            scope,
            source["expires_at"],
            policy=policy,
        )

    def complete_reset(self, proof: ResetProof) -> tuple[Account, Account, ResetChange]:
        self.iam.installation_lock()
        self.iam.check_policy(proof.policy)
        account = self._reset_account(proof.account_id)
        self.s.execute(
            text("SELECT id FROM iam_sessions WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": proof.account_id},
        ).all()
        self.iam.lock_trainer_credentials(proof.account_id)
        source = self.reset_source(proof.source_id, account, lock=True)
        if (
            source["expires_at"] != proof.expires_at
            or proof.operator_grant != self.iam.account_roles(proof.account_id).operator_grant
            or proof.security_version != account["security_version"]
            or proof.generation != account["reset_generation"]
            or proof.trainer_role_epoch != account["trainer_role_epoch"]
        ):
            raise Rejected(401, "invalid_reset")
        before = self.iam._account(proof.account_id)
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=:h,password_reset_pending=false,"
                "row_version=row_version+1,security_version=security_version+1 WHERE id=:a"
            ),
            {"h": self.iam._upgrades.pop(proof.account_id), "a": proof.account_id},
        )
        self.iam.revoke_management_sources(proof.account_id)
        self.s.execute(
            text("UPDATE iam_reset_credentials SET consumed=true WHERE account_id=:a"),
            {"a": proof.account_id},
        )
        return before, self.iam._account(proof.account_id), self.reset_change(account)

    def confirm_complete(self, proof: ResetProof) -> None:
        self.iam.check_policy(proof.policy)
        if proof.operator_grant != self.iam.account_roles(proof.account_id).operator_grant:
            raise Rejected(401, "invalid_reset")
        valid = self.s.execute(
            text(
                "SELECT 1 FROM iam_reset_credentials WHERE id=:i "
                "AND account_id=:a AND policy_version=2 AND consumed AND "
                "expires_at=:deadline AND expires_at>clock_timestamp()"
            ),
            {"i": proof.source_id, "a": proof.account_id, "deadline": proof.expires_at},
        ).first()
        if valid is None:
            raise Rejected(401, "invalid_reset")
