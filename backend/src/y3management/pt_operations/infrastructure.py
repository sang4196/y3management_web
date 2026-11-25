"""Catalog private SQL; transaction completion belongs to Application UoW."""

from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.pt_operations.public import (
    CatalogCommand,
    CatalogMutation,
    CatalogResult,
    Product,
    ProductPage,
    ProductValues,
)


class Repository:
    def __init__(self, session: Session) -> None:
        self.s = session

    def version(self, org: UUID, ident: UUID, version: int) -> Product:
        r = (
            self.s.execute(
                text("""SELECT * FROM pt_product_versions
          WHERE organization_id=:o AND product_id=:i AND version=:v"""),
                {"o": org, "i": ident, "v": version},
            )
            .mappings()
            .one()
        )
        return Product(
            ident,
            r["version"],
            ProductValues(
                r["name"],
                str(r["price_won"]),
                str(r["session_count"]),
                r["payment_type"],
                r["is_service"],
            ),
            r["selling"],
            r["recorded_at"],
        )

    def get(self, org: UUID, ident: UUID) -> Product:
        version = self.s.execute(
            text("""SELECT current_version FROM pt_products
          WHERE organization_id=:o AND id=:i FOR UPDATE"""),
            {"o": org, "i": ident},
        ).scalar_one_or_none()
        if version is None:
            raise Rejected(404, "not_found")
        return self.version(org, ident, version)

    def list(self, org: UUID, offset: int, limit: int) -> ProductPage:
        total = self.s.execute(
            text("SELECT count(*) FROM pt_products WHERE organization_id=:o"), {"o": org}
        ).scalar_one()
        rows = self.s.execute(
            text("""SELECT id,current_version FROM pt_products
          WHERE organization_id=:o ORDER BY created_at,id OFFSET :off LIMIT :lim"""),
            {"o": org, "off": offset, "lim": limit},
        ).all()
        return ProductPage(tuple(self.version(org, r.id, r.current_version) for r in rows), total)

    def operation(self, org: UUID, ident: UUID) -> tuple[CatalogResult, UUID, bytes] | None:
        r = (
            self.s.execute(
                text("""SELECT * FROM pt_product_operations
          WHERE organization_id=:o AND operation_id=:i"""),
                {"o": org, "i": ident},
            )
            .mappings()
            .first()
        )
        if r is None:
            return None
        result = CatalogResult(
            ident,
            r["kind"],
            r["changed"],
            self.version(org, r["product_id"], r["after_version"]),
            self.get(org, r["product_id"]),
        )
        return result, r["actor_id"], bytes(r["fingerprint"])

    def prepare(
        self,
        caller: Caller,
        c: CatalogCommand,
        before: Product | None,
        changed: bool,
        fingerprint: bytes,
    ) -> tuple[CatalogResult, CatalogMutation | None]:
        org = caller.organization_id
        ident = before.id if before else uuid4()
        revision = (before.version + int(changed)) if before else 1
        recorded = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        mutation = CatalogMutation(
            org,
            c.operation_id,
            ident,
            caller.account_id,
            "MASTER",
            None,
            c.kind,
            before.version if before else None,
            revision,
            changed,
            recorded,
        )
        args = asdict(mutation)
        self.s.execute(
            text("""INSERT INTO pt_product_operations
          (organization_id,operation_id,product_id,actor_id,actor_role,actor_branch,kind,
           before_version,after_version,changed,recorded_at,canonical_version,fingerprint)
          VALUES(:organization_id,:operation_id,:product_id,:actor_id,:actor_role,:actor_branch,
          :kind,:before_version,:after_version,:changed,:recorded_at,1,:fingerprint)"""),
            {**args, "fingerprint": fingerprint},
        )
        if changed:
            values = c.values if c.values is not None else before.values if before else None
            assert values is not None
            selling = (before.selling if before else True) if c.kind != "stop" else False
            self.s.execute(
                text("""INSERT INTO pt_product_versions
              (organization_id,product_id,version,name,price_won,session_count,payment_type,
               is_service,selling,source_operation_id,actor_id,kind,before_version,before_selling,
               recorded_at,changed)
              VALUES(:organization_id,:product_id,:after_version,:name,:price,:count,:payment_type,
              :is_service,:selling,:operation_id,:actor_id,:kind,:before_version,:before_selling,
              :recorded_at,true)"""),
                {
                    **args,
                    **asdict(values),
                    "price": Decimal(values.price_won),
                    "count": int(values.session_count),
                    "selling": selling,
                    "before_selling": before.selling if before else None,
                },
            )
            if before is None:
                self.s.execute(
                    text("""INSERT INTO pt_products(id,organization_id,current_version,created_at)
                 VALUES(:i,:o,1,:t)"""),
                    {"i": ident, "o": org, "t": recorded},
                )
            else:
                self.s.execute(
                    text("""UPDATE pt_products SET current_version=:v
                 WHERE organization_id=:o AND id=:i"""),
                    {"o": org, "i": ident, "v": revision},
                )
        current = self.get(org, ident)
        return CatalogResult(
            c.operation_id, c.kind, changed, current, current
        ), mutation if changed else None

    def seal(self, org: UUID, operation: UUID, clock: datetime) -> None:
        self.s.execute(
            text("""UPDATE pt_product_operations SET validated_at=:t
          WHERE organization_id=:o AND operation_id=:i AND validated_at IS NULL"""),
            {"o": org, "i": operation, "t": clock},
        )
