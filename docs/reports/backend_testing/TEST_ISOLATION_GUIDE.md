# Test Isolation & Database Setup Guide

## Overview

This guide explains how to use the test isolation infrastructure to ensure reliable, deterministic tests with proper state cleanup.

## Core Isolation Principles

### 1. Complete Test Independence

Each test should run as if it's the only test in the suite:

- No shared state between tests
- No dependencies on test execution order
- Deterministic outcomes regardless of parallel execution

### 2. Database Isolation Levels

Different test types require different isolation levels:

#### Level 1: In-Memory Database (Default)

```python
@pytest.mark.anyio
async def test_basic_functionality(async_client):
    # Uses per-test SQLite database in memory
    # Automatically cleaned up after test
    response = await async_client.get("/api/endpoint")
    assert response.status_code == 200
```

#### Level 2: Transaction Rollback (Recommended for Database Tests)

```python
@pytest.mark.anyio
async def test_database_operations(async_client, isolated_db_session):
    # All database changes are rolled back after test
    # Perfect isolation with real database operations
    user = User(username="test", email="test@example.com")
    isolated_db_session.add(user)
    await isolated_db_session.commit()

    # Changes exist during test but are rolled back after
```

#### Level 3: Clean Database State (For Complex Scenarios)

```python
@pytest.mark.anyio
async def test_complex_workflow(async_client, clean_database):
    # Database is completely empty at start and end of test
    # Useful for testing migration scenarios or complex state
    response = await async_client.post("/api/setup-workflow")
    assert response.status_code == 200
```

#### Level 4: Seeded Database (For Integration Tests)

```python
@pytest.mark.anyio
async def test_with_known_data(async_client, seeded_database):
    # Database contains consistent test data
    # Users: testuser1, testuser2, admin_test are pre-created
    response = await async_client.get("/api/users")
    assert len(response.json()) == 3
```

## Available Fixtures

### Database Fixtures

#### `app` - Per-Test Application Instance

```python
def test_endpoint_behavior(app):
    # Fresh FastAPI app with per-test SQLite database
    # Automatically cleaned up after test
    assert app is not None
```

#### `async_client` - In-Process HTTP Client

```python
@pytest.mark.anyio
async def test_api_endpoint(async_client):
    # Async HTTP client that runs app in-process
    # No external server required
    response = await async_client.get("/health")
    assert response.status_code == 200
```

#### `isolated_db_session` - Transaction-Based Isolation

```python
@pytest.mark.anyio
async def test_database_changes(isolated_db_session):
    # All changes automatically rolled back after test
    user = User(username="test")
    isolated_db_session.add(user)
    await isolated_db_session.commit()

    # Changes visible during test but rolled back after
```

#### `clean_database` - Empty Database State

```python
@pytest.mark.anyio
async def test_from_clean_state(clean_database, app):
    # Database is completely empty
    # All tables truncated before and after test
    session_factory = app.state._test_session_factory
    async with session_factory() as session:
        # Database is guaranteed to be empty
        result = await session.execute("SELECT COUNT(*) FROM users")
        assert result.scalar() == 0
```

#### `seeded_database` - Pre-Populated Test Data

```python
@pytest.mark.anyio
async def test_with_seed_data(seeded_database, app):
    # Standard test users pre-created
    # testuser1@example.com, testuser2@example.com, admin@example.com
    session_factory = app.state._test_session_factory
    async with session_factory() as session:
        result = await session.execute("SELECT COUNT(*) FROM users")
        assert result.scalar() == 3
```

### Test State Management

#### `test_pollution_detector` (Auto-Used)

```python
# Automatically detects mock pollution and state leakage
# Warns if too many mock objects accumulate
# No explicit usage required - runs automatically
```

#### `clean_mock_session` - Fresh Mock Session

```python
def test_service_with_clean_mocks(clean_mock_session):
    # Guaranteed fresh mock session
    # No state from previous tests
    clean_mock_session.execute.return_value = mock_result
    # Test implementation
```

#### `database_state_validator` - State Consistency Checking

```python
@pytest.mark.anyio
async def test_database_consistency(database_state_validator, app):
    # Validate database state before and after operations
    await database_state_validator(app, "before operations")

    # Perform database operations

    await database_state_validator(app, "after operations")
```

## Best Practices

### 1. Choose the Right Isolation Level

```python
# Unit tests - No database needed
def test_business_logic():
    result = calculate_something(input_data)
    assert result == expected

# Integration tests - Use isolated sessions
@pytest.mark.anyio
async def test_api_with_database(async_client, isolated_db_session):
    response = await async_client.post("/api/create", json=data)
    assert response.status_code == 201

# Complex integration - Use clean database
@pytest.mark.anyio
async def test_complex_workflow(async_client, clean_database):
    # Multi-step workflow starting from empty state

# Tests needing standard data - Use seeded database
@pytest.mark.anyio
async def test_user_interactions(async_client, seeded_database):
    # Test interactions with existing users
```

### 2. Avoid Shared Test State

```python
# BAD: Global state that affects other tests
test_user_counter = 0

def test_user_creation():
    global test_user_counter
    test_user_counter += 1
    # Other tests affected by this counter

# GOOD: Self-contained state
@pytest.mark.anyio
async def test_user_creation(async_client):
    user_data = {"username": f"user_{uuid4().hex[:8]}"}
    response = await async_client.post("/api/users", json=user_data)
    assert response.status_code == 201
```

