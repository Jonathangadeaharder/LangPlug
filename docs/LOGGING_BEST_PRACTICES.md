# Logging Best Practices

This document defines the logging standards for the LangPlug project.

## Backend (Python)

### Logger Acquisition

**Always use structlog via the centralized config:**

```python
# CORRECT
from core.config.logging_config import get_logger

logger = get_logger(__name__)

# WRONG - bypasses structlog configuration
import logging
logger = logging.getLogger(__name__)
```

### Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| **DEBUG** | Development diagnostics, loop iterations | `logger.debug("Processing segment", segment_id=i)` |
| **INFO** | Significant business events | `logger.info("Task completed", task_id=task_id, duration=elapsed)` |
| **WARNING** | Recoverable issues, deprecations | `logger.warning("Retry attempt", attempt=2, max=3)` |
| **ERROR** | Failures requiring attention | `logger.error("Database connection failed", error=str(e))` |

### Structured Logging

**Always use keyword arguments for context:**

```python
# CORRECT - structured, queryable
logger.info("User authenticated", user_id=user.id, method="oauth")

# WRONG - unstructured, hard to query
logger.info(f"User {user.id} authenticated via oauth")
```

### Hot Path Logging

**Avoid logging in frequently-called code:**

```python
# WRONG - logs every 2 seconds during polling
logger.debug(f"Progress check: {progress}%")

# CORRECT - log significant changes only
if progress % 10 == 0:  # Log every 10%
    logger.debug("Progress milestone", progress=progress)
```

### Sensitive Data

**Never log sensitive information:**

```python
# WRONG
logger.info("Login attempt", password=password, token=token)

# CORRECT
logger.info("Login attempt", user_email=email, has_token=bool(token))
```

### Correlation IDs

**Use task/request IDs to correlate logs:**

```python
logger.info("Processing started", task_id=task_id, user_id=user_id)
# ... later ...
logger.info("Processing complete", task_id=task_id, result_count=len(results))
```

---

## Frontend (TypeScript)

### Logger Usage

**Always use the structured logger service:**

```typescript
// CORRECT
import { logger } from '@/services/logger'

logger.info('Progress', 'Task started', { taskId, userId })
logger.error('Progress', 'Connection failed', { error: String(e) })

// WRONG - raw console calls
console.log('[Progress] Task started:', taskId)
console.error('Connection failed:', e)
```

### Log Levels

| Level | When to Use |
|-------|-------------|
| **debug** | Development only, detailed diagnostics |
| **info** | User actions, navigation, API responses |
| **warn** | Recoverable errors, deprecation notices |
| **error** | Failures, unhandled exceptions |

### API Logging

**Use the dedicated API logging methods:**

```typescript
// Request logging
logger.apiRequest('POST', '/api/process/chunk', { videoPath })

// Response logging (includes duration)
logger.apiResponse('POST', '/api/process/chunk', 200, response, durationMs)
```

### User Actions

**Track user interactions:**

```typescript
logger.userAction('clicked_start_processing', 'ChunkProcessor', {
  videoId,
  chunkNumber: 1,
})
```

### Performance

**Don't log in render loops or frequent callbacks:**

```typescript
// WRONG - logs 60 times per second
useEffect(() => {
  logger.debug('Render', 'Component updated')
})

// CORRECT - log significant state changes
useEffect(() => {
  if (status === 'completed') {
    logger.info('Task', 'Processing completed', { taskId })
  }
}, [status])
```

---

## Log Output Examples

### Backend (structlog JSON format)
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "logger": "services.processing.chunk_processor",
  "event": "Chunk processing started",
  "task_id": "chunk_123",
  "user_id": 456,
  "video_path": "Malcolm/S01E01.mp4"
}
```

### Frontend (sent to backend)
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "category": "Progress",
  "message": "Task started",
  "data": { "taskId": "chunk_123" },
  "url": "http://localhost:5173/learn/malcolm/1",
  "userId": "456"
}
```

---

## Migration Checklist

When updating existing code:

1. [ ] Replace `import logging` with `from core.config.logging_config import get_logger`
2. [ ] Replace `logging.getLogger(__name__)` with `get_logger(__name__)`
3. [ ] Replace f-string messages with structured kwargs
4. [ ] Remove hardcoded logger names (use `__name__`)
5. [ ] Add task/request IDs for correlation
6. [ ] Review log levels (DEBUG vs INFO)
7. [ ] Remove sensitive data from log messages
8. [ ] Replace `console.log` with `logger.debug/info/warn/error`
