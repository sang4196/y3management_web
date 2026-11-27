"""Private Pass persistence; no Member PII or IAM credential reads."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.iam.public import Caller
from y3management.pt_operations.public import (
    IssueCommand,
    IssuedPass,
    IssueResult,
    PassIssueEvent,
    Product,
    ProductValues,
)


class PassRepository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def operation(self, org: UUID, ident: UUID) -> tuple[IssueResult, UUID, bytes] | None:
        row = (
            self.s.execute(
                text("""SELECT p.*,o.actor_id AS original_actor,o.fingerprint,
          v.name AS product_name FROM pt_pass_issue_operations o JOIN pt_passes p
          ON (p.organization_id,p.id)=(o.organization_id,o.pass_id)
          JOIN pt_product_versions v ON (v.organization_id,v.product_id,v.version)=
            (p.organization_id,p.product_id,p.product_version)
          WHERE o.organization_id=:o AND o.operation_id=:i"""),
                {"o": org, "i": ident},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        record = IssuedPass(
            row["id"],
            row["member_id"],
            row["trainer_id"],
            row["product_id"],
            row["product_version"],
            ProductValues(
                row["product_name"],
                str(row["price_won"]),
                str(row["purchased_sessions"]),
                row["payment_type"],
                row["is_service"],
            ),
            row["issued_branch_id"],
            str(row["purchased_sessions"]),
            str(row["initial_remaining_sessions"]),
            row["issued_at"],
        )
        return IssueResult(ident, record), row["original_actor"], bytes(row["fingerprint"])

    def create(
        self,
        caller: Caller,
        c: IssueCommand,
        product: Product,
        role: str,
        branch: UUID | None,
        digest: bytes,
    ) -> tuple[IssueResult, PassIssueEvent]:
        ident = uuid4()
        clock = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        args = {
            "o": caller.organization_id,
            "id": ident,
            "op": c.operation_id,
            "actor": caller.account_id,
            "role": role,
            "actor_branch": branch,
            "branch": c.issued_branch_id,
            "bv": c.expected_branch_version,
            "member": c.member_id,
            "mv": c.expected_member_version,
            "trainer": c.trainer_id,
            "tv": c.expected_trainer_version,
            "product": c.product_id,
            "pv": c.expected_product_version,
            "price": Decimal(product.values.price_won),
            "count": int(product.values.session_count),
            "type": product.values.payment_type,
            "service": product.values.is_service,
            "clock": clock,
            "digest": digest,
        }
        self.s.execute(
            text("""INSERT INTO pt_passes(id,organization_id,source_operation_id,actor_id,
          issued_branch_id,branch_version,member_id,member_version,trainer_id,trainer_version,
          product_id,product_version,price_won,purchased_sessions,initial_remaining_sessions,payment_type,
          is_service,issued_at) VALUES(:id,:o,:op,:actor,:branch,:bv,:member,:mv,:trainer,:tv,
          :product,:pv,:price,:count,:count,:type,:service,:clock)"""),
            args,
        )
        self.s.execute(
            text("""INSERT INTO pt_pass_issue_operations(organization_id,operation_id,pass_id,
          actor_id,actor_role,actor_branch,issued_branch_id,expected_branch_version,member_id,
          expected_member_version,trainer_id,expected_trainer_version,product_id,expected_product_version,
          fingerprint,recorded_at) VALUES(:o,:op,:id,:actor,:role,:actor_branch,:branch,
          :bv,:member,:mv,
          :trainer,:tv,:product,:pv,:digest,:clock)"""),
            args,
        )
        row = self.operation(caller.organization_id, c.operation_id)
        assert row is not None
        return row[0], PassIssueEvent(
            caller.organization_id,
            c.operation_id,
            ident,
            c.member_id,
            c.trainer_id,
            c.issued_branch_id,
            caller.account_id,
            role,
            branch,
            clock,
        )

    def seal(self, org: UUID, result: IssueResult, clock: datetime) -> IssueResult:
        self.s.execute(
            text("UPDATE pt_passes SET issued_at=:t WHERE organization_id=:o AND id=:i"),
            {"o": org, "i": result.pass_record.id, "t": clock},
        )
        self.s.execute(
            text(
                "UPDATE pt_pass_issue_operations SET recorded_at=:t,validated_at=:t "
                "WHERE organization_id=:o AND operation_id=:i"
            ),
            {"o": org, "i": result.operation_id, "t": clock},
        )
        return replace(result, pass_record=replace(result.pass_record, issued_at=clock))
