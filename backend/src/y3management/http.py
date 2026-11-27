"""Strict same-origin HTTPS adapters. No database authentication in dependencies."""

from dataclasses import asdict
from typing import Annotated, Literal, cast
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, FastAPI, Header, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.iam.public import (
    Account,
    AccountRoles,
    EmergencySnapshot,
    HandoffRequest,
    LifecycleAccount,
    OperatorCommand,
    Setup,
    TrainerRoleRequest,
)
from y3management.membership.public import MemberCommand, MemberValues
from y3management.pt_operations.public import CatalogCommand, ProductValues
from y3management.use_cases import Service
from y3management.workforce.public import (
    BaseCommand,
    BaseQuery,
    CompensationRequest,
    RegisterTrainer,
    TrainerHomeRequest,
    TrainerStateRequest,
)

AUTH = "__Host-y3-auth"
PREAUTH = "__Host-y3-preauth"


class BodyLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not str(scope["path"]).startswith("/api/"):
            await self.app(scope, receive, send)
            return
        chunks: list[bytes] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > 8192:
                await JSONResponse({"detail": "invalid_request"}, status_code=413)(
                    scope, receive, send
                )
                return
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def buffered() -> Message:
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, buffered, send)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class MemberInput(Input):
    operation_id: UUID
    name: str = Field(strict=True, repr=False)
    phone: str = Field(strict=True, repr=False)
    home_branch_id: UUID


class MemberUpdateInput(Input):
    operation_id: UUID
    expected_member_version: int = Field(strict=True, ge=1, le=9223372036854775807)
    name: str = Field(strict=True, repr=False)
    phone: str = Field(strict=True, repr=False)


class MemberStateInput(Input):
    operation_id: UUID
    expected_member_version: int = Field(strict=True, ge=1, le=9223372036854775807)


class ProductInput(Input):
    operation_id: UUID
    name: str = Field(strict=True, max_length=200)
    price_won: str = Field(strict=True, max_length=1024)
    session_count: str = Field(strict=True, max_length=19)
    payment_type: Literal["RATE", "FIXED_AMOUNT"]
    is_service: bool = Field(strict=True)


class ProductUpdateInput(ProductInput):
    expected_product_version: int = Field(strict=True, ge=1, le=9223372036854775807)


class ProductStopInput(Input):
    operation_id: UUID
    expected_product_version: int = Field(strict=True, ge=1, le=9223372036854775807)


class TrainerAccountInput(Input):
    operation_id: UUID
    login_id: str = Field(min_length=3, max_length=64)


class TrainerSetupInput(Input):
    operation_id: UUID
    expected_account_version: int = Field(strict=True, ge=1)


class BaseCreateInput(Input):
    operation_id: UUID
    expected_base_ledger_version: int = Field(strict=True, ge=1)
    expected_trainer_version: int = Field(strict=True, ge=1)
    start_month: str = Field(strict=True, max_length=7)
    planned_amount_won: str = Field(strict=True, max_length=1024)


class BaseCancelInput(Input):
    operation_id: UUID
    expected_base_ledger_version: int = Field(strict=True, ge=1)
    expected_trainer_version: int = Field(strict=True, ge=1)
    expected_change_revision: int = Field(strict=True, ge=1)


class BaseEditInput(BaseCancelInput):
    planned_amount_won: str = Field(strict=True, max_length=1024)


class CompensationInput(Input):
    operation_id: UUID
    rate_percent: int = Field(strict=True, ge=0, le=100)
    fixed_amount_won: str = Field(strict=True, max_length=1024)
    expected_compensation_version: int = Field(strict=True, ge=1)
    expected_trainer_version: int = Field(strict=True, ge=1)


class TrainerHomeInput(Input):
    operation_id: UUID
    destination_home_branch_id: UUID
    expected_trainer_version: int = Field(strict=True, ge=1)


class TrainerStateInput(Input):
    operation_id: UUID
    desired_active: bool = Field(strict=True)
    expected_trainer_version: int = Field(strict=True, ge=1)


class TrainerRoleInput(Input):
    operation_id: UUID
    account_id: UUID
    desired_granted: bool = Field(strict=True)
    expected_account_version: int = Field(strict=True, ge=1)
    expected_role_version: int = Field(strict=True, ge=0)
    expected_trainer_version: int = Field(strict=True, ge=1)
    identity_confirmed: bool = Field(strict=True)


class TrainerRoleLookup(Input):
    login_id: str = Field(strict=True, min_length=3, max_length=64)


class TrainerInput(Input):
    operation_id: UUID
    name: str = Field(strict=True, max_length=200)
    phone: str = Field(strict=True, max_length=128)
    home_branch_id: UUID
    rate_percent: int = Field(strict=True, ge=0, le=100)
    fixed_amount_won: str = Field(strict=True, max_length=1024)
    base_salary_won: str = Field(strict=True, max_length=1024)
    base_salary_start_month: str = Field(strict=True, max_length=7)


class HandoffSnapshot(Input):
    row_version: int = Field(ge=1, strict=True)
    security_version: int = Field(ge=1, strict=True)
    reset_generation: int = Field(ge=0, strict=True)
    password_reset_pending: bool = Field(strict=True)
    password_ready: bool = Field(strict=True)


class HandoffInput(Input):
    operation_id: UUID
    supersedes_case_id: UUID
    expected: HandoffSnapshot
    identity_confirmed: bool = Field(strict=True)


class Login(Input):
    login_id: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=512, repr=False)


class PasswordChange(Input):
    current_password: str = Field(min_length=1, max_length=512, repr=False)
    new_password: str = Field(min_length=1, max_length=512, repr=False)


class Complete(Input):
    setup_token: str = Field(min_length=40, max_length=128, repr=False)
    new_password: str = Field(min_length=1, max_length=512, repr=False)


class NewBranch(Input):
    code: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=128)


class Issue(Input):
    login_id: str = Field(min_length=3, max_length=64)
    branch_id: UUID


class Lookup(Input):
    login_id: str = Field(min_length=3, max_length=64)


class Version(Input):
    expected_version: int = Field(gt=0, strict=True)


class ResetRequest(Input):
    expected_account_version: int = Field(gt=0, strict=True)
    expected_generation: int = Field(ge=0, strict=True)
    identity_confirmed: bool = Field(strict=True)


class ResetComplete(Input):
    reset_token: str = Field(min_length=40, max_length=128, repr=False)
    new_password: str = Field(min_length=1, max_length=512, repr=False)


class EmergencyToken(Input):
    emergency_token: str = Field(min_length=40, max_length=128, repr=False)


class EmergencyPassword(EmergencyToken):
    new_password: str = Field(min_length=1, max_length=512, repr=False)


class Access(Version):
    branch_id: UUID


class LoginIDChange(Version):
    login_id: str = Field(min_length=3, max_length=64, strict=True)


class Disable(Version):
    status: Literal["DISABLED"]


def account_json(account: Account) -> dict[str, object]:
    scope = None
    if account.master or account.branch_id is not None:
        scope = {
            "kind": "ORGANIZATION" if account.master else "BRANCH",
            "branch_id": str(account.branch_id) if account.branch_id else None,
        }
    result: dict[str, object] = {
        "account_id": str(account.id),
        "login_id": account.login_id,
        "state": account.state,
        "version": account.version,
        "admin_scope": scope,
    }
    if isinstance(account, LifecycleAccount):
        if account.operator:
            result["operator_scope"] = {
                "branch_id": str(account.operator.branch_id),
                "version": account.operator.version,
            }
        result.update(
            restore_state=account.restore_state,
            trainer_id=str(account.trainer_id) if account.trainer_id else None,
            trainer_granted=account.trainer_granted,
            setup_route=account.setup_route,
        )
    return result


class OperatorReissue(Version):
    expected_operator_version: Annotated[int, Field(strict=True, gt=0)]


class OperatorLookup(Lookup):
    branch_id: UUID | None = None


class OperatorRoleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    expected_account_version: Annotated[int, Field(strict=True, gt=0)]
    expected_operator_version: Annotated[int, Field(strict=True, ge=0)]
    desired_granted: Annotated[bool, Field(strict=True)]
    branch_id: UUID | None = None


class OperatorMoveInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    expected_account_version: Annotated[int, Field(strict=True, gt=0)]
    expected_operator_version: Annotated[int, Field(strict=True, gt=0)]
    branch_id: UUID


def cookie(response: Response, name: str, value: str) -> None:
    response.set_cookie(name, value, secure=True, httponly=True, samesite="lax", path="/")


def clear(response: Response, name: str) -> None:
    response.delete_cookie(name, secure=True, httponly=True, samesite="lax", path="/")


