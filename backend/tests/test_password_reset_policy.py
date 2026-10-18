"""Actual reset DTO and helper failure rendering excludes unbound canary secrets."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

from tests.test_iam import SyntheticSecret


def test_reset_failure_locals_canary(tmp_path: Path) -> None:
    secret = SyntheticSecret(secrets.token_hex(32))
    probe = tmp_path / "test_reset_private.py"
    probe.write_text("""import os
from uuid import uuid4
from y3management.http import ResetComplete
from y3management.iam.public import ResetProof
from tests.test_iam import SyntheticSecret
from tests.test_iam_mfa_management import link_token
from tests.test_iam_password_reset import complete

class Response:
    status_code = 200
    def json(self):
        return {"csrf_token": SyntheticSecret(os.environ["RESET_CANARY"])}

class Client:
    def get(self, *args, **kwargs):
        return Response()
    def post(self, *args, **kwargs):
        passed = False
        assert passed, "EXPECTED_RESET_HELPER_FAILURE"

def test_actual_reset_helpers():
    body = ResetComplete(reset_token=os.environ["RESET_CANARY"],
                         new_password=os.environ["RESET_CANARY"])
    proof = ResetProof(uuid4(),uuid4(),1,1)
    link = SyntheticSecret("https://example.invalid/reset#token="+os.environ["RESET_CANARY"])
    complete(Client(),link_token(link),SyntheticSecret(os.environ["RESET_CANARY"]))
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
        env={**os.environ, "RESET_CANARY": secret},
        capture_output=True,
        timeout=30,
    )
    code = result.returncode
    output = SyntheticSecret((result.stdout + result.stderr).decode())
    del result
    assert code == 1 and "EXPECTED_RESET_HELPER_FAILURE" in output
    assert secret not in output
