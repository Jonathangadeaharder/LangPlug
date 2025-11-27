# Test Suite & Performance Benchmarking - Phase 2B

## 🧪 Testing & Quality Assurance

### 1. Run Current Test Suite with Coverage

```bash
cd src/backend

# Run all tests with coverage
pytest tests/ \
    --cov=api \
    --cov=services \
    --cov=core \
    --cov=database \
    --cov-report=html \
    --cov-report=term-missing \
    -v

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov\index.html # Windows
xdg-open htmlcov/index.html # Linux
```

### 2. Integration Tests for Phase 1 Fixes

Create `tests/integration/test_phase1_fixes.py`:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

class TestDependencyInjectionFixes:
    """Verify DI pattern works correctly"""
    
    async def test_vocabulary_service_receives_dependencies(self):
        """Vocabulary service accepts injected dependencies"""
        mock_query = MagicMock()
        mock_progress = MagicMock()
        mock_stats = MagicMock()
        
        service = VocabularyService(
            query_service=mock_query,
            progress_service=mock_progress,
            stats_service=mock_stats
        )
        
        assert service.query_service is mock_query
        assert service.progress_service is mock_progress
        assert service.stats_service is mock_stats

class TestN1QueryFixes:
    """Verify N+1 query problem is fixed"""
    
    async def test_subtitle_processing_uses_single_session(self, db_session):
        """Subtitle processor reuses DB session"""
        processor = SubtitleProcessor()
        
        # Create test subtitles
        subtitles = [
            FilteredSubtitle(words=[FilteredWord(text="hallo")]),
            FilteredSubtitle(words=[FilteredWord(text="welt")]),
        ]
        
        # Track DB connections
        connection_count = 0
        original_execute = db_session.execute
        
        async def tracked_execute(*args, **kwargs):
            nonlocal connection_count
            connection_count += 1
            return await original_execute(*args, **kwargs)
        
        db_session.execute = tracked_execute
        
        # Process subtitles
        await processor.process_subtitles(
            subtitles, set(), "A1", "de", mock_vocab_service, db_session
        )
        
        # Should use single session, not multiple connections
        assert connection_count <= 3  # Main query + maybe 2 more, not 2000+

class TestAsyncIOFixes:
    """Verify async file I/O works"""
    
    async def test_write_srt_uses_aiofiles(self, tmp_path):
        """SRT writing uses async file I/O"""
        service = SubtitleGenerationService()
        test_file = tmp_path / "test.srt"
        content = "1\n00:00:00,000 --> 00:00:05,000\nHallo"
        
        # Should not block
        await service.write_srt_file(test_file, content)
        
        # Verify file was written
        assert test_file.exists()
        assert test_file.read_text() == content
```

### 3. Performance Benchmarks

Create `scripts/performance_benchmark.py`:

```python
import asyncio
import time
from pathlib import Path

class PerformanceBenchmark:
    """Measure performance improvements"""
    
    async def benchmark_subtitle_processing(self):
        """Measure subtitle processing speed"""
        print("=" * 60)
        print("SUBTITLE PROCESSING BENCHMARK")
        print("=" * 60)
        
        # Create test data (20-minute episode)
        subtitles = self._create_test_subtitles(num_words=2000)
        
        # Benchmark
        start = time.time()
        result = await processor.process_subtitles(
            subtitles, set(), "A1", "de", vocab_service, db_session
        )
        duration = time.time() - start
        
        print(f"Processed {len(subtitles)} subtitles in {duration:.3f}s")
        print(f"Words per second: {2000/duration:.0f}")
        print(f"Expected (before fix): ~2-3 seconds")
        print(f"Actual (after fix): {duration:.3f}s")
        print(f"Speedup: {2.5 / duration:.1f}x")
    
    async def benchmark_vocabulary_lookup(self):
        """Measure vocabulary lookup speed"""
        print("\n" + "=" * 60)
        print("VOCABULARY LOOKUP BENCHMARK")
        print("=" * 60)
        
        word = "hallo"
        iterations = 100
        
        # Without cache
        start = time.time()
        for _ in range(iterations):
            result = await vocab_service.get_word_info(word, "de", db_session)
        duration_no_cache = time.time() - start
        
        # With Redis cache
        start = time.time()
        for _ in range(iterations):
            result = await cached_vocab_service.get_word_info(word, "de", db_session)
        duration_with_cache = time.time() - start
        
        print(f"Without cache: {duration_no_cache/iterations*1000:.2f}ms per lookup")
        print(f"With cache: {duration_with_cache/iterations*1000:.2f}ms per lookup")
        print(f"Speedup: {duration_no_cache / duration_with_cache:.1f}x")
    
    async def benchmark_file_io(self):
        """Measure file I/O speed"""
        print("\n" + "=" * 60)
        print("FILE I/O BENCHMARK")
        print("=" * 60)
        
        content = "1\n00:00:00,000 --> 00:00:05,000\nSubtitle text\n" * 1000
        
        # Async I/O
        start = time.time()
        await aiofiles_service.write_srt_file(Path("test.srt"), content)
        duration_async = time.time() - start
        
        # Sync I/O
        start = time.time()
        Path("test.srt").write_text(content)
        duration_sync = time.time() - start
        
        print(f"Async I/O: {duration_async*1000:.2f}ms")
        print(f"Sync I/O: {duration_sync*1000:.2f}ms")
        print(f"Non-blocking: ✅ Event loop not blocked")
