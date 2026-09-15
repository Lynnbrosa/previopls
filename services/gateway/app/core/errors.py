import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.logging import get_logger


log = get_logger(__name__)


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class SignatureError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "INVALID_SIGNATURE"


def _body(code: str, message: str, details: Any = None) -> dict:
    payload: dict = {"error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return payload


_STATUS_CODES = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
    status.HTTP_502_BAD_GATEWAY: "UPSTREAM_ERROR",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
}


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.code, exc.message, exc.details))

    @app.exception_handler(HTTPException)
    async def handle_http(_request: Request, exc: HTTPException):
        default_code = _STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
        headers = getattr(exc, "headers", None)
        if isinstance(exc.detail, dict):
            code = str(exc.detail.get("code") or default_code)
            message = str(exc.detail.get("message") or "Erro")
            details = {k: v for k, v in exc.detail.items() if k not in ("code", "message")} or None
            return JSONResponse(status_code=exc.status_code, content=_body(code, message, details), headers=headers)
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(default_code, str(exc.detail)),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_request: Request, exc: RequestValidationError):
        details = jsonable_encoder({"errors": exc.errors()})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_body("VALIDATION_ERROR", "Dados inválidos", details),
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity(_request: Request, _exc: IntegrityError):
        incident = uuid.uuid4().hex[:8]
        log.error("db_integrity_error", incident=incident)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_body("CONFLICT", f"Violação de integridade (incident={incident})"),
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_db(_request: Request, _exc: SQLAlchemyError):
        incident = uuid.uuid4().hex[:8]
        log.error("db_error", incident=incident)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_body("INTERNAL_ERROR", f"Erro interno (incident={incident})"),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_request: Request, _exc: Exception):
        incident = uuid.uuid4().hex[:8]
        log.exception("unhandled_error", incident=incident)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_body("INTERNAL_ERROR", f"Erro interno (incident={incident})"),
        )