def attach(app: FastAPI, settings: Settings) -> None:
    router = APIRouter(prefix="/api/v1")
    app.add_middleware(BodyLimit)

    def service(request: Request) -> Service:
        return cast(Service, request.app.state.iam_service)

    def source(request: Request) -> None:
        if (
            request.url.scheme != "https"
            or str(request.base_url).rstrip("/") != settings.canonical_origin
        ):
            raise Rejected(403, "origin_failed")
        if request.headers.get("sec-fetch-site") == "cross-site":
            raise Rejected(403, "origin_failed")
        origin = request.headers.get("origin")
        if origin is None:
            ref = urlsplit(request.headers.get("referer", ""))
            origin = f"{ref.scheme}://{ref.netloc}" if ref.scheme and ref.netloc else None
        if (
            origin is None
            and request.method == "GET"
            and request.headers.get("sec-fetch-site") == "same-origin"
            and request.headers.get("x-y3-client")
        ):
            return
        if origin != settings.canonical_origin:
            raise Rejected(403, "origin_failed")

    @app.middleware("http")
    async def security_headers(request: Request, call_next: object) -> Response:
        from starlette.middleware.base import RequestResponseEndpoint

        response = await cast(RequestResponseEndpoint, call_next)(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> Response:
        if request.url.path.startswith(
            (
                "/api/v1/admin/products",
                "/api/v1/admin/product-operations",
                "/api/v1/admin/trainers",
                "/api/v1/admin/trainer-registrations",
                "/api/v1/admin/trainer-home-candidates",
                "/api/v1/admin/trainer-account-operations",
                "/api/v1/admin/trainer-role-operations",
                "/api/v1/admin/trainer-state-operations",
                "/api/v1/auth/",
            )
        ):
            return JSONResponse({"detail": "invalid_request"}, status_code=422)
        return await request_validation_exception_handler(request, error)

    @app.exception_handler(Rejected)
    async def rejected(request: Request, error: Rejected) -> JSONResponse:
        headers = {"Retry-After": str(error.retry_after)} if error.retry_after else None
        return JSONResponse({"detail": error.detail}, status_code=error.status, headers=headers)

    def read(request: Request) -> str | None:
        if (
            request.url.scheme != "https"
            or str(request.base_url).rstrip("/") != settings.canonical_origin
        ):
            raise Rejected(403, "origin_failed")
        return request.cookies.get(AUTH)

    def write(request: Request) -> tuple[str | None, str | None]:
        source(request)
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            raise Rejected(415, "json_required")
        return request.cookies.get(AUTH), request.headers.get("x-csrf-token")

    @router.get("/auth/csrf")
    def csrf(request: Request) -> JSONResponse:
        source(request)
        if not request.headers.get("x-y3-client"):
            raise Rejected(403, "csrf_failed")
        nonce, token = service(request).csrf(read(request), request.cookies.get(PREAUTH))
        response = JSONResponse({"csrf_token": nonce})
        if token:
            cookie(response, PREAUTH, token)
        return response

    @router.post("/auth/login", status_code=204)
    def login(request: Request, body: Login) -> Response:
        auth, nonce = write(request)
        token = service(request).login(
            body.login_id, body.password, request.cookies.get(PREAUTH), nonce, auth
        )
        response = Response(status_code=204)
        cookie(response, AUTH, token)
        clear(response, PREAUTH)
        return response

    @router.get("/auth/me")
    def me(request: Request) -> dict[str, object]:
        c, trainer, binding = service(request).identity_profile(read(request))
        roles: list[dict[str, object]] = []
        if c.master or c.branch_id:
            roles.append(
                {
                    "role": "ADMIN",
                    "scope": "ORGANIZATION" if c.master else "BRANCH",
                    "branch_id": str(c.branch_id) if c.branch_id else None,
                }
            )
        if c.operator:
            roles.append(
                {
                    "role": "OPERATOR",
                    "branch_id": str(c.operator.branch_id),
                    "version": c.operator.version,
                }
            )
        if trainer is not None and trainer.active:
            roles.append(
                {
                    "role": "TRAINER",
                    "trainer_id": str(trainer.trainer_id),
                    "home_branch_id": str(trainer.home_branch_id),
                }
            )
        return {
            "account_id": str(c.account_id),
            "organization_id": str(c.organization_id),
            "roles": roles,
            "trainer_binding": (
                {"trainer_id": str(binding.trainer_id), "granted": binding.granted}
                if binding is not None
                else None
            ),
            "capabilities": (
                ["branches:read", *(["branches:create", "accounts:manage"] if c.master else [])]
                if c.master or c.branch_id
                else []
            ),
        }

    @router.post("/auth/logout", status_code=204)
    def logout(request: Request) -> Response:
        auth, nonce = write(request)
        service(request).logout(auth, request.cookies.get(PREAUTH), nonce)
        response = Response(status_code=204)
        clear(response, AUTH)
        clear(response, PREAUTH)
        return response

    @router.post("/auth/password", status_code=204)
    def change_password(request: Request, body: PasswordChange) -> Response:
        auth, nonce = write(request)
        service(request).change_password(auth, nonce, body.current_password, body.new_password)
        response = Response(status_code=204)
        clear(response, AUTH)
        clear(response, PREAUTH)
        return response

    def operator_json(roles: AccountRoles, setup: Setup | None = None) -> dict[str, object]:
        assert roles.operator
        result = account_json(roles.account)
        result.pop("admin_scope")
        result["operator_scope"] = {
            "branch_id": str(roles.operator.branch_id),
            "version": roles.operator.version,
        }
        if setup:
            result.update(
                setup_link=settings.canonical_origin + "/operator-activate#token=" + setup.token,
                expires_at=setup.expires_at.isoformat(),
            )
        return result

    ExpectedOperatorActor = Annotated[UUID, Header(alias="X-Y3-Expected-Actor")]

    @router.post("/admin/operator-roles/lookup")
    def operator_role_lookup(
        request: Request, body: OperatorLookup, expected_actor: ExpectedOperatorActor
    ) -> object:
        auth, nonce = write(request)
        return service(request).operator_candidate(
            auth, body.login_id, body.branch_id, nonce, expected_actor=expected_actor
        )

    @router.get("/admin/operator-roles/{ident}")
    def operator_role_state(
        request: Request,
        ident: UUID,
        expected_actor: ExpectedOperatorActor,
        branch_id: UUID | None = None,
    ) -> object:
        return service(request).operator_candidate(
            read(request), ident, branch_id, expected_actor=expected_actor
        )

    @router.post("/admin/operator-roles/{ident}/changes")
    def operator_role_change(
        request: Request,
        ident: UUID,
        body: OperatorRoleInput,
        expected_actor: ExpectedOperatorActor,
    ) -> object:
        return service(request).change_operator(
            *write(request),
            OperatorCommand(
                body.operation_id,
                ident,
                body.expected_account_version,
                body.expected_operator_version,
                "role",
                body.branch_id,
                body.desired_granted,
            ),
            expected_actor=expected_actor,
        )

    @router.post("/admin/operator-roles/{ident}/branch")
    def operator_role_move(
        request: Request,
        ident: UUID,
        body: OperatorMoveInput,
        expected_actor: ExpectedOperatorActor,
    ) -> object:
        return service(request).change_operator(
            *write(request),
            OperatorCommand(
                body.operation_id,
                ident,
                body.expected_account_version,
                body.expected_operator_version,
                "move",
                body.branch_id,
                True,
            ),
            expected_actor=expected_actor,
        )

    @router.get("/admin/operator-role-operations/{operation}")
    def operator_role_operation(
        request: Request, operation: UUID, expected_actor: ExpectedOperatorActor
    ) -> object:
        return service(request).operator_operation(
            read(request), operation, expected_actor=expected_actor
        )

    @router.post("/admin/operator-accounts", status_code=201)
    def issue_operator(request: Request, body: Issue) -> dict[str, object]:
        return operator_json(
            *service(request).issue_operator(
                *write(request), identifier=body.login_id, branch=body.branch_id
            )
        )

    @router.post("/admin/operator-accounts/lookup")
    def lookup_operator(request: Request, body: Lookup) -> dict[str, object]:
        auth, nonce = write(request)
        return operator_json(service(request).read_operator(auth, body.login_id, nonce))

    @router.get("/admin/operator-accounts/{ident}")
    def get_operator(request: Request, ident: UUID) -> dict[str, object]:
        return operator_json(service(request).read_operator(read(request), ident))

    @router.post("/admin/operator-accounts/{ident}/initial-setup", status_code=201)
    def reissue_operator(request: Request, ident: UUID, body: OperatorReissue) -> dict[str, object]:
        return operator_json(
            *service(request).issue_operator(
                *write(request),
                target=ident,
                expected=body.expected_version,
                expected_operator=body.expected_operator_version,
            )
        )

    @router.get("/operator/branches/{ident}")
    def operator_branch(request: Request, ident: UUID) -> dict[str, object]:
        return asdict(service(request).operator_branch(read(request), ident))

    @router.post("/auth/operator-credentials/complete", status_code=204)
    def complete_operator(request: Request, body: Complete) -> Response:
        _, nonce = write(request)
        service(request).complete_operator(
            body.setup_token, body.new_password, request.cookies.get(PREAUTH), nonce
        )
        response = Response(status_code=204)
        clear(response, PREAUTH)
        return response

    @router.post("/auth/trainer-credentials/complete", status_code=204)
    def trainer_complete(request: Request, body: Complete) -> Response:
        _, nonce = write(request)
        service(request).complete_trainer_setup(
            body.setup_token, body.new_password, request.cookies.get(PREAUTH), nonce
        )
        response = Response(status_code=204)
        clear(response, PREAUTH)
        return response

    @router.get("/admin/trainers/{trainer_id}/role")
    def trainer_role_state(request: Request, trainer_id: UUID) -> object:
        return jsonable_encoder(asdict(service(request).role_state(read(request), trainer_id)))

    @router.post("/admin/trainers/{trainer_id}/role-account-lookup")
    def trainer_role_lookup(request: Request, trainer_id: UUID, body: TrainerRoleLookup) -> object:
        auth, nonce = write(request)
        return jsonable_encoder(
            asdict(service(request).role_lookup(auth, trainer_id, body.login_id, nonce))
        )

    @router.get("/admin/trainer-role-operations/{operation_id}")
    def trainer_role_operation(request: Request, operation_id: UUID) -> object:
        return jsonable_encoder(
            asdict(service(request).role_operation(read(request), operation_id))
        )

    @router.post("/admin/trainers/{trainer_id}/role")
    def trainer_role_change(request: Request, trainer_id: UUID, body: TrainerRoleInput) -> Response:
        auth, nonce = write(request)
        result = service(request).change_trainer_role(
            auth, nonce, trainer_id, TrainerRoleRequest(**body.model_dump())
        )
        response = JSONResponse(jsonable_encoder(asdict(result)))
        if result.reauthentication_required:
            clear(response, AUTH)
        return response

    @router.get("/admin/trainers/{trainer_id}/login-account")
    def trainer_account_state(request: Request, trainer_id: UUID) -> object:
        return jsonable_encoder(
            asdict(service(request).trainer_account_state(read(request), trainer_id))
        )

    @router.get("/admin/trainer-account-operations/{operation_id}")
    def trainer_account_operation(request: Request, operation_id: UUID) -> object:
        return jsonable_encoder(
            asdict(service(request).trainer_account_operation(read(request), operation_id))
        )

    def trainer_delivery(
        request: Request,
        trainer_id: UUID,
        operation: UUID,
        identifier: str | None,
        expected: int | None = None,
    ) -> JSONResponse:
        auth, nonce = write(request)
        result, setup = service(request).issue_trainer_account(
            auth, nonce, trainer_id, operation, identifier, expected
        )
        body = {"operation": jsonable_encoder(asdict(result))}
        if setup is not None:
            body.update(
                setup_link=settings.canonical_origin + "/trainer-activate#token=" + setup.token,
                expires_at=setup.expires_at.isoformat(),
            )
        return JSONResponse(body, status_code=201 if setup else 200)

    @router.post("/admin/trainers/{trainer_id}/login-account")
    def trainer_account_issue(
        request: Request, trainer_id: UUID, body: TrainerAccountInput
    ) -> JSONResponse:
        return trainer_delivery(request, trainer_id, body.operation_id, body.login_id)

    @router.post("/admin/trainers/{trainer_id}/initial-setup")
    def trainer_setup_reissue(
        request: Request, trainer_id: UUID, body: TrainerSetupInput
    ) -> JSONResponse:
        return trainer_delivery(
            request, trainer_id, body.operation_id, None, body.expected_account_version
        )

    @router.post("/auth/credentials/complete", status_code=204)
    def complete(request: Request, body: Complete) -> Response:
        _, nonce = write(request)
        service(request).complete(
            body.setup_token, body.new_password, request.cookies.get(PREAUTH), nonce
        )
        response = Response(status_code=204)
        clear(response, PREAUTH)
        return response

    @router.get("/branches")
    def branches(
        request: Request,
        offset: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
    ) -> dict[str, object]:
        if set(request.query_params) - {"offset", "limit"}:
            raise Rejected(422, "invalid_request")
        page = service(request).branches(read(request), offset, limit)
        return {"items": [asdict(b) for b in page.items], "total": page.total}

    @router.get("/branches/{ident}")
    def branch(request: Request, ident: UUID) -> dict[str, object]:
        if request.query_params:
            raise Rejected(422, "invalid_request")
        return asdict(service(request).branch(read(request), ident))

    @router.post("/admin/branches", status_code=201)
    def create_branch(request: Request, body: NewBranch) -> dict[str, object]:
        auth, nonce = write(request)
        return asdict(service(request).create_branch(auth, nonce, body.code, body.name))

    def issued(result: tuple[Account, Setup]) -> dict[str, object]:
        account, setup = result
        return {
            **account_json(account),
            "setup_link": settings.canonical_origin + "/activate#token=" + setup.token,
            "expires_at": setup.expires_at.isoformat(),
        }

    @router.post("/admin/master-accounts", status_code=201)
    def issue_master(request: Request, body: Lookup) -> dict[str, object]:
        auth, nonce = write(request)
        return issued(service(request).issue_master(auth, nonce, body.login_id))

    @router.post("/admin/master-accounts/lookup")
    def lookup_master(request: Request, body: Lookup) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(service(request).lookup_master(auth, nonce, body.login_id))

    @router.get("/admin/master-accounts/{ident}")
    def get_master(request: Request, ident: UUID) -> dict[str, object]:
        return account_json(service(request).get_master(read(request), ident))

    @router.patch("/admin/master-accounts/{ident}/status")
    def disable_master(request: Request, ident: UUID, body: Disable) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(
            service(request).manage_master(
                auth, nonce, ident, body.expected_version, "account_disable"
            )
        )

    @router.post("/admin/master-accounts/{ident}/restore")
    def restore_master(request: Request, ident: UUID, body: Version) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(
            service(request).manage_master(
                auth, nonce, ident, body.expected_version, "account_restore"
            )
        )

    @router.patch("/admin/master-accounts/{ident}/login-id")
    def rename_master(request: Request, ident: UUID, body: LoginIDChange) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(
            service(request).manage_master(
                auth, nonce, ident, body.expected_version, "login_id_change", body.login_id
            )
        )

    @router.post("/admin/master-accounts/{ident}/activation", status_code=201)
    def reissue_master(request: Request, ident: UUID, body: Version) -> dict[str, object]:
        auth, nonce = write(request)
        return issued(service(request).reissue_master(auth, nonce, ident, body.expected_version))

    @router.get("/admin/master-accounts/{ident}/emergency-recovery")
    def handoff_state(request: Request, ident: UUID) -> dict[str, object]:
        if request.query_params:
            raise Rejected(422, "invalid_request")
        return asdict(service(request).handoff_state(read(request), ident))

    @router.get("/admin/master-accounts/{ident}/emergency-recovery/{operation}")
    def handoff_status(request: Request, ident: UUID, operation: UUID) -> dict[str, object]:
        if request.query_params:
            raise Rejected(422, "invalid_request")
        return asdict(service(request).handoff_state(read(request), ident, operation))

    @router.post("/admin/master-accounts/{ident}/emergency-recovery/handoff", status_code=201)
    def handoff(request: Request, ident: UUID, body: HandoffInput) -> dict[str, object]:
        auth, nonce = write(request)
        result = service(request).handoff(
            auth,
            nonce,
            ident,
            HandoffRequest(
                body.operation_id,
                body.supersedes_case_id,
                EmergencySnapshot(**body.expected.model_dump()),
            ),
            body.identity_confirmed,
        )
        return {
            "operation_id": str(body.operation_id),
            "recipient_link": settings.canonical_origin
            + "/emergency-recover#token="
            + result.token,
            "expires_at": result.expires_at.isoformat(),
        }

    @router.post("/auth/emergency-recovery/inspect")
    def emergency_inspect(request: Request, body: EmergencyToken) -> dict[str, object]:
        _, nonce = write(request)
        return asdict(
            service(request).emergency_recipient(
                body.emergency_token, request.cookies.get(AUTH), request.cookies.get(PREAUTH), nonce
            )
        )

    @router.post("/auth/emergency-recovery/password/complete", status_code=204)
    def emergency_password(request: Request, body: EmergencyPassword) -> Response:
        _, nonce = write(request)
        service(request).emergency_password(
            body.emergency_token,
            body.new_password,
            request.cookies.get(AUTH),
            request.cookies.get(PREAUTH),
            nonce,
        )
        response = Response(status_code=204)
        clear(response, AUTH)
        clear(response, PREAUTH)
        return response

    @router.get("/admin/accounts/{ident}/password-reset")
    def reset_state(request: Request, ident: UUID) -> dict[str, object]:
        return asdict(service(request).reset_state(read(request), ident))

    def reset_result(
        request: Request, ident: UUID, body: ResetRequest, *, reissue: bool
    ) -> dict[str, object]:
        auth, nonce = write(request)
        result = service(request).reset_password(
            auth,
            nonce,
            ident,
            body.expected_account_version,
            body.expected_generation,
            body.identity_confirmed,
            reissue=reissue,
        )
        return {
            "reset_link": settings.canonical_origin + "/reset#token=" + result.token,
            "expires_at": result.expires_at.isoformat(),
        }

    @router.post("/admin/accounts/{ident}/password-reset", status_code=201)
    def reset_start(request: Request, ident: UUID, body: ResetRequest) -> dict[str, object]:
        return reset_result(request, ident, body, reissue=False)

    @router.post("/admin/accounts/{ident}/password-reset/reissue", status_code=201)
    def reset_reissue(request: Request, ident: UUID, body: ResetRequest) -> dict[str, object]:
        return reset_result(request, ident, body, reissue=True)

    @router.post("/auth/password-reset/complete", status_code=204)
    def reset_complete(request: Request, body: ResetComplete) -> Response:
        _, nonce = write(request)
        service(request).complete_reset(
            body.reset_token, body.new_password, request.cookies.get(PREAUTH), nonce
        )
        response = Response(status_code=204)
        for name in (AUTH, PREAUTH):
            clear(response, name)
        return response

    @router.post("/admin/accounts", status_code=201)
    def issue(request: Request, body: Issue) -> dict[str, object]:
        auth, nonce = write(request)
        return issued(service(request).issue(auth, nonce, body.login_id, body.branch_id))

    @router.post("/admin/account-lifecycle/lookup")
    def lifecycle_lookup(request: Request, body: Lookup) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(service(request).lifecycle_read(auth, body.login_id, nonce))

    @router.get("/admin/account-lifecycle/{ident}")
    def lifecycle_get(request: Request, ident: UUID) -> dict[str, object]:
        return account_json(service(request).lifecycle_read(read(request), ident))

    @router.post("/admin/accounts/lookup")
    def lookup(request: Request, body: Lookup) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(service(request).lookup(auth, nonce, body.login_id))

    @router.get("/admin/accounts/{ident}")
    def get_account(request: Request, ident: UUID) -> dict[str, object]:
        return account_json(service(request).get_account(read(request), ident))

    @router.post("/admin/accounts/{ident}/activation", status_code=201)
    def reissue(request: Request, ident: UUID, body: Version) -> dict[str, object]:
        auth, nonce = write(request)
        return issued(service(request).reissue(auth, nonce, ident, body.expected_version))

    @router.patch("/admin/accounts/{ident}/login-id")
    def change_login_id(request: Request, ident: UUID, body: LoginIDChange) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(
            service(request).change_login_id(
                auth, nonce, ident, body.expected_version, body.login_id
            )
        )

    @router.patch("/admin/accounts/{ident}/access")
    def access(request: Request, ident: UUID, body: Access) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(
            service(request).change(auth, nonce, ident, body.expected_version, body.branch_id)
        )

    @router.patch("/admin/accounts/{ident}/status")
    def disable(request: Request, ident: UUID, body: Disable) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(
            service(request).change(auth, nonce, ident, body.expected_version, disable=True)
        )

    @router.post("/admin/accounts/{ident}/restore")
    def restore(request: Request, ident: UUID, body: Version) -> dict[str, object]:
        auth, nonce = write(request)
        return account_json(service(request).restore(auth, nonce, ident, body.expected_version))

    def workforce_query(request: Request, allowed: set[str]) -> None:
        if any(k not in allowed for k in request.query_params):
            raise Rejected(422, "invalid_request")

    @router.post("/admin/trainers")
    def register_trainer(request: Request, body: TrainerInput) -> Response:
        workforce_query(request, set())
        auth, nonce = write(request)
        result = service(request).register_trainer(
            auth, nonce, RegisterTrainer(**body.model_dump())
        )
        return JSONResponse(
            jsonable_encoder(
                {"operation_id": result.operation_id, "trainer": asdict(result.trainer)}
            ),
            status_code=201 if result.created else 200,
        )

    @router.get("/admin/trainer-registrations/{operation}")
    def trainer_registration(request: Request, operation: UUID) -> dict[str, object]:
        workforce_query(request, set())
        result = service(request).trainer_registration(read(request), operation)
        return {"operation_id": result.operation_id, "trainer": asdict(result.trainer)}

    @router.get("/admin/trainers/{ident}/base-schedule")
    def base_schedule(
        request: Request,
        ident: UUID,
        basis_month: str,
        expected_actor: ExpectedOperatorActor,
        offset: int = 0,
        limit: int = 25,
        expected_base_ledger_version: int | None = None,
        expected_server_business_month: str | None = None,
        expected_basis_month: str | None = None,
    ) -> dict[str, object]:
        workforce_query(
            request,
            {
                "basis_month",
                "offset",
                "limit",
                "expected_base_ledger_version",
                "expected_server_business_month",
                "expected_basis_month",
            },
        )
        return asdict(
            service(request).base_schedule(
                read(request),
                ident,
                BaseQuery(
                    basis_month,
                    offset,
                    limit,
                    expected_base_ledger_version,
                    expected_server_business_month,
                    expected_basis_month,
                ),
                expected_actor=expected_actor,
            )
        )

    @router.get("/admin/trainers/{ident}/base-schedule-history")
    def base_history(
        request: Request,
        ident: UUID,
        expected_actor: ExpectedOperatorActor,
        offset: int = 0,
        limit: int = 25,
        expected_base_ledger_version: int | None = None,
        expected_server_business_month: str | None = None,
    ) -> dict[str, object]:
        workforce_query(
            request,
            {"offset", "limit", "expected_base_ledger_version", "expected_server_business_month"},
        )
        head, history, clock, business_month = service(request).base_history(
            read(request),
            ident,
            offset,
            limit,
            expected_base_ledger_version,
            expected_server_business_month,
            expected_actor=expected_actor,
        )
        return {
            "trainer_id": head.trainer_id,
            "home_branch_id": head.home_branch_id,
            "trainer_version": head.trainer_version,
            "base_ledger_version": head.base_ledger_version,
            "as_of": clock,
            "server_business_month": business_month,
            **asdict(history),
        }

    @router.post("/admin/trainers/{ident}/base-schedule/changes")
    def create_base(
        request: Request, ident: UUID, body: BaseCreateInput, expected_actor: ExpectedOperatorActor
    ) -> dict[str, object]:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_base(
                auth,
                nonce,
                ident,
                BaseCommand(kind="create", **body.model_dump()),
                expected_actor=expected_actor,
            )
        )

    @router.post("/admin/trainers/{ident}/base-schedule/changes/{change}/edit")
    def edit_base(
        request: Request,
        ident: UUID,
        change: UUID,
        body: BaseEditInput,
        expected_actor: ExpectedOperatorActor,
    ) -> dict[str, object]:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_base(
                auth,
                nonce,
                ident,
                BaseCommand(kind="edit", change_id=change, **body.model_dump()),
                expected_actor=expected_actor,
            )
        )

    @router.post("/admin/trainers/{ident}/base-schedule/changes/{change}/cancel")
    def cancel_base(
        request: Request,
        ident: UUID,
        change: UUID,
        body: BaseCancelInput,
        expected_actor: ExpectedOperatorActor,
    ) -> dict[str, object]:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_base(
                auth,
                nonce,
                ident,
                BaseCommand(kind="cancel", change_id=change, **body.model_dump()),
                expected_actor=expected_actor,
            )
        )

    @router.get("/admin/trainer-base-operations/{operation}")
    def base_operation(
        request: Request, operation: UUID, expected_actor: ExpectedOperatorActor
    ) -> dict[str, object]:
        workforce_query(request, set())
        return asdict(
            service(request).base_operation(read(request), operation, expected_actor=expected_actor)
        )

    @router.get("/admin/trainers/{ident}/compensation")
    def compensation(
        request: Request, ident: UUID, expected_actor: ExpectedOperatorActor
    ) -> dict[str, object]:
        workforce_query(request, set())
        return asdict(
            service(request).compensation(read(request), ident, expected_actor=expected_actor)
        )

    @router.get("/admin/trainers/{ident}/compensation-history")
    def compensation_history(
        request: Request,
        ident: UUID,
        expected_actor: ExpectedOperatorActor,
        offset: int = 0,
        limit: int = 25,
    ) -> dict[str, object]:
        workforce_query(request, {"offset", "limit"})
        return asdict(
            service(request).compensation_history(
                read(request), ident, offset, limit, expected_actor=expected_actor
            )
        )

    @router.post("/admin/trainers/{ident}/compensation")
    def change_compensation(
        request: Request,
        ident: UUID,
        body: CompensationInput,
        expected_actor: ExpectedOperatorActor,
    ) -> dict[str, object]:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_compensation(
                auth,
                nonce,
                ident,
                CompensationRequest(**body.model_dump()),
                expected_actor=expected_actor,
            )
        )

    @router.get("/admin/trainer-compensation-operations/{operation}")
    def compensation_operation(
        request: Request, operation: UUID, expected_actor: ExpectedOperatorActor
    ) -> dict[str, object]:
        workforce_query(request, set())
        return asdict(
            service(request).compensation_operation(
                read(request), operation, expected_actor=expected_actor
            )
        )

    @router.post("/admin/trainers/{ident}/home")
    def change_trainer_home(
        request: Request,
        ident: UUID,
        body: TrainerHomeInput,
        expected_actor: ExpectedOperatorActor,
    ) -> dict[str, object]:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_trainer_home(
                auth,
                nonce,
                ident,
                TrainerHomeRequest(**body.model_dump()),
                expected_actor=expected_actor,
            )
        )

    @router.get("/admin/trainer-home-operations/{operation}")
    def trainer_home_operation(
        request: Request, operation: UUID, expected_actor: ExpectedOperatorActor
    ) -> dict[str, object]:
        workforce_query(request, set())
        return asdict(
            service(request).trainer_home_operation(
                read(request), operation, expected_actor=expected_actor
            )
        )

    @router.post("/admin/trainers/{ident}/state")
    def change_trainer_state(
        request: Request, ident: UUID, body: TrainerStateInput
    ) -> dict[str, object]:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_trainer_state(
                auth, nonce, ident, TrainerStateRequest(**body.model_dump())
            )
        )

    @router.get("/admin/trainer-state-operations/{operation}")
    def trainer_state_operation(request: Request, operation: UUID) -> dict[str, object]:
        workforce_query(request, set())
        return asdict(service(request).trainer_state_operation(read(request), operation))

    @router.get("/admin/trainers/{ident}")
    def trainer(request: Request, ident: UUID) -> dict[str, object]:
        workforce_query(request, set())
        return asdict(service(request).trainer(read(request), ident))

    @router.get("/admin/trainers")
    def trainers(request: Request, offset: int = 0, limit: int = 25) -> dict[str, object]:
        workforce_query(request, {"offset", "limit"})
        return asdict(service(request).trainers(read(request), offset, limit))

    @router.get("/admin/trainer-home-candidates")
    def trainer_candidates(request: Request, offset: int = 0, limit: int = 25) -> dict[str, object]:
        workforce_query(request, {"offset", "limit"})
        return {
            "items": [
                asdict(c) for c in service(request).trainer_candidates(read(request), offset, limit)
            ]
        }

    @app.get("/account-lifecycle", response_class=HTMLResponse)
    def lifecycle_page(request: Request) -> str:
        caller, _ = service(request).principal(read(request))
        if not caller.master:
            raise Rejected(403, "forbidden")
        return LIFECYCLE_PAGE

    @app.get("/account-lifecycle.js")
    def lifecycle_script(request: Request) -> Response:
        read(request)
        return Response(LIFECYCLE_SCRIPT, media_type="application/javascript")

    @app.get("/trainers", response_class=HTMLResponse)
    def trainers_page(request: Request) -> str:
        read(request)
        return workforce_page()

    @app.get("/trainers.js")
    def trainers_script(request: Request) -> Response:
        read(request)
        return Response(WORKFORCE_SCRIPT, media_type="application/javascript")

    @app.get("/trainers.css")
    def trainers_style(request: Request) -> Response:
        read(request)
        return Response(
            """*{box-sizing:border-box}body{max-width:44rem;margin:auto;padding:1rem;
font-family:system-ui,sans-serif}label{display:block;margin:.8rem 0}input,select{display:block;
width:100%;min-width:0;padding:.6rem}fieldset{min-width:0}button{padding:.7rem;margin:.3rem}
p,li{overflow-wrap:anywhere}h1{font-size:1.6rem}""",
            media_type="text/css",
        )

    @router.get("/admin/products")
    def products(
        request: Request, expected_actor: ExpectedOperatorActor, offset: int = 0, limit: int = 25
    ) -> object:
        workforce_query(request, {"offset", "limit"})
        return asdict(
            service(request).products(read(request), offset, limit, expected_actor=expected_actor)
        )

    @router.get("/admin/products/{ident}")
    def product(request: Request, ident: UUID, expected_actor: ExpectedOperatorActor) -> object:
        workforce_query(request, set())
        return asdict(service(request).product(read(request), ident, expected_actor=expected_actor))

    @router.get("/admin/product-operations/{operation}")
    def product_operation(
        request: Request, operation: UUID, expected_actor: ExpectedOperatorActor
    ) -> object:
        workforce_query(request, set())
        return asdict(
            service(request).product_operation(
                read(request), operation, expected_actor=expected_actor
            )
        )

    @router.post("/admin/products")
    def create_product(
        request: Request, body: ProductInput, expected_actor: ExpectedOperatorActor
    ) -> object:
        workforce_query(request, set())
        auth, nonce = write(request)
        values = ProductValues(**body.model_dump(exclude={"operation_id"}))
        return asdict(
            service(request).change_product(
                auth,
                nonce,
                CatalogCommand(body.operation_id, "create", values=values),
                expected_actor=expected_actor,
            )
        )

    @router.post("/admin/products/{ident}")
    def update_product(
        request: Request,
        ident: UUID,
        body: ProductUpdateInput,
        expected_actor: ExpectedOperatorActor,
    ) -> object:
        workforce_query(request, set())
        auth, nonce = write(request)
        values = ProductValues(
            **body.model_dump(exclude={"operation_id", "expected_product_version"})
        )
        return asdict(
            service(request).change_product(
                auth,
                nonce,
                CatalogCommand(
                    body.operation_id, "update", ident, body.expected_product_version, values
                ),
                expected_actor=expected_actor,
            )
        )

    @router.post("/admin/products/{ident}/stop")
    def stop_product(
        request: Request, ident: UUID, body: ProductStopInput, expected_actor: ExpectedOperatorActor
    ) -> object:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_product(
                auth,
                nonce,
                CatalogCommand(body.operation_id, "stop", ident, body.expected_product_version),
                expected_actor=expected_actor,
            )
        )

    @app.get("/products", response_class=HTMLResponse)
    def product_page(request: Request) -> str:
        caller, _ = service(request).principal(read(request))
        if not caller.master:
            raise Rejected(403, "forbidden")
        return PRODUCT_PAGE

    @app.get("/products.css")
    def product_style(request: Request) -> Response:
        read(request)
        return Response(
            "#products button{max-width:100%;white-space:normal;overflow-wrap:anywhere;"
            "text-align:left}#selection{max-width:100%;white-space:normal;overflow-wrap:anywhere}"
            "nav{display:flex;flex-wrap:wrap}",
            media_type="text/css",
        )

    @app.get("/products.js")
    def product_script(request: Request) -> Response:
        read(request)
        return Response(PRODUCT_SCRIPT, media_type="application/javascript")

    @router.get("/admin/member-branches")
    def member_branches(
        request: Request, expected_actor: ExpectedOperatorActor, offset: int = 0, limit: int = 25
    ) -> object:
        workforce_query(request, {"offset", "limit"})
        return [
            asdict(b)
            for b in service(request).member_branches(
                read(request), offset, limit, expected_actor=expected_actor
            )
        ]

    @router.get("/admin/members")
    def members(
        request: Request, expected_actor: ExpectedOperatorActor, offset: int = 0, limit: int = 25
    ) -> object:
        workforce_query(request, {"offset", "limit"})
        return asdict(
            service(request).members(read(request), offset, limit, expected_actor=expected_actor)
        )

    @router.get("/admin/members/{ident}")
    def member(request: Request, ident: UUID, expected_actor: ExpectedOperatorActor) -> object:
        workforce_query(request, set())
        return asdict(service(request).member(read(request), ident, expected_actor=expected_actor))

    @router.get("/admin/member-operations/{operation}")
    def member_operation(
        request: Request, operation: UUID, expected_actor: ExpectedOperatorActor
    ) -> object:
        workforce_query(request, set())
        return asdict(
            service(request).member_operation(
                read(request), operation, expected_actor=expected_actor
            )
        )

    @router.post("/admin/members")
    def create_member(
        request: Request, body: MemberInput, expected_actor: ExpectedOperatorActor
    ) -> object:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_member(
                auth,
                nonce,
                MemberCommand(
                    body.operation_id,
                    "create",
                    home_branch_id=body.home_branch_id,
                    values=MemberValues(body.name, body.phone),
                ),
                expected_actor=expected_actor,
            )
        )

    @router.post("/admin/members/{ident}")
    def update_member(
        request: Request,
        ident: UUID,
        body: MemberUpdateInput,
        expected_actor: ExpectedOperatorActor,
    ) -> object:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_member(
                auth,
                nonce,
                MemberCommand(
                    body.operation_id,
                    "update",
                    ident,
                    body.expected_member_version,
                    values=MemberValues(body.name, body.phone),
                ),
                expected_actor=expected_actor,
            )
        )

    @router.post("/admin/members/{ident}/deactivate")
    def deactivate_member(
        request: Request, ident: UUID, body: MemberStateInput, expected_actor: ExpectedOperatorActor
    ) -> object:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_member(
                auth,
                nonce,
                MemberCommand(body.operation_id, "deactivate", ident, body.expected_member_version),
                expected_actor=expected_actor,
            )
        )

    @router.post("/admin/members/{ident}/reactivate")
    def reactivate_member(
        request: Request, ident: UUID, body: MemberStateInput, expected_actor: ExpectedOperatorActor
    ) -> object:
        workforce_query(request, set())
        auth, nonce = write(request)
        return asdict(
            service(request).change_member(
                auth,
                nonce,
                MemberCommand(body.operation_id, "reactivate", ident, body.expected_member_version),
                expected_actor=expected_actor,
            )
        )

    @app.get("/members", response_class=HTMLResponse)
    def members_page(request: Request) -> str:
        caller, _ = service(request).principal(read(request))
        if not (caller.master or caller.branch_id or caller.operator):
            raise Rejected(403, "forbidden")
        return MEMBER_PAGE

    @app.get("/members.css")
    def members_style(request: Request) -> Response:
        read(request)
        return Response(MEMBER_STYLE, media_type="text/css")

    @app.get("/members.js")
    def members_script(request: Request) -> Response:
        read(request)
        return Response(MEMBER_SCRIPT, media_type="application/javascript")

    app.include_router(router)

    @app.get("/operator-accounts", response_class=HTMLResponse)
    def operator_accounts_page(request: Request) -> str:
        caller = service(request).me(read(request))
        if not caller.master and not caller.branch_id:
            raise Rejected(403, "forbidden")
        return """<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>운영자 계정</title>
<h1>운영자 계정</h1><a href="/operator-roles">기존 계정 역할·지점 관리</a>
<form id="operator" method="post">
<label>로그인 ID <input id="login" required></label>
<label>업무 지점 <select id="branch"></select></label>
<button value="lookup" disabled>현재 상태 조회</button>
<button value="issue" disabled>새 계정 발급</button>
<button value="reissue" disabled>초기 설정 링크 재발급</button></form>
<p role="status" id="result"></p><div id="delivery"></div>
<script src="/operator-accounts.js"></script></html>"""

    @app.get("/operator-roles", response_class=HTMLResponse)
    def operator_roles_page(request: Request) -> str:
        service(request).branches(read(request), 0, 1)
        return """<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Operator 역할 관리</title><h1>Operator 역할·업무 지점</h1>
<a href="/operator-accounts">신규 계정 발급</a> <a href="/account">내 계정</a>
<form id="role-lookup"><label>현재 로그인 ID <input id="role-login" required></label>
<label>최초 업무 지점 <select id="role-branch" required></select></label>
<button id="role-find" disabled>조회</button></form>
<pre id="role-current"></pre><button id="role-grant" disabled>부여·재부여</button>
<button id="role-revoke" disabled>역할 회수</button>
<label>이동 목적지 <select id="role-destination"></select></label>
<button id="role-move" disabled>지점 이동</button>
<button id="role-reconcile" disabled>마지막 요청 확인</button>
<p id="role-message" role="status"></p><a href="/login">다시 로그인</a>
<script src="/operator-roles.js"></script></html>"""

    @app.get("/operator-roles.js")
    def operator_roles_script() -> Response:
        return Response(OPERATOR_ROLES_JS, media_type="application/javascript")

    @app.get("/operator-accounts.js")
    def operator_accounts_script() -> Response:
        return Response(OPERATOR_ACCOUNTS_JS, media_type="application/javascript")

    @app.get("/operator-activate", response_class=HTMLResponse)
    @app.get("/trainer-activate", response_class=HTMLResponse)
    def trainer_activation_page(request: Request) -> str:
        return """<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>최초 비밀번호 설정</title>
<h1>최초 비밀번호 설정</h1><form id="trainer-setup" method="post" >
<label>새 비밀번호
<input id="new-password" type="password" autocomplete="new-password" required></label>
<button disabled>설정</button></form><p id="result" role="status"></p><a href="/login">로그인</a>
<script src="/trainer-account.js"></script></html>"""

    @app.get("/account", response_class=HTMLResponse)
    def self_account_page(request: Request) -> str:
        caller, _ = service(request).principal(read(request))
        page = """<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>내 계정</title>
<h1>내 계정</h1><pre id="identity"></pre><form id="self-password" method="post" action="/account">
<label>현재 비밀번호
<input id="current-password" type="password" autocomplete="current-password" required></label>
<label>새 비밀번호
<input id="new-password" type="password" autocomplete="new-password" required></label>
<button disabled>비밀번호 변경</button></form><button id="signout" disabled>로그아웃</button>
<p id="result" role="status"></p><script src="/trainer-account.js"></script></html>"""

        link = (
            '<a id="members-link" href="/members">회원 관리</a>'
            if caller.master or caller.branch_id or caller.operator
            else ""
        )
        return page.replace("<h1>내 계정</h1>", "<h1>내 계정</h1>" + link)

    @app.get("/trainer-account.js")
    def trainer_account_script(request: Request) -> Response:
        return Response(
            r"""'use strict';
let setupToken=new URLSearchParams(location.hash.slice(1)).get('token');
history.replaceState(null,'',location.pathname);
const out=document.getElementById('result'),form=document.querySelector('form');
async function csrf(){const r=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'trainer'}});
if(!r.ok)throw Error();return (await r.json()).csrf_token;}
async function post(path,body){const nonce=await csrf();const r=await fetch('/api/v1'+path,
{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':nonce},
body:JSON.stringify(body)});
if(!r.ok)throw Error();return r;}
let generation=0;
const button=form.querySelector('button');
function resetSetup(){
 setupToken=new URLSearchParams(location.hash.slice(1)).get('token');
 history.replaceState(null,'',location.pathname);generation++;
 form.reset();form.hidden=false;button.disabled=!setupToken;out.textContent='';
}
if(form.id==='trainer-setup'){
 addEventListener('hashchange',resetSetup);
 addEventListener('pagehide',()=>{generation++;setupToken=null;form.reset();button.disabled=true;});
}
form.addEventListener('submit',async e=>{e.preventDefault();if(button.disabled)return;
const seq=generation;button.disabled=true;
try{const password=document.getElementById('new-password').value;
if(form.id==='trainer-setup'){await post(location.pathname==='/operator-activate'?
'/auth/operator-credentials/complete':'/auth/trainer-credentials/complete',
{setup_token:setupToken,new_password:password});if(seq!==generation)return;setupToken=null;form.hidden=true;
out.textContent='설정했습니다. 로그인해 주세요.';}
else{await post('/auth/password',
{current_password:document.getElementById('current-password').value,
new_password:password});location.href='/login';}
}catch{if(seq===generation)
 out.textContent='처리하지 못했습니다. 현재 상태와 입력을 확인해 주세요.';}
finally{if(seq===generation){form.reset();button.disabled=form.id==='trainer-setup'&&!setupToken;}}});
button.disabled=form.id==='trainer-setup'&&!setupToken;
const logout=document.getElementById('signout');if(logout){logout.disabled=false;
logout.addEventListener('click',async()=>{try{await post('/auth/logout',{});location.href='/login';}
catch{out.textContent='로그아웃하지 못했습니다.';}});
fetch('/api/v1/auth/me').then(async r=>{if(!r.ok)throw Error();
const profile=await r.json();
document.getElementById('identity').textContent=JSON.stringify(profile,null,2);
const op=profile.roles.find(role=>role.role==='OPERATOR');if(op){
const branch=await fetch('/api/v1/operator/branches/'+op.branch_id);if(!branch.ok)throw Error();
const data=await branch.json();
document.getElementById('identity').append('\n업무 지점 '+data.code+' '+data.name);}})
.catch(()=>{out.textContent='로그인이 필요합니다.';});}
""",
            media_type="application/javascript",
        )

    @app.get("/activate", response_class=HTMLResponse)
    def activation_page(request: Request) -> str:
        read(request)
        return """<!doctype html><meta charset="utf-8"><title>비밀번호 설정</title>
<form id="setup" method="post" action="/activate">
<label>새 비밀번호 <input id="password" type="password" autocomplete="new-password"
required></label>
<button id="submit" disabled>설정</button></form><p id="result"></p>
<script src="/activate.js"></script>"""

    @app.get("/activate.js")
    def activation_script(request: Request) -> Response:
        read(request)
        script = """(()=>{'use strict';
        let token=new URLSearchParams(location.hash.slice(1)).get('token');
        history.replaceState(null,'',location.pathname);
        document.getElementById('submit').disabled=!token;
        document.getElementById('setup').addEventListener('submit',async e=>{e.preventDefault();
        const output=document.getElementById('result');try{
          if(!token)throw Error();
          const prep=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'setup'}});
          if(!prep.ok)throw Error();const csrf=(await prep.json()).csrf_token;
          const r=await fetch('/api/v1/auth/credentials/complete',{method:'POST',
          headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},
          body:JSON.stringify({setup_token:token,
          new_password:document.getElementById('password').value})});
          if(!r.ok)throw Error();token=null;document.getElementById('password').value='';
          output.textContent='비밀번호가 설정되었습니다. 로그인해 주세요.';
        }catch{output.textContent='설정할 수 없습니다. 새 설정 링크와 입력을 확인해 주세요.';}
        });})();"""
        return Response(script, media_type="application/javascript")

    def password_page(flow: str) -> str:
        action = {"login": "/login", "reset": "/reset", "emergency": "/emergency-recover"}[flow]
        return f"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/trainers.css"><title>Y3 인증</title>
