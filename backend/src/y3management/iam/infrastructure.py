"""IAM-owned persistence and lock plan. No cross-module private reads."""

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.passwords import Passwords
from y3management.iam.public import (
    Account,
    AccountRoles,
    Authentication,
    Caller,
    IdentityTransition,
    LoginProof,
    Reservation,
    Setup,
    TrainerAccountState,
    TrainerBinding,
    TrainerOperation,
    TrainerSetupProof,
)


def login_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,63}", value):
        raise Rejected(422, "invalid_request")
    return value.lower()


def digest(value: str) -> bytes:
    return hashlib.sha256(value.encode()).digest()


class IAM:
    def __init__(
        self, session: Session, passwords: Passwords, key: str, mode: str | None = None
    ) -> None:
        self.s = session
        self.passwords = passwords
        self.key = key.encode()
        self.mode = mode
        self._upgrades: dict[UUID, str] = {}

    def now(self) -> datetime:
        result: datetime = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        return result

    def _account(self, ident: UUID) -> Account:
        row = (
            self.s.execute(
                text(
                    "SELECT a.*,g.scope,g.branch_id FROM iam_accounts a "
                    "LEFT JOIN iam_admin_grants g ON g.account_id=a.id WHERE a.id=:id"
                ),
                {"id": ident},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise Rejected(404, "not_found")
        return Account(
            row["id"],
            row["organization_id"],
            row["login_id"],
            row["state"],
            row["branch_id"],
            row["scope"] == "ORGANIZATION",
            row["row_version"],
        )

    def installation_lock(self) -> None:
        self.s.execute(text("SELECT id FROM iam_installation WHERE id=1 FOR UPDATE")).one()

    def ensure_uninstalled(self) -> None:
        self.installation_lock()
        installed = self.s.execute(text("SELECT organization_id FROM iam_installation WHERE id=1"))
        if (
            installed.scalar_one() is not None
            or self.s.execute(text("SELECT 1 FROM iam_accounts LIMIT 1")).first()
        ):
            raise Rejected(409, "already_installed")

    def bootstrap(self, organization_id: UUID, identifier: str) -> Account:
        # Called after hash preparation in this adapter, prior to installation locks.
        encoded = self._upgrades.pop(UUID(int=0))
        ident = uuid4()
        self.s.execute(
            text(
                "INSERT INTO iam_accounts(id,organization_id,login_id,state,password_hash) "
                "VALUES(:id,:org,:login,'ACTIVE',:hash)"
            ),
            {"id": ident, "org": organization_id, "login": identifier, "hash": encoded},
        )
        self.s.execute(
            text("INSERT INTO iam_login_ids VALUES(:login,:id)"), {"login": identifier, "id": ident}
        )
        self.s.execute(
            text("INSERT INTO iam_admin_grants VALUES(:id,:org,'ORGANIZATION',NULL)"),
            {"id": ident, "org": organization_id},
        )
        self.s.execute(
            text("UPDATE iam_installation SET organization_id=:o WHERE id=1"),
            {"o": organization_id},
        )
        return self._account(ident)

    def prepare_master(self, identifier: str, password: str) -> None:
        self._upgrades[UUID(int=0)] = self.passwords.create(password, identifier)

    def preparation(self, token: str | None, nonce: str | None, consume: bool = False) -> None:
        row = (
            self.s.execute(
                text("SELECT * FROM iam_preparations WHERE digest=:d FOR UPDATE"),
                {"d": digest(token or "")},
            )
            .mappings()
            .first()
        )
        if (
            row is None
            or row["consumed"]
            or row["expires_at"] <= self.now()
            or not secrets.compare_digest(str(row["csrf"]), nonce or "")
        ):
            raise Rejected(403, "csrf_failed")
        if consume:
            self.s.execute(
                text("UPDATE iam_preparations SET consumed=true WHERE id=:id"), {"id": row["id"]}
            )

    def login_subject(self, identifier: str) -> Account | None:
        row = self.s.execute(
            text("SELECT id FROM iam_accounts WHERE login_id=:l"), {"l": identifier}
        ).first()
        return self._account(row.id) if row else None

    def verify_login(
        self, identifier: str, password: str, reservation: Reservation
    ) -> LoginProof | None:
        row = (
            self.s.execute(
                text(
                    "SELECT id,state,password_hash,security_version,recovery_pending,"
                    "password_reset_pending,trainer_role_epoch "
                    "FROM iam_accounts "
                    "WHERE login_id=:login"
                ),
                {"login": identifier},
            )
            .mappings()
            .first()
        )
        if (row["id"] if row else None) != reservation.account_id or (
            row["security_version"] if row else None
        ) != reservation.security_version:
            # Never verify a credential against a principal not admitted by this reservation.
            raise Rejected(503, "unavailable")
        encoded = (
            str(row["password_hash"])
            if row and row["state"] == "ACTIVE" and not row["password_reset_pending"]
            else None
        )
        valid, upgrade = self.passwords.verify(password, encoded)
        if (
            not valid
            or row is None
            or encoded is None
            or row["recovery_pending"]
            or row["password_reset_pending"]
        ):
            return None
        if upgrade:
            self._upgrades[row["id"]] = upgrade
        return LoginProof(
            row["id"],
            row["security_version"],
            hmac.digest(self.key, encoded.encode(), "sha256"),
            row["trainer_role_epoch"],
        )

    def login(
        self,
        proof: LoginProof,
        sid: UUID,
        preauth: str | None,
        nonce: str | None,
        reservation: Reservation,
    ) -> tuple[str, Account]:
        roles = self.account_roles(proof.account_id)
        if self.mode == "mfa" and roles.admin:
            raise Rejected(403, "mfa_required")
        if not roles.admin and not roles.trainer_granted:
            raise Rejected(401, "invalid_credentials")
        lock = "UPDATE" if proof.account_id in self._upgrades else "SHARE"
        row = (
            self.s.execute(
                text("SELECT * FROM iam_accounts WHERE id=:id FOR " + lock),
                {"id": proof.account_id},
            )
            .mappings()
            .one()
        )
        marker = hmac.digest(self.key, str(row["password_hash"]).encode(), "sha256")
        if (
            row["state"] != "ACTIVE"
            or row["recovery_pending"]
            or row["password_reset_pending"]
            or row["security_version"] != proof.security_version
            or row["trainer_role_epoch"] != proof.trainer_role_epoch
            or not hmac.compare_digest(marker, proof.credential_marker)
        ):
            raise Rejected(401, "invalid_credentials")
        budget_key = (
            bytes(row["login_budget_key"])
            if row["login_budget_key"] is not None
            else hmac.digest(self.key, row["login_id"].encode(), "sha256")
        )
        if (
            reservation.account_id != proof.account_id
            or reservation.security_version != proof.security_version
            or not hmac.compare_digest(reservation.key, budget_key)
        ):
            raise Rejected(503, "unavailable")
        if proof.account_id in self._upgrades:
            self.s.execute(
                text("UPDATE iam_accounts SET password_hash=:h WHERE id=:a"),
                {"h": self._upgrades.pop(proof.account_id), "a": proof.account_id},
            )
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        now = self.now()
        slot = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:i AND kind='session_slot'"),
            {"i": sid},
        ).scalar_one_or_none()
        if slot is None or slot <= now:
            raise Rejected(503, "unavailable")
        self.s.execute(
            text(
                "INSERT INTO "
                "iam_sessions(id,account_id,digest,csrf,security_version,trainer_role_epoch,"
                "created_at,last_activity,expires_at,revoked) "
                "VALUES(:id,:a,:d,:c,:v,:re,:n,:n,:e,false)"
            ),
            {
                "id": sid,
                "a": proof.account_id,
                "d": digest(token),
                "c": csrf,
                "v": proof.security_version,
                "re": proof.trainer_role_epoch,
                "n": now,
                "e": min(slot, now + timedelta(hours=8)),
            },
        )
        self.preparation(preauth, nonce, consume=True)
        return token, self._account(proof.account_id)

    def authenticate(
        self,
        token: str | None,
        *,
        management: bool = False,
        target: UUID | None = None,
        touch: bool = True,
        audience: Literal["admin", "account"] = "admin",
    ) -> Authentication:
        hint = self.s.execute(
            text("SELECT id,account_id FROM iam_sessions WHERE digest=:d"),
            {"d": digest(token or "")},
        ).first()
        if hint is None:
            raise Rejected(401, "unauthorized")
        if management:
            self.installation_lock()
        ids = sorted({hint.account_id, *([target] if target else [])}, key=str)
        for ident in ids:
            self.s.execute(
                text(
                    "SELECT id FROM iam_accounts WHERE id=:id FOR "
                    + ("UPDATE" if management else "SHARE")
                ),
                {"id": ident},
            ).first()
        # Lock every affected AuthSession in ID order; never actor first then a lower target ID.
        if management and target:
            self.s.execute(
                text(
                    "SELECT id FROM iam_sessions WHERE account_id IN (:actor,:target) "
                    "ORDER BY id FOR UPDATE"
                ),
                {"actor": hint.account_id, "target": target},
            ).all()
        else:
            self.s.execute(
                text("SELECT id FROM iam_sessions WHERE id=:id FOR UPDATE"), {"id": hint.id}
            ).first()
        row = (
            self.s.execute(
                text(
                    "SELECT s.*,a.state,a.recovery_pending,a.password_reset_pending,"
                    "a.security_version AS current_version,"
                    "a.trainer_role_epoch AS current_role_epoch "
                    "FROM iam_sessions s JOIN iam_accounts a ON a.id=s.account_id "
                    "WHERE s.id=:id"
                ),
                {"id": hint.id},
            )
            .mappings()
            .first()
        )
        roles = self.account_roles(hint.account_id)
        require_uv = self.mode == "mfa" and (audience == "admin" or roles.admin)
        now = self.now()
        if (
            row is None
            or (require_uv and row["assurance"] != "password_uv")
            or row["recovery_pending"]
            or row["password_reset_pending"]
            or row["revoked"]
            or row["state"] != "ACTIVE"
            or row["security_version"] != row["current_version"]
            or row["trainer_role_epoch"] != row["current_role_epoch"]
            or row["expires_at"] <= now
            or row["last_activity"] + timedelta(minutes=30) <= now
        ):
            raise Rejected(401, "unauthorized")
        if (
            require_uv
            and not self.s.execute(
                text(
                    "SELECT 1 FROM iam_passkeys WHERE account_id=:a AND revoked_at IS NULL LIMIT 1"
                ),
                {"a": hint.account_id},
            ).first()
        ):
            raise Rejected(401, "unauthorized")
        if not roles.admin:
            if audience == "admin":
                if roles.binding is not None:
                    raise Rejected(401, "unauthorized")
                # A valid former administrator lacks current authorization. Never return
                # this unsupported principal to management or refresh its session.
                raise Rejected(403, "forbidden")
            if not roles.trainer_granted:
                raise Rejected(401, "unauthorized")
        account = self._account(hint.account_id)
        if touch:
            self.s.execute(
                text("UPDATE iam_sessions SET last_activity=:n WHERE id=:id"),
                {"n": now, "id": hint.id},
            )
        caller = Caller(account.id, account.organization_id, account.branch_id, account.master)
        return Authentication(
            caller,
            hint.id,
            str(row["csrf"]),
            str(row["assurance"]),
            roles.binding,
            roles.trainer_granted,
        )

    def csrf(self, authentication: Authentication, nonce: str | None) -> None:
        if not secrets.compare_digest(authentication.csrf, nonce or ""):
            raise Rejected(403, "csrf_failed")

    def require_master(self, caller: Caller) -> None:
        if not caller.master:
            raise Rejected(403, "forbidden")

    def scoped_account(self, caller: Caller, ident: UUID) -> Account:
        self.require_master(caller)
        account = self._account(ident)
        if (
            account.organization_id != caller.organization_id
            or account.master
            or account.branch_id is None
        ):
            raise Rejected(404, "not_found")
        return account

    def lookup(self, caller: Caller, identifier: str) -> Account:
        self.require_master(caller)
        row = self.s.execute(
            text("SELECT id FROM iam_accounts WHERE organization_id=:org AND login_id=:l"),
            {"org": caller.organization_id, "l": identifier},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")
        return self.scoped_account(caller, row.id)

    def issue(self, caller: Caller, identifier: str, branch: UUID) -> Account:
        self.require_master(caller)
        ident = uuid4()
        self.s.execute(
            text(
                "INSERT INTO iam_accounts(id,organization_id,login_id,state) "
                "VALUES(:id,:o,:l,'PENDING_SETUP')"
            ),
            {"id": ident, "o": caller.organization_id, "l": identifier},
        )
        self.s.execute(
            text("INSERT INTO iam_login_ids VALUES(:l,:id)"), {"l": identifier, "id": ident}
        )
        self.s.execute(
            text("INSERT INTO iam_admin_grants VALUES(:id,:o,'BRANCH',:b)"),
            {"id": ident, "o": caller.organization_id, "b": branch},
        )
        return self._account(ident)

    def setup(self, account: Account, state_id: UUID, *, reissue: bool) -> tuple[Account, Setup]:
        if account.state != "PENDING_SETUP":
            raise Rejected(409, "conflict")
        self.s.execute(
            text("SELECT id FROM iam_credentials WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": account.id},
        ).all()
        self.s.execute(
            text("UPDATE iam_credentials SET consumed=true WHERE account_id=:a"), {"a": account.id}
        )
        if reissue:
            self.s.execute(
                text("UPDATE iam_accounts SET row_version=row_version+1 WHERE id=:a"),
                {"a": account.id},
            )
            account = self._account(account.id)
        token = secrets.token_urlsafe(32)
        expiry: datetime = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:id"), {"id": state_id}
        ).scalar_one()
        if expiry <= self.now():
            raise Rejected(503, "unavailable")
        self.s.execute(
            text("INSERT INTO iam_credentials VALUES(:id,:a,:d,:v,:e,false)"),
            {
                "id": state_id,
                "a": account.id,
                "d": digest(token),
                "v": account.version,
                "e": expiry,
            },
        )
        return account, Setup(token, expiry)

    def complete(
        self, token: str, password: str, preauth: str | None, nonce: str | None
    ) -> Account:
        if self.mode == "mfa":
            raise Rejected(403, "mfa_required")
        hint = self.s.execute(
            text(
                "SELECT c.account_id FROM iam_credentials c JOIN iam_accounts a ON "
                "a.id=c.account_id "
                "WHERE c.digest=:d AND NOT c.consumed AND c.expires_at>clock_timestamp() "
                "AND a.state='PENDING_SETUP' AND c.row_version=a.row_version"
            ),
            {"d": digest(token)},
        ).first()
        if hint is None:
            raise Rejected(400, "invalid_setup")
        before = self._account(hint.account_id)
        encoded = self.passwords.create(password, before.login_id)
        self.s.execute(
            text("SELECT id FROM iam_accounts WHERE id=:a FOR UPDATE"), {"a": before.id}
        ).one()
        self.s.execute(
            text("SELECT id FROM iam_sessions WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": before.id},
        ).all()
        self.preparation(preauth, nonce)
        row = (
            self.s.execute(
                text("SELECT * FROM iam_credentials WHERE digest=:d FOR UPDATE"),
                {"d": digest(token)},
            )
            .mappings()
            .first()
        )
        account = self._account(before.id)
        if (
            row is None
            or row["consumed"]
            or row["expires_at"] <= self.now()
            or account.state != "PENDING_SETUP"
            or row["row_version"] != account.version
        ):
            raise Rejected(400, "invalid_setup")
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=:h,state='ACTIVE',"
                "row_version=row_version+1,security_version=security_version+1 WHERE id=:a"
            ),
            {"a": account.id, "h": encoded},
        )
        self.s.execute(
            text("UPDATE iam_credentials SET consumed=true WHERE account_id=:a"), {"a": account.id}
        )
        self.preparation(preauth, nonce, consume=True)
        return self._account(account.id)

    def lock_credentials(self, ident: UUID) -> None:
        self.s.execute(
            text("SELECT id FROM iam_credentials WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": ident},
        ).all()

    def change(self, account: Account, branch: UUID | None, disable: bool) -> Account:
        if account.state != "ACTIVE":
            raise Rejected(409, "conflict")
        if not disable and account.branch_id == branch:
            return account
        self.s.execute(
            text("SELECT id FROM iam_credentials WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": account.id},
        ).all()
        self.s.execute(
            text(
                "UPDATE iam_accounts SET state=:s,row_version=row_version+1,"
                "security_version=security_version+1 WHERE id=:a"
            ),
            {"s": "DISABLED" if disable else "ACTIVE", "a": account.id},
        )
        if not disable:
            self.s.execute(
                text("UPDATE iam_admin_grants SET branch_id=:b WHERE account_id=:a"),
                {"a": account.id, "b": branch},
            )
        self.s.execute(
            text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"), {"a": account.id}
        )
        self.s.execute(
            text("UPDATE iam_credentials SET consumed=true WHERE account_id=:a"), {"a": account.id}
        )
        return self._account(account.id)

    def change_login_id(self, account: Account, identifier: str) -> Account:
        if account.state != "ACTIVE":
            raise Rejected(409, "conflict")
        if account.login_id == identifier:
            return account
        self.lock_credentials(account.id)
        owner = self.s.execute(
            text("SELECT account_id FROM iam_login_ids WHERE login_id=:l"), {"l": identifier}
        ).scalar_one_or_none()
        if owner is not None and owner != account.id:
            raise Rejected(409, "conflict")
        if owner is None:
            self.s.execute(
                text("INSERT INTO iam_login_ids VALUES(:l,:a)"),
                {"l": identifier, "a": account.id},
            )
        self.s.execute(
            text(
                "UPDATE iam_accounts SET login_id=:l,"
                "login_budget_key=COALESCE(login_budget_key,:k),"
                "row_version=row_version+1,security_version=security_version+1 WHERE id=:a"
            ),
            {
                "l": identifier,
                "k": hmac.digest(self.key, account.login_id.encode(), "sha256"),
                "a": account.id,
            },
        )
        self.s.execute(
            text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"), {"a": account.id}
        )
        self.s.execute(
            text("UPDATE iam_credentials SET consumed=true WHERE account_id=:a"), {"a": account.id}
        )
        return self._account(account.id)

    def prepare_password_change(
        self, ident: UUID, current_password: str, new_password: str
    ) -> LoginProof:
        # This adapter has only unlocked snapshots until final authentication below.
        row = (
            self.s.execute(
                text(
                    "SELECT login_id,state,password_hash,security_version,"
                    "recovery_pending,password_reset_pending,trainer_role_epoch "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": ident},
            )
            .mappings()
            .one()
        )
        if row["state"] != "ACTIVE" or row["recovery_pending"] or row["password_reset_pending"]:
            raise Rejected(401, "unauthorized")
        encoded = str(row["password_hash"])
        valid, _ = self.passwords.verify(current_password, encoded)
        if not valid:
            raise Rejected(401, "invalid_credentials")
        self._upgrades[ident] = self.passwords.create(new_password, row["login_id"])
        return LoginProof(
            ident,
            row["security_version"],
            hmac.digest(self.key, encoded.encode(), "sha256"),
            row["trainer_role_epoch"],
        )

    def change_password(self, proof: LoginProof) -> tuple[Account, Account]:
        # Account and every affected session are already locked in the canonical order.
        row = (
            self.s.execute(
                text(
                    "SELECT state,password_hash,security_version,recovery_pending,"
                    "password_reset_pending,trainer_role_epoch "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": proof.account_id},
            )
            .mappings()
            .one()
        )
        marker = hmac.digest(self.key, str(row["password_hash"]).encode(), "sha256")
        if (
            row["state"] != "ACTIVE"
            or row["recovery_pending"]
            or row["password_reset_pending"]
            or row["security_version"] != proof.security_version
            or row["trainer_role_epoch"] != proof.trainer_role_epoch
            or not hmac.compare_digest(marker, proof.credential_marker)
        ):
            raise Rejected(401, "unauthorized")
        before = self._account(proof.account_id)
        self.lock_credentials(proof.account_id)
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=:h,row_version=row_version+1,"
                "security_version=security_version+1 WHERE id=:a"
            ),
            {"h": self._upgrades.pop(proof.account_id), "a": proof.account_id},
        )
        self.s.execute(
            text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"),
            {"a": proof.account_id},
        )
        self.s.execute(
            text("UPDATE iam_credentials SET consumed=true WHERE account_id=:a"),
            {"a": proof.account_id},
        )
        self.s.execute(
            text("UPDATE iam_trainer_setup_credentials SET consumed=true WHERE account_id=:a"),
            {"a": proof.account_id},
        )
        return before, self._account(proof.account_id)

    def restore(self, account: Account) -> Account:
        # Caller and affected rows are locked by the management use case.
        if account.state != "DISABLED":
            raise Rejected(409, "conflict")
        self.s.execute(
            text(
                "UPDATE iam_accounts SET state='ACTIVE',row_version=row_version+1,"
                "security_version=security_version+1 WHERE id=:a"
            ),
            {"a": account.id},
        )
        # Never revive credentials or sessions issued before the account was disabled.
        # Keep the existing password, grant and independent login attempt budget.
        return self._account(account.id)

    def logout(self, authentication: Authentication) -> None:
        self.s.execute(
            text("UPDATE iam_sessions SET revoked=true WHERE id=:id"),
            {"id": authentication.session_id},
        )

    def gc_sessions(self) -> None:
        now = self.now()
        candidates = list(
            self.s.execute(
                text(
                    "SELECT DISTINCT account_id FROM iam_sessions "
                    "WHERE revoked OR expires_at<=:n OR last_activity<=:idle "
                    "ORDER BY account_id"
                ),
                {"n": now, "idle": now - timedelta(minutes=30)},
            ).scalars()
        )
        for account in candidates:
            self.s.execute(
                text("SELECT id FROM iam_accounts WHERE id=:a FOR SHARE"), {"a": account}
            ).first()
        rows = self.s.execute(
            text(
                "SELECT id FROM iam_sessions WHERE revoked OR expires_at<=:n "
                "OR last_activity<=:idle ORDER BY id FOR UPDATE"
            ),
            {"n": now, "idle": now - timedelta(minutes=30)},
        ).scalars()
        for ident in list(rows):
            self.s.execute(text("DELETE FROM iam_sessions WHERE id=:i"), {"i": ident})

    def master_management(self, caller: Caller, ident: UUID) -> Account:
        account = self.master_onboarding(caller, ident)
        if caller.account_id == ident:
            raise Rejected(404, "not_found")
        return account

    def revoke_management_sources(self, ident: UUID) -> None:
        # Installation, Accounts and all affected Sessions are already locked.
        for table in (
            "iam_credentials",
            "iam_mfa_contexts",
            "iam_recovery_credentials",
            "iam_reset_credentials",
            "iam_emergency_credentials",
        ):
            self.s.execute(
                text(f"SELECT id FROM {table} WHERE account_id=:a ORDER BY id FOR UPDATE"),
                {"a": ident},
            ).all()
            extra = ",password_hash=NULL" if table == "iam_mfa_contexts" else ""
            self.s.execute(
                text(f"UPDATE {table} SET consumed=true{extra} WHERE account_id=:a"),
                {"a": ident},
            )
        self.s.execute(
            text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"), {"a": ident}
        )

    def master_onboarding(self, caller: Caller, ident: UUID) -> Account:
        self.require_master(caller)
        account = self._account(ident)
        if account.organization_id != caller.organization_id or not account.master:
            raise Rejected(404, "not_found")
        return account

    def lookup_master(self, caller: Caller, identifier: str) -> Account:
        self.require_master(caller)
        ident = self.s.execute(
            text("SELECT id FROM iam_accounts WHERE organization_id=:o AND login_id=:l"),
            {"o": caller.organization_id, "l": identifier},
        ).scalar_one_or_none()
        if ident is None:
            raise Rejected(404, "not_found")
        return self.master_onboarding(caller, ident)

    def issue_master(self, caller: Caller, identifier: str) -> Account:
        self.require_master(caller)
        ident = uuid4()
        self.s.execute(
            text(
                "INSERT INTO iam_accounts(id,organization_id,login_id,state) "
                "VALUES(:id,:o,:l,'PENDING_SETUP')"
            ),
            {"id": ident, "o": caller.organization_id, "l": identifier},
        )
        self.s.execute(
            text("INSERT INTO iam_login_ids VALUES(:l,:id)"), {"l": identifier, "id": ident}
        )
        self.s.execute(
            text("INSERT INTO iam_admin_grants VALUES(:id,:o,'ORGANIZATION',NULL)"),
            {"id": ident, "o": caller.organization_id},
        )
        return self._account(ident)

    def account_roles(self, ident: UUID) -> AccountRoles:
        account = self._account(ident)
        row = self.s.execute(
            text(
                "SELECT account_id,organization_id,trainer_id,binding_version "
                "FROM iam_trainer_bindings WHERE account_id=:a"
            ),
            {"a": ident},
        ).first()
        grant = self.s.execute(
            text("SELECT granted FROM iam_trainer_role_grants WHERE account_id=:a"), {"a": ident}
        ).first()
        epoch = self.s.execute(
            text("SELECT trainer_role_epoch FROM iam_accounts WHERE id=:a"), {"a": ident}
        ).scalar_one()
        return AccountRoles(
            account,
            TrainerBinding(*row) if row else None,
            bool(grant and grant.granted),
            int(epoch),
        )

    def lock_login(self, ident: UUID) -> AccountRoles:
        self.installation_lock()
        self.s.execute(
            text("SELECT id FROM iam_accounts WHERE id=:a FOR UPDATE"), {"a": ident}
        ).one()
        self.s.execute(
            text("SELECT id FROM iam_sessions WHERE account_id=:a ORDER BY id FOR UPDATE"),
            {"a": ident},
        ).all()
        return self.account_roles(ident)

    def trainer_binding(self, org: UUID, trainer: UUID) -> TrainerBinding | None:
        row = self.s.execute(
            text(
                "SELECT account_id,organization_id,trainer_id,binding_version "
                "FROM iam_trainer_bindings WHERE organization_id=:o AND trainer_id=:t"
            ),
            {"o": org, "t": trainer},
        ).first()
        return TrainerBinding(*row) if row else None

    def trainer_state(self, org: UUID, trainer: UUID) -> TrainerAccountState:
        binding = self.trainer_binding(org, trainer)
        if binding is None:
            return TrainerAccountState(trainer, None, None, None, None, None)
        a = self._account(binding.account_id)
        expiry = self.s.execute(
            text(
                "SELECT expires_at FROM iam_trainer_setup_credentials "
                "WHERE account_id=:a AND NOT consumed "
                "AND expires_at>clock_timestamp() AND account_version=:v"
            ),
            {"a": a.id, "v": a.version},
        ).scalar_one_or_none()
        return TrainerAccountState(trainer, a.id, a.login_id, a.state, a.version, expiry)

    def trainer_operation(self, org: UUID, operation: UUID) -> TrainerOperation | None:
        row = self.s.execute(
            text(
                "SELECT operation_id,kind,trainer_id,account_id,committed_account_version "
                "FROM iam_trainer_account_operations WHERE organization_id=:o "
                "AND operation_id=:i"
            ),
            {"o": org, "i": operation},
        ).first()
        if row is None:
            return None
        return TrainerOperation(
            row.operation_id,
            row.kind,
            row.trainer_id,
            row.account_id,
            row.committed_account_version,
            self.trainer_state(org, row.trainer_id),
        )

    def lock_trainer_credentials(self, ident: UUID) -> None:
        self.lock_credentials(ident)
        self.s.execute(
            text(
                "SELECT id FROM iam_trainer_setup_credentials WHERE account_id=:a "
                "ORDER BY id FOR UPDATE"
            ),
            {"a": ident},
        ).all()

    def identity_transition(self, ident: UUID) -> IdentityTransition:
        roles = self.account_roles(ident)
        if roles.binding is None or roles.admin or not roles.trainer_granted:
            raise Rejected(409, "conflict")
        version = int(
            self.s.execute(
                text("SELECT security_version FROM iam_accounts WHERE id=:a"), {"a": ident}
            ).scalar_one()
        )
        return IdentityTransition(roles.account, version, roles.binding)

    def trainer_issue(
        self,
        caller: Caller,
        trainer: UUID,
        home: UUID,
        operation: UUID,
        identifier: str | None,
        expected: int | None,
        slot: UUID,
    ) -> tuple[TrainerOperation, Setup | None, IdentityTransition | None]:
        if not caller.master and caller.branch_id != home:
            raise Rejected(404, "not_found")
        kind = "issue" if identifier is not None else "reissue"
        payload: dict[str, str | int | None] = {"kind": kind, "trainer_id": str(trainer)}
        if identifier is not None:
            payload["login_id"] = login_id(identifier)
        else:
            payload["expected_account_version"] = expected
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).digest()
        old = self.s.execute(
            text(
                "SELECT fingerprint FROM iam_trainer_account_operations "
                "WHERE organization_id=:o AND operation_id=:i FOR UPDATE"
            ),
            {"o": caller.organization_id, "i": operation},
        ).first()
        if old:
            if bytes(old.fingerprint) != fingerprint:
                raise Rejected(409, "conflict")
            result = self.trainer_operation(caller.organization_id, operation)
            assert result is not None
            return result, None, None
        binding = self.trainer_binding(caller.organization_id, trainer)
        before = None
        if identifier is not None:
            if binding is not None:
                raise Rejected(409, "conflict")
            ident = uuid4()
            self.s.execute(
                text(
                    "INSERT INTO iam_accounts(id,organization_id,login_id,state) "
                    "VALUES(:a,:o,:l,'PENDING_SETUP')"
                ),
                {"a": ident, "o": caller.organization_id, "l": login_id(identifier)},
            )
            self.s.execute(
                text("INSERT INTO iam_login_ids VALUES(:l,:a)"),
                {"l": login_id(identifier), "a": ident},
            )
            self.s.execute(
                text(
                    "INSERT INTO iam_trainer_bindings(account_id,organization_id,trainer_id) "
                    "VALUES(:a,:o,:t)"
                ),
                {"a": ident, "o": caller.organization_id, "t": trainer},
            )
        else:
            if binding is None:
                raise Rejected(404, "not_found")
            ident = binding.account_id
            before = self.identity_transition(ident)
            if before.account.state != "PENDING_SETUP" or before.account.version != expected:
                raise Rejected(409, "conflict")
            self.s.execute(
                text("UPDATE iam_trainer_setup_credentials SET consumed=true WHERE account_id=:a"),
                {"a": ident},
            )
            self.s.execute(
                text("UPDATE iam_accounts SET row_version=row_version+1 WHERE id=:a"), {"a": ident}
            )
        if identifier is not None:
            self.s.execute(
                text("UPDATE iam_accounts SET trainer_role_epoch=1 WHERE id=:a"), {"a": ident}
            )
            self.s.execute(
                text(
                    "INSERT INTO iam_trainer_role_grants "
                    "(account_id,organization_id,trainer_id,granted,role_version,origin) "
                    "VALUES(:a,:o,:t,true,1,'i1_issue')"
                ),
                {"a": ident, "o": caller.organization_id, "t": trainer},
            )
        current = self.identity_transition(ident)
        expiry = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:i AND kind='credential'"),
            {"i": slot},
        ).scalar_one_or_none()
        if expiry is None or expiry <= self.now():
            raise Rejected(503, "unavailable")
        token = secrets.token_urlsafe(32)
        self.s.execute(
            text(
                "INSERT INTO iam_trainer_setup_credentials "
                "(id,purpose,organization_id,account_id,trainer_id,digest,account_version,"
                "security_version,binding_version,expires_at,trainer_role_epoch) "
                "VALUES(:i,'trainer_initial',:o,:a,:t,:d,:v,:sv,1,:e,:re)"
            ),
            {
                "i": slot,
                "o": caller.organization_id,
                "a": ident,
                "t": trainer,
                "d": digest(token),
                "v": current.account.version,
                "sv": current.security_version,
                "re": self.account_roles(ident).trainer_role_epoch,
                "e": expiry,
            },
        )
        self.s.execute(
            text(
                "INSERT INTO iam_trainer_account_operations "
                "(organization_id,operation_id,kind,trainer_id,account_id,actor_id,target_home_at_commit,"
                "canonical_version,fingerprint,committed_account_version) "
                "VALUES(:o,:i,:k,:t,:a,:actor,:h,1,:f,:v)"
            ),
            {
                "o": caller.organization_id,
                "i": operation,
                "k": kind,
                "t": trainer,
                "a": ident,
                "actor": caller.account_id,
                "h": home,
                "f": fingerprint,
                "v": current.account.version,
            },
        )
        result = self.trainer_operation(caller.organization_id, operation)
        assert result is not None
        return result, Setup(token, expiry), before

    def prepare_trainer_setup(self, token: str, password: str) -> TrainerSetupProof:
        row = (
            self.s.execute(
                text("SELECT * FROM iam_trainer_setup_credentials WHERE digest=:d"),
                {"d": digest(token)},
            )
            .mappings()
            .first()
        )
        if row is None or row["consumed"] or row["expires_at"] <= self.now():
            raise Rejected(400, "invalid_setup")
        current = self.identity_transition(row["account_id"])
        if current.account.state != "PENDING_SETUP":
            raise Rejected(400, "invalid_setup")
        self._upgrades[current.account.id] = self.passwords.create(
            password, current.account.login_id
        )
        return TrainerSetupProof(
            row["id"],
            current.account.id,
            row["organization_id"],
            row["trainer_id"],
            row["account_version"],
            row["security_version"],
            row["binding_version"],
            row["expires_at"],
            row["trainer_role_epoch"],
        )

    def lock_trainer_setup(
        self, proof: TrainerSetupProof, preauth: str | None, nonce: str | None
    ) -> TrainerBinding:
        self.lock_login(proof.account_id)
        self.preparation(preauth, nonce)
        self.lock_trainer_credentials(proof.account_id)
        self._check_trainer_source(proof, consumed=False)
        return self.identity_transition(proof.account_id).binding

    def _check_trainer_source(self, proof: TrainerSetupProof, *, consumed: bool) -> None:
        row = (
            self.s.execute(
                text(
                    "SELECT c.*,s.kind,s.expires_at AS slot_expiry,"
                    "a.recovery_pending,a.password_reset_pending "
                    "FROM iam_trainer_setup_credentials c "
                    "JOIN iam_security_states s ON s.id=c.id "
                    "JOIN iam_accounts a ON a.id=c.account_id WHERE c.id=:i"
                ),
                {"i": proof.source_id},
            )
            .mappings()
            .first()
        )
        current = self.identity_transition(proof.account_id)
        delta = 1 if consumed else 0
        if (
            row is None
            or row["purpose"] != "trainer_initial"
            or row["kind"] != "credential"
            or row["recovery_pending"]
            or row["password_reset_pending"]
            or row["consumed"] != consumed
            or row["expires_at"] != proof.expires_at
            or row["slot_expiry"] != proof.expires_at
            or proof.expires_at <= self.now()
            or row["account_id"] != proof.account_id
            or row["trainer_id"] != proof.trainer_id
            or row["organization_id"] != proof.organization_id
            or row["account_version"] != proof.account_version
            or row["security_version"] != proof.security_version
            or row["trainer_role_epoch"] != proof.trainer_role_epoch
            or row["binding_version"] != proof.binding_version
            or row["trainer_role_epoch"] != proof.trainer_role_epoch
            or self.account_roles(proof.account_id).trainer_role_epoch != proof.trainer_role_epoch
            or current.binding
            != TrainerBinding(
                proof.account_id, proof.organization_id, proof.trainer_id, proof.binding_version
            )
            or current.account.version != proof.account_version + delta
            or current.security_version != proof.security_version + delta
            or current.account.state != ("ACTIVE" if consumed else "PENDING_SETUP")
        ):
            raise Rejected(400, "invalid_setup")

    def complete_trainer_setup(
        self, proof: TrainerSetupProof, preauth: str | None, nonce: str | None
    ) -> IdentityTransition:
        self._check_trainer_source(proof, consumed=False)
        before = self.identity_transition(proof.account_id)
        self.s.execute(
            text(
                "UPDATE iam_accounts SET password_hash=:h,state='ACTIVE',row_version=row_version+1,"
                "security_version=security_version+1 WHERE id=:a"
            ),
            {"a": proof.account_id, "h": self._upgrades.pop(proof.account_id)},
        )
        self.s.execute(
            text("UPDATE iam_trainer_setup_credentials SET consumed=true WHERE account_id=:a"),
            {"a": proof.account_id},
        )
        self.preparation(preauth, nonce, consume=True)
        return before

    def confirm_trainer_setup(self, proof: TrainerSetupProof) -> None:
        self._check_trainer_source(proof, consumed=True)

    def confirm_trainer_delivery(self, operation: TrainerOperation, slot: UUID) -> None:
        current = self.identity_transition(operation.account_id)
        row = (
            self.s.execute(
                text("SELECT * FROM iam_trainer_setup_credentials WHERE id=:i"), {"i": slot}
            )
            .mappings()
            .one()
        )
        proof = TrainerSetupProof(
            slot,
            current.account.id,
            current.account.organization_id,
            current.binding.trainer_id,
            row["account_version"],
            row["security_version"],
            row["binding_version"],
            row["expires_at"],
            row["trainer_role_epoch"],
        )
        self._check_trainer_source(proof, consumed=False)
        if operation.committed_account_version != current.account.version:
            raise Rejected(409, "conflict")

    def confirm_identity_transition(
        self,
        before: IdentityTransition,
        *,
        changed: bool,
        authentication: Authentication | None = None,
        logout: bool = False,
    ) -> None:
        current = self.identity_transition(before.account.id)
        delta = int(changed)
        if (
            current.binding != before.binding
            or current.account.state != "ACTIVE"
            or current.account.version != before.account.version + delta
            or current.security_version != before.security_version + delta
        ):
            raise Rejected(401, "unauthorized")
        if authentication is not None:
            row = (
                self.s.execute(
                    text("SELECT * FROM iam_sessions WHERE id=:i"), {"i": authentication.session_id}
                )
                .mappings()
                .one()
            )
            now = self.now()
            if (
                row["account_id"] != before.account.id
                or row["security_version"] != before.security_version
                or row["revoked"] != (changed or logout)
                or row["expires_at"] <= now
                or row["last_activity"] + timedelta(minutes=30) <= now
            ):
                raise Rejected(401, "unauthorized")

    def confirm_login(self, proof: LoginProof, reservation: Reservation, sid: UUID) -> None:
        row = (
            self.s.execute(
                text(
                    "SELECT s.expires_at,s.account_id,s.security_version,s.revoked,a.state,"
                    "s.trainer_role_epoch,a.trainer_role_epoch AS current_role_epoch,"
                    "a.security_version AS current_version,t.lease_until,t.outcome "
                    "FROM iam_sessions s JOIN iam_accounts a ON a.id=s.account_id "
                    "JOIN iam_attempts t ON t.id=:r AND t.key=:k WHERE s.id=:s"
                ),
                {"s": sid, "r": reservation.id, "k": reservation.key},
            )
            .mappings()
            .first()
        )
        now = self.now()
        if (
            row is None
            or row["account_id"] != proof.account_id
            or row["security_version"] != proof.security_version
            or row["trainer_role_epoch"] != proof.trainer_role_epoch
            or row["current_version"] != proof.security_version
            or row["current_role_epoch"] != proof.trainer_role_epoch
            or row["state"] != "ACTIVE"
            or row["revoked"]
            or row["expires_at"] <= now
            or row["lease_until"] <= now
            or row["outcome"] != "pending"
        ):
            raise Rejected(401, "invalid_credentials")

    def revoke_undelivered_session(self, sid: UUID) -> None:
        self.s.execute(text("UPDATE iam_sessions SET revoked=true WHERE id=:i"), {"i": sid})

    def confirm_preparation(self, token: str | None, nonce: str | None) -> None:
        row = self.s.execute(
            text("SELECT consumed,expires_at,csrf FROM iam_preparations WHERE digest=:d"),
            {"d": digest(token or "")},
        ).first()
        if (
            row is None
            or not row.consumed
            or row.expires_at <= self.now()
            or not secrets.compare_digest(row.csrf, nonce or "")
        ):
            raise Rejected(403, "csrf_failed")
