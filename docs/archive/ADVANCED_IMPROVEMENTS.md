# LangPlug Advanced Code Improvements - Phase 2

## Overview

Building on the Phase 1 fixes, this document outlines advanced improvements using proven libraries and best practices.

---

## 🎬 Option 2: Library Replacements

### 1. guessit - Video Filename Parsing

**Current Issue**: Manual regex parsing (`r"episode[\s_\.]*(\d+)"`) is fragile.

**Installation**: ✅ Done

**Improvement**: Replace with `guessit` library that handles:
- Episode numbering patterns: S01E01, 1x01, Episode 1, etc.
- Season detection
- Quality info (1080p, 720p)
- Codec detection
- Multiple naming conventions

**Implementation Location**: `src/backend/services/videoservice/video_service.py`

**Example**:
```python
from guessit import guessit

# Before: Manual regex
def parse_filename(filename):
    match = re.search(r"episode[\s_\.]*(\d+)", filename, re.IGNORECASE)
    return match.group(1) if match else None

# After: guessit
def parse_filename(filename):
    result = guessit(filename)
    return result.get('episode')  # Returns episode number
```

---

### 2. ffmpeg-python - FFmpeg Abstraction

**Current Issue**: Manual subprocess handling with OS-specific workarounds.

**Installation**: ✅ Done

**Improvement**: Abstract FFmpeg differences across platforms:
- Windows/Linux/Mac compatibility
- No platform-specific event loop workarounds needed
- Better error handling
- Cleaner API

**Implementation Location**: `src/backend/services/processing/chunk_transcription_service.py`

**Example**:
```python
import ffmpeg

# Before: Manual subprocess with platform workarounds
cmd = ["ffmpeg", "-i", str(video_file), "-ss", str(start_time), ...]
process = await asyncio.create_subprocess_exec(*cmd, ...)

# After: ffmpeg-python
stream = ffmpeg.input(str(video_file))
stream = ffmpeg.filter(stream, 'atrim', start=start_time, duration=duration)
out = ffmpeg.output(stream, str(audio_output))
ffmpeg.run(out)
```

---

### 3. pysrt - SRT File Handling

**Current Issue**: Manual SRT parsing and generation with timestamp formatting.

**Installation**: ✅ Done

**Improvement**: Robust SRT handling:
- Parse existing SRT files
- Generate SRT with proper formatting
- Handle edge cases
- Subtitle synchronization

**Implementation Location**: `src/backend/services/processing/chunk_transcription_service.py`

**Example**:
```python
import pysrt

# Before: Manual timestamp formatting
def format_srt_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

# After: pysrt
subs = pysrt.SubRipFile()
for i, segment in enumerate(segments):
    sub = pysrt.SubRipItem(
        index=i+1,
        start=pysrt.SubRipTime(milliseconds=segment.start_time*1000),
        end=pysrt.SubRipTime(milliseconds=segment.end_time*1000),
        text=segment.text
    )
    subs.append(sub)
subs.save(str(output_path))
```

---

### 4. redis - Distributed Caching

**Current Issue**: No caching layer for frequently accessed vocabulary.

**Installation**: ✅ Done

**Improvement**: Add Redis for:
- Vocabulary lookups caching
- User progress caching
- Session data
- Game state persistence
- Distributed system support

**Implementation Location**: `src/backend/core/cache/redis_client.py` (NEW)

**Example**:
```python
from redis import Redis

redis_client = Redis(host='localhost', port=6379, db=0)

# Cache vocabulary lookups
cache_key = f"vocab:{word}:{language}"
cached = redis_client.get(cache_key)
if cached:
    return json.loads(cached)

# Store in cache for 1 hour
redis_client.setex(cache_key, 3600, json.dumps(word_data))
```

---

## ⚡ Option 3: Performance Optimization

### 1. Database Query Profiling

**Goal**: Identify slow queries and optimize them.

**Implementation**:
```python
# Add to config.py
SQLALCHEMY_ECHO = True  # Log all SQL queries
SQLALCHEMY_ECHO_POOL = True  # Log connection pool

# Slow query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 2. Redis Vocabulary Caching

**Goal**: Cache frequently accessed vocabulary words.

**Implementation**:
```python
class VocabularyCacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour
    
    async def get_word_info(self, word: str, language: str, db: AsyncSession):
        cache_key = f"vocab:{word}:{language}"
        
        # Try cache first
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Fall back to database
        word_info = await self._query_database(word, language, db)
        
        # Cache result
        await self.redis.setex(cache_key, self.ttl, json.dumps(word_info))
        return word_info
```

### 3. Video Streaming Optimization

**Goal**: Optimize video delivery.

**Implementation**:
- Add range request support for partial downloads
- Implement video chunking
- Add adaptive bitrate support
- Optimize codec selection

### 4. Telemetry Monitoring

**Goal**: Track performance metrics.

**Implementation**:
```python
from telemetry import telemetryService

