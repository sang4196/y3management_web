"""Strict same-origin HTTPS adapters. No database authentication in dependencies."""

import json
from dataclasses import asdict
from typing import Annotated, Literal, cast
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, FastAPI, Query, Request
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
    Ceremony,
    EmergencySnapshot,
    HandoffRequest,
    Setup,
    TrainerRoleRequest,
)
from y3management.use_cases import Service
from y3management.workforce.public import RegisterTrainer, TrainerStateRequest

AUTH = "__Host-y3-auth"
PREAUTH = "__Host-y3-preauth"
CEREMONY = "__Host-y3-ceremony"


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


class TrainerAccountInput(Input):
    operation_id: UUID
    login_id: str = Field(min_length=3, max_length=64)


class TrainerSetupInput(Input):
    operation_id: UUID
    expected_account_version: int = Field(strict=True, ge=1)


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
    key_set_version: int = Field(ge=0, strict=True)
    reset_generation: int = Field(ge=0, strict=True)
    recovery_generation: int = Field(ge=0, strict=True)
    password_reset_pending: bool = Field(strict=True)
    recovery_pending: bool = Field(strict=True)
    password_ready: bool = Field(strict=True)
    key_ready: bool = Field(strict=True)


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


class Enrollment(Input):
    setup_token: str = Field(min_length=40, max_length=128, repr=False)
    new_password: str | None = Field(default=None, min_length=1, max_length=512, repr=False)


class PasskeyResponse(Input):
    credential: dict[str, object] = Field(repr=False)


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


class KeyVersion(Input):
    expected_key_set_version: int = Field(ge=0, strict=True)


class RecoveryRequest(KeyVersion):
    expected_account_version: int = Field(gt=0, strict=True)
    identity_confirmed: bool = Field(strict=True)


class ResetRequest(Input):
    expected_account_version: int = Field(gt=0, strict=True)
    expected_generation: int = Field(ge=0, strict=True)
    identity_confirmed: bool = Field(strict=True)


class ResetComplete(Input):
    reset_token: str = Field(min_length=40, max_length=128, repr=False)
    new_password: str = Field(min_length=1, max_length=512, repr=False)


class RecoveryToken(Input):
    recovery_token: str = Field(min_length=40, max_length=128, repr=False)


class EmergencyToken(Input):
    emergency_token: str = Field(min_length=40, max_length=128, repr=False)


class EmergencyOptions(EmergencyToken):
    new_password: str | None = Field(default=None, min_length=1, max_length=512, repr=False)


class EmergencyPassword(EmergencyToken):
    new_password: str = Field(min_length=1, max_length=512, repr=False)


class Access(Version):
    branch_id: UUID


class LoginIDChange(Version):
    login_id: str = Field(min_length=3, max_length=64, strict=True)


class Disable(Version):
    status: Literal["DISABLED"]


