# LangPlug Backend - Architecture Overview

**Version**: 1.0
**Last Updated**: 2025-10-03

High-level overview of the LangPlug Backend architecture, patterns, and design decisions.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Component Structure](#component-structure)
4. [Data Flow](#data-flow)
5. [Key Design Decisions](#key-design-decisions)
6. [Technology Stack](#technology-stack)
7. [Further Reading](#further-reading)

---

## System Overview

### Purpose

LangPlug Backend is a **language learning platform** that combines:
- 🎥 **Video content management** with subtitle processing
- 📝 **Vocabulary tracking** with CEFR level classification
- 🎮 **Interactive learning games** based on user's vocabulary
- 🔊 **AI-powered transcription** using Whisper
- 🌐 **Translation services** using OPUS-MT/NLLB models
- 📊 **Progress tracking** and learning analytics

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        LangPlug System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │   Frontend   │◄────────┤   Backend    │                    │
│  │   (React)    │  HTTP   │   (FastAPI)  │                    │
│  └──────────────┘  WS     └──────┬───────┘                    │
│                                   │                             │
│                          ┌────────┴────────┐                   │
│                          │                 │                   │
│                    ┌─────▼─────┐    ┌─────▼─────┐            │
│                    │ Database  │    │   Files   │            │
│                    │ SQLite/   │    │  Videos   │            │
│                    │ Postgres  │    │  SRT      │            │
│                    └───────────┘    └───────────┘            │
│                                                                 │
│                    ┌──────────────────────────┐               │
│                    │   AI Models (Local)      │               │
│                    │   - Whisper (Speech→Text)│               │
│                    │   - OPUS-MT (Translation)│               │
│                    │   - spaCy (NLP/Lemma)    │               │
│                    └──────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Patterns

### 1. Layered Architecture

The system follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────┐
│      Presentation Layer             │  FastAPI Routes
│      (API Routes)                   │  Request/Response handling
├─────────────────────────────────────┤
│      Business Logic Layer           │  Services
│      (Services)                     │  Domain logic
├─────────────────────────────────────┤
│      Data Access Layer              │  Repositories
│      (Repositories)                 │  Database operations
├─────────────────────────────────────┤
│      Infrastructure Layer           │  External services
│      (AI Models, File System)       │  Third-party integrations
└─────────────────────────────────────┘
```

**Benefits**:
- Clear separation of concerns
- Easy to test (mock lower layers)
- Independent layer evolution
- Enforced dependencies (top → bottom)

**See**: `../../docs/architecture/decisions/ADR-001-layered-architecture.md`

### 2. Repository Pattern

**Data access is abstracted** through repository interfaces:

```python
# Repository interface (abstraction)
class VocabularyRepository(Protocol):
    async def get_word(self, user_id: str, word: str) -> Word: ...
    async def save_word(self, word: Word) -> Word: ...

# Concrete implementation
class SQLAlchemyVocabularyRepository:
    async def get_word(self, user_id: str, word: str) -> Word:
        # SQLAlchemy-specific implementation
        ...
```

**Benefits**:
- Database independence (swap SQLite ↔ PostgreSQL)
- Easier testing (mock repositories)
- Centralized data access logic
- Query optimization in one place

**See**: `../../docs/architecture/decisions/ADR-007-repository-pattern-data-access.md`

### 3. Strategy Pattern (AI Services)

**Transcription and translation use Strategy Pattern** to switch between models:

```python
# Strategy interface
class TranscriptionStrategy(Protocol):
    def transcribe(self, audio_path: str) -> str: ...

# Concrete strategies
class WhisperStrategy(TranscriptionStrategy):
    def transcribe(self, audio_path: str) -> str:
        # Whisper-specific implementation
        ...

class ParakeetStrategy(TranscriptionStrategy):
    def transcribe(self, audio_path: str) -> str:
        # Parakeet-specific implementation
        ...

# Factory selects strategy
factory.get_transcription_service("whisper")  # Returns WhisperStrategy
```

**Benefits**:
- Easy to add new AI models
- Runtime model selection
- Isolated model-specific logic
- Testable (mock strategies)

**See**: `../../docs/architecture/decisions/ADR-006-strategy-pattern-ai-models.md`

### 4. Facade Pattern (Service Layer)

**Complex subsystems hidden behind simple facades**:

```python
# Facade (simple interface)
class VocabularyService:
    def __init__(self):
        self.query_service = VocabularyQueryService()
        self.progress_service = VocabularyProgressService()
        self.stats_service = VocabularyStatsService()

    def mark_word_as_known(self, user_id: str, word: str):
        # Delegates to specialized services
        self.progress_service.update_word_status(...)
        self.stats_service.recalculate_stats(...)

# Client code (simple)
vocabulary_service.mark_word_as_known(user_id, word)
```

**Benefits**:
- Simple client interface
- Complex logic hidden
- Easier to refactor internals
- Clear service boundaries

**Location**: `services/vocabulary/vocabulary_service_new.py`

---

## Component Structure

### API Layer (`api/`)

**FastAPI routes** organized by resource:

```
api/
├── routes/
│   ├── auth.py              # Authentication (login, register, token refresh)
│   ├── vocabulary.py        # Vocabulary management
│   ├── videos.py            # Video upload, streaming, subtitles
│   ├── game.py              # Learning game sessions
│   ├── processing.py        # Video processing orchestration
│   ├── user_profile.py      # User preferences and settings
│   └── ...
├── models/                  # Pydantic request/response models
└── dtos/                    # Data Transfer Objects
```

**Responsibilities**:
- HTTP request/response handling
- Input validation (Pydantic)
- Authentication enforcement
- Error serialization

### Service Layer (`services/`)

**Business logic** organized by domain:

```
services/
├── authservice/             # User authentication and authorization
│   ├── auth_service.py      # Login, registration, sessions
│   ├── token_service.py     # JWT token creation and validation
│   └── password_validator.py # Password strength validation
├── vocabulary/              # Vocabulary management
│   ├── vocabulary_service_new.py       # Facade
│   ├── vocabulary_query_service.py     # Queries
│   ├── vocabulary_progress_service.py  # Progress tracking
│   └── vocabulary_stats_service.py     # Analytics
├── processing/              # Video/subtitle processing
│   ├── chunk_processor.py              # Processing pipeline orchestration
│   ├── chunk_transcription_service.py  # Audio → Text (Whisper)
│   ├── chunk_translation_service.py    # Text translation
│   └── chunk_handler.py                # Chunk management
├── transcriptionservice/    # Transcription strategies
│   ├── whisper_implementation.py
│   └── parakeet_implementation.py
├── translationservice/      # Translation strategies
│   ├── opus_implementation.py
│   └── nllb_implementation.py
└── ...
```

**Responsibilities**:
- Business rule enforcement
- Workflow orchestration
- External service integration
- Data transformation

### Data Layer (`database/`)

**Database models and repositories**:

```
database/
├── models.py                # SQLAlchemy ORM models
└── repositories/            # Data access abstractions
    ├── vocabulary_repository.py
    ├── user_repository.py
    ├── processing_repository.py
    └── ...
```

**Responsibilities**:
- Database schema definition
- CRUD operations
- Transaction management
- Query optimization

### Core Layer (`core/`)

**Cross-cutting concerns**:

```
core/
├── config.py                # Configuration management
├── dependencies.py          # FastAPI dependency injection
├── auth.py                  # Authentication helpers
├── middleware.py            # HTTP middleware
├── exceptions.py            # Custom exceptions
├── transaction.py           # Transaction decorators
├── file_security.py         # File upload security
└── rate_limit.py            # Rate limiting (optional)
```

**Responsibilities**:
- Application configuration
- Security enforcement
- Logging and monitoring
- Shared utilities

---

## Data Flow

### Example: Video Processing Workflow

```
1. Client Upload
   │
   ├──► POST /api/videos/upload/series-name
   │     └─► Route: videos.py
   │          └─► Validates file (file_security.py)
   │               └─► Saves to disk (video_service.py)
   │
2. Client Initiates Processing
   │
   ├──► POST /api/processing/chunk
   │     └─► Route: processing.py
   │          └─► ChunkProcessor.process_chunk()
   │               │
   │               ├─► 1. Extract audio (FFmpeg)
   │               ├─► 2. Transcribe (Whisper)
   │               ├─► 3. Translate (OPUS-MT)
   │               ├─► 4. Filter vocabulary (spaCy)
   │               └─► 5. Generate subtitles (SRT)
   │
3. Client Polls Progress
   │
   ├──► GET /api/processing/status/{task_id}
   │     └─► Returns processing status and percentage
   │
4. Client Downloads Result
   │
   └──► GET /api/videos/subtitles/{subtitle_path}
        └─► Returns SRT subtitle file
```

### Authentication Flow

```
1. User Registration
   POST /api/auth/register
   └─► AuthService.register_user()
       └─► PasswordValidator.validate()
       └─► PasswordValidator.hash_password()
       └─► UserRepository.create()

2. User Login
   POST /api/auth/login
   └─► AuthService.login()
       └─► PasswordValidator.verify_password()
       └─► TokenService.create_token_pair()
           ├─► Access Token (JWT, 30 min)
           └─► Refresh Token (JWT, 7 days, httpOnly cookie)

3. Protected Endpoint Access
   GET /api/profile
   └─► Depends(current_active_user)
       └─► TokenService.verify_access_token()
           └─► Decodes JWT
           └─► Validates expiration
           └─► Returns User object

4. Token Refresh
   POST /api/auth/token/refresh
   └─► Cookie: refresh_token
       └─► TokenService.refresh_access_token()
           └─► Validates refresh token
           └─► Issues new access token
```

---

## Key Design Decisions

### ADR-001: Layered Architecture
**Decision**: Use layered architecture (API → Services → Repositories → Infrastructure)
**Rationale**: Clear separation of concerns, testability, maintainability
**Trade-off**: More indirection, but better structure

### ADR-002: FastAPI + React Stack
**Decision**: FastAPI for backend, React for frontend
**Rationale**: Modern async Python, great docs, TypeScript support
**Trade-off**: Learning curve, but high developer productivity

### ADR-003: SQLite → PostgreSQL
**Decision**: SQLite for development, PostgreSQL for production
**Rationale**: Simple dev setup, production scalability
**Trade-off**: Minor differences, but async drivers abstract most

### ADR-004: JWT Authentication
**Decision**: JWT tokens (access + refresh) instead of sessions
**Rationale**: Stateless, scalable, supports SPA architecture
**Trade-off**: Token invalidation harder, but refresh mechanism mitigates

### ADR-005: WebSockets for Real-time
**Decision**: WebSocket connections for processing updates
**Rationale**: True real-time, better than polling
**Trade-off**: Connection management complexity

### ADR-006: Strategy Pattern for AI Models
**Decision**: Abstract AI services behind strategy interfaces
**Rationale**: Easy to swap models, test, benchmark
**Trade-off**: Extra abstraction layer

### ADR-007: Repository Pattern
**Decision**: Data access through repository interfaces
**Rationale**: Database independence, testability
**Trade-off**: Boilerplate, but worth it for flexibility

### ADR-008: OpenAPI-First Design
**Decision**: Design API with OpenAPI/Swagger
**Rationale**: Auto-generated docs, client generation
**Trade-off**: Pydantic models required, but excellent validation

**Full ADRs**: `../../docs/architecture/decisions/`

---

## Technology Stack

### Backend Core

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Primary language |
| **FastAPI** | 0.100+ | Web framework |
| **Uvicorn** | Latest | ASGI server |
| **Pydantic** | 2.0+ | Data validation |
| **SQLAlchemy** | 2.0+ | ORM |
| **Alembic** | Latest | Database migrations |

### AI/ML

| Technology | Purpose |
|------------|---------|
| **Whisper** | Speech-to-text transcription |
| **OPUS-MT** | Machine translation (Helsinki-NLP) |
| **NLLB** | Alternative translation (Meta) |
| **spaCy** | NLP, lemmatization, tokenization |
| **Transformers** | Hugging Face model loading |

### Database

| Database | Use Case |
|----------|----------|
| **SQLite** | Development, testing |
| **PostgreSQL** | Production (recommended) |
| **aiosqlite** | Async SQLite driver |
| **asyncpg** | Async PostgreSQL driver |

### Testing

| Tool | Purpose |
|------|---------|
| **pytest** | Test framework |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage measurement |
| **httpx** | Async HTTP client for tests |
| **faker** | Test data generation |

### Code Quality

| Tool | Purpose |
|------|---------|
| **Ruff** | Fast linter and formatter |
| **Bandit** | Security scanner |
| **pre-commit** | Git hooks |
| **MyPy** | Type checking (optional) |

---

## Further Reading

### Documentation

- **[DEVELOPER_SETUP.md](DEVELOPER_SETUP.md)** - Development environment setup
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration reference
- **[API_INTEGRATION_GUIDE.md](API_INTEGRATION_GUIDE.md)** - API integration examples
- **[TEST_REPORT.md](../TEST_REPORT.md)** - Test suite status
- **[TESTING_BEST_PRACTICES.md](../TESTING_BEST_PRACTICES.md)** - Testing guidelines

### Architecture Documentation

- **[Architecture Index](../../docs/architecture/INDEX.md)** - Complete architecture docs
- **[ADRs](../../docs/architecture/decisions/)** - Architecture decision records
- **[Diagrams](../../docs/architecture/diagrams/)** - System diagrams (PlantUML)
- **[Migration Guides](../../docs/architecture/MIGRATION_GUIDES.md)** - Migration strategies
- **[Implementation Roadmap](../../docs/architecture/IMPLEMENTATION_ROADMAP.md)** - Future plans

### Security & Operations

- **[SECURITY_AND_TRANSACTIONS.md](../SECURITY_AND_TRANSACTIONS.md)** - Security features
- **[MIGRATIONS.md](MIGRATIONS.md)** - Database migration guide (to be created)
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment procedures (to be created)

---

## Architecture Evolution

### Current State (v0.1.0)

✅ **Implemented**:
- Layered architecture with clear boundaries
- JWT authentication with refresh tokens
- Video upload and processing pipeline
- Vocabulary tracking and progress
- Learning game sessions
- WebSocket real-time updates
- Comprehensive test suite (1,619 tests)

### Future Enhancements

🔮 **Planned**:
- **Celery**: Background task processing (long-running jobs)
- **Redis**: Caching and session storage
- **Elasticsearch**: Full-text search for vocabulary
- **S3**: Cloud storage for videos (scalability)
- **Docker**: Containerization for deployment
- **Kubernetes**: Orchestration for scaling
- **Monitoring**: Prometheus + Grafana metrics
- **Tracing**: OpenTelemetry distributed tracing

**See**: `../../docs/architecture/IMPLEMENTATION_ROADMAP.md`

---

## Common Architectural Questions

### Q: Why FastAPI instead of Django?

**A**: FastAPI offers:
- Modern async/await support (better performance)
- Automatic OpenAPI documentation
- Built-in Pydantic validation
- Easier to understand for small teams
- Better suited for API-first applications

Django is excellent for full-stack monoliths with admin panels, but LangPlug has a separate React frontend.

### Q: Why not microservices?

**A**: Current scale doesn't justify microservices complexity:
- Single team, single codebase easier to manage
- No independent scaling needs yet
- Shared database simplifies transactions
- Monolith can scale vertically for current load

**When to consider microservices**: 10x current load, multiple teams, independent service releases needed.

### Q: Why local AI models instead of APIs?

**A**:
- **Cost**: No per-request API fees
- **Privacy**: User data stays on-premises
- **Latency**: No network round-trip
- **Offline**: Works without internet
- **Control**: Model versioning and tuning

**Trade-off**: Requires GPU resources and model storage.

### Q: Why both SQLite and PostgreSQL support?

**A**:
- **Development**: SQLite = zero setup, fast tests
- **Production**: PostgreSQL = scalability, concurrent writes
- **Testing**: Both to ensure compatibility
- **Migration**: Alembic abstracts differences

Repository pattern makes database swapping transparent.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Maintained By**: Development Team
