# LangPlug Backend - Monitoring & Observability Guide

**Version**: 1.0
**Last Updated**: 2025-10-03

Guide for monitoring, logging, and observability in production.

---

## Table of Contents

1. [Overview](#overview)
2. [Logging Strategy](#logging-strategy)
3. [Health Checks](#health-checks)
4. [Metrics Collection](#metrics-collection)
5. [Alerting](#alerting)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### Observability Pillars

```
┌─────────────────────────────────────────────┐
│         OBSERVABILITY                       │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Logs    │  │ Metrics  │  │ Traces   │ │
│  │          │  │          │  │          │ │
│  │  What    │  │  How     │  │  Where   │ │
│  │  Happened│  │  Much    │  │  Time    │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
```

**Logs**: Event details (what happened, when, context)
**Metrics**: Quantitative data (requests/sec, CPU%, latency)
**Traces**: Request flow through system (distributed tracing)

---

## Logging Strategy

### Log Levels

LangPlug uses **5 log levels**:

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Development details | `"Executing query: SELECT * FROM users WHERE id=123"` |
| **INFO** | Normal operations | `"User logged in: johndoe"` |
| **WARNING** | Potential issues | `"API rate limit approaching for user 123"` |
| **ERROR** | Errors that don't stop app | `"Failed to process video chunk: timeout"` |
| **CRITICAL** | System-breaking errors | `"Database connection lost"` |

**Production**: Use `WARNING` level (only warnings, errors, critical)
**Staging**: Use `INFO` level
**Development**: Use `DEBUG` level

### Log Configuration

**Environment Variable**:
```bash
# Production
LANGPLUG_LOG_LEVEL=WARNING
LANGPLUG_LOG_FORMAT=json

# Development
LANGPLUG_LOG_LEVEL=DEBUG
LANGPLUG_LOG_FORMAT=detailed
```

### Log Formats

**JSON Format** (recommended for production):
```json
{
  "timestamp": "2025-10-03T10:30:45.123Z",
  "level": "ERROR",
  "logger": "services.processing.chunk_processor",
  "message": "Failed to transcribe audio",
  "context": {
    "user_id": "123e4567",
    "video_id": "video_001",
    "chunk_id": "chunk_005",
    "error": "Whisper model timeout"
  }
}
```

**Detailed Format** (development):
```
2025-10-03 10:30:45,123 - ERROR - services.processing.chunk_processor:142 - Failed to transcribe audio
  user_id: 123e4567
  video_id: video_001
  chunk_id: chunk_005
  error: Whisper model timeout
```

### Application Logging

**Good logging practices**:

```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD - Structured logging with context
logger.info(
    "User login successful",
    extra={
        "user_id": user.id,
        "username": user.username,
        "ip_address": request.client.host
    }
)

# ✅ GOOD - Error with exception context
try:
    result = process_video(video_id)
except Exception as e:
    logger.error(
        f"Video processing failed: {e}",
        extra={"video_id": video_id},
        exc_info=True  # Include stack trace
    )

# ❌ BAD - Vague message, no context
logger.info("Processing started")

# ❌ BAD - Using print instead of logger
print("User logged in")
```

### Log Aggregation

#### Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.10.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.10.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

**Logstash configuration** (`logstash.conf`):
```
input {
  file {
    path => "/var/log/langplug/*.log"
    codec => "json"
  }
}

filter {
  # Parse JSON logs
  json {
    source => "message"
  }

  # Add timestamp
  date {
    match => ["timestamp", "ISO8601"]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "langplug-logs-%{+YYYY.MM.dd}"
  }
}
```

#### Option 2: Loki + Grafana (Lightweight)

```yaml
# docker-compose.loki.yml
version: '3.8'

services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log/langplug:/var/log/langplug:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## Health Checks

### Application Health Endpoint

**Basic health check**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
```

**Detailed health check** (database, AI models, disk space):
```python
@app.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    checks = {}

    # Database check
    try:
        await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"

    # Disk space check
    import shutil
    stats = shutil.disk_usage("/var/lib/langplug")
    free_percent = (stats.free / stats.total) * 100
    checks["disk_space"] = {
        "status": "healthy" if free_percent > 10 else "warning",
        "free_percent": round(free_percent, 2)
    }

    # AI model check
    try:
        from services.transcriptionservice.factory import get_transcription_service
        service = get_transcription_service("whisper")
        checks["ai_models"] = "healthy"
    except Exception as e:
        checks["ai_models"] = f"unhealthy: {str(e)}"

    # Overall status
    overall = "healthy" if all(
        v == "healthy" or (isinstance(v, dict) and v.get("status") == "healthy")
        for v in checks.values()
    ) else "degraded"

    return {"status": overall, "checks": checks}
```

### External Health Monitoring

**UptimeRobot** (free tier):
- Monitor: https://app.langplug.com/health
- Check interval: 5 minutes
- Alert: Email/SMS when down

**Pingdom**, **StatusCake**, or **Better Uptime** are alternatives.

---

## Metrics Collection

### Prometheus + Grafana

**Install Prometheus exporter**:
```bash
pip install prometheus-fastapi-instrumentator
```

**Add to `main.py`**:
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Instrument FastAPI
Instrumentator().instrument(app).expose(app)
```

**Metrics endpoint**: `http://localhost:8000/metrics`

**Example metrics**:
```
# HTTP request duration
http_request_duration_seconds_bucket{le="0.5",method="GET",path="/api/profile"} 1234
http_request_duration_seconds_count{method="GET",path="/api/profile"} 1500

# HTTP requests total
http_requests_total{method="GET",path="/api/profile",status="200"} 1450
http_requests_total{method="GET",path="/api/profile",status="401"} 50

# Active requests
http_requests_inprogress{method="GET",path="/api/processing/chunk"} 5
```

### Custom Metrics

**Add business metrics**:
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
video_uploads_total = Counter(
    'langplug_video_uploads_total',
    'Total video uploads',
    ['status']  # success, failed
)

video_processing_duration = Histogram(
    'langplug_video_processing_seconds',
    'Video processing duration',
    buckets=[10, 30, 60, 120, 300]  # seconds
)

active_users = Gauge(
    'langplug_active_users',
    'Number of active users'
)

# Use metrics
video_uploads_total.labels(status='success').inc()

with video_processing_duration.time():
    process_video(video_id)

active_users.set(count_active_users())
```

### Grafana Dashboards

**Key metrics to track**:

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Request Rate** | Requests per second | Alert if >1000 |
| **Error Rate** | 4xx/5xx responses | Alert if >5% |
| **Response Time (P95)** | 95th percentile latency | Alert if >1000ms |
| **CPU Usage** | Server CPU utilization | Alert if >80% |
| **Memory Usage** | Server memory utilization | Alert if >90% |
| **Disk Usage** | Disk space remaining | Alert if <10% |
| **Database Connections** | Active DB connections | Alert if >80% pool |

---

## Alerting

### Alert Rules

**Prometheus alert rules** (`alerts.yml`):
```yaml
groups:
  - name: langplug_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Slow responses
      - alert: SlowResponses
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow API responses"
          description: "P95 latency is {{ $value }}s"

      # Database down
      - alert: DatabaseDown
        expr: up{job="langplug_backend",check="database"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"

      # Disk space low
      - alert: DiskSpaceLow
        expr: disk_free_percent < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space low: {{ $value }}%"
```

### Alert Destinations

**Slack webhook**:
```yaml
# alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

**Email**:
```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'ops@langplug.com'
        from: 'alerts@langplug.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@langplug.com'
        auth_password: '${SMTP_PASSWORD}'
```

---

## Troubleshooting

### Common Issues

#### High CPU Usage

**Check**:
```bash
# Find process consuming CPU
top -u langplug

# Check which endpoint is slow
tail -f /var/log/langplug/langplug.log | grep "duration"
```

**Solutions**:
- Scale horizontally (add more workers)
- Optimize AI model (use smaller model)
- Add caching (Redis)
- Profile code (`cProfile`)

#### Memory Leaks

**Check**:
```bash
# Monitor memory over time
watch -n 5 "ps aux | grep uvicorn"

# Check for memory growth
cat /proc/$(pgrep -f uvicorn)/status | grep VmRSS
```

**Solutions**:
- Use smaller AI models
- Implement batch processing
- Clear caches periodically
- Restart workers periodically

#### Database Connection Pool Exhausted

**Check**:
```bash
# PostgreSQL active connections
psql -U langplug -d langplug -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

**Solutions**:
- Increase pool size in SQLAlchemy
- Fix slow queries (add indexes)
- Ensure connections are properly closed
- Use connection pooling (pgBouncer)

### Log Analysis

**Find errors in last hour**:
```bash
journalctl -u langplug --since "1 hour ago" | grep ERROR
```

**Most common errors**:
```bash
grep ERROR /var/log/langplug/*.log | \
  cut -d':' -f4- | sort | uniq -c | sort -rn | head -10
```

**Slowest endpoints**:
```bash
grep "duration" /var/log/langplug/*.log | \
  awk '{print $NF, $(NF-2)}' | sort -rn | head -20
```

---

## Related Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment procedures
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration reference
- **[DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)** - Local setup

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: DevOps Team