<body data-flow="{flow}"><form id="password-form" method="post" action="{action}">
<label>로그인 ID <input id="identifier" autocomplete="username"></label>
<label>비밀번호 <input id="password" type="password" autocomplete="current-password"></label>
<button disabled>계속</button></form><p id="result"></p>
<script src="/password-auth.js"></script></body>"""

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request) -> str:
        read(request)
        return password_page("login")

    @app.get("/reset", response_class=HTMLResponse)
    def reset_page(request: Request) -> str:
        read(request)
        return password_page("reset")

    @app.get("/emergency-recover", response_class=HTMLResponse)
    def emergency_page(request: Request) -> str:
        read(request)
        return password_page("emergency")

    @app.get("/password-auth.js")
    def password_script(request: Request) -> Response:
        read(request)
        return Response(PASSWORD_SCRIPT, media_type="application/javascript")


PASSWORD_SCRIPT = r"""(()=>{'use strict';
let token=new URLSearchParams(location.hash.slice(1)).get('token');
history.replaceState(null,'',location.pathname);
const flow=document.body.dataset.flow,form=document.getElementById('password-form');
const out=document.getElementById('result'),id=document.getElementById('identifier');
const pw=document.getElementById('password'),button=form.querySelector('button');
id.parentElement.hidden=flow!=='login';id.required=flow==='login';pw.required=true;
pw.autocomplete=flow==='login'?'current-password':'new-password';
button.disabled=flow!=='login'&&!token;
form.addEventListener('submit',async e=>{e.preventDefault();button.disabled=true;
try{const p=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'password'}});
if(!p.ok)throw Error();const csrf=(await p.json()).csrf_token;
const path=flow==='login'?'/auth/login':flow==='reset'?'/auth/password-reset/complete':
'/auth/emergency-recovery/password/complete';
const body=flow==='login'?{login_id:id.value,password:pw.value}:flow==='reset'?
{reset_token:token,new_password:pw.value}:{emergency_token:token,new_password:pw.value};
const r=await fetch('/api/v1'+path,{method:'POST',headers:{'Content-Type':'application/json',
'X-CSRF-Token':csrf},body:JSON.stringify(body)});if(!r.ok)throw Error();
if(flow==='login'){
const current=await fetch('/api/v1/auth/me');if(!current.ok)throw Error();
const identity=await current.json();
if(!identity.roles.some(role=>role.role==='ADMIN')&&(identity.roles.some(role=>role.role==='OPERATOR')||
(identity.roles.length===1&&identity.roles[0].role==='TRAINER'))){
location.href='/account';return;}
out.textContent='로그인되었습니다.';
if(identity.roles.some(role=>role.role==='ADMIN')){
 document.getElementById('operator-link')?.remove();
 const link=document.createElement('a');link.id='operator-link';link.href='/operator-accounts';
 link.textContent='운영자 계정';out.after(link);}
document.getElementById('members-link')?.remove();
if(identity.roles.some(r=>r.role==='ADMIN'||r.role==='OPERATOR')){
 const members=document.createElement('a');members.id='members-link';members.href='/members';
 members.textContent='회원 관리';out.after(members);}
const old=document.getElementById('lifecycle-link');if(old)old.remove();
if(identity.capabilities.includes('accounts:manage')){
 document.getElementById('products-link')?.remove();
 const products=document.createElement('a');products.id='products-link';products.href='/products';
 products.textContent='PT 상품 관리';out.after(products);
 const link=document.createElement('a');link.id='lifecycle-link';link.href='/account-lifecycle';
 link.textContent='계정 관리';out.after(link);}}

else{token=null;form.hidden=true;out.textContent='비밀번호가 설정되었습니다. 로그인해 주세요.';}
}catch{out.textContent='처리하지 못했습니다. 입력 또는 설정 링크를 확인해 주세요.';}
finally{pw.value='';button.disabled=flow!=='login'&&!token;}});})();"""


def workforce_page() -> str:
    return """<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/trainers.css"><title>Trainer 등록</title>
