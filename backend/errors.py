from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.schemas import ErrorResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base exception type for expected application failures."""

    default_status_code = 500
    default_code = "application_error"

    def __init__(
        self,
        detail: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code or self.default_status_code
        self.code = code or self.default_code


class InvalidRequestError(AppError):
    default_status_code = 400
    default_code = "invalid_request"


class DependencyUnavailableError(AppError):
    default_status_code = 503
    default_code = "dependency_unavailable"


class UpstreamServiceError(AppError):
    default_status_code = 502
    default_code = "upstream_service_error"


class ConfigurationError(AppError):
    default_status_code = 500
    default_code = "configuration_error"


class CacheBackendError(AppError):
    default_status_code = 503
    default_code = "cache_backend_error"


class CacheQueryError(CacheBackendError):
    default_code = "cache_query_error"


class PersistenceError(CacheBackendError):
    default_code = "persistence_error"


def _build_error_response(
    *,
    detail: str,
    code: str,
    request_id: str | None,
    status_code: int,
) -> JSONResponse:
    payload = ErrorResponse(
        detail=detail,
        code=code,
        request_id=request_id,
    ).model_dump(exclude_none=True)
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register JSON exception handlers for expected and unexpected failures."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)

        if exc.status_code >= 500:
            logger.error(
                "Application error [%s] request_id=%s: %s",
                exc.code,
                request_id,
                exc.detail,
                exc_info=(type(exc), exc, exc.__traceback__),
            )
        else:
            logger.warning(
                "Client error [%s] request_id=%s: %s",
                exc.code,
                request_id,
                exc.detail,
            )

        return _build_error_response(
            detail=exc.detail,
            code=exc.code,
            request_id=request_id,
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled application error request_id=%s", request_id, exc_info=exc)
        return _build_error_response(
            detail="An unexpected server error occurred.",
            code="internal_server_error",
            request_id=request_id,
            status_code=500,
        )
