"""
Rate Limiting Configuration
Requires: pip install slowapi==0.1.9

To enable rate limiting:
1. Install: pip install slowapi==0.1.9
2. Add to main.py: app.state.limiter = limiter
3. Add exception handler to main.py
4. Apply @limiter.limit() decorator to endpoints

Example usage in main.py:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from core.rate_limit import limiter

    app = FastAPI(...)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Example endpoint protection:
    from core.rate_limit import limiter, RateLimits
    from fastapi import Request

    @router.post("/auth/login")
    @limiter.limit(RateLimits.LOGIN)
    async def login(request: Request, ...):
        ...

    @router.post("/videos/upload/{series}")
    @limiter.limit(RateLimits.VIDEO_UPLOAD)
    async def upload_video(request: Request, ...):
        ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,  # Rate limit by IP address
    default_limits=["1000/hour"],  # Default limit for all endpoints
    headers_enabled=True,  # Send rate limit info in response headers
)


# Recommended rate limits by endpoint type
class RateLimits:
    """Standard rate limits for different endpoint types"""

    # Authentication endpoints (prevent brute force)
    LOGIN = "5/minute"  # 5 login attempts per minute
    REGISTER = "3/hour"  # 3 registrations per hour per IP
    PASSWORD_RESET = "3/hour"  # 3 password reset requests per hour
    TOKEN_REFRESH = "10/minute"  # 10 token refreshes per minute

    # File upload endpoints (prevent abuse)
    VIDEO_UPLOAD = "10/hour"  # 10 video uploads per hour
    SUBTITLE_UPLOAD = "20/hour"  # 20 subtitle uploads per hour

    # General API endpoints
    API_READ = "100/minute"  # 100 read requests per minute
    API_WRITE = "50/minute"  # 50 write requests per minute

    # Video streaming (high volume)
    VIDEO_STREAM = "1000/hour"  # 1000 stream requests per hour

    # Vocabulary/game endpoints
    VOCABULARY_MARK = "200/minute"  # 200 vocabulary marks per minute
    GAME_SESSION = "50/hour"  # 50 game sessions per hour
