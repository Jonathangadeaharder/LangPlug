# LangPlug Backend - Developer Setup Guide

**Version**: 1.0
**Last Updated**: 2025-10-03

Complete guide for setting up the LangPlug Backend development environment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [IDE Configuration](#ide-configuration)
4. [Database Setup](#database-setup)
5. [Running the Development Server](#running-the-development-server)
6. [Running Tests](#running-tests)
7. [Debugging](#debugging)
8. [Code Quality Tools](#code-quality-tools)
9. [Environment Variables](#environment-variables)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software               | Minimum Version | Recommended | Installation                                    |
| ---------------------- | --------------- | ----------- | ----------------------------------------------- |
| **Python**             | 3.11.0          | 3.11.7      | [python.org](https://www.python.org/downloads/) |
| **Git**                | 2.30+           | Latest      | [git-scm.com](https://git-scm.com/)             |
| **FFmpeg**             | 4.4+            | Latest      | [ffmpeg.org](https://ffmpeg.org/download.html)  |
| **Node.js** (Frontend) | 18.0+           | 20.x LTS    | [nodejs.org](https://nodejs.org/)               |

### Optional Software

| Software       | Purpose                | Installation                                                |
| -------------- | ---------------------- | ----------------------------------------------------------- |
| **Docker**     | PostgreSQL for testing | [docker.com](https://www.docker.com/)                       |
| **PostgreSQL** | Production database    | [postgresql.org](https://www.postgresql.org/)               |
| **VS Code**    | Recommended IDE        | [code.visualstudio.com](https://code.visualstudio.com/)     |
| **PyCharm**    | Alternative IDE        | [jetbrains.com/pycharm](https://www.jetbrains.com/pycharm/) |

### System Requirements

- **OS**: Windows 10/11 (with WSL2), macOS 12+, or Linux (Ubuntu 20.04+)
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space (AI models require significant storage)
- **CPU**: Multi-core processor recommended for parallel testing

### Platform-Specific Notes

#### Windows (WSL2 Required)

**Why WSL2?** The project uses Python libraries that work best in a Linux environment. WSL2 provides a native Linux kernel on Windows.

1. **Enable WSL2**:

   ```powershell
   # Run in PowerShell as Administrator
   wsl --install
   wsl --set-default-version 2
   ```

2. **Install Ubuntu**:

   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

3. **Verify Installation**:

   ```bash
   wsl -l -v
   # Should show Ubuntu with VERSION 2
   ```

4. **Important**: All development should be done **inside WSL2**, not in Windows directly.

#### macOS

1. **Install Homebrew** (package manager):

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install FFmpeg**:

   ```bash
   brew install ffmpeg
   ```

3. **Install Python 3.11**:
   ```bash
   brew install python@3.11
   ```

#### Linux (Ubuntu/Debian)

```bash
# Update package lists
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install FFmpeg
sudo apt install ffmpeg

# Install build essentials (for compiling Python packages)
sudo apt install build-essential
```

---

## Initial Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-org/LangPlug.git
cd LangPlug/Backend

# Verify you're in the correct directory
pwd
# Should show: .../LangPlug/Backend
```

### 2. Create Virtual Environment

**Why?** Virtual environments isolate project dependencies from system Python.

```bash
# Create virtual environment
python3.11 -m venv api_venv

# Activate virtual environment
# On Linux/macOS/WSL:
source api_venv/bin/activate

# On Windows (PowerShell - NOT recommended, use WSL):
# api_venv\Scripts\Activate.ps1

# Verify activation (should show path to api_venv)
which python
# Should show: .../LangPlug/Backend/api_venv/bin/python
```

**Important**: Always activate the virtual environment before working on the project.

### 3. Install Dependencies

```bash
# Ensure virtual environment is activated
source api_venv/bin/activate

# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt

# This will take 5-10 minutes (many packages, some compile from source)
```

**Troubleshooting Installation**:

If you encounter errors during installation:

```bash
# Missing Python headers (Linux)
sudo apt install python3.11-dev

# Missing compiler (Linux)
sudo apt install build-essential

# Missing FFmpeg development libraries (Linux)
sudo apt install libavcodec-dev libavformat-dev libavutil-dev

# macOS: Install Xcode command line tools
xcode-select --install
```

### 4. Install AI Models

The project uses AI models for transcription and translation. These are large downloads.

```bash
# Install spaCy language models (German and English)
python install_spacy_models.py

# Download Whisper model (for transcription)
# This happens automatically on first use, but you can pre-download:
# python download_whisper_model.py  # If script exists
```

**Model Sizes**:

- `de_core_news_sm` (German): ~15MB
- `en_core_web_sm` (English): ~13MB
- Whisper `tiny` model: ~75MB
- Whisper `base` model: ~140MB
- Whisper `small` model: ~460MB

**Recommendation**: Use `whisper-tiny` for development, larger models for production.

### 5. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

See [Environment Variables](#environment-variables) section for complete reference.

### 6. Initialize Database

```bash
# Create database directory
mkdir -p data

# Run database migrations
python -m alembic upgrade head

# Verify database was created
ls -la data/
# Should see: langplug.db
```

### 7. Verify Installation

```bash
# Run a simple health check
python -c "from main import app; print('✓ FastAPI app imports successfully')"

# Check if all imports work
python -c "import services.transcriptionservice; print('✓ Services import successfully')"

# Verify test suite can be collected
python -m pytest --collect-only -q | tail -5
# Should show: "XXXX tests collected in X.XXs"
```

✅ **If all commands succeed, your environment is ready!**

---

## IDE Configuration

### VS Code (Recommended)

#### Required Extensions

Install these extensions for the best development experience:

1. **Python** (`ms-python.python`) - Python language support
2. **Pylance** (`ms-python.vscode-pylance`) - Fast type checking and IntelliSense
3. **Ruff** (`charliermarsh.ruff`) - Fast Python linter and formatter
4. **GitLens** (`eamodio.gitlens`) - Git integration

#### Recommended Extensions

- **Better Comments** (`aaron-bond.better-comments`) - Colorful comments
- **Error Lens** (`usernamehw.errorlens`) - Inline error messages
- **Python Test Explorer** (`littlefoxteam.vscode-python-test-adapter`) - Test UI
- **REST Client** (`humao.rest-client`) - Test API endpoints

#### Workspace Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/api_venv/bin/python",
  "python.terminal.activateEnvironment": true,

  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["tests", "-v"],

  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,

  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true,
      "source.fixAll": true
    }
  },

  "ruff.lint.args": ["--config=pyproject.toml"],
  "ruff.format.args": ["--config=pyproject.toml"],

  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true
  },

  "editor.rulers": [120],
  "editor.tabSize": 4,
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true
}
```

#### Launch Configuration

Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "LANGPLUG_DEBUG": "True"
      }
    },
    {
      "name": "Python: Current Test File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v", "-s"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### PyCharm

#### Setup Python Interpreter

1. **File → Settings → Project → Python Interpreter**
2. Click gear icon → **Add**
3. Select **Existing environment**
4. Browse to: `Backend/api_venv/bin/python`
5. Click **OK**

#### Configure Test Runner

1. **File → Settings → Tools → Python Integrated Tools**
2. Set **Default test runner** to **pytest**
3. Click **OK**

#### Enable Ruff

1. **File → Settings → Tools → External Tools**
2. Click **+** to add new tool
3. Name: **Ruff Format**
4. Program: `$ProjectFileDir$/api_venv/bin/ruff`
5. Arguments: `format $FilePath$`
6. Working directory: `$ProjectFileDir$`

---

## Database Setup

### SQLite (Development - Default)

SQLite is used by default for development. No additional setup required.

```bash
# Database file location
data/langplug.db

# View database (optional)
sqlite3 data/langplug.db
> .tables
> .quit
```

### PostgreSQL (Testing - Recommended)

For more realistic testing that matches production:

#### Using Docker (Easiest)

```bash
# Start PostgreSQL container
cd Backend
docker compose -f docker-compose.postgresql.yml up -d db

# Verify container is running
docker ps | grep postgres

# Run tests with PostgreSQL
USE_TEST_POSTGRES=1 \
TEST_POSTGRES_URL="postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug" \
python -m pytest

# Stop container when done
docker compose -f docker-compose.postgresql.yml down
```

#### Native PostgreSQL

```bash
# Install PostgreSQL (Linux)
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE langplug_dev;
CREATE USER langplug_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE langplug_dev TO langplug_user;
\q

# Update .env file
DATABASE_URL=postgresql+asyncpg://langplug_user:your_password@localhost:5432/langplug_dev
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View current migration version
alembic current

# View migration history
alembic history
```

---

## Running the Development Server

### Standard Development Server

```bash
# Activate virtual environment (if not already)
source api_venv/bin/activate

# Run with auto-reload (recommended for development)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Server will be available at:
# - API: http://localhost:8000
# - Interactive docs: http://localhost:8000/docs
# - Alternative docs: http://localhost:8000/redoc
```

### With Custom Configuration

```bash
# Run with different port
uvicorn main:app --reload --port 8080

# Run with debug logging
LANGPLUG_LOG_LEVEL=DEBUG uvicorn main:app --reload

# Run with specific number of workers (production-like)
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Using the Management CLI

```bash
# Using the project's management CLI (from project root)
cd ..  # Go to project root
python management/cli.py start-backend

# Or using the convenience script
cd Backend
python run_backend.py
```

### Verify Server is Running

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy"}

# Open interactive API docs
# Navigate to: http://localhost:8000/docs
```

---

## Running Tests

### Quick Start

```bash
# Activate virtual environment
source api_venv/bin/activate

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run in parallel (faster)
python -m pytest -n auto
```

### Test Categories

```bash
# Unit tests only (fast)
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ tests/api/ -v

# E2E tests only
python -m pytest tests/e2e_*.py -v

# Security tests
python -m pytest tests/security/ -v

# Performance tests
python -m pytest tests/performance/ -v
```

### Test Filtering

```bash
# Run tests matching pattern
python -m pytest -k "auth" -v

# Run specific test file
python -m pytest tests/unit/services/test_vocabulary_service.py -v

# Run specific test function
python -m pytest tests/unit/services/test_vocabulary_service.py::test_function_name -v

# Run tests with specific marker
python -m pytest -m "asyncio" -v
```

### Test Output Options

```bash
# Show print statements
python -m pytest -s

# Stop on first failure
python -m pytest -x

# Run last failed tests only
python -m pytest --lf

# Show local variables on failure
python -m pytest -l

# Quiet mode (minimal output)
python -m pytest -q
```

### Coverage Reports

```bash
# Run tests with coverage
python -m pytest --cov=api --cov=core --cov=services --cov-report=html --cov-report=term-missing

# Open HTML coverage report
# Browser: htmlcov/index.html

# Coverage for specific module
python -m pytest tests/unit/services/ --cov=services.vocabulary --cov-report=term-missing
```

### PowerShell Commands (WSL)

When running from WSL, use PowerShell wrapper:

```bash
# Run tests with PowerShell (ensures Windows compatibility)
powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest"

# This is especially important for:
# - npm commands
# - File system operations
# - Integration with Windows tools
```

For more testing information, see:

- **[TEST_REPORT.md](../TEST_REPORT.md)** - Test suite status and metrics
- **[TESTING_BEST_PRACTICES.md](../TESTING_BEST_PRACTICES.md)** - Testing guidelines

---

## Debugging

### VS Code Debugging

1. **Set breakpoints**: Click left of line number in editor
2. **Start debugging**: Press `F5` or Run → Start Debugging
3. **Use debug console**: Evaluate expressions while paused
4. **Step through code**:
   - `F10` - Step over
   - `F11` - Step into
   - `Shift+F11` - Step out
   - `F5` - Continue

### PyCharm Debugging

1. **Set breakpoints**: Click left gutter in editor
2. **Debug configuration**: Run → Debug 'main'
3. **Debug controls**: Same as VS Code (F10, F11, etc.)

### Print Debugging

```python
# Quick debug print (use temporarily, remove before commit)
print(f"DEBUG: variable_name = {variable_name}")

# Better: Use logging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Processing item: {item}")
logger.info(f"Operation completed: {result}")
logger.error(f"Error occurred: {error}", exc_info=True)
```

### Interactive Debugging (pdb)

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# When code reaches this line, you get interactive shell:
# (Pdb) print(variable_name)
# (Pdb) next  # Execute next line
# (Pdb) step  # Step into function
# (Pdb) continue  # Continue execution
# (Pdb) quit  # Stop debugging
```

### Debugging Tests

```bash
# Run test with pdb on failure
python -m pytest --pdb

# Run test with pdb on error (not assertion failures)
python -m pytest --pdbcls=IPython.terminal.debugger:Pdb

# Debug specific test
python -m pytest tests/unit/test_file.py::test_function --pdb -s
```

### Common Debugging Scenarios

#### **"Import Error" or "Module Not Found"**

```bash
# Verify virtual environment is activated
which python
# Should show: .../api_venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt

# Check if module is installed
pip list | grep module_name
```

#### **"Database Locked" Error**

```bash
# Close any other connections to database
# Delete database and recreate
rm data/langplug.db
alembic upgrade head
```

#### **"Port Already in Use"**

```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/macOS
taskkill /PID <PID> /F  # Windows
```

---

## Code Quality Tools

### Pre-commit Hooks

Automatically run code quality checks before each commit:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run hooks on staged files only
pre-commit run
```

**Hooks configured**:

- ✅ Ruff linting (code quality)
- ✅ Ruff formatting (code style)
- ✅ Bandit (security scanning)
- ✅ Trailing whitespace removal
- ✅ End-of-file fixing
- ✅ YAML/TOML/JSON validation
- ✅ Test naming validation
- ⚠️ MyPy (temporarily disabled)

### Manual Linting

```bash
# Run Ruff linter
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .

# Check formatting without changes
ruff format . --check
```

### Type Checking (Optional)

```bash
# Run MyPy type checker
mypy .

# Check specific file
mypy services/vocabulary/vocabulary_service.py

# Ignore errors temporarily
mypy . --ignore-missing-imports
```

### Security Scanning

```bash
# Run Bandit security scanner
bandit -r . -c pyproject.toml

# Scan specific directory
bandit -r services/ -c pyproject.toml
```

---

## Environment Variables

### Required Variables

Create `.env` file in `Backend/` directory:

```bash
# Application Settings
LANGPLUG_HOST=0.0.0.0
LANGPLUG_PORT=8000
LANGPLUG_DEBUG=True  # Set to False in production
LANGPLUG_ENVIRONMENT=development  # development, staging, production

# Paths
LANGPLUG_VIDEOS_PATH=../videos
LANGPLUG_DATA_PATH=./data
LANGPLUG_LOGS_PATH=./logs

# Security
LANGPLUG_SECRET_KEY=your-secret-key-min-32-characters-long-change-in-production
LANGPLUG_SESSION_TIMEOUT_HOURS=24

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/langplug.db
# For PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/langplug

# AI Services
LANGPLUG_TRANSCRIPTION_SERVICE=whisper
LANGPLUG_TRANSCRIPTION_MODEL=tiny  # tiny, base, small, medium, large
LANGPLUG_TRANSLATION_SERVICE=opus
LANGPLUG_TRANSLATION_MODEL=opus-de-es  # For German-Spanish

# Language Settings
LANGPLUG_DEFAULT_NATIVE_LANGUAGE=en
LANGPLUG_DEFAULT_TARGET_LANGUAGE=de

# Logging
LANGPLUG_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LANGPLUG_LOG_FORMAT=detailed  # simple, detailed, json

# CORS (Frontend integration)
LANGPLUG_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Optional Variables

```bash
# Rate Limiting (if enabled)
LANGPLUG_RATE_LIMIT_ENABLED=False
LANGPLUG_RATE_LIMIT_PER_MINUTE=60

# Redis (if using caching)
REDIS_URL=redis://localhost:6379/0

# Celery (if using background tasks)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# External APIs (if integrated)
OPENAI_API_KEY=your-api-key
DEEPL_API_KEY=your-api-key
```

### Environment Variable Reference

| Variable                       | Default        | Description                          |
| ------------------------------ | -------------- | ------------------------------------ |
| `LANGPLUG_HOST`                | `0.0.0.0`      | Server bind address                  |
| `LANGPLUG_PORT`                | `8000`         | Server port                          |
| `LANGPLUG_DEBUG`               | `False`        | Enable debug mode (detailed errors)  |
| `LANGPLUG_SECRET_KEY`          | _Required_     | Secret for JWT tokens (min 32 chars) |
| `LANGPLUG_TRANSCRIPTION_MODEL` | `tiny`         | Whisper model size                   |
| `DATABASE_URL`                 | SQLite default | Database connection URL              |

For complete reference, see **[CONFIGURATION.md](CONFIGURATION.md)** (to be created in Phase 2, Task 2.2).

---

## Troubleshooting

### Common Issues

#### 1. **Virtual Environment Not Activating**

**Symptoms**: `python` still points to system Python

**Solution**:

```bash
# Deactivate any active environment
deactivate

# Recreate virtual environment
rm -rf api_venv
python3.11 -m venv api_venv
source api_venv/bin/activate

# Verify
which python  # Should show api_venv path
```

#### 2. **Import Errors After Installing Dependencies**

**Symptoms**: `ModuleNotFoundError` despite running `pip install`

**Solution**:

```bash
# Verify pip is from virtual environment
which pip  # Should show api_venv path

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Clear pip cache if needed
pip cache purge
```

#### 3. **Database Migration Errors**

**Symptoms**: Alembic errors when running `upgrade head`

**Solution**:

```bash
# Reset database (DEVELOPMENT ONLY - destroys data)
rm data/langplug.db
alembic upgrade head

# If migration is corrupted, recreate migrations
# (Advanced - consult team first)
```

#### 4. **FFmpeg Not Found**

**Symptoms**: `FFmpeg not installed` error when processing videos

**Solution**:

```bash
# Linux/WSL
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version
```

#### 5. **Tests Fail in WSL**

**Symptoms**: Bus errors, SQLite async issues

**Solution**:

```bash
# Option 1: Use PostgreSQL for testing (recommended)
docker compose -f docker-compose.postgresql.yml up -d db
USE_TEST_POSTGRES=1 TEST_POSTGRES_URL="..." python -m pytest

# Option 2: Skip heavy tests
SKIP_DB_HEAVY_TESTS=1 python -m pytest

# Option 3: Run tests with PowerShell wrapper
powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest"
```

#### 6. **Port Already in Use**

**Symptoms**: `Address already in use` when starting server

**Solution**:

```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS

# Kill process
kill -9 <PID>

# Or use different port
uvicorn main:app --port 8001
```

#### 7. **AI Models Not Downloading**

**Symptoms**: Slow first run or errors about missing models

**Solution**:

```bash
# Manually download spaCy models
python -m spacy download de_core_news_sm
python -m spacy download en_core_web_sm

# Whisper models download automatically on first use
# But you can pre-download:
python -c "import whisper; whisper.load_model('tiny')"
```

### Getting Help

If you encounter issues not covered here:

1. **Check existing documentation**:
   - [README.md](../README.md) - Project overview
   - [TEST_REPORT.md](../TEST_REPORT.md) - Test suite information
   - [TESTING_BEST_PRACTICES.md](../TESTING_BEST_PRACTICES.md) - Testing guidelines

2. **Search project issues**: Check GitHub issues for similar problems

3. **Ask the team**: Reach out in team channels with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages (full stack trace)
   - Environment details (OS, Python version, etc.)

---

## Next Steps

Once your environment is set up:

1. **Explore the API**:
   - Visit http://localhost:8000/docs
   - Try out endpoints in the interactive documentation
   - Register a test user and explore authentication

2. **Read the architecture documentation**:
   - `docs/architecture/` - System design and patterns
   - [SECURITY_AND_TRANSACTIONS.md](SECURITY_AND_TRANSACTIONS.md) - Security features

3. **Write your first test**:
   - See [TESTING_BEST_PRACTICES.md](../TESTING_BEST_PRACTICES.md)
   - Follow test patterns from existing tests

4. **Make your first change**:
   - Create a feature branch
   - Make changes
   - Run tests and linting
   - Submit a pull request

---

## Development Workflow Checklist

Before starting work:

- [ ] Virtual environment activated
- [ ] Latest code pulled from main
- [ ] Dependencies up to date (`pip install -r requirements.txt`)
- [ ] Database migrations applied (`alembic upgrade head`)

Before committing:

- [ ] Tests pass (`python -m pytest`)
- [ ] Code is formatted (`ruff format .`)
- [ ] Linting passes (`ruff check .`)
- [ ] Pre-commit hooks pass (`pre-commit run`)
- [ ] Changes are tested

Before pushing:

- [ ] Commit message follows conventions (see CLAUDE.md)
- [ ] No sensitive data in commits
- [ ] Branch is up to date with main

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: Development Team
