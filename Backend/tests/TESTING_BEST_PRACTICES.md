# Testing Best Practices for LangPlug Backend

## Overview

This document outlines the best practices for testing in the LangPlug Backend project, including patterns for robust mock isolation, database testing, and test infrastructure management.

## Test Infrastructure Architecture

### Base Classes

#### DatabaseTestBase (`tests/base.py`)

- **Purpose**: Provides standardized database session mocking with proper isolation
- **Usage**: Inherit from this class for any test that needs database interaction
- **Key Features**:
  - Isolated mock sessions for each test
  - Standardized query result configuration
  - Session operation validation

```python
from tests.base import DatabaseTestBase

class TestMyService(DatabaseTestBase):
    def test_my_function(self):
        mock_session = self.create_mock_session()
        self.configure_mock_query_result(mock_session, {
            'scalar_one_or_none': None  # No existing record
        })
        # Test implementation
```

#### ServiceTestBase (`tests/base.py`)

- **Purpose**: Enhanced database testing for service layer tests
- **Usage**: For testing business logic services that interact with the database
- **Key Features**:
  - Built-in session operation assertions
  - Isolated mock session fixtures
  - Transaction validation

#### RouteTestBase (`tests/base.py`)

- **Purpose**: API route testing with proper dependency injection mocking
- **Usage**: For testing FastAPI routes and endpoints
- **Key Features**:
  - Context manager mocks for dependency injection
  - HTTP response validation
  - Authentication flow helpers

### Standardized Mock Patterns

#### Using StandardMockPatterns (`tests/mock_standards.py`)

```python
from tests.mock_standards import StandardMockPatterns

# Create standardized session mock
mock_session = StandardMockPatterns.mock_sqlalchemy_session()

# Configure query results
StandardMockPatterns.configure_session_query_results(mock_session, {
    'scalar_one_or_none': None,
    'all': [mock_user1, mock_user2],
    'rowcount': 2
})

# Create FastAPI dependency context
mock_context = StandardMockPatterns.mock_fastapi_dependency_context(mock_session)
```

## Testing Categories

### 1. Unit Tests (`tests/unit/`)

**Scope**: Individual functions and methods in isolation
**Principles**:

- Test one function at a time
- Mock external dependencies while keeping fixtures lightweight
- Focus on business logic that surfaces through return values or observable side-effects
- Assert on user-facing outcomes first; interaction/count assertions are strictly optional and only when the behaviour cannot be observed otherwise
- Fast execution (< 100ms per test)

**Example Structure**:

```python
class TestAuthService(ServiceTestBase):
    async def test_register_user_success(self, isolated_mock_session):
        # Arrange
        service = AuthService(isolated_mock_session)

        # Act
        result = await service.register_user('testuser@example.com', 'Sup3rSecret!')

        # Assert
        assert result.email == 'testuser@example.com'
        assert result.is_active is True
        # Optional: verify essential side-effect when not observable elsewhere
        self.assert_session_operations(isolated_mock_session, {
            'add': 1,
            'commit': 1,
        })
```

### 2. Integration Tests (`tests/integration/`)

**Scope**: Multiple components working together
**Principles**:

- Test component interactions
- Use in-memory databases when possible
- Validate data flow between layers
- Moderate execution time (< 1s per test)

### 3. API/Route Tests (`tests/unit/test_*_routes.py`)

**Scope**: HTTP endpoint testing
**Principles**:

- Test complete request/response cycle
- Mock database dependencies
- Validate status codes and response structure
- Test authentication and authorization

## Mock Isolation Strategies

### The Problem

Tests can fail due to mock pollution, where mocks from one test affect another test. This manifests as:

- Tests that pass individually but fail in groups
- Intermittent failures
- Tests dependent on execution order

### Solution: Proper Mock Isolation

#### 1. Use Fresh Mock Instances

