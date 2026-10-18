"""IAM-owned persistence and lock plan. No cross-module private reads."""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.passwords import Passwords
from y3management.iam.public import Account, Authentication, Caller, LoginProof, Reservation, Setup


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
                    "password_reset_pending "
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
            row["id"], row["security_version"], hmac.digest(self.key, encoded.encode(), "sha256")
        )

    def login(
        self,
        proof: LoginProof,
        sid: UUID,
        preauth: str | None,
        nonce: str | None,
        reservation: Reservation,
    ) -> tuple[str, Account]:
        if self.mode == "mfa":
            raise Rejected(403, "mfa_required")
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
                "iam_sessions(id,account_id,digest,csrf,security_version,"
                "created_at,last_activity,expires_at,revoked) "
                "VALUES(:id,:a,:d,:c,:v,:n,:n,:e,false)"
            ),
            {
                "id": sid,
                "a": proof.account_id,
                "d": digest(token),
                "c": csrf,
                "v": proof.security_version,
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
                    "a.security_version AS current_version "
                    "FROM iam_sessions s JOIN iam_accounts a ON a.id=s.account_id "
                    "WHERE s.id=:id"
                ),
                {"id": hint.id},
            )
            .mappings()
            .first()
        )
        now = self.now()
        if (
            row is None
            or (self.mode == "mfa" and row["assurance"] != "password_uv")
            or row["recovery_pending"]
            or row["password_reset_pending"]
            or row["revoked"]
            or row["state"] != "ACTIVE"
            or row["security_version"] != row["current_version"]
            or row["expires_at"] <= now
            or row["last_activity"] + timedelta(minutes=30) <= now
        ):
            raise Rejected(401, "unauthorized")
        if (
            self.mode == "mfa"
            and not self.s.execute(
                text(
                    "SELECT 1 FROM iam_passkeys WHERE account_id=:a AND revoked_at IS NULL LIMIT 1"
                ),
                {"a": hint.account_id},
            ).first()
        ):
            raise Rejected(401, "unauthorized")
        account = self._account(hint.account_id)
        if touch:
            self.s.execute(
                text("UPDATE iam_sessions SET last_activity=:n WHERE id=:id"),
                {"n": now, "id": hint.id},
            )
        caller = Caller(account.id, account.organization_id, account.branch_id, account.master)
        return Authentication(caller, hint.id, str(row["csrf"]))

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
                    "recovery_pending,password_reset_pending "
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
            ident, row["security_version"], hmac.digest(self.key, encoded.encode(), "sha256")
        )

    def change_password(self, proof: LoginProof) -> tuple[Account, Account]:
        # Account and every affected session are already locked in the canonical order.
        row = (
            self.s.execute(
                text(
                    "SELECT state,password_hash,security_version,recovery_pending,"
                    "password_reset_pending "
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