<h1>Trainer 등록</h1><form id="trainer-form" method="post" action="/api/v1/admin/trainers">
<fieldset id="fields" disabled>
<label>이름
<input id="name" required></label>


<label>전화번호
<input id="phone" type="tel" required></label>


<label>Home Branch
<select id="home_branch_id" required><option value="">선택</option></select></label>

<label>Rate (%)
<input id="rate_percent" type="text" inputmode="numeric" required></label>


<label>Fixed Amount (원)
<input id="fixed_amount_won" type="text" inputmode="numeric" required></label>


<label>시작 월부터 적용되는 기본급 설정 (원)
<input id="base_salary_won" type="text" inputmode="numeric" required></label>


<label>기본급 적용 시작 월 (YYYY-MM)
<input id="base_salary_start_month" type="text" required></label>


<button id="submit" disabled>등록</button></fieldset></form>
<button id="status" disabled>이번 등록 결과 확인</button><button id="new" disabled>새 등록</button>
<p id="result" role="status"></p><h2>등록된 Trainer</h2><ul id="trainers"></ul>
<script src="/trainers.js"></script>"""


WORKFORCE_SCRIPT = """(()=>{'use strict';

const $=id=>document.getElementById(id),out=$('result');
let operation=crypto.randomUUID();

let busy=false,identity=null;

async function listing(){const r=await fetch('/api/v1/admin/trainers');
if(!r.ok)throw Error();

const data=await r.json();
$('trainers').replaceChildren();
for(const t of data.items){
const li=document.createElement('li');
li.textContent=t.name+' ('+t.home_branch_id+')';
$('trainers').append(li);
const accountRefresh=accountControls(li,t);
let resetRefresh=async()=>{};
const roleRefresh=roleControls(li,t,async(preserve)=>{
 await accountRefresh(preserve);await resetRefresh();});
if(identity.capabilities.includes('accounts:manage'))
 resetRefresh=resetControls(li,t,async()=>{await roleRefresh();await accountRefresh(true);});
stateControls(li,t,async()=>{await roleRefresh();await accountRefresh(true);await resetRefresh();});
if(identity.roles.some(r=>r.role==='ADMIN'&&r.scope==='ORGANIZATION'))homeControls(li,t);
compensationControls(li,t);baseControls(li,t);
}}
// Only the newest read may publish a complete snapshot; writes invalidate older reads.
function latestRead(){let epoch=0,current=Promise.resolve();
return {invalidate(){epoch++;},run(read,apply){
const mine=++epoch;
const task=(async()=>{const value=await read();if(mine===epoch)apply(value);})();
current=task;
return (async()=>{let waiting=task;for(;;){
try{await waiting;}catch(error){if(waiting===current)throw error;}
if(waiting===current)return;waiting=current;
}})();
}};}
function updateTrainer(t,next){
if(next.id!==t.id)throw Error();
if(next.version<t.version)return;
if(next.version===t.version&&(next.active!==t.active||next.home_branch_id!==t.home_branch_id))
 throw Error();
Object.assign(t,next);
}
function roleControls(li,t,accountRefresh){
const box=document.createElement('section');
box.dataset.roleTrainer=t.id;

const title=document.createElement('h3');
title.textContent='기존 계정 Trainer 역할';

const status=document.createElement('p'),out=document.createElement('p');
out.setAttribute('role','status');

const form=document.createElement('form');
form.method='post';
form.action='/trainers';

const login=document.createElement('input');
login.setAttribute('aria-label','역할 연결할 기존 로그인 ID');

login.autocomplete='off';
login.required=true;

const lookup=document.createElement('button');
lookup.textContent='정확 계정 확인';

const confirm=document.createElement('input');
confirm.type='checkbox';

const label=document.createElement('label');
label.append(confirm,
 document.createTextNode('이 Trainer와 계정 소유자가 같은 사람임을 확인했습니다.'));

const grant=document.createElement('button'),revoke=document.createElement('button');

const fresh=document.createElement('button'),check=document.createElement('button');

const operation=document.createElement('input');
operation.setAttribute('aria-label','역할 작업 번호');

operation.autocomplete='off';
operation.placeholder='결과를 조회할 작업 UUID';

grant.textContent='Trainer 역할 부여';
revoke.textContent='Trainer 역할 회수';

fresh.textContent='새 역할 작업';
check.textContent='역할 작업 결과 확인';

for(const b of [grant,revoke,fresh,check])b.type='button';

form.append(login,lookup);
box.append(title,status,form,label,grant,revoke,fresh,operation,check,out);
li.append(box);

let current=null,candidate=null,version=t.version,pending=null,locked=false;
const reads=latestRead();

function buttons(){for(const b of [lookup,grant,revoke,fresh,check])b.disabled=locked;

grant.disabled=locked||!t.active||(!current?.account_id&&!candidate)||!!pending;

revoke.disabled=locked||!current?.account_id||!!pending;
check.disabled=locked||!operation.value.trim();
}
function load(){return reads.run(async()=>{
const [r,d]=await Promise.all([
 fetch('/api/v1/admin/trainers/'+t.id+'/role'),fetch('/api/v1/admin/trainers/'+t.id)]);
if(!r.ok||!d.ok)throw Error();
return Promise.all([r.json(),d.json()]);
},([role,trainer])=>{
updateTrainer(t,trainer);current=role;version=t.version;
status.textContent=current.account_id?'연결 계정: '+current.login_id+' / '+current.state+
 ' / Trainer 역할 '+(current.granted?'부여됨':'회수됨'):'연결된 계정 없음';
buttons();
});}

async function post(path,body){const c=await fetch('/api/v1/auth/csrf',
 {headers:{'X-Y3-Client':'trainer-role'}});
if(!c.ok)throw Error();

return fetch('/api/v1'+path,{method:'POST',headers:{'Content-Type':'application/json',
 'X-CSRF-Token':(await c.json()).csrf_token},body:JSON.stringify(body)});
}
form.addEventListener('submit',async e=>{e.preventDefault();
if(locked||pending)return;

locked=true;
candidate=null;
confirm.checked=false;
buttons();
try{
const r=await post('/admin/trainers/'+t.id+'/role-account-lookup',{login_id:login.value});

if(!r.ok)throw Error();
candidate=await r.json();

out.textContent='확인할 계정: '+candidate.login_id+' / '+candidate.state+
 (candidate.eligible?' / 선택 가능':' / 현재 연결 불가');

if(!candidate.eligible)candidate=null;

}catch{out.textContent='현재 범위와 정확한 계정을 확인해 주세요.';
}finally{locked=false;
buttons();
}});

async function submit(desired){if(locked||pending)return;
reads.invalidate();

const selected=current?.account_id?current:candidate;
if(!selected)return;

if(!current?.account_id&&!confirm.checked){out.textContent='동일인 확인이 필요합니다.';
return;
}
if(!window.confirm(
 '실제 역할이 변경되면 대상의 모든 로그인이 종료됩니다. 진행하시겠습니까?'
))return;

pending={operation_id:crypto.randomUUID(),account_id:selected.account_id,desired_granted:desired,
 expected_account_version:selected.account_version,expected_role_version:current?.role_version||0,
 expected_trainer_version:version,identity_confirmed:confirm.checked};

operation.value=pending.operation_id;

out.textContent="작업 번호를 보관하세요: "+pending.operation_id;

locked=true;
buttons();
try{const r=await post('/admin/trainers/'+t.id+'/role',pending);

if(!r.ok){out.textContent='변경하지 못했습니다. 작업 결과를 확인한 뒤 새 작업으로 진행해 주세요.';
return;
}
const data=await r.json();
out.textContent=data.changed?'역할 변경 완료: 대상 로그인 종료':'역할이 같아 변경 없음';

if(data.reauthentication_required){location.href='/login';
return;
}await load();
await accountRefresh();

}catch{out.textContent='결과가 불명확합니다. 자동 재시도하지 말고 작업 결과를 확인해 주세요.';
}
finally{locked=false;
buttons();
}}
grant.addEventListener('click',()=>submit(true));
revoke.addEventListener('click',()=>submit(false));

operation.addEventListener('input',buttons);

check.addEventListener('click',async()=>{if(locked)return;
const id=operation.value.trim();

if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)){
 out.textContent='올바른 작업 번호를 입력하세요.';
return;
}locked=true;
buttons();
try{
const r=await fetch('/api/v1/admin/trainer-role-operations/'+encodeURIComponent(id));

if(!r.ok)throw Error();
const data=await r.json();
if(data.current_state.trainer_id!==t.id){
 out.textContent='다른 Trainer의 작업 번호입니다.';return;
}
out.textContent=data.changed?
 '역할 변경 기록 확인':'변경 없는 작업 확인';
await load();
await accountRefresh();

}catch{out.textContent='작업 결과를 확인할 수 없습니다. 현재 권한과 로그인 상태를 확인해 주세요.';
}
finally{locked=false;
buttons();
}});

fresh.addEventListener('click',async()=>{if(locked)return;
pending=null;
candidate=null;

confirm.checked=false;
out.textContent='';
locked=true;
buttons();
try{await load();
}
catch{out.textContent='현재 역할을 확인할 수 없습니다.';
}finally{locked=false;
buttons();
}});

locked=true;
buttons();
load().catch(()=>{out.textContent='현재 역할을 확인할 수 없습니다.';
})
.finally(()=>{locked=false;
buttons();
});

return load;
}
function accountControls(li,t){
const box=document.createElement('div'),status=document.createElement('p');
const form=document.createElement('form'),input=document.createElement('input');
const issue=document.createElement('button'),refresh=document.createElement('button');
const reissue=document.createElement('button'),result=document.createElement('p');
form.method='post';form.action='/trainers';input.autocomplete='off';
input.setAttribute('aria-label','Trainer 로그인 ID');input.required=true;
issue.textContent='계정 발급';refresh.textContent='계정 상태 확인';
reissue.textContent='초기 설정 링크 재발급';refresh.type=reissue.type='button';
issue.disabled=reissue.disabled=true;
form.append(input,issue);box.append(status,form,refresh,reissue,result);li.append(box);
box.dataset.trainer=t.id;
let state=null,pending=null,working=false,link=null;
const reads=latestRead();
function load(){return reads.run(async()=>{const [r,g,d]=await Promise.all([
 fetch('/api/v1/admin/trainers/'+t.id+'/login-account'),
 fetch('/api/v1/admin/trainers/'+t.id+'/role'),fetch('/api/v1/admin/trainers/'+t.id)]);
if(!r.ok||!g.ok||!d.ok)throw Error();
return Promise.all([r.json(),g.json(),d.json()]);
},([account,role,trainer])=>{
updateTrainer(t,trainer);state=account;
if(link){
if(state.state!=='PENDING_SETUP'||!role.granted||state.account_id!==link.account_id||
 state.account_version!==link.version||
 Date.parse(state.initial_setup_expires_at)!==Date.parse(link.expires_at)||
 Date.parse(link.expires_at)<=Date.now()){link=null;result.replaceChildren();}
else{const a=result.querySelector('a');if(a){
 a.textContent=t.active?'본인 비밀번호 설정 링크':'본인 비밀번호 설정 링크 (일시 보류)';
 a.setAttribute('aria-disabled',String(!t.active));
 if(t.active)a.href=link.url;else a.removeAttribute('href');}}
}
status.textContent=state.state?(state.login_id+': '+state.state):'계정 미발급';
issue.disabled=!!state.account_id||!t.active;input.disabled=!!state.account_id;
reissue.disabled=state.state!=='PENDING_SETUP'||!t.active||!role.granted;});}
async function send(kind){if(working)return;working=true;reads.invalidate();refresh.disabled=true;
result.replaceChildren();link=null;
try{if(!pending)pending={kind,body:{operation_id:crypto.randomUUID(),
...(kind==='login-account'?{login_id:input.value}:{expected_account_version:state.account_version})}};
if(pending.kind!==kind){result.textContent='먼저 계정 상태를 확인하세요.';return;}
const c=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'trainer-issue'}});
if(!c.ok)throw Error();
const r=await fetch('/api/v1/admin/trainers/'+t.id+'/'+kind,{method:'POST',
headers:{'Content-Type':'application/json','X-CSRF-Token':(await c.json()).csrf_token},
body:JSON.stringify(pending.body)});
if(!r.ok){result.textContent='처리 결과를 확인하세요 ('+r.status+').';return;}
const data=await r.json();pending=null;
if(data.setup_link){link={url:data.setup_link,expires_at:data.expires_at,
 account_id:data.operation.account_id,version:data.operation.committed_account_version};
const a=document.createElement('a');a.href=data.setup_link;
a.textContent='본인 비밀번호 설정 링크';a.referrerPolicy='no-referrer';result.append(a);
result.append(document.createTextNode(' 만료: '+data.expires_at));}
else result.textContent='이미 처리된 요청입니다. 링크가 필요하면 명시적으로 재발급하세요.';
await load();
}catch{result.textContent='연결을 확인하고 계정 상태 확인을 눌러 주세요.';}
finally{working=false;refresh.disabled=false;}}
form.addEventListener('submit',e=>{e.preventDefault();send('login-account');});
reissue.addEventListener('click',()=>send('initial-setup'));
refresh.addEventListener('click',async()=>{if(working)return;result.replaceChildren();try{
if(pending){const r=await fetch(
'/api/v1/admin/trainer-account-operations/'+pending.body.operation_id);
if(r.ok){pending=null;result.textContent='처리 확인. 링크가 필요하면 재발급하세요.';}
else if(r.status!==404)throw Error();}
await load();}catch{result.textContent='현재 권한과 연결을 확인하세요.';}});
load().catch(()=>{status.textContent='계정 상태를 조회할 수 없습니다.';});
return async(preserve=false)=>{
if(!preserve){reads.invalidate();result.replaceChildren();link=null;}
issue.disabled=reissue.disabled=true;await load();};
}
function resetControls(li,t,refreshPanels){
const box=document.createElement('section');box.dataset.trainerReset=t.id;
const title=document.createElement('h3');title.textContent='계정 비밀번호 재설정';
const status=document.createElement('p'),result=document.createElement('p');
result.dataset.resetResult='';result.setAttribute('role','status');
const label=document.createElement('label'),confirmed=document.createElement('input');
confirmed.type='checkbox';confirmed.dataset.resetIdentity='';
label.append(confirmed,document.createTextNode('본인을 확인했습니다'));
const start=document.createElement('button'),reissue=document.createElement('button');
const refresh=document.createElement('button');
start.dataset.resetStart='';reissue.dataset.resetReissue='';refresh.dataset.resetRefresh='';
start.textContent='비밀번호 재설정 시작';reissue.textContent='비밀번호 재설정 링크 재발급';
refresh.textContent='재설정 상태 확인';
for(const b of [start,reissue,refresh])b.type='button';
box.append(title,status,label,start,reissue,refresh,result);li.append(box);
const reads=latestRead();let current=null,working=false;
function buttons(){
start.disabled=working||!current||current.password_reset_pending||!confirmed.checked;
reissue.disabled=working||!current||!current.password_reset_pending||!confirmed.checked;
refresh.disabled=working;confirmed.disabled=working||!current;}
async function load(){current=null;buttons();
return reads.run(async()=>{
 const r=await fetch('/api/v1/admin/trainers/'+t.id+'/login-account');
 if(!r.ok)throw Error();const account=await r.json();
 if(account.state!=='ACTIVE'||account.account_id===identity.account_id)return null;
 const response=await fetch('/api/v1/admin/accounts/'+account.account_id+'/password-reset');
 if(!response.ok)throw Error();return response.json();
},value=>{current=value;
 status.textContent=current?(current.password_reset_pending?'새 비밀번호 설정 대기':'재설정 가능'):
 'ACTIVE인 다른 연결 계정만 재설정할 수 있습니다.';buttons();});}
async function send(again){if(working||!current||!confirmed.checked)return;
const snapshot=current;working=true;reads.invalidate();result.replaceChildren();buttons();
try{const c=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'trainer-reset'}});
 if(!c.ok)throw Error();const response=await fetch('/api/v1/admin/accounts/'+snapshot.account_id+
 '/password-reset'+(again?'/reissue':''),{method:'POST',
 headers:{'Content-Type':'application/json','X-CSRF-Token':(await c.json()).csrf_token},
 body:JSON.stringify({expected_account_version:snapshot.account_version,
 expected_generation:snapshot.generation,identity_confirmed:true})});
 if(!response.ok)throw Error();const issued=await response.json();
 await refreshPanels();await load();
 if(!current||!current.password_reset_pending||current.account_id!==snapshot.account_id||
 current.generation!==snapshot.generation+1||
 Date.parse(current.expires_at)!==Date.parse(issued.expires_at))throw Error();
 const a=document.createElement('a');a.dataset.resetLink='';a.href=issued.reset_link;
 a.referrerPolicy='no-referrer';a.textContent='본인 비밀번호 재설정 링크';result.append(a);
 result.append(document.createTextNode(' 만료: '+issued.expires_at));
}catch{reads.invalidate();result.replaceChildren();current=null;
try{await refreshPanels();await load();
 result.textContent='현재 상태를 다시 확인했습니다. 필요하면 명시적으로 재발급하세요.';
}catch{current=null;result.textContent='현재 권한과 상태를 확인할 수 없습니다. 다시 조회하세요.';}}

