"""Explicit continuation of a password case by another current Master."""

from dataclasses import asdict
from typing import Any
from uuid import UUID

from sqlalchemy import text

from y3management.contracts import Rejected
from y3management.iam.emergency import Emergency
from y3management.iam.public import Caller, EmergencyChange, HandoffRequest, HandoffState, Setup


class Handoff:
    def __init__(self, emergency: Emergency) -> None:
        self.e = emergency
        self.s = emergency.s
        self.iam = emergency.iam

    def case(self, caller: Caller, ident: UUID, operation: UUID) -> dict[str, Any]:
        self.iam.master_management(caller, ident)
        for table, legacy in (
            ("iam_password_emergency_cases", False),
            ("iam_emergency_cases", True),
        ):
            row = (
                self.s.execute(
                    text(
                        f"SELECT * FROM {table} WHERE id=:i AND account_id=:a "
                        "AND organization_id=:o"
                    ),
                    {"i": operation, "a": ident, "o": caller.organization_id},
                )
                .mappings()
                .first()
            )
            if row is not None:
                return {**row, "legacy": legacy}
        raise Rejected(404, "not_found")

    def latest(self, ident: UUID) -> UUID | None:
        return self.s.execute(
            text("""SELECT id FROM (
          SELECT id,row_version FROM iam_password_emergency_cases WHERE account_id=:a
          UNION ALL SELECT id,row_version FROM iam_emergency_cases WHERE account_id=:a
          ) c ORDER BY row_version DESC LIMIT 1"""),
            {"a": ident},
        ).scalar_one_or_none()

    def validate(self, caller: Caller, ident: UUID, operation: UUID) -> dict[str, Any]:
        c = self.case(caller, ident, operation)
        row = self.e.target(ident, caller.organization_id)
        if not c["legacy"]:
            self.e.lineage(operation)
        if c["completed_at"] is not None:
            raise Rejected(409, "case_completed")
        if self.latest(ident) != operation:
            raise Rejected(409, "case_superseded")
        operating = c["issuer_kind"] == "operating" if c["legacy"] else c["kind"] == "operating"
        if operating and c["expires_at"] > self.iam.now():
            raise Rejected(409, "handoff_not_due")
        if not row["password_reset_pending"] or row["password_hash"] is not None:
            raise Rejected(409, "insufficient_scope")
        if c["legacy"]:
            policy = self.iam.policy()
            transition = (
                self.s.execute(
                    text("""SELECT * FROM iam_policy_account_transitions
              WHERE transition_id=:p AND organization_id=:o AND account_id=:a
              AND legacy_parent_id=:c AND legacy_password_continuation_eligible"""),
                    {
                        "p": policy.transition_id,
                        "o": caller.organization_id,
                        "a": ident,
                        "c": operation,
                    },
                )
                .mappings()
                .first()
            )
            if transition is None:
                raise Rejected(409, "stale_snapshot")
            # The transition records P=B and the permitted B->A delta. Never rebase A.
            fields = (
                "row_version",
                "security_version",
                "reset_generation",
                "key_set_version",
                "recovery_generation",
                "state",
                "password_reset_pending",
                "recovery_pending",
            )
            grant = self.iam._account(ident)
            if (
                any(row[k] != transition["after_" + k] for k in fields)
                or (row["password_hash"] is not None) != transition["after_password_ready"]
                or not grant.master
                or transition["after_admin_scope"] != "ORGANIZATION"
                or grant.branch_id != transition["after_admin_branch"]
            ):
                raise Rejected(409, "stale_snapshot")
            self.e.legacy_lineage(c["id"], transition["legacy_origin_id"])
            c["transition"] = dict(transition)
        elif any(row[k] != c[k] for k in ("row_version", "security_version", "reset_generation")):
            raise Rejected(409, "stale_snapshot")
        return c

    def state(self, caller: Caller, ident: UUID, operation: UUID | None) -> HandoffState:
        self.iam.master_management(caller, ident)
        selected = operation or self.latest(ident)
        if selected is None:
            raise Rejected(404, "not_found")
        c = self.case(caller, ident, selected)
        if c["legacy"]:
            status = "completed" if c["completed_at"] else "retired"
            if self.latest(ident) != selected:
                status = "superseded"
            origin = c["approval_origin_case_id"]
            parent = c["supersedes"]
            issuer = "legacy_" + c["issuer_kind"]
        else:
            status = self.e.case_status(c)
            parent = c["parent_id"] or c["legacy_parent_id"]
            try:
                origin = self.e.lineage(selected)
            except Rejected:
                origin = None
            issuer = c["kind"]
        return HandoffState(
            selected,
            c["factors"] if c["legacy"] else "password",
            c["expires_at"],
            status,
            issuer,
            origin,
            parent,
            self.e.snapshot(self.e.target(ident, caller.organization_id)),
        )

    def issue(
        self, caller: Caller, ident: UUID, request: HandoffRequest, slot: UUID
    ) -> tuple[Setup, EmergencyChange]:
        # Service already holds installation, sorted actor/target accounts and sessions.
        c = self.validate(caller, ident, request.supersedes_case_id)
        before = self.e.target(ident, caller.organization_id)
        if request.expected != self.e.snapshot(before):
            raise Rejected(409, "stale_snapshot")
        if self.s.execute(
            text("SELECT 1 FROM iam_password_emergency_cases WHERE id=:i"),
            {"i": request.operation_id},
        ).first():
            raise Rejected(409, "execution_already_used")
        expiry = self.e.allocation(slot)
        self.e.revoke(ident)
        self.s.execute(
            text(
                "UPDATE iam_accounts SET row_version=row_version+1,"
                "security_version=security_version+1,reset_generation=reset_generation+1 WHERE "
                "id=:a"
            ),
            {"a": ident},
        )
        after = self.e.target(ident, caller.organization_id)
        case = self.e.case_values(
            request.operation_id, after, self.iam.now(), expiry, asdict(request)
        )
        case.update(issuer_account_id=caller.account_id, approval_mode="current_master")
        if c["legacy"]:
            t = c["transition"]
            case.update(
                kind="legacy_handoff",
                legacy_parent_id=c["id"],
                legacy_origin_id=t["legacy_origin_id"],
                legacy_origin_factors=t["legacy_factors"],
                legacy_parent_factors=t["legacy_factors"],
                policy_transition_id=t["transition_id"],
                continuation_eligible=True,
            )
        else:
            case.update(kind="handoff", parent_id=c["id"])
        setup = self.e.store(case, slot)
        return setup, self.e.event(before, after, case, "handoff", caller.account_id)

    def confirm(self, ident: UUID, operation: UUID, slot: UUID) -> None:
        source = self.e.source_id(slot)
        expiry = self.e.allocation(slot)
        if (
            source["account_id"] != ident
            or source["case_id"] != operation
            or source["expires_at"] != expiry
        ):
            raise Rejected(409, "expired_allocation")
