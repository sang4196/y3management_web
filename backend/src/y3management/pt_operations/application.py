"""Catalog policy: exact values, current Master and Actor-bound CAS/replay."""

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, replace
from datetime import datetime
from uuid import UUID

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.pt_operations.infrastructure import Repository
from y3management.pt_operations.public import (
    CatalogCommand,
    CatalogMutation,
    CatalogResult,
    Product,
    ProductPage,
    ProductValues,
)


def normalize(values: ProductValues) -> ProductValues:
    if (
        not isinstance(values.name, str)
        or not values.name.strip()
        or len(values.name) > 200
        or any(unicodedata.category(c) in {"Cc", "Cs"} for c in values.name)
        or not isinstance(values.price_won, str)
        or re.fullmatch(r"(?:0|[1-9][0-9]{0,1023})", values.price_won) is None
        or not isinstance(values.session_count, str)
        or re.fullmatch(r"[1-9][0-9]{0,18}", values.session_count) is None
        or int(values.session_count) > 9223372036854775807
        or values.payment_type not in {"RATE", "FIXED_AMOUNT"}
        or type(values.is_service) is not bool
        or (values.is_service and values.payment_type != "FIXED_AMOUNT")
    ):
        raise Rejected(422, "invalid_request")
    return replace(values, name=values.name.strip())


class Catalog:
    def __init__(self, repository: Repository) -> None:
        self.repo = repository

    def _master(self, caller: Caller) -> None:
        if not caller.master:
            raise Rejected(403, "forbidden")

    def get(self, caller: Caller, ident: UUID) -> Product:
        self._master(caller)
        return self.repo.get(caller.organization_id, ident)

    def list(self, caller: Caller, offset: int, limit: int) -> ProductPage:
        self._master(caller)
        if offset < 0 or not 1 <= limit <= 100:
            raise Rejected(422, "invalid_request")
        return self.repo.list(caller.organization_id, offset, limit)

    def operation(self, caller: Caller, ident: UUID) -> CatalogResult:
        self._master(caller)
        row = self.repo.operation(caller.organization_id, ident)
        if row is None or row[1] != caller.account_id:
            raise Rejected(404, "not_found")
        return row[0]

    def change(
        self, caller: Caller, command: CatalogCommand
    ) -> tuple[CatalogResult, CatalogMutation | None]:
        self._master(caller)
        c = command
        if (
            not isinstance(c.operation_id, UUID)
            or c.kind not in {"create", "update", "stop"}
            or (
                c.kind == "create"
                and (c.product_id is not None or c.expected_product_version is not None)
            )
            or (
                c.kind != "create"
                and (
                    not isinstance(c.product_id, UUID)
                    or type(c.expected_product_version) is not int
                    or c.expected_product_version < 1
                    or c.expected_product_version > 9223372036854775807
                )
            )
            or (c.kind == "stop" and c.values is not None)
            or (c.kind != "stop" and c.values is None)
        ):
            raise Rejected(422, "invalid_request")
        if c.values is not None:
            c = replace(c, values=normalize(c.values))
        payload = {
            **asdict(c),
            "actor_id": caller.account_id,
            "organization_id": caller.organization_id,
            "canonical_version": 1,
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).digest()
        old = self.repo.operation(caller.organization_id, c.operation_id)
        if old is not None:
            if old[1] != caller.account_id or old[2] != fingerprint:
                raise Rejected(409, "operation_conflict")
            return old[0], None
        before = self.get(caller, c.product_id) if c.product_id is not None else None
        if before is not None and before.version != c.expected_product_version:
            raise Rejected(409, "conflict")
        changed = before is None or (
            before.selling if c.kind == "stop" else before.values != c.values
        )
        if changed and before is not None and before.version == 9223372036854775807:
            raise Rejected(409, "version_exhausted")
        return self.repo.prepare(caller, c, before, changed, fingerprint)

    def confirm(self, caller: Caller, result: CatalogResult) -> None:
        if self.operation(caller, result.operation_id) != result:
            raise Rejected(409, "conflict")

    def seal(self, caller: Caller, result: CatalogResult, clock: datetime) -> CatalogResult:
        self.repo.seal(caller.organization_id, result.operation_id, clock)
        return result
