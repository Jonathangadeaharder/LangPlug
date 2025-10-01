"""Tests for token blacklist service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from core.token_blacklist import TokenBlacklist


class TestTokenBlacklist:
    """Test TokenBlacklist initialization and basic functionality."""

    def test_initialization_without_redis(self):
        """Test initialization when Redis is not available."""
        with patch("core.token_blacklist.REDIS_AVAILABLE", False):
            blacklist = TokenBlacklist()
            assert not blacklist._use_redis
            assert isinstance(blacklist._memory_blacklist, set)
            assert isinstance(blacklist._memory_expiry, dict)
            assert len(blacklist._memory_blacklist) == 0

    def test_initialization_with_redis(self):
        """Test initialization when Redis is available."""
        with patch("core.token_blacklist.REDIS_AVAILABLE", True):
            blacklist = TokenBlacklist()
            assert blacklist._use_redis
            assert blacklist._redis_client is None

    @pytest.mark.anyio
    async def test_get_redis_client_without_redis(self):
        """Test Redis client getter when Redis is not available."""
        with patch("core.token_blacklist.REDIS_AVAILABLE", False):
            blacklist = TokenBlacklist()
            client = await blacklist._get_redis_client()
            assert client is None

    @pytest.mark.anyio
    async def test_get_redis_client_success(self):
        """Test successful Redis client creation."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()

        with patch("core.token_blacklist.REDIS_AVAILABLE", True):
            with patch("redis.asyncio.Redis", return_value=mock_redis):
                blacklist = TokenBlacklist()
                client = await blacklist._get_redis_client()

                assert client is mock_redis
                mock_redis.ping.assert_called_once()

    @pytest.mark.anyio
    async def test_get_redis_client_connection_failure(self):
        """Test Redis client creation with connection failure."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))

        with patch("core.token_blacklist.REDIS_AVAILABLE", True):
            with patch("redis.asyncio.Redis", return_value=mock_redis):
                blacklist = TokenBlacklist()
                client = await blacklist._get_redis_client()

                assert client is None
                assert not blacklist._use_redis
                mock_redis.ping.assert_called_once()


class TestTokenBlacklistMemoryOperations:
    """Test token blacklist operations using memory storage."""

    @pytest.fixture
    def memory_blacklist(self):
        """Create blacklist instance using memory storage."""
        with patch("core.token_blacklist.REDIS_AVAILABLE", False):
            return TokenBlacklist()

    @pytest.mark.anyio
    async def test_add_token_memory_storage(self, memory_blacklist):
        """Test adding token to memory storage."""
        token = "test_token_12345"
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        result = await memory_blacklist.add_token(token, expires_at)

        assert result is True
        assert token in memory_blacklist._memory_blacklist
        assert memory_blacklist._memory_expiry[token] == expires_at

    @pytest.mark.anyio
    async def test_add_token_memory_default_expiry(self, memory_blacklist):
        """Test adding token with default expiry."""
        token = "test_token_12345"

        result = await memory_blacklist.add_token(token)

        assert result is True
        assert token in memory_blacklist._memory_blacklist
        # Check that default expiry was set (1 day from now)
        assert token in memory_blacklist._memory_expiry
        expiry = memory_blacklist._memory_expiry[token]
        now = datetime.now(UTC)
        assert (expiry - now).days == 0  # Same day
        assert (expiry - now).seconds > 23 * 3600  # More than 23 hours

    @pytest.mark.anyio
    async def test_is_blacklisted_memory_storage(self, memory_blacklist):
        """Test checking if token is blacklisted in memory."""
        token = "test_token_12345"
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        # Initially not blacklisted
        result = await memory_blacklist.is_blacklisted(token)
        assert result is False

        # Add to blacklist
        await memory_blacklist.add_token(token, expires_at)

        # Now should be blacklisted
        result = await memory_blacklist.is_blacklisted(token)
        assert result is True

    @pytest.mark.anyio
    async def test_is_blacklisted_expired_token_memory(self, memory_blacklist):
        """Test blacklisted token that has expired."""
        token = "test_token_12345"
        expires_at = datetime.now(UTC) - timedelta(hours=1)  # Expired

        await memory_blacklist.add_token(token, expires_at)

        # Should not be blacklisted due to expiry
        result = await memory_blacklist.is_blacklisted(token)
        assert result is False

        # Token should be removed from blacklist
        assert token not in memory_blacklist._memory_blacklist
        assert token not in memory_blacklist._memory_expiry

    @pytest.mark.anyio
    async def test_remove_token_memory_storage(self, memory_blacklist):
        """Test removing token from memory storage."""
        token = "test_token_12345"
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        # Add token first
        await memory_blacklist.add_token(token, expires_at)
        assert token in memory_blacklist._memory_blacklist

        # Remove token
        result = await memory_blacklist.remove_token(token)
        assert result is True
        assert token not in memory_blacklist._memory_blacklist
        assert token not in memory_blacklist._memory_expiry

    @pytest.mark.anyio
    async def test_remove_nonexistent_token_memory(self, memory_blacklist):
        """Test removing token that doesn't exist."""
        token = "nonexistent_token"

        result = await memory_blacklist.remove_token(token)
        assert result is False

    @pytest.mark.anyio
    async def test_cleanup_expired_tokens_memory(self, memory_blacklist):
        """Test cleanup of expired tokens in memory."""
        # Add mix of expired and valid tokens
        expired_token = "expired_token"
        valid_token = "valid_token"

        await memory_blacklist.add_token(expired_token, datetime.now(UTC) - timedelta(hours=1))
        await memory_blacklist.add_token(valid_token, datetime.now(UTC) + timedelta(hours=1))

        # Cleanup
        result = await memory_blacklist.cleanup_expired()

        assert result is None  # cleanup_expired doesn't return anything
        assert expired_token not in memory_blacklist._memory_blacklist
        assert valid_token in memory_blacklist._memory_blacklist


