"""
Unit tests for RateLimitMiddleware with Redis support
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI, Request, Response

from core.security.security_middleware import RateLimitMiddleware


@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    return app


@pytest.fixture
def middleware(app):
    return RateLimitMiddleware(app, requests_per_minute=5, burst_size=2)


@pytest.mark.asyncio
async def test_rate_limit_fallback_when_redis_disconnected(app):
    """Test that middleware falls back to in-memory when Redis is disconnected"""

    # Mock Redis client to simulate disconnection
    mock_redis = AsyncMock()
    mock_redis.is_connected.return_value = False

    with patch("core.dependencies.cache_dependencies.get_redis_client", return_value=mock_redis):
        middleware = RateLimitMiddleware(app, requests_per_minute=2, burst_size=2)

        # Helper to process request through middleware
        async def call_next(request):
            return Response("ok", status_code=200)

        request = Mock(spec=Request)
        request.url.path = "/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()

        # First request - should pass
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200

        # Second request - should pass
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200

        # Third request - should fail (limit is 2)
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 429
        assert "Retry-After" in response.headers


@pytest.mark.asyncio
async def test_rate_limit_uses_redis_when_connected(app):
    """Test that middleware uses Redis when connected"""

    # Mock Redis client
    mock_redis = AsyncMock()
    mock_redis.is_connected.return_value = True
    # Mock rate_limit return: (allowed, remaining, reset_at)
    mock_redis.rate_limit.return_value = (True, 4, 1234567890)

    with patch("core.dependencies.cache_dependencies.get_redis_client", return_value=mock_redis):
        middleware = RateLimitMiddleware(app, requests_per_minute=5)

        async def call_next(request):
            return Response("ok", status_code=200)

        request = Mock(spec=Request)
        request.url.path = "/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()

        # Should call redis
        response = await middleware.dispatch(request, call_next)

        assert response.status_code == 200
        mock_redis.rate_limit.assert_called_once()
        assert response.headers["X-RateLimit-Remaining"] == "4"


@pytest.mark.asyncio
async def test_rate_limit_redis_exceeded(app):
    """Test that middleware handles Redis rate limit exceeded"""

    mock_redis = AsyncMock()
    mock_redis.is_connected.return_value = True
    # Mock rate_limit return: (allowed=False, remaining=0, reset_at=future)
    mock_redis.rate_limit.return_value = (False, 0, 2000000000)

    with patch("core.dependencies.cache_dependencies.get_redis_client", return_value=mock_redis):
        middleware = RateLimitMiddleware(app, requests_per_minute=5)

        async def call_next(request):
            return Response("ok", status_code=200)

        request = Mock(spec=Request)
        request.url.path = "/test"
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = Mock()

        with patch("time.time", return_value=1000000000):
            response = await middleware.dispatch(request, call_next)

        assert response.status_code == 429
        assert "Rate limit exceeded" in str(response.body) if hasattr(response, "body") else ""
