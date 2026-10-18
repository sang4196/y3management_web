"""The actual management fingerprint helpers never materialize raw verifier rows."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_iam import SyntheticSecret


@pytest.mark.parametrize("helper", ["snapshot", "factors"])
def test_management_helper_error_locals_private(tmp_path: Path, helper: str) -> None:
    canary = SyntheticSecret(secrets.token_hex(24))
    probe = tmp_path / "test_helper_failure.py"
    probe.write_text("""import hashlib, os
from tests.test_iam_master_management import snapshot, factors

class Result:
    def scalar_one(self):
        return hashlib.md5(os.environ['PRIVATE_CANARY'].encode()).hexdigest()
class Database:
    count = 0
    def session(self): return self
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, query, *args):
        assert 'md5(' in str(query), 'RAW_ROWS_MUST_STAY_IN_DB'
        self.count += 1
        if self.count == 2: raise RuntimeError('EXPECTED_HELPER_FAILURE')
        return Result()
def test_helper_failure():
    if os.environ['HELPER'] == 'snapshot': snapshot(Database())
    else: factors(Database(), 'synthetic-id')
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
        env={**os.environ, "PRIVATE_CANARY": canary, "HELPER": helper},
        capture_output=True,
        timeout=30,
    )
    code = result.returncode
    output = SyntheticSecret((result.stdout + result.stderr).decode())
    del result
    assert code == 1 and "EXPECTED_HELPER_FAILURE" in output
    assert canary not in output


@pytest.mark.parametrize("action", ["account_disable", "account_restore", "login_id_change"])
def test_master_management_requires_mfa_before_any_transaction(action: str) -> None:
    from types import SimpleNamespace
    from typing import Any, cast
    from uuid import uuid4

    from y3management.contracts import Rejected
    from y3management.use_cases import Service

    # No open() method: a legacy request must reject before touching persistence.
    service = Service(cast(Any, SimpleNamespace(settings=SimpleNamespace(iam_mode="s1_password"))))
    with pytest.raises(Rejected) as rejected:
        service.manage_master(None, None, uuid4(), 1, cast(Any, action), "renamed.master")
    assert rejected.value.status == 403
