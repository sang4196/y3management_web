"""No DB checks for explicit modes, protected installation files and private DTOs."""

import os
import secrets
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from y3management.cli import PrivateEnrollmentFile
from y3management.config import Settings
from y3management.iam.public import Ceremony, Setup


def test_mfa_has_no_missing_configuration_fallback(settings: Settings) -> None:
    values = settings.model_dump() | dict(
        iam_enabled=True,
        canonical_origin="https://localhost:8443",
        iam_key=secrets.token_urlsafe(32),
        security_state_capacity=64,
        auth_session_capacity=16,
    )
    with pytest.raises(ValidationError):
        Settings.model_validate(values)
    for mode in ("s1_password", "mfa"):
        assert Settings.model_validate(values | {"iam_mode": mode}).iam_mode == mode
    with pytest.raises(ValidationError):
        Settings.model_validate(values | {"iam_mode": "mfa", "environment": "production"})


@pytest.mark.parametrize("case", ["public_parent", "symlink_parent", "existing", "symlink_file"])
def test_private_delivery_denies_unsafe_paths(tmp_path: Path, case: str) -> None:
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    target = private / "link"
    if case == "public_parent":
        private.chmod(0o755)
    if case == "symlink_parent":
        alias = tmp_path / "alias"
        alias.symlink_to(private)
        target = alias / "link"
    if case == "existing":
        target.write_text("existing")
    if case == "symlink_file":
        target.symlink_to(private / "other")
    with pytest.raises((ValueError, OSError)):
        PrivateEnrollmentFile(str(target), "https://localhost")
    if case == "existing":
        assert target.read_text() == "existing"


def test_private_file_delivery_and_rollback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    target = private / "capability"
    secret = secrets.token_urlsafe(32)
    previous = os.umask(0o777)
    try:
        file = PrivateEnrollmentFile(str(target), "https://localhost")
    finally:
        os.umask(previous)
    file.deliver(Setup(secret, datetime.now(UTC)))
    assert target.stat().st_mode & 0o777 == 0o600
    assert target.stat().st_uid == os.getuid()
    file.close(remove=True)
    assert not target.exists()
    assert secret not in capsys.readouterr().out
    ceremony = Ceremony(secret, secret, secret, datetime.now(UTC))
    assert secret not in repr(ceremony)


def test_mfa_failure_locals_canary(tmp_path: Path) -> None:
    import subprocess
    import sys

    from tests.test_iam import SyntheticSecret

    names = ("CEREMONY", "NONCE", "CHALLENGE", "RAW_PROOF", "PUBLIC_KEY", "INSTALL_FILE")
    values = {name: SyntheticSecret(secrets.token_hex(24)) for name in names}
    probe = tmp_path / "test_mfa_failure.py"
    probe.write_text("""import os
from datetime import datetime, UTC
from uuid import uuid4
from tests.test_iam import SyntheticSecret
from tests.test_iam_mfa import protect
from y3management.iam.public import Ceremony, RegistrationProof, Setup

def test_private_mfa_failure():
    ceremony = Ceremony(os.environ['CEREMONY'],os.environ['NONCE'],
                        os.environ['CHALLENGE'],datetime.now(UTC))
    setup = Setup(os.environ['INSTALL_FILE'],datetime.now(UTC))
    proof = RegistrationProof(uuid4(), bytes.fromhex(os.environ['CHALLENGE']),
        bytes.fromhex(os.environ['RAW_PROOF']),bytes.fromhex(os.environ['PUBLIC_KEY']),0,
        'single_device',False,'install')
    payload = protect({'response':{'clientDataJSON':os.environ['RAW_PROOF']},
                       'options':{'challenge':os.environ['CHALLENGE']}})
    file_contents = SyntheticSecret(os.environ['INSTALL_FILE'])
    passed = False
    assert passed, 'EXPECTED_MFA_PRIVATE_FAILURE'
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
        env={**os.environ, **values},
        capture_output=True,
        timeout=30,
    )
    code = result.returncode
    output = SyntheticSecret((result.stdout + result.stderr).decode())
    del result
    assert code == 1 and "EXPECTED_MFA_PRIVATE_FAILURE" in output
    assert not any(
        value in output or repr(bytes.fromhex(value)) in output for value in values.values()
    )
