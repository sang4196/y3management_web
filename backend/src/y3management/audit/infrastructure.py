"""Atomic audit writer; never accepts arbitrary event payloads."""

from dataclasses import asdict
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from y3management.audit.public import (
    Event,
    InitialCompensationSet,
    TrainerIdentityEvent,
    TrainerRegistered,
    TrainerRoleEvent,
)
from y3management.contracts import Rejected


class Audit:
    def __init__(self, session: Session) -> None:
        self.s = session
        self.request_id = uuid4()

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