```python
# ❌ BAD: Shared mock instance
@pytest.fixture
def shared_mock_session():
    return create_mock_session()  # Same instance reused

# ✅ GOOD: Fresh instance per test
@pytest.fixture
def fresh_mock_session():
    return DatabaseTestBase.create_mock_session()  # New instance each time
```

#### 2. Configure Mock State Per Test

```python
def test_user_exists(self, auth_service):
    service, mock_session = auth_service

    # Configure this test's specific behavior
    self.configure_mock_query_result(mock_session, {
        'scalar_one_or_none': mock_user  # User exists
    })

    # Test implementation
```

#### 3. Use Context Managers for Patches

```python
def test_with_external_dependency(self):
    with patch('module.external_service') as mock_service:
        mock_service.return_value = expected_result
        # Test implementation
    # Patch automatically cleaned up
```

## Database Testing Patterns

### Mock Database Sessions

```python
# Create standardized mock session
mock_session = DatabaseTestBase.create_mock_session()

# Configure query results
DatabaseTestBase.configure_mock_query_result(mock_session, {
    'scalar_one_or_none': None,  # SELECT ... LIMIT 1
    'all': [mock_record1, mock_record2],  # SELECT all records
    'rowcount': 1,  # Number of affected rows
    'first': mock_record1  # First record
})

# Test service method
result = await service.find_user(user_id=1)
```

### Sequential Query Results

For tests that make multiple database queries:

```python
# Create sequence of results for multiple execute() calls
results = DatabaseTestBase.create_mock_execute_sequence([
    {'scalar_one_or_none': None},  # First query: no user
    {'rowcount': 1}  # Second query: insert successful
])

mock_session.execute.side_effect = results
```

## Error Testing Patterns

### Database Errors

```python
def test_database_error_handling(self, service_with_mock):
    service, mock_session = service_with_mock

    # Configure session to raise database error
    mock_session.execute.side_effect = Exception("Database connection failed")

    # Test that service handles the error appropriately
    with pytest.raises(ServiceError) as exc_info:
        await service.get_user(user_id=1)

    assert "Database connection failed" in str(exc_info.value)
    # Optional: use the helper to confirm a critical side-effect like rollbacks
    self.assert_session_operations(mock_session, {
        'rollback': 1
    })
```

### HTTP Error Testing

```python
def test_api_error_handling(self, async_client):
    # Mock dependency to raise exception
    mock_context, mock_session = RouteTestBase.create_mock_session_context()
    mock_session.execute.side_effect = Exception("Database error")

    with patch('api.routes.module.get_async_session') as mock_get_session:
        mock_get_session.return_value = mock_context

        response = await async_client.get("/api/endpoint")

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]
```

## Test Health Monitoring

### Automatic Validation

The test infrastructure includes automatic validation:

```python
# Tests automatically validate cleanup
@pytest.mark.usefixtures("test_cleanup_validator")
def test_my_function(self):
    # Test implementation
    pass  # Cleanup automatically validated
```

### Health Metrics

Monitor test performance and reliability:

```python
@pytest.mark.usefixtures("health_monitored_test")
def test_with_monitoring(self, health_monitored_test):
    # Test implementation
    # Metrics automatically collected:
    # - Execution time
    # - Memory usage
    # - Mock cleanup rate
```

## Common Anti-Patterns and Solutions

### ❌ Anti-Pattern: Shared Mock State

```python
# BAD: Mock configured once, shared across tests
@pytest.fixture(scope="module")
def shared_mock():
    mock = create_mock()
    mock.configure_behavior()
    return mock
```

### ✅ Solution: Per-Test Mock Configuration

```python
# GOOD: Fresh mock per test with explicit configuration
@pytest.fixture
def isolated_mock():
    return create_fresh_mock()

def test_scenario_a(self, isolated_mock):
    configure_mock_for_scenario_a(isolated_mock)
    # Test implementation
```

### ❌ Anti-Pattern: Hard-Coded Mock Values

```python
# BAD: Hard-coded values make tests brittle
mock_user.id = 123
mock_user.username = "testuser"
```

### ✅ Solution: Dynamic Test Data

