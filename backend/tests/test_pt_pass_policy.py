"""No DB: exact issuance command and independent issuer scopes."""

from dataclasses import replace
from uuid import uuid4

import pytest

from y3management.contracts import Rejected
from y3management.http import PassSearchInput
from y3management.iam.public import Caller, OperatorScope
from y3management.pt_operations.passes import fingerprint, issue_role
from y3management.pt_operations.public import IssueCommand


def test_issue_role_union_and_command_actor_version_binding() -> None:
    a, b, org, actor = [uuid4() for _ in range(4)]
    caller = Caller(actor, org, a, False, OperatorScope(b, 1))
    assert issue_role(caller, a) == ("BRANCH_ADMIN", a)
    assert issue_role(caller, b) == ("OPERATOR", b)
    with pytest.raises(Rejected):
        issue_role(caller, uuid4())
    command = IssueCommand(uuid4(), b, 1, uuid4(), 1, uuid4(), 1, uuid4(), 1)
    original = fingerprint(caller, command)
    assert fingerprint(replace(caller, account_id=uuid4()), command) != original
    assert fingerprint(caller, replace(command, expected_product_version=2)) != original
    with pytest.raises(Rejected):
        fingerprint(caller, replace(command, expected_member_version=True))


def test_search_value_never_appears_in_model_repr() -> None:
    body = PassSearchInput(issued_branch_id=uuid4(), query="가상 비공개 검색어")
    assert body.query not in repr(body)
