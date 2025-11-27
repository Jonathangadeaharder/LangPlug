# Operations Runbook & Documentation - Phase 2D

## 📋 Operations Runbook

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LangPlug Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (React/TypeScript)                                 │
│  └─> React Query (Caching)                                   │
│      └─> Axios Client                                        │
│                                                               │
│  API Gateway (FastAPI)                                       │
│  └─> Route Handlers                                          │
│      └─> Services (DI)                                       │
│          ├─> Vocabulary Service                              │
│          ├─> Game Service                                    │
│          └─> Video Service                                   │
│                                                               │
│  Cache Layer (Redis)                                         │
│  └─> Vocabulary Cache                                        │
│  └─> Session Cache                                           │
│                                                               │
│  Database (SQLite/PostgreSQL)                                │
│  └─> Users                                                   │
│  └─> Vocabulary                                              │
│  └─> Progress                                                │
│  └─> Game Sessions                                           │
│                                                               │
│  File Storage                                                │
│  └─> Videos                                                  │
│  └─> SRT Files                                               │
│  └─> Audio Chunks                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Monitoring & Health Checks

### 1. System Health Check

```bash
#!/bin/bash
# scripts/health-check.sh

echo "LangPlug System Health Check"
echo "============================"

# Check Backend
echo -n "Backend API... "
curl -s http://localhost:8000/health && echo "✅" || echo "❌"

# Check Frontend
echo -n "Frontend... "
curl -s http://localhost:5173 > /dev/null && echo "✅" || echo "❌"

# Check Redis
echo -n "Redis Cache... "
redis-cli ping && echo "✅" || echo "❌"

# Check Database
echo -n "Database... "
sqlite3 data/langplug.db ".tables" > /dev/null && echo "✅" || echo "❌"

# Check Disk Space
echo -n "Disk Space... "
free_space=$(df /data | tail -1 | awk '{print $4}')
if [ "$free_space" -gt 1000000 ]; then echo "✅ ($(free_space/1024)MB)"; 
else echo "⚠️ (Low: $(free_space/1024)MB)"; fi
```

### 2. Performance Monitoring

```bash
#!/bin/bash
# scripts/monitor-performance.sh

# Monitor API response times
watch -n 5 'tail -100 logs/backend.log | grep "response_time" | tail -20'

# Monitor database connection pool
sqlite3 data/langplug.db "PRAGMA database_list;"

# Monitor Redis memory
redis-cli info memory | grep "used_memory_human"

# Monitor cache hit ratio
redis-cli info stats | grep "keyspace_hits\|keyspace_misses"
```

### 3. Logging Configuration

```python
# src/backend/core/logging_config.py

import logging
import logging.config
from pathlib import Path

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {funcName}:{lineno} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/langplug.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'performance': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/performance.log',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json',
        }
    },
    'loggers': {
        'api': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'performance': {
            'handlers': ['performance'],
            'level': 'DEBUG',
        }
    }
}
```

---

## 🚀 Deployment Procedures

### 1. Zero-Downtime Deployment

```bash
#!/bin/bash
# scripts/deploy-zero-downtime.sh

set -e

# Step 1: Pull new code
git pull origin main

# Step 2: Run tests
cd src/backend
pytest tests/ -q

# Step 3: Start new backend instance (on different port)
NEW_PORT=8001
python -m uvicorn main:app --port $NEW_PORT --reload &
NEW_PID=$!

# Step 4: Wait for new instance to be healthy
sleep 5
for i in {1..30}; do
    if curl -f http://localhost:$NEW_PORT/health; then
        echo "New instance healthy"
        break
    fi
    sleep 1
done

# Step 5: Switch traffic (update load balancer/nginx)
# nginx config: upstream backend { server 127.0.0.1:8001; }
systemctl reload nginx

# Step 6: Kill old instance
kill $(lsof -t -i:8000)
kill $NEW_PID

# Step 7: Start new instance on original port
python -m uvicorn main:app --port 8000 --reload &
```

### 2. Rollback Procedure

```bash
#!/bin/bash
# scripts/rollback.sh

echo "Rolling back to previous version..."

# Restore database backup
cp data/langplug.db.backup-$(date -d yesterday +%Y%m%d) data/langplug.db

# Revert code
git reset --hard HEAD~1
git clean -fd

# Reinstall dependencies
pip install -r src/backend/requirements.txt

# Restart services
systemctl restart langplug-backend
systemctl restart langplug-frontend

echo "Rollback complete"
```

---

## 🆘 Troubleshooting Guide

### Issue: High Database Connection Count

**Symptoms**: Database connection errors, slow queries

**Diagnosis**:
```bash
# Check current connections
sqlite3 data/langplug.db "PRAGMA database_list;"
lsof -p <python_pid> | grep database

# Check for N+1 queries
tail -100 logs/backend.log | grep "SELECT"
```

**Solution**:
1. Verify `subtitle_processor.py` uses passed `db` session
2. Check that vocabulary service isn't creating new sessions
3. Review recent code changes for database access

