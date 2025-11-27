# Test Standards & Best Practices

## Test Taxonomy

### Unit Tests (`tests/unit/`)

**Purpose**: Test individual functions/classes in isolation

- **Speed**: < 100ms per test
- **Dependencies**: Fully mocked, no external systems
- **Scope**: Single function/method behavior
- **Location**: Mirror source structure: `tests/unit/services/test_auth_service.py`

**Requirements**:

- ✅ All external dependencies mocked
- ✅ Fast, deterministic execution
- ✅ Test public APIs, not implementation details
- ❌ No database connections
- ❌ No file system access
- ❌ No network calls
- ❌ No subprocess spawning

### Integration Tests (`tests/integration/`)

**Purpose**: Test component interactions within process boundaries

- **Speed**: < 5s per test
- **Dependencies**: In-process only (TestClient, in-memory DB)
- **Scope**: API endpoints, service integration, database operations
- **Location**: `tests/integration/test_auth_endpoints.py`

**Requirements**:

- ✅ Use FastAPI TestClient or async client
- ✅ In-memory databases with transaction rollback
- ✅ Dependency injection for test doubles
- ✅ Proper setup/teardown per test
- ❌ No external processes (uvicorn, docker)
- ❌ No real file system dependencies
- ❌ No polling/sleep patterns

### Contract Tests (`tests/contract/`)

**Purpose**: Validate API schemas and data structures

- **Speed**: < 1s per test
- **Dependencies**: Schema validation only
- **Scope**: Request/response formats, data models
- **Location**: `tests/contract/test_auth_contract.py`

**Requirements**:

- ✅ Pydantic model validation
- ✅ OpenAPI schema compliance
- ✅ Mock all external systems
- ❌ No real backend dependencies
- ❌ No network calls

### End-to-End Tests (`tests/e2e/`)

**Purpose**: Critical user journeys only

- **Speed**: < 30s per test
- **Dependencies**: Minimal, well-controlled
- **Scope**: Complete workflows
- **Location**: `tests/e2e/test_user_registration_flow.py`

**Constraints**:

- Maximum 10 E2E tests total
- Only test critical business flows
- Proper cleanup and isolation
- Clear failure diagnostics

## Anti-Patterns to Eliminate

### ❌ Loose Assertions

```python
# BAD: Accepts both success and failure
assert response.status_code in {200, 500}

# GOOD: Explicit expectations
assert response.status_code == 200
data = response.json()
assert "languages" in data
```

### ❌ Print-Based Testing

```python
# BAD: No assertions, just output
print(f"Test result: {result}")

# GOOD: Proper assertions
assert result.is_valid
assert len(result.errors) == 0
```

### ❌ External Process Dependencies

```python
# BAD: Spawns real server
subprocess.Popen(["uvicorn", "main:app"])
time.sleep(5)  # Wait for startup

# GOOD: In-process testing
client = TestClient(app)
response = client.get("/health")
```

### ❌ Implementation Coupling

```python
# BAD: Tests internal mock calls
mock_session.execute.assert_called_exactly(3)

# GOOD: Tests behavior
result = await service.get_stats()
assert result.total_concepts == 100
```

### ❌ Shared State Dependencies

```python
# BAD: Depends on seeded data
response = client.get("/vocab/stats")  # Relies on DB state

# GOOD: Self-contained data
user = await create_test_user()
response = client.get("/vocab/stats", auth=user.token)
```

### ❌ Hardcoded Credentials & External Tokens

```python
# BAD: Real bearer token committed to source control
headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1Ni..."}

# GOOD: Use fixtures or env vars so secrets never land in tests
headers = make_auth_headers(test_user)
```

### ❌ Unauthorized Skip Markers

**Policy**: Per CLAUDE.md: "Never introduce skip/xfail/ignore markers to bypass a failing path. Surface the failure and coordinate with the user."

```python
# BAD: Hiding broken functionality
@pytest.mark.skip(reason="Test fails, need to fix later")
def test_authentication_flow():
    ...

# BAD: Skip without proper justification
@pytest.mark.skip
def test_payment_processing():
    ...

# ACCEPTABLE: Optional AI/ML dependency
@pytest.mark.skip(reason="Requires PyTorch (pip install torch)")
def test_translation_model():
    ...

# ACCEPTABLE: Environment-controlled
@pytest.mark.skipif(
    os.environ.get("SKIP_HEAVY_AI_TESTS") == "1",
    reason="Skipping AI model tests"
)
def test_whisper_transcription():
    ...
```

