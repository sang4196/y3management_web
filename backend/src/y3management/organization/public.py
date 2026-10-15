"""Organization facts and scoped read contracts."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from y3management.iam.public import Caller


@dataclass(frozen=True)
class Branch:
    id: UUID
    code: str
    name: str


@dataclass(frozen=True)
class BranchPage:
    items: tuple[Branch, ...]
    total: int


class OrganizationPort(Protocol):
    def create_initial(self, name: str) -> UUID: ...
    def create_branch(self, caller: Caller, code: str, name: str) -> Branch: ...
    def require_branch(self, caller: Caller, branch_id: UUID) -> None: ...
    def list_branches(self, caller: Caller, offset: int, limit: int) -> BranchPage: ...
    def get_branch(self, caller: Caller, branch_id: UUID) -> Branch: ...