# Record API response time
async def track_request(endpoint: str, duration: float, status: int):
    telemetryService.recordApiResponseTime(endpoint, duration, status)

# Record database query time
async def track_db_query(query: str, duration: float):
    telemetryService.recordDatabaseQueryTime(query, duration)
```

---

## 🧪 Option 4: Testing & Quality

### 1. Full Test Suite with Coverage

```bash
# Run tests with coverage report
cd src/backend
pytest tests/ --cov=api --cov=services --cov=core \
    --cov-report=html --cov-report=term
```

**Expected**: >80% code coverage

### 2. Integration Tests for Fixed Components

**Tests needed**:
- DI pattern: Verify services can be mocked
- N+1 queries: Verify single DB connection
- Async I/O: Verify non-blocking operations
- Redis caching: Verify cache hits/misses

### 3. Performance Benchmarking

```bash
# Benchmark before/after
import timeit

# Subtitle processing
time_before = timeit.timeit(lambda: process_subtitles_old(), number=10)
time_after = timeit.timeit(lambda: process_subtitles_new(), number=10)
print(f"Speedup: {time_before / time_after}x")
```

### 4. Production Metrics

**Monitor**:
- Request latency (p50, p95, p99)
- Database query time
- Cache hit ratio
- API error rate
- Video streaming quality

---

## 📚 Option 5: Documentation & Onboarding

### 1. Runbooks for Operations

Create `OPERATIONS_RUNBOOK.md`:
- How to monitor the system
- How to handle common issues
- How to scale horizontally
- How to backup/restore

### 2. Architecture Diagrams

Create visualizations of:
- System architecture (Backend → Frontend → DB)
- Data flow (Video → Processing → SRT → Game)
- DI pattern flow
- Cache layer architecture

### 3. Troubleshooting Guide

Common issues and solutions:
- High database connection count
- Slow subtitle processing
- Redis connection failures
- Cache invalidation issues

### 4. Developer Setup Guide

Step-by-step guide for new developers:
- Clone repository
- Install dependencies
- Set environment variables
- Run tests
- Start development servers

---

## 📋 Implementation Plan

### Phase 2A: Library Integration (Days 1-2)
- [ ] Replace video filename parsing with guessit
- [ ] Replace FFmpeg subprocess with ffmpeg-python
- [ ] Replace SRT parsing with pysrt
- [ ] Set up Redis client
- [ ] Update requirements.txt

### Phase 2B: Performance Optimization (Days 3-4)
- [ ] Add query profiling
- [ ] Implement Redis caching layer
- [ ] Optimize video streaming
- [ ] Add telemetry tracking
- [ ] Benchmark improvements

### Phase 2C: Testing (Days 5-6)
- [ ] Expand test coverage to >80%
- [ ] Add integration tests
- [ ] Performance benchmarks
- [ ] Load testing

### Phase 2D: Documentation (Days 7-8)
- [ ] Create operations runbook
- [ ] Draw architecture diagrams
- [ ] Troubleshooting guide
- [ ] Developer setup guide

---

## 📊 Expected Outcomes

### Performance
- ✅ Video filename parsing: More robust (handles all formats)
- ✅ FFmpeg: Platform-independent
- ✅ SRT processing: More reliable
- ✅ Vocabulary lookups: 10-100x faster (with Redis)
- ✅ Overall: 50% faster for typical operations

### Code Quality
- ✅ Fewer custom implementations
- ✅ More maintainable
- ✅ Industry-standard libraries
- ✅ Better error handling

### Team Productivity
- ✅ Easier onboarding
- ✅ Better documentation
- ✅ Clear runbooks
- ✅ Less operational burden

---

## ⚠️ Implementation Notes

### Guessit
- Library: `from guessit import guessit`
- Pros: Handles complex naming patterns
- Cons: ~2MB dependency
- Risk: Low (read-only parsing)

### FFmpeg-Python
- Library: `import ffmpeg`
- Pros: Cleaner API, cross-platform
- Cons: Requires FFmpeg binary
- Risk: Medium (subprocess execution)

### pysrt
- Library: `import pysrt`
- Pros: Robust SRT handling
- Cons: ~200KB dependency
- Risk: Low (file manipulation)

### Redis
- Library: `from redis import Redis`
- Pros: High-performance caching
- Cons: New infrastructure dependency
- Risk: Medium (requires Redis server)

---

## 🔄 Rollback Strategy

Each improvement can be rolled back independently:
1. Keep old implementations in separate modules
2. Add feature flags to switch implementations
3. Test both versions in staging

---

## 📈 Success Metrics

- ✅ 100% test coverage for new code
- ✅ 80%+ coverage overall
- ✅ All video filenames parsed correctly
- ✅ No FFmpeg subprocess errors
- ✅ Cache hit ratio >70%
- ✅ 50% faster vocabulary lookups
- ✅ Operations team trained
- ✅ Zero security regressions

---

**Status**: Planning complete, ready for implementation