finally{working=false;confirmed.checked=false;buttons();}}
start.addEventListener('click',()=>send(false));reissue.addEventListener('click',()=>send(true));
confirmed.addEventListener('change',buttons);
async function refreshState(){reads.invalidate();result.replaceChildren();confirmed.checked=false;
try{await load();}catch{current=null;
 status.textContent='현재 재설정 상태를 확인할 수 없습니다.';buttons();}}
refresh.addEventListener('click',()=>{if(!working)refreshState();});
buttons();refreshState();return refreshState;
}

function baseControls(li,t){
const owner=identity.account_id,box=document.createElement('section');
box.dataset.baseTrainer=t.id;

const open=document.createElement('button');
open.type='button';
open.textContent='일반 기본급 일정';

open.dataset.baseOpen='';
box.append(open);
li.append(box);
let opened=false;

open.onclick=()=>{if(opened)return;
opened=true;
open.disabled=true;
build();
};

function build(){const panel=document.createElement('div');
panel.dataset.basePanel='';
box.append(panel);

const status=document.createElement('p'),anchor=document.createElement('p'),
 effective=document.createElement('p');

status.dataset.baseStatus='';
effective.dataset.baseEffective='';
anchor.dataset.baseAnchor='';

const basis=document.createElement('input');
basis.setAttribute('aria-label','기준 월');
basis.dataset.baseBasis='';

const start=document.createElement('input');
start.setAttribute('aria-label','일반 기본급 적용 시작 월');
start.dataset.baseStart='';

const amount=document.createElement('input');
amount.setAttribute('aria-label','일반 기본급 예정 금액 (원)');
amount.dataset.baseAmount='';

amount.inputMode='numeric';
const fresh=button('기준 월 조회','baseRefresh');

const create=button('미래 일정 등록','baseCreate'),next=button('일정 다음 페이지','baseNext');

const historyNext=button('기본급 이력 다음 페이지','baseHistoryNext');

const op=document.createElement('input');
op.setAttribute('aria-label','기본급 작업 번호');
op.dataset.baseOperation='';

const check=button('기본급 작업 결과 확인','baseCheck');

const rows=document.createElement('ol'),history=document.createElement('ol'),
 result=document.createElement('p');

rows.dataset.baseRows='';
history.dataset.baseHistory='';
result.dataset.baseResult='';
result.setAttribute('role','status');

panel.append(status,anchor,basis,fresh,effective,start,amount,create,rows,next,history,
 historyNext,op,check,result);

let selection=null,working=false,pending=null,generation=0,highest=0,offset=0,historyOffset=0,
 more=false,historyMore=false;

function button(label,key){const b=document.createElement('button');
b.type='button';
b.textContent=label;
b.dataset[key]='';
return b;
}
function buttons(){for(const b of panel.querySelectorAll('button,input'))b.disabled=working;

create.disabled=working||!selection||!!pending;
next.disabled=working||!selection||!more;

historyNext.disabled=working||!selection||!historyMore;

for(const b of rows.querySelectorAll('button'))b.disabled=working||!selection||!!pending||
 b.dataset.eligible!=='true';
}
async function actor(){const r=await fetch('/api/v1/auth/me');
if(!r.ok)throw Error();
const me=await r.json();

if(me.account_id!==owner||!me.roles.some(r=>r.role==='ADMIN')){generation++;
selection=null;

rows.replaceChildren();
history.replaceChildren();
anchor.textContent=effective.textContent='';
amount.value='';
result.textContent='';
throw Error();
}}
async function get(path){const r=await fetch('/api/v1'+path,
 {headers:{'X-Y3-Expected-Actor':owner}});

if(!r.ok)throw Error();
return r.json();
}
function valid(){return selection&&selection.trainer_version===t.version&&
 selection.home_branch_id===t.home_branch_id;
}
async function load(reset){const mine=++generation;
await actor();

if(reset){offset=historyOffset=0;
}
let q='?basis_month='+encodeURIComponent(basis.value||'0001-01')+'&offset='+offset+'&limit=25';

let h='?offset='+historyOffset+'&limit=25';

if(selection){const token='&expected_base_ledger_version='+selection.base_ledger_version+
 '&expected_server_business_month='+selection.server_business_month;

 if(offset)q+=token+'&expected_basis_month='+selection.basis_month;
if(historyOffset)h+=token;
}
const base='/admin/trainers/'+t.id;

const [page,audit,trainer]=await Promise.all([get(base+'/base-schedule'+q),get(base+
 '/base-schedule-history'+h),get(base)]);

await actor();
if(mine!==generation)return false;

if(page.trainer_version<t.version||page.base_ledger_version<highest||
 trainer.version!==page.trainer_version||
 trainer.home_branch_id!==page.home_branch_id||
 audit.base_ledger_version!==page.base_ledger_version||
 audit.server_business_month!==page.server_business_month)throw Error();

updateTrainer(t,trainer);
highest=page.base_ledger_version;
selection=page;

if(!basis.value){basis.value=page.server_business_month;
return load(true);
}
status.textContent='서버 기준 월: '+page.server_business_month+' / 조회 기준 월: '+page.basis_month;

anchor.textContent='최초 일반 기본급: '+page.anchor.planned_amount_won+'원 / '+
 page.anchor.start_month+' (원본 보존)';

effective.textContent='기준 월 일반 설정: '+
 (page.general_setting? page.general_setting.planned_amount_won+'원 / '+
 page.general_setting.start_month:'없음');

rows.replaceChildren();
for(const item of page.items){const row=document.createElement('li');
row.dataset.baseChange=item.change_id;

const label=document.createElement('span');
label.textContent=item.start_month+' / '+item.planned_amount_won+'원 / '+
 (item.active?'등록 일정':'취소됨 (예정 금액 보존, 적용 금액 아님)');

const input=document.createElement('input');
input.value=item.planned_amount_won;
input.setAttribute('aria-label','수정할 기본급 금액');
input.dataset.baseEditAmount='';

const edit=button('미래 금액 수정','baseEdit'),cancel=button('미래 일정 취소','baseCancel');

edit.dataset.eligible=cancel.dataset.eligible=String(item.cancellable);

edit.onclick=()=>save('edit',item,input.value);
cancel.onclick=()=>{if(confirm(item.start_month+' / '+item.planned_amount_won+
 '원 일정 전체를 취소할까요?'))save('cancel',item);
};

row.append(label,input,edit,cancel);
rows.append(row);
}
history.replaceChildren();
for(const item of audit.items){const row=document.createElement('li');

row.textContent=item.kind+' / '+item.start_month+' / '+item.planned_amount_won+'원 / '+
 item.actor_role+' / '+item.recorded_at;
history.append(row);
}
more=offset+page.items.length<page.total;
historyMore=historyOffset+audit.items.length<audit.total;
buttons();
return true;
}
async function save(kind,item,value){if(working||pending||!valid())return;

const money=kind==='create'?amount.value:value;

if(kind!=='cancel'&&!/^(0|[1-9][0-9]{0,1023})$/.test(money)){
result.textContent='0원 이상 정수원을 입력하세요.';
return;
}
if(kind==='create'&&
 !/^[0-9]{4}-(0[1-9]|1[0-2])$/.test(start.value)){result.textContent='적용 시작 월을 입력하세요.';
return;
}
const body={operation_id:crypto.randomUUID(),
 expected_trainer_version:selection.trainer_version,
 expected_base_ledger_version:selection.base_ledger_version};

if(kind==='create'){body.start_month=start.value;
body.planned_amount_won=money;
}
else{body.expected_change_revision=item.revision;
if(kind==='edit')body.planned_amount_won=money;
}
pending={body,path:'/admin/trainers/'+t.id+'/base-schedule/changes'+(item?'/'+item.change_id+
 '/'+kind:'')};

op.value=body.operation_id;
working=true;
buttons();
try{await actor();
if(!valid())throw Error();

const c=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'base-schedule'}});
if(!c.ok)throw Error();
const nonce=(await c.json()).csrf_token;

await actor();
if(!valid())throw Error();
const r=await fetch('/api/v1'+pending.path,{method:'POST',
 headers:{'Content-Type':'application/json',
 'X-CSRF-Token':nonce,'X-Y3-Expected-Actor':owner},body:JSON.stringify(body)});
if(!r.ok)throw Error();

const data=await r.json();
highest=Math.max(highest,data.current_base_ledger_version);

if(!await load(true))throw Error();
pending=null;
result.textContent=data.changed?'기본급 저장 완료':'동일 금액으로 변경 없음';

}catch{selection=null;
result.textContent='결과가 불명확합니다. 작업 번호로 확인하세요.';
}
finally{working=false;
buttons();
}}
create.onclick=()=>save('create');
fresh.onclick=async()=>{if(working)return;
working=true;
buttons();

try{if(!await load(true))throw Error();
pending=null;
result.textContent='';
}catch{selection=null;
result.textContent='일정을 새로 조회하세요.';
}finally{working=false;
buttons();
}};

check.onclick=async()=>{if(working||!/^[0-9a-f-]{36}$/i.test(op.value))return;
working=true;
buttons();

try{await actor();
const receipt=await get('/admin/trainer-base-operations/'+op.value);
if(receipt.trainer_id!==t.id)throw Error();

highest=Math.max(highest,receipt.current_base_ledger_version);
if(!await load(true))throw Error();
pending=null;

result.textContent='작업 당시 '+receipt.kind+' / '+receipt.committed_change.start_month+' / '+
 receipt.committed_change.planned_amount_won+'원; 현재 일정은 조회 패널 기준';

}catch{selection=null;
result.textContent='현재 권한과 작업 결과를 확인할 수 없습니다.';
}finally{working=false;
buttons();
}};

async function page(kind){if(working||!selection)return;
working=true;
buttons();
if(kind==='history')historyOffset+=25;
else offset+=25;

try{if(!await load(false))throw Error();
}catch{selection=null;
result.textContent='페이지 기준이 바뀌었습니다. 새로 조회하세요.';
}finally{working=false;
buttons();
}}
next.onclick=()=>page('list');
historyNext.onclick=()=>page('history');

load(true).catch(()=>{selection=null;
status.textContent='기본급 일정을 확인할 수 없습니다.';
buttons();
});

addEventListener('pagehide',()=>{generation++;
selection=null;
buttons();
});
buttons();
}}

