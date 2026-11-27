"""State history is separate from the original Pass and never changes its balance/relations."""

from dataclasses import replace
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.pt_operations.public import (
    PassState,
    PassStateCommand,
    PassStateEvent,
    PassStatePage,
    PassStateResult,
)


class StateRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def initialize(self, org: UUID, ident: UUID) -> None:
        self.s.execute(
            text("""INSERT INTO pt_pass_state_versions(organization_id,pass_id,version,
          manual_expired,kind,recorded_at,origin_issued_at)
          SELECT organization_id,id,1,false,'issued',issued_at,issued_at FROM pt_passes
          WHERE organization_id=:o AND id=:i"""),
            {"o": org, "i": ident},
        )
        self.s.execute(
            text(
                "INSERT INTO pt_pass_state_heads(organization_id,pass_id,current_version) "
                "VALUES(:o,:i,1)"
            ),
            {"o": org, "i": ident},
        )

    def branch(self, org: UUID, ident: UUID) -> UUID:
        branch = self.s.execute(
            text("SELECT issued_branch_id FROM pt_passes WHERE organization_id=:o AND id=:i"),
            {"o": org, "i": ident},
        ).scalar_one_or_none()
        if branch is None:
            raise Rejected(404, "not_found")
        return UUID(str(branch))

    def version(self, org: UUID, ident: UUID, version: int) -> PassState:
        r = self.s.execute(
            text("""SELECT p.id,p.member_id,v.name,p.issued_branch_id,
          p.initial_remaining_sessions,s.version,s.manual_expired,s.recorded_at
          FROM pt_pass_state_versions s JOIN pt_passes p ON
          (p.organization_id,p.id)=(s.organization_id,s.pass_id)
          JOIN pt_product_versions v ON (v.organization_id,v.product_id,v.version)=
          (p.organization_id,p.product_id,p.product_version)
          WHERE s.organization_id=:o AND s.pass_id=:i AND s.version=:v"""),
            {"o": org, "i": ident, "v": version},
        ).one()
        return PassState(r[0], r[1], r[2], r[3], str(r[4]), r[5], r[6], r[7])

    def get(self, org: UUID, ident: UUID) -> PassState:
        version = self.s.execute(
            text(
                "SELECT current_version FROM pt_pass_state_heads "
                "WHERE organization_id=:o AND pass_id=:i FOR UPDATE"
            ),
            {"o": org, "i": ident},
        ).scalar_one_or_none()
        if version is None:
            raise Rejected(404, "not_found")
        return self.version(org, ident, version)

    def list(self, caller: Caller, offset: int, limit: int) -> PassStatePage:
        args = {
            "o": caller.organization_id,
            "master": caller.master,
            "b": caller.branch_id,
            "off": offset,
            "lim": limit,
        }
        base = (
            "FROM pt_passes WHERE organization_id=:o "
            "AND (:master OR issued_branch_id=CAST(:b AS uuid))"
        )
        total = int(self.s.execute(text("SELECT count(*) " + base), args).scalar_one())
        ids = self.s.execute(
            text("SELECT id " + base + " ORDER BY issued_at,id OFFSET :off LIMIT :lim"), args
        ).scalars()
        return PassStatePage(tuple(self.get(caller.organization_id, i) for i in ids), total)

    def operation(self, org: UUID, ident: UUID) -> tuple[PassStateResult, UUID, bytes] | None:
        r = (
            self.s.execute(
                text(
                    "SELECT * FROM pt_pass_state_operations WHERE "
                    "organization_id=:o AND operation_id=:i"
                ),
                {"o": org, "i": ident},
            )
            .mappings()
            .first()
        )
        if r is None:
            return None
        committed = self.version(org, r["pass_id"], r["after_version"])
        return (
            PassStateResult(ident, r["changed"], committed, self.get(org, r["pass_id"])),
            r["actor_id"],
            bytes(r["fingerprint"]),
        )

    def prepare(
        self,
        caller: Caller,
        c: PassStateCommand,
        before: PassState,
        role: str,
        branch: UUID | None,
        changed: bool,
        digest: bytes,
    ) -> tuple[PassStateResult, PassStateEvent | None]:
        clock = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        if clock < before.recorded_at:
            raise Rejected(409, "clock_conflict")
        args = {
            "o": caller.organization_id,
            "i": c.pass_id,
            "op": c.operation_id,
            "actor": caller.account_id,
            "role": role,
            "branch": branch,
            "issued": before.issued_branch_id,
            "kind": "expire" if c.desired_expired else "release",
            "reason": c.reason,
            "bv": before.version,
            "av": before.version + int(changed),
            "be": before.manual_expired,
            "ae": c.desired_expired,
            "bt": before.recorded_at,
            "at": clock if changed else before.recorded_at,
            "t": clock,
            "changed": changed,
            "digest": digest,
        }
        if changed:
            self.s.execute(
                text("""INSERT INTO pt_pass_state_versions(organization_id,pass_id,version,
              manual_expired,kind,source_operation_id,before_version,before_expired,before_recorded_at,
              recorded_at) VALUES(:o,:i,:av,:ae,:kind,:op,:bv,:be,:bt,:at)"""),
                args,
            )
            self.s.execute(
                text(
                    "UPDATE pt_pass_state_heads SET current_version=:av WHERE "
                    "organization_id=:o AND pass_id=:i"
                ),
                args,
            )
        self.s.execute(
            text("""INSERT INTO pt_pass_state_operations(organization_id,operation_id,pass_id,
          issued_branch_id,actor_id,actor_role,actor_branch,kind,reason,before_version,after_version,
          before_expired,after_expired,before_recorded_at,after_recorded_at,recorded_at,changed,fingerprint)
          VALUES(:o,:op,:i,:issued,:actor,:role,:branch,:kind,:reason,:bv,:av,:be,:ae,:bt,:at,:t,:changed,:digest)"""),
            args,
        )
        current = self.get(caller.organization_id, c.pass_id)
        result = PassStateResult(c.operation_id, changed, current, current)
        event = PassStateEvent(
            caller.organization_id,
            c.operation_id,
            c.pass_id,
            before.issued_branch_id,
            caller.account_id,
            role,
            branch,
            args["kind"],
            c.reason,
            before.version,
            current.version,
            before.manual_expired,
            c.desired_expired,
            before.recorded_at,
            clock,
        )
        return result, event if changed else None

    def seal(self, org: UUID, result: PassStateResult, clock: datetime) -> PassStateResult:
        args = {
            "o": org,
            "op": result.operation_id,
            "i": result.committed_state.pass_id,
            "v": result.committed_state.version,
            "t": clock,
        }
        if result.changed:
            before_time = self.s.execute(
                text(
                    "SELECT before_recorded_at FROM pt_pass_state_operations "
                    "WHERE organization_id=:o AND operation_id=:op"
                ),
                args,
            ).scalar_one()
            if clock < before_time:
                raise Rejected(409, "clock_conflict")
            self.s.execute(
                text(
                    "UPDATE pt_pass_state_versions SET recorded_at=:t WHERE "
                    "organization_id=:o AND pass_id=:i AND version=:v"
                ),
                args,
            )
            self.s.execute(
                text(
                    "UPDATE pt_pass_state_operations SET "
                    "recorded_at=:t,after_recorded_at=:t,validated_at=:t WHERE "
                    "organization_id=:o AND operation_id=:op"
                ),
                args,
            )
            state = replace(result.committed_state, recorded_at=clock)
            return replace(result, committed_state=state, current_state=state)
        self.s.execute(
            text(
                "UPDATE pt_pass_state_operations SET validated_at=:t WHERE "
                "organization_id=:o AND operation_id=:op"
            ),
            args,
        )
        return result
