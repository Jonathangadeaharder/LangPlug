# DEPRECATED: LangPlug CRUSH Development Guide

**⚠️ DEPRECATION NOTICE**: This file has been consolidated into the unified AI Development Guide.

**👉 Use instead**: `AI_DEVELOPMENT_GUIDE.md` - Comprehensive guide for all AI coding assistants

---

# Original: LangPlug CRUSH Development Guide

## Build Commands

### Backend (Python/FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (Linux/WSL)
cd Backend && python run_backend.py

# Run development server (Windows/PowerShell from WSL)
powershell.exe -Command "python E:\Users\Jonandrop\IdeaProjects\LangPlug\Backend\run_backend.py"

# Always use this for proper initialization:
cmd.exe /c start.bat
```

### Frontend (TypeScript/React)

```bash
# Install dependencies
npm install

# Run development server
cd Frontend && npm run dev

# On Windows, use cmd.exe prefix:
cmd.exe /c "npm run dev"
```

## Linting Commands

### Backend

```bash
# Run linter (Ruff)
cd Backend && ruff check .

# Auto-fix linting issues
cd Backend && ruff check . --fix

# Format code
cd Backend && ruff format .
```

### Frontend

```bash
# Run ESLint
cd Frontend && npm run lint

# Fix linting issues automatically
cd Frontend && npm run lint -- --fix
```

## Test Commands

### Backend (Python/Pytest)

```bash
# Run all tests
cd Backend && pytest

# Run a single test file
cd Backend && pytest tests/api/test_auth_endpoints.py

# Run a specific test function
cd Backend && pytest tests/api/test_auth_endpoints.py::test_user_registration

# Run tests with coverage
cd Backend && pytest --cov=core --cov=api --cov=services

# Run tests in verbose mode
cd Backend && pytest -v

# Run tests in collect-only mode to see what will be executed
cd Backend && pytest tests/api/test_processing_contract_improved.py --collect-only -q
```

### Frontend (TypeScript/Vitest)

```bash
# Run all tests
cd Frontend && npm run test

# Run a single test file
cd Frontend && npm run test -- src/components/auth/LoginForm.test.tsx

# Run tests in watch mode
cd Frontend && npm run test -- --watch
```

## Code Style Guidelines

### Backend (Python)

1. **Imports**:
   - Standard library, third-party, then local imports
   - Import sorting with isort (first-party: api, core, database, services, tests)
   - Specific imports over wildcard imports

2. **Formatting**:
   - PEP 8 with 4-space indentation
   - Line length: 88 characters
   - Double quotes for strings
   - Google-style docstrings
   - Use Ruff for formatting

3. **Types**:
   - Explicit type hints for all functions
   - Pydantic models for data structures
   - UUID for user IDs (not integers)

4. **Naming Conventions**:
   - snake_case for variables/functions
   - PascalCase for classes
   - UPPER_CASE for constants

5. **Error Handling**:
   - Specific exception types
   - Log errors with context
   - Structured exception handling
   - Consistent error response formats

6. **Database**:
   - SQLAlchemy async sessions
   - UserManager.parse_id() for UUID handling
   - Alembic for migrations

7. **Testing**:
   - Use `@pytest.mark.asyncio` for async tests (not `@pytest.mark.anyio`)
   - Only asyncio backend is used (no trio)
   - Transaction rollback for test isolation

### Frontend (TypeScript/React)

1. **Imports**:
   - Path aliases (@/\*) for internal modules
   - Type-only imports with `import type {}`
   - Default imports for libraries

2. **Formatting**:
   - Prettier/ESLint for consistent formatting
   - TypeScript strict mode

3. **Types**:
   - Interfaces for component props
   - TypeScript for all components/functions

4. **Naming Conventions**:
   - PascalCase for components/files
   - camelCase for variables/functions
   - UPPER_CASE for constants

### Testing Best Practices

- Use transaction rollback for test isolation
- Follow FastAPI-Users API behavior (form data for login)
- Auth responses: {"access_token": "...", "token_type": "bearer"}
- Use auth helpers from tests/auth_helpers.py
- Generate unique test data with AuthTestHelper.generate_unique_user_data()

### WSL/Windows Interoperability

- Execute Python with api_venv
- Windows Python: /mnt/e/path/to/python.exe
- Run .bat files: cmd.exe /c filename.bat
- Clean up processes: cmd.exe /c "taskkill /F /IM cmd.exe && taskkill /F /IM python.exe && taskkill /F /IM node.exe"
