"""Exception handlers for FastAPI application"""

from datetime import datetime

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import LangPlugException
from core.sentry_config import capture_exception, set_context

logger = structlog.get_logger(__name__)


def setup_exception_handlers(app: FastAPI):
    """Setup exception handlers for the FastAPI application"""

    @app.exception_handler(LangPlugException)
    async def langplug_exception_handler(request: Request, exc: LangPlugException):
        """Handle custom LangPlug exceptions"""
        logger.warning(
            "LangPlug exception",
            status_code=exc.status_code,
            message=exc.message,
            path=request.url.path,
            method=request.method,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": exc.__class__.__name__, "timestamp": datetime.utcnow().isoformat()},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with user-friendly messages"""
        logger.warning(
            "HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )

        # Translate fastapi-users error codes to user-friendly messages
        error_translations = {
            "REGISTER_USER_ALREADY_EXISTS": "An account with this email or username already exists",
            "LOGIN_BAD_CREDENTIALS": "Invalid email or password",
            "LOGIN_USER_NOT_VERIFIED": "Please verify your email address before logging in",
            "RESET_PASSWORD_BAD_TOKEN": "Invalid or expired password reset link",
            "RESET_PASSWORD_INVALID_PASSWORD": "Password does not meet security requirements",
            "VERIFY_USER_BAD_TOKEN": "Invalid or expired verification link",
            "VERIFY_USER_ALREADY_VERIFIED": "Your account is already verified",
        }

        # Check if this is a fastapi-users error code
        detail = exc.detail
        if isinstance(detail, str) and detail in error_translations:
            detail = error_translations[detail]

        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logger.warning(
            "Starlette HTTP exception",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"type": "http_error", "message": exc.detail, "status_code": exc.status_code}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        # Serialize error details to handle ValueError objects
        serialized_errors = []
        for error in exc.errors():
            serialized_error = dict(error)
            # Handle ValueError objects in ctx
            if "ctx" in serialized_error and "error" in serialized_error["ctx"]:
                error_obj = serialized_error["ctx"]["error"]
                if hasattr(error_obj, "__str__"):
                    serialized_error["ctx"]["error"] = str(error_obj)
            serialized_errors.append(serialized_error)

        logger.warning("Validation error", errors=serialized_errors, path=request.url.path, method=request.method)

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Request validation failed",
                    "details": serialized_errors,
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """Handle SQLAlchemy database errors"""
        logger.error(
            "Database error",
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )

        # Set context for Sentry
        set_context(
            "database_error", {"error_type": type(exc).__name__, "path": request.url.path, "method": request.method}
        )

        # Capture exception with Sentry
        capture_exception(exc)

        return JSONResponse(
            status_code=500, content={"error": {"type": "database_error", "message": "A database error occurred"}}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(
            "Unhandled exception",
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )

        # Set context for Sentry
        set_context(
            "unhandled_error", {"error_type": type(exc).__name__, "path": request.url.path, "method": request.method}
        )

        # Capture exception with Sentry
        capture_exception(exc)

        return JSONResponse(
            status_code=500,
            content={"error": {"type": "internal_error", "message": "An internal server error occurred"}},
        )
