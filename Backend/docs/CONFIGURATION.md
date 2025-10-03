# LangPlug Backend - Configuration Guide

**Version**: 1.0
**Last Updated**: 2025-10-03

Complete reference for configuring the LangPlug Backend application.

---

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Environment Variables](#environment-variables)
3. [Configuration Files](#configuration-files)
4. [Deployment Scenarios](#deployment-scenarios)
5. [Security Considerations](#security-considerations)
6. [Validation and Defaults](#validation-and-defaults)
7. [Troubleshooting](#troubleshooting)

---

## Configuration Overview

### Configuration Sources

LangPlug Backend reads configuration from multiple sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in Backend directory
3. **Default values** in `core/config.py`

### Configuration Philosophy

- **Environment-specific**: Different configurations for dev/staging/prod
- **Security-first**: Sensitive values via environment variables only
- **Validation**: All configurations validated at startup
- **Fail-fast**: Invalid configuration prevents server start

---

## Environment Variables

### Application Settings

#### `LANGPLUG_HOST`
- **Type**: String (IP address)
- **Default**: `0.0.0.0`
- **Description**: Server bind address
- **Valid Values**:
  - `0.0.0.0` - Listen on all interfaces (recommended for containers)
  - `127.0.0.1` - Localhost only (development)
  - Specific IP address
- **Example**:
  ```bash
  LANGPLUG_HOST=127.0.0.1
  ```

#### `LANGPLUG_PORT`
- **Type**: Integer
- **Default**: `8000`
- **Description**: Server port number
- **Valid Values**: 1024-65535 (recommended: 8000-9000)
- **Example**:
  ```bash
  LANGPLUG_PORT=8080
  ```

#### `LANGPLUG_DEBUG`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Enable debug mode (detailed error messages, auto-reload)
- **Valid Values**: `True`, `False`, `1`, `0`
- **Security**: ⚠️ **NEVER** enable in production
- **Example**:
  ```bash
  # Development
  LANGPLUG_DEBUG=True

  # Production
  LANGPLUG_DEBUG=False
  ```

#### `LANGPLUG_ENVIRONMENT`
- **Type**: String (enum)
- **Default**: `development`
- **Description**: Application environment
- **Valid Values**: `development`, `staging`, `production`
- **Impact**:
  - Controls logging verbosity
  - Affects CORS strictness
  - Influences error detail level
- **Example**:
  ```bash
  LANGPLUG_ENVIRONMENT=production
  ```

---

### Path Configuration

#### `LANGPLUG_VIDEOS_PATH`
- **Type**: String (directory path)
- **Default**: `../videos`
- **Description**: Root directory for video storage
- **Requirements**:
  - Must be writable by application
  - Sufficient disk space (videos are large)
  - Can be absolute or relative path
- **Example**:
  ```bash
  # Relative path
  LANGPLUG_VIDEOS_PATH=../videos

  # Absolute path
  LANGPLUG_VIDEOS_PATH=/mnt/storage/langplug/videos

  # Windows path (WSL)
  LANGPLUG_VIDEOS_PATH=/mnt/c/Videos/LangPlug
  ```

#### `LANGPLUG_DATA_PATH`
- **Type**: String (directory path)
- **Default**: `./data`
- **Description**: Directory for databases, user data, caches
- **Requirements**:
  - Must be writable
  - Contains SQLite database (if using SQLite)
  - Persists across restarts
- **Example**:
  ```bash
  LANGPLUG_DATA_PATH=./data
  ```

#### `LANGPLUG_LOGS_PATH`
- **Type**: String (directory path)
- **Default**: `./logs`
- **Description**: Directory for application logs
- **Requirements**:
  - Must be writable
  - Log rotation recommended for production
- **Example**:
  ```bash
  LANGPLUG_LOGS_PATH=/var/log/langplug
  ```

---

### Security Configuration

#### `LANGPLUG_SECRET_KEY`
- **Type**: String
- **Default**: None (must be provided)
- **Description**: Secret key for JWT token signing and encryption
- **Requirements**:
  - **Minimum 32 characters**
  - Random, unpredictable value
  - Different for each environment
  - **NEVER** commit to version control
- **Security**: 🔒 **CRITICAL** - Protects all authentication
- **Generation**:
  ```bash
  # Generate secure random key
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- **Example**:
  ```bash
  LANGPLUG_SECRET_KEY=your-generated-random-secret-key-at-least-32-characters
  ```

#### `LANGPLUG_SESSION_TIMEOUT_HOURS`
- **Type**: Integer
- **Default**: `24`
- **Description**: Session expiration time in hours
- **Valid Values**: 1-168 (1 hour to 7 days)
- **Security**: Shorter is more secure, longer is more convenient
- **Example**:
  ```bash
  # Development: Long sessions
  LANGPLUG_SESSION_TIMEOUT_HOURS=168

  # Production: Shorter sessions
  LANGPLUG_SESSION_TIMEOUT_HOURS=8
  ```

#### `LANGPLUG_CORS_ORIGINS`
- **Type**: Comma-separated list of URLs
- **Default**: `http://localhost:3000`
- **Description**: Allowed CORS origins for frontend
- **Requirements**:
  - Include protocol (http/https)
  - No trailing slashes
  - Comma-separated for multiple origins
- **Security**: Only allow trusted frontend URLs
- **Example**:
  ```bash
  # Development
  LANGPLUG_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

  # Production
  LANGPLUG_CORS_ORIGINS=https://app.langplug.com,https://www.langplug.com
  ```

---

### Database Configuration

#### `DATABASE_URL`
- **Type**: String (database URL)
- **Default**: `sqlite+aiosqlite:///./data/langplug.db`
- **Description**: Database connection string
- **Formats**:

  **SQLite** (Development):
  ```bash
  DATABASE_URL=sqlite+aiosqlite:///./data/langplug.db
  ```

  **PostgreSQL** (Production):
  ```bash
  DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/database
  ```

  **PostgreSQL with SSL**:
  ```bash
  DATABASE_URL=postgresql+asyncpg://user:password@host:5432/db?ssl=require
  ```

- **Security**:
  - Use strong passwords
  - Don't commit credentials
  - Use SSL in production
  - Restrict database user permissions

---

### AI Services Configuration

#### `LANGPLUG_TRANSCRIPTION_SERVICE`
- **Type**: String (enum)
- **Default**: `whisper`
- **Description**: Transcription service to use
- **Valid Values**:
  - `whisper` - OpenAI Whisper (local, offline)
  - `parakeet` - NVIDIA NeMo Parakeet (experimental)
- **Example**:
  ```bash
  LANGPLUG_TRANSCRIPTION_SERVICE=whisper
  ```

#### `LANGPLUG_TRANSCRIPTION_MODEL`
- **Type**: String (enum)
- **Default**: `tiny`
- **Description**: Whisper model size
- **Valid Values**: `tiny`, `base`, `small`, `medium`, `large`
- **Performance vs Accuracy**:
  | Model | Size | Speed | Accuracy | RAM |
  |-------|------|-------|----------|-----|
  | tiny | 75MB | Fastest | Good | ~1GB |
  | base | 140MB | Fast | Better | ~1GB |
  | small | 460MB | Medium | Very Good | ~2GB |
  | medium | 1.5GB | Slow | Excellent | ~5GB |
  | large | 2.9GB | Slowest | Best | ~10GB |

- **Recommendation**:
  - Development: `tiny` or `base`
  - Production: `small` or `medium`
  - High accuracy: `large` (requires GPU)
- **Example**:
  ```bash
  LANGPLUG_TRANSCRIPTION_MODEL=small
  ```

#### `LANGPLUG_TRANSLATION_SERVICE`
- **Type**: String (enum)
- **Default**: `opus`
- **Description**: Translation service to use
- **Valid Values**:
  - `opus` - Helsinki-NLP OPUS-MT (local, offline)
  - `nllb` - Meta NLLB (larger, more accurate)
- **Example**:
  ```bash
  LANGPLUG_TRANSLATION_SERVICE=opus
  ```

#### `LANGPLUG_TRANSLATION_MODEL`
- **Type**: String
- **Default**: Auto-selected based on language pair
- **Description**: Specific translation model to use
- **Format**: `{service}-{source}-{target}`
- **Examples**:
  ```bash
  # German to English
  LANGPLUG_TRANSLATION_MODEL=opus-de-en

  # Spanish to English
  LANGPLUG_TRANSLATION_MODEL=opus-es-en

  # NLLB distilled model
  LANGPLUG_TRANSLATION_MODEL=nllb-distilled-600m
  ```

---

### Language Settings

#### `LANGPLUG_DEFAULT_NATIVE_LANGUAGE`
- **Type**: String (ISO 639-1 code)
- **Default**: `en`
- **Description**: Default native language for new users
- **Valid Values**: `en`, `de`, `es`, `fr`, `it`, etc.
- **Example**:
  ```bash
  LANGPLUG_DEFAULT_NATIVE_LANGUAGE=en
  ```

#### `LANGPLUG_DEFAULT_TARGET_LANGUAGE`
- **Type**: String (ISO 639-1 code)
- **Default**: `de`
- **Description**: Default target learning language for new users
- **Valid Values**: `en`, `de`, `es`, `fr`, `it`, etc.
- **Example**:
  ```bash
  LANGPLUG_DEFAULT_TARGET_LANGUAGE=de
  ```

---

### Logging Configuration

#### `LANGPLUG_LOG_LEVEL`
- **Type**: String (enum)
- **Default**: `INFO`
- **Description**: Minimum log level to record
- **Valid Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Recommendations**:
  - Development: `DEBUG` or `INFO`
  - Production: `INFO` or `WARNING`
  - Troubleshooting: `DEBUG`
- **Example**:
  ```bash
  LANGPLUG_LOG_LEVEL=INFO
  ```

#### `LANGPLUG_LOG_FORMAT`
- **Type**: String (enum)
- **Default**: `detailed`
- **Description**: Log output format
- **Valid Values**:
  - `simple` - Minimal format (timestamp, level, message)
  - `detailed` - Include module, function, line number
  - `json` - Structured JSON logs (for log aggregation)
- **Example**:
  ```bash
  # Development
  LANGPLUG_LOG_FORMAT=detailed

  # Production (with ELK stack)
  LANGPLUG_LOG_FORMAT=json
  ```

---

### Optional Features

#### `LANGPLUG_RATE_LIMIT_ENABLED`
- **Type**: Boolean
- **Default**: `False`
- **Description**: Enable API rate limiting
- **Requirements**: Requires `slowapi` package
- **Example**:
  ```bash
  LANGPLUG_RATE_LIMIT_ENABLED=True
  LANGPLUG_RATE_LIMIT_PER_MINUTE=60
  ```

#### `REDIS_URL`
- **Type**: String (Redis URL)
- **Default**: None
- **Description**: Redis connection for caching/rate limiting
- **Format**: `redis://host:port/db`
- **Example**:
  ```bash
  REDIS_URL=redis://localhost:6379/0
  ```

#### `CELERY_BROKER_URL`
- **Type**: String (Broker URL)
- **Default**: None
- **Description**: Celery task queue broker (for background tasks)
- **Example**:
  ```bash
  CELERY_BROKER_URL=redis://localhost:6379/1
  CELERY_RESULT_BACKEND=redis://localhost:6379/2
  ```

---

## Configuration Files

### `.env` File

Create `.env` in the `Backend/` directory:

```bash
# Application
LANGPLUG_HOST=0.0.0.0
LANGPLUG_PORT=8000
LANGPLUG_DEBUG=True
LANGPLUG_ENVIRONMENT=development

# Paths
LANGPLUG_VIDEOS_PATH=../videos
LANGPLUG_DATA_PATH=./data
LANGPLUG_LOGS_PATH=./logs

# Security
LANGPLUG_SECRET_KEY=your-secret-key-change-this
LANGPLUG_SESSION_TIMEOUT_HOURS=24
LANGPLUG_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/langplug.db

# AI Services
LANGPLUG_TRANSCRIPTION_SERVICE=whisper
LANGPLUG_TRANSCRIPTION_MODEL=tiny
LANGPLUG_TRANSLATION_SERVICE=opus

# Languages
LANGPLUG_DEFAULT_NATIVE_LANGUAGE=en
LANGPLUG_DEFAULT_TARGET_LANGUAGE=de

# Logging
LANGPLUG_LOG_LEVEL=INFO
LANGPLUG_LOG_FORMAT=detailed
```

### `.env.example` File

Template for new developers (commit this to git):

```bash
# Application Settings
LANGPLUG_HOST=0.0.0.0
LANGPLUG_PORT=8000
LANGPLUG_DEBUG=True
LANGPLUG_ENVIRONMENT=development

# Paths (adjust for your system)
LANGPLUG_VIDEOS_PATH=../videos
LANGPLUG_DATA_PATH=./data
LANGPLUG_LOGS_PATH=./logs

# Security (CHANGE THESE!)
LANGPLUG_SECRET_KEY=CHANGE-THIS-TO-RANDOM-STRING-MIN-32-CHARS
LANGPLUG_SESSION_TIMEOUT_HOURS=24
LANGPLUG_CORS_ORIGINS=http://localhost:3000

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/langplug.db

# AI Services
LANGPLUG_TRANSCRIPTION_SERVICE=whisper
LANGPLUG_TRANSCRIPTION_MODEL=tiny
LANGPLUG_TRANSLATION_SERVICE=opus

# Languages
LANGPLUG_DEFAULT_NATIVE_LANGUAGE=en
LANGPLUG_DEFAULT_TARGET_LANGUAGE=de

# Logging
LANGPLUG_LOG_LEVEL=INFO
LANGPLUG_LOG_FORMAT=detailed
```

---

## Deployment Scenarios

### Development Environment

```bash
# .env.development
LANGPLUG_DEBUG=True
LANGPLUG_ENVIRONMENT=development
LANGPLUG_LOG_LEVEL=DEBUG
LANGPLUG_SECRET_KEY=dev-secret-key-not-for-production
DATABASE_URL=sqlite+aiosqlite:///./data/langplug_dev.db
LANGPLUG_TRANSCRIPTION_MODEL=tiny
LANGPLUG_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Characteristics**:
- Debug mode enabled
- Verbose logging
- Small AI models for speed
- SQLite database
- Permissive CORS

### Staging Environment

```bash
# .env.staging
LANGPLUG_DEBUG=False
LANGPLUG_ENVIRONMENT=staging
LANGPLUG_LOG_LEVEL=INFO
LANGPLUG_SECRET_KEY=${STAGING_SECRET_KEY}  # From secrets manager
DATABASE_URL=postgresql+asyncpg://user:${DB_PASSWORD}@db-staging:5432/langplug
LANGPLUG_TRANSCRIPTION_MODEL=small
LANGPLUG_TRANSLATION_MODEL=opus-de-en
LANGPLUG_CORS_ORIGINS=https://staging.langplug.com
```

**Characteristics**:
- Production-like configuration
- PostgreSQL database
- Medium AI models
- Stricter CORS
- Secrets from environment/vault

### Production Environment

```bash
# .env.production
LANGPLUG_DEBUG=False
LANGPLUG_ENVIRONMENT=production
LANGPLUG_LOG_LEVEL=WARNING
LANGPLUG_LOG_FORMAT=json
LANGPLUG_SECRET_KEY=${PROD_SECRET_KEY}  # From secrets manager
LANGPLUG_SESSION_TIMEOUT_HOURS=8
DATABASE_URL=postgresql+asyncpg://langplug:${DB_PASSWORD}@db-prod:5432/langplug?ssl=require
LANGPLUG_TRANSCRIPTION_MODEL=medium
LANGPLUG_TRANSLATION_MODEL=opus-de-en
LANGPLUG_CORS_ORIGINS=https://app.langplug.com
REDIS_URL=redis://${REDIS_PASSWORD}@redis-prod:6379/0
LANGPLUG_RATE_LIMIT_ENABLED=True
```

**Characteristics**:
- Debug disabled
- Minimal logging (warnings and errors)
- JSON logs for aggregation
- PostgreSQL with SSL
- Larger AI models for accuracy
- Rate limiting enabled
- Redis for caching
- Secrets from secure vault

---

## Security Considerations

### Secrets Management

❌ **NEVER** commit secrets to version control:

```bash
# .gitignore should include:
.env
.env.local
.env.*.local
*.key
*.pem
```

✅ **Best practices**:

1. **Development**: Use `.env` file (local only)
2. **CI/CD**: Use environment variables
3. **Production**: Use secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)

### Secret Generation

```bash
# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Output: Kx7j_9PLmNqRsWtUvYzBcDeFgHiJkLmN

# Generate database password
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### Database Security

1. **Use strong passwords**:
   - Minimum 16 characters
   - Mix of letters, numbers, symbols
   - Generated randomly

2. **Restrict permissions**:
   ```sql
   -- Create limited user
   CREATE USER langplug_app WITH PASSWORD 'strong_password';
   GRANT CONNECT ON DATABASE langplug TO langplug_app;
   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO langplug_app;
   ```

3. **Use SSL/TLS**:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
   ```

### CORS Security

Only allow trusted origins:

```bash
# ❌ BAD - Allows all origins
LANGPLUG_CORS_ORIGINS=*

# ✅ GOOD - Specific origins only
LANGPLUG_CORS_ORIGINS=https://app.langplug.com,https://www.langplug.com
```

---

## Validation and Defaults

### Configuration Validation

The application validates configuration at startup:

```python
# Example from core/config.py
class Settings(BaseSettings):
    secret_key: str = Field(..., min_length=32)  # Required, min 32 chars
    port: int = Field(8000, ge=1024, le=65535)   # Valid port range
    debug: bool = Field(False)                    # Default False
    environment: Literal["development", "staging", "production"]
```

**Validation Failures**:
- Application will not start
- Clear error message shown
- Fix configuration and restart

### Default Values

All configuration has sensible defaults:

| Variable | Default | Notes |
|----------|---------|-------|
| `LANGPLUG_HOST` | `0.0.0.0` | Listen on all interfaces |
| `LANGPLUG_PORT` | `8000` | Standard FastAPI port |
| `LANGPLUG_DEBUG` | `False` | Safe default (production) |
| `LANGPLUG_ENVIRONMENT` | `development` | Explicit environment required |
| `LANGPLUG_LOG_LEVEL` | `INFO` | Balance verbosity/performance |
| `LANGPLUG_TRANSCRIPTION_MODEL` | `tiny` | Fastest model for development |
| `DATABASE_URL` | SQLite in `./data` | No external dependencies |

---

## Troubleshooting

### Configuration Issues

#### **"SECRET_KEY must be at least 32 characters"**

**Solution**:
```bash
# Generate new secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
LANGPLUG_SECRET_KEY=<generated-secret>
```

#### **"Invalid DATABASE_URL format"**

**Solution**:
```bash
# Check URL format:
# sqlite+aiosqlite:///path/to/db.db
# postgresql+asyncpg://user:password@host:5432/database

# Ensure no spaces or special characters without encoding
```

#### **"CORS origin not allowed"**

**Solution**:
```bash
# Add frontend URL to LANGPLUG_CORS_ORIGINS
LANGPLUG_CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# No trailing slashes!
# ❌ http://localhost:3000/
# ✅ http://localhost:3000
```

#### **"Video path not found"**

**Solution**:
```bash
# Verify path exists
ls -la ../videos  # or your configured path

# Create if missing
mkdir -p ../videos

# Check permissions
chmod 755 ../videos
```

### Environment Variable Not Loading

**Symptoms**: Changes to `.env` not taking effect

**Solutions**:

1. **Restart server** (changes require restart)
2. **Check file location** (`.env` must be in `Backend/` directory)
3. **Check syntax** (no spaces around `=`):
   ```bash
   # ❌ BAD
   LANGPLUG_PORT = 8000

   # ✅ GOOD
   LANGPLUG_PORT=8000
   ```
4. **Check quotes** (usually not needed):
   ```bash
   # Simple values - no quotes
   LANGPLUG_PORT=8000

   # Values with spaces - use quotes
   LANGPLUG_LOG_MESSAGE="Application started"
   ```

---

## Configuration Management Tools

### View Current Configuration

```python
# Python script to view loaded configuration
from core.config import settings

print("Current Configuration:")
print(f"Environment: {settings.environment}")
print(f"Debug: {settings.debug}")
print(f"Host: {settings.host}")
print(f"Port: {settings.port}")
print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else settings.database_url}")
# Don't print secrets!
```

### Configuration Checklist

Before deploying:

- [ ] `SECRET_KEY` is random and secure (min 32 chars)
- [ ] `DEBUG` is `False` in production
- [ ] `LANGPLUG_ENVIRONMENT` matches deployment target
- [ ] `DATABASE_URL` points to correct database
- [ ] Database credentials are secure and not default
- [ ] `LANGPLUG_CORS_ORIGINS` includes only trusted URLs
- [ ] All paths (`VIDEOS_PATH`, `DATA_PATH`, `LOGS_PATH`) exist and are writable
- [ ] AI model sizes appropriate for resources
- [ ] Logging level appropriate for environment
- [ ] No secrets in version control (check `.gitignore`)

---

## Related Documentation

- **[DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)** - Development environment setup
- **[SECURITY_AND_TRANSACTIONS.md](../SECURITY_AND_TRANSACTIONS.md)** - Security features
- **[README.md](../README.md)** - Project overview

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: Development Team
