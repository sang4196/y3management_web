"""Immutable IAM values. No database/HTTP objects or password hashes cross here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID


@dataclass(frozen=True)
class Caller:
    account_id: UUID
    organization_id: UUID
    branch_id: UUID | None
    master: bool


@dataclass(frozen=True, repr=False)
class Authentication:
    caller: Caller
    session_id: UUID
    csrf: str


@dataclass(frozen=True)
class Account:
    id: UUID
    organization_id: UUID
    login_id: str
    state: str
    branch_id: UUID | None
    master: bool
    version: int


@dataclass(frozen=True, repr=False)
class LoginProof:
    account_id: UUID
    security_version: int
    credential_marker: bytes


@dataclass(frozen=True, repr=False)
class Setup:
    token: str
    expires_at: datetime


@dataclass(frozen=True, repr=False)
class Preparation:
    token: str
    csrf: str


@dataclass(frozen=True, repr=False)
class Reservation:
    key: bytes
    id: UUID
    account_id: UUID | None
    security_version: int | None


# Module ports expose immutable facts and commands, not persistence adapters.


class IAMPort(Protocol):
    def prepare_master(self, identifier: str, password: str) -> None: ...
    def ensure_uninstalled(self) -> None: ...
    def bootstrap(self, organization_id: UUID, identifier: str) -> Account: ...
    def preparation(self, token: str | None, nonce: str | None, consume: bool = False) -> None: ...
    def login_subject(self, identifier: str) -> Account | None: ...
    def verify_login(
        self, identifier: str, password: str, reservation: Reservation
    ) -> LoginProof | None: ...
    def login(
        self,
        proof: LoginProof,
        sid: UUID,
        preauth: str | None,
        nonce: str | None,
        reservation: Reservation,
    ) -> tuple[str, Account]: ...
    def authenticate(
        self,
        token: str | None,
        *,
        management: bool = False,
        target: UUID | None = None,
        touch: bool = True,
    ) -> Authentication: ...
    def csrf(self, authentication: Authentication, nonce: str | None) -> None: ...
    def require_master(self, caller: Caller) -> None: ...
    def scoped_account(self, caller: Caller, ident: UUID) -> Account: ...
    def lookup(self, caller: Caller, identifier: str) -> Account: ...
    def issue(self, caller: Caller, identifier: str, branch: UUID) -> Account: ...
    def master_management(self, caller: Caller, ident: UUID) -> Account: ...
    def revoke_management_sources(self, ident: UUID) -> None: ...
    def master_onboarding(self, caller: Caller, ident: UUID) -> Account: ...
    def lookup_master(self, caller: Caller, identifier: str) -> Account: ...
    def issue_master(self, caller: Caller, identifier: str) -> Account: ...
    def setup(
        self, account: Account, state_id: UUID, *, reissue: bool
    ) -> tuple[Account, Setup]: ...
    def complete(
        self, token: str, password: str, preauth: str | None, nonce: str | None
    ) -> Account: ...
    def lock_credentials(self, ident: UUID) -> None: ...
    def change(self, account: Account, branch: UUID | None, disable: bool) -> Account: ...
    def change_login_id(self, account: Account, identifier: str) -> Account: ...
    def prepare_password_change(
        self, ident: UUID, current_password: str, new_password: str
    ) -> LoginProof: ...
    def change_password(self, proof: LoginProof) -> tuple[Account, Account]: ...
    def restore(self, account: Account) -> Account: ...
    def logout(self, authentication: Authentication) -> None: ...
    def gc_sessions(self) -> None: ...


class SecurityPort(Protocol):
    def allocate(self, kind: str, *, collect: bool = True) -> UUID: ...
    def release(self, ident: UUID, *, collect: bool = True) -> None: ...
    def preparation(self, raw: str | None) -> Preparation: ...
    def reserve(self, login_id: str) -> Reservation: ...
    def finish(self, reservation: Reservation, success: bool) -> None: ...
    def cancel(self, reservation: Reservation) -> None: ...
    def mfa_stage(self, reservation: Reservation, stage: str) -> None: ...


@dataclass(frozen=True, repr=False)
class Ceremony:
    token: str
    csrf: str
    options_json: str
    expires_at: datetime


@dataclass(frozen=True, repr=False)
class RegistrationProof:
    context_id: UUID
    challenge: bytes
    credential_id: bytes
    public_key: bytes
    sign_count: int
    device_type: str
    backed_up: bool
    purpose: str


@dataclass(frozen=True)
class KeyChange:
    key_id: UUID | None
    before_key_set_version: int
    after_key_set_version: int
    before_recovery_generation: int
    after_recovery_generation: int


@dataclass(frozen=True)
class RecoveryState:
    account_id: UUID
    account_version: int
    key_set_version: int
    recovery_pending: bool
    generation: int
    expires_at: datetime | None


@dataclass(frozen=True)
class Passkey:
    key_id: UUID
    created_at: datetime
    device_type: str
    backed_up: bool


@dataclass(frozen=True)
class KeyList:
    items: tuple[Passkey, ...]
    key_set_version: int


@dataclass(frozen=True)
class ResetState:
    account_id: UUID
    account_version: int
    password_reset_pending: bool
    generation: int
    expires_at: datetime | None


@dataclass(frozen=True)
class ResetChange:
    before_reset_generation: int
    after_reset_generation: int
    before_password_ready: bool
    after_password_ready: bool


@dataclass(frozen=True, repr=False)
class ResetProof:
    source_id: UUID
    account_id: UUID
    security_version: int
    generation: int


class MFAPort(Protocol):
    def reset_state(self, caller: Caller, ident: UUID) -> ResetState: ...
    def start_reset(
        self,
        caller: Caller,
        ident: UUID,
        version: int,
        generation: int,
        slot: UUID,
        *,
        reissue: bool,
    ) -> tuple[Account, Account, Setup, ResetChange]: ...
    def prepare_reset(self, token: str, password: str) -> ResetProof: ...
    def complete_reset(self, proof: ResetProof) -> tuple[Account, Account, ResetChange]: ...

    def recovery_state(self, caller: Caller, ident: UUID) -> RecoveryState: ...
    def start_recovery(
        self,
        caller: Caller,
        ident: UUID,
        version: int,
        key_version: int,
        slot: UUID,
        *,
        reissue: bool,
    ) -> tuple[Account, Account, Setup, KeyChange]: ...
    def begin_recovery(self, token: str, slot: UUID) -> Ceremony: ...
    def keys(self, ident: UUID) -> KeyList: ...
    def delete_key(
        self, ident: UUID, key_id: UUID, version: int
    ) -> tuple[Account, Account, KeyChange]: ...
    def failure_subject(self, reservation: Reservation) -> Account | None: ...
    def installation(self, account: Account, state_id: UUID) -> Setup: ...
    def begin_install(self, token: str) -> Ceremony: ...
    def begin_setup(self, token: str, password: str, state_id: UUID) -> Ceremony: ...
    def begin_add(self, authentication: Authentication, state_id: UUID) -> Ceremony: ...
    def begin_login(
        self, proof: LoginProof, reservation: Reservation, state_id: UUID
    ) -> Ceremony: ...
    def reservation(self, token: str | None, nonce: str | None) -> Reservation: ...
    def verify_registration(
        self, token: str | None, nonce: str | None, payload: str
    ) -> RegistrationProof: ...
    def register(
        self,
        token: str | None,
        nonce: str | None,
        proof: RegistrationProof,
        authentication: Authentication | None,
    ) -> tuple[Account, KeyChange]: ...
    def authenticate(
        self, token: str | None, nonce: str | None, payload: str, sid: UUID
    ) -> tuple[str, Account]: ...
    def revoke_undelivered(self, sid: UUID) -> None: ...


@dataclass(frozen=True)
class OperatingRecoveryAuthority:
    organization_id: UUID
    executor_ref: str
    executor_uid: int
    operations: frozenset[str]


@dataclass(frozen=True)
class EmergencySnapshot:
    row_version: int
    security_version: int
    key_set_version: int
    reset_generation: int
    recovery_generation: int
    password_reset_pending: bool
    recovery_pending: bool
    password_ready: bool
    key_ready: bool


@dataclass(frozen=True)
class EmergencyRequest:
    operation_id: UUID
    organization_id: UUID
    account_id: UUID
    factors: Literal["password", "passkey", "both"]
    expected: EmergencySnapshot
    approval_ref: str
    owner_ref: str
    checked_at: datetime
    approval_valid_until: datetime
    supersedes: UUID | None = None


@dataclass(frozen=True)
class EmergencyView:
    operation_id: UUID
    factors: str
    expires_at: datetime
    status: str


class EmergencyPort(Protocol):
    def preflight(self, authority: OperatingRecoveryAuthority, ident: UUID) -> None: ...

    def inspect(self, authority: OperatingRecoveryAuthority, ident: UUID) -> EmergencySnapshot: ...
    def status(self, authority: OperatingRecoveryAuthority, operation: UUID) -> EmergencyView: ...
    def issue(
        self, authority: OperatingRecoveryAuthority, request: EmergencyRequest, slot: UUID
    ) -> tuple[Setup, EmergencyChange]: ...
    def recipient(self, token: str) -> EmergencyView: ...
    def begin(self, token: str, password: str | None, slot: UUID) -> Ceremony: ...
    def password(self, token: str, password: str) -> EmergencyChange: ...
    def complete(
        self, token: str | None, nonce: str | None, proof: RegistrationProof
    ) -> EmergencyChange: ...


@dataclass(frozen=True)
class EmergencyChange:
    action: str
    organization_id: UUID
    actor_id: UUID | None
    target_id: UUID
    actor_role: str
    actor_scope: str
    before_state: str
    after_state: str
    before_version: int
    after_version: int
    before_key_set_version: int
    after_key_set_version: int
    before_recovery_generation: int
    after_recovery_generation: int
    before_reset_generation: int
    after_reset_generation: int
    before_password_ready: bool
    after_password_ready: bool
    emergency_case_id: UUID
    emergency_factors: str
    executor_ref: str
    approval_mode: str
