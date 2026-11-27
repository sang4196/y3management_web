"""Membership-owned SQL; transaction completion belongs to the outer UoW."""

from dataclasses import asdict
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.membership.public import (
    Member,
    MemberCommand,
    MemberMutation,
    MemberPage,
    MemberResult,
    MemberValues,
)


class Repository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def version(self, org: UUID, ident: UUID, version: int) -> Member:
        r = (
            self.s.execute(
                text("""SELECT * FROM membership_member_versions
          WHERE organization_id=:o AND member_id=:i AND version=:v"""),
                {"o": org, "i": ident, "v": version},
            )
            .mappings()
            .one()
        )
        return Member(
            ident,
            r["version"],
            MemberValues(r["name"], r["phone"]),
            r["home_branch_id"],
            r["active"],
            r["recorded_at"],
        )

    def home(self, org: UUID, ident: UUID) -> UUID:
        home = self.s.execute(
            text("""SELECT v.home_branch_id FROM membership_members m
          JOIN membership_member_versions v ON (v.organization_id,v.member_id,v.version)=
          (m.organization_id,m.id,m.current_version) WHERE m.organization_id=:o AND m.id=:i"""),
            {"o": org, "i": ident},
        ).scalar_one_or_none()
        if home is None:
            raise Rejected(404, "not_found")
        return UUID(str(home))

    def get(self, org: UUID, ident: UUID) -> Member:
        version = self.s.execute(
            text("""SELECT current_version FROM membership_members
          WHERE organization_id=:o AND id=:i FOR UPDATE"""),
            {"o": org, "i": ident},
        ).scalar_one_or_none()
        if version is None:
            raise Rejected(404, "not_found")
        return self.version(org, ident, version)

    def list(self, caller: Caller, offset: int, limit: int) -> MemberPage:
        args = {
            "o": caller.organization_id,
            "master": caller.master,
            "ba": caller.branch_id,
            "op": caller.operator.branch_id if caller.operator else None,
            "off": offset,
            "lim": limit,
        }
        source = """FROM membership_members m JOIN membership_member_versions v
          ON (v.organization_id,v.member_id,v.version)=(m.organization_id,m.id,m.current_version)
          WHERE m.organization_id=:o AND (:master OR v.home_branch_id=CAST(:ba AS uuid)
            OR v.home_branch_id=CAST(:op AS uuid))"""
        total = self.s.execute(text("SELECT count(*) " + source), args).scalar_one()
        rows = self.s.execute(
            text(
                "SELECT m.id,m.current_version "
                + source
                + " ORDER BY m.created_at,m.id OFFSET :off LIMIT :lim"
            ),
            args,
        ).all()
        return MemberPage(
            tuple(self.version(caller.organization_id, r.id, r.current_version) for r in rows),
            total,
        )

    def operation(self, org: UUID, ident: UUID) -> tuple[MemberResult, UUID, bytes] | None:
        r = (
            self.s.execute(
                text("""SELECT * FROM membership_member_operations
          WHERE organization_id=:o AND operation_id=:i"""),
                {"o": org, "i": ident},
            )
            .mappings()
            .first()
        )
        if r is None:
            return None
        return (
            MemberResult(
                ident,
                r["kind"],
                r["changed"],
                self.version(org, r["member_id"], r["after_version"]),
                self.version(
                    org,
                    r["member_id"],
                    self.s.execute(
                        text("""SELECT current_version
              FROM membership_members WHERE organization_id=:o AND id=:i"""),
                        {"o": org, "i": r["member_id"]},
                    ).scalar_one(),
                ),
            ),
            r["actor_id"],
            bytes(r["fingerprint"]),
        )

    def prepare(
        self,
        caller: Caller,
        c: MemberCommand,
        before: Member | None,
        home: UUID,
        active: bool,
        actor_role: str,
        actor_branch: UUID | None,
        changed: bool,
        fingerprint: bytes,
    ) -> tuple[MemberResult, MemberMutation | None]:
        org = caller.organization_id
        ident = before.id if before else uuid4()
        version = before.version + int(changed) if before else 1
        recorded = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        mutation = MemberMutation(
            org,
            c.operation_id,
            ident,
            caller.account_id,
            actor_role,
            actor_branch,
            home,
            c.kind,
            before.version if before else None,
            version,
            changed,
            recorded,
        )
        args = asdict(mutation)
        self.s.execute(
            text("""INSERT INTO membership_member_operations
          (organization_id,operation_id,member_id,actor_id,actor_role,actor_branch,home_branch_id,
          kind,before_version,after_version,changed,recorded_at,canonical_version,fingerprint)
          VALUES(:organization_id,:operation_id,:member_id,:actor_id,:actor_role,:actor_branch,
          :home_branch_id,:kind,:before_version,:after_version,:changed,:recorded_at,1,:fingerprint)"""),
            {**args, "fingerprint": fingerprint},
        )
        if changed:
            values = c.values if c.values is not None else before.values if before else None
            assert values is not None
            self.s.execute(
                text("""INSERT INTO membership_member_versions
              (organization_id,member_id,version,name,phone,home_branch_id,active,source_operation_id,
              actor_id,kind,before_version,before_active,before_home_branch_id,recorded_at,changed)
              VALUES(:organization_id,:member_id,:after_version,:name,:phone,:home_branch_id,:active,
              :operation_id,:actor_id,:kind,:before_version,:before_active,:before_home,:recorded_at,true)"""),
                {
                    **args,
                    **asdict(values),
                    "active": active,
                    "before_active": before.active if before else None,
                    "before_home": before.home_branch_id if before else None,
                },
            )
            if before is None:
                self.s.execute(
                    text("""INSERT INTO membership_members
                  (id,organization_id,current_version,created_at) VALUES(:i,:o,1,:t)"""),
                    {"i": ident, "o": org, "t": recorded},
                )
            else:
                self.s.execute(
                    text("""UPDATE membership_members SET current_version=:v
                  WHERE organization_id=:o AND id=:i"""),
                    {"o": org, "i": ident, "v": version},
                )
        current = self.get(org, ident)
        return MemberResult(
            c.operation_id, c.kind, changed, current, current
        ), mutation if changed else None

    def seal(self, org: UUID, operation: UUID, clock: datetime) -> None:
        self.s.execute(
            text("""UPDATE membership_member_operations SET validated_at=:t
          WHERE organization_id=:o AND operation_id=:i AND validated_at IS NULL"""),
            {"o": org, "i": operation, "t": clock},
        )

    def issue_search(
        self, org: UUID, query: str, offset: int, limit: int
    ) -> tuple[tuple[UUID, ...], int]:
        # strpos is a literal substring; %, _ and backslash never become wildcards.
        phone = query.replace(" ", "").replace("-", "")
        if phone.startswith("+82"):
            phone = "0" + phone[3:]
        base = """FROM membership_members m JOIN membership_member_versions v
          ON (v.organization_id,v.member_id,v.version)=(m.organization_id,m.id,m.current_version)
          WHERE m.organization_id=:o AND v.active AND
            (strpos(lower(v.name),lower(:q))>0 OR strpos(v.phone,:phone)>0)"""
        args = {"o": org, "q": query, "phone": phone or query, "off": offset, "lim": limit}
        total = int(self.s.execute(text("SELECT count(*) " + base), args).scalar_one())
        rows = self.s.execute(
            text("SELECT m.id " + base + " ORDER BY m.created_at,m.id OFFSET :off LIMIT :lim"), args
        )
        return tuple(rows.scalars()), total
