"""Policy and startup guarantees independent of PostgreSQL availability."""

import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.iam.passwords import Passwords
from y3management.runtime import ProcessGuard


@pytest.fixture(scope="module")
def passwords() -> Passwords:
    return Passwords()


@pytest.mark.parametrize(
    "value",
    [
        "password" * 3,
        "administrator" * 2,
        "correcthorsebatterystaple",
        "correct horse battery staple",
        "y3management2026@",
        "IndependentAdmin2026@",
        "비밀번호" * 4 + "!",
        "비밀번호" * 4,
        "123456789012345",
    ],
)
def test_real_filtered_corpus_preserves_finite_defenses(passwords: Passwords, value: str) -> None:
    with pytest.raises(Rejected) as rejected:
        passwords.policy(value, "independentadmin")
    assert rejected.value.status == 422


@pytest.mark.parametrize(
    "value",
    [
        "노란 우산 아래 password 단어를 적어 둔 산책길.",
        "y3management 옆 골목에서 초록 고양이를 보았다.",
        "  Quiet clouds pass above a small amber lantern.  ",
        " 비밀번호비밀번호비밀번호비밀번호 ",
    ],
)
def test_password_input_is_nfc_only(passwords: Passwords, value: str) -> None:
    import unicodedata

    assert passwords.policy(unicodedata.normalize("NFD", value), "independentadmin") == value


def test_hash_gate_has_no_unbounded_queue(passwords: Passwords) -> None:
    with passwords.capacity(), passwords.capacity(), pytest.raises(Rejected) as full:
        passwords.create("서로 다른 충분한 가상 단어 네 개", "person")
    assert full.value.status == 503
    encoded = passwords.create("서로 다른 충분한 가상 단어 네 개", "person")
    assert passwords.verify("서로 다른 충분한 가상 단어 네 개", encoded)[0]


def test_digest_corpus_tampering_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import y3management.iam.passwords as module

    original = Path(module.__file__).with_name("data")
    target = tmp_path / "data"
    shutil.copytree(original, target)
    artifact = target / "blocked-sha256.txt"
    raw = artifact.read_bytes()
    artifact.write_bytes((b"f" if raw[:1] != b"f" else b"e") + raw[1:])
    monkeypatch.setattr(module, "__file__", str(tmp_path / "passwords.py"))
    with pytest.raises(ValueError, match="CORPUS_INTEGRITY_FAILED"):
        Passwords()


def test_startup_failure_releases_canonical_guard(settings: Settings) -> None:
    class WrongResource:
        def close(self) -> None:
            pass

        def is_ready(self) -> bool:
            return True

    cfg = Settings.model_validate(
        {
            **settings.model_dump(),
            "database_schema": "iam_test_" + uuid4().hex,
            "iam_enabled": True,
            "canonical_origin": "https://localhost:8443",
            "iam_key": "s" * 43,
            "security_state_capacity": 64,
            "auth_session_capacity": 16,
        }
    )
    for _ in range(2):
        with (
            pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"),
            TestClient(create_app(cfg, database=WrongResource())),
        ):
            pass
        guard = ProcessGuard(cfg)
        guard.close()
    assert Path("/tmp/y3management-runtime").is_dir()


@pytest.mark.parametrize(
    "body",
    [
        {"expected_version": True, "login_id": "valid.name"},
        {"expected_version": "2", "login_id": "valid.name"},
        {"expected_version": 2, "login_id": 123},
        {"expected_version": 2, "login_id": "valid.name", "role": "MASTER"},
        {"expected_version": 0, "login_id": "valid.name"},
    ],
)
def test_login_id_change_strict_contract(body: dict[str, object]) -> None:
    from pydantic import ValidationError

    from y3management.http import LoginIDChange

    with pytest.raises(ValidationError):
        LoginIDChange.model_validate(body)


@pytest.mark.parametrize(
    "identifier", [" abcd", "abcd ", "ab", "a" * 65, "reserved:name", "한글아이디"]
)
def test_login_id_normalization_rejects_ambiguous_names(identifier: str) -> None:
    from y3management.use_cases import normalize_login

    with pytest.raises(Rejected) as error:
        normalize_login(identifier)
    assert error.value.status == 422


def test_failure_locals_keep_synthetic_secrets_private(tmp_path: Path) -> None:
    import os
    import secrets
    import subprocess
    import sys

    from tests.test_iam import SyntheticSecret

    canaries = {
        name: SyntheticSecret(secrets.token_hex(16))
        for name in ("PASSWORD", "COOKIE", "NONCE", "HASH", "ANCHOR")
    }
    probe = tmp_path / "test_private_failure.py"
    probe.write_text("""import os
from uuid import uuid4
from tests.test_iam import SyntheticSecret
from tests.test_iam_s2 import fingerprint_rows
from y3management.iam.public import LoginProof, Reservation

def test_deliberate_failure():
    password = SyntheticSecret(os.environ['PASSWORD'])
    cookie = SyntheticSecret(os.environ['COOKIE'])
    nonce = SyntheticSecret(os.environ['NONCE'])
    encoded = SyntheticSecret(os.environ['HASH'])
    reservation = Reservation(bytes.fromhex(os.environ['ANCHOR']), uuid4(), uuid4(), 2)
    proof = LoginProof(uuid4(), 2, bytes.fromhex(os.environ['HASH']))
    fingerprint = fingerprint_rows([(encoded, reservation.key)])
    safe_boolean = False
    assert safe_boolean, 'EXPECTED_PRIVATE_FAILURE'
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
        env={**os.environ, **canaries},
        capture_output=True,
        timeout=30,
    )
    code = result.returncode
    output = SyntheticSecret((result.stdout + result.stderr).decode())
    del result
    expected_failure = code == 1 and "EXPECTED_PRIVATE_FAILURE" in output
    leaked = any(
        value in output or repr(bytes.fromhex(value)) in output for value in canaries.values()
    )
    repr_hidden = "<synthetic-secret>" in output
    assert expected_failure and repr_hidden
    assert not leaked
