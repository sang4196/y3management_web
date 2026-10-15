"""Immutable IAM values. No database/HTTP objects or password hashes cross here."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class Caller:
    account_id: UUID
    organization_id: UUID
    branch_id: UUID | None
    master: bool


@dataclass(frozen=True)
class Authentication:
    caller: Caller
    session_id: UUID
    csrf: str


@dataclass(frozen=True)
class Account:
    id: UUID
    organization_id: UUID
    login_id: str
    state: str
    branch_id: UUID | None
    master: bool
    version: int


@dataclass(frozen=True, repr=False)
class LoginProof:
    account_id: UUID
    security_version: int
    credential_marker: bytes


@dataclass(frozen=True)
class Setup:
    token: str
    expires_at: datetime


@dataclass(frozen=True)
class Preparation:
    token: str
    csrf: str


@dataclass(frozen=True, repr=False)
class Reservation:
    key: bytes
    id: UUID
    account_id: UUID | None
    security_version: int | None


# Module ports expose immutable facts and commands, not persistence adapters.


class IAMPort(Protocol):
    def prepare_master(self, identifier: str, password: str) -> None: ...
    def ensure_uninstalled(self) -> None: ...
    def bootstrap(self, organization_id: UUID, identifier: str) -> Account: ...
    def preparation(self, token: str | None, nonce: str | None, consume: bool = False) -> None: ...
    def login_subject(self, identifier: str) -> Account | None: ...
    def verify_login(
        self, identifier: str, password: str, reservation: Reservation
    ) -> LoginProof | None: ...
    def login(
        self,
        proof: LoginProof,
        sid: UUID,
        preauth: str | None,
        nonce: str | None,
        reservation: Reservation,
    ) -> tuple[str, Account]: ...
    def authenticate(
        self,
        token: str | None,
        *,
        management: bool = False,
        target: UUID | None = None,
        touch: bool = True,
    ) -> Authentication: ...
    def csrf(self, authentication: Authentication, nonce: str | None) -> None: ...
    def require_master(self, caller: Caller) -> None: ...
    def scoped_account(self, caller: Caller, ident: UUID) -> Account: ...
    def lookup(self, caller: Caller, identifier: str) -> Account: ...
    def issue(self, caller: Caller, identifier: str, branch: UUID) -> Account: ...
    def setup(
        self, account: Account, state_id: UUID, *, reissue: bool
    ) -> tuple[Account, Setup]: ...
    def complete(
        self, token: str, password: str, preauth: str | None, nonce: str | None
    ) -> Account: ...
    def lock_credentials(self, ident: UUID) -> None: ...
    def change(self, account: Account, branch: UUID | None, disable: bool) -> Account: ...
    def change_login_id(self, account: Account, identifier: str) -> Account: ...
    def prepare_password_change(
        self, ident: UUID, current_password: str, new_password: str
    ) -> LoginProof: ...
    def change_password(self, proof: LoginProof) -> tuple[Account, Account]: ...
    def restore(self, account: Account) -> Account: ...
    def logout(self, authentication: Authentication) -> None: ...
    def gc_sessions(self) -> None: ...


class SecurityPort(Protocol):
    def allocate(self, kind: str) -> UUID: ...
    def release(self, ident: UUID) -> None: ...
    def preparation(self, raw: str | None) -> Preparation: ...
    def reserve(self, login_id: str) -> Reservation: ...
    def finish(self, reservation: Reservation, success: bool) -> None: ...
    def cancel(self, reservation: Reservation) -> None: ...
