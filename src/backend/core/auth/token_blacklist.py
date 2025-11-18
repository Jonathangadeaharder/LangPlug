"""Token blacklist service for JWT token revocation - In-memory implementation"""

import logging
from datetime import UTC, datetime, timedelta

# Python 3.10 compatibility: Use timezone.utc instead of UTC constant
UTC = UTC

logger = logging.getLogger(__name__)


class TokenBlacklist:
    """
    Token blacklist service using in-memory storage

    Note: This is suitable for single-instance deployments only.
    For distributed systems, use a Redis-based token blacklist.

    Usage:
        blacklist = TokenBlacklist()
        await blacklist.add_token(token, expires_at)
        is_blocked = await blacklist.is_blacklisted(token)
    """

    def __init__(self):
        """Initialize token blacklist with in-memory storage"""
        self._blacklist: dict[str, datetime] = {}
        logger.info("TokenBlacklist initialized (in-memory)")

    async def add_token(self, token: str, expires_at: datetime | None = None) -> bool:
        """
        Add a token to the blacklist

        Args:
            token: JWT token to blacklist
            expires_at: When the token expires (optional, defaults to 24h from now)

        Returns:
            bool: True if successfully added
        """
        if not token or token is None:
            logger.warning("Attempted to add empty or None token to blacklist")
            return False

        logger.debug(f"Adding token to blacklist: {token[:20]}...")

        if expires_at is None:
            expires_at = datetime.now(UTC) + timedelta(hours=24)

        # Check if token already expired
        if expires_at <= datetime.now(UTC):
            logger.warning("Token already expired, not adding to blacklist")
            return False

        # Store token with expiration time
        self._blacklist[token] = expires_at
        logger.debug(f"Token added to blacklist, expires at: {expires_at}")

        # Cleanup expired tokens periodically
        await self.cleanup_expired()

        return True

    async def is_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted

        Args:
            token: JWT token to check

        Returns:
            bool: True if blacklisted, False otherwise
        """
        if not token or token is None:
            logger.debug("Checking blacklist for empty/None token - returning False")
            return False

        logger.debug(f"Checking if token is blacklisted: {token[:20]}...")

        # Cleanup expired tokens first
        await self.cleanup_expired()

        # Check if token is in blacklist and not expired
        if token in self._blacklist:
            expires_at = self._blacklist[token]
            if expires_at > datetime.now(UTC):
                logger.debug("Token is blacklisted and not expired")
                return True
            else:
                # Token expired, remove it
                del self._blacklist[token]
                logger.debug("Token was blacklisted but expired, removed")
                return False

        logger.debug("Token is not blacklisted")
        return False

    async def remove_token(self, token: str) -> bool:
        """
        Remove a token from the blacklist

        Args:
            token: JWT token to remove

        Returns:
            bool: True if token was removed, False if not found
        """
        logger.debug(f"Removing token from blacklist: {token[:20]}...")

        if token in self._blacklist:
            del self._blacklist[token]
            logger.debug("Token removed from blacklist")
            return True

        logger.debug("Token not found in blacklist")
        return False

    async def cleanup_expired(self):
        """
        Remove expired tokens from the blacklist

        Should be called periodically to prevent memory bloat.
        """
        now = datetime.now(UTC)
        expired_tokens = [token for token, expires_at in self._blacklist.items() if expires_at <= now]

        for token in expired_tokens:
            del self._blacklist[token]

        if expired_tokens:
            logger.debug(f"Cleaned up {len(expired_tokens)} expired tokens from blacklist")