def account_json(account: Account) -> dict[str, object]:
    return {
        "account_id": str(account.id),
        "login_id": account.login_id,
        "state": account.state,
        "version": account.version,
        "admin_scope": {
            "kind": "ORGANIZATION" if account.master else "BRANCH",
            "branch_id": str(account.branch_id) if account.branch_id else None,
        },
    }


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
        token = service(request).login_entry(
            body.login_id, body.password, request.cookies.get(PREAUTH), nonce, auth
        )
        if isinstance(token, Ceremony):
            return ceremony_response(token)
        response = Response(status_code=204)
        cookie(response, AUTH, token)
        clear(response, PREAUTH)
        return response

    def ceremony_response(result: Ceremony) -> JSONResponse:
        response = JSONResponse(
            {
                "publicKey": json.loads(result.options_json),
                "csrf_token": result.csrf,
                "expires_at": result.expires_at.isoformat(),
            }
        )
        cookie(response, CEREMONY, result.token)
        clear(response, PREAUTH)
        return response

    @router.post("/auth/passkeys/enrollment/options")
    def enrollment_options(request: Request, body: Enrollment) -> Response:
        _, nonce = write(request)
        return ceremony_response(
            service(request).begin_enrollment(
                body.setup_token, body.new_password, request.cookies.get(PREAUTH), nonce
            )
        )

    @router.get("/auth/passkeys")
    def passkey_list(request: Request) -> dict[str, object]:
        return asdict(service(request).passkeys(read(request)))

    @router.delete("/auth/passkeys/{key_id}")
    def passkey_delete(request: Request, key_id: UUID, body: KeyVersion) -> Response:
        auth, nonce = write(request)
        service(request).delete_passkey(auth, nonce, key_id, body.expected_key_set_version)
        response = Response(status_code=204)
        for name in (AUTH, PREAUTH, CEREMONY):
            clear(response, name)
        return response

    @router.post("/auth/passkeys/recovery/options")
    def recovery_options(request: Request, body: RecoveryToken) -> Response:
        _, nonce = write(request)
        return ceremony_response(
            service(request).begin_recovery(
                body.recovery_token, request.cookies.get(PREAUTH), nonce
            )
        )

    @router.post("/auth/passkeys/recovery/verify")
    def recovery_verify(request: Request, body: PasskeyResponse) -> Response:
        auth, nonce = write(request)
        service(request).register_passkey(
            request.cookies.get(CEREMONY),
            nonce,
            json.dumps(body.credential),
            auth,
            additional=False,
            recovery=True,
        )
        response = Response(status_code=204)
        for name in (AUTH, PREAUTH, CEREMONY):
            clear(response, name)
        return response

    @router.post("/auth/passkeys/options")
    def additional_options(request: Request) -> Response:
        auth, nonce = write(request)
        return ceremony_response(service(request).begin_passkey(auth, nonce))

    @router.post("/auth/passkeys/enrollment/verify")
    def enrollment_verify(request: Request, body: PasskeyResponse) -> Response:
        auth, nonce = write(request)
        service(request).register_passkey(
            request.cookies.get(CEREMONY),
            nonce,
            json.dumps(body.credential),
            auth,
            additional=False,
        )
        response = Response(status_code=204)
        clear(response, CEREMONY)
        return response

    @router.post("/auth/passkeys/verify")
    def additional_verify(request: Request, body: PasskeyResponse) -> Response:
        auth, nonce = write(request)
        service(request).register_passkey(
            request.cookies.get(CEREMONY), nonce, json.dumps(body.credential), auth, additional=True
        )
        response = Response(status_code=204)
        clear(response, CEREMONY)
        return response

    @router.post("/auth/login/passkey/verify")
    def login_verify(request: Request, body: PasskeyResponse) -> Response:
        _, nonce = write(request)
        raw = service(request).finish_mfa_login(
            request.cookies.get(CEREMONY), nonce, json.dumps(body.credential)
        )
        response = Response(status_code=204)
        cookie(response, AUTH, raw)
        clear(response, CEREMONY)
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

    @router.post("/auth/emergency-recovery/options")
    def emergency_options(request: Request, body: EmergencyOptions) -> Response:
        _, nonce = write(request)
        return ceremony_response(
            service(request).emergency_begin(
                body.emergency_token,
                body.new_password,
                request.cookies.get(AUTH),
                request.cookies.get(PREAUTH),
                nonce,
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
        clear(response, PREAUTH)
        return response

    @router.post("/auth/emergency-recovery/verify", status_code=204)
    def emergency_verify(request: Request, body: PasskeyResponse) -> Response:
        _, nonce = write(request)
        service(request).emergency_complete(
            request.cookies.get(CEREMONY),
            nonce,
            json.dumps(body.credential),
            request.cookies.get(AUTH),
        )
        response = Response(status_code=204)
        clear(response, CEREMONY)
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
        for name in (AUTH, PREAUTH, CEREMONY):
            clear(response, name)
        return response

    @router.get("/admin/accounts/{ident}/passkey-recovery")
    def recovery_state(request: Request, ident: UUID) -> dict[str, object]:
        return asdict(service(request).recovery_state(read(request), ident))

    def recover_result(
        request: Request, ident: UUID, body: RecoveryRequest, *, reissue: bool
    ) -> dict[str, object]:
        auth, nonce = write(request)
        result = service(request).recover(
            auth,
            nonce,
            ident,
            body.expected_account_version,
            body.expected_key_set_version,
            body.identity_confirmed,
            reissue=reissue,
        )
        return {
            "recovery_link": settings.canonical_origin + "/recover#token=" + result.token,
            "expires_at": result.expires_at.isoformat(),
        }

    @router.post("/admin/accounts/{ident}/passkey-recovery", status_code=201)
    def recover(request: Request, ident: UUID, body: RecoveryRequest) -> dict[str, object]:
        return recover_result(request, ident, body, reissue=False)

    @router.post("/admin/accounts/{ident}/passkey-recovery/reissue", status_code=201)
    def recover_reissue(request: Request, ident: UUID, body: RecoveryRequest) -> dict[str, object]:
        return recover_result(request, ident, body, reissue=True)

    @router.post("/admin/accounts", status_code=201)
    def issue(request: Request, body: Issue) -> dict[str, object]:
        auth, nonce = write(request)
        return issued(service(request).issue(auth, nonce, body.login_id, body.branch_id))

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

    app.include_router(router)

    @app.get("/trainer-activate", response_class=HTMLResponse)
    def trainer_activation_page(request: Request) -> str:
        return """<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>최초 비밀번호 설정</title>
<h1>최초 비밀번호 설정</h1><form id="trainer-setup" method="post" action="/trainer-activate">
<label>새 비밀번호
<input id="new-password" type="password" autocomplete="new-password" required></label>
<button disabled>설정</button></form><p id="result" role="status"></p><a href="/login">로그인</a>
<script src="/trainer-account.js"></script></html>"""

    @app.get("/account", response_class=HTMLResponse)
    def self_account_page(request: Request) -> str:
        service(request).principal(read(request))
        return """<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>내 계정</title>
<h1>내 계정</h1><pre id="identity"></pre><form id="self-password" method="post" action="/account">
<label>현재 비밀번호
<input id="current-password" type="password" autocomplete="current-password" required></label>
<label>새 비밀번호
<input id="new-password" type="password" autocomplete="new-password" required></label>
<button disabled>비밀번호 변경</button></form><button id="signout" disabled>로그아웃</button>
<p id="result" role="status"></p><script src="/trainer-account.js"></script></html>"""

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
form.addEventListener('submit',async e=>{e.preventDefault();
form.querySelector('button').disabled=true;
try{const password=document.getElementById('new-password').value;
if(form.id==='trainer-setup'){await post('/auth/trainer-credentials/complete',
{setup_token:setupToken,new_password:password});setupToken=null;form.hidden=true;
out.textContent='설정했습니다. 로그인해 주세요.';}
else{await post('/auth/password',
{current_password:document.getElementById('current-password').value,
new_password:password});location.href='/login';}
}catch{out.textContent='처리하지 못했습니다. 현재 상태와 입력을 확인해 주세요.';}
finally{form.querySelector('button').disabled=false;}});
form.querySelector('button').disabled=false;
const logout=document.getElementById('signout');if(logout){logout.disabled=false;
logout.addEventListener('click',async()=>{try{await post('/auth/logout',{});location.href='/login';}
catch{out.textContent='로그아웃하지 못했습니다.';}});
fetch('/api/v1/auth/me').then(async r=>{if(!r.ok)throw Error();
document.getElementById('identity').textContent=JSON.stringify(await r.json(),null,2);})
.catch(()=>{out.textContent='로그인이 필요합니다.';});}
""",
            media_type="application/javascript",
        )

    @app.get("/activate", response_class=HTMLResponse)
    def activation_page(request: Request) -> str:
        read(request)
        if settings.iam_mode == "mfa":
            return mfa_page("setup")
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

    def mfa_page(flow: str) -> str:
        return f"""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="/trainers.css"><title>Y3 인증</title>
<body data-flow="{flow}"><form id="mfa">
<label>로그인 ID <input id="identifier" autocomplete="username"></label>
<label>비밀번호 <input id="password" type="password" autocomplete="current-password"></label>
<button>계속</button></form><ul id="keys"></ul><p id="result"></p>
<script src="/mfa.js"></script></body>"""

    @app.get("/enroll", response_class=HTMLResponse)
    def enroll_page(request: Request) -> str:
        read(request)
        return mfa_page("install")

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request) -> str:
        read(request)
        return mfa_page("login")

    @app.get("/passkeys", response_class=HTMLResponse)
    def keys_page(request: Request) -> str:
        read(request)
        return mfa_page("add").replace(
            '<ul id="keys">',
            "<p>삭제하면 서비스에 등록된 Passkey가 해제되고 현재 기기를 포함한 "
            "모든 로그인이 종료됩니다. 남은 Passkey로 다시 로그인해야 합니다.</p>"
            '<ul id="keys">',
        )

    @app.get("/reset", response_class=HTMLResponse)
    def reset_page(request: Request) -> str:
        read(request)
        return mfa_page("reset")

    @app.get("/recover", response_class=HTMLResponse)
    def recovery_page(request: Request) -> str:
        read(request)
        return mfa_page("recovery")

    @app.get("/emergency-recover", response_class=HTMLResponse)
    def emergency_page(request: Request) -> str:
        read(request)
        return mfa_page("emergency").replace(
            '<ul id="keys">',
            '<p>승인된 인증요인을 준비한 뒤 별도로 로그인해 주세요.</p><ul id="keys">',
        )

    @app.get("/mfa.js")
    def mfa_script(request: Request) -> Response:
        read(request)
        return Response(MFA_SCRIPT, media_type="application/javascript")


MFA_SCRIPT = r"""(()=>{'use strict';
let token=new URLSearchParams(location.hash.slice(1)).get('token');
history.replaceState(null,'',location.pathname);
const flow=document.body.dataset.flow;
const form=document.getElementById('mfa'),out=document.getElementById('result');
const id=document.getElementById('identifier'),pw=document.getElementById('password');
id.parentElement.hidden=flow!=='login';
pw.parentElement.hidden=!['login','setup','reset','emergency'].includes(flow);
if(['setup','reset','emergency'].includes(flow))pw.autocomplete='new-password';
const decode=s=>Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
const encode=b=>btoa(String.fromCharCode(...new Uint8Array(b)))
.replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
async function post(path,csrf,body){const r=await fetch('/api/v1'+path,{method:'POST',
headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(body)});
if(!r.ok)throw Error();return r;}
async function listKeys(){
if(flow!=='add')return;
const response=await fetch('/api/v1/auth/passkeys',{headers:{'X-Y3-Client':'mfa'}});
if(!response.ok){out.textContent='다시 로그인해 주세요.';return;}
const snapshot=await response.json(),list=document.getElementById('keys');list.replaceChildren();
for(const item of snapshot.items){
const li=document.createElement('li'),button=document.createElement('button');
li.textContent='등록: '+item.created_at+' ';button.textContent='삭제';
button.disabled=snapshot.items.length<2;
button.addEventListener('click',async()=>{button.disabled=true;
try{const p=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'mfa'}});
if(!p.ok)throw Error();const nonce=(await p.json()).csrf_token;
const r=await fetch('/api/v1/auth/passkeys/'+item.key_id,{method:'DELETE',
headers:{'Content-Type':'application/json','X-CSRF-Token':nonce},
body:JSON.stringify({expected_key_set_version:snapshot.key_set_version})});
if(!r.ok)throw Error();list.replaceChildren();form.hidden=true;
out.textContent='키를 삭제하고 모든 로그인을 종료했습니다. 남은 키로 다시 로그인해 주세요.';
}catch{out.textContent='삭제할 수 없습니다. 다시 로그인하여 목록을 확인해 주세요.';}});
li.append(button);list.append(li);}}
listKeys().catch(()=>{out.textContent='목록을 불러올 수 없습니다.';});
if(flow==='emergency'){
form.querySelector('button').disabled=true;
(async()=>{try{
const p=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'mfa'}});
if(!p.ok)throw Error();const csrf=(await p.json()).csrf_token;
const info=await (await post('/auth/emergency-recovery/inspect',csrf,
{emergency_token:token})).json();
pw.parentElement.hidden=info.factors==='passkey';
form.querySelector('button').disabled=false;
}catch{form.hidden=true;out.textContent='설정 링크를 확인하거나 먼저 로그아웃해 주세요.';}})();}

