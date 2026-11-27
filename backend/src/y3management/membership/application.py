"""Current independent edit scopes, canonical mobile values and kind-bound receipts."""

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, replace
from datetime import datetime
from uuid import UUID

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.membership.infrastructure import Repository
from y3management.membership.public import (
    Member,
    MemberCommand,
    MemberMutation,
    MemberPage,
    MemberResult,
    MemberValues,
)
from y3management.organization.public import OrganizationPort


def normalize(values: MemberValues) -> MemberValues:
    if (
        not isinstance(values.name, str)
        or not values.name.strip()
        or len(values.name.strip()) > 200
        or any(unicodedata.category(c) in {"Cc", "Cs"} for c in values.name)
        or not isinstance(values.phone, str)
        or len(values.phone) > 64
        or re.fullmatch(r"[0-9+ -]+", values.phone) is None
    ):
        raise Rejected(422, "invalid_request")
    phone = values.phone.replace(" ", "").replace("-", "")
    if phone.startswith("+82"):
        phone = "0" + phone[3:]
    if re.fullmatch(r"010[2-9][0-9]{7}", phone) is None:
        raise Rejected(422, "invalid_request")
    return MemberValues(values.name.strip(), phone)


def role(caller: Caller, home: UUID, kind: str = "update") -> tuple[str, UUID | None]:
    if caller.master:
        return "MASTER", None
    if caller.branch_id == home:
        return "BRANCH_ADMIN", home
    if kind in {"create", "update"} and caller.operator and caller.operator.branch_id == home:
        return "OPERATOR", home
    raise Rejected(404, "not_found")


def require_editor(caller: Caller) -> None:
    if not (caller.master or caller.branch_id or caller.operator):
        raise Rejected(403, "forbidden")


class Membership:
    def __init__(self, repository: Repository, organization: OrganizationPort) -> None:
        self.repo = repository
        self.organization = organization

    def _current(self, caller: Caller, ident: UUID, kind: str = "update") -> Member:
        require_editor(caller)
        home = self.repo.home(caller.organization_id, ident)
        role(caller, home, kind)
        fact = self.organization.lock_member_branch(caller, home)
        member = self.repo.get(caller.organization_id, ident)
        if member.home_branch_id != home:
            raise Rejected(409, "conflict")
        return replace(member, home_branch_name=fact.name, home_active=fact.active)

    def get(self, caller: Caller, ident: UUID) -> Member:
        return self._current(caller, ident)

    def list(self, caller: Caller, offset: int, limit: int) -> MemberPage:
        require_editor(caller)
        if offset < 0 or not 1 <= limit <= 100:
            raise Rejected(422, "invalid_request")
        page = self.repo.list(caller, offset, limit)
        return MemberPage(tuple(self.get(caller, m.id) for m in page.items), page.total)

    def operation(self, caller: Caller, ident: UUID) -> MemberResult:
        require_editor(caller)
        row = self.repo.operation(caller.organization_id, ident)
        if row is None or row[1] != caller.account_id:
            raise Rejected(404, "not_found")
        result = row[0]
        current = self._current(caller, result.current_member.id, result.kind)
        committed = replace(
            result.committed_member,
            home_branch_name=current.home_branch_name,
            home_active=current.home_active,
        )
        return replace(result, current_member=current, committed_member=committed)

    def change(
        self, caller: Caller, command: MemberCommand
    ) -> tuple[MemberResult, MemberMutation | None]:
        require_editor(caller)
        c = command
        if (
            not isinstance(c.operation_id, UUID)
            or c.kind not in {"create", "update", "deactivate", "reactivate"}
            or (
                c.kind == "create"
                and (
                    c.member_id is not None
                    or c.expected_member_version is not None
                    or not isinstance(c.home_branch_id, UUID)
                )
            )
            or (
                c.kind != "create"
                and (
                    not isinstance(c.member_id, UUID)
                    or type(c.expected_member_version) is not int
                    or not 1 <= c.expected_member_version <= 9223372036854775807
                    or c.home_branch_id is not None
                )
            )
            or (c.kind in {"create", "update"} and c.values is None)
            or (c.kind in {"deactivate", "reactivate"} and c.values is not None)
        ):
            raise Rejected(422, "invalid_request")
        if c.values is not None:
            c = replace(c, values=normalize(c.values))
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    **asdict(c),
                    "actor_id": caller.account_id,
                    "organization_id": caller.organization_id,
                    "canonical_version": 1,
                },
                sort_keys=True,
                default=str,
                separators=(",", ":"),
            ).encode()
        ).digest()
        old = self.repo.operation(caller.organization_id, c.operation_id)
        if old is not None:
            if old[1] != caller.account_id or old[2] != fingerprint:
                raise Rejected(409, "operation_conflict")
            return self.operation(caller, c.operation_id), None
        before = self._current(caller, c.member_id, c.kind) if c.member_id else None
        home = before.home_branch_id if before else c.home_branch_id
        assert home is not None
        selected_role, branch = role(caller, home, c.kind)
        fact = self.organization.lock_member_branch(caller, home)
        if before is None and not fact.active:
            raise Rejected(409, "branch_inactive")
        if before is not None and before.version != c.expected_member_version:
            raise Rejected(409, "conflict")
        active = before.active if before else True
        if c.kind in {"deactivate", "reactivate"}:
            active = c.kind == "reactivate"
        changed = (
            before is None
            or before.active != active
            or (c.values is not None and before.values != c.values)
        )
        if changed and before and before.version == 9223372036854775807:
            raise Rejected(409, "version_exhausted")
        result, mutation = self.repo.prepare(
            caller, c, before, home, active, selected_role, branch, changed, fingerprint
        )
        current = replace(
            result.current_member, home_branch_name=fact.name, home_active=fact.active
        )
        return replace(result, committed_member=current, current_member=current), mutation

    def confirm(self, caller: Caller, result: MemberResult) -> None:
        if self.operation(caller, result.operation_id) != result:
            raise Rejected(409, "conflict")

    def seal(self, caller: Caller, result: MemberResult, clock: datetime) -> MemberResult:
        self.repo.seal(caller.organization_id, result.operation_id, clock)
        return result
