"""Atomic audit writer; never accepts arbitrary event payloads."""

from dataclasses import asdict
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from y3management.audit.public import (
    BaseHistoryItem,
    BaseHistoryPage,
    BaseScheduleEvent,
    CompensationEvent,
    CompensationHistoryItem,
    CompensationHistoryPage,
    Event,
    InitialCompensationSet,
    OperatorAccountEvent,
    OperatorRoleEvent,
    PasswordEmergencyEvent,
    TrainerHomeEvent,
    TrainerIdentityEvent,
    TrainerRegistered,
    TrainerRoleEvent,
    TrainerStateEvent,
)
from y3management.contracts import Rejected


class Audit:
    def __init__(self, session: Session) -> None:
        self.s = session
        self.request_id = uuid4()

    def append_password_emergency(self, event: PasswordEmergencyEvent) -> None:
        values = {"id": uuid4(), **asdict(event)}
        self.s.execute(
            text(
                "INSERT INTO audit_password_emergency_events ("
                + ",".join(values)
                + ") VALUES ("
                + ",".join(":" + k for k in values)
                + ")"
            ),
            values,
        )

    def append_operator_role(self, event: OperatorRoleEvent) -> None:
        values = asdict(event)
        self.s.execute(
            text(
                "INSERT INTO audit_operator_role_events ("
                + ",".join(values)
                + ") VALUES ("
                + ",".join(":" + k for k in values)
                + ")"
            ),
            values,
        )

    def append_operator(self, event: OperatorAccountEvent) -> None:
        columns = tuple(asdict(event))
        self.s.execute(
            text(
                "INSERT INTO audit_operator_account_events(id,"
                + ",".join(columns)
                + ") VALUES(:id,"
                + ",".join(":" + k for k in columns)
                + ")"
            ),
            {"id": uuid4(), **asdict(event)},
        )

    def append_trainer_identity(self, event: TrainerIdentityEvent) -> None:
        columns = tuple(asdict(event))
        self.s.execute(
            text(
                "INSERT INTO audit_trainer_identity_events(id,"
                + ",".join(columns)
                + ") VALUES(:id,"
                + ",".join(":" + k for k in columns)
                + ")"
            ),
            {"id": uuid4(), **asdict(event)},
        )

    def append_trainer_state(self, event: TrainerStateEvent) -> None:
        columns = tuple(asdict(event))
        self.s.execute(
            text(
                "INSERT INTO audit_trainer_state_events(id,"
                + ",".join(columns)
                + ") VALUES(:id,"
                + ",".join(":" + k for k in columns)
                + ")"
            ),
            {"id": uuid4(), **asdict(event)},
        )

    def append_trainer_role(self, event: TrainerRoleEvent) -> None:
        columns = tuple(asdict(event))
        self.s.execute(
            text(
                "INSERT INTO audit_trainer_role_events(id,"
                + ",".join(columns)
                + ") VALUES(:id,"
                + ",".join(":" + k for k in columns)
                + ")"
            ),
            {"id": uuid4(), **asdict(event)},
        )

    def append(self, event: Event) -> None:
        try:
            self.s.execute(
                text("""INSERT INTO audit_events
              (id,organization_id,actor_id,target_id,action,success,before_state,after_state,
               before_branch,after_branch,actor_role,actor_scope,actor_branch,before_version,
               after_version,branch_code,branch_name,request_id,before_login_id,after_login_id,
               key_id,before_key_set_version,after_key_set_version,
               before_recovery_generation,after_recovery_generation,
               before_reset_generation,after_reset_generation,before_password_ready,after_password_ready,
               emergency_case_id,emergency_factors,executor_ref,approval_mode,approval_origin_case_id,previous_case_id,handoff_kind)
              VALUES (:id,:organization_id,:actor_id,:target_id,:action,:success,:before_state,
                      :after_state,:before_branch,:after_branch,:actor_role,:actor_scope,:actor_branch,
                      :before_version,:after_version,:branch_code,:branch_name,:request_id,
                      :before_login_id,:after_login_id,:key_id,:before_key_set_version,:after_key_set_version,
                      :before_recovery_generation,:after_recovery_generation,
                      :before_reset_generation,:after_reset_generation,:before_password_ready,:after_password_ready,
                      :emergency_case_id,:emergency_factors,:executor_ref,:approval_mode,:approval_origin_case_id,:previous_case_id,:handoff_kind)"""),
                {"id": uuid4(), "request_id": self.request_id, **asdict(event)},
            )
        except SQLAlchemyError:
            raise Rejected(503, "unavailable") from None

    def append_trainer_registered(self, event: TrainerRegistered) -> None:
        self._workforce(event, None)

    def append_initial_compensation(self, event: InitialCompensationSet) -> None:
        self._workforce(event.registration, event)

    def _workforce(self, event: TrainerRegistered, values: InitialCompensationSet | None) -> None:
        from datetime import date
        from decimal import Decimal

        args = {
            **asdict(event),
            "id": uuid4(),
            "kind": "initial_compensation" if values else "trainer_registered",
            "rate": values.rate if values else None,
            "fixed": Decimal(values.fixed) if values else None,
            "base": Decimal(values.base) if values else None,
            "month": date.fromisoformat(values.month + "-01") if values else None,
        }
        self.s.execute(
            text(
                "INSERT INTO audit_workforce_initial_events(id, organization_id, "
                "operation_id, trainer_id, actor_id, actor_role, actor_branch, "
                "target_home, version, event_kind, after_rate, after_fixed, after_base, "
                "after_month) VALUES(:id, :organization_id, :operation_id, :trainer_id, "
                ":actor_id, :actor_role, :actor_branch, :target_home, 1, :kind, :rate, "
                ":fixed, :base, :month)"
            ),
            args,
        )

    def append_trainer_home(self, event: TrainerHomeEvent) -> None:
        columns = tuple(asdict(event))
        self.s.execute(
            text(
                "INSERT INTO audit_trainer_home_events(id,"
                + ",".join(columns)
                + ") VALUES(:id,"
                + ",".join(":" + k for k in columns)
                + ")"
            ),
            {"id": uuid4(), **asdict(event)},
        )

    def append_compensation(self, event: CompensationEvent) -> None:
        args = {"id": uuid4(), **asdict(event)}
        args["before_fixed"] = Decimal(event.before_fixed)
        args["after_fixed"] = Decimal(event.after_fixed)
        columns = tuple(asdict(event))
        self.s.execute(
            text(
                "INSERT INTO audit_compensation_events(id,"
                + ",".join(columns)
                + ") VALUES(:id,"
                + ",".join(":" + k for k in columns)
                + ")"
            ),
            args,
        )

    def compensation_history(
        self, organization: UUID, trainer: UUID, offset: int, limit: int
    ) -> CompensationHistoryPage:
        query = """SELECT version AS compensation_version,operation_id,actor_id,actor_role,
            actor_branch,target_home,before_rate,after_rate,before_fixed,after_fixed,
            after_base AS initial_base_salary_won,
            after_month AS initial_base_salary_start_month,created_at AS recorded_at
            FROM audit_workforce_initial_events WHERE organization_id=:o AND trainer_id=:t
              AND event_kind='initial_compensation'
            UNION ALL
            SELECT after_version,operation_id,actor_id,actor_role,actor_branch,target_home,
              before_rate,after_rate,before_fixed,after_fixed,NULL::numeric,NULL::date,recorded_at
            FROM audit_compensation_events WHERE organization_id=:o AND trainer_id=:t"""
        args = {"o": organization, "t": trainer, "off": offset, "lim": limit}
        total = int(
            self.s.execute(text("SELECT count(*) FROM (" + query + ") h"), args).scalar_one()
        )
        rows = self.s.execute(
            text(
                "SELECT * FROM (" + query + ") h ORDER BY compensation_version "
                "OFFSET :off LIMIT :lim"
            ),
            args,
        )
        items = []
        for row in rows:
            month = row.initial_base_salary_start_month
            items.append(
                CompensationHistoryItem(
                    row.compensation_version,
                    row.operation_id,
                    row.actor_id,
                    row.actor_role,
                    row.actor_branch,
                    row.target_home,
                    row.before_rate,
                    row.after_rate,
                    str(row.before_fixed) if row.before_fixed is not None else None,
                    str(row.after_fixed),
                    str(row.initial_base_salary_won)
                    if row.initial_base_salary_won is not None
                    else None,
                    f"{month.year:04d}-{month.month:02d}" if month is not None else None,
                    row.recorded_at,
                )
            )
        return CompensationHistoryPage(tuple(items), total)

    def append_base_schedule(self, event: BaseScheduleEvent) -> None:
        args = {"id": uuid4(), **asdict(event)}
        args["before_amount"] = (
            Decimal(event.before_amount) if event.before_amount is not None else None
        )
        args["after_amount"] = Decimal(event.after_amount)
        columns = tuple(asdict(event))
        self.s.execute(
            text(
                "INSERT INTO audit_base_schedule_events(id,"
                + ",".join(columns)
                + ") VALUES(:id,"
                + ",".join(":" + c for c in columns)
                + ")"
            ),
            args,
        )

    def base_schedule_history(
        self, organization: UUID, trainer: UUID, offset: int, limit: int
    ) -> BaseHistoryPage:
        query = """SELECT 1::bigint AS ledger_version,'initial' AS kind,trainer_id AS change_id,
            after_month AS start_month,NULL::numeric AS before_amount,after_base AS planned_amount,
            true AS active,1::bigint AS revision,actor_id,actor_role,actor_branch,target_home,
            created_at AS recorded_at FROM audit_workforce_initial_events
            WHERE organization_id=:o AND trainer_id=:t AND event_kind='initial_compensation'
            UNION ALL SELECT after_ledger_version,kind,change_id,start_month,before_amount,
              after_amount,after_active,after_revision,actor_id,actor_role,actor_branch,target_home,
              recorded_at FROM audit_base_schedule_events
              WHERE organization_id=:o AND trainer_id=:t"""
        args = {"o": organization, "t": trainer, "off": offset, "lim": limit}
        total = int(
            self.s.execute(text("SELECT count(*) FROM (" + query + ") h"), args).scalar_one()
        )
        rows = self.s.execute(
            text("SELECT * FROM (" + query + ") h ORDER BY ledger_version OFFSET :off LIMIT :lim"),
            args,
        )
        items = tuple(
            BaseHistoryItem(
                r.ledger_version,
                r.kind,
                r.change_id,
                f"{r.start_month.year:04d}-{r.start_month.month:02d}",
                str(r.before_amount) if r.before_amount is not None else None,
                str(r.planned_amount),
                r.active,
                r.revision,
                r.actor_id,
                r.actor_role,
                r.actor_branch,
                r.target_home,
                r.recorded_at,
            )
            for r in rows
        )
        return BaseHistoryPage(items, total)
