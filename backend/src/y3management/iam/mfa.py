"""IAM-owned WebAuthn adapter. Library verification, explicit ceremony capabilities."""

import hmac
import secrets
from datetime import timedelta
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy import text
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    parse_authentication_credential_json,
    parse_client_data_json,
    parse_registration_credential_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

from y3management.contracts import Rejected
from y3management.iam.infrastructure import IAM, digest
from y3management.iam.public import (
    Account,
    Authentication,
    Ceremony,
    LoginProof,
    RegistrationProof,
    Reservation,
    Setup,
)


class MFA:
    def __init__(self, iam: IAM, origin: str) -> None:
        self.iam = iam
        self.s = iam.s
        self.origin = origin
        self.rp = urlsplit(origin).hostname or ""

    def enabled(self) -> None:
        if self.iam.mode != "mfa":
            raise Rejected(403, "mfa_unavailable")

    def account(self, ident: UUID, *, lock: bool = True) -> dict[str, Any]:
        row = (
            self.s.execute(
                text("SELECT * FROM iam_accounts WHERE id=:id" + (" FOR UPDATE" if lock else "")),
                {"id": ident},
            )
            .mappings()
            .one()
        )
        return dict(row)

    def context(
        self, token: str | None, nonce: str | None = None, *, lock: bool = False
    ) -> dict[str, Any]:
        self.enabled()
        hint = self.s.execute(
            text("SELECT account_id FROM iam_mfa_contexts WHERE digest=:d"),
            {"d": digest(token or "")},
        ).first()
        if hint is None:
            raise Rejected(401, "invalid_ceremony")
        account = self.account(hint.account_id, lock=lock)
        row = (
            self.s.execute(
                text(
                    "SELECT * FROM iam_mfa_contexts WHERE digest=:d"
                    + (" FOR UPDATE" if lock else "")
                ),
                {"d": digest(token or "")},
            )
            .mappings()
            .first()
        )
        if (
            row is None
            or row["consumed"]
            or row["expires_at"] <= self.iam.now()
            or row["security_version"] != account["security_version"]
            or row["row_version"] != account["row_version"]
            or account["state"] == "DISABLED"
        ):
            raise Rejected(401, "invalid_ceremony")
        if nonce is not None and not secrets.compare_digest(row["csrf"], nonce):
            raise Rejected(403, "csrf_failed")
        if row["source_id"] is not None:
            source = (
                self.s.execute(
                    text("SELECT * FROM iam_credentials WHERE id=:id"), {"id": row["source_id"]}
                )
                .mappings()
                .first()
            )
            if (
                source is None
                or source["consumed"]
                or source["expires_at"] <= self.iam.now()
                or source["row_version"] != account["row_version"]
            ):
                raise Rejected(401, "invalid_ceremony")
        return dict(row)

    def create(self, ident: UUID, state_id: UUID, purpose: str, **values: Any) -> str:
        self.enabled()
        account = self.account(ident)
        expiry = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:id"), {"id": state_id}
        ).scalar_one()
        expiry = min(
            expiry,
            self.iam.now() + timedelta(minutes=30 if purpose == "install" else 5),
            values.pop("deadline", expiry),
        )
        if expiry <= self.iam.now():
            raise Rejected(401, "invalid_ceremony")
        raw = secrets.token_urlsafe(32)
        params = dict(
            id=state_id,
            digest=digest(raw),
            csrf=secrets.token_urlsafe(32),
            account_id=ident,
            purpose=purpose,
            expires_at=expiry,
            security_version=account["security_version"],
            row_version=account["row_version"],
            challenge=None,
            password_hash=None,
            marker=None,
            source_id=None,
            session_id=None,
            attempt_id=None,
            budget_key=None,
        )
        params.update(values)
        columns = ",".join(params)
        binds = ",".join(":" + k for k in params)
        self.s.execute(text(f"INSERT INTO iam_mfa_contexts({columns}) VALUES({binds})"), params)
        return raw

    def installation(self, account: Account, state_id: UUID) -> Setup:
        raw = self.create(account.id, state_id, "install")
        return Setup(raw, self.context(raw)["expires_at"])

    def options(self, raw: str) -> Ceremony:
        row = self.context(raw, lock=True)
        challenge = bytes(row["challenge"]) if row["challenge"] else secrets.token_bytes(32)
        self.s.execute(
            text("UPDATE iam_mfa_contexts SET challenge=:c WHERE id=:id"),
            {"c": challenge, "id": row["id"]},
        )
        account = self.iam._account(row["account_id"])
        descriptors = [
            PublicKeyCredentialDescriptor(id=bytes(v))
            for v in self.s.execute(
                text(
                    "SELECT credential_id FROM iam_passkeys WHERE "
                    "account_id=:a ORDER BY credential_id"
                ),
                {"a": account.id},
            ).scalars()
        ]
        if row["purpose"] == "login":
            if not descriptors:
                raise Rejected(401, "invalid_credentials")
            options = options_to_json(
                generate_authentication_options(
                    rp_id=self.rp,
                    challenge=challenge,
                    timeout=300000,
                    allow_credentials=descriptors,
                    user_verification=UserVerificationRequirement.REQUIRED,
                )
            )
        else:
            options = options_to_json(
                generate_registration_options(
                    rp_id=self.rp,
                    rp_name="Y3",
                    user_id=account.id.bytes,
                    user_name=account.login_id,
                    challenge=challenge,
                    timeout=300000,
                    exclude_credentials=descriptors,
                    authenticator_selection=AuthenticatorSelectionCriteria(
                        user_verification=UserVerificationRequirement.REQUIRED
                    ),
                )
            )
        return Ceremony(raw, row["csrf"], options, row["expires_at"])

    def begin_install(self, token: str) -> Ceremony:
        row = self.context(token, lock=True)
        if (
            row["purpose"] != "install"
            or self.s.execute(
                text("SELECT 1 FROM iam_passkeys WHERE account_id=:a"), {"a": row["account_id"]}
            ).first()
        ):
            raise Rejected(401, "invalid_ceremony")
        return self.options(token)

    def begin_setup(self, token: str, password: str, state_id: UUID) -> Ceremony:
        self.enabled()
        source = (
            self.s.execute(
                text("SELECT * FROM iam_credentials WHERE digest=:d"), {"d": digest(token)}
            )
            .mappings()
            .first()
        )
        if source is None:
            raise Rejected(400, "invalid_setup")
        before = self.iam._account(source["account_id"])
        encoded = self.iam.passwords.create(password, before.login_id)
        account = self.account(before.id)
        source = (
            self.s.execute(
                text("SELECT * FROM iam_credentials WHERE digest=:d FOR UPDATE"),
                {"d": digest(token)},
            )
            .mappings()
            .one()
        )
        if (
            source["consumed"]
            or source["expires_at"] <= self.iam.now()
            or account["state"] != "PENDING_SETUP"
            or source["row_version"] != account["row_version"]
        ):
            raise Rejected(400, "invalid_setup")
        # Restart invalidates every prior derived ceremony and its staged password.
        self.s.execute(
            text(
                "UPDATE iam_mfa_contexts SET consumed=true,password_hash=NULL "
                "WHERE account_id=:a AND purpose='setup'"
            ),
            {"a": before.id},
        )
        raw = self.create(
            before.id,
            state_id,
            "setup",
            source_id=source["id"],
            password_hash=encoded,
            deadline=source["expires_at"],
        )
        return self.options(raw)

    def begin_add(self, authentication: Authentication, state_id: UUID) -> Ceremony:
        raw = self.create(
            authentication.caller.account_id, state_id, "add", session_id=authentication.session_id
        )
        return self.options(raw)

    def failure_subject(self, reservation: Reservation) -> Account | None:
        self.enabled()
        if reservation.account_id is None:
            return None
        found = (
            self.s.execute(
                text("SELECT * FROM iam_accounts WHERE id=:id"), {"id": reservation.account_id}
            )
            .mappings()
            .first()
        )
        if found is None:
            return None
        try:
            self.bind_reservation(dict(found), reservation)
        except Rejected:
            return None
        return self.iam._account(reservation.account_id)

    def bind_reservation(self, account: dict[str, Any], reservation: Reservation) -> None:
        actual_key = (
            bytes(account["login_budget_key"])
            if account["login_budget_key"] is not None
            else hmac.digest(self.iam.key, account["login_id"].encode(), "sha256")
        )
        if (
            reservation.account_id != account["id"]
            or reservation.security_version != account["security_version"]
            or not hmac.compare_digest(reservation.key, actual_key)
        ):
            raise Rejected(503, "unavailable")

    def begin_login(self, proof: LoginProof, reservation: Reservation, state_id: UUID) -> Ceremony:
        account = self.account(proof.account_id)
        self.bind_reservation(account, reservation)
        if (
            account["state"] != "ACTIVE"
            or account["security_version"] != proof.security_version
            or not hmac.compare_digest(
                proof.credential_marker,
                hmac.digest(self.iam.key, account["password_hash"].encode(), "sha256"),
            )
        ):
            raise Rejected(401, "invalid_credentials")
        attempt = self.s.execute(
            text(
                "SELECT lease_until FROM iam_attempts WHERE id=:id "
                "AND key=:key AND stage='waiting' AND outcome='pending'"
            ),
            {"id": reservation.id, "key": reservation.key},
        ).first()
        if attempt is None:
            raise Rejected(401, "invalid_credentials")
        raw = self.create(
            proof.account_id,
            state_id,
            "login",
            marker=proof.credential_marker,
            attempt_id=reservation.id,
            budget_key=reservation.key,
            deadline=attempt.lease_until,
        )
        return self.options(raw)

    def reservation(self, token: str | None, nonce: str | None) -> Reservation:
        row = self.context(token, nonce or "")
        if row["purpose"] != "login":
            raise Rejected(401, "invalid_ceremony")
        return Reservation(
            bytes(row["budget_key"]), row["attempt_id"], row["account_id"], row["security_version"]
        )

    def consume(self, row: dict[str, Any]) -> None:
        self.s.execute(
            text("UPDATE iam_mfa_contexts SET consumed=true,password_hash=NULL WHERE id=:id"),
            {"id": row["id"]},
        )

    def verify_registration(
        self,
        token: str | None,
        nonce: str | None,
        payload: str,
    ) -> RegistrationProof:
        before = self.context(token, nonce or "")
        if before["purpose"] not in ("install", "setup", "add") or before["challenge"] is None:
            raise Rejected(401, "invalid_ceremony")
        try:
            parsed = parse_registration_credential_json(payload)
            if parse_client_data_json(parsed.response.client_data_json).cross_origin:
                raise ValueError()
            verified = verify_registration_response(
                credential=parsed,
                expected_challenge=bytes(before["challenge"]),
                expected_rp_id=self.rp,
                expected_origin=self.origin,
                require_user_presence=True,
                require_user_verification=True,
            )
        except Exception:
            raise Rejected(401, "invalid_passkey") from None
        return RegistrationProof(
            before["id"],
            bytes(before["challenge"]),
            verified.credential_id,
            verified.credential_public_key,
            verified.sign_count,
            verified.credential_device_type.value,
            verified.credential_backed_up,
            before["purpose"],
        )

    def register(
        self,
        token: str | None,
        nonce: str | None,
        proof: RegistrationProof,
        authentication: Authentication | None,
    ) -> Account:
        row = self.context(token, nonce or "", lock=True)
        if (row["purpose"] == "add") != (authentication is not None):
            raise Rejected(401, "invalid_ceremony")
        if row["purpose"] not in ("install", "setup", "add"):
            raise Rejected(401, "invalid_ceremony")
        if row["purpose"] == "add":
            if (
                authentication is None
                or authentication.session_id != row["session_id"]
                or authentication.caller.account_id != row["account_id"]
            ):
                raise Rejected(401, "unauthorized")
        elif self.s.execute(
            text("SELECT 1 FROM iam_passkeys WHERE account_id=:a"), {"a": row["account_id"]}
        ).first():
            raise Rejected(409, "conflict")
        if (
            row["id"] != proof.context_id
            or bytes(row["challenge"]) != proof.challenge
            or row["purpose"] != proof.purpose
        ):
            raise Rejected(401, "invalid_ceremony")
        self.s.execute(
            text(
                "INSERT INTO iam_passkeys "
                "(credential_id,account_id,public_key,sign_count,device_type,backed_up) "
                "VALUES(:id,:a,:key,:count,:device,:backup)"
            ),
            {
                "id": proof.credential_id,
                "a": row["account_id"],
                "key": proof.public_key,
                "count": proof.sign_count,
                "device": proof.device_type,
                "backup": proof.backed_up,
            },
        )
        if row["purpose"] == "setup":
            self.s.execute(
                text(
                    "UPDATE iam_accounts SET password_hash=:h,state='ACTIVE',"
                    "row_version=row_version+1,security_version=security_version+1 WHERE id=:a"
                ),
                {"h": row["password_hash"], "a": row["account_id"]},
            )
            self.s.execute(
                text("UPDATE iam_credentials SET consumed=true WHERE account_id=:a"),
                {"a": row["account_id"]},
            )
        self.consume(row)
        return self.iam._account(row["account_id"])

    def authenticate(
        self, token: str | None, nonce: str | None, payload: str, sid: UUID
    ) -> tuple[str, Account]:
        before = self.context(token, nonce or "")
        if before["purpose"] != "login" or before["challenge"] is None:
            raise Rejected(401, "invalid_ceremony")
        try:
            parsed = parse_authentication_credential_json(payload)
            client = parse_client_data_json(parsed.response.client_data_json)
            if client.cross_origin:
                raise ValueError()
            if (
                parsed.response.user_handle is not None
                and parsed.response.user_handle != before["account_id"].bytes
            ):
                raise ValueError()
            credential = (
                self.s.execute(
                    text("SELECT * FROM iam_passkeys WHERE credential_id=:id AND account_id=:a"),
                    {"id": parsed.raw_id, "a": before["account_id"]},
                )
                .mappings()
                .first()
            )
            if credential is None:
                raise ValueError()
            verified = verify_authentication_response(
                credential=parsed,
                expected_challenge=bytes(before["challenge"]),
                expected_rp_id=self.rp,
                expected_origin=self.origin,
                credential_public_key=bytes(credential["public_key"]),
                credential_current_sign_count=credential["sign_count"],
                require_user_verification=True,
            )
            if verified.credential_device_type.value != credential["device_type"]:
                raise ValueError()
        except Exception:
            raise Rejected(401, "invalid_passkey") from None
        row = self.context(token, nonce or "", lock=True)
        account = self.account(row["account_id"])
        self.bind_reservation(
            account,
            Reservation(
                bytes(row["budget_key"]),
                row["attempt_id"],
                row["account_id"],
                row["security_version"],
            ),
        )
        current = (
            self.s.execute(
                text("SELECT * FROM iam_passkeys WHERE credential_id=:id FOR UPDATE"),
                {"id": parsed.raw_id},
            )
            .mappings()
            .one()
        )
        attempt = (
            self.s.execute(
                text("SELECT * FROM iam_attempts WHERE id=:id"), {"id": row["attempt_id"]}
            )
            .mappings()
            .first()
        )
        if (
            account["state"] != "ACTIVE"
            or bytes(row["challenge"]) != bytes(before["challenge"])
            or current["sign_count"] != credential["sign_count"]
            or current["account_id"] != row["account_id"]
            or attempt is None
            or not hmac.compare_digest(bytes(attempt["key"]), bytes(row["budget_key"]))
            or attempt["outcome"] != "pending"
            or attempt["stage"] != "verifying"
            or attempt["lease_until"] <= self.iam.now()
            or not hmac.compare_digest(
                bytes(row["marker"]),
                hmac.digest(self.iam.key, account["password_hash"].encode(), "sha256"),
            )
        ):
            raise Rejected(401, "invalid_credentials")
        self.s.execute(
            text("UPDATE iam_passkeys SET sign_count=:c,backed_up=:b WHERE credential_id=:id"),
            {"c": verified.new_sign_count, "b": verified.credential_backed_up, "id": parsed.raw_id},
        )
        raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        expiry = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:id AND kind='session_slot'"),
            {"id": sid},
        ).scalar_one()
        now = self.iam.now()
        if expiry <= now:
            raise Rejected(503, "unavailable")
        self.s.execute(
            text(
                "INSERT INTO iam_sessions(id,account_id,digest,csrf,security_version,"
                "created_at,last_activity,expires_at,assurance) "
                "VALUES(:id,:a,:d,:c,:v,:n,:n,:e,'password_uv')"
            ),
            {
                "id": sid,
                "a": row["account_id"],
                "d": digest(raw),
                "c": csrf,
                "v": row["security_version"],
                "n": now,
                "e": expiry,
            },
        )
        self.consume(row)
        return raw, self.iam._account(row["account_id"])

    def revoke_undelivered(self, sid: UUID) -> None:
        # No account-wide revocation: only the server-generated unreturned session id.
        self.s.execute(text("UPDATE iam_sessions SET revoked=true WHERE id=:id"), {"id": sid})
