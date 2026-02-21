import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.core.exceptions import AppError


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        correlation_id = getattr(request.state, "correlation_id", "")
        logger.error(
            "app_error",
            extra={"correlation_id": correlation_id, "extra": {"code": exc.code, "message": exc.message}},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "code": exc.code,
                "correlation_id": correlation_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        correlation_id = getattr(request.state, "correlation_id", "")
        logger.error("request_validation_error", exc_info=True, extra={"correlation_id": correlation_id})
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "message": "Request validation failed",
                "code": "REQUEST_VALIDATION_ERROR",
                "correlation_id": correlation_id,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", "")
        logger.error("unhandled_error", exc_info=True, extra={"correlation_id": correlation_id})
        return JSONResponse(
            status_code=500,
            content={
                "error": True,
                "message": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
                "correlation_id": correlation_id,
            },
        )