function compensationControls(li,t){
const owner=identity.account_id,box=document.createElement('section');
box.dataset.compensationTrainer=t.id;
const title=document.createElement('h3');title.textContent='보상 설정';
const status=document.createElement('p'),base=document.createElement('p');
base.dataset.compensationBase='';
const rate=document.createElement('input'),fixed=document.createElement('input');
rate.setAttribute('aria-label','보상 Rate (%)');
fixed.setAttribute('aria-label','보상 Fixed Amount (원)');
rate.inputMode=fixed.inputMode='numeric';rate.dataset.compensationRate='';fixed.dataset.compensationFixed='';
const change=document.createElement('button'),fresh=document.createElement('button');
const check=document.createElement('button'),next=document.createElement('button');
change.textContent='Rate/Fixed 저장';fresh.textContent='보상 새로 조회';
check.textContent='보상 작업 결과 확인';next.textContent='이력 다음 페이지';
change.dataset.compensationChange='';fresh.dataset.compensationRefresh='';
check.dataset.compensationCheck='';next.dataset.compensationNext='';
for(const b of [change,fresh,check,next])b.type='button';
const operation=document.createElement('input');
operation.setAttribute('aria-label','보상 작업 번호');
operation.dataset.compensationOperation='';
const history=document.createElement('ol');history.dataset.compensationHistory='';
const result=document.createElement('p');result.setAttribute('role','status');
result.dataset.compensationResult='';
box.append(title,status,rate,fixed,base,change,fresh,operation,check,history,next,result);li.append(box);
let generation=0,working=false,ready=false,pending=null,selection=null,highest=0;
let offset=0,more=false;
function buttons(){change.disabled=working||!ready||!!pending;
rate.disabled=fixed.disabled=working||!ready||!!pending;
fresh.disabled=check.disabled=operation.disabled=working;next.disabled=working||!ready||!more;}
async function actor(){const r=await fetch('/api/v1/auth/me');if(!r.ok)throw Error();
const me=await r.json();if(me.account_id!==owner||!me.roles.some(r=>r.role==='ADMIN')){
 generation++;ready=false;selection=null;status.textContent='로그인 사용자가 변경되었습니다.';
 rate.value=fixed.value='';base.textContent='';history.replaceChildren();result.textContent='';
 buttons();throw Error();}}
async function get(path){const r=await fetch('/api/v1'+path,
 {headers:{'X-Y3-Expected-Actor':owner}});
if(!r.ok)throw Error();return r.json();}
async function load(){const mine=++generation;ready=false;buttons();await actor();
const [current,page,trainer]=await Promise.all([
 get('/admin/trainers/'+t.id+'/compensation'),
 get('/admin/trainers/'+t.id+'/compensation-history?offset='+offset+'&limit=25'),
 get('/admin/trainers/'+t.id)]);await actor();if(mine!==generation)return false;
if(current.trainer_id!==t.id||current.trainer_version<t.version||
 current.compensation_version<highest||trainer.version!==current.trainer_version||
 trainer.home_branch_id!==current.home_branch_id||page.total!==current.compensation_version){
 selection=null;ready=false;status.textContent='설정이 변경되었습니다. 보상을 새로 조회하세요.';
 buttons();return false;}
updateTrainer(t,trainer);highest=current.compensation_version;selection=current;
rate.value=String(current.rate_percent);fixed.value=current.fixed_amount_won;
base.textContent='최초 일반 기본급 설정: '+current.initial_base_salary_won+'원 / 적용 시작 월: '+
 current.initial_base_salary_start_month+' (이 화면에서는 변경하지 않습니다)';
status.textContent='현재 Rate/Fixed 설정';history.replaceChildren();
for(const item of page.items){const row=document.createElement('li');
row.textContent=(item.before_rate===null?'최초 설정':'변경')+' #'+item.compensation_version+
 ': Rate '+(item.before_rate===null?'없음':item.before_rate)+' → '+item.after_rate+'%, Fixed '+
 (item.before_fixed===null?'없음':item.before_fixed)+' → '+item.after_fixed+'원 / '+
 item.actor_role+' '+item.actor_id+' / '+item.recorded_at;history.append(row);}
more=offset+page.items.length<page.total;ready=true;buttons();return true;}
function validSelection(){return selection&&selection.trainer_version===t.version&&
 selection.home_branch_id===t.home_branch_id&&selection.compensation_version===highest;}
change.addEventListener('click',async()=>{if(working||!ready||pending)return;
if(!validSelection()){ready=false;status.textContent='현재 보상을 새로 조회하세요.';
 buttons();return;}
if(!/^(0|[1-9][0-9]?|100)$/.test(rate.value)||! /^(0|[1-9][0-9]{0,1023})$/.test(fixed.value)){
 result.textContent='Rate는 0~100 정수, Fixed는 0원 이상 정수로 입력하세요.';return;}
const mine=generation;pending={actor:owner,trainer:t.id,body:{operation_id:crypto.randomUUID(),
 rate_percent:Number(rate.value),fixed_amount_won:fixed.value,
 expected_compensation_version:selection.compensation_version,
 expected_trainer_version:selection.trainer_version}};operation.value=pending.body.operation_id;
working=true;buttons();try{await actor();if(mine!==generation||!validSelection())throw Error();
const c=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'compensation'}});
if(!c.ok)throw Error();const nonce=(await c.json()).csrf_token;await actor();
if(mine!==generation||!validSelection())throw Error();
const r=await fetch('/api/v1/admin/trainers/'+pending.trainer+'/compensation',{method:'POST',
 headers:{'Content-Type':'application/json','X-CSRF-Token':nonce,'X-Y3-Expected-Actor':owner},
 body:JSON.stringify(pending.body)});if(!r.ok)throw Error();const data=await r.json();
await actor();if(mine!==generation||data.trainer_id!==t.id)throw Error();
highest=Math.max(highest,data.current_state.compensation_version);
if(!await load())throw Error();
result.textContent=data.changed?'Rate/Fixed 저장 완료':'동일한 설정으로 변경 없음';
}catch{ready=false;result.textContent='결과가 불명확합니다. 작업 번호로 확인하세요.';}
finally{working=false;buttons();}});
check.addEventListener('click',async()=>{if(working)return;const mine=generation;
const id=operation.value.trim();
if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))return;
working=true;buttons();try{await actor();
const data=await get('/admin/trainer-compensation-operations/'+encodeURIComponent(id));
await actor();if(mine!==generation||data.trainer_id!==t.id)throw Error();
highest=Math.max(highest,data.current_state.compensation_version);
if(!await load())throw Error();
result.textContent='작업 당시 Rate/Fixed: '+data.committed_rate_percent+'% / '+
 data.committed_fixed_amount_won+'원; 현재: '+selection.rate_percent+'% / '+
 selection.fixed_amount_won+'원';
}catch{ready=false;result.textContent='현재 권한과 작업 결과를 확인할 수 없습니다.';}
finally{working=false;buttons();}});
async function refresh(reset){if(working)return;working=true;buttons();if(reset)offset=0;
try{if(!await load())throw Error();pending=null;operation.value='';result.textContent='';}
catch{ready=false;rate.value=fixed.value='';base.textContent='';history.replaceChildren();
 result.textContent='현재 보상을 확인할 수 없습니다.';}
finally{working=false;buttons();}}
fresh.addEventListener('click',()=>refresh(true));
next.addEventListener('click',()=>{if(more&&!working){offset+=25;refresh(false);}});
addEventListener('pagehide',()=>{generation++;ready=false;selection=null;buttons();});
load().catch(()=>{ready=false;buttons();status.textContent='현재 보상을 확인할 수 없습니다.';});
}
function homeControls(li,t){
const owner=identity.account_id,box=document.createElement('section');box.dataset.homeTrainer=t.id;
const title=document.createElement('h3');title.textContent='소속 지점 변경';
const status=document.createElement('p'),select=document.createElement('select');
select.setAttribute('aria-label','변경할 소속 지점');select.dataset.homeDestination='';
const change=document.createElement('button'),fresh=document.createElement('button');
const check=document.createElement('button'),operation=document.createElement('input');
const result=document.createElement('p');result.setAttribute('role','status');
result.dataset.homeResult='';
operation.setAttribute('aria-label','소속 변경 작업 번호');operation.dataset.homeOperation='';
change.textContent='소속 변경';fresh.textContent='소속 새로 조회';
check.textContent='소속 작업 결과 확인';
change.dataset.homeChange='';fresh.dataset.homeRefresh='';check.dataset.homeCheck='';
for(const b of [change,fresh,check])b.type='button';
box.append(title,status,select,change,fresh,operation,check,result);li.append(box);
let ready=false,working=false,pending=null,generation=0,selection=null;
const names=new Map();
async function branchName(id){if(names.has(id))return names.get(id);
const r=await fetch('/api/v1/branches/'+encodeURIComponent(id));if(!r.ok)throw Error();
const b=await r.json();names.set(id,b.name);return b.name;}
function buttons(){change.disabled=working||!ready||!!pending;fresh.disabled=working;
check.disabled=working;select.disabled=working||!ready||!!pending;operation.disabled=working;}
async function actor(){const r=await fetch('/api/v1/auth/me');if(!r.ok)throw Error();
const me=await r.json();if(me.account_id!==owner||
 !me.roles.some(r=>r.role==='ADMIN'&&r.scope==='ORGANIZATION')){
 ready=false;generation++;result.textContent='로그인 사용자가 변경되었습니다. 화면을 다시 여세요.';
 buttons();throw Error();}}
async function load(){const mine=++generation;ready=false;buttons();await actor();
const [r,c]=await Promise.all([fetch('/api/v1/admin/trainers/'+t.id),
 fetch('/api/v1/admin/trainer-home-candidates?limit=100')]);
if(!r.ok||!c.ok)throw Error();const current=await r.json();let candidates=(await c.json()).items;
for(let offset=100;candidates.length===offset;offset+=100){
 const next=await fetch('/api/v1/admin/trainer-home-candidates?limit=100&offset='+offset);
 if(!next.ok)throw Error();candidates.push(...(await next.json()).items);}
for(const b of candidates)names.set(b.id,b.name);
const currentName=await branchName(current.home_branch_id);
await actor();if(mine!==generation)return;
if(current.version<t.version){selection=null;ready=false;
 status.textContent='소속 정보가 변경되었습니다. 소속을 새로 조회하세요.';buttons();return;}
updateTrainer(t,current);selection={home:current.home_branch_id,version:current.version};
status.textContent='현재 소속: '+currentName;
select.replaceChildren();
for(const item of candidates){const option=document.createElement('option');
 option.value=item.id;option.textContent=item.name;select.append(option);}
if(!candidates.some(b=>b.id===current.home_branch_id)){
 const option=document.createElement('option');option.value=current.home_branch_id;
 option.textContent=currentName+' (현재 비활성)';select.append(option);}
select.value=current.home_branch_id;ready=true;buttons();}
select.addEventListener('change',()=>{generation++;});
addEventListener('pagehide',()=>{generation++;ready=false;buttons();});
change.addEventListener('click',async()=>{if(working||!ready||pending)return;
if(!selection||selection.version!==t.version||selection.home!==t.home_branch_id){
 ready=false;result.textContent='소속 정보가 변경되었습니다. 소속을 새로 조회하세요.';
 buttons();return;}
const mine=generation;pending={actor:owner,trainer:t.id,body:{operation_id:crypto.randomUUID(),
 destination_home_branch_id:select.value,expected_trainer_version:selection.version}};
operation.value=pending.body.operation_id;working=true;buttons();
try{await actor();if(mine!==generation)throw Error();
const c=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'trainer-home'}});
if(!c.ok)throw Error();const token=(await c.json()).csrf_token;
await actor();if(mine!==generation)throw Error();
const r=await fetch('/api/v1/admin/trainers/'+pending.trainer+'/home',{method:'POST',
 headers:{'Content-Type':'application/json','X-CSRF-Token':token,'X-Y3-Expected-Actor':owner},
 body:JSON.stringify(pending.body)});
if(!r.ok)throw Error();const data=await r.json();await actor();
if(mine!==generation)throw Error();await load();
result.textContent=data.changed?'소속 변경 완료. 작업 번호를 보관하세요.':'소속이 같아 변경 없음';
}catch{ready=false;result.textContent='결과가 불명확합니다. 작업 번호로 확인하세요.';}
finally{working=false;buttons();}});
check.addEventListener('click',async()=>{if(working)return;const mine=generation;
const id=operation.value.trim();
if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))return;
working=true;buttons();try{await actor();
const r=await fetch('/api/v1/admin/trainer-home-operations/'+encodeURIComponent(id),
 {headers:{'X-Y3-Expected-Actor':owner}});if(!r.ok)throw Error();
const data=await r.json();await actor();if(mine!==generation||data.trainer_id!==t.id)throw Error();
const beforeName=await branchName(data.before_home_branch_id);
const committedName=await branchName(data.committed_home_branch_id);
const currentName=await branchName(data.current_state.home_branch_id);
await actor();if(mine!==generation)throw Error();
await load();result.textContent='작업 당시 소속: '+beforeName+' → '+committedName+
 ' / 결과 조회 당시 소속: '+currentName;
}catch{ready=false;result.textContent='현재 권한과 작업 결과를 확인할 수 없습니다.';}
finally{working=false;buttons();}});
fresh.addEventListener('click',async()=>{if(working)return;working=true;buttons();
try{await load();pending=null;operation.value='';result.textContent='';}
catch{ready=false;result.textContent='현재 소속을 확인할 수 없습니다.';}
finally{working=false;buttons();}});
load().catch(()=>{ready=false;buttons();result.textContent='현재 소속을 확인할 수 없습니다.';});
}
function stateControls(li,t,refreshPanels){
const box=document.createElement('section');box.dataset.stateTrainer=t.id;
const status=document.createElement('p'),out=document.createElement('p');
out.setAttribute('role','status');
const change=document.createElement('button'),fresh=document.createElement('button');
const check=document.createElement('button'),operation=document.createElement('input');
operation.setAttribute('aria-label','업무 상태 작업 번호');operation.autocomplete='off';
fresh.textContent='새 상태 작업';check.textContent='상태 작업 결과 확인';
for(const b of [change,fresh,check])b.type='button';
box.append(status,change,fresh,operation,check,out);li.append(box);
let pending=null,locked=false,ready=false;
function buttons(){status.textContent='업무 상태: '+(t.active?'활성':'비활성');
change.textContent=t.active?'Trainer 비활성화':'Trainer 재활성화';
change.disabled=locked||!ready||!!pending;fresh.disabled=locked;check.disabled=locked;
}
async function load(){ready=false;buttons();await refreshPanels();ready=true;buttons();}
async function reconcile(id){const r=await fetch(
 '/api/v1/admin/trainer-state-operations/'+encodeURIComponent(id));
if(!r.ok)throw Error();const data=await r.json();
if(data.trainer_id!==t.id){out.textContent='다른 Trainer의 작업 번호입니다.';return;}
await load();out.textContent=data.changed?'상태 변경 기록 확인':'변경 없는 상태 작업 확인';
}
change.addEventListener('click',async()=>{
if(locked||pending||!ready)return;
pending={operation_id:crypto.randomUUID(),desired_active:!t.active,
 expected_trainer_version:t.version};operation.value=pending.operation_id;
locked=true;buttons();
try{const c=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'trainer-state'}});
if(!c.ok)throw Error();
const r=await fetch('/api/v1/admin/trainers/'+t.id+'/state',{method:'POST',
 headers:{'Content-Type':'application/json','X-CSRF-Token':(await c.json()).csrf_token},
 body:JSON.stringify(pending)});
if(!r.ok)throw Error();await r.json();await load();
out.textContent='업무 상태 처리 완료. 작업 번호를 보관하세요.';
}catch{ready=false;
out.textContent='결과가 불명확합니다. 작업 번호로 결과를 확인해 주세요.';
}finally{locked=false;buttons();}});
check.addEventListener('click',async()=>{if(locked)return;
const id=operation.value.trim();
if(!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)){
 out.textContent='올바른 작업 번호를 입력하세요.';return;}
locked=true;buttons();try{await reconcile(id);}
catch{ready=false;out.textContent='현재 권한과 작업 결과를 확인할 수 없습니다.';}
finally{locked=false;buttons();}});
fresh.addEventListener('click',async()=>{if(locked)return;locked=true;buttons();
try{await load();pending=null;operation.value='';out.textContent='';}
catch{ready=false;out.textContent='현재 상태를 확인할 수 없습니다.';}
finally{locked=false;buttons();}});
load().catch(()=>{ready=false;buttons();out.textContent='현재 상태를 확인할 수 없습니다.';});
}
$('trainer-form').addEventListener('submit',async e=>{e.preventDefault();
if(busy)return;
busy=true;

try{const body={operation_id:operation};
for(const id of ['name','phone','home_branch_id',
'fixed_amount_won','base_salary_won','base_salary_start_month'])body[id]=$(id).value;

if(!/^(0|[1-9][0-9]?)$|^100$/.test($('rate_percent').value))throw Error();

body.rate_percent=Number($('rate_percent').value);

for(const id of ['fixed_amount_won','base_salary_won'])
if(!/^(0|[1-9][0-9]{0,1023})$/.test(body[id]))throw Error();

if(Array.from(body.name).length>200||Array.from(body.phone).length>128)throw Error();

if(!/^[0-9]{4}-(0[1-9]|1[0-2])$/.test(body.base_salary_start_month))throw Error();


const c=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'workforce'}});
if(!c.ok)throw Error();

const r=await fetch('/api/v1/admin/trainers',{method:'POST',
headers:{'Content-Type':'application/json','X-CSRF-Token':(await c.json()).csrf_token},
body:JSON.stringify(body)});

if(!r.ok){
out.textContent=r.status===503?'결과 확인 후 같은 요청으로 재시도하세요.':
'등록할 수 없습니다 ('+r.status+').';
return;
}
const data=await r.json();
out.textContent='등록 확인: '+data.trainer.id+' (계정 미발급)';
await listing();

}catch{out.textContent='입력 또는 현재 인증을 확인하세요.';
}finally{busy=false;
}});

$('status').addEventListener('click',async()=>{try{
const r=await fetch('/api/v1/admin/trainer-registrations/'+operation);
out.textContent=r.ok?'등록 확인: '+(await r.json()).trainer.id:'등록 결과를 확인할 수 없습니다.';
}catch{out.textContent='연결을 확인하세요.';
}});

$('new').addEventListener('click',()=>{if(busy)return;
operation=crypto.randomUUID();

$('trainer-form').reset();
out.textContent='새 등록';
});

