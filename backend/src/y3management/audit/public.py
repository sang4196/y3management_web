"""Allowlisted audit command, with no arbitrary payload or secret fields."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class Event:
    action: str
    organization_id: UUID | None
    actor_id: UUID | None
    target_id: UUID | None
    success: bool = True
    before_state: str | None = None
    after_state: str | None = None
    before_branch: UUID | None = None
    after_branch: UUID | None = None
    actor_role: str | None = None
    actor_scope: str | None = None
    actor_branch: UUID | None = None
    before_version: int | None = None
    after_version: int | None = None
    branch_code: str | None = None
    branch_name: str | None = None
    before_login_id: str | None = None
    after_login_id: str | None = None
    key_id: UUID | None = None
    before_key_set_version: int | None = None
    after_key_set_version: int | None = None
    before_recovery_generation: int | None = None
    after_recovery_generation: int | None = None

    before_reset_generation: int | None = None
    after_reset_generation: int | None = None
    before_password_ready: bool | None = None
    after_password_ready: bool | None = None

    emergency_case_id: UUID | None = None
    emergency_factors: str | None = None
    executor_ref: str | None = None
    approval_mode: str | None = None
    approval_origin_case_id: UUID | None = None
    previous_case_id: UUID | None = None
    handoff_kind: str | None = None


@dataclass(frozen=True)
class PasswordEmergencyEvent:
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


@dataclass(frozen=True)
class OperatorAccountEvent:
    kind: str
    organization_id: UUID
    account_id: UUID
    branch_id: UUID
    actor_id: UUID | None
    actor_role: str
    actor_branch: UUID | None
    before_state: str | None
    after_state: str
    before_version: int | None
    after_version: int


class AuditPort(Protocol):
    def append_pass_state(self, event: PassStateChanged) -> None: ...
    def seal_pass_state(self, org: UUID, operation: UUID, clock: datetime) -> None: ...

    def append_pass_issue(self, event: PassIssued) -> None: ...
    def seal_pass_issue(self, org: UUID, operation: UUID, clock: datetime) -> None: ...

    def append_member(self, event: MemberEvent) -> None: ...

    def append_product(self, event: ProductEvent) -> None: ...

    def append_base_schedule(self, event: BaseScheduleEvent) -> None: ...
    def base_schedule_history(
        self, organization: UUID, trainer: UUID, offset: int, limit: int
    ) -> BaseHistoryPage: ...

    def append_compensation(self, event: CompensationEvent) -> None: ...
    def compensation_history(
        self, organization: UUID, trainer: UUID, offset: int, limit: int
    ) -> CompensationHistoryPage: ...

    def append_trainer_home(self, event: TrainerHomeEvent) -> None: ...

    def append_operator_role(self, event: OperatorRoleEvent) -> None: ...

    def append_operator(self, event: OperatorAccountEvent) -> None: ...

    def append_password_emergency(self, event: PasswordEmergencyEvent) -> None: ...

    def append_trainer_state(self, event: TrainerStateEvent) -> None: ...

    def append_trainer_role(self, event: TrainerRoleEvent) -> None: ...

    def append_trainer_identity(self, event: TrainerIdentityEvent) -> None: ...

    def append_trainer_registered(self, event: TrainerRegistered) -> None: ...
    def append_initial_compensation(self, event: InitialCompensationSet) -> None: ...

    def append(self, event: Event) -> None: ...


@dataclass(frozen=True)
class TrainerRegistered:
    organization_id: UUID
    operation_id: UUID
    trainer_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID


@dataclass(frozen=True, repr=False)
class InitialCompensationSet:
    registration: TrainerRegistered
    rate: int
    fixed: str
    base: str
    month: str


@dataclass(frozen=True)
class TrainerIdentityEvent:
    organization_id: UUID
    account_id: UUID
    trainer_id: UUID
    kind: str
    actor_id: UUID | None
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID
    operation_id: UUID | None
    before_state: str | None
    after_state: str
    before_version: int | None
    after_version: int
    before_security_version: int | None
    after_security_version: int


@dataclass(frozen=True)
class TrainerRoleEvent:
    organization_id: UUID
    operation_id: UUID
    account_id: UUID
    trainer_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID
    kind: str
    before_granted: bool
    after_granted: bool
    before_role_version: int
    after_role_version: int
    before_epoch: int
    after_epoch: int
    before_account_version: int
    after_account_version: int
    before_security_version: int
    after_security_version: int


@dataclass(frozen=True)
class TrainerStateEvent:
    organization_id: UUID
    operation_id: UUID
    trainer_id: UUID
    account_id: UUID | None
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID
    before_active: bool
    after_active: bool
    before_version: int
    after_version: int
    recorded_at: datetime


@dataclass(frozen=True)
class OperatorRoleEvent:
    organization_id: UUID
    operation_id: UUID
    account_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    kind: str
    before_granted: bool
    after_granted: bool
    before_branch: UUID | None
    after_branch: UUID
    before_version: int
    after_version: int
    account_state: str
    account_version: int


@dataclass(frozen=True)
class TrainerHomeEvent:
    organization_id: UUID
    operation_id: UUID
    trainer_id: UUID
    actor_id: UUID
    before_home_branch_id: UUID
    after_home_branch_id: UUID
    before_version: int
    after_version: int
    recorded_at: datetime
    actor_role: str = "MASTER"
    actor_branch: UUID | None = None


@dataclass(frozen=True, repr=False)
class CompensationEvent:
    organization_id: UUID
    operation_id: UUID
    trainer_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID
    before_rate: int
    after_rate: int
    before_fixed: str
    after_fixed: str
    before_version: int
    after_version: int
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class CompensationHistoryItem:
    compensation_version: int
    operation_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID
    before_rate: int | None
    after_rate: int
    before_fixed: str | None
    after_fixed: str
    initial_base_salary_won: str | None
    initial_base_salary_start_month: str | None
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class CompensationHistoryPage:
    items: tuple[CompensationHistoryItem, ...]
    total: int


@dataclass(frozen=True, repr=False)
class BaseScheduleEvent:
    organization_id: UUID
    operation_id: UUID
    trainer_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID
    kind: str
    change_id: UUID
    start_month: date
    before_amount: str | None
    after_amount: str
    before_active: bool | None
    after_active: bool
    before_revision: int | None
    after_revision: int
    before_ledger_version: int
    after_ledger_version: int
    changed: bool
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class BaseHistoryItem:
    ledger_version: int
    kind: str
    change_id: UUID
    start_month: str
    before_amount_won: str | None
    planned_amount_won: str
    active: bool
    revision: int
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    target_home: UUID
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class BaseHistoryPage:
    items: tuple[BaseHistoryItem, ...]
    total: int


@dataclass(frozen=True, repr=False)
class ProductEvent:
    organization_id: UUID
    operation_id: UUID
    product_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    kind: str
    before_version: int | None
    after_version: int
    changed: bool
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class MemberEvent:
    organization_id: UUID
    operation_id: UUID
    member_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    home_branch_id: UUID
    kind: str
    before_version: int | None
    after_version: int
    changed: bool
    recorded_at: datetime


@dataclass(frozen=True)
class PassIssued:
    organization_id: UUID
    operation_id: UUID
    pass_id: UUID
    member_id: UUID
    trainer_id: UUID
    issued_branch_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class PassStateChanged:
    organization_id: UUID
    operation_id: UUID
    pass_id: UUID
    issued_branch_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    kind: str
    reason: str
    before_version: int
    after_version: int
    before_expired: bool
    after_expired: bool
    before_recorded_at: datetime
    recorded_at: datetime
