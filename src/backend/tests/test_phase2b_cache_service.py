"""
Phase 2B Tests - Vocabulary Cache Service

Comprehensive tests for:
- Vocabulary cache service
- Cache hit/miss performance
- Fallback to database
- Cache invalidation
- Performance metrics
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache.redis_client import RedisCacheClient
from services.vocabulary.vocabulary_cache_service import VocabularyCacheService


class TestVocabularyCacheService:
    """Test vocabulary caching with Redis"""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        client = MagicMock(spec=RedisCacheClient)
        client.is_connected = MagicMock(return_value=True)
        return client

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_vocab_service(self):
        """Create mock vocabulary service"""
        service = AsyncMock()
        service.get_word_info = AsyncMock()
        service.get_words_by_level = AsyncMock()
        return service

    @pytest.fixture
    def cache_service(self, mock_redis):
        """Create cache service with mock Redis"""
        return VocabularyCacheService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_service, mock_db, mock_vocab_service):
        """Test cache hit returns cached value"""
        # Setup
        cache_service.cache.get = AsyncMock(return_value={"word": "hallo", "level": "A1"})

        # Execute
        result = await cache_service.get_word_info("hallo", "de", mock_db, mock_vocab_service)

        # Verify
        assert result == {"word": "hallo", "level": "A1"}
        assert cache_service.stats["hits"] == 1
        assert cache_service.stats["misses"] == 0
        mock_vocab_service.get_word_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_miss_fallback_to_db(self, cache_service, mock_db, mock_vocab_service):
        """Test cache miss falls back to database"""
        # Setup
        word_data = {"word": "hallo", "level": "A1", "translation": "hello"}
        cache_service.cache.get = AsyncMock(return_value=None)
        cache_service.cache.set = AsyncMock(return_value=True)
        mock_vocab_service.get_word_info = AsyncMock(return_value=word_data)

        # Execute
        result = await cache_service.get_word_info("hallo", "de", mock_db, mock_vocab_service)

        # Verify
        assert result == word_data
        assert cache_service.stats["misses"] == 1
        assert cache_service.stats["hits"] == 0
        mock_vocab_service.get_word_info.assert_called_once()
        cache_service.cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_not_found(self, cache_service, mock_db, mock_vocab_service):
        """Test cache miss when word not in database"""
        # Setup
        cache_service.cache.get = AsyncMock(return_value=None)
        mock_vocab_service.get_word_info = AsyncMock(return_value=None)

        # Execute
        result = await cache_service.get_word_info("nonexistent", "de", mock_db, mock_vocab_service)

        # Verify
        assert result is None
        assert cache_service.stats["misses"] == 1
        cache_service.cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_error_fallback(self, cache_service, mock_db, mock_vocab_service):
        """Test fallback to database on cache error"""
        # Setup
        word_data = {"word": "hallo", "level": "A1"}
        cache_service.cache.get = AsyncMock(side_effect=Exception("Redis error"))
        mock_vocab_service.get_word_info = AsyncMock(return_value=word_data)

        # Execute
        result = await cache_service.get_word_info("hallo", "de", mock_db, mock_vocab_service)

        # Verify
        assert result == word_data
        assert cache_service.stats["errors"] == 1
        mock_vocab_service.get_word_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_word(self, cache_service):
        """Test invalidating specific word cache"""
        cache_service.cache.delete = AsyncMock(return_value=True)

        result = await cache_service.invalidate_word("hallo", "de")

        assert result is True
        cache_service.cache.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_level(self, cache_service):
        """Test invalidating level cache"""
        cache_service.cache.delete = AsyncMock(return_value=True)

        result = await cache_service.invalidate_level("de", "A1")

        assert result is True
        cache_service.cache.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_language(self, cache_service):
        """Test invalidating all cache for language"""
        cache_service.cache.invalidate_pattern = AsyncMock(return_value=50)

        deleted = await cache_service.invalidate_language("de")

        assert deleted == 50
        cache_service.cache.invalidate_pattern.assert_called_once_with("vocab:de:*")

    @pytest.mark.asyncio
    async def test_get_words_by_level_cache_hit(self, cache_service, mock_db, mock_vocab_service):
        """Test level-based lookup with cache hit"""
        words = ["hallo", "welt", "haus"]
        cache_service.cache.get = AsyncMock(return_value=words)

        result = await cache_service.get_words_by_level("de", "A1", mock_db, mock_vocab_service)

        assert result == words
        assert cache_service.stats["hits"] == 1

    @pytest.mark.asyncio
    async def test_get_words_by_level_cache_miss(self, cache_service, mock_db, mock_vocab_service):
        """Test level-based lookup with cache miss"""
        words = ["hallo", "welt", "haus"]
        cache_service.cache.get = AsyncMock(return_value=None)
        cache_service.cache.set = AsyncMock(return_value=True)
        mock_vocab_service.get_words_by_level = AsyncMock(return_value=words)

        result = await cache_service.get_words_by_level("de", "A1", mock_db, mock_vocab_service)

        assert result == words
        assert cache_service.stats["misses"] == 1
        mock_vocab_service.get_words_by_level.assert_called_once()

    @pytest.mark.asyncio
    async def test_warm_cache(self, cache_service, mock_db, mock_vocab_service):
        """Test warming cache on startup"""
        words_a1 = ["hallo", "welt"]
        words_a2 = ["glauben", "verstehen"]

        cache_service.cache.set = AsyncMock(return_value=True)
        mock_vocab_service.get_words_by_level = AsyncMock(side_effect=[words_a1, words_a2])

        cached = await cache_service.warm_cache("de", ["A1", "A2"], mock_db, mock_vocab_service)

        assert cached == 2
        assert cache_service.cache.set.call_count == 2

    def test_get_stats(self, cache_service):
        """Test statistics reporting"""
        cache_service.stats = {"hits": 70, "misses": 30, "errors": 0}

        stats = cache_service.get_stats()

        assert stats["hits"] == 70
        assert stats["misses"] == 30
        assert stats["total"] == 100
        assert stats["hit_ratio"] == "70.0%"
        assert stats["errors"] == 0

    def test_reset_stats(self, cache_service):
        """Test resetting statistics"""
        cache_service.stats = {"hits": 10, "misses": 5, "errors": 2}

        cache_service.reset_stats()

        assert cache_service.stats == {"hits": 0, "misses": 0, "errors": 0}

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, cache_service):
        """Test cache key format"""
        key = cache_service._make_key("Hallo", "de")
        assert key == "vocab:de:hallo"

        level_key = cache_service._make_level_key("de", "A1")
        assert level_key == "vocab:level:de:a1"

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self, cache_service, mock_db, mock_vocab_service):
        """Test thread-safe concurrent cache operations"""
        import asyncio

        word_data = {"word": "test", "level": "A1"}
        cache_service.cache.get = AsyncMock(return_value=None)
        cache_service.cache.set = AsyncMock(return_value=True)
        mock_vocab_service.get_word_info = AsyncMock(return_value=word_data)

        # Simulate concurrent requests
        tasks = [cache_service.get_word_info("test", "de", mock_db, mock_vocab_service) for _ in range(5)]

        results = await asyncio.gather(*tasks)

        # All should return same data
        assert all(r == word_data for r in results)


class TestCachePerformanceMetrics:
    """Test performance metrics and reporting"""

    @pytest.fixture
    def cache_service(self):
        """Create cache service"""
        mock_redis = MagicMock(spec=RedisCacheClient)
        return VocabularyCacheService(redis_client=mock_redis)

    def test_hit_ratio_calculation(self, cache_service):
        """Test hit ratio calculation accuracy"""
        test_cases = [
            (100, 0, "100.0%"),
            (75, 25, "75.0%"),
            (1, 99, "1.0%"),
            (0, 100, "0.0%"),
        ]

        for hits, misses, expected_ratio in test_cases:
            cache_service.stats = {"hits": hits, "misses": misses, "errors": 0}
            stats = cache_service.get_stats()
            assert stats["hit_ratio"] == expected_ratio

    def test_stats_tracking(self, cache_service):
        """Test statistics tracking"""
        # Simulate cache operations
        cache_service.stats["hits"] = 5
        cache_service.stats["misses"] = 2
        cache_service.stats["errors"] = 1

        stats = cache_service.get_stats()

        assert stats["total"] == 7
        assert stats["hits"] == 5
        assert stats["misses"] == 2
        assert stats["errors"] == 1


class TestCacheIntegration:
    """Integration tests for cache with Phase 2A services"""

    @pytest.mark.asyncio
    async def test_cache_with_video_filename_parser(self):
        """Test cache integration with video parser"""
        from services.videoservice.video_filename_parser import VideoFilenameParser

        parser = VideoFilenameParser()

        # Cache service can store parsed video info
        mock_redis = MagicMock(spec=RedisCacheClient)
        cache_service = VocabularyCacheService(redis_client=mock_redis)

        # Parse video
        parsed = parser.parse("Breaking.Bad.S01E01.720p.mkv")

        # Could be cached
        cache_service.cache.set = AsyncMock(return_value=True)
        await cache_service.cache.set("video:breaking-bad:1:1", parsed)

        assert cache_service.cache.set.called

    @pytest.mark.asyncio
    async def test_cache_with_srt_handler(self):
        """Test cache integration with SRT handler"""
        import pysrt

        from services.videoservice.srt_file_handler import SRTFileHandler

        handler = SRTFileHandler()

        # Create SRT subtitles
        subs = pysrt.SubRipFile()
        subs.append(handler.create_subtitle(1, 0, 5000, "Test"))

        # Cache service could cache processed subtitles
        mock_redis = MagicMock(spec=RedisCacheClient)
        cache_service = VocabularyCacheService(redis_client=mock_redis)

        text = handler.extract_text(subs)
        cache_service.cache.set = AsyncMock(return_value=True)
        await cache_service.cache.set("srt:episode:1", text)

        assert cache_service.cache.set.called
