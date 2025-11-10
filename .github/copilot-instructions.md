# GitHub Copilot Instructions for LangPlug

## Project Overview

LangPlug is a Netflix-style German language learning platform that combines video streaming with interactive vocabulary learning. The project uses FastAPI backend with React/TypeScript frontend.

## Core Architecture

### Backend (`src/backend/`)
- **Framework**: FastAPI with async/await patterns
- **Database**: SQLite with SQLAlchemy ORM and async sessions
- **AI Services**: Whisper transcription, vocabulary filtering, translation
- **Authentication**: Session-based with bcrypt password hashing
- **Structure**:
  - `src/backend/core/` - Core modules (database, models)
  - `src/backend/services/` - Business logic services
  - `src/backend/api/` - API routes and endpoints

### Frontend (`src/frontend/`)
- **Framework**: React 18 with TypeScript
- **Styling**: Styled Components
- **State Management**: Zustand
- **Build Tool**: Vite
- **Video Player**: ReactPlayer with custom controls

## Critical Development Rules

### Code Standards

1. **NO emojis or non-ASCII characters in Python code** - Use ASCII tags like [INFO], [ERROR], [WARN] instead
2. **NO version suffixes** - Never use `_v2`, `_new`, `_old`, `_temp`, `_backup` in filenames or class names
3. **NO backward compatibility layers** - Update all dependencies to use new architecture directly
4. **NEVER comment out code** - Delete obsolete code completely; Git is the safety net
5. **Minimal changes** - Keep changes focused; don't refactor unrelated code
6. **No one-letter variables** - Use descriptive variable names

### Environment & Tooling

- **Python Environment**: Always use the virtual environment at `src/backend/api_venv/`
- **Windows PowerShell**: Prefer PowerShell for running servers and Python tools on host OS
- **WSL**: Use only for light file operations; avoid mixing environments for runtime tasks
- **Activation Pattern**: 
  ```bash
  cd /mnt/c/Users/Jonandrop/IdeaProjects/LangPlug/src/backend && \
  powershell.exe -Command ". api_venv/Scripts/activate; python -m pytest ..."
  ```

## Testing Guidelines

### Test Philosophy (80/20 Protective Testing)

- **Behavior-focused**: Don't assert internal implementation details
- **Descriptive names**: Use names like `test_register_returns_token`
- **Minimal setup**: Use shared fixtures from `Backend/tests/conftest.py`
- **Default coverage per feature**:
  1. Happy path scenario (contract works end-to-end)
  2. Invalid/missing input scenario (fails gracefully)
  3. Single high-risk boundary (size limit, state transition)

### Testing Conventions

- Use in-process FastAPI clients with dependency overrides (see `src/backend/tests/conftest.py`)
- Mock external services (Redis, transcription) and filesystem paths
- No network or disk I/O in tests
- Align assertions with behavior, not exact error message text
- Each test must complete within 60 seconds (enforced by pytest-timeout)

### Backend Testing

```bash
# Run all backend tests
cd src/backend && pytest

# Run with coverage
cd src/backend && pytest --cov=core --cov=api --cov=services

# Lint backend
cd src/backend && ruff check .
```

### Database Testing

- Use `async_client` and `db_session` fixtures from `src/backend/tests/conftest.py`
- Tests use single file-backed SQLite database per run
- Clean schema per test via create/drop cycles
- Database access via `core.database.AsyncSessionLocal` and `get_async_session` dependency

## Contract-Driven Development (CDD)

### Contract Lifecycle

1. **Define contracts first** - Update OpenAPI spec or schema modules before implementation
2. **Generate clients** - Stub consumer/provider clients from contracts
3. **Write tests first** - Author tests capturing agreed behavior (80/20 guidance)
4. **Implement and validate** - Keep code aligned with contract and tests

### Contract Requirements

