# DEPRECATED: LangPlug Development Guide for Agentic Coding Agents

**⚠️ DEPRECATION NOTICE**: This file has been consolidated into the unified AI Development Guide.

**👉 Use instead**: `AI_DEVELOPMENT_GUIDE.md` - Comprehensive guide for all AI coding assistants

---

# Original: LangPlug Development Guide for Agentic Coding Agents

## Build/Lint/Test Commands

```bash
# Run backend server (Windows/PowerShell from WSL)
powershell.exe -Command "python E:\Users\Jonandrop\IdeaProjects\LangPlug\Backend\run_backend.py"

# Run backend server (Linux/WSL)
cd Backend && python run_backend.py

# Run all tests
cd Backend && pytest

# Run a single test file
cd Backend && pytest tests/api/test_auth_endpoints.py

# Run tests with coverage
cd Backend && pytest --cov=core --cov=api --cov=services

# Linting and formatting
cd Backend && ruff check .
cd Backend && ruff format .

# Frontend development
cd Frontend && npm run dev
```

## Code Style Guidelines

### Python Formatting

- Line length: 88 characters
- Double quotes for strings
- Google-style docstrings
- Import sorting with isort (first-party: api, core, database, services, tests)

### Naming Conventions

- snake_case for variables/functions
- PascalCase for classes
- UPPER_CASE for constants

### Type Hints

- Use explicit type hints for all functions
- Prefer Pydantic models for data structures
- Use UUID for user IDs (not integers)

### Error Handling

- Use structured exception handling
- Log errors appropriately with context
- Return consistent error response formats

### Testing Best Practices

- Use transaction rollback for test isolation
- Follow FastAPI-Users actual API behavior (form data for login, not JSON)
- Authentication responses: {"access_token": "...", "token_type": "bearer"}
- Use standardized auth helpers from tests/auth_helpers.py
- Generate unique test data with AuthTestHelper.generate_unique_user_data()

### Database

- Use SQLAlchemy async sessions
- Implement UserManager.parse_id() for UUID handling
- Apply migrations with Alembic

### WSL/Windows Interoperability

- When running Python scripts from WSL that need to match Windows execution, use:
  `powershell.exe -Command "python E:\Users\Jonandrop\IdeaProjects\LangPlug\Backend\script_name.py"`
- This ensures consistent virtual environment and path handling between WSL and Windows
