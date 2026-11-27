"""Only Workforce-owned SQL; shared transaction provided by composition."""

from dataclasses import asdict
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.workforce.base_infrastructure import BaseRepository
from y3management.workforce.public import (
    CompensationChange,
    CompensationRequest,
    CompensationResult,
    CompensationState,
    IssueTrainer,
    IssueTrainerPage,
    ManagedTrainer,
    RegisterTrainer,
    TrainerHomeChange,
    TrainerHomeRequest,
    TrainerHomeResult,
    TrainerIdentityFact,
    TrainerPage,
    TrainerStateChange,
    TrainerStateRequest,
    TrainerStateResult,
)
from y3management.workforce.validation import month


class Repository:
    def __init__(self, session: Session) -> None:
        self.s = session
        self.base = BaseRepository(session)

    def identity(
        self, org: UUID, ident: UUID, *, lock: bool = False, shared: bool = False
    ) -> TrainerIdentityFact:
        row = self.s.execute(
            text(
                "SELECT id, organization_id, home_branch_id, active, row_version FROM "
                "workforce_trainers WHERE organization_id=:o AND id=:i"
                + (" FOR UPDATE" if lock else (" FOR SHARE" if shared else ""))
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
        self.s.execute(
            text(
                "INSERT INTO workforce_trainer_state_origins "
                "(trainer_id,organization_id,origin,active,trainer_version,recorded_at,"
                "registration_operation_id) SELECT id,organization_id,'registered',active,"
                "row_version,created_at,:op FROM workforce_trainers WHERE id=:i"
            ),
            args,
        )
        self.s.execute(
            text("""INSERT INTO workforce_trainer_home_origins
            (trainer_id,organization_id,origin,home_branch_id,trainer_version,recorded_at,
             registration_operation_id) SELECT id,organization_id,'registered',home_branch_id,
             row_version,created_at,:op FROM workforce_trainers WHERE id=:i"""),
            args,
        )
        self.base.register(org, ident, c.operation_id)
        return self.get(org, ident)

    def state_operation(
        self,
        org: UUID,
        operation: UUID,
    ) -> tuple[TrainerStateResult, bytes] | None:
        row = self.s.execute(
            text(
                "SELECT trainer_id,changed,committed_active,committed_trainer_version,fingerprint "
                "FROM workforce_trainer_state_operations "
                "WHERE organization_id=:o AND operation_id=:i"
            ),
            {"o": org, "i": operation},
        ).first()
        if row is None:
            return None
        return (
            TrainerStateResult(
                operation,
                row.trainer_id,
                row.changed,
                row.committed_active,
                row.committed_trainer_version,
                self.identity(org, row.trainer_id),
            ),
            bytes(row.fingerprint),
        )

    def change_state(
        self,
        actor: UUID,
        fact: TrainerIdentityFact,
        request: TrainerStateRequest,
        fingerprint: bytes,
    ) -> tuple[TrainerStateResult, TrainerStateChange | None]:
        changed = fact.active != request.desired_active
        now = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        change = TrainerStateChange(
            fact.organization_id,
            request.operation_id,
            fact.trainer_id,
            fact.active,
            request.desired_active,
            fact.version,
            fact.version + int(changed),
            now,
        )
        args = {
            **asdict(change),
            "actor": actor,
            "home": fact.home_branch_id,
            "fp": fingerprint,
            "changed": changed,
        }
        if changed:
            self.s.execute(
                text(
                    "UPDATE workforce_trainers SET active=:after_active, "
                    "row_version=:after_version WHERE organization_id=:organization_id "
                    "AND id=:trainer_id"
                ),
                args,
            )
        self.s.execute(
            text(
                "INSERT INTO workforce_trainer_state_operations "
                "(organization_id,operation_id,trainer_id,actor_id,target_home,canonical_version,"
                "fingerprint,desired_active,expected_trainer_version,before_active,before_version,"
                "committed_active,committed_trainer_version,changed,recorded_at) VALUES "
                "(:organization_id,:operation_id,:trainer_id,:actor,:home,1,:fp,:after_active,"
                ":before_version,:before_active,:before_version,:after_active,:after_version,"
                ":changed,:recorded_at)"
            ),
            args,
        )
        if changed:
            columns = tuple(asdict(change))
            self.s.execute(
                text(
                    "INSERT INTO workforce_trainer_state_transitions ("
                    + ",".join(columns)
                    + ") VALUES ("
                    + ",".join(":" + k for k in columns)
                    + ")"
                ),
                asdict(change),
            )
        return TrainerStateResult(
            request.operation_id,
            fact.trainer_id,
            changed,
            request.desired_active,
            change.after_version,
            self.identity(fact.organization_id, fact.trainer_id),
        ), change if changed else None

    def home_operation(
        self, org: UUID, operation: UUID
    ) -> tuple[TrainerHomeResult, bytes, UUID] | None:
        row = self.s.execute(
            text("""SELECT trainer_id,changed,before_home_branch_id,
            after_home_branch_id,before_version,after_version,recorded_at,fingerprint,actor_id
            FROM workforce_trainer_home_operations
            WHERE organization_id=:o AND operation_id=:i"""),
            {"o": org, "i": operation},
        ).first()
        if row is None:
            return None
        return (
            TrainerHomeResult(
                operation,
                row.trainer_id,
                row.changed,
                row.before_home_branch_id,
                row.after_home_branch_id,
                row.before_version,
                row.after_version,
                row.recorded_at,
                self.identity(org, row.trainer_id),
            ),
            bytes(row.fingerprint),
            row.actor_id,
        )

    def change_home(
        self,
        actor: UUID,
        fact: TrainerIdentityFact,
        request: TrainerHomeRequest,
        fingerprint: bytes,
    ) -> tuple[TrainerHomeResult, TrainerHomeChange | None]:
        changed = fact.home_branch_id != request.destination_home_branch_id
        now = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        change = TrainerHomeChange(
            fact.organization_id,
            request.operation_id,
            fact.trainer_id,
            actor,
            fact.home_branch_id,
            request.destination_home_branch_id,
            fact.version,
            fact.version + int(changed),
            now,
        )
        args = {**asdict(change), "fp": fingerprint, "changed": changed}
        if changed:
            self.s.execute(
                text("""UPDATE workforce_trainers
                SET home_branch_id=:after_home_branch_id,row_version=:after_version
                WHERE organization_id=:organization_id AND id=:trainer_id"""),
                args,
            )
        self.s.execute(
            text("""INSERT INTO workforce_trainer_home_operations
            (organization_id,operation_id,trainer_id,actor_id,canonical_version,fingerprint,
             before_home_branch_id,after_home_branch_id,expected_trainer_version,
             before_version,after_version,changed,recorded_at)
            VALUES (:organization_id,:operation_id,:trainer_id,:actor_id,1,:fp,
             :before_home_branch_id,:after_home_branch_id,:before_version,
             :before_version,:after_version,:changed,:recorded_at)"""),
            args,
        )
        if changed:
            columns = tuple(asdict(change))
            self.s.execute(
                text(
                    "INSERT INTO workforce_trainer_home_transitions ("
                    + ",".join(columns)
                    + ") VALUES ("
                    + ",".join(":" + k for k in columns)
                    + ")"
                ),
                asdict(change),
            )
        return TrainerHomeResult(
            request.operation_id,
            fact.trainer_id,
            changed,
            fact.home_branch_id,
            request.destination_home_branch_id,
            fact.version,
            change.after_version,
            now,
            self.identity(fact.organization_id, fact.trainer_id),
        ), (change if changed else None)

    def compensation(self, org: UUID, trainer: UUID) -> CompensationState:
        row = self.s.execute(
            text("""SELECT t.id,t.home_branch_id,t.row_version,t.rate_percent,
            t.fixed_amount_won,t.compensation_version,s.base_salary_won,s.base_salary_start_month
            FROM workforce_trainers t JOIN workforce_initial_snapshots s
            ON s.organization_id=t.organization_id AND s.trainer_id=t.id
            WHERE t.organization_id=:o AND t.id=:i
              AND t.base_salary_won=s.base_salary_won
              AND t.base_salary_start_month=s.base_salary_start_month"""),
            {"o": org, "i": trainer},
        ).first()
        if row is None:
            raise Rejected(503, "unavailable")
        return CompensationState(
            row[0],
            row[1],
            row[2],
            row[3],
            str(row[4]),
            row[5],
            str(row[6]),
            f"{row[7].year:04d}-{row[7].month:02d}",
        )

    def compensation_operation(
        self, org: UUID, operation: UUID
    ) -> tuple[CompensationResult, bytes, UUID] | None:
        row = self.s.execute(
            text("""SELECT trainer_id,changed,before_rate,before_fixed,
            before_version,after_rate,after_fixed,after_version,recorded_at,fingerprint,actor_id
            FROM workforce_compensation_operations
            WHERE organization_id=:o AND operation_id=:i"""),
            {"o": org, "i": operation},
        ).first()
        if row is None:
            return None
        return (
            CompensationResult(
                operation,
                row.trainer_id,
                row.changed,
                row.before_rate,
                str(row.before_fixed),
                row.before_version,
                row.after_rate,
                str(row.after_fixed),
                row.after_version,
                row.recorded_at,
                self.compensation(org, row.trainer_id),
            ),
            bytes(row.fingerprint),
            row.actor_id,
        )

    def change_compensation(
        self,
        caller: Caller,
        fact: TrainerIdentityFact,
        current: CompensationState,
        request: CompensationRequest,
        fingerprint: bytes,
    ) -> tuple[CompensationResult, CompensationChange | None]:
        changed = (
            request.rate_percent != current.rate_percent
            or request.fixed_amount_won != current.fixed_amount_won
        )
        now = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        change = CompensationChange(
            fact.organization_id,
            request.operation_id,
            fact.trainer_id,
            caller.account_id,
            "MASTER" if caller.master else "BRANCH_ADMIN",
            None if caller.master else caller.branch_id,
            fact.home_branch_id,
            current.rate_percent,
            request.rate_percent,
            current.fixed_amount_won,
            request.fixed_amount_won,
            current.compensation_version,
            current.compensation_version + int(changed),
            now,
        )
        args = {
            **asdict(change),
            "fp": fingerprint,
            "changed": changed,
            "trainer_version": fact.version,
        }
        args["before_fixed"] = Decimal(change.before_fixed)
        args["after_fixed"] = Decimal(change.after_fixed)
        if changed:
            self.s.execute(
                text("""UPDATE workforce_trainers SET rate_percent=:after_rate,
                fixed_amount_won=:after_fixed,compensation_version=:after_version
                WHERE organization_id=:organization_id AND id=:trainer_id"""),
                args,
            )
        self.s.execute(
            text("""INSERT INTO workforce_compensation_operations
            (organization_id,operation_id,trainer_id,actor_id,actor_role,actor_branch,target_home,
             canonical_version,fingerprint,expected_trainer_version,expected_compensation_version,
             before_rate,after_rate,before_fixed,after_fixed,before_version,after_version,
             changed,recorded_at) VALUES (:organization_id,:operation_id,:trainer_id,:actor_id,
             :actor_role,:actor_branch,:target_home,1,:fp,:trainer_version,:before_version,
             :before_rate,:after_rate,:before_fixed,:after_fixed,:before_version,:after_version,
             :changed,:recorded_at)"""),
            args,
        )
        return CompensationResult(
            request.operation_id,
            fact.trainer_id,
            changed,
            change.before_rate,
            change.before_fixed,
            change.before_version,
            change.after_rate,
            change.after_fixed,
            change.after_version,
            now,
            self.compensation(fact.organization_id, fact.trainer_id),
        ), (change if changed else None)

    def issue_trainers(self, org: UUID, offset: int, limit: int) -> IssueTrainerPage:
        args = {"o": org, "off": offset, "lim": limit}
        total = int(
            self.s.execute(
                text("SELECT count(*) FROM workforce_trainers WHERE organization_id=:o AND active"),
                args,
            ).scalar_one()
        )
        rows = self.s.execute(
            text(
                "SELECT id,name,home_branch_id,row_version FROM workforce_trainers "
                "WHERE organization_id=:o AND active ORDER BY id OFFSET :off LIMIT :lim"
            ),
            args,
        )
        return IssueTrainerPage(tuple(IssueTrainer(*r) for r in rows), total)
