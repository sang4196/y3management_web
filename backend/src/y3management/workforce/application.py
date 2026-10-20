"""Current Home authority and initial registration/replay policy."""

from uuid import UUID

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.organization.public import ScopedBranchFact
from y3management.workforce.infrastructure import Repository
from y3management.workforce.public import (
    ManagedTrainer,
    RegisterTrainer,
    RegistrationResult,
    TrainerIdentityFact,
    TrainerPage,
)
from y3management.workforce.validation import fingerprint, normalize


class Workforce:
    def __init__(self, repository: Repository) -> None:
        self.repo = repository

    def normalize(self, command: RegisterTrainer) -> RegisterTrainer:
        return normalize(command)

    def _scope(self, caller: Caller, home: UUID, org: UUID) -> None:
        if not caller.master and caller.branch_id is None:
            raise Rejected(403, "forbidden")
        if caller.organization_id != org or (not caller.master and caller.branch_id != home):
            raise Rejected(404, "not_found")

    def identity(self, organization_id: UUID, ident: UUID) -> TrainerIdentityFact:
        return self.repo.identity(organization_id, ident)

    def hint(self, caller: Caller, operation: UUID) -> TrainerIdentityFact | None:
        row = self.repo.operation(caller.organization_id, operation)
        return self.identity(caller.organization_id, row[0]) if row else None

    def get(self, caller: Caller, ident: UUID) -> ManagedTrainer:
        fact = self.repo.identity(caller.organization_id, ident, lock=True)
        self._scope(caller, fact.home_branch_id, fact.organization_id)
        return self.repo.get(caller.organization_id, ident)

    def list(self, caller: Caller, offset: int, limit: int) -> TrainerPage:
        if not caller.master and caller.branch_id is None:
            raise Rejected(403, "forbidden")
        if offset < 0 or not 1 <= limit <= 100:
            raise Rejected(422, "invalid_request")
        return self.repo.list(
            caller.organization_id, None if caller.master else caller.branch_id, offset, limit
        )

    def register(
        self, caller: Caller, branch: ScopedBranchFact, command: RegisterTrainer
    ) -> RegistrationResult:
        c = normalize(command)
        existing = self.repo.operation(caller.organization_id, c.operation_id, lock=True)
        if existing:
            trainer = self.get(caller, existing[0])
            if (
                trainer.home_branch_id != branch.branch_id
                or branch.organization_id != caller.organization_id
            ):
                raise Rejected(409, "conflict")
            if existing[1] != fingerprint(c):
                raise Rejected(409, "operation_conflict")
            return RegistrationResult(c.operation_id, trainer, False)
        self._scope(caller, branch.branch_id, branch.organization_id)  # profile registration
        self._scope(caller, c.home_branch_id, branch.organization_id)  # initial compensation
        if c.home_branch_id != branch.branch_id or not branch.active:
            raise Rejected(409, "branch_inactive")
        trainer = self.repo.create(caller.organization_id, caller.account_id, c, fingerprint(c))
        return RegistrationResult(c.operation_id, trainer, True)

    def confirm(self, caller: Caller, result: RegistrationResult) -> None:
        if self.get(caller, result.trainer.id) != result.trainer:
            raise Rejected(409, "conflict")