### Issue: Slow Vocabulary Lookups

**Symptoms**: Vocabulary endpoints taking >100ms

**Diagnosis**:
```bash
# Check Redis cache
redis-cli info stats | grep "keyspace"
redis-cli keys "vocab:*" | wc -l

# Check query performance
tail logs/backend.log | grep "vocabulary" | grep "time:"
```

**Solution**:
1. Verify Redis is running and connected
2. Check cache hit ratio (should be >70%)
3. Review database indexes on vocabulary table

### Issue: File I/O Blocking Event Loop

**Symptoms**: Frozen API during file operations

**Diagnosis**:
```bash
# Check for sync I/O in async code
grep -r "open(" src/backend/services --include="*.py" | grep "async def"

# Monitor event loop lag
tail logs/performance.log | grep "event_loop_lag"
```

**Solution**:
1. Ensure all file operations use `aiofiles`
2. Check for missing `async`/`await` keywords
3. Review subprocess calls (use ffmpeg-python instead)

### Issue: Redis Connection Failures

**Symptoms**: Cache errors, slow fallback to database

**Diagnosis**:
```bash
# Check Redis status
redis-cli ping
redis-cli info server

# Check connection logs
tail logs/backend.log | grep "redis"
```

**Solution**:
1. Restart Redis: `systemctl restart redis`
2. Check Redis port (default 6379)
3. Verify Redis credentials in config
4. Check network connectivity

---

## 📊 Metrics to Monitor

### Key Performance Indicators (KPIs)

```
Response Time:
  - API latency: <500ms (p95)
  - Vocabulary lookup: <10ms
  - Subtitle processing: <100ms
  - Video streaming: <2Mbps

Reliability:
  - Uptime: >99.9%
  - Error rate: <0.1%
  - Cache hit ratio: >70%

Capacity:
  - Concurrent users: 100+
  - Requests per second: 1000+
  - Database connections: <20
  - Memory usage: <500MB
```

### Alerting Rules

```yaml
# monitoring/alerts.yaml

alerts:
  - name: HighAPILatency
    condition: api_latency_p95 > 1000ms
    action: page_oncall
  
  - name: HighErrorRate
    condition: error_rate > 1%
    action: slack_notification
  
  - name: LowCacheHitRatio
    condition: cache_hit_ratio < 50%
    action: investigate
  
  - name: HighDatabaseConnections
    condition: db_connections > 30
    action: page_oncall
```

---

## 📚 Developer Setup Guide

### New Developer Onboarding

```bash
#!/bin/bash
# scripts/setup-dev-environment.sh

echo "LangPlug Development Environment Setup"
echo "======================================"

# 1. Clone repository
git clone https://github.com/yourorg/langplug.git
cd langplug

# 2. Install system dependencies
brew install python3.11 redis postgresql ffmpeg  # macOS
apt-get install python3.11 redis-server postgresql ffmpeg  # Ubuntu

# 3. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate  # Windows

# 4. Install Python dependencies
cd src/backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Install Node dependencies
cd ../frontend
npm install

# 6. Setup environment variables
cp .env.example .env
# Edit .env with your settings

# 7. Initialize database
cd ../backend
python -m pytest tests/unit/test_db.py  # Initialize DB

# 8. Start development servers
cd ../backend
python -m uvicorn main:app --reload  # Terminal 1

# Terminal 2:
cd src/frontend
npm run dev

# 9. Verify setup
curl http://localhost:8000/health
open http://localhost:5173
```

### IDE Setup

**VS Code Extensions**:
- Python
- Pylance
- Black Formatter
- ES Lint
- Prettier
- Thunder Client (API testing)

**VS Code Settings**:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true
}
```

---

## 📖 Documentation Templates

### Service Documentation Template

```markdown
# VocabularyService

## Purpose
Manages vocabulary lookups, filtering, and user progress tracking.

## Architecture
- Query Service: Read operations
- Progress Service: Write operations
- Stats Service: Analytics

## Dependencies
- Redis (optional, for caching)
- SQLAlchemy (database)

## Usage
\`\`\`python
service = VocabularyService(query_service, progress_service, stats_service)
word_info = await service.get_word_info("hallo", "de", db)
\`\`\`

## Performance
- Typical lookup: <10ms (with cache)
- Cache hit ratio: >70%

## Testing
\`\`\`bash
pytest tests/services/test_vocabulary_service.py -v
\`\`\`

## Troubleshooting
See OPERATIONS_RUNBOOK.md
```

---

## ✅ Deployment Checklist

Before deploying to production:

- [ ] All tests pass
- [ ] Code review completed
- [ ] Database backed up
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Runbooks reviewed
- [ ] Team trained
- [ ] Rollback plan tested
- [ ] Performance benchmarks OK
- [ ] Security reviewed

---

## 📞 Support Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| Backend Lead | slack: #backend | 9-5 UTC |
| DevOps | slack: #devops | 24/7 on-call |
| On-Call | pagerduty | Always |

---

**Status**: Ready for operational deployment

