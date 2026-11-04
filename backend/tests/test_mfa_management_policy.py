"""Secret-safe recovery inputs and failure rendering without a database."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

from tests.test_iam import SyntheticSecret


def test_recovery_failure_locals_canary(tmp_path: Path) -> None:
    secret = SyntheticSecret(secrets.token_hex(32))
    probe = tmp_path / "test_management_private.py"
    probe.write_text("""import os
from datetime import datetime, UTC
from y3management.http import ResetComplete, EmergencyPassword
from y3management.iam.public import Setup
from tests.password_helpers import protect

def test_expected_failure():
    token = ResetComplete(reset_token=os.environ['RECOVERY_CANARY'],
        new_password=os.environ['RECOVERY_CANARY'])
    response = EmergencyPassword(emergency_token=os.environ['RECOVERY_CANARY'],
        new_password=os.environ['RECOVERY_CANARY'])
    delivered = Setup(os.environ['RECOVERY_CANARY'],datetime.now(UTC))
    result = protect({'recovery_link':os.environ['RECOVERY_CANARY']})
    passed = False
    assert passed, 'EXPECTED_RECOVERY_PRIVATE_FAILURE'
""")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(probe),
            "--confcutdir",
            str(tmp_path),
            "--showlocals",
            "-q",
            "-o",
            "addopts=",
        ],
        env={**os.environ, "RECOVERY_CANARY": secret},
        capture_output=True,
        timeout=30,
    )
    code = result.returncode
    output = SyntheticSecret((result.stdout + result.stderr).decode())
    del result
    assert code == 1 and "EXPECTED_RECOVERY_PRIVATE_FAILURE" in output
    assert secret not in output


def test_derived_link_helper_locals_canary(tmp_path: Path) -> None:
    secret = SyntheticSecret(secrets.token_hex(32))
    probe = tmp_path / "test_derived_private.py"
    probe.write_text("""import os
import pytest
from tests.test_iam import SyntheticSecret
from tests.password_helpers import activate
from tests.password_helpers import link_token, complete

class Response:
    status_code = 200
    def json(self):
        return {"csrf_token": SyntheticSecret(os.environ["DERIVED_CANARY"])}

class Client:
    def get(self, *args, **kwargs):
        return Response()
    def post(self, *args, **kwargs):
        passed = False
        assert passed, "EXPECTED_DERIVED_HELPER_FAILURE"

@pytest.mark.parametrize("flow", ["setup", "recovery"])
def test_actual_helpers(flow):
    link = SyntheticSecret("https://example.invalid/#token=" + os.environ["DERIVED_CANARY"])
    token = link_token(link)
    if flow == "setup":
        activate(Client(), token, SyntheticSecret(os.environ["DERIVED_CANARY"]))
    else:
        complete(Client(), token, SyntheticSecret(os.environ["DERIVED_CANARY"]))
""")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(probe),
            "--confcutdir",
            str(tmp_path),
            "--showlocals",
            "-q",
            "-o",
            "addopts=",
        ],
        env={**os.environ, "DERIVED_CANARY": secret},
        capture_output=True,
        timeout=30,
    )
    code = result.returncode
    output = SyntheticSecret((result.stdout + result.stderr).decode())
    del result
    assert code == 1 and "EXPECTED_DERIVED_HELPER_FAILURE" in output and "2 failed" in output
    assert secret not in output