### 3. Use Proper Data Builders

```python
# Use the helpers/data_builders.py utilities
from tests.helpers import UserBuilder, TestDataSets

@pytest.mark.anyio
async def test_user_workflow(async_client, isolated_db_session):
    # Create test data with builders
    user = UserBuilder().with_username("testuser").as_admin().build()
    concepts = TestDataSets.create_german_vocabulary_set()

    # Test with well-structured data
```

### 4. Test Cleanup Verification

```python
@pytest.mark.anyio
async def test_cleanup_verification(async_client, clean_database, app):
    # Verify clean start
    session_factory = app.state._test_session_factory
    async with session_factory() as session:
        count_before = await session.execute("SELECT COUNT(*) FROM users")
        assert count_before.scalar() == 0

    # Perform operations
    response = await async_client.post("/api/users", json=user_data)
    assert response.status_code == 201

    # clean_database fixture ensures cleanup after test
```

## Performance Considerations

### Fast Test Execution

- **In-Memory SQLite**: Tests run 10x faster than external databases
- **Transaction Rollback**: Faster than table truncation for complex data
- **Per-Test Isolation**: Enables safe parallel test execution

### Memory Management

```python
# Tests automatically clean up database connections
# No manual cleanup required for standard fixtures

# For custom resources, use proper teardown
@pytest.fixture
async def custom_resource():
    resource = await create_expensive_resource()
    try:
        yield resource
    finally:
        await resource.cleanup()
```

## Troubleshooting

### Common Issues

#### Test Pollution

```python
# Symptom: Tests pass individually but fail in suite
# Cause: Shared state or inadequate cleanup

# Solution: Use proper isolation fixtures
@pytest.mark.anyio
async def test_isolated_behavior(async_client, isolated_db_session):
    # Guaranteed clean state
```

#### Database Lock Errors

```python
# Symptom: SQLite database lock errors
# Cause: Unclosed database connections

# Solution: Use fixtures properly (they handle cleanup)
@pytest.mark.anyio
async def test_with_proper_session(async_client):
    # async_client fixture handles all database management
    response = await async_client.get("/api/data")
```

#### Mock State Leakage

```python
# Symptom: Mocks affect unrelated tests
# Cause: Mock objects not properly isolated

# Solution: Use clean_mock_session fixture
def test_with_clean_mocks(clean_mock_session):
    # Fresh mock state guaranteed
```

### Debug Tools

#### Test State Inspection

```python
@pytest.mark.anyio
async def test_debug_state(app, database_state_validator):
    # Inspect database state at any point
    await database_state_validator(app, "debug checkpoint")

    # Check for mock pollution
    import gc
    mock_count = len([obj for obj in gc.get_objects()
                     if isinstance(obj, (MagicMock, AsyncMock))])
    print(f"Mock objects: {mock_count}")
```

## Migration from Legacy Tests

### Before: External Dependencies

```python
# OLD: Flaky, slow, environment-dependent
def test_with_real_server():
    subprocess.run(["uvicorn", "main:app", "--port", "8001"])
    time.sleep(5)  # Wait for startup
    response = requests.get("http://localhost:8001/health")
    assert response.status_code == 200
```

### After: Isolated In-Process

```python
# NEW: Fast, reliable, deterministic
@pytest.mark.anyio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

### Before: Shared Database State

```python
# OLD: Tests affect each other
def test_user_creation():
    # Assumes database state from previous tests
    user = create_user("testuser")
    assert user.id == expected_id  # Breaks if run out of order

def test_user_count():
    assert get_user_count() == 5  # Depends on previous test
```

### After: Isolated State

```python
# NEW: Independent, reliable
@pytest.mark.anyio
async def test_user_creation(async_client, isolated_db_session):
    user_data = {"username": "testuser", "email": "test@example.com"}
    response = await async_client.post("/api/users", json=user_data)

    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == "testuser"

@pytest.mark.anyio
async def test_user_count_starts_at_zero(async_client, clean_database):
    response = await async_client.get("/api/users")
    assert response.status_code == 200
    assert len(response.json()) == 0
```

## Test Categorization

### Mark Tests by Isolation Requirements

```python
@pytest.mark.unit
def test_pure_function():
    # No database or external dependencies

@pytest.mark.integration
@pytest.mark.anyio
async def test_api_endpoint(async_client, isolated_db_session):
    # Tests API with database in isolation

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.anyio
async def test_complete_workflow(seeded_database, async_client):
    # End-to-end workflow with pre-populated data
```

### Run Tests by Category

```bash
# Fast unit tests only
pytest -m unit

# Integration tests with isolation
pytest -m integration

# Everything except slow tests
pytest -m "not slow"

# Full suite including E2E
pytest
```

## Summary

The test isolation infrastructure provides:

- **Zero shared state** between tests
- **Deterministic execution** regardless of order
- **Fast, reliable** test runs with in-memory databases
- **Proper cleanup** with automatic teardown
- **Multiple isolation levels** for different test needs

Choose the appropriate fixtures based on your test requirements, and follow the patterns to ensure reliable, maintainable tests.
