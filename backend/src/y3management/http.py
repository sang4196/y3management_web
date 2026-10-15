"""Strict same-origin HTTPS adapters. No database authentication in dependencies."""

from dataclasses import asdict
from typing import Annotated, Literal, cast
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, FastAPI, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.iam.public import Account, Setup
from y3management.use_cases import Service

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


class Access(Version):
    branch_id: UUID


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
        c = service(request).me(read(request))
        return {
            "account_id": str(c.account_id),
            "organization_id": str(c.organization_id),
            "roles": [
                {
                    "role": "ADMIN",
                    "scope": "ORGANIZATION" if c.master else "BRANCH",
                    "branch_id": str(c.branch_id) if c.branch_id else None,
                }
            ],
            "capabilities": [
                "branches:read",
                *(["branches:create", "accounts:manage"] if c.master else []),
            ],
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

    app.include_router(router)

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