async function init(){try{
const me=await fetch('/api/v1/auth/me');if(!me.ok)throw Error();identity=await me.json();
for(let offset=0;;offset+=100){
const r=await fetch('/api/v1/admin/trainer-home-candidates?limit=100&offset='+offset);
if(!r.ok)throw Error();

const candidates=(await r.json()).items;
for(const b of candidates){const o=document.createElement('option');
o.value=b.id;
o.textContent=b.name;
$('home_branch_id').append(o);
}
if(candidates.length<100)break;
}
await listing();
$('fields').disabled=false;
$('submit').disabled=false;
$('status').disabled=false;
$('new').disabled=false;

}catch{out.textContent='현재 관리자 로그인이 필요합니다.';
}}init();
})();
"""


LIFECYCLE_PAGE = """<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>계정 관리</title><link rel="stylesheet" href="/trainers.css">
<h1>계정 관리</h1><form id="lookup" method="post" action="/account-lifecycle">
<label>현재 로그인 ID <input id="identifier" required maxlength="64" autocomplete="off"></label>
<button>정확히 일치하는 계정 조회</button></form>
<p id="state"></p><button id="refresh" disabled>최신 상태 조회</button>
<fieldset id="actions" disabled><legend>계정 변경</legend>
<button id="disable">차단</button><button id="restore">복구</button>
<label>새 로그인 ID <input id="new-id" maxlength="64"></label><button id="rename">ID 변경</button>
<button id="setup">최초 설정 링크 별도 발급</button></fieldset>
<p id="message" role="status"></p><output id="link"></output>
<script src="/account-lifecycle.js"></script></html>"""


LIFECYCLE_SCRIPT = r"""(()=>{
'use strict';
const el=id=>document.getElementById(id),base='/api/v1/admin/account-lifecycle/';
let current=null,target=null,generation=0,writing=false;
function display(account){
 current=account;
 el('link').textContent='';
 el('actions').disabled=writing||!current;
 el('refresh').disabled=writing||!target;
 el('identifier').disabled=writing;
 el('lookup').querySelector('button').disabled=writing;
 const roles=[];
 if(account?.admin_scope)
  roles.push(account.admin_scope.kind==='ORGANIZATION'?'Master':'Branch Admin');
 if(account?.operator_scope)roles.push('Operator');
 if(account?.trainer_granted)roles.push('Trainer');
 el('state').textContent=account?[account.login_id,roles.join(' + ')||'현재 역할 없음',
  account.state,
  account.restore_state?'복구 시 '+account.restore_state:'',
  account.state==='PENDING_SETUP'&&!account.setup_route?'현재 최초 설정 링크 발급 불가':''
 ].filter(Boolean).join(' / '):'';
 el('disable').disabled=!current||current.state==='DISABLED';
 el('restore').disabled=!current||current.state!=='DISABLED';
 el('setup').disabled=!current?.setup_route;
}
async function request(url,method,body){
 const token=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'account-lifecycle'}});
 if(!token.ok)throw Error();
 return fetch(url,{method,headers:{'Content-Type':'application/json',
 'X-CSRF-Token':(await token.json()).csrf_token},body:JSON.stringify(body)});
}
async function read(id){
 const response=await fetch(base+id);if(!response.ok)throw Error();
 const row=await response.json();if(row.account_id!==id)throw Error();return row;
}
async function lookup(refresh){
 if(writing)return;
 const mine=++generation,id=target;
 if(!refresh)target=null;
 el('message').textContent='';display(null);
 try{
  let row;
  if(refresh)row=await read(id);
  else{
   const response=await request(base+'lookup','POST',{login_id:el('identifier').value});
   if(!response.ok)throw Error();row=await response.json();
  }
  if(mine!==generation)return;
  target=row.account_id;display(row);
 }catch{if(mine===generation)el('message').textContent='계정을 확인할 수 없습니다.';}
}
el('lookup').onsubmit=e=>{e.preventDefault();lookup(false);};
el('identifier').oninput=()=>{generation++;target=null;display(null);el('message').textContent='';};
el('refresh').onclick=()=>lookup(true);
async function change(kind){
 if(writing||!current)return;
 const before=current,id=before.account_id,mine=++generation;
 writing=true;display(before);el('message').textContent='';
 let next=null,secret='',message='';
 try{
  const setup=kind==='setup';
  const operator=setup&&before.setup_route.startsWith('/api/v1/admin/operator-accounts/');
  const trainer=setup&&before.setup_route.startsWith('/api/v1/admin/trainers/');
  const body=trainer?{operation_id:crypto.randomUUID(),expected_account_version:before.version}:
   {expected_version:before.version};
  if(operator)body.expected_operator_version=before.operator_scope.version;
  if(kind==='status')body.status='DISABLED';
  if(kind==='login-id')body.login_id=el('new-id').value;
  const response=await request(setup?before.setup_route:'/api/v1/admin/accounts/'+id+'/'+kind,
   setup||kind==='restore'?'POST':'PATCH',body);
  if(!response.ok){
   message=response.status===409?'최신 상태를 확인한 뒤 다시 선택해 주세요.':
    '요청 결과를 확인할 수 없습니다. 현재 상태를 확인해 주세요.';
   next=await read(id);
  }else{
   const applied=await response.json();
   next=await read(id);
   const version=trainer?applied.operation.committed_account_version:applied.version;
   if(setup&&next.version===version&&next.setup_route===before.setup_route&&
      (!operator||(next.operator_scope?.version===applied.operator_scope?.version&&
       next.operator_scope?.branch_id===applied.operator_scope?.branch_id)))
    secret=applied.setup_link||'';
   message=secret?'최초 설정 링크가 발급되었습니다.':'현재 계정 상태를 확인해 주세요.';
  }
 }catch{
  message='요청 결과를 확인할 수 없습니다. 현재 상태를 확인해 주세요.';
  try{next=await read(id);}catch{next=null;}
 }finally{
  if(mine===generation){
   writing=false;display(next);el('message').textContent=message;el('link').textContent=secret;
  }
 }
}
for(const [id,action] of [['disable','status'],['restore','restore'],['rename','login-id'],
 ['setup','setup']])el(id).onclick=()=>change(action);
window.addEventListener('pagehide',()=>{generation++;writing=false;target=null;display(null);});
})();"""

OPERATOR_ACCOUNTS_JS = r"""'use strict';
const form = document.querySelector('form');
const login = document.querySelector('#login');
const branch = document.querySelector('#branch');
const status = document.querySelector('#result');
const delivery = document.querySelector('#delivery');
const base = '/api/v1/admin/operator-accounts';
let generation = 0;
let selected = null;
let writing = false;

function controls() {
  login.disabled = branch.disabled = writing;
  for (const button of form.querySelectorAll('button')) {
    button.disabled = writing ||
      (button.value === 'reissue' && selected?.state !== 'PENDING_SETUP') ||
      (button.value === 'issue' && !branch.value);
  }
}
function clearSelection() {
  generation++;
  selected = null;
  status.textContent = '';
  delivery.replaceChildren();
  controls();
}
function show(account) {
  selected = account;
  status.textContent = account.login_id + ' · ' + account.state + ' · 버전 ' + account.version;
}
async function json(response) {
  if (!response.ok) throw Error();
  return response.json();
}
async function post(url, body) {
  const preparation = await json(await fetch('/api/v1/auth/csrf', {
    headers: {'X-Y3-Client': 'operator'}
  }));
  return json(await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': preparation.csrf_token},
    body: JSON.stringify(body)
  }));
}
async function readAccount(id) {
  const account = await json(await fetch(base + '/' + id));
  if (account.account_id !== id) throw Error();
  return account;
}
function lookup(identifier) {
  return post(base + '/lookup', {login_id: identifier});
}

form.addEventListener('input', clearSelection);
addEventListener('pagehide', () => {
  writing = false;
  clearSelection();
});
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (writing || !event.submitter || event.submitter.disabled) return;
  const action = event.submitter.value;
  const previous = selected;
  const identifier = login.value;
  writing = action !== 'lookup';
  clearSelection();
  const request = generation;
  try {
    if (action === 'lookup') {
      const account = await lookup(identifier);
      if (request === generation) show(account);
      return;
    }
    const result = action === 'issue'
      ? await post(base, {login_id: identifier, branch_id: branch.value})
      : await post(base + '/' + previous.account_id + '/initial-setup', {
          expected_version: previous.version,
          expected_operator_version: previous.operator_scope.version
        });
    if (request !== generation) return;
    const id = action === 'reissue' ? previous.account_id : result.account_id;
    const account = await readAccount(id);
    if (request !== generation) return;
    show(account);
    if (account.account_id === result.account_id && account.version === result.version &&
        account.operator_scope.version === result.operator_scope.version &&
        account.operator_scope.branch_id === result.operator_scope.branch_id &&
        account.state === 'PENDING_SETUP' && result.setup_link) {
      const link = document.createElement('a');
      link.href = result.setup_link;
      link.textContent = '최초 설정 링크';
      delivery.append(link);
    }
  } catch {
    if (request !== generation) return;
    status.textContent = '처리 결과를 확인할 수 없습니다.';
    if (writing) {
      try {
        const current = action === 'reissue'
          ? await readAccount(previous.account_id)
          : await lookup(identifier);
        if (request === generation) {
          show(current);
          status.append(' · 현재 상태입니다. 링크가 필요하면 명시적으로 재발급하세요.');
        }
      } catch {
        // The exact-ID lookup also failed. No secret or prior selection is retained.
      }
    }
  } finally {
    if (request === generation) {
      writing = false;
      controls();
    }
  }
});

async function loadBranches() {
  try {
    for (let offset = 0; ; offset += 100) {
      const page = await json(await fetch('/api/v1/branches?offset=' + offset + '&limit=100'));
      for (const item of page.items) branch.add(new Option(item.name, item.id));
      if (!page.items.length || offset + page.items.length >= page.total) break;
    }
  } catch {
    status.textContent = '지점을 불러올 수 없습니다.';
  }
  controls();
}
loadBranches();
"""

OPERATOR_ROLES_JS = r"""(()=>{'use strict';
const el=id=>document.getElementById('role-'+id),base='/api/v1/admin/operator-roles';
let selected=null,writing=false,generation=0,actor=null,pending=null;
function controls(){
 el('login').disabled=el('branch').disabled=el('destination').disabled=writing;
 el('find').disabled=writing||!actor;
 el('grant').disabled=writing||!selected?.can_grant;
 el('revoke').disabled=writing||!selected?.can_revoke;
 el('move').disabled=writing||!selected?.can_move||!el('destination').value;
 el('reconcile').disabled=writing||!pending||pending.actor!==actor;
}
function show(row){
 selected=row;
 el('current').textContent=row?row.login_id+' · '+row.state+' · '+row.branch_id+
  ' · Operator '+(row.operator_grant?.granted?'유효':'없음')+
  ' · 버전 '+(row.operator_grant?.scope.version||0):'';
 controls();
}
function clear(){generation++;show(null);el('message').textContent='';}
async function json(response){if(!response.ok)throw Error(String(response.status));
 return response.json();}
function invalidateActor(){
 generation++;actor=null;writing=false;savePending(null);show(null);
 el('message').textContent='로그인 계정이 바뀌었습니다. 화면을 새로 열어 주세요.';
}
async function verifyActor(expected,allowSignedOut=false){
 const response=await fetch('/api/v1/auth/me');
 if(response.status===401&&allowSignedOut&&expected&&actor===expected)return;
 const me=await json(response);
 if(!expected||actor!==expected||me.account_id!==expected){invalidateActor();throw Error('actor');}
}
async function post(path,body,expected){
 await verifyActor(expected);
 const csrf=await json(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'operator-role'}}));
 return fetch(path,{method:'POST',headers:{'Content-Type':'application/json',
  'X-CSRF-Token':csrf.csrf_token,'X-Y3-Expected-Actor':expected},body:JSON.stringify(body)});
}
async function current(id,branch,expected){
 await verifyActor(expected);
 return json(await fetch(base+'/'+id+'?branch_id='+encodeURIComponent(branch),
  {headers:{'X-Y3-Expected-Actor':expected}}));
}
el('login').oninput=clear;el('branch').onchange=clear;
el('destination').onchange=controls;
el('lookup').onsubmit=async event=>{
 event.preventDefault();if(writing)return;clear();const mine=generation,owner=actor;
 try{const row=await json(await post(base+'/lookup',
  {login_id:el('login').value,branch_id:el('branch').value},owner));
  await verifyActor(owner);if(mine===generation&&owner===actor)show(row);
 }catch{if(mine===generation)el('message').textContent='현재 관리 가능한 계정을 확인해 주세요.';}
};
function savePending(value){pending=value;
 if(value)sessionStorage.setItem('y3-operator-operation',JSON.stringify(value));
 else sessionStorage.removeItem('y3-operator-operation');controls();}
async function change(action){
 if(writing||!selected)return;
 const before=selected,mine=++generation,owner=actor;
 const body={operation_id:crypto.randomUUID(),expected_account_version:before.account_version,
  expected_operator_version:before.operator_grant?.scope.version||0,
  branch_id:action==='move'?el('destination').value:before.branch_id};
 if(action!=='move')body.desired_granted=action==='grant';
 writing=true;show(null);el('message').textContent='처리 중';
 savePending({operation:body.operation_id,actor:owner,account:before.account_id});
 try{
  const path=base+'/'+before.account_id+(action==='move'?'/branch':'/changes');
  const response=await post(path,body,owner);
  if(mine!==generation)return;
  if(!response.ok){await verifyActor(owner);
   if(mine!==generation)return;
   el('message').textContent=response.status===409?
   '충돌했습니다. 최신 상태를 다시 조회해 주세요.':
   '결과를 확인할 수 없습니다. 재로그인 또는 마지막 요청 확인을 이용해 주세요.';return;}
  const receipt=await response.json();
  await verifyActor(owner,receipt.reauthentication_required);
  if(mine!==generation)return;
  if(receipt.reauthentication_required){
   el('message').textContent='본인 변경이 저장됐습니다. 다시 로그인한 뒤 마지막 요청을 확인하세요.';
   return;
  }
  const row=await current(before.account_id,body.branch_id,owner);
  await verifyActor(owner);
  if(mine!==generation)return;
  show(row);el('message').textContent='요청 결과를 확인했습니다. 표시된 값은 현재 상태입니다.';
 }catch{if(mine===generation)el('message').textContent=
  '응답이 확인되지 않았습니다. 자동 재시도하지 않습니다. 마지막 요청을 확인해 주세요.';
 }finally{if(mine===generation){writing=false;controls();}}
}
el('grant').onclick=()=>change('grant');el('revoke').onclick=()=>change('revoke');
el('move').onclick=()=>change('move');
el('reconcile').onclick=async()=>{
 if(writing||!pending||pending.actor!==actor)return;
 const mine=++generation,owner=actor,saved=pending;writing=true;show(null);
 try{await verifyActor(owner);const receipt=await json(await fetch(
  '/api/v1/admin/operator-role-operations/'+saved.operation,
  {headers:{'X-Y3-Expected-Actor':owner}}));
  await verifyActor(owner);
  if(mine!==generation)return;
  if(pending!==saved||receipt.current.account_id!==saved.account)throw Error();
  show(receipt.current);el('message').textContent='확정 요청 버전 '+receipt.committed_version+
   ' · '+(receipt.changed?'변경 저장':'변경 없음')+' · 위 표시는 현재 상태입니다.';
 }catch{if(mine===generation)el('message').textContent=
  '현재 권한으로 요청 결과를 확인할 수 없습니다. 현재 계정을 조회해 주세요.';
 }finally{if(mine===generation){writing=false;controls();}}
};
addEventListener('pagehide',()=>{generation++;selected=null;writing=false;});
(async()=>{try{
 const me=await json(await fetch('/api/v1/auth/me'));actor=me.account_id;
 for(let offset=0;;offset+=100){
  const page=await json(await fetch('/api/v1/branches?offset='+offset+'&limit=100'));
  for(const branch of page.items){el('branch').add(new Option(branch.name,branch.id));
   el('destination').add(new Option(branch.name,branch.id));}
  if(!page.items.length||offset+page.items.length>=page.total)break;
 }
 try{const saved=JSON.parse(sessionStorage.getItem('y3-operator-operation')||'null');
  if(saved&&saved.actor===actor&&typeof saved.operation==='string'&&typeof saved.account==='string')
   pending=saved;
 }catch{savePending(null);}
 controls();
}catch{el('message').textContent='로그인과 관리 권한을 확인해 주세요.';}})();
})();"""


PRODUCT_PAGE = """<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/trainers.css">
<link rel="stylesheet" href="/products.css">
<title>PT 상품 관리</title>
<h1>PT 상품 관리</h1>
<p>조직 공통 상품 · 판매중단 후에도 정보는 수정할 수 있습니다.</p>
<nav>
<button id="refresh" disabled>목록 새로 조회</button>
<button id="new" disabled>새 상품</button>
</nav>
<p id="list-status">
</p>
<ul id="products">
</ul>
<button id="prev" disabled>이전 목록</button>
<button id="next" disabled>다음 목록</button>
<form id="product-form" method="post" action="/api/v1/admin/products">
<fieldset id="product-fields" disabled>
<legend id="selection">새 상품</legend>
<label>상품명<input id="product-name" required maxlength="200">
</label>
<label>판매가격 (원)<input id="product-price" required
 inputmode="numeric" maxlength="1024" pattern="0|[1-9][0-9]*">
</label>
<label>총횟수<input id="product-count" required
 inputmode="numeric" maxlength="19" pattern="[1-9][0-9]*">
