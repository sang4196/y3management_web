"""Canonical contact values and independent role selection without a database."""

from typing import Any
from uuid import uuid4

import pytest

from y3management.contracts import Rejected
from y3management.http import MemberInput, MemberUpdateInput
from y3management.iam.public import Caller, OperatorScope
from y3management.membership.application import normalize, role
from y3management.membership.public import MemberValues


@pytest.mark.parametrize(
    "phone", ["01020000000", "010-2000-0000", "+82 10 2000 0000", " +82-10-2000-0000 "]
)
def test_domestic_mobile_notation_is_one_canonical_value(phone: str) -> None:
    value = normalize(MemberValues("  가상 회원  ", phone))
    assert value.name == "가상 회원" and value.phone == "01020000000"
    assert value.name not in repr(value) and value.phone not in repr(value)


@pytest.mark.parametrize(
    "phone",
    [
        "",
        " ",
        "0212345678",
        "07020000000",
        "+12002000000",
        "01120000000",
        "01010000000",
        "0102000000",
        "010200000000",
        "+8201020000000",
        "010.2000.0000",
        "０１０２０００００００",
        "01020000000\n",
    ],
)
def test_other_number_kinds_and_malformed_values_are_generic(phone: str) -> None:
    with pytest.raises(Rejected, match="invalid_request"):
        normalize(MemberValues("가상 회원", phone))


def test_current_role_union_never_lends_admin_rights_to_operator_branch() -> None:
    a, b = uuid4(), uuid4()
    caller = Caller(uuid4(), uuid4(), a, False, OperatorScope(b, 1))
    assert role(caller, a) == ("BRANCH_ADMIN", a)
    assert role(caller, b) == ("OPERATOR", b)
    with pytest.raises(Rejected):
        role(caller, b, "deactivate")
    with pytest.raises(Rejected):
        role(caller, uuid4())


def test_http_personal_fields_are_not_in_model_repr() -> None:
    args: dict[str, Any] = dict(operation_id=uuid4(), name="가상 비공개 이름", phone="01020000000")
    for model in [
        MemberInput(**args, home_branch_id=uuid4()),
        MemberUpdateInput(**args, expected_member_version=1),
    ]:
        assert args["name"] not in repr(model) and args["phone"] not in repr(model)