```python
# GOOD: Use factories or builders for test data
from tests.factories import UserFactory

mock_user = UserFactory.create(
    username=f"testuser_{test_id}",
    email=f"test_{test_id}@example.com"
)
```

### ❌ Anti-Pattern: Testing Implementation Details

```python
# BAD: Test depends on internal implementation
assert service.database_connection.execute.called
```

### ✅ Solution: Test Interface Behavior

```python
# GOOD: Test the public interface and observable behavior
result = await service.get_user(user_id=1)
assert result.username == "expected_username"
```

## Test Organization

### File Structure

```
tests/
├── base.py                    # Base test classes
├── mock_standards.py          # Standardized mock patterns
├── fixture_validation.py      # Automatic validation
├── conftest.py               # Pytest configuration
├── auth_helpers.py           # Authentication test utilities
├── unit/
│   ├── models/               # Model tests
│   ├── services/             # Service layer tests
│   └── test_*_routes.py      # Route tests
├── integration/
│   └── test_*.py             # Integration tests
└── e2e/
    └── test_*.py             # End-to-end tests
```

### Naming Conventions

- **Files**: `test_<module_name>.py`
- **Classes**: `Test<FeatureName><TestType>` (e.g., `TestAuthServiceRegistration`)
- **Methods**: `test_<action>_<expected_outcome>` (e.g., `test_register_user_success`)

## Debugging Failed Tests

### Common Failure Modes

1. **Mock Pollution**: Test passes alone but fails in group
   - **Solution**: Use `isolated_mock_session` fixture
   - **Validation**: Check mock cleanup rate in test report

2. **Database State Issues**: Tests dependent on execution order
   - **Solution**: Use transaction rollback in teardown
   - **Validation**: Run tests with `--random-order`

3. **Async Context Issues**: Context managers not properly awaited
   - **Solution**: Use `@validate_async_fixture` decorator
   - **Validation**: Check for coroutine warnings

### Debug Tools

```python
# Enable detailed mock call logging
from tests.fixture_validation import DatabaseTestValidator

def test_with_debugging(self, mock_session):
    # Validate mock setup
    validation = DatabaseTestValidator.validate_session_mock(mock_session)
    print(f"Mock validation: {validation}")

    # Get improvement suggestions
    suggestions = DatabaseTestValidator.suggest_mock_improvements(mock_session)
    if suggestions:
        print(f"Mock improvements: {suggestions}")
```

## Migration Guide

### Upgrading Existing Tests

1. **Inherit from Base Classes**:

   ```python
   # Before
   class TestMyService:
       pass

   # After
   class TestMyService(ServiceTestBase):
       pass
   ```

2. **Use Standardized Mocks**:

   ```python
   # Before
   mock_session = AsyncMock()

   # After
   mock_session = DatabaseTestBase.create_mock_session()
   ```

3. **Add Validation**:

   ```python
   # Before
   result = await service.create_user(data)
   assert result is not None

   # After
   result = await service.create_user(data)
   assert result is not None
   self.assert_session_operations(mock_session, {
       'add': 1,
       'commit': 1
   })
   ```

## Performance Guidelines

### Target Metrics

- **Unit tests**: < 100ms per test
- **Integration tests**: < 1s per test
- **Mock cleanup rate**: > 80%
- **Memory leak detection**: < 10MB per test suite

### Performance Monitoring

The test infrastructure automatically monitors:

- Execution time per test
- Memory usage patterns
- Mock cleanup rates
- Failure pattern analysis

Results are reported at the end of each test session.

## Conclusion

Following these best practices will lead to:

- **Reliable tests**: Consistent results across environments
- **Maintainable tests**: Easy to understand and modify
- **Fast feedback**: Quick identification of issues
- **Robust infrastructure**: Self-healing and self-monitoring test suite

The test infrastructure provided (`DatabaseTestBase`, `StandardMockPatterns`, `FixtureValidator`) automates many of these best practices, making it easier to write high-quality tests while reducing boilerplate code.