- Contracts live in `src/backend/api/openapi_spec.py` and frontend schema modules
- All contract updates require peer review
- Apply semantic versioning (PATCH/MINOR/MAJOR)
- Run contract tests on every change (`pytest -k contract`)
- Document new behavior and migration steps

## API Development

### FastAPI Patterns

- Use async route handlers with `async def`
- Dependency injection for database sessions via `get_async_session`
- Background tasks via FastAPI `BackgroundTasks` with explicit signatures
- Proper error handling with appropriate HTTP status codes
- OpenAPI documentation auto-generated from route definitions

### Database Operations

- Use async SQLAlchemy sessions
- Repository pattern for data access
- Proper transaction handling with `async with session.begin()`
- No raw SQL unless absolutely necessary

## Frontend Development

### React/TypeScript Patterns

- Functional components with hooks
- TypeScript for type safety
- Styled Components for CSS-in-JS
- Zustand for state management
- Proper error boundaries and loading states

### Component Structure

- Keep components small and focused
- Extract reusable logic to custom hooks
- Use TypeScript interfaces for props
- Follow existing naming conventions

## Protected Files

**DO NOT DELETE** the following essential documentation files:
- `AGENTS.md`
- `QWEN.MD.md`
- `GEMINI.md`
- `CLAUDE.md`

## Documentation Requirements

- Update relevant documentation alongside code changes
- API changes require OpenAPI spec updates
- Feature changes require README updates
- Breaking changes need migration guides

## Pull Request Checklist

Before submitting PRs:
- [ ] Tests pass (`cd src/backend && pytest`)
- [ ] Linting passes (`cd src/backend && ruff check .`)
- [ ] Coverage maintained (`pytest --cov`)
- [ ] Generated artifacts up to date (OpenAPI client, schemas)
- [ ] Documentation updated
- [ ] Contract tests pass if contracts changed
- [ ] Frontend tests pass if frontend changed (`cd src/frontend && npm run test`)

## Server Management

- **Start servers**: Use `scripts\start-all.bat` or `scripts\stop-all.bat`
- **Verify status**: Check log files in `src/backend/logs/backend.log` and `src/frontend/frontend.log`
- **Restart after**: Installing packages, changing env vars, modifying config

## Common Patterns

### Adding a New API Endpoint

1. Define route in appropriate file under `src/backend/api/`
2. Add request/response models in `src/backend/core/models.py`
3. Implement service logic in `src/backend/services/`
4. Write tests in `src/backend/tests/api/`
5. Update OpenAPI spec if needed
6. Document in API docs

### Adding a New Service

1. Create service file in `src/backend/services/`
2. Define service interface and implementation
3. Add dependency injection if needed
4. Write unit tests in `src/backend/tests/services/`
5. Update service documentation

### Adding Frontend Component

1. Create component in appropriate directory under `src/frontend/src/`
2. Define TypeScript interfaces for props
3. Use styled-components for styling
4. Add to Storybook if applicable
5. Write component tests

## Tech Stack Reference

### Backend
- FastAPI (web framework)
- SQLite/SQLAlchemy (database)
- Whisper (speech transcription)
- SpaCy (NLP for German)
- Transformers (Hugging Face models)
- MoviePy (video/audio processing)

### Frontend
- React 18
- TypeScript
- Vite (build tool)
- Styled Components
- Zustand (state management)
- React Router (routing)
- Framer Motion (animations)

## Performance Considerations

- Use CUDA GPU for faster transcription when available
- Lazy load components and routes
- Optimize video delivery
- Cache frequently accessed data
- Use async operations for I/O

## Security Guidelines

- Never commit secrets or credentials
- Use environment variables for sensitive config
- Validate all user inputs
- Sanitize data before database operations
- Use prepared statements/ORM to prevent SQL injection
- Implement proper authentication checks on protected routes

## Additional Resources

- Full project documentation: `README.md`
- Contributing guidelines: `CONTRIBUTING.md`
- AI agent guidelines: `AGENTS.md`
- Architecture details: See `src/backend/README.md` and `src/frontend/README.md`
