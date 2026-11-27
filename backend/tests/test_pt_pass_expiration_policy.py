"""No database: admin scope and private required state-change reason."""

from dataclasses import replace
from uuid import uuid4

import pytest

from y3management.contracts import Rejected
from y3management.http import PassExpirationInput
from y3management.iam.public import Caller, OperatorScope
from y3management.pt_operations.pass_states import canonical, state_role
from y3management.pt_operations.public import PassStateCommand


def test_operator_scope_does_not_extend_ba_expiration_scope() -> None:
    a, b = uuid4(), uuid4()
    caller = Caller(uuid4(), uuid4(), a, False, OperatorScope(b, 1))
    assert state_role(caller, a) == ("BRANCH_ADMIN", a)
    with pytest.raises(Rejected) as error:
        state_role(caller, b)
    assert error.value.status == 404
    with pytest.raises(Rejected) as error:
        state_role(replace(caller, branch_id=None))
    assert error.value.status == 403
    assert state_role(replace(caller, master=True), b) == ("MASTER", None)


@pytest.mark.parametrize("reason", ["", " ", "a" * 201, "bad\nreason"])
def test_reason_required_bounded_and_private(reason: str) -> None:
    c = PassStateCommand(uuid4(), uuid4(), 1, True, reason)
    with pytest.raises(Rejected):
        canonical(c)


def test_canonical_reason_and_http_repr() -> None:
    c = PassStateCommand(uuid4(), uuid4(), 1, True, " 가상 비공개 사유 ")
    assert canonical(c).reason == "가상 비공개 사유" and c.reason not in repr(c)
    body = PassExpirationInput(
        operation_id=c.operation_id, expected_state_version=1, desired_expired=True, reason=c.reason
    )
    assert c.reason not in repr(body)
