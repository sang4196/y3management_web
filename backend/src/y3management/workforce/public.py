"""Immutable Workforce contracts; no phone or money in identity facts."""

from dataclasses import dataclass
from datetime import date
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
    def normalize(self, command: RegisterTrainer) -> RegisterTrainer: ...
    def hint(self, caller: Caller, operation: UUID) -> TrainerIdentityFact | None: ...
    def identity(self, organization_id: UUID, ident: UUID) -> TrainerIdentityFact: ...
    def get(self, caller: Caller, ident: UUID) -> ManagedTrainer: ...
    def list(self, caller: Caller, offset: int, limit: int) -> TrainerPage: ...
    def register(
        self, caller: Caller, branch: ScopedBranchFact, command: RegisterTrainer
    ) -> RegistrationResult: ...
    def confirm(self, caller: Caller, result: RegistrationResult) -> None: ...
