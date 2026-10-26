"""External request boundary: identity is never an input authority."""

import pytest
from pydantic import ValidationError

from y3management.http import TrainerAccountInput, TrainerSetupInput


@pytest.mark.parametrize(
    "field", ["role", "organization_id", "branch_id", "admin_scope", "account_id"]
)
def test_issue_rejects_client_authority(field: str) -> None:
    with pytest.raises(ValidationError):
        TrainerAccountInput.model_validate(
            {
                "operation_id": "00000000-0000-0000-0000-000000000001",
                "login_id": "trainer.allowed",
                field: "untrusted",
            }
        )


@pytest.mark.parametrize("version", [True, 0, -1, "1"])
def test_reissue_requires_actual_positive_integer(version: object) -> None:
    with pytest.raises(ValidationError):
        TrainerSetupInput.model_validate(
            {
                "operation_id": "00000000-0000-0000-0000-000000000001",
                "expected_account_version": version,
            }
        )