form.addEventListener('submit',async e=>{e.preventDefault();
form.querySelector('button').disabled=true;
try{
const p=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'mfa'}});if(!p.ok)throw Error();
const csrf=(await p.json()).csrf_token;
let emergencyFactors=null;
if(flow==='emergency'){
const info=await (await post('/auth/emergency-recovery/inspect',csrf,
{emergency_token:token})).json();
emergencyFactors=info.factors;
if(emergencyFactors==='password'){
await post('/auth/emergency-recovery/password/complete',csrf,
{emergency_token:token,new_password:pw.value});
token=null;form.hidden=true;
out.textContent='복구했습니다. 새 비밀번호와 Passkey로 로그인해 주세요.';return;}}
if(flow==='reset'){
await post('/auth/password-reset/complete',csrf,{reset_token:token,new_password:pw.value});
token=null;form.hidden=true;
out.textContent='비밀번호를 설정했습니다. 다시 로그인해 주세요. '+
 '관리자 역할이 있으면 기존 Passkey 인증도 필요합니다. '+
 '계정·역할·Trainer 상태에 따른 이용 제한은 유지됩니다.';
return;}
const path=flow==='login'?'/auth/login':flow==='add'?'/auth/passkeys/options':
flow==='emergency'?'/auth/emergency-recovery/options':
flow==='recovery'?'/auth/passkeys/recovery/options':'/auth/passkeys/enrollment/options';
const body=flow==='login'?{login_id:id.value,password:pw.value}:flow==='add'?{}:
flow==='emergency'?{emergency_token:token,...(emergencyFactors==='both'?{new_password:pw.value}:{})}:
flow==='recovery'?{recovery_token:token}:
{setup_token:token,...(flow==='setup'?{new_password:pw.value}:{})};
const loginResponse=await post(path,csrf,body);pw.value='';
if(flow==='login'&&loginResponse.status===204){location.href='/account';return;}
const result=await loginResponse.json();
const options=result.publicKey;options.challenge=decode(options.challenge);
if(options.user)options.user.id=decode(options.user.id);
for(const key of ['allowCredentials','excludeCredentials'])
if(options[key])for(const item of options[key])item.id=decode(item.id);
const credential=flow==='login'?await navigator.credentials.get({publicKey:options}):
await navigator.credentials.create({publicKey:options});
const response={clientDataJSON:encode(credential.response.clientDataJSON)};
for(const key of ['attestationObject','authenticatorData','signature','userHandle'])
if(credential.response[key])response[key]=encode(credential.response[key]);
await post(flow==='login'?'/auth/login/passkey/verify':flow==='add'?'/auth/passkeys/verify':
flow==='emergency'?'/auth/emergency-recovery/verify':
flow==='recovery'?'/auth/passkeys/recovery/verify':'/auth/passkeys/enrollment/verify',result.csrf_token,{credential:{id:credential.id,
rawId:encode(credential.rawId),type:credential.type,response}});
token=null;await listKeys();
if(flow==='emergency')form.hidden=true;
out.textContent=flow==='login'?'로그인되었습니다.':flow==='emergency'?
'복구했습니다. 비밀번호와 새 Passkey로 로그인해 주세요.':'Passkey가 등록되었습니다.';
}catch{out.textContent='인증할 수 없습니다. 입력 또는 설정 링크를 확인하고 다시 시도해 주세요.';}
finally{pw.value='';form.querySelector('button').disabled=false;}});})();"""


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
