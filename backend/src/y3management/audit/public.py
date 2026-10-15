"""Allowlisted audit command, with no arbitrary payload or secret fields."""

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


class AuditPort(Protocol):
    def append(self, event: Event) -> None: ...
