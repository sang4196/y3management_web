"""Protected local operating inputs. Manual approval is an attestation, not identity proof."""

import json
import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.engine import make_url

from y3management.config import Settings
from y3management.iam.public import EmergencyRequest, EmergencySnapshot, OperatingRecoveryAuthority

Ref = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:/-]+$")]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class SnapshotInput(StrictInput):
    row_version: int = Field(gt=0, strict=True)
    security_version: int = Field(gt=0, strict=True)
    key_set_version: int = Field(ge=0, strict=True)
    reset_generation: int = Field(ge=0, strict=True)
    recovery_generation: int = Field(ge=0, strict=True)
    password_reset_pending: bool = Field(strict=True)
    recovery_pending: bool = Field(strict=True)
    password_ready: bool = Field(strict=True)
    key_ready: bool = Field(strict=True)


class ExecutionInput(StrictInput):
    operation_id: UUID
    organization_id: UUID
    account_id: UUID
    environment: Literal["test", "development"]
    database: str
    database_schema: str
    factors: Literal["password", "passkey", "both"]
    expected: SnapshotInput
    revocation_scope: Literal["target_only"]
    approval_ref: Ref
    owner_ref: Ref
    checked_at: datetime
    approval_valid_until: datetime
    manual_checks: Literal["owner_authority_original_current_recipient_all_masters_unavailable"]
    approval_conditions: Literal["issuance_only_no_additional_conditions"]
    supersedes: UUID | None = None


class Descriptor(StrictInput):
    uid: int = Field(ge=0, strict=True)
    executor_ref: Ref
    environment: Literal["test", "development"]
    database: str
    database_schema: str
    organizations: list[UUID] = Field(min_length=1, max_length=128)
    operations: list[Literal["inspect", "execute", "status"]] = Field(min_length=1, max_length=3)


def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError("DUPLICATE_INPUT_KEY")
        result[key] = value
    return result


def protected_read(path: str, *, root_policy: bool = False) -> bytes:
    target = Path(path)
    if not target.is_absolute() or ".." in target.parts or not target.name:
        raise ValueError("PROTECTED_ABSOLUTE_PATH_REQUIRED")
    owner = 0 if root_policy else os.getuid()
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    fd = -1
    try:
        for component in target.parent.parts[1:]:
            child = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            os.close(directory)
            directory = child
            metadata = os.fstat(directory)
            if root_policy and (metadata.st_uid != 0 or metadata.st_mode & 0o022):
                raise ValueError("UNTRUSTED_POLICY_HIERARCHY")
        metadata = os.fstat(directory)
        if not root_policy and (
            metadata.st_uid != owner or stat.S_IMODE(metadata.st_mode) != 0o700
        ):
            raise ValueError("PROTECTED_PARENT_REQUIRED")
        fd = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        before = os.fstat(fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != owner
            or before.st_nlink != 1
            or (
                stat.S_IMODE(before.st_mode) not in (0o400, 0o444)
                if root_policy
                else stat.S_IMODE(before.st_mode) != 0o600
            )
            or not 1 <= before.st_size <= 16384
        ):
            raise ValueError("PROTECTED_FILE_REQUIRED")
        raw = os.read(fd, 16385)
        after = os.fstat(fd)
        current = os.stat(target.name, dir_fd=directory, follow_symlinks=False)
        if (
            len(raw) != before.st_size
            or (
                before.st_ino,
                before.st_dev,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            != (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            or (current.st_ino, current.st_dev) != (before.st_ino, before.st_dev)
        ):
            raise ValueError("INPUT_CHANGED")
        return raw
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(directory)


def authority(settings: Settings, organization: UUID, action: str) -> OperatingRecoveryAuthority:
    if (
        os.getuid() != os.geteuid()
        or settings.iam_mode != "mfa"
        or settings.environment not in ("test", "development")
        or not settings.emergency_authority_file
    ):
        raise ValueError("OPERATING_AUTHORITY_REQUIRED")
    test = settings.emergency_test_authority
    if test and settings.environment != "test":
        raise ValueError("TEST_AUTHORITY_ONLY")
    raw = protected_read(settings.emergency_authority_file, root_policy=not test)
    descriptor = Descriptor.model_validate(json.loads(raw, object_pairs_hook=pairs))
    database = make_url(settings.database_url.get_secret_value()).database
    if (
        descriptor.uid != os.getuid()
        or descriptor.environment != settings.environment
        or descriptor.database != database
        or descriptor.database_schema != settings.database_schema
        or organization not in descriptor.organizations
        or action not in descriptor.operations
    ):
        raise ValueError("OPERATING_PERMISSION_DENIED")
    return OperatingRecoveryAuthority(
        organization, descriptor.executor_ref, os.getuid(), frozenset(descriptor.operations)
    )


def execution(settings: Settings, path: str) -> EmergencyRequest:
    body = ExecutionInput.model_validate(json.loads(protected_read(path), object_pairs_hook=pairs))
    if (
        body.environment != settings.environment
        or body.database != make_url(settings.database_url.get_secret_value()).database
        or body.database_schema != settings.database_schema
        or body.checked_at.tzinfo is None
        or body.approval_valid_until.tzinfo is None
    ):
        raise ValueError("EXECUTION_TARGET_OR_TIME_INVALID")
    return EmergencyRequest(
        body.operation_id,
        body.organization_id,
        body.account_id,
        body.factors,
        EmergencySnapshot(**body.expected.model_dump()),
        body.approval_ref,
        body.owner_ref,
        body.checked_at,
        body.approval_valid_until,
        body.supersedes,
    )
