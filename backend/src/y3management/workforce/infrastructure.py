"""Only Workforce-owned SQL; shared transaction provided by composition."""

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.workforce.public import (
    ManagedTrainer,
    RegisterTrainer,
    TrainerIdentityFact,
    TrainerPage,
)
from y3management.workforce.validation import month


class Repository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def identity(self, org: UUID, ident: UUID, *, lock: bool = False) -> TrainerIdentityFact:
        row = self.s.execute(
            text(
                "SELECT id, organization_id, home_branch_id, active, row_version FROM "
                "workforce_trainers WHERE organization_id=:o AND id=:i"
                + (" FOR UPDATE" if lock else "")
            ),
            {"o": org, "i": ident},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")
        return TrainerIdentityFact(*row)

    def operation(
        self, org: UUID, operation: UUID, *, lock: bool = False
    ) -> tuple[UUID, bytes] | None:
        row = self.s.execute(
            text(
                "SELECT trainer_id, fingerprint FROM workforce_registration_operations "
                "WHERE organization_id=:o AND operation_id=:i" + (" FOR UPDATE" if lock else "")
            ),
            {"o": org, "i": operation},
        ).first()
        return (row[0], bytes(row[1])) if row else None

    def get(self, org: UUID, ident: UUID) -> ManagedTrainer:
        row = self.s.execute(
            text(
                "SELECT id, name, home_branch_id, active, row_version FROM "
                "workforce_trainers WHERE organization_id=:o AND id=:i"
            ),
            {"o": org, "i": ident},
        ).one()
        return ManagedTrainer(*row)

    def list(self, org: UUID, branch: UUID | None, offset: int, limit: int) -> TrainerPage:
        where = "organization_id=:o AND (CAST(:b AS uuid) IS NULL OR home_branch_id=:b)"
        args = {"o": org, "b": branch, "off": offset, "lim": limit}
        total = int(
            self.s.execute(
                text("SELECT count(*) FROM workforce_trainers WHERE " + where), args
            ).scalar_one()
        )
        rows = self.s.execute(
            text(
                "SELECT id,name,home_branch_id,active,row_version FROM workforce_trainers WHERE "
                + where
                + " ORDER BY id OFFSET :off LIMIT :lim"
            ),
            args,
        )
        return TrainerPage(tuple(ManagedTrainer(*row) for row in rows), total)

    def create(
        self, org: UUID, actor: UUID, c: RegisterTrainer, fingerprint: bytes
    ) -> ManagedTrainer:
        ident = uuid4()
        args = {
            "i": ident,
            "o": org,
            "b": c.home_branch_id,
            "name": c.name,
            "phone": c.phone,
            "rate": c.rate_percent,
            "fixed": Decimal(c.fixed_amount_won),
            "base": Decimal(c.base_salary_won),
            "month": month(c.base_salary_start_month),
            "op": c.operation_id,
            "actor": actor,
            "fp": fingerprint,
        }
        self.s.execute(
            text(
                "INSERT INTO workforce_trainers(id, organization_id, home_branch_id, "
                "name, phone, active, row_version, rate_percent, fixed_amount_won, "
                "base_salary_won, base_salary_start_month) VALUES(:i, :o, :b, :name, "
                ":phone, true, 1, :rate, :fixed, :base, :month)"
            ),
            args,
        )
        self.s.execute(
            text(
                "INSERT INTO workforce_initial_snapshots(trainer_id, organization_id, "
                "home_branch_id, rate_percent, fixed_amount_won, base_salary_won, "
                "base_salary_start_month, version, created_at) SELECT id, "
                "organization_id, home_branch_id, rate_percent, fixed_amount_won, "
                "base_salary_won, base_salary_start_month, 1, created_at FROM "
                "workforce_trainers WHERE id=:i"
            ),
            args,
        )
        self.s.execute(
            text(
                "INSERT INTO workforce_registration_operations(organization_id, "
                "operation_id, trainer_id, creator_account_id, canonical_version, "
                "fingerprint) VALUES(:o, :op, :i, :actor, 1, :fp)"
            ),
            args,
        )
        return self.get(org, ident)
