"""
Security middleware for FastAPI application
"""

import hashlib
import logging
import time
from collections import defaultdict

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from .middleware import LoggingMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    def __init__(self, app, enforce_https: bool = True):
        super().__init__(app)
        self.enforce_https = enforce_https

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        if self.enforce_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:*;"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with sliding window algorithm"""

    def __init__(self, app, requests_per_minute: int = 60, burst_size: int = 10, exclude_paths: list | None = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.request_counts: dict[str, list] = defaultdict(list)
        self.window_size = 60  # 60 seconds

    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for the client"""
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _is_excluded(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting"""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    def _add_cors_headers(self, response: JSONResponse, origin: str | None = None) -> JSONResponse:
        """Add CORS headers to response (for rate limit error responses)"""
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = (
            "X-Request-ID, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After"
        )
        return response

    async def dispatch(self, request: Request, call_next):
        if self._is_excluded(request.url.path):
            return await call_next(request)

        origin = request.headers.get("origin")

        client_id = self._get_client_id(request)
        current_time = time.time()

        self.request_counts[client_id] = [
            timestamp for timestamp in self.request_counts[client_id] if timestamp > current_time - self.window_size
        ]

        request_count = len(self.request_counts[client_id])

        if request_count >= self.requests_per_minute:
            oldest_request = min(self.request_counts[client_id])
            retry_after = int(self.window_size - (current_time - oldest_request))

            logger.warning(f"Rate limit exceeded for {client_id}")
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded", "retry_after": retry_after},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after)),
                },
            )
            return self._add_cors_headers(response, origin)

        recent_requests = sum(1 for timestamp in self.request_counts[client_id] if timestamp > current_time - 5)

        if recent_requests >= self.burst_size:
            logger.warning(f"Burst limit exceeded for {client_id}")
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Burst limit exceeded. Please slow down."},
                headers={"Retry-After": "5"},
            )
            return self._add_cors_headers(response, origin)

        self.request_counts[client_id].append(current_time)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self.requests_per_minute - request_count - 1)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests"""

    def __init__(self, app, max_body_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            logger.warning(f"Request body too large: {content_length} bytes")
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content={"detail": "Request body too large"}
            )

        request_id = (
            request.headers.get("X-Request-ID")
            or hashlib.sha256(f"{time.time()}{request.client}".encode()).hexdigest()[:16]
        )
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


def setup_security_middleware(app: FastAPI, settings):
    """Configure all security middleware for the application"""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    app.add_middleware(SecurityHeadersMiddleware, enforce_https=settings.environment == "production")

    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=300,
        burst_size=60,
    )

    app.add_middleware(RequestValidationMiddleware, max_body_size=settings.max_upload_size)

    app.add_middleware(LoggingMiddleware)

    logger.info("Security middleware configured successfully")
