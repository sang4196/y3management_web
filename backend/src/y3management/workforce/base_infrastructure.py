"""Workforce-owned Base plan SQL, using the composition transaction only."""

from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.workforce.public import (
    BaseCommand,
    BaseFact,
    BaseMutation,
    BaseQuery,
    BaseResult,
    BaseSnapshot,
    PreparedBase,
    TrainerIdentityFact,
)
from y3management.workforce.validation import month


def ym(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


class BaseRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def register(self, org: UUID, trainer: UUID, operation: UUID) -> None:
        self.s.execute(
            text("""INSERT INTO workforce_base_ledgers
            (organization_id,trainer_id,ledger_version,registration_operation_id)
            VALUES(:o,:t,1,:op)"""),
            {"o": org, "t": trainer, "op": operation},
        )

    def identity(self, org: UUID, trainer: UUID) -> TrainerIdentityFact:
        row = self.s.execute(
            text("""SELECT id,organization_id,home_branch_id,active,row_version
            FROM workforce_trainers WHERE organization_id=:o AND id=:t FOR SHARE"""),
            {"o": org, "t": trainer},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")
        return TrainerIdentityFact(*row)

    def ledger(self, org: UUID, trainer: UUID) -> int:
        value = self.s.execute(
            text("""SELECT ledger_version FROM workforce_base_ledgers
            WHERE organization_id=:o AND trainer_id=:t FOR SHARE"""),
            {"o": org, "t": trainer},
        ).scalar_one_or_none()
        if value is None:
            raise Rejected(503, "unavailable")
        return int(value)

    def anchor(self, org: UUID, trainer: UUID) -> BaseFact:
        row = self.s.execute(
            text("""SELECT s.base_salary_won,s.base_salary_start_month
            FROM workforce_initial_snapshots s JOIN workforce_base_ledgers l
              ON l.organization_id=s.organization_id AND l.trainer_id=s.trainer_id
            WHERE s.organization_id=:o AND s.trainer_id=:t"""),
            {"o": org, "t": trainer},
        ).first()
        if row is None:
            raise Rejected(503, "unavailable")
        return BaseFact(trainer, ym(row[1]), str(row[0]), 1, True, True, False)

    def change(self, org: UUID, trainer: UUID, change: UUID) -> BaseFact:
        row = self.s.execute(
            text("""SELECT id,start_month,planned_amount,revision,active
            FROM workforce_base_changes WHERE organization_id=:o AND trainer_id=:t AND id=:c"""),
            {"o": org, "t": trainer, "c": change},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")
        return BaseFact(row[0], ym(row[1]), str(row[2]), row[3], row[4])

    def snapshot(
        self, org: UUID, trainer: UUID, query: BaseQuery
    ) -> tuple[BaseSnapshot, TrainerIdentityFact]:
        fact = self.identity(org, trainer)
        version = self.ledger(org, trainer)
        anchor = self.anchor(org, trainer)
        args = {
            "o": org,
            "t": trainer,
            "m": month(query.basis_month),
            "off": query.offset,
            "lim": query.limit,
        }
        total = int(
            self.s.execute(
                text(
                    "SELECT count(*) FROM workforce_base_changes "
                    "WHERE organization_id=:o AND trainer_id=:t"
                ),
                args,
            ).scalar_one()
        )
        rows = self.s.execute(
            text("""SELECT id,start_month,planned_amount,revision,active
            FROM workforce_base_changes WHERE organization_id=:o AND trainer_id=:t
            ORDER BY start_month,id OFFSET :off LIMIT :lim"""),
            args,
        )
        items = tuple(BaseFact(r[0], ym(r[1]), str(r[2]), r[3], r[4]) for r in rows)
        projected = self.s.execute(
            text("""SELECT id,start_month,planned_amount,revision,active
            FROM workforce_base_changes WHERE organization_id=:o AND trainer_id=:t
              AND active AND start_month<=:m ORDER BY start_month DESC LIMIT 1"""),
            args,
        ).first()
        projection = (
            BaseFact(projected[0], ym(projected[1]), str(projected[2]), projected[3], projected[4])
            if projected
            else (anchor if anchor.start_month <= query.basis_month else None)
        )
        return BaseSnapshot(
            trainer, fact.home_branch_id, fact.version, version, anchor, projection, items, total
        ), fact

    def operation_target(self, org: UUID, operation: UUID) -> UUID | None:
        return self.s.execute(
            text(
                "SELECT trainer_id FROM workforce_base_operations "
                "WHERE organization_id=:o AND operation_id=:op"
            ),
            {"o": org, "op": operation},
        ).scalar_one_or_none()

    def operation(self, org: UUID, operation: UUID) -> tuple[BaseResult, UUID, bytes] | None:
        row = (
            self.s.execute(
                text(
                    "SELECT * FROM workforce_base_operations "
                    "WHERE organization_id=:o AND operation_id=:op"
                ),
                {"o": org, "op": operation},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        self.identity(org, row["trainer_id"])
        committed = BaseFact(
            row["change_id"],
            ym(row["start_month"]),
            str(row["after_amount"]),
            row["after_revision"],
            row["after_active"],
        )
        result = BaseResult(
            operation,
            row["trainer_id"],
            row["kind"],
            row["changed"],
            committed,
            row["after_ledger_version"],
            row["recorded_at"],
            row["validated_at"],
            ym(row["business_month"]),
            self.ledger(org, row["trainer_id"]),
            self.change(org, row["trainer_id"], row["change_id"]),
        )
        return result, row["actor_id"], bytes(row["fingerprint"])

    def prepare(
        self, caller: Caller, fact: TrainerIdentityFact, request: BaseCommand, digest: bytes
    ) -> PreparedBase:
        org, trainer = fact.organization_id, fact.trainer_id
        version = self.ledger(org, trainer)
        if (
            version != request.expected_base_ledger_version
            or fact.version != request.expected_trainer_version
        ):
            raise Rejected(409, "conflict")
        anchor = self.anchor(org, trainer)
        now = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        current_month = now.astimezone(ZoneInfo("Asia/Seoul")).date().replace(day=1)
        old = None
        if request.kind == "create":
            assert request.start_month is not None and request.planned_amount_won is not None
            start = month(request.start_month)
            assert request.planned_amount_won is not None
            amount: str | None = request.planned_amount_won
            ident = uuid4()
            revision = 1
            if start < month(anchor.start_month):
                raise Rejected(409, "before_initial_anchor")
        else:
            assert request.change_id is not None
            if request.change_id == trainer:
                raise Rejected(409, "initial_anchor_immutable")
            old = self.change(org, trainer, request.change_id)
            if not old.active or old.revision != request.expected_change_revision:
                raise Rejected(409, "conflict")
            ident = old.change_id
            start = month(old.start_month)
            amount = (
                old.planned_amount_won if request.kind == "cancel" else request.planned_amount_won
            )
            assert amount is not None
            revision = old.revision + int(
                request.kind == "cancel" or amount != old.planned_amount_won
            )
        assert amount is not None
        if start <= current_month:
            raise Rejected(409, "schedule_no_longer_future")
        changed = old is None or request.kind == "cancel" or amount != old.planned_amount_won
        active = request.kind != "cancel"
        m = BaseMutation(
            org,
            request.operation_id,
            trainer,
            caller.account_id,
            "MASTER" if caller.master else "BRANCH_ADMIN",
            None if caller.master else caller.branch_id,
            fact.home_branch_id,
            request.kind,
            ident,
            start,
            old.planned_amount_won if old else None,
            amount,
            old.active if old else None,
            active,
            old.revision if old else None,
            revision,
            version,
            version + int(changed),
            changed,
            now,
        )
        args = {**asdict(m), "after_amount": Decimal(amount)}
        if old is None:
            self.s.execute(
                text("""INSERT INTO workforce_base_changes
                (organization_id,trainer_id,id,start_month,planned_amount,revision,active)
                VALUES(:organization_id,:trainer_id,:change_id,:start_month,:after_amount,
                       :after_revision,:after_active)"""),
                args,
            )
        elif changed:
            self.s.execute(
                text("""UPDATE workforce_base_changes SET planned_amount=:after_amount,
                revision=:after_revision,active=:after_active WHERE organization_id=:organization_id
                AND trainer_id=:trainer_id AND id=:change_id"""),
                args,
            )
        if changed:
            self.s.execute(
                text("""UPDATE workforce_base_ledgers SET ledger_version=:after_ledger_version
                WHERE organization_id=:organization_id AND trainer_id=:trainer_id"""),
                args,
            )
        return PreparedBase(m, digest, fact.version)

    def seal(self, prepared: PreparedBase, clock: datetime, business_month: str) -> BaseResult:
        m = prepared.mutation
        columns = tuple(asdict(m))
        args = {
            **asdict(m),
            "before_amount": Decimal(m.before_amount) if m.before_amount is not None else None,
            "after_amount": Decimal(m.after_amount),
            "fp": prepared.fingerprint,
            "tv": prepared.expected_trainer_version,
            "validated": clock,
            "month": month(business_month),
        }
        self.s.execute(
            text(
                "INSERT INTO workforce_base_operations ("
                + ",".join(columns)
                + ",canonical_version,fingerprint,expected_trainer_version,"
                + "validated_at,business_month)"
                + " VALUES ("
                + ",".join(":" + c for c in columns)
                + ",1,:fp,:tv,:validated,:month)"
            ),
            args,
        )
        current = BaseFact(
            m.change_id, ym(m.start_month), m.after_amount, m.after_revision, m.after_active
        )
        return BaseResult(
            m.operation_id,
            m.trainer_id,
            m.kind,
            m.changed,
            current,
            m.after_ledger_version,
            m.recorded_at,
            clock,
            business_month,
            m.after_ledger_version,
            current,
        )
