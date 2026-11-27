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
    def issue_products(
        self, caller: Caller, branch: UUID, offset: int, limit: int
    ) -> ProductPage: ...
    def issue_product(self, caller: Caller, branch: UUID, ident: UUID) -> Product: ...

    def get(self, caller: Caller, ident: UUID) -> Product: ...
    def list(self, caller: Caller, offset: int, limit: int) -> ProductPage: ...
    def operation(self, caller: Caller, ident: UUID) -> CatalogResult: ...
    def change(
        self, caller: Caller, command: CatalogCommand
    ) -> tuple[CatalogResult, CatalogMutation | None]: ...
    def confirm(self, caller: Caller, result: CatalogResult) -> None: ...
    def seal(self, caller: Caller, result: CatalogResult, clock: datetime) -> CatalogResult: ...


@dataclass(frozen=True)
class IssueCommand:
    operation_id: UUID
    issued_branch_id: UUID
    expected_branch_version: int
    member_id: UUID
    expected_member_version: int
    trainer_id: UUID
    expected_trainer_version: int
    product_id: UUID
    expected_product_version: int


@dataclass(frozen=True)
class IssuedPass:
    id: UUID
    member_id: UUID
    initial_trainer_id: UUID
    product_id: UUID
    product_version: int
    product: ProductValues
    issued_branch_id: UUID
    purchased_sessions: str
    initial_remaining_sessions: str
    issued_at: datetime


@dataclass(frozen=True)
class IssueResult:
    operation_id: UUID
    pass_record: IssuedPass


@dataclass(frozen=True)
class PassIssueEvent:
    organization_id: UUID
    operation_id: UUID
    pass_id: UUID
    member_id: UUID
    trainer_id: UUID
    issued_branch_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    recorded_at: datetime


class PassPort(Protocol):
    def operation(self, caller: Caller, ident: UUID) -> IssueResult: ...
    def replay(self, caller: Caller, command: IssueCommand) -> IssueResult | None: ...
    def issue(
        self, caller: Caller, command: IssueCommand, product: Product
    ) -> tuple[IssueResult, PassIssueEvent]: ...
    def confirm(self, caller: Caller, result: IssueResult) -> None: ...
    def seal(self, caller: Caller, result: IssueResult, clock: datetime) -> IssueResult: ...


@dataclass(frozen=True)
class PassState:
    pass_id: UUID
    member_id: UUID
    product_name: str
    issued_branch_id: UUID
    remaining_sessions: str
    version: int
    manual_expired: bool
    recorded_at: datetime


@dataclass(frozen=True)
class PassStatePage:
    items: tuple[PassState, ...]
    total: int


@dataclass(frozen=True, repr=False)
class PassStateCommand:
    operation_id: UUID
    pass_id: UUID
    expected_state_version: int
    desired_expired: bool
    reason: str


@dataclass(frozen=True)
class PassStateResult:
    operation_id: UUID
    changed: bool
    committed_state: PassState
    current_state: PassState


@dataclass(frozen=True, repr=False)
class PassStateEvent:
    organization_id: UUID
    operation_id: UUID
    pass_id: UUID
    issued_branch_id: UUID
    actor_id: UUID
    actor_role: str
    actor_branch: UUID | None
    kind: str
    reason: str
    before_version: int
    after_version: int
    before_expired: bool
    after_expired: bool
    before_recorded_at: datetime
    recorded_at: datetime


class PassStatePort(Protocol):
    def initialize(self, org: UUID, ident: UUID) -> None: ...
    def get(self, caller: Caller, ident: UUID) -> PassState: ...
    def list(self, caller: Caller, offset: int, limit: int) -> PassStatePage: ...
    def operation(self, caller: Caller, ident: UUID) -> PassStateResult: ...
    def replay(self, caller: Caller, command: PassStateCommand) -> PassStateResult | None: ...
    def change(
        self, caller: Caller, command: PassStateCommand
    ) -> tuple[PassStateResult, PassStateEvent | None]: ...
    def confirm(self, caller: Caller, result: PassStateResult) -> None: ...
    def seal(self, caller: Caller, result: PassStateResult, clock: datetime) -> PassStateResult: ...
