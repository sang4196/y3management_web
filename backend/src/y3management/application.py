"""HTTP and lifetime composition; synchronous business work stays within one worker."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Protocol

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from y3management.config import Settings, load_settings
from y3management.database import Database
from y3management.http import attach
from y3management.runtime import ProcessGuard
from y3management.uow import UnitOfWork
from y3management.use_cases import Service

logger = logging.getLogger("y3management")


class DatabaseResource(Protocol):
    def is_ready(self) -> bool: ...
    def close(self) -> None: ...


def create_app(
    settings: Settings | None = None,
    *,
    database: DatabaseResource | None = None,
) -> FastAPI:
    configuration = settings if settings is not None else load_settings()
    logger.setLevel(configuration.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        guard: ProcessGuard | None = None
        resource: DatabaseResource | None = None
        try:
            try:
                guard = ProcessGuard(configuration) if configuration.iam_enabled else None
                resource = database if database is not None else Database(configuration)
                app.state.database = resource
                if configuration.iam_enabled:
                    if not isinstance(resource, Database):
                        raise ValueError("IAM_REQUIRES_DATABASE")
                    app.state.iam_service = Service(UnitOfWork(resource, configuration))
            except Exception:
                raise ValueError("APPLICATION_STARTUP_FAILED") from None
            logger.info("application_started")
            yield
        finally:
            try:
                if resource is not None:
                    await run_in_threadpool(resource.close)
            finally:
                if guard is not None:
                    guard.close()
            logger.info("application_stopped")

    app = FastAPI(
        title="Y3 Management",
        lifespan=lifespan,
        debug=False,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.middleware("http")
    async def safe_errors(request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception:
            logger.error("request_failed")  # No body, URL, headers, exception or traceback.
            return JSONResponse({"detail": "Internal server error"}, status_code=500)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse({"detail": "Invalid request"}, status_code=422)

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready")
    def ready(request: Request) -> JSONResponse:
        resource: DatabaseResource = request.app.state.database
        available = resource.is_ready()
        return JSONResponse(
            {"status": "ready" if available else "not_ready"},
            status_code=200 if available else 503,
        )

    if configuration.iam_enabled:
        attach(app, configuration)
    return app
