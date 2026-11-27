"""Immutable Workforce contracts; no phone or money in identity facts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Protocol
from uuid import UUID

from y3management.iam.public import Caller
from y3management.organization.public import ScopedBranchFact


@dataclass(frozen=True, repr=False)
class RegisterTrainer:
    operation_id: UUID
    name: str
    phone: str
    home_branch_id: UUID
    rate_percent: int
    fixed_amount_won: str
    base_salary_won: str
    base_salary_start_month: str


@dataclass(frozen=True)
class TrainerIdentityFact:
    trainer_id: UUID
    organization_id: UUID
    home_branch_id: UUID
    active: bool
    version: int


@dataclass(frozen=True)
class ManagedTrainer:
    id: UUID
    name: str
    home_branch_id: UUID
    active: bool
    version: int


@dataclass(frozen=True)
class TrainerPage:
    items: tuple[ManagedTrainer, ...]
    total: int


@dataclass(frozen=True, repr=False)
class InitialValues:
    rate: int
    fixed: str
    base: str
    month: date


@dataclass(frozen=True)
class RegistrationResult:
    operation_id: UUID
    trainer: ManagedTrainer
    created: bool


class WorkforcePort(Protocol):
    def issue_trainers(self, caller: Caller, offset: int, limit: int) -> IssueTrainerPage: ...
    def issue_trainer(self, caller: Caller, ident: UUID) -> TrainerIdentityFact: ...

    def base_head(self, caller: Caller, trainer: UUID) -> BaseSnapshot: ...
    def base_history_token(
        self,
        snapshot: BaseSnapshot,
        offset: int,
        limit: int,
        expected_ledger: int | None,
        expected_month: str | None,
        clock: datetime,
    ) -> str: ...

    def base_snapshot(self, caller: Caller, trainer: UUID, query: BaseQuery) -> BaseSnapshot: ...
    def base_page(self, snapshot: BaseSnapshot, query: BaseQuery, clock: datetime) -> BasePage: ...
    def base_replay(
        self, caller: Caller, trainer: UUID, request: BaseCommand
    ) -> BaseResult | None: ...
    def base_operation_target(self, organization: UUID, operation: UUID) -> UUID | None: ...

    def base_operation(self, caller: Caller, operation: UUID) -> BaseResult | None: ...
    def prepare_base(
        self, caller: Caller, fact: TrainerIdentityFact, request: BaseCommand
    ) -> PreparedBase: ...
    def confirm_base(self, prepared: PreparedBase, caller: Caller) -> None: ...
    def seal_base(self, prepared: PreparedBase, clock: datetime) -> BaseResult: ...

    def compensation(self, caller: Caller, trainer: UUID) -> CompensationState: ...
    def compensation_operation(
        self, caller: Caller, operation: UUID
    ) -> CompensationResult | None: ...
    def change_compensation(
        self, caller: Caller, fact: TrainerIdentityFact, request: CompensationRequest
    ) -> tuple[CompensationResult, CompensationChange | None]: ...
    def confirm_compensation(self, caller: Caller, result: CompensationResult) -> None: ...

    def home_operation(self, caller: Caller, operation_id: UUID) -> TrainerHomeResult | None: ...
    def change_home(
        self,
        caller: Caller,
        branch: ScopedBranchFact,
        trainer: TrainerIdentityFact,
        request: TrainerHomeRequest,
    ) -> tuple[TrainerHomeResult, TrainerHomeChange | None]: ...
    def confirm_home(self, caller: Caller, result: TrainerHomeResult) -> None: ...

    def state_operation(self, caller: Caller, operation_id: UUID) -> TrainerStateResult | None: ...
    def change_state(
        self,
        caller: Caller,
        branch: ScopedBranchFact,
        trainer: TrainerIdentityFact,
        request: TrainerStateRequest,
    ) -> tuple[TrainerStateResult, TrainerStateChange | None]: ...
    def confirm_state(self, caller: Caller, result: TrainerStateResult) -> None: ...

    def lock_identity(
        self, organization_id: UUID, ident: UUID, *, exclusive: bool = False
    ) -> TrainerIdentityFact: ...

    def normalize(self, command: RegisterTrainer) -> RegisterTrainer: ...
    def hint(self, caller: Caller, operation: UUID) -> TrainerIdentityFact | None: ...
    def identity(self, organization_id: UUID, ident: UUID) -> TrainerIdentityFact: ...
    def get(self, caller: Caller, ident: UUID) -> ManagedTrainer: ...
    def list(self, caller: Caller, offset: int, limit: int) -> TrainerPage: ...
    def register(
        self, caller: Caller, branch: ScopedBranchFact, command: RegisterTrainer
    ) -> RegistrationResult: ...
    def confirm(self, caller: Caller, result: RegistrationResult) -> None: ...


@dataclass(frozen=True)
class TrainerStateRequest:
    operation_id: UUID
    desired_active: bool
    expected_trainer_version: int


@dataclass(frozen=True)
class TrainerStateResult:
    operation_id: UUID
    trainer_id: UUID
    changed: bool
    committed_active: bool
    committed_trainer_version: int
    current_state: TrainerIdentityFact


@dataclass(frozen=True)
class TrainerStateChange:
    organization_id: UUID
    operation_id: UUID
    trainer_id: UUID
    before_active: bool
    after_active: bool
    before_version: int
    after_version: int
    recorded_at: datetime


@dataclass(frozen=True)
class TrainerHomeRequest:
    operation_id: UUID
    destination_home_branch_id: UUID
    expected_trainer_version: int


@dataclass(frozen=True)
class TrainerHomeResult:
    operation_id: UUID
    trainer_id: UUID
    changed: bool
    before_home_branch_id: UUID
    committed_home_branch_id: UUID
    before_trainer_version: int
    committed_trainer_version: int
    recorded_at: datetime
    current_state: TrainerIdentityFact


@dataclass(frozen=True)
class TrainerHomeChange:
    organization_id: UUID
    operation_id: UUID
    trainer_id: UUID
    actor_id: UUID
    before_home_branch_id: UUID
    after_home_branch_id: UUID
    before_version: int
    after_version: int
    recorded_at: datetime


@dataclass(frozen=True, repr=False)
class CompensationRequest:
    operation_id: UUID
    rate_percent: int
    fixed_amount_won: str
    expected_compensation_version: int
    expected_trainer_version: int


@dataclass(frozen=True, repr=False)
class CompensationState:
    trainer_id: UUID
    home_branch_id: UUID
    trainer_version: int
    rate_percent: int
    fixed_amount_won: str
    compensation_version: int
    initial_base_salary_won: str
    initial_base_salary_start_month: str


@dataclass(frozen=True, repr=False)
class CompensationResult:
    operation_id: UUID
    trainer_id: UUID
    changed: bool
    before_rate_percent: int
    before_fixed_amount_won: str
    before_compensation_version: int
    committed_rate_percent: int
    committed_fixed_amount_won: str
    committed_compensation_version: int
    recorded_at: datetime
    current_state: CompensationState


@dataclass(frozen=True, repr=False)
class CompensationChange:
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
class BaseCommand:
    operation_id: UUID
    kind: Literal["create", "edit", "cancel"]
    expected_base_ledger_version: int
    expected_trainer_version: int
    change_id: UUID | None = None
    start_month: str | None = None
    planned_amount_won: str | None = None
    expected_change_revision: int | None = None


@dataclass(frozen=True)
class BaseQuery:
    basis_month: str
    offset: int = 0
    limit: int = 25
    expected_base_ledger_version: int | None = None
    expected_server_business_month: str | None = None
    expected_basis_month: str | None = None


@dataclass(frozen=True, repr=False)
class BaseFact:
    change_id: UUID
    start_month: str
    planned_amount_won: str
    revision: int
    active: bool
    is_initial: bool = False
    cancellable: bool | None = None


@dataclass(frozen=True, repr=False)
class BaseSnapshot:
    trainer_id: UUID
    home_branch_id: UUID
    trainer_version: int
    base_ledger_version: int
    anchor: BaseFact
    projection: BaseFact | None
    items: tuple[BaseFact, ...]
    total: int


@dataclass(frozen=True, repr=False)
class BasePage:
    trainer_id: UUID
    home_branch_id: UUID
    trainer_version: int
    base_ledger_version: int
    basis_month: str
    server_business_month: str
    as_of: datetime
    anchor: BaseFact
    general_setting: BaseFact | None
    items: tuple[BaseFact, ...]
    total: int


@dataclass(frozen=True, repr=False)
class BaseMutation:
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
class PreparedBase:
    mutation: BaseMutation
    fingerprint: bytes
    expected_trainer_version: int


@dataclass(frozen=True, repr=False)
class BaseResult:
    operation_id: UUID
    trainer_id: UUID
    kind: str
    changed: bool
    committed_change: BaseFact
    committed_base_ledger_version: int
    recorded_at: datetime
    validated_at: datetime
    validated_business_month: str
    current_base_ledger_version: int
    current_change: BaseFact


@dataclass(frozen=True)
class IssueTrainer:
    id: UUID
    name: str
    home_branch_id: UUID
    version: int
    home_branch_name: str = ""


@dataclass(frozen=True)
class IssueTrainerPage:
    items: tuple[IssueTrainer, ...]
    total: int