class TestTokenBlacklistRedisOperations:
    """Test token blacklist operations using Redis storage."""

    @pytest.fixture
    def redis_blacklist(self):
        """Create blacklist instance with Redis enabled."""
        with patch("core.token_blacklist.REDIS_AVAILABLE", True):
            return TokenBlacklist()

    @pytest.mark.anyio
    async def test_add_token_redis_storage(self, redis_blacklist):
        """Test adding token to Redis storage."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)

        with patch("core.token_blacklist.redis.Redis", return_value=mock_redis):
            token = "test_token_12345"
            expires_at = datetime.now(UTC) + timedelta(hours=1)

            result = await redis_blacklist.add_token(token, expires_at)

            assert result is True
            mock_redis.ping.assert_called_once()
            mock_redis.setex.assert_called_once()

    @pytest.mark.anyio
    async def test_is_blacklisted_redis_storage(self, redis_blacklist):
        """Test checking blacklisted token in Redis."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)  # Token exists

        with patch("core.token_blacklist.redis.Redis", return_value=mock_redis):
            token = "test_token_12345"

            result = await redis_blacklist.is_blacklisted(token)

            assert result is True
            mock_redis.ping.assert_called_once()
            mock_redis.exists.assert_called_once_with(f"blacklist:{token}")

    @pytest.mark.anyio
    async def test_is_blacklisted_redis_not_found(self, redis_blacklist):
        """Test checking non-blacklisted token in Redis."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)  # Token doesn't exist

        with patch("core.token_blacklist.redis.Redis", return_value=mock_redis):
            token = "test_token_12345"

            result = await redis_blacklist.is_blacklisted(token)

            assert result is False
            mock_redis.exists.assert_called_once_with(f"blacklist:{token}")

    @pytest.mark.anyio
    async def test_remove_token_redis_storage(self, redis_blacklist):
        """Test removing token from Redis storage."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)  # Token was deleted

        with patch("core.token_blacklist.redis.Redis", return_value=mock_redis):
            token = "test_token_12345"

            result = await redis_blacklist.remove_token(token)

            assert result is True
            mock_redis.delete.assert_called_once_with(f"blacklist:{token}")

    @pytest.mark.anyio
    async def test_redis_operation_failure_fallback(self, redis_blacklist):
        """Test fallback to memory when Redis operation fails."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))

        with patch("core.token_blacklist.redis.Redis", return_value=mock_redis):
            token = "test_token_12345"
            expires_at = datetime.now(UTC) + timedelta(hours=1)

            result = await redis_blacklist.add_token(token, expires_at)

            # Should succeed using memory fallback
            assert result is True
            assert token in redis_blacklist._memory_blacklist


class TestTokenBlacklistEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def blacklist(self):
        """Create blacklist instance."""
        with patch("core.token_blacklist.REDIS_AVAILABLE", False):
            return TokenBlacklist()

    @pytest.mark.anyio
    async def test_add_empty_token(self, blacklist):
        """Test adding empty token."""
        result = await blacklist.add_token("")
        assert result is False

    @pytest.mark.anyio
    async def test_add_none_token(self, blacklist):
        """Test adding None token."""
        result = await blacklist.add_token(None)
        assert result is False

    @pytest.mark.anyio
    async def test_is_blacklisted_empty_token(self, blacklist):
        """Test checking empty token."""
        result = await blacklist.is_blacklisted("")
        assert result is False

    @pytest.mark.anyio
    async def test_is_blacklisted_none_token(self, blacklist):
        """Test checking None token."""
        result = await blacklist.is_blacklisted(None)
        assert result is False

    @pytest.mark.anyio
    async def test_multiple_cleanup_calls(self, blacklist):
        """Test multiple cleanup operations."""
        # Add some expired tokens
        token1 = "expired1"
        token2 = "expired2"

        await blacklist.add_token(token1, datetime.now(UTC) - timedelta(hours=1))
        await blacklist.add_token(token2, datetime.now(UTC) - timedelta(hours=2))

        # Multiple cleanups should work
        result1 = await blacklist.cleanup_expired()
        result2 = await blacklist.cleanup_expired()

        assert result1 is None
        assert result2 is None
        assert len(blacklist._memory_blacklist) == 0

    @pytest.mark.anyio
    async def test_cleanup_with_no_expired_tokens(self, blacklist):
        """Test cleanup when no tokens are expired."""
        # Add valid token
        token = "valid_token"
        await blacklist.add_token(token, datetime.now(UTC) + timedelta(hours=1))

        result = await blacklist.cleanup_expired()

        assert result is None
        assert token in blacklist._memory_blacklist

    @pytest.mark.anyio
    async def test_concurrent_operations(self, blacklist):
        """Test concurrent token operations without sleep."""
        import asyncio

        # First, add all tokens
        for i in range(5):
            await blacklist.add_token(f"token_{i}", datetime.now(UTC) + timedelta(hours=1))

        # Then verify all can be checked concurrently
        check_tasks = [asyncio.create_task(blacklist.is_blacklisted(f"token_{i}")) for i in range(5)]

        results = await asyncio.gather(*check_tasks)

        # All tokens should be found
        assert all(results)