</label>
<label>지급방식<select id="product-type" required>
<option value="">선택</option>
<option value="RATE">비율 지급</option>
<option value="FIXED_AMOUNT">고정금액 지급</option>
</select>
</label>
<label>서비스 상품<select id="product-service" required>
<option value="">선택</option>
<option value="false">일반 상품</option>
<option value="true">서비스 상품</option>
</select>
</label>
<p id="selling">
</p>
<button id="save" disabled>등록</button>
<button id="stop" type="button" disabled>판매중단</button>
</fieldset>
</form>
<p id="product-result" role="status">
</p>
<label>작업번호<input id="product-operation" readonly>
</label>
<button id="check" disabled>작업 결과 대사</button>
<noscript>자바스크립트 사용 후 상품을 관리할 수 있습니다.</noscript>
<script src="/products.js">
</script>"""

PRODUCT_SCRIPT = r"""(()=>{'use strict';

const $=id=>document.getElementById(id),form=$('product-form'),fields=$('product-fields');

const name=$('product-name'),price=$('product-price'),count=$('product-count');
const type=$('product-type');

const service=$('product-service'),out=$('product-result'),rows=$('products');

let owner=null,selected=null,pending=null,busy=false,ready=false,generation=0;
let offset=0,total=0,known=new Map();

const buttons=['save','stop','check'];

async function identity(){const r=await fetch('/api/v1/auth/me');
if(!r.ok)throw Error();
return r.json();
}
function clear(){ready=false;
selected=null;
known.clear();
rows.replaceChildren();
form.reset();
$('selling').textContent='';

 $('selection').textContent='새 상품';
$('save').textContent='등록';
fields.disabled=true;
buttons.forEach(k=>$(k).disabled=true);
}
async function actor(){const me=await identity();

 if(owner!==null&&owner!==me.account_id){owner=me.account_id;
generation++;
clear();

 out.textContent='계정이 변경되었습니다. 새로 조회해 주세요.';
throw Error('actor');
}
 if(!me.capabilities.includes('accounts:manage')){clear();
throw Error('actor');
}
 owner=me.account_id;
return owner;
}
async function api(path,body){const headers={'X-Y3-Expected-Actor':owner};

 if(body){const r=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'catalog'}});

 if(!r.ok)throw Error();
headers['X-CSRF-Token']=(await r.json()).csrf_token;
headers['Content-Type']='application/json';
}
 const r=await fetch('/api/v1'+path,{method:body?'POST':'GET',headers,
...(body?{body:JSON.stringify(body)}:{})});

 if(!r.ok){const e=Error('response');
e.status=r.status;
const data=await r.json().catch(()=>null);
const safe=['conflict','version_exhausted','invalid_request','operation_conflict','actor_changed'];
if(data&&safe.includes(data.detail))e.detail=data.detail;
throw e;
}return r.json();
}
function enable(){fields.disabled=busy||!ready;
const blocked=busy||pending!==null;

 $('save').disabled=blocked||!ready;
$('stop').disabled=blocked||!ready||!selected||!selected.selling;

 $('check').disabled=busy||!pending;
$('refresh').disabled=false;
$('new').disabled=busy||!!pending;

 $('prev').disabled=busy||!!pending||offset===0;
$('next').disabled=busy||!!pending||offset+25>=total;
}
function publish(p){const v=known.get(p.id)||0;
if(p.version<v)return false;

 known.set(p.id,p.version);
ready=true;
selected=p;
name.value=p.values.name;
price.value=p.values.price_won;

 count.value=p.values.session_count;
type.value=p.values.payment_type;
service.value=String(p.values.is_service);

 $('selection').textContent=p.values.name+' · 버전 '+p.version;
$('save').textContent='정보 저장';

 $('selling').textContent=p.selling?'판매 중':'판매중단';
enable();
return true;
}
async function detail(id){const g=++generation;
await actor();
const p=await api('/admin/products/'+id);

 await actor();
if(g!==generation)return false;
return publish(p);
}
async function list(){const g=++generation;
await actor();
const page=await api('/admin/products?offset='+offset+'&limit=25');

 await actor();
if(g!==generation)return false;
rows.replaceChildren();
total=page.total;

 for(const p of page.items){const li=document.createElement('li');
const b=document.createElement('button');

 b.type='button';
b.dataset.product=p.id;
b.textContent=p.values.name+' · '+p.values.price_won+'원 · '+
 p.values.session_count+'회 · '+(p.selling?'판매 중':'판매중단');
b.onclick=()=>{if(!busy&&!pending)detail(p.id).catch(failure);
};

 li.append(b);
rows.append(li);
}
 ready=true;
$('list-status').textContent='전체 '+total+'개 · 이번 요청의 목록';
enable();
return true;
}
function failure(e){if(e.message==='actor')return;

 out.textContent=e.status===409?'정보가 변경되었습니다. 새로 조회해 주세요.':
'처리하지 못했습니다. 새로 조회해 주세요.';
}
function newProduct(){generation++;
ready=true;
selected=null;
form.reset();
$('selection').textContent='새 상품';

 $('save').textContent='등록';
$('selling').textContent='등록하면 판매가 시작됩니다.';
out.textContent='';
enable();
}
async function fresh(result){const g=++generation;
const p=await api('/admin/products/'+result.committed_product.id);

 await actor();
if(g!==generation||!publish(p))return false;

 out.textContent='작업 당시 '+result.kind+' · 버전 '+result.committed_product.version+
 ' · 현재 상품은 새로 조회한 정보입니다.';
return true;
}
async function reconcile(){if(!pending||busy)return;
busy=true;
enable();
const original=pending;

 try{await actor();
if(original.actor!==owner)throw Error('actor');

 let result;try{result=await api('/admin/product-operations/'+original.body.operation_id);}
catch(e){if(e.status!==404)throw e;await actor();
try{result=await api(original.path,original.body);}
catch(retryError){
const refused=(retryError.status===409&&
 ['conflict','version_exhausted'].includes(retryError.detail))||
 (retryError.status===422&&retryError.detail==='invalid_request');
if(!refused)throw retryError;
await actor();
if(original.actor!==owner)throw Error('actor');
pending=null;
generation++;
ready=false;
selected=null;
form.reset();
$('selling').textContent='';
$('selection').textContent=original.product_id?'현재 상품 새로 조회':'새 상품';
$('save').textContent=original.product_id?'정보 저장':'등록';
out.textContent='원 작업이 거부되었습니다. 현재 정보를 확인하고 있습니다.';
try{
const published=original.product_id?await detail(original.product_id):await list();
if(published)out.textContent='원 작업이 거부되었습니다. 현재 정보를 새로 조회했습니다.';
}catch(refreshError){
if(refreshError.message!=='actor')
 out.textContent='원 작업이 거부되었습니다. 현재 정보를 다시 조회해 주세요.';
}
return;
}}

 await actor();
if(await fresh(result)){pending=null;
enable();
}}
 catch(e){if(e.message!=='actor')
out.textContent='작업 결과를 확인하지 못했습니다. 같은 작업번호로 다시 대사해 주세요.';
}
 finally{busy=false;
enable();
}}
async function submit(kind){if(busy||pending)return;
busy=true;
enable();

 try{await actor();
const snap=selected;
if(kind!=='create'&&!snap)throw Error();

 const body={operation_id:crypto.randomUUID()};

 if(kind!=='stop')Object.assign(body,{name:name.value,price_won:price.value,session_count:count.value,
 payment_type:type.value,is_service:service.value==='true'});

 if(kind!=='stop'&&service.value==='')throw Error();

 if(kind!=='create')body.expected_product_version=snap.version;

 const path='/admin/products'+(kind==='create'?'':'/'+snap.id)+(kind==='stop'?'/stop':'');

 pending={actor:owner,body,path,product_id:snap?snap.id:null};
$('product-operation').value=body.operation_id;

 let result;
try{result=await api(path,body);
}catch(e){if(e.status&&e.status<500){pending=null;
throw e;
}
 out.textContent='저장 결과가 불명확합니다. 같은 작업번호로 결과를 대사해 주세요.';
return;
}
 await actor();
if(await fresh(result))pending=null;

 }catch(e){if(pending&&e.message!=='actor')
out.textContent='현재 정보를 확인하지 못했습니다. 같은 작업번호로 결과를 대사해 주세요.';

 else failure(e);
}finally{busy=false;
enable();
}}
form.addEventListener('submit',e=>{e.preventDefault();
submit(selected?'update':'create');
});

$('stop').onclick=()=>{if(selected&&confirm(selected.values.name+' 상품의 판매를 중단할까요?'))
submit('stop');
};

$('check').onclick=reconcile;

$('refresh').onclick=()=>{const id=selected?.id;
const keep=pending;
clear();
pending=keep;

 list().then(published=>published&&id?detail(id):undefined).catch(failure);
};

$('new').onclick=()=>{if(pending||busy)return;
actor().then(newProduct).catch(failure);
};

$('prev').onclick=()=>{offset=Math.max(0,offset-25);
clear();
list().catch(failure);
};

$('next').onclick=()=>{offset+=25;
clear();
list().catch(failure);
};

service.onchange=()=>{if(service.value==='true')type.value='FIXED_AMOUNT';
};

actor().then(()=>{newProduct();
return list();
}).catch(failure);

})();
"""


MEMBER_STYLE = """
body{font-family:system-ui,sans-serif;max-width:860px;margin:auto;padding:16px;
box-sizing:border-box}
*{box-sizing:border-box}nav{display:flex;flex-wrap:wrap;gap:12px}
input,select,button{max-width:100%;font:inherit}
label{display:block;margin:12px 0}
input,select{display:block;width:100%;padding:8px}
button{padding:8px;margin:4px;white-space:normal;overflow-wrap:anywhere}
#members button{display:block;width:100%;text-align:left;margin:4px 0}
p,li,#selection{overflow-wrap:anywhere}
fieldset{min-width:0}
"""


MEMBER_PAGE = """<!doctype html>
<html lang="ko">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>회원 관리</title>
<link rel="stylesheet" href="/members.css">
<nav>
<a href="/branches">지점</a>
<a href="/trainers">트레이너</a>
<a href="/members">회원</a>
<a href="/products">상품</a>
<a href="/account">내 계정</a>
</nav>
<h1>회원 기본관리</h1>
<p>현재 관리할 수 있는 회원의 이름과 국내 휴대전화 번호를 관리합니다.</p>
<button id="new">새 회원</button>
<button id="refresh">목록 새로고침</button>
<div id="members">
</div>
<button id="prev">이전</button>
<button id="next">다음</button>
<p id="page">
</p>
<p id="selection">
</p>
<form id="form">
<fieldset id="fields">
<legend>회원 정보</legend>
<label>이름<input id="name" maxlength="200" required autocomplete="off">
</label>
<label>휴대전화<input id="phone" type="tel" maxlength="64" required autocomplete="off"
placeholder="010-2000-0000">
</label>
<label>등록 Home Branch<select id="home" required>
</select>
</label>
<button id="save" type="submit">등록</button>
</fieldset>
</form>
<button id="deactivate">비활성화</button>
<button id="reactivate">재활성화</button>
<p id="operation">
</p>
<button id="reconcile">저장 결과 확인</button>
<p id="message" role="status">
</p>
<script src="/members.js" defer>
</script>
</html>"""

MEMBER_SCRIPT = r"""'use strict';

(()=>{
const $=id=>document.getElementById(id);

let owner=null,nonce=null,invalid=false,generation=0,selected=null,pending=null;

let busy=false,ready=false,offset=0,total=0,canState=false,roles=[];

function scope(me){return JSON.stringify([me.account_id,me.organization_id,
 me.roles.filter(r=>r.role==='ADMIN'||r.role==='OPERATOR')]);
}
async function json(response){let value;
try{value=await response.json();
}catch{throw Error('network');
}
 if(!response.ok){const e=Error('request');
e.status=response.status;
e.detail=value.detail;
throw e;
}return value;
}
function clearSelection(){selected=null;
ready=false;
$('form').reset();
$('selection').textContent='';
$('home').disabled=false;
}
function invalidate(){invalid=true;
generation++;
owner=null;
nonce=null;
pending=null;
busy=false;

 clearSelection();
$('members').replaceChildren();
$('home').replaceChildren();
$('operation').textContent='';
$('page').textContent='';

 $('message').textContent='로그인 또는 관리 범위가 변경되었습니다. 페이지를 다시 열어 주세요.';
controls();
}
async function actor(){if(invalid)throw Error('actor');

 const me=await json(await fetch('/api/v1/auth/me'));

 const token=await json(await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'membership'}}));

 const current=await json(await fetch('/api/v1/auth/me'));

 const stamp=scope(current);

 if(scope(me)!==stamp||
 !current.roles.some(r=>r.role==='ADMIN'||r.role==='OPERATOR')){invalidate();
throw Error('actor');
}
 if(owner===null){owner={id:current.account_id,stamp};
nonce=token.csrf_token;
}
 else if(owner.stamp!==stamp||nonce!==token.csrf_token){invalidate();
throw Error('actor');
}
 roles=current.roles;

 canState=roles.some(r=>r.role==='ADMIN'&&(r.scope==='ORGANIZATION'||r.branch_id===selected?.home_branch_id));

 return current;

}
async function api(path,body){await actor();
if(invalid||!owner)throw Error('actor');

 const headers={'X-Y3-Expected-Actor':owner.id};

 if(body){headers['Content-Type']='application/json';
headers['X-CSRF-Token']=nonce;
}
 return json(await fetch('/api/v1/admin'+path,{
 method:body?'POST':'GET',headers,...(body?{body:JSON.stringify(body)}:{})}));
}
function controls(){const locked=invalid||busy||!!pending;

 $('fields').disabled=locked||!ready;
$('save').textContent=selected?'저장':'등록';

 $('home').disabled=!!selected||locked;

 $('new').disabled=locked;
$('refresh').disabled=locked;
$('prev').disabled=locked||offset===0;
$('next').disabled=locked||offset+25>=total;

 $('deactivate').hidden=!selected||!canState||!selected.active;

 $('reactivate').hidden=!selected||!canState||selected.active;

 $('deactivate').disabled=locked;
$('reactivate').disabled=locked;
$('reconcile').disabled=invalid||busy||!pending;

}
function publish(member){
 if(selected&&selected.id===member.id&&selected.version>member.version)return false;

 selected=member;
ready=true;

 canState=roles.some(r=>r.role==='ADMIN'&&
 (r.scope==='ORGANIZATION'||r.branch_id===member.home_branch_id));
$('name').value=member.values.name;
$('phone').value=member.values.phone;

 $('home').replaceChildren(new Option(member.home_branch_name,member.home_branch_id));

 $('selection').textContent=`${member.values.name} · ${member.active?'활성 회원':'비활성 회원'}`+
 ` · Home ${member.home_branch_name} (${member.home_active?'활성':'비활성'}) · v${member.version}`;

 controls();
return true;
}
async function detail(id){const g=++generation;
clearSelection();
controls();

 const member=await api('/members/'+id);
await actor();
if(g!==generation||invalid)return false;

 publish(member);
await actor();
controls();
return true;
}
async function list(){const g=++generation;
clearSelection();
controls();

 const page=await api('/members?offset='+offset+'&limit=25');
await actor();
if(g!==generation||invalid)return false;

 total=page.total;
$('members').replaceChildren();
for(const m of page.items){const b=document.createElement('button');
b.type='button';

 b.textContent=`${m.values.name} · ${m.values.phone} · ${m.home_branch_name}`+
 ` · ${m.active?'활성':'비활성'}`;

 b.onclick=()=>{if(!busy&&!pending)detail(m.id).catch(failure);
};
$('members').append(b);
}
 $('page').textContent=`${total}명 · ${Math.floor(offset/25)+1}쪽`;
controls();
return true;
}
async function newMember(){const g=++generation;
clearSelection();
controls();

 const branches=[];

 for(let start=0;;start+=100){
 const page=await api('/member-branches?offset='+start+'&limit=100');

 await actor();
if(g!==generation||invalid)return;

 branches.push(...page);
if(page.length<100)break;

 }
 $('home').replaceChildren(new Option('Home Branch 선택',''),
 ...branches.map(b=>new Option(b.name,b.id)));

 ready=branches.length>0;
controls();
}
function failure(e){if(e.message==='actor')return;

 if(e.status===401||e.status===403){invalidate();
return;
}
 $('message').textContent=pending?
 '저장 결과가 확인되지 않았습니다. 같은 작업번호로 확인해 주세요.':
 '현재 관리할 수 있는 정보를 다시 조회해 주세요.';
controls();
}
function known(e){return (e.status===409&&
 ['conflict','operation_conflict','version_exhausted','branch_inactive'].includes(e.detail))||
 (e.status===422&&['invalid_request','Invalid request'].includes(e.detail));
}
async function fresh(result){const g=++generation;

 const member=await api('/members/'+result.current_member.id);
await actor();
if(g!==generation||invalid)return false;

 return publish(member);
}
async function rejected(original){await actor();
if(pending!==original||invalid)return;

 pending=null;
$('operation').textContent='';
generation++;
clearSelection();

 if(original.id)await detail(original.id);
else await newMember();

 $('message').textContent='변경이 적용되지 않았습니다. 현재값을 확인한 뒤 다시 저장해 주세요.';
}
async function reconcile(){if(!pending||busy||invalid)return;

 const original=pending;
busy=true;
controls();

 try{await actor();
if(!owner||original.stamp!==owner.stamp)throw Error('actor');

 let result;
try{result=await api('/member-operations/'+original.body.operation_id);
}
 catch(e){if(e.status!==404)throw e;

 try{result=await api(original.path,original.body);
}catch(retry){if(known(retry)){await rejected(original);
return;
}throw retry;
}}
 await actor();
if(pending!==original||invalid)return;

 if(await fresh(result)){pending=null;
$('operation').textContent='';
$('message').textContent='원래 저장 결과를 확인하고 현재값을 조회했습니다.';
}
 }catch(e){failure(e);
}finally{busy=false;
controls();
}}
async function submit(kind){if(busy||pending||invalid||!ready)return;

 const snap=selected;
busy=true;
controls();

 try{await actor();
const body={operation_id:crypto.randomUUID()};
let path='/members';

 if(kind==='create'){body.name=$('name').value;
body.phone=$('phone').value;
body.home_branch_id=$('home').value;
}
 else{if(!snap)throw Error('selection');
path+='/'+snap.id;
body.expected_member_version=snap.version;

 if(kind==='update'){body.name=$('name').value;
body.phone=$('phone').value;
}else path+='/'+kind;
}
 if(invalid||!owner)return;

 pending={body,path,id:snap?.id||null,stamp:owner.stamp};
const original=pending;

 $('operation').textContent='작업번호: '+body.operation_id;

 let result;
try{result=await api(path,body);
}catch(e){if(known(e)){await rejected(original);
return;
}throw e;
}
 await actor();
if(pending!==original||invalid)return;

 if(await fresh(result)){pending=null;
$('operation').textContent='';
$('message').textContent=result.changed?'저장했습니다.':'변경된 정보가 없습니다.';
}
 }catch(e){failure(e);
}finally{busy=false;
controls();
}}
$('form').onsubmit=e=>{e.preventDefault();
submit(selected?'update':'create');
};

$('deactivate').onclick=()=>submit('deactivate');
$('reactivate').onclick=()=>submit('reactivate');

$('reconcile').onclick=reconcile;
$('new').onclick=()=>{newMember().catch(failure);
};

$('refresh').onclick=()=>{list().catch(failure);
};

for(const [id,d] of [['prev',-25],['next',25]])$(id).onclick=()=>{if(busy||pending)return;
offset=Math.max(0,offset+d);
list().catch(failure);
};

addEventListener('pagehide',invalidate);

actor().then(list).then(newMember).catch(failure);
controls();

})();
"""
