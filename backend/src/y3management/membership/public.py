"""Immutable Member contracts; private personal values never appear in repr."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from y3management.iam.public import Caller
from y3management.organization.public import AssignmentCandidate, MemberBranchFact


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
    home_branch_name: str | None = ""
    home_active: bool | None = True


@dataclass(frozen=True, repr=False)
class MemberPage:
    items: tuple[Member, ...]
    total: int


@dataclass(frozen=True, repr=False)
class MemberCommand:
    operation_id: UUID
    kind: Literal["create", "update", "deactivate", "reactivate", "move_home"]
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


@dataclass(frozen=True, repr=False)
class MemberMoveAck:
    operation_id: UUID
    changed: bool
    member_id: UUID
    committed_member_version: int
    kind: str = "move_home"


@dataclass(frozen=True, repr=False)
class MemberMoveProof:
    after: Member
    source: MemberBranchFact
    target: MemberBranchFact


class MembershipPort(Protocol):
    def home_candidates(
        self, caller: Caller, ident: UUID, offset: int, limit: int
    ) -> tuple[AssignmentCandidate, ...]: ...
    def move_operation(self, caller: Caller, operation: UUID) -> MemberMoveAck: ...
    def move_home(
        self, caller: Caller, command: MemberCommand
    ) -> tuple[MemberMoveAck, MemberMutation | None, MemberMoveProof | None]: ...
    def confirm_move(
        self, caller: Caller, ack: MemberMoveAck, proof: MemberMoveProof | None
    ) -> None: ...
    def seal_move(self, caller: Caller, ack: MemberMoveAck, clock: datetime) -> MemberMoveAck: ...

    def get(self, caller: Caller, ident: UUID) -> Member: ...
    def list(self, caller: Caller, offset: int, limit: int) -> MemberPage: ...
    def operation(self, caller: Caller, ident: UUID) -> MemberResult: ...
    def change(
        self, caller: Caller, command: MemberCommand
    ) -> tuple[MemberResult, MemberMutation | None]: ...
    def confirm(self, caller: Caller, result: MemberResult) -> None: ...
    def seal(self, caller: Caller, result: MemberResult, clock: datetime) -> MemberResult: ...