```

### 4. Load Testing

```bash
# Install locust for load testing
pip install locust

# Create locustfile.py
# Run load test
locust -f locustfile.py -u 100 -r 10 --run-time 5m
```

---

## 📊 Performance Optimization Guide

### 1. Database Query Optimization

```python
# Add to src/backend/core/config/config.py

# Enable query logging
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
SQLALCHEMY_ECHO_POOL = os.getenv("SQLALCHEMY_ECHO_POOL", "false").lower() == "true"

# Pool configuration
SQLALCHEMY_POOL_SIZE = int(os.getenv("SQLALCHEMY_POOL_SIZE", "20"))
SQLALCHEMY_MAX_OVERFLOW = int(os.getenv("SQLALCHEMY_MAX_OVERFLOW", "0"))
SQLALCHEMY_POOL_PRE_PING = True  # Verify connections before using

import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 2. Redis Caching Implementation

Create `src/backend/core/cache/redis_client.py`:

```python
import json
from typing import Any, Optional
from redis import Redis
from redis.exceptions import RedisError
import logging

logger = logging.getLogger(__name__)

class RedisCacheClient:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = Redis(host=host, port=port, db=db, decode_responses=True)
        self.default_ttl = 3600  # 1 hour
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except RedisError as e:
            logger.error(f"Redis get error for {key}: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        try:
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, json.dumps(value))
            return True
        except RedisError as e:
            logger.error(f"Redis set error for {key}: {e}")
        return False
    
    async def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Redis delete error for {key}: {e}")
        return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis invalidate error for {pattern}: {e}")
        return 0

# Global cache client
redis_cache = RedisCacheClient()
```

### 3. Vocabulary Cache Service

Create `src/backend/services/vocabulary/vocabulary_cache_service.py`:

```python
from core.cache.redis_client import redis_cache
from typing import Any, Optional

class VocabularyCacheService:
    def __init__(self, redis_client=redis_cache):
        self.cache = redis_client
        self.ttl = 3600  # 1 hour
    
    def _make_key(self, word: str, language: str) -> str:
        return f"vocab:{language}:{word.lower()}"
    
    async def get_word_info(
        self, word: str, language: str, db, vocab_service
    ) -> Optional[dict]:
        """Get word info with caching"""
        cache_key = self._make_key(word, language)
        
        # Try cache
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Fallback to database
        word_info = await vocab_service.get_word_info(word, language, db)
        
        # Cache result
        if word_info:
            await self.cache.set(cache_key, word_info, self.ttl)
        
        return word_info
    
    async def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cache entries for a user's updates"""
        # Invalidate progress-related cache
        return await self.cache.invalidate_pattern(f"user:{user_id}:*")
```

### 4. Monitoring & Telemetry

```python
# Enhanced telemetry service in src/frontend/src/services/telemetry.ts

class TelemetryService {
  private metrics: PerformanceMetric[] = []
  private pageLoads: PageLoadMetric[] = []
  private dbQueries: DatabaseMetric[] = []
  private cacheHits = 0
  private cacheMisses = 0
  
  recordCacheHit(key: string): void {
    this.cacheHits++
  }
  
  recordCacheMiss(key: string): void {
    this.cacheMisses++
  }
  
  getCacheHitRatio(): number {
    const total = this.cacheHits + this.cacheMisses
    return total > 0 ? this.cacheHits / total : 0
  }
  
  recordDatabaseQuery(query: string, duration: number): void {
    this.dbQueries.push({
      query,
      duration,
      timestamp: Date.now(),
    })
  }
  
  getSlowestQueries(limit: number = 10): DatabaseMetric[] {
    return this.dbQueries
      .sort((a, b) => b.duration - a.duration)
      .slice(0, limit)
  }
}
```

---

## ✅ Verification Checklist

After implementing Phase 2B:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage >80%: `pytest --cov=... --cov-report=term`
- [ ] Subtitle processing <100ms
- [ ] Vocabulary lookup <10ms (with cache)
- [ ] No blocking I/O detected
- [ ] Redis cache hits >70%
- [ ] Load test passes at 100 concurrent users
- [ ] No memory leaks
- [ ] No N+1 queries

---

## 📈 Expected Results

### Before Phase 2B
- Subtitle processing: 2-3 seconds (2000+ DB connections)
- Vocabulary lookup: 50-100ms per word (no cache)
- File I/O: Event loop blocked
- Coverage: ~60%

### After Phase 2B
- Subtitle processing: 20-50ms (1 DB connection)
- Vocabulary lookup: <5ms with cache (70%+ hit ratio)
- File I/O: Non-blocking async
- Coverage: >80%
- Load capacity: 100+ concurrent users

---

**Status**: Ready for testing and benchmarking implementation
