# LangPlug Backend

The backend for LangPlug, a German language learning platform that combines video content with intelligent subtitle filtering and vocabulary tracking.

## Project Structure

```
Backend/
├── api/                 # API route definitions
│   └── routes/          # Individual route modules
├── core/                # Core application components
├── data/                # Data files and databases
├── database/            # Database management and migrations
├── docs/                # Project documentation
│   └── archive/         # Historical documentation
├── logs/                # Application logs
├── scripts/             # Utility scripts
│   ├── analysis/        # Code analysis scripts
│   ├── database/        # Database scripts
│   ├── debug/           # Debugging utilities
│   ├── setup/           # Setup scripts
│   ├── testing/         # Test utilities
│   └── utils/           # General utilities
├── services/            # Business logic and service layers
│   ├── authservice/     # Authentication service
│   ├── filterservice/   # Subtitle filtering services
│   ├── logging/         # Logging services
│   ├── processing/      # Video/subtitle processing
│   ├── transcriptionservice/ # Audio transcription services
│   ├── translationservice/   # Language translation services
│   └── vocabulary/      # Vocabulary management services
├── tests/               # Unit, integration, and API tests
│   ├── api/             # API contract tests
│   ├── integration/     # Integration tests
│   ├── security/        # Security tests
│   └── unit/            # Unit tests
├── videos/              # Video storage (symlink)
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
├── CHANGELOG.md        # Version history
└── README.md          # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- FFmpeg
- Git

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd LangPlug/Backend
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables (see Configuration section)

5. Run the development server:

```bash
uvicorn main:app --reload
```

### Configuration

Create a `.env` file in the Backend directory with the following variables:

```
LANGPLUG_HOST=0.0.0.0
LANGPLUG_PORT=8000
LANGPLUG_DEBUG=True
LANGPLUG_VIDEOS_PATH=../videos
LANGPLUG_DATA_PATH=./data
LANGPLUG_LOGS_PATH=./logs
LANGPLUG_TRANSCRIPTION_SERVICE=whisper
LANGPLUG_TRANSLATION_SERVICE=nllb
LANGPLUG_DEFAULT_LANGUAGE=de
LANGPLUG_SESSION_TIMEOUT_HOURS=24
LANGPLUG_LOG_LEVEL=INFO
```

## API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation.

### OpenAPI Specification

The backend automatically generates an OpenAPI specification that serves as the single source of truth for API contracts.

**Location**: `Backend/openapi.json` (auto-generated, excluded from git)

**Regenerate the spec**:

```bash
cd Backend
python export_openapi.py
```

**Frontend Integration**:

The Frontend uses the OpenAPI spec to:

- Generate TypeScript client types
- Generate Zod validation schemas
- Keep frontend/backend validation in sync

**Update frontend after API changes**:

```bash
cd Frontend
npm run update-openapi
```

This command:

1. Exports the latest OpenAPI spec from the backend
2. Generates TypeScript types from the spec
3. Generates Zod schemas for runtime validation

**Manual steps** (if needed):

```bash
# Export OpenAPI spec only
cd Backend && python export_openapi.py

# Generate TypeScript client only
cd Frontend && npm run generate:client

# Generate Zod schemas only
cd Frontend && npm run generate:schemas
```

## Testing

### Running Tests

```bash
# Run all tests
cd Backend && python -m pytest

# Run tests with verbose output
cd Backend && python -m pytest -v

# Run only API tests
cd Backend && python -m pytest tests/api/

# Run specific test file
cd Backend && python -m pytest tests/api/test_processing_contract_improved.py

# Run tests in parallel (faster)
cd Backend && python -m pytest -n auto

# Run tests with coverage
cd Backend && python -m pytest --cov=api --cov=core --cov=services
```

### Test Architecture

Our test suite follows modern async testing patterns with:

- **Async Test Client**: HTTPX AsyncClient for realistic API testing
- **Real Authentication Flows**: Registration and login instead of fake tokens
- **URL Builder Utility**: Named routes instead of hardcoded paths
- **Database Isolation**: Transaction rollback for perfect test isolation
- **Asyncio Backend**: Focused on asyncio compatibility for reliable results

### Key Test Files

- `tests/api/test_processing_contract_improved.py` - Async processing API contract tests
- `tests/api/test_video_contract_improved.py` - Async video API contract tests
- `tests/api/test_auth_contract_improved.py` - Async authentication contract tests
- `tests/auth_helpers.py` - Authentication test helpers with `AuthTestHelperAsync` class

### Test Documentation

- [docs/TESTING_BEST_PRACTICES.md](docs/TESTING_BEST_PRACTICES.md) - Guidelines for writing new tests
- [docs/TESTING_INDEX.md](docs/TESTING_INDEX.md) - Index of all testing documentation
- [TEST_AUDIT_RESULTS.md](TEST_AUDIT_RESULTS.md) - Test architecture audit results (2025-10-05)

### Code Quality

```bash
# Run linter
ruff check .

