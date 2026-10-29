"""Immutable Workforce contracts; no phone or money in identity facts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
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
