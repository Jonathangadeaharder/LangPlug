"""Token blacklist service for JWT token revocation"""

import logging
from datetime import UTC, datetime, timedelta

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TokenBlacklist:
    """Service for managing blacklisted JWT tokens"""

    def __init__(self):
        self._use_redis = REDIS_AVAILABLE  # Use Redis if available, fallback to memory
        self._memory_blacklist: set[str] = set()
        self._memory_expiry: dict[str, datetime] = {}
        self._redis_client = None
        logger.info(f"TokenBlacklist initialized with Redis: {self._use_redis}")

    async def _get_redis_client(self):
        """Get Redis client (lazy initialization)"""
        if not self._use_redis:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, falling back to memory")
                self._use_redis = False
                return None

        return self._redis_client

    async def add_token(self, token: str, expires_at: datetime | None = None) -> bool:
        """Add a token to the blacklist"""
        # Validate token
        if not token or token is None:
            logger.warning("Attempted to add empty or None token to blacklist")
            return False

        logger.info(f"Adding token to blacklist: {token[:20]}...")

        if expires_at is None:
            expires_at = datetime.now(UTC) + timedelta(hours=24)

        if self._use_redis:
            redis_client = await self._get_redis_client()
            if redis_client:
                try:
                    # Set token with expiration
                    ttl = int((expires_at - datetime.now(UTC)).total_seconds())
                    if ttl > 0:
                        await redis_client.setex(f"blacklist:{token}", ttl, "1")
                        logger.info(f"Token added to Redis blacklist with TTL: {ttl}")
                        return True
                except Exception as e:
                    logger.error(f"Redis blacklist add failed: {e}")
                    # Fall back to memory

        # Memory fallback
        self._memory_blacklist.add(token)
        self._memory_expiry[token] = expires_at
        logger.info(f"Token added to memory blacklist. Total tokens: {len(self._memory_blacklist)}")
        return True

    async def is_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        # Validate token
        if not token or token is None:
            logger.debug("Checking blacklist for empty/None token - returning False")
            return False

        logger.debug(f"Checking if token is blacklisted: {token[:20]}...")

        if self._use_redis:
            redis_client = await self._get_redis_client()
            if redis_client:
                try:
                    result = await redis_client.exists(f"blacklist:{token}")
                    is_blacklisted = bool(result)
                    logger.debug(f"Redis blacklist check result: {is_blacklisted}")
                    return is_blacklisted
                except Exception as e:
                    logger.error(f"Redis blacklist check failed: {e}")
                    # Fall back to memory

        # Memory fallback
        if token in self._memory_blacklist:
            # Check if token has expired
            if token in self._memory_expiry and datetime.now(UTC) > self._memory_expiry[token]:
                # Token expired, remove it
                self._memory_blacklist.discard(token)
                del self._memory_expiry[token]
                logger.debug(f"Expired token removed from blacklist: {token[:20]}...")
                return False
            logger.debug(f"Token found in memory blacklist: {token[:20]}...")
            return True

        logger.debug(f"Token not in blacklist: {token[:20]}...")
        return False

    async def remove_token(self, token: str) -> bool:
        """Remove a token from the blacklist"""
        logger.info(f"Removing token from blacklist: {token[:20]}...")

        if self._use_redis:
            redis_client = await self._get_redis_client()
            if redis_client:
                try:
                    result = await redis_client.delete(f"blacklist:{token}")
                    logger.info(f"Token removed from Redis blacklist: {bool(result)}")
                    return bool(result)
                except Exception as e:
                    logger.error(f"Redis blacklist remove failed: {e}")
                    # Fall back to memory

        # Memory fallback
        removed = token in self._memory_blacklist
        self._memory_blacklist.discard(token)
        self._memory_expiry.pop(token, None)
        logger.info(f"Token removed from memory blacklist: {removed}")
        return removed

    async def cleanup_expired(self):
        """Clean up expired tokens from memory storage"""
        if not self._use_redis:
            now = datetime.now(UTC)
            expired_tokens = [token for token, expiry in self._memory_expiry.items() if now > expiry]

            for token in expired_tokens:
                self._memory_blacklist.discard(token)
                del self._memory_expiry[token]

            if expired_tokens:
                logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")


# Global instance
token_blacklist = TokenBlacklist()