**Approved Skip Reasons** (pre-commit hook enforced):

- **AI/ML Dependencies**: `"Requires openai-whisper"`, `"Requires PyTorch"`, `"Requires spaCy"`
- **Installation Instructions**: Must include `"pip install ..."`
- **Environment Variables**: `"SKIP_HEAVY_AI_TESTS"`, performance test flags
- **Manual/Performance Tests**: Tests in `tests/manual/` directory

**What to do instead**:

1. **Fix the test** - Most common solution
2. **Delete the test** - If obsolete or testing wrong behavior
3. **Add approved reason** - Only for optional dependencies
4. **Coordinate with user** - Get approval for exceptions

**Pre-commit Hook**: A pre-commit hook automatically checks for unauthorized skip markers and blocks commits with unapproved skips.

## Required Patterns

### ✅ Arrange-Act-Assert Structure

```python
async def test_get_vocabulary_returns_correct_format():
    # Arrange
    user = await create_test_user()
    vocab_data = create_test_vocabulary(level="A1")

    # Act
    response = await client.get("/vocab", auth=user.token)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["vocabulary"]) > 0
```

### ✅ Descriptive Test Names

```python
# Pattern: test_When<condition>_Then<expected_outcome>
def test_When_invalid_password_provided_Then_returns_validation_error()
def test_When_user_not_authenticated_Then_returns_401_unauthorized()
def test_When_vocabulary_requested_Then_returns_user_specific_data()
```

### ✅ Proper Error Testing

```python
async def test_When_invalid_credentials_Then_raises_authentication_error():
    with pytest.raises(AuthenticationError) as exc_info:
        await auth_service.authenticate("invalid", "wrong")

    assert "Invalid credentials" in str(exc_info.value)
```

### ✅ Test Data Builders

```python
def create_test_user(username: str = None, **kwargs) -> User:
    return User(
        username=username or f"user_{uuid4().hex[:8]}",
        password_hash="hashed_password",
        is_active=True,
        **kwargs
    )
```

## File Organization

```
Backend/tests/
├── unit/                  # Fast, isolated unit tests
│   ├── services/
│   ├── models/
│   └── core/
├── integration/           # In-process integration tests
│   ├── api/
│   └── database/
├── contract/             # Schema/API contract tests
├── e2e/                  # Minimal end-to-end tests
├── fixtures/             # Shared test data and fixtures
├── helpers/              # Test utility functions
│   ├── auth_helpers.py
│   ├── data_builders.py
│   └── assertions.py
└── conftest.py           # Pytest configuration
```

## Performance Standards

| Test Type   | Max Duration | Max Memory | Parallel Safe |
| ----------- | ------------ | ---------- | ------------- |
| Unit        | 100ms        | 50MB       | ✅ Yes        |
| Integration | 5s           | 200MB      | ✅ Yes        |
| Contract    | 1s           | 100MB      | ✅ Yes        |
| E2E         | 30s          | 500MB      | ❌ Sequential |

## Coverage Requirements

- **Unit Tests**: 80% line coverage minimum
- **Critical Paths**: 100% coverage (auth, payments, data integrity)
- **Exclusions**: Auto-generated code, external API clients
- **Integration**: All API endpoints must have contract tests
- **Error Paths**: All custom exceptions must be tested

## Review Checklist

Before merging any test changes:

### Code Quality

- [ ] Test names clearly describe the scenario
- [ ] Single responsibility per test
- [ ] Proper arrange-act-assert structure
- [ ] No implementation details tested
- [ ] All assertions are explicit and meaningful

### Performance & Reliability

- [ ] Tests run within time limits
- [ ] No external dependencies in unit/integration tests
- [ ] Proper cleanup and isolation
- [ ] Tests pass consistently (no flaky tests)
- [ ] No hardcoded credentials or secrets

### Maintainability

- [ ] Tests will survive reasonable refactoring
- [ ] Clear failure messages
- [ ] Minimal duplication via helpers/fixtures
- [ ] Follows established patterns and conventions

## Migration Strategy

1. **New tests**: Follow these standards immediately
2. **Existing tests**: Gradual migration, prioritize most problematic first
3. **Safety net**: Keep working tests until replacements are proven
4. **Documentation**: Update examples and guidelines as patterns evolve
