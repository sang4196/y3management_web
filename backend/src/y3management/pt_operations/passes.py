"""Issuance-only policy; cross-module facts are validated by the outer application UoW."""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from uuid import UUID

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.pt_operations.pass_repository import PassRepository
from y3management.pt_operations.public import IssueCommand, IssueResult, PassIssueEvent, Product


def issue_role(caller: Caller, branch: UUID) -> tuple[str, UUID | None]:
    if caller.master:
        return "MASTER", None
    if caller.branch_id == branch:
        return "BRANCH_ADMIN", branch
    if caller.operator and caller.operator.branch_id == branch:
        return "OPERATOR", branch
    raise Rejected(404, "not_found")


def fingerprint(caller: Caller, command: IssueCommand) -> bytes:
    if any(
        not isinstance(getattr(command, k), UUID)
        for k in ["operation_id", "issued_branch_id", "member_id", "trainer_id", "product_id"]
    ) or any(
        type(getattr(command, k)) is not int or not 1 <= getattr(command, k) <= 9223372036854775807
        for k in [
            "expected_branch_version",
            "expected_member_version",
            "expected_trainer_version",
            "expected_product_version",
        ]
    ):
        raise Rejected(422, "invalid_request")
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


class Passes:
    def __init__(self, repository: PassRepository) -> None:
        self.repo = repository

    def operation(self, caller: Caller, ident: UUID) -> IssueResult:
        row = self.repo.operation(caller.organization_id, ident)
        if row is None or row[1] != caller.account_id:
            raise Rejected(404, "not_found")
        issue_role(caller, row[0].pass_record.issued_branch_id)
        return row[0]

    def replay(self, caller: Caller, command: IssueCommand) -> IssueResult | None:
        digest = fingerprint(caller, command)
        row = self.repo.operation(caller.organization_id, command.operation_id)
        if row is None:
            return None
        result = self.operation(caller, command.operation_id)
        if row[2] != digest:
            raise Rejected(409, "operation_conflict")
        return result

    def issue(
        self, caller: Caller, command: IssueCommand, product: Product
    ) -> tuple[IssueResult, PassIssueEvent]:
        selected_role, branch = issue_role(caller, command.issued_branch_id)
        digest = fingerprint(caller, command)
        if product.id != command.product_id or product.version != command.expected_product_version:
            raise Rejected(409, "conflict")
        if not product.selling:
            raise Rejected(409, "product_stopped")
        return self.repo.create(caller, command, product, selected_role, branch, digest)

    def confirm(self, caller: Caller, result: IssueResult) -> None:
        if self.operation(caller, result.operation_id) != result:
            raise Rejected(409, "conflict")

    def seal(self, caller: Caller, result: IssueResult, clock: datetime) -> IssueResult:
        return self.repo.seal(caller.organization_id, result, clock)