# Format code
ruff format .
```

## Services

### Transcription Service

- Uses OpenAI Whisper for speech-to-text conversion
- Supports multiple model sizes (tiny, base, small, medium, large)

### Translation Service

- Uses Facebook's NLLB (No Language Left Behind) for translation
- Supports German to English translation

### Filtering Service

- Filters subtitles based on user's vocabulary knowledge
- Identifies "blocking words" that may impede comprehension

## Logging

Logs are written to the `logs/` directory with both file and console output. Log levels can be configured via the `LANGPLUG_LOG_LEVEL` environment variable.

## Documentation

### Essential Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - Detailed configuration guide
- [docs/DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md) - Complete developer setup guide
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment instructions

### Architecture & Design

- [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) - System architecture overview
- [docs/CODE_STYLE.md](docs/CODE_STYLE.md) - Code style guidelines and standards
- [docs/REPOSITORY_PATTERN.md](docs/REPOSITORY_PATTERN.md) - Repository pattern implementation
- [docs/DTO_STANDARDS.md](docs/DTO_STANDARDS.md) - Data Transfer Object standards

### API & Integration

- [docs/API_CONTRACT_TESTING_GUIDE.md](docs/API_CONTRACT_TESTING_GUIDE.md) - API contract testing guide
- [docs/API_INTEGRATION_GUIDE.md](docs/API_INTEGRATION_GUIDE.md) - API integration guide
- [docs/INTEGRATION_TEST_STRATEGY.md](docs/INTEGRATION_TEST_STRATEGY.md) - Integration testing strategy

### Testing

- [docs/TESTING_BEST_PRACTICES.md](docs/TESTING_BEST_PRACTICES.md) - Testing standards and best practices
- [docs/TESTING_INDEX.md](docs/TESTING_INDEX.md) - Index of all testing documentation
- [docs/TESTING_QUICK_REFERENCE.md](docs/TESTING_QUICK_REFERENCE.md) - Quick testing reference
- [TEST_AUDIT_RESULTS.md](TEST_AUDIT_RESULTS.md) - Test architecture audit (2025-10-05)

### Database & Operations

- [docs/POSTGRESQL_SETUP_GUIDE.md](docs/POSTGRESQL_SETUP_GUIDE.md) - PostgreSQL setup guide
- [docs/MIGRATIONS.md](docs/MIGRATIONS.md) - Database migration guide
- [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) - Application migration guide
- [docs/MONITORING.md](docs/MONITORING.md) - Monitoring and observability
- [docs/SECURITY_AND_TRANSACTIONS.md](docs/SECURITY_AND_TRANSACTIONS.md) - Security and transaction patterns

### Code Quality Tools

- [docs/CODE_QUALITY_TOOLS.md](docs/CODE_QUALITY_TOOLS.md) - Quality tools and linting
- [docs/CODE_METRICS_GUIDE.md](docs/CODE_METRICS_GUIDE.md) - Code metrics and analysis

### Historical Documentation

Outdated refactoring summaries, test reports, and analyses have been archived to [docs/archive/](docs/archive/) for reference.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

[License information to be added]
Notes:

- Tests enforce a global timeout of 60 seconds per test via `pytest-timeout` (see `Backend/pytest.ini`).
- In constrained sandboxes (e.g., WSL seccomp or CI with restricted syscalls), you can skip DB-heavy
  performance/security specs by setting `SKIP_DB_HEAVY_TESTS=1` for the test run:
  ```bash
  cd Backend && SKIP_DB_HEAVY_TESTS=1 pytest tests/performance tests/security
  ```
  This does not affect local development; it only gates heavy specs when the environment cannot
  initialize the async SQLite engine reliably.

### Postgres-backed Test Runs (Recommended for stability)

To avoid edge cases with `aiosqlite` under async lifecycles, you can run tests against Postgres.

1. Start Postgres (Docker):

```bash
cd Backend
docker compose -f docker-compose.postgresql.yml up -d db
```

2. Run tests pointing to the Postgres DB:

```bash
cd Backend
USE_TEST_POSTGRES=1 TEST_POSTGRES_URL="postgresql+asyncpg://langplug_user:langplug_password@localhost:5432/langplug" pytest
```

The test harness will drop/create schemas per test, so use a dedicated test database or ensure the
container is not used for production data.
