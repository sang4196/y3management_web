"""Protected execution files: meaningful hostile filesystem and JSON cases."""

import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from y3management.config import Settings
from y3management.operating import Descriptor, authority, pairs, protected_read


def test_protected_input_regular_and_duplicate_keys(tmp_path: Path) -> None:
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    target = folder / "request"
    target.write_bytes(b'{"value":1}')
    target.chmod(0o600)
    assert protected_read(str(target)) == b'{"value":1}'
    with pytest.raises(ValueError):
        json.loads('{"value":1,"value":2}', object_pairs_hook=pairs)


@pytest.mark.parametrize(
    "attack", ["symlink", "parent_link", "hardlink", "fifo", "mode", "parent_mode", "oversize"]
)
def test_protected_input_rejects_unsafe_files(tmp_path: Path, attack: str) -> None:
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    target = folder / "request"
    target.write_bytes(b"{}")
    target.chmod(0o600)
    chosen = target
    if attack == "symlink":
        chosen = folder / "link"
        chosen.symlink_to(target)
    elif attack == "parent_link":
        link = tmp_path / "linked"
        link.symlink_to(folder, target_is_directory=True)
        chosen = link / target.name
    elif attack == "hardlink":
        os.link(target, folder / "alias")
    elif attack == "fifo":
        target.unlink()
        os.mkfifo(target, 0o600)
    elif attack == "mode":
        target.chmod(0o644)
    elif attack == "parent_mode":
        folder.chmod(0o755)
    else:
        target.write_bytes(b"x" * 16385)
    with pytest.raises((ValueError, OSError)):
        protected_read(str(chosen))


def test_authority_requires_kernel_identity_and_fixed_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    descriptor = folder / "authority"
    org = uuid4()
    body = dict(
        uid=os.getuid(),
        executor_ref="fixture-operator",
        environment="test",
        database="y3management_test",
        database_schema="public",
        organizations=[str(org)],
        operations=["inspect", "execute", "status"],
    )
    descriptor.write_text(json.dumps(body))
    descriptor.chmod(0o600)
    settings = Settings(
        environment="test",
        database_url="postgresql+psycopg://y3management_test:synthetic@localhost:55433/y3management_test",
        iam_mode="mfa",
        emergency_authority_file=str(descriptor),
        emergency_test_authority=True,
    )
    assert authority(settings, org, "execute").executor_uid == os.getuid()
    with pytest.raises(ValueError):
        authority(settings, uuid4(), "execute")
    with pytest.raises(ValueError):
        authority(settings.model_copy(update={"emergency_test_authority": False}), org, "execute")
    with pytest.raises(ValueError):
        authority(settings.model_copy(update={"emergency_authority_file": None}), org, "execute")
    with pytest.raises(ValidationError):
        Descriptor.model_validate({**body, "approved": True})
    monkeypatch.setattr(os, "geteuid", lambda: os.getuid() + 1)
    with pytest.raises(ValueError):
        authority(settings, org, "execute")
