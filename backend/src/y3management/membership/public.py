"""Immutable Member contracts; private personal values never appear in repr."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from y3management.iam.public import Caller


@dataclass(frozen=True, repr=False)
class MemberValues:
    name: str
    phone: str


@dataclass(frozen=True, repr=False)
class Member:
    id: UUID
    version: int
    values: MemberValues
    home_branch_id: UUID
    active: bool
    recorded_at: datetime
    home_branch_name: str = ""
    home_active: bool = True


@dataclass(frozen=True, repr=False)
class MemberPage:
    items: tuple[Member, ...]
    total: int


@dataclass(frozen=True, repr=False)
class MemberCommand:
    operation_id: UUID
    kind: Literal["create", "update", "deactivate", "reactivate"]
    member_id: UUID | None = None
    expected_member_version: int | None = None
    home_branch_id: UUID | None = None
    values: MemberValues | None = None


@dataclass(frozen=True, repr=False)
class MemberMutation:
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


@dataclass(frozen=True, repr=False)
class MemberResult:
    operation_id: UUID
    kind: str
    changed: bool
    committed_member: Member
    current_member: Member


class MembershipPort(Protocol):
    def get(self, caller: Caller, ident: UUID) -> Member: ...
    def list(self, caller: Caller, offset: int, limit: int) -> MemberPage: ...
    def operation(self, caller: Caller, ident: UUID) -> MemberResult: ...
    def change(
        self, caller: Caller, command: MemberCommand
    ) -> tuple[MemberResult, MemberMutation | None]: ...
    def confirm(self, caller: Caller, result: MemberResult) -> None: ...
    def seal(self, caller: Caller, result: MemberResult, clock: datetime) -> MemberResult: ...
