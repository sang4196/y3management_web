"""Existing-case continuation by a real current normal Master."""

import secrets
from dataclasses import asdict, replace
from typing import Any
from uuid import UUID

from sqlalchemy import text

from y3management.contracts import Rejected
from y3management.iam.emergency import Emergency
from y3management.iam.infrastructure import digest
from y3management.iam.public import (
    Caller,
    EmergencyChange,
    HandoffRequest,
    HandoffState,
    Setup,
)


class Handoff:
    def __init__(self, emergency: Emergency) -> None:
        self.e = emergency
        self.s = emergency.s
        self.iam = emergency.iam

    def case(self, caller: Caller, ident: UUID, operation: UUID) -> dict[str, Any]:
        self.iam.master_management(caller, ident)
        row = (
            self.s.execute(
                text(
                    "SELECT * FROM iam_emergency_cases WHERE id=:id AND account_id=:a "
                    "AND organization_id=:o"
                ),
                {"id": operation, "a": ident, "o": caller.organization_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            raise Rejected(404, "not_found")
        return dict(row)

    def latest(self, ident: UUID) -> UUID | None:
        return self.s.execute(
            text(
                "SELECT id FROM iam_emergency_cases WHERE account_id=:a "
                "ORDER BY row_version DESC LIMIT 1"
            ),
            {"a": ident},
        ).scalar_one_or_none()

    def validate(self, caller: Caller, ident: UUID, operation: UUID) -> dict[str, Any]:
        c = self.case(caller, ident, operation)
        row = self.e.target(ident, caller.organization_id)
        if c["completed_at"] is not None:
            raise Rejected(409, "case_completed")
        if self.latest(ident) != operation:
            raise Rejected(409, "case_superseded")
        if c["issuer_kind"] == "operating":
            if c["expires_at"] > self.iam.now():
                raise Rejected(409, "handoff_not_due")
        else:
            origin = self.case(caller, ident, c["approval_origin_case_id"])
            parent = self.case(caller, ident, c["supersedes"])
            if (
                origin["issuer_kind"] != "operating"
                or origin["factors"] != c["factors"]
                or parent["factors"] != c["factors"]
                or not origin["row_version"] <= parent["row_version"] < c["row_version"]
                or (parent["issuer_kind"] == "operating" and parent["id"] != origin["id"])
                or (
                    parent["issuer_kind"] == "master_handoff"
                    and parent["approval_origin_case_id"] != origin["id"]
                )
            ):
                raise Rejected(409, "invalid_lineage")
        if any(
            row[k] != c[k]
            for k in (
                "row_version",
                "security_version",
                "key_set_version",
                "reset_generation",
                "recovery_generation",
            )
        ):
            raise Rejected(409, "stale_snapshot")
        snap = self.e.snapshot(row)
        password = c["factors"] in ("password", "both")
        key = c["factors"] in ("passkey", "both")
        if (
            snap.password_reset_pending != password
            or snap.password_ready == password
            or snap.recovery_pending != key
            or snap.key_ready == key
        ):
            raise Rejected(409, "insufficient_scope")
        return c

    def state(self, caller: Caller, ident: UUID, operation: UUID | None) -> HandoffState:
        self.iam.master_management(caller, ident)
        selected = operation if operation is not None else self.latest(ident)
        if selected is None:
            raise Rejected(404, "not_found")
        c = self.case(caller, ident, selected)
        status = "issued"
        if c["completed_at"] is not None:
            status = "completed"
        elif self.latest(ident) != selected:
            status = "superseded"
        elif c["expires_at"] <= self.iam.now():
            status = "expired"
        else:
            source = self.s.execute(
                text("SELECT id FROM iam_emergency_credentials WHERE case_id=:c"), {"c": selected}
            ).scalar_one_or_none()
            try:
                if source is None:
                    raise Rejected(401, "invalid_recovery")
                self.e.mfa.emergency_source(source)
            except Rejected:
                status = "stale"
        return HandoffState(
            selected,
            c["factors"],
            c["expires_at"],
            status,
            c["issuer_kind"],
            c["approval_origin_case_id"],
            c["supersedes"],
            self.e.snapshot(self.e.mfa.account(ident, lock=False)),
        )

    def issue(
        self, caller: Caller, ident: UUID, request: HandoffRequest, slot: UUID
    ) -> tuple[Setup, EmergencyChange]:
        # Service holds Installation and both Accounts/Sessions before entering here.
        self.s.execute(
            text("SELECT key_id FROM iam_passkeys WHERE account_id=:a ORDER BY key_id FOR UPDATE"),
            {"a": ident},
        ).all()
        c = self.validate(caller, ident, request.supersedes_case_id)
        before = self.e.mfa.account(ident, lock=False)
        if request.expected != self.e.snapshot(before):
            raise Rejected(409, "stale_snapshot")
        if self.s.execute(
            text("SELECT 1 FROM iam_emergency_cases WHERE id=:i"), {"i": request.operation_id}
        ).first():
            raise Rejected(409, "execution_already_used")
        expiry = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:i AND kind='emergency'"),
            {"i": slot},
        ).scalar_one()
        now = self.iam.now()
        if expiry <= now:
            raise Rejected(409, "expired_allocation")
        self.e.revoke(ident)
        changes = ["row_version=row_version+1", "security_version=security_version+1"]
        if c["factors"] in ("password", "both"):
            changes += ["reset_generation=reset_generation+1"]
        if c["factors"] in ("passkey", "both"):
            changes += [
                "recovery_generation=recovery_generation+1",
                "key_set_version=key_set_version+1",
            ]
        self.s.execute(
            text("UPDATE iam_accounts SET " + ",".join(changes) + " WHERE id=:i"), {"i": ident}
        )
        after = self.e.mfa.account(ident, lock=False)
        origin = c["id"] if c["issuer_kind"] == "operating" else c["approval_origin_case_id"]
        values = {
            "id": request.operation_id,
            "organization_id": caller.organization_id,
            "account_id": ident,
            "factors": c["factors"],
            "issued_at": now,
            "expires_at": expiry,
            "supersedes": c["id"],
            "handoff_parent_id": c["id"],
            "issuer_kind": "master_handoff",
            "issuer_account_id": caller.account_id,
            "approval_mode": "current_master",
            "approval_origin_case_id": origin,
            **{
                k: after[k]
                for k in (
                    "row_version",
                    "security_version",
                    "key_set_version",
                    "reset_generation",
                    "recovery_generation",
                )
            },
            **{"expected_" + k: v for k, v in asdict(request.expected).items()},
        }
        self.s.execute(
            text(
                "INSERT INTO iam_emergency_cases ("
                + ",".join(values)
                + ") VALUES ("
                + ",".join(":" + k for k in values)
                + ")"
            ),
            values,
        )
        raw = secrets.token_urlsafe(32)
        self.s.execute(
            text(
                "INSERT INTO iam_emergency_credentials "
                "(id,case_id,account_id,factors,digest,expires_at) "
                "VALUES(:id,:c,:a,:f,:d,:e)"
            ),
            {
                "id": slot,
                "c": request.operation_id,
                "a": ident,
                "f": c["factors"],
                "d": digest(raw),
                "e": expiry,
            },
        )
        change = replace(
            self.e.event(before, after, request.operation_id, c["factors"], None, issue=True),
            action="emergency_handoff",
            actor_id=caller.account_id,
            actor_role="MASTER",
            actor_scope="ORGANIZATION",
            approval_mode="current_master",
            approval_origin_case_id=origin,
            previous_case_id=c["id"],
            handoff_kind="takeover" if c["issuer_kind"] == "operating" else "reissue",
        )
        return Setup(raw, expiry), change

    def confirm(self, ident: UUID, operation: UUID, slot: UUID) -> None:
        source = self.e.mfa.emergency_source(slot)
        lease = self.s.execute(
            text("SELECT expires_at FROM iam_security_states WHERE id=:s AND kind='emergency'"),
            {"s": slot},
        ).scalar_one_or_none()
        if (
            source["account_id"] != ident
            or source["case_id"] != operation
            or lease is None
            or lease <= self.iam.now()
        ):
            raise Rejected(409, "expired_allocation")
