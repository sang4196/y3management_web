"""Allowlisted audit command, with no arbitrary payload or secret fields."""

from __future__ import annotations

from dataclasses import dataclass
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


class AuditPort(Protocol):
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
