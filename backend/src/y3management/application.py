"""HTTP composition only. No PT registration, authentication or business models."""

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
        resource = database if database is not None else Database(configuration)
        app.state.database = resource
        logger.info("application_started")
        try:
            yield
        finally:
            await run_in_threadpool(resource.close)
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

    return app
