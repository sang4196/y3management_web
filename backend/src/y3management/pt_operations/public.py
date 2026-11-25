"""Immutable Catalog values. No database or HTTP objects cross this boundary."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from y3management.iam.public import Caller


@dataclass(frozen=True)
class ProductValues:
    name: str
    price_won: str
    session_count: str
    payment_type: Literal["RATE", "FIXED_AMOUNT"]
    is_service: bool


@dataclass(frozen=True)
class Product:
    id: UUID
    version: int
    values: ProductValues
    selling: bool
    recorded_at: datetime


@dataclass(frozen=True)
class ProductPage:
    items: tuple[Product, ...]
    total: int


@dataclass(frozen=True)
class CatalogCommand:
    operation_id: UUID
    kind: Literal["create", "update", "stop"]
    product_id: UUID | None = None
    expected_product_version: int | None = None
    values: ProductValues | None = None


@dataclass(frozen=True)
class CatalogMutation:
    organization_id: UUID
    operation_id: UUID
    product_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    kind: str
    before_version: int | None
    after_version: int
    changed: bool
    recorded_at: datetime


@dataclass(frozen=True)
class CatalogResult:
    operation_id: UUID
    kind: str
    changed: bool
    committed_product: Product
    current_product: Product


class CatalogPort(Protocol):
    def get(self, caller: Caller, ident: UUID) -> Product: ...
    def list(self, caller: Caller, offset: int, limit: int) -> ProductPage: ...
    def operation(self, caller: Caller, ident: UUID) -> CatalogResult: ...
    def change(
        self, caller: Caller, command: CatalogCommand
    ) -> tuple[CatalogResult, CatalogMutation | None]: ...
    def confirm(self, caller: Caller, result: CatalogResult) -> None: ...
    def seal(self, caller: Caller, result: CatalogResult, clock: datetime) -> CatalogResult: ...
