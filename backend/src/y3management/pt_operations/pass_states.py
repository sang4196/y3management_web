"""Manual expiration only: current Issued Branch administrators and immutable issue facts."""

import hashlib
import json
import unicodedata
from dataclasses import asdict, replace
from datetime import datetime
from uuid import UUID

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.pt_operations.pass_state_repository import StateRepository
from y3management.pt_operations.public import (
    PassState,
    PassStateCommand,
    PassStateEvent,
    PassStatePage,
    PassStateResult,
)


def state_role(caller: Caller, branch: UUID | None = None) -> tuple[str, UUID | None]:
    if caller.master:
        return "MASTER", None
    if caller.branch_id is not None and (branch is None or caller.branch_id == branch):
        return "BRANCH_ADMIN", caller.branch_id
    raise Rejected(403 if branch is None else 404, "forbidden" if branch is None else "not_found")


def canonical(c: PassStateCommand) -> PassStateCommand:
    if (
        not isinstance(c.operation_id, UUID)
        or not isinstance(c.pass_id, UUID)
        or type(c.expected_state_version) is not int
        or not 1 <= c.expected_state_version <= 9223372036854775807
        or type(c.desired_expired) is not bool
        or not isinstance(c.reason, str)
        or not c.reason.strip()
        or len(c.reason.strip()) > 200
        or any(unicodedata.category(x) in {"Cc", "Cs"} for x in c.reason)
    ):
        raise Rejected(422, "invalid_request")
    return replace(c, reason=c.reason.strip())


def fingerprint(caller: Caller, command: PassStateCommand) -> bytes:
    return hashlib.sha256(
        json.dumps(
            {
                **asdict(command),
                "actor_id": caller.account_id,
                "organization_id": caller.organization_id,
                "canonical_version": 1,
            },
            default=str,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).digest()


class PassStates:
    def __init__(self, repository: StateRepository) -> None:
        self.repo = repository

    def initialize(self, org: UUID, ident: UUID) -> None:
        self.repo.initialize(org, ident)

    def get(self, caller: Caller, ident: UUID) -> PassState:
        state_role(caller)
        branch = self.repo.branch(caller.organization_id, ident)
        state_role(caller, branch)
        return self.repo.get(caller.organization_id, ident)

    def list(self, caller: Caller, offset: int, limit: int) -> PassStatePage:
        state_role(caller)
        if offset < 0 or not 1 <= limit <= 100:
            raise Rejected(422, "invalid_request")
        return self.repo.list(caller, offset, limit)

    def operation(self, caller: Caller, ident: UUID) -> PassStateResult:
        state_role(caller)
        row = self.repo.operation(caller.organization_id, ident)
        if row is None or row[1] != caller.account_id:
            raise Rejected(404, "not_found")
        current = self.get(caller, row[0].current_state.pass_id)
        return replace(row[0], current_state=current)

    def replay(self, caller: Caller, command: PassStateCommand) -> PassStateResult | None:
        state_role(caller)
        c = canonical(command)
        row = self.repo.operation(caller.organization_id, c.operation_id)
        if row is None:
            return None
        result = self.operation(caller, c.operation_id)
        if row[2] != fingerprint(caller, c):
            raise Rejected(409, "operation_conflict")
        return result

    def change(
        self, caller: Caller, command: PassStateCommand
    ) -> tuple[PassStateResult, PassStateEvent | None]:
        c = canonical(command)
        before = self.get(caller, c.pass_id)
        if before.version != c.expected_state_version:
            raise Rejected(409, "conflict")
        changed = before.manual_expired != c.desired_expired
        if changed and before.version == 9223372036854775807:
            raise Rejected(409, "version_exhausted")
        role, branch = state_role(caller, before.issued_branch_id)
        return self.repo.prepare(caller, c, before, role, branch, changed, fingerprint(caller, c))

    def confirm(self, caller: Caller, result: PassStateResult) -> None:
        if self.operation(caller, result.operation_id) != result:
            raise Rejected(409, "conflict")

    def seal(self, caller: Caller, result: PassStateResult, clock: datetime) -> PassStateResult:
        return self.repo.seal(caller.organization_id, result, clock)
