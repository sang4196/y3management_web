"""Public Organization use cases enforce caller authority even without HTTP."""

from uuid import UUID

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.organization.infrastructure import Organization as Repository
from y3management.organization.public import Branch, BranchPage


class Organization:
    def __init__(self, repository: Repository) -> None:
        self._repo = repository

    def create_initial(self, name: str) -> UUID:
        # Installation command only; application holds IAM's exclusive installation gate.
        return self._repo.create_initial(name)

    def _master(self, caller: Caller) -> None:
        if not caller.master:
            raise Rejected(403, "forbidden")

    def _scope(self, caller: Caller) -> UUID | None:
        if not caller.master and caller.branch_id is None:
            raise Rejected(403, "forbidden")
        return None if caller.master else caller.branch_id

    def create_branch(self, caller: Caller, code: str, name: str) -> Branch:
        self._master(caller)
        return self._repo.create_branch(caller.organization_id, code, name)

    def require_branch(self, caller: Caller, branch_id: UUID) -> None:
        self._master(caller)
        self._repo.require_branch(caller.organization_id, branch_id)

    def list_branches(self, caller: Caller, offset: int, limit: int) -> BranchPage:
        if offset < 0 or not 1 <= limit <= 100:
            raise Rejected(422, "invalid_request")
        return self._repo.list_branches(caller.organization_id, self._scope(caller), offset, limit)

    def get_branch(self, caller: Caller, branch_id: UUID) -> Branch:
        return self._repo.get_branch(caller.organization_id, self._scope(caller), branch_id)
