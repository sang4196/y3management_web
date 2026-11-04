"""Immutable IAM values. No database/HTTP objects or password hashes cross here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID


@dataclass(frozen=True)
class PolicyStamp:
    version: int
    transition_id: UUID


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
    assurance: str = "password"
    binding: TrainerBinding | None = None
    trainer_granted: bool = False
    policy: PolicyStamp = field(kw_only=True)


@dataclass(frozen=True, repr=False)
class PasswordChangeActor:
    """Original actor deadlines and exact expected C3 effects, prepared before mutation."""

    authentication: Authentication
    expected_digest: bytes
    last_activity: datetime
    expires_at: datetime
    policy: PolicyStamp


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
    trainer_role_epoch: int = 0
    policy: PolicyStamp = field(kw_only=True)


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
    policy: PolicyStamp = field(kw_only=True)


# Module ports expose immutable facts and commands, not persistence adapters.


class IAMPort(Protocol):
    def policy(self) -> PolicyStamp: ...
    def check_policy(self, expected: PolicyStamp) -> None: ...

    def revoke_trainer_only_sessions(self, binding: TrainerBinding) -> int: ...

    def account_roles(self, ident: UUID) -> AccountRoles: ...
    def lock_login(self, ident: UUID) -> AccountRoles: ...
    def trainer_binding(self, org: UUID, trainer: UUID) -> TrainerBinding | None: ...
    def trainer_state(self, org: UUID, trainer: UUID) -> TrainerAccountState: ...
    def trainer_operation(self, org: UUID, operation: UUID) -> TrainerOperation | None: ...
    def trainer_issue(
        self,
        caller: Caller,
        trainer: UUID,
        home: UUID,
        operation: UUID,
        identifier: str | None,
        expected: int | None,
        slot: UUID,
    ) -> tuple[TrainerOperation, Setup | None, IdentityTransition | None]: ...
    def lock_trainer_credentials(self, ident: UUID) -> None: ...
    def prepare_trainer_setup(self, token: str, password: str) -> TrainerSetupProof: ...
    def lock_trainer_setup(
        self, proof: TrainerSetupProof, preauth: str | None, nonce: str | None
    ) -> TrainerBinding: ...
    def complete_trainer_setup(
        self, proof: TrainerSetupProof, preauth: str | None, nonce: str | None
    ) -> IdentityTransition: ...
    def confirm_trainer_setup(self, proof: TrainerSetupProof) -> None: ...
    def confirm_trainer_delivery(self, operation: TrainerOperation, slot: UUID) -> None: ...
    def identity_transition(self, ident: UUID) -> IdentityTransition: ...
    def confirm_identity_transition(
        self,
        before: IdentityTransition,
        *,
        changed: bool,
        authentication: Authentication | None = None,
        logout: bool = False,
    ) -> None: ...
    def confirm_login(self, proof: LoginProof, reservation: Reservation, sid: UUID) -> None: ...
    def revoke_undelivered_session(
        self, sid: UUID, *, attempt_id: UUID, account_id: UUID, policy: PolicyStamp
    ) -> None: ...
    def installation_lock(self) -> None: ...
    def confirm_preparation(self, token: str | None, nonce: str | None) -> None: ...
    def confirm_setup(self, token: str) -> None: ...
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
        audience: Literal["admin", "account"] = "admin",
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
    def password_change_actor(
        self, authentication: Authentication, proof: LoginProof
    ) -> PasswordChangeActor: ...
    def change_password(self, proof: LoginProof) -> tuple[Account, Account]: ...
    def confirm_password_change(self, snapshot: PasswordChangeActor) -> None: ...
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
    trainer_role_epoch: int = 0
    policy: PolicyStamp = field(kw_only=True)


class PasswordResetPort(Protocol):
    def confirm_complete(self, proof: ResetProof) -> None: ...
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
    reset_generation: int
    password_reset_pending: bool
    password_ready: bool


@dataclass(frozen=True)
class EmergencyRequest:
    operation_id: UUID
    organization_id: UUID
    account_id: UUID
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
    def confirm_complete(self, proof: EmergencyPasswordProof) -> None: ...
    def preflight(self, authority: OperatingRecoveryAuthority, ident: UUID) -> None: ...

    def inspect(self, authority: OperatingRecoveryAuthority, ident: UUID) -> EmergencySnapshot: ...
    def status(self, authority: OperatingRecoveryAuthority, operation: UUID) -> EmergencyView: ...
    def issue(
        self, authority: OperatingRecoveryAuthority, request: EmergencyRequest, slot: UUID
    ) -> tuple[Setup, EmergencyChange]: ...
    def recipient(self, token: str) -> EmergencyView: ...
    def prepare_password(self, token: str, password: str) -> EmergencyPasswordProof: ...
    def complete_password(self, proof: EmergencyPasswordProof) -> EmergencyChange: ...


@dataclass(frozen=True)
class EmergencyChange:
    case_id: UUID
    organization_id: UUID
    target_id: UUID
    actor_id: UUID | None
    action: str
    actor_role: str
    approval_mode: str
    before_version: int
    after_version: int
    before_security_version: int
    after_security_version: int
    before_reset_generation: int
    after_reset_generation: int
    policy_version: int
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class EmergencyPasswordProof:
    source_id: UUID
    case_id: UUID
    organization_id: UUID
    account_id: UUID
    row_version: int
    security_version: int
    reset_generation: int
    trainer_role_epoch: int
    expires_at: datetime
    policy: PolicyStamp
    password_hash: str = field(repr=False)


@dataclass(frozen=True)
class HandoffRequest:
    operation_id: UUID
    supersedes_case_id: UUID
    expected: EmergencySnapshot


@dataclass(frozen=True)
class HandoffState:
    operation_id: UUID
    factors: str
    expires_at: datetime
    status: str
    issuer_kind: str
    approval_origin_case_id: UUID | None
    supersedes_case_id: UUID | None
    snapshot: EmergencySnapshot


class HandoffPort(Protocol):
    def confirm(self, ident: UUID, operation: UUID, slot: UUID) -> None: ...

    def state(self, caller: Caller, ident: UUID, operation: UUID | None) -> HandoffState: ...
    def validate(self, caller: Caller, ident: UUID, operation: UUID) -> object: ...
    def issue(
        self, caller: Caller, ident: UUID, request: HandoffRequest, slot: UUID
    ) -> tuple[Setup, EmergencyChange]: ...


@dataclass(frozen=True)
class TrainerBinding:
    account_id: UUID
    organization_id: UUID
    trainer_id: UUID
    version: int


@dataclass(frozen=True)
class AccountRoles:
    account: Account
    binding: TrainerBinding | None
    trainer_granted: bool = False
    trainer_role_epoch: int = 0

    @property
    def admin(self) -> bool:
        return self.account.master or self.account.branch_id is not None


@dataclass(frozen=True)
class TrainerAccountState:
    trainer_id: UUID
    account_id: UUID | None
    login_id: str | None
    state: str | None
    account_version: int | None
    initial_setup_expires_at: datetime | None


@dataclass(frozen=True)
class TrainerOperation:
    operation_id: UUID
    kind: str
    trainer_id: UUID
    account_id: UUID
    committed_account_version: int
    current_state: TrainerAccountState


@dataclass(frozen=True, repr=False)
class TrainerSetupProof:
    source_id: UUID
    account_id: UUID
    organization_id: UUID
    trainer_id: UUID
    account_version: int
    security_version: int
    binding_version: int
    expires_at: datetime
    trainer_role_epoch: int = 0
    policy: PolicyStamp = field(kw_only=True)


@dataclass(frozen=True)
class IdentityTransition:
    account: Account
    security_version: int
    binding: TrainerBinding


@dataclass(frozen=True)
class TrainerRoleRequest:
    operation_id: UUID
    account_id: UUID
    desired_granted: bool
    expected_account_version: int
    expected_role_version: int
    expected_trainer_version: int
    identity_confirmed: bool


@dataclass(frozen=True)
class TrainerRoleState:
    trainer_id: UUID
    account_id: UUID | None
    login_id: str | None
    state: str | None
    account_version: int | None
    granted: bool
    role_version: int


@dataclass(frozen=True)
class TrainerRoleCandidate:
    account_id: UUID
    login_id: str
    state: str
    account_version: int
    role_version: int
    eligible: bool


@dataclass(frozen=True)
class TrainerRoleResult:
    operation_id: UUID
    changed: bool
    committed_granted: bool
    committed_role_version: int
    current_state: TrainerRoleState
    reauthentication_required: bool = False


@dataclass(frozen=True, repr=False)
class RoleActorSnapshot:
    authentication: Authentication
    stable_digest: bytes
    role_epoch: int
    last_activity: datetime
    expires_at: datetime
    policy: PolicyStamp = field(kw_only=True)


@dataclass(frozen=True)
class TrainerRoleChange:
    kind: str
    before_granted: bool
    after_granted: bool
    before_role_version: int
    after_role_version: int
    account_version: int
    security_version: int


class TrainerRolesPort(Protocol):
    def lock(self, ident: UUID) -> None: ...
    def state(self, organization: UUID, trainer: UUID) -> TrainerRoleState: ...
    def lookup(
        self, organization: UUID, trainer: UUID, identifier: str
    ) -> TrainerRoleCandidate: ...
    def operation(self, organization: UUID, operation: UUID) -> TrainerRoleResult | None: ...
    def snapshot(self, authentication: Authentication) -> RoleActorSnapshot: ...
    def confirm_actor(
        self, snapshot: RoleActorSnapshot, *, self_change: bool, touch: bool = False
    ) -> None: ...
    def change(
        self,
        caller: Caller,
        trainer: UUID,
        home: UUID,
        active: bool,
        trainer_version: int,
        request: TrainerRoleRequest,
    ) -> tuple[TrainerRoleResult, TrainerRoleChange | None]: ...
    def confirm_change(self, result: TrainerRoleResult, change: TrainerRoleChange) -> None: ...
