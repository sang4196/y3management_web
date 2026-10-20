"""Atomic audit writer; never accepts arbitrary event payloads."""

from dataclasses import asdict
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from y3management.audit.public import Event
from y3management.contracts import Rejected


class Audit:
    def __init__(self, session: Session) -> None:
        self.s = session
        self.request_id = uuid4()

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
               emergency_case_id,emergency_factors,executor_ref,approval_mode)
              VALUES (:id,:organization_id,:actor_id,:target_id,:action,:success,:before_state,
                      :after_state,:before_branch,:after_branch,:actor_role,:actor_scope,:actor_branch,
                      :before_version,:after_version,:branch_code,:branch_name,:request_id,
                      :before_login_id,:after_login_id,:key_id,:before_key_set_version,:after_key_set_version,
                      :before_recovery_generation,:after_recovery_generation,
                      :before_reset_generation,:after_reset_generation,:before_password_ready,:after_password_ready,
                      :emergency_case_id,:emergency_factors,:executor_ref,:approval_mode)"""),
                {"id": uuid4(), "request_id": self.request_id, **asdict(event)},
            )
        except SQLAlchemyError:
            raise Rejected(503, "unavailable") from None
