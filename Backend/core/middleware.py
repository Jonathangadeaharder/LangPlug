"""
Middleware for FastAPI application
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import LangPlugException

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        api_logger = logging.getLogger("api")

        api_logger.info(
            f"API Request: {request.method} {request.url.path}",
            extra={
                "event_type": "api_request",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": {k: v for k, v in request.headers.items() if k.lower() not in ["authorization", "cookie"]},
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            response_body = None
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) < 1024 * 10:
                        response_body = "[Response body available but not logged for privacy]"
                except Exception:
                    pass

            api_logger.info(
                f"API Response: {response.status_code} {request.method} {request.url.path}",
                extra={
                    "event_type": "api_response",
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": round(process_time, 4),
                    "response_headers": dict(response.headers),
                    "response_body": response_body,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "process_time": round(process_time, 4),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                exc_info=True,
            )
            raise


def setup_middleware(app: FastAPI) -> None:
    """Set up all middleware for the FastAPI application"""

    # CORS middleware is now configured in security_middleware.py to avoid duplication
    # This function is kept for backward compatibility and exception handlers

    # Exception handlers
    @app.exception_handler(LangPlugException)
    async def langplug_exception_handler(request: Request, exc: LangPlugException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": exc.__class__.__name__, "timestamp": datetime.utcnow().isoformat()},
        )

    logger.info("Middleware configured successfully (CORS configured in security_middleware)")
