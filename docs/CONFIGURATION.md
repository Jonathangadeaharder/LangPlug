# LangPlug Configuration Guide

## Overview

LangPlug uses environment variables for configuration across different deployment contexts. This document explains the purpose of each configuration file and how they interact.

---

## Configuration Files

### 1. `.env.example`

**Purpose**: Template for local development
**Location**: Project root
**Usage**: Copy to `.env` and customize

**Contains**:

- Required environment variables with example values
- Comments explaining each setting
- No sensitive data (safe to commit)

**When to use**: First-time setup, onboarding new developers

```bash
# Setup
cp .env.example .env
# Edit .env with your local values
```

---

### 2. `.env` (Local Development)

**Purpose**: Your personal development environment
**Location**: Project root (gitignored)
**Usage**: Automatically loaded by backend

**Contains**:

- Local database paths
- Development API keys
- Custom feature flags
- Local service URLs

**Security**: NEVER commit this file (already in `.gitignore`)

---

### 3. `.env.production`

**Purpose**: Production deployment settings
**Location**: Project root
**Usage**: Deployed to production environment

**Contains**:

- Production database URLs
- Production API endpoints
- Performance tuning settings
- Production feature flags

**Deployment**:

```bash
# Render.com, Heroku, etc. load this automatically
# Or manually: cp .env.production .env
```

---

### 4. `Backend/.env.testing`

**Purpose**: Test suite configuration
**Location**: `Backend/.env.testing`
**Usage**: Auto-loaded by pytest via `conftest.py`

**Contains**:

- Test database paths (usually in-memory SQLite)
- Fast model selections (whisper-tiny, opus-de-es)
- Test-specific feature flags
- Mock service URLs

**How it's loaded**:

```python
# Backend/tests/conftest.py
os.environ["TESTING"] = "1"
os.environ["LANGPLUG_TRANSCRIPTION_SERVICE"] = "whisper-tiny"
...
```

---

### 5. `Backend/core/config.py`

**Purpose**: Central configuration loader
**Location**: `Backend/core/config.py`
**Usage**: Imports settings into application

**Responsibilities**:

- Load environment variables
- Validate required settings
- Provide type-safe defaults
- Convert strings to proper types

**Usage in code**:

```python
from core.config import settings

database_url = settings.database_url
debug_mode = settings.debug
```

---

## Configuration Hierarchy

**Loading Order** (later overrides earlier):

1. Default values in `config.py`
2. `.env` file (development)
3. Environment variables (production/testing)
4. Test-specific overrides in `conftest.py` (tests only)

```
Defaults (config.py)
  ↓
Local .env
  ↓
Environment Variables
  ↓
Test Overrides (if testing)
```

---

## Key Settings Explained

### Database

```bash
# Development (local SQLite)
DATABASE_URL=sqlite:///./langplug.db

# Production (PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/langplug
```

### AI Services

```bash
# Transcription
LANGPLUG_TRANSCRIPTION_SERVICE=whisper-tiny  # Fast for dev/test
LANGPLUG_TRANSCRIPTION_SERVICE=whisper-base  # Production

# Translation
LANGPLUG_TRANSCRIPTION_SERVICE=opus-de-es    # Fast for dev/test
LANGPLUG_TRANSLATION_SERVICE=nllb-200        # Production
```

### Security

```bash
# JWT Secret (NEVER commit the real value!)
SECRET_KEY=your-super-secret-key-change-this

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Features

```bash
# Debug mode (enables extra endpoints, verbose logging)
LANGPLUG_DEBUG=true   # Development
LANGPLUG_DEBUG=false  # Production

# Sentry Error Tracking
SENTRY_DSN=https://...  # Production only
```

---

## Environment-Specific Settings

### Development

```bash
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./langplug_dev.db
TRANSCRIPTION_SERVICE=whisper-tiny
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Testing

```bash
TESTING=1
DEBUG=true
DATABASE_URL=sqlite:///:memory:  # In-memory for speed
TRANSCRIPTION_SERVICE=whisper-tiny
ANYIO_BACKEND=asyncio  # Disable trio
```

### Production

```bash
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://...
TRANSCRIPTION_SERVICE=whisper-base
SENTRY_DSN=https://...
CORS_ORIGINS=https://langplug.app
```

---

## Best Practices

### ✅ Do

- Use `.env.example` as template
- Keep sensitive data in `.env` (gitignored)
- Document all new environment variables
- Use type-safe defaults in `config.py`
- Test with `TESTING=1` before deployment

### ❌ Don't

- Commit `.env` to git
- Hard-code secrets in code
- Use production keys in development
- Skip validation in `config.py`
- Mix production and development configs

---

## Troubleshooting

### "Setting X not found"

1. Check if variable is in `.env.example`
2. Copy to your `.env`
3. Restart backend server

### "Tests failing with wrong config"

- Ensure `Backend/.env.testing` exists
- Check `conftest.py` for test overrides
- Run with `TESTING=1` environment variable

### "Different behavior in production"

- Compare `.env` vs `.env.production`
- Check for missing production-specific settings
- Verify environment variables in deployment platform

---

## Adding New Settings

When adding a new configuration:

1. **Add to `config.py`**:

```python
class Settings(BaseSettings):
    my_new_setting: str = Field(default="default_value", env="MY_NEW_SETTING")
```

2. **Add to `.env.example`**:

```bash
# My new feature setting
MY_NEW_SETTING=example_value
```

3. **Document here** with:
   - Purpose
   - Valid values
   - Default value
   - Required or optional

4. **Update `.env.production`** if different from development

---

## Configuration Audit Results

### ✅ No Conflicts Found

- All files have distinct purposes
- Clear separation of concerns
- Proper gitignore setup

### 📝 Recommendations

1. Consider consolidating test overrides from `conftest.py` into `Backend/.env.testing`
2. Add validation for required production settings
3. Create `Backend/.env.development` for clarity (currently just `.env`)

---

## References

- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Twelve-Factor App: https://12factor.net/config
- Environment Variables Best Practices: https://github.com/joho/godotenv#faq
