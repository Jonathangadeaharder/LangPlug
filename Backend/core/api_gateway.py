"""
API Gateway pattern implementation for cross-cutting concerns
"""

import time

from fastapi import HTTPException, Request, Response, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .caching import cache_manager
from .config import settings


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window"""

    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 1 minute window
        self.request_counts: dict[str, list] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # Clean old requests outside the window
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip] if current_time - timestamp < self.window_size
            ]
        else:
            self.request_counts[client_ip] = []

        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

        # Add current request
        self.request_counts[client_ip].append(current_time)

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class CachingMiddleware(BaseHTTPMiddleware):
    """Response caching middleware for GET requests"""

    def __init__(self, app: ASGIApp, default_ttl: int = 300):
        super().__init__(app)
        self.default_ttl = default_ttl
        self.cacheable_paths = {
            "/vocabulary/search": 600,  # 10 minutes
            "/vocabulary/level": 1800,  # 30 minutes
            "/vocabulary/random": 300,  # 5 minutes
        }

    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Check if path is cacheable
        cache_ttl = self._get_cache_ttl(request.url.path)
        if cache_ttl is None:
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get from cache
        cached_response = cache_manager.get(cache_key)
        if cached_response:
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"],
            )

        # Execute request
        response = await call_next(request)

        # Cache successful responses
        if response.status_code == 200:
            # Read response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Store in cache
            cache_data = {
                "content": response_body.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type,
            }
            cache_manager.set(cache_key, cache_data, cache_ttl)

            # Return new response with body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type,
            )

        return response

    def _get_cache_ttl(self, path: str) -> int | None:
        """Get cache TTL for a given path"""
        for cacheable_path, ttl in self.cacheable_paths.items():
            if path.startswith(cacheable_path):
                return ttl
        return None

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        query_params = str(sorted(request.query_params.items()))
        return f"api_cache:{request.url.path}:{hash(query_params)}"


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Request validation and transformation middleware"""

    async def dispatch(self, request: Request, call_next):
        # Add request ID for tracing
        request_id = f"req_{int(time.time() * 1000000)}"
        request.state.request_id = request_id

        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content-Type must be application/json"
                )

        response = await call_next(request)

        # Add response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = str(int((time.time() - request.state.start_time) * 1000))

        return response


class APIGateway:
    """API Gateway for managing cross-cutting concerns"""

    def __init__(self, app):
        self.app = app
        self._setup_middleware()

    def _setup_middleware(self):
        """Setup gateway middleware"""
        # Add rate limiting
        self.app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=settings.rate_limit_per_minute if hasattr(settings, "rate_limit_per_minute") else 60,
        )

        # Add caching
        self.app.add_middleware(CachingMiddleware, default_ttl=settings.cache_ttl_default)

        # Add request validation
        self.app.add_middleware(RequestValidationMiddleware)

    def setup_health_checks(self):
        """Setup health check endpoints"""

        @self.app.get("/health")
        async def health_check():
            """Basic health check"""
            return {"status": "healthy", "timestamp": time.time()}

        @self.app.get("/health/detailed")
        async def detailed_health_check():
            """Detailed health check with dependencies"""
            checks = {
                "database": await self._check_database(),
                "cache": await self._check_cache(),
                "disk_space": await self._check_disk_space(),
            }

            all_healthy = all(checks.values())
            status_code = 200 if all_healthy else 503

            return Response(
                content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks}, status_code=status_code
            )

    async def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            from core.database import SessionLocal

            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            return True
        except Exception:
            return False

    async def _check_cache(self) -> bool:
        """Check cache connectivity"""
        try:
            cache_manager.set("health_check", "ok", 10)
            result = cache_manager.get("health_check")
            cache_manager.delete("health_check")
            return result == "ok"
        except Exception:
            return False

    async def _check_disk_space(self) -> bool:
        """Check available disk space"""
        try:
            import shutil

            total, _used, free = shutil.disk_usage("/")
            # Return healthy if more than 10% free space
            return (free / total) > 0.1
        except Exception:
            return False
