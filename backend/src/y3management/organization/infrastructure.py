"""Only this module queries organization-owned tables."""

from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.organization.public import (
    AssignmentCandidate,
    Branch,
    BranchPage,
    ScopedBranchFact,
)


class Organization:
    def __init__(self, session: Session) -> None:
        self.s = session

    def create_initial(self, name: str) -> UUID:
        if self.s.execute(text("SELECT 1 FROM organization_organizations LIMIT 1")).first():
            raise Rejected(409, "already_installed")
        ident = uuid4()
        self.s.execute(
            text("INSERT INTO organization_organizations VALUES(:id,:name)"),
            {"id": ident, "name": name},
        )
        return ident

    def create_branch(self, organization_id: UUID, code: str, name: str) -> Branch:
        ident = uuid4()
        self.s.execute(
            text(
                "INSERT INTO organization_branches(id, organization_id, code, name) "
                "VALUES(:id, :org, :code, :name)"
            ),
            {"id": ident, "org": organization_id, "code": code, "name": name},
        )
        return Branch(ident, code, name)

    def require_branch(self, organization_id: UUID, branch_id: UUID) -> None:
        row = self.s.execute(
            text(
                "SELECT id FROM organization_branches WHERE organization_id=:o AND id=:b FOR SHARE"
            ),
            {"o": organization_id, "b": branch_id},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")

    def list_branches(
        self, organization_id: UUID, branch_id: UUID | None, offset: int, limit: int
    ) -> BranchPage:
        where = "organization_id=:org" + (" AND id=:branch" if branch_id else "")
        args = {"org": organization_id, "branch": branch_id, "offset": offset, "limit": limit}
        total = int(
            self.s.execute(
                text(f"SELECT count(*) FROM organization_branches WHERE {where}"), args
            ).scalar_one()
        )
        rows = self.s.execute(
            text(
                f"SELECT id,code,name FROM organization_branches WHERE {where} "
                "ORDER BY id OFFSET :offset LIMIT :limit"
            ),
            args,
        )
        return BranchPage(tuple(Branch(*row) for row in rows), total)

    def get_branch(self, organization_id: UUID, scope: UUID | None, branch_id: UUID) -> Branch:
        if scope is not None and scope != branch_id:
            raise Rejected(404, "not_found")
        row = self.s.execute(
            text(
                "SELECT id,code,name FROM organization_branches WHERE organization_id=:o AND id=:b"
            ),
            {"o": organization_id, "b": branch_id},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")
        return Branch(*row)

    def lock_scoped_branch(self, org: UUID, ident: UUID) -> ScopedBranchFact:
        row = self.s.execute(
            text(
                "SELECT organization_id, id, active, row_version FROM "
                "organization_branches WHERE organization_id=:o AND id=:i FOR SHARE"
            ),
            {"o": org, "i": ident},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")
        return ScopedBranchFact(*row)

    def assignment_candidates(
        self, org: UUID, branch: UUID | None, offset: int, limit: int
    ) -> tuple[AssignmentCandidate, ...]:
        rows = self.s.execute(
            text(
                "SELECT id, code, name, row_version FROM organization_branches WHERE "
                "organization_id=:o AND active AND (CAST(:b AS uuid) IS NULL OR id=:b) "
                "ORDER BY id OFFSET :off LIMIT :lim"
            ),
            {"o": org, "b": branch, "off": offset, "lim": limit},
        )
        return tuple(AssignmentCandidate(*row) for row in rows)
