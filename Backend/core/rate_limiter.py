"""
Rate limiting middleware for API endpoints
"""

import logging
import time

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm"""

    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 60 seconds window
        self.request_history: dict[str, list] = {}

    def _get_user_key(self, request: Request, user_id: str | None = None) -> str:
        """Generate a unique key for the user/client"""
        if user_id:
            return f"user:{user_id}"

        # Fallback to IP address if no user ID
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _clean_old_requests(self, timestamps: list, current_time: float) -> list:
        """Remove requests older than the window size"""
        cutoff = current_time - self.window_size
        return [ts for ts in timestamps if ts > cutoff]

    async def check_rate_limit(self, request: Request, user_id: str | None = None) -> tuple[bool, dict[str, str]]:
        """
        Check if request exceeds rate limit

        Returns:
            Tuple of (is_allowed, rate_limit_headers)
        """
        current_time = time.time()
        user_key = self._get_user_key(request, user_id)

        # Get and clean request history
        if user_key not in self.request_history:
            self.request_history[user_key] = []

        self.request_history[user_key] = self._clean_old_requests(self.request_history[user_key], current_time)

        # Check rate limit
        request_count = len(self.request_history[user_key])

        # Calculate headers
        headers = {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(max(0, self.requests_per_minute - request_count)),
            "X-RateLimit-Reset": str(int(current_time + self.window_size)),
        }

        if request_count >= self.requests_per_minute:
            # Calculate retry after
            oldest_request = min(self.request_history[user_key])
            retry_after = int(self.window_size - (current_time - oldest_request))
            headers["Retry-After"] = str(retry_after)

            return False, headers

        # Add current request to history
        self.request_history[user_key].append(current_time)

        return True, headers


# Global rate limiter instances
vocabulary_rate_limiter = RateLimiter(requests_per_minute=30)
search_rate_limiter = RateLimiter(requests_per_minute=60)  # Higher limit for search


async def rate_limit_middleware(request: Request, user_id: str | None = None, limiter: RateLimiter | None = None):
    """Middleware function to apply rate limiting"""
    if not limiter:
        limiter = vocabulary_rate_limiter

    is_allowed, headers = await limiter.check_rate_limit(request, user_id)

    if not is_allowed:
        logger.warning(f"Rate limit exceeded for {user_id or request.client.host}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.", headers=headers)

    # Add rate limit headers to successful responses
    # This needs to be handled in the endpoint response
    return headers
