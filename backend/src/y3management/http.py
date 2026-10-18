"""Strict same-origin HTTPS adapters. No database authentication in dependencies."""

import json
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
from y3management.iam.public import Account, Ceremony, Setup
from y3management.use_cases import Service

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
        if settings.iam_mode == "mfa":
            return ceremony_response(
                service(request).begin_mfa_login(
                    body.login_id, body.password, request.cookies.get(PREAUTH), nonce, auth
                )
            )
        token = service(request).login(
            body.login_id, body.password, request.cookies.get(PREAUTH), nonce, auth
        )
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

    app.include_router(router)

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
        return f"""<!doctype html><meta charset="utf-8"><title>Y3 인증</title>
<body data-flow="{flow}"><form id="mfa">
<label>로그인 ID <input id="identifier" autocomplete="username"></label>
<label>비밀번호 <input id="password" type="password" autocomplete="current-password"></label>
<button>계속</button></form><p id="result"></p><script src="/mfa.js"></script></body>"""

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
        return mfa_page("add")

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
pw.parentElement.hidden=!['login','setup'].includes(flow);
if(flow==='setup')pw.autocomplete='new-password';
const decode=s=>Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
const encode=b=>btoa(String.fromCharCode(...new Uint8Array(b)))
.replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
async function post(path,csrf,body){const r=await fetch('/api/v1'+path,{method:'POST',
headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(body)});
if(!r.ok)throw Error();return r;}
form.addEventListener('submit',async e=>{e.preventDefault();
form.querySelector('button').disabled=true;
try{
const p=await fetch('/api/v1/auth/csrf',{headers:{'X-Y3-Client':'mfa'}});if(!p.ok)throw Error();
const csrf=(await p.json()).csrf_token;
const path=flow==='login'?'/auth/login':flow==='add'?'/auth/passkeys/options':
'/auth/passkeys/enrollment/options';
const body=flow==='login'?{login_id:id.value,password:pw.value}:flow==='add'?{}:
{setup_token:token,...(flow==='setup'?{new_password:pw.value}:{})};
const result=await (await post(path,csrf,body)).json();pw.value='';
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
'/auth/passkeys/enrollment/verify',result.csrf_token,{credential:{id:credential.id,
rawId:encode(credential.rawId),type:credential.type,response}});
token=null;out.textContent=flow==='login'?'로그인되었습니다.':'Passkey가 등록되었습니다.';
}catch{out.textContent='인증할 수 없습니다. 입력 또는 설정 링크를 확인하고 다시 시도해 주세요.';}
finally{pw.value='';form.querySelector('button').disabled=false;}});})();"""
