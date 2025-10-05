# Testing Best Practices for LangPlug Backend

**Version**: 1.0
**Last Updated**: 2025-10-03

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Structure & Organization](#test-structure--organization)
3. [Unit Testing](#unit-testing)
4. [Integration Testing](#integration-testing)
5. [End-to-End Testing](#end-to-end-testing)
6. [Async Testing Patterns](#async-testing-patterns)
7. [Fixtures & Test Data](#fixtures--test-data)
8. [Mocking & Stubbing](#mocking--stubbing)
9. [Common Patterns](#common-patterns)
10. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
11. [Test Quality Checklist](#test-quality-checklist)

---

## Testing Philosophy

### Core Principles

1. **Test Behavior, Not Implementation**
   - Focus on observable outcomes, not internal mechanisms
   - Tests should survive refactoring without changes
   - Verify public contracts, not private methods

2. **Independence & Isolation**
   - Tests must be deterministic and isolated
   - No dependencies on test execution order
   - Each test cleans up after itself

3. **Fast Feedback Loop**
   - Unit tests should run in milliseconds
   - Integration tests in seconds
   - Entire suite in minutes

4. **Maintainability**
   - Clear, descriptive test names
   - Well-organized test structure
   - DRY principle (Don't Repeat Yourself)
   - Living documentation through tests

5. **Confidence Over Coverage**
   - 80% meaningful coverage > 100% trivial coverage
   - Test critical paths thoroughly
   - Focus on business logic over boilerplate

### Test Pyramid

```
        /\
       /E2E\      ← Few (4%)  - Slow, expensive, high value
      /------\
     /  INT   \   ← Some (22%) - Medium speed, integration points
    /----------\
   /   UNIT     \ ← Many (74%) - Fast, focused, low cost
  /--------------\
```

**Distribution Goal**:

- **Unit Tests**: 70-75% (fast, focused, isolated)
- **Integration Tests**: 20-25% (API contracts, service integration)
- **E2E Tests**: 3-5% (critical user workflows)

---

## Test Structure & Organization

### Directory Structure

```
tests/
├── unit/                    # Unit tests (isolated components)
│   ├── services/
│   ├── core/
│   ├── models/
│   └── dtos/
├── integration/            # Integration tests (multi-component)
│   └── api/
├── api/                    # API contract tests
├── e2e_*.py               # End-to-end tests
├── security/              # Security tests
├── performance/           # Performance benchmarks
├── fixtures/              # Shared fixtures
├── helpers/               # Test utilities
└── conftest.py           # Pytest configuration
```

### File Naming Conventions

- **Unit tests**: `tests/unit/<module>/test_<component>.py`
- **Integration tests**: `tests/integration/test_<feature>_integration.py`
- **API tests**: `tests/api/test_<resource>_routes.py`
- **E2E tests**: `tests/e2e_<scenario>.py`

### Test Function Naming

Use descriptive names that explain **what** is being tested and **what** the expected outcome is:

```python
# ✅ Good - Clear scenario and expected outcome
def test_When_invalid_token_provided_Then_returns_401_unauthorized():
    pass

def test_user_can_update_vocabulary_word_status():
    pass

def test_video_upload_requires_authentication():
    pass

# ❌ Bad - Vague, unclear what is tested
def test_token():
    pass

def test_vocabulary():
    pass

def test_video_function():
    pass
```

**Naming Pattern**: `test_<scenario>_<expected_outcome>` or `test_When_<condition>_Then_<result>`

---

## Unit Testing

### What to Unit Test

Unit tests verify **individual components** in isolation:

- ✅ Service layer business logic
- ✅ Data validation and transformation
- ✅ Calculation and algorithm correctness
- ✅ Error handling and edge cases
- ✅ Utility functions
- ✅ Repository methods (with mocked database)

### Unit Test Structure (Arrange-Act-Assert)

```python
import pytest
from services.vocabulary.vocabulary_service_new import VocabularyService


class TestVocabularyService:
    """Test suite for VocabularyService"""

    def test_When_word_added_to_known_list_Then_status_updated_correctly(self):
        """Test that marking a word as known updates its status"""
        # Arrange (Setup)
        service = VocabularyService()
        user_id = "test-user-123"
        word = "Hallo"

        # Act (Execute)
        result = service.mark_word_as_known(user_id, word)

        # Assert (Verify)
        assert result.status == "known"
        assert result.word == word
        assert result.marked_at is not None
```

### Testing Edge Cases

```python
class TestPasswordValidator:
    """Test password validation rules"""

    # Happy path
    def test_valid_password_passes_validation(self):
        """Test that a valid password is accepted"""
        validator = PasswordValidator()
        assert validator.validate("SecurePass123!") is True

    # Edge cases
    def test_empty_password_fails_validation(self):
        """Test that empty password is rejected"""
        validator = PasswordValidator()
        with pytest.raises(ValidationError, match="Password cannot be empty"):
            validator.validate("")

    def test_short_password_fails_validation(self):
        """Test that passwords shorter than 8 characters are rejected"""
        validator = PasswordValidator()
        with pytest.raises(ValidationError, match="at least 8 characters"):
            validator.validate("short")

    def test_password_without_numbers_fails_validation(self):
        """Test that passwords without numbers are rejected"""
        validator = PasswordValidator()
        with pytest.raises(ValidationError, match="contain at least one number"):
            validator.validate("SecurePassword!")
```

### Testing Exceptions

```python
def test_invalid_user_id_raises_value_error(self):
    """Test that invalid user ID raises ValueError"""
    service = VocabularyService()

    with pytest.raises(ValueError, match="Invalid user ID"):
        service.get_user_words(user_id=None)


def test_database_error_is_propagated(self):
    """Test that database errors are not silently caught"""
    service = VocabularyService()

    with pytest.raises(DatabaseError):
        service.save_word("user-id", None)  # Will trigger DB error
```

---

## Integration Testing

### What to Integration Test

Integration tests verify that **multiple components work together**:

- ✅ API endpoint contracts (request → response)
- ✅ Database transactions and rollback
- ✅ Service-to-service communication
- ✅ Authentication and authorization flows
- ✅ File uploads and processing
- ✅ WebSocket connections

### API Contract Testing

```python
import pytest
from httpx import AsyncClient


class TestVocabularyAPI:
    """Integration tests for vocabulary API endpoints"""

    @pytest.mark.asyncio
    async def test_GET_vocabulary_words_returns_user_words(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test that GET /api/vocabulary/words returns authenticated user's words"""
        # Arrange
        # (auth_headers fixture provides authentication)

        # Act
        response = await async_client.get(
            "/api/vocabulary/words",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert all("word" in item for item in data)
        assert all("status" in item for item in data)


    @pytest.mark.asyncio
    async def test_POST_vocabulary_mark_word_updates_status(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test that POST /api/vocabulary/mark updates word status"""
        # Arrange
        payload = {
            "word": "Hallo",
            "status": "known"
        }

        # Act
        response = await async_client.post(
            "/api/vocabulary/mark",
            headers=auth_headers,
            json=payload
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "Hallo"
        assert data["status"] == "known"
```

### Testing Authentication Flows

```python
@pytest.mark.asyncio
async def test_authentication_flow_registers_and_logs_in_user(
    async_client: AsyncClient
):
    """Test complete authentication flow: register → login → access protected resource"""
    # Step 1: Register new user
    register_payload = {
        "username": "testuser",
        "password": "SecurePass123!",
        "email": "test@example.com"
    }
    register_response = await async_client.post(
        "/api/auth/register",
        json=register_payload
    )
    assert register_response.status_code == 201

    # Step 2: Login with credentials
    login_payload = {
        "username": "testuser",
        "password": "SecurePass123!"
    }
    login_response = await async_client.post(
        "/api/auth/login",
        json=login_payload
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data

    # Step 3: Access protected resource with token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    profile_response = await async_client.get(
        "/api/profile",
        headers=headers
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["username"] == "testuser"
```

### Testing Error Responses

```python
@pytest.mark.asyncio
async def test_unauthorized_request_returns_401(async_client: AsyncClient):
    """Test that requests without authentication return 401"""
    response = await async_client.get("/api/vocabulary/words")

    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_invalid_request_body_returns_422(
    async_client: AsyncClient, auth_headers: dict
):
    """Test that invalid request body returns 422 Unprocessable Entity"""
    invalid_payload = {
        "word": "",  # Empty word should fail validation
        "status": "invalid_status"  # Invalid status
    }

    response = await async_client.post(
        "/api/vocabulary/mark",
        headers=auth_headers,
        json=invalid_payload
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["field"] == "word" for error in errors)
    assert any(error["field"] == "status" for error in errors)
```

---

## End-to-End Testing

### What to E2E Test

E2E tests verify **complete user workflows** from start to finish:

- ✅ Critical user journeys (registration → upload → processing → download)
- ✅ Multi-step workflows
- ✅ Real data persistence
- ✅ External integrations

### E2E Test Example

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_video_processing_workflow(async_client: AsyncClient):
    """
    E2E test for complete video processing workflow:
    1. User registers
    2. User logs in
    3. User uploads video
    4. System processes video (transcription + translation)
    5. User downloads processed subtitles
    """
    # Step 1: Register user
    register_response = await async_client.post(
        "/api/auth/register",
        json={"username": "e2e_user", "password": "Pass123!", "email": "e2e@test.com"}
    )
    assert register_response.status_code == 201

    # Step 2: Login
    login_response = await async_client.post(
        "/api/auth/login",
        json={"username": "e2e_user", "password": "Pass123!"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Upload video
    with open("tests/data/sample_video.mp4", "rb") as f:
        files = {"file": ("sample.mp4", f, "video/mp4")}
        upload_response = await async_client.post(
            "/api/videos/upload/test-series",
            headers=headers,
            files=files
        )
    assert upload_response.status_code == 200
    video_id = upload_response.json()["id"]

    # Step 4: Process video
    process_response = await async_client.post(
        f"/api/processing/start/{video_id}",
        headers=headers
    )
    assert process_response.status_code == 200
    processing_id = process_response.json()["processing_id"]

    # Wait for processing to complete (with timeout)
    import asyncio
    for _ in range(30):  # 30 seconds timeout
        status_response = await async_client.get(
            f"/api/processing/status/{processing_id}",
            headers=headers
        )
        if status_response.json()["status"] == "completed":
            break
        await asyncio.sleep(1)
    else:
        pytest.fail("Processing timeout")

    # Step 5: Download subtitles
    download_response = await async_client.get(
        f"/api/videos/{video_id}/subtitles",
        headers=headers
    )
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/x-subrip"
    assert len(download_response.content) > 0
```

### E2E Test Best Practices

1. **Use real data flows** - No mocking except for external APIs
2. **Keep E2E tests focused** - Test critical paths only
3. **Handle timing issues** - Use retries and reasonable timeouts
4. **Clean up after tests** - Remove test data created during E2E tests
5. **Run E2E tests separately** - Mark with `@pytest.mark.e2e` for selective execution

---

## Async Testing Patterns

### Async Test Functions

All async tests must be decorated with `@pytest.mark.asyncio`:

```python
import pytest


@pytest.mark.asyncio
async def test_async_function():
    """Test an async function"""
    result = await some_async_function()
    assert result is not None
```

### Using Async Client

Use `httpx.AsyncClient` for API testing:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_api_endpoint(async_client: AsyncClient):
    """Test API endpoint with async client"""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
```

### Testing Async Context Managers

```python
@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager"""
    async with AsyncSessionFactory() as session:
        result = await session.execute(query)
        assert result is not None
```

### Testing Concurrent Operations

```python
import asyncio
import pytest


@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test that multiple concurrent requests are handled correctly"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Execute multiple requests concurrently
        tasks = [
            client.get("/api/vocabulary/words"),
            client.get("/api/videos/list"),
            client.get("/api/profile"),
        ]
        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
```

---

## Fixtures & Test Data

### Fixture Scope

Choose appropriate scope for fixtures:

- **function** (default): New instance per test (most isolated)
- **class**: Shared within test class
- **module**: Shared across module
- **session**: Shared across entire test session (use sparingly)

```python
import pytest


@pytest.fixture(scope="function")
def user():
    """Create a new user for each test"""
    return User(id="test-123", username="testuser")


@pytest.fixture(scope="module")
def database():
    """Create database connection once per module"""
    db = create_test_database()
    yield db
    db.close()
```

### Fixture Dependencies

Fixtures can depend on other fixtures:

```python
@pytest.fixture
def auth_token(test_user):
    """Generate auth token for test user"""
    return generate_token(test_user.id)


@pytest.fixture
def auth_headers(auth_token):
    """Generate authentication headers"""
    return {"Authorization": f"Bearer {auth_token}"}
```

### Test Data Builders

Use factory functions for complex test data:

```python
# tests/helpers/data_builders.py

def build_vocabulary_word(word="Hallo", status="learning", **overrides):
    """Build a vocabulary word with sensible defaults"""
    data = {
        "word": word,
        "lemma": word.lower(),
        "status": status,
        "marked_at": "2025-10-03T10:00:00Z",
        "difficulty": "A1",
    }
    data.update(overrides)
    return data


def build_user(username="testuser", **overrides):
    """Build a user with sensible defaults"""
    data = {
        "id": f"user-{uuid.uuid4()}",
        "username": username,
        "email": f"{username}@test.com",
        "created_at": "2025-10-03T10:00:00Z",
    }
    data.update(overrides)
    return data
```

### Using Faker for Realistic Data

```python
from faker import Faker

fake = Faker()


@pytest.fixture
def random_user():
    """Generate a user with random but realistic data"""
    return {
        "username": fake.user_name(),
        "email": fake.email(),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
    }
```

---

## Mocking & Stubbing

### When to Mock

✅ **DO mock**:

- External APIs (OpenAI, translation services)
- Slow operations (AI model inference)
- File system operations (in unit tests)
- Time-dependent functions (`datetime.now()`)
- Random number generation

❌ **DON'T mock**:

- Your own business logic
- Database operations (use transactions instead)
- Simple functions
- FastAPI dependencies (use test overrides instead)

### Mocking with unittest.mock

```python
from unittest.mock import Mock, patch, AsyncMock


def test_service_calls_external_api(monkeypatch):
    """Test service with mocked external API"""
    # Create mock
    mock_api = Mock()
    mock_api.translate.return_value = "Translated text"

    # Inject mock
    monkeypatch.setattr("services.translation_service.api_client", mock_api)

    # Test
    service = TranslationService()
    result = service.translate("Original text", "en", "de")

    # Verify
    assert result == "Translated text"
    mock_api.translate.assert_called_once_with("Original text", "en", "de")
```

### Mocking Async Functions

```python
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_async_service_call(monkeypatch):
    """Test async service with mocked async call"""
    # Create async mock
    mock_repository = AsyncMock()
    mock_repository.get_user.return_value = {"id": "123", "name": "Test User"}

    # Inject mock
    service = UserService(repository=mock_repository)

    # Test
    user = await service.get_user("123")

    # Verify
    assert user["name"] == "Test User"
    mock_repository.get_user.assert_called_once_with("123")
```

### Patching Context Managers

```python
def test_file_operations_with_mocked_open(monkeypatch):
    """Test file operations with mocked open()"""
    from unittest.mock import mock_open

    mock_file = mock_open(read_data="file contents")
    monkeypatch.setattr("builtins.open", mock_file)

    # Test code that reads files
    service = FileService()
    content = service.read_config("/path/to/config.json")

    assert content == "file contents"
    mock_file.assert_called_once_with("/path/to/config.json", encoding="utf-8")
```

---

## Common Patterns

### Parametrized Tests

Test multiple scenarios with same test logic:

```python
import pytest


@pytest.mark.parametrize("password,expected_valid", [
    ("SecurePass123!", True),
    ("short", False),
    ("NoNumbers!", False),
    ("nouppercaseornumbers", False),
    ("NOLOWERCASE123", False),
])
def test_password_validation(password, expected_valid):
    """Test password validation with various inputs"""
    validator = PasswordValidator()
    is_valid = validator.validate(password)
    assert is_valid == expected_valid
```

### Testing Exception Messages

```python
def test_invalid_input_raises_descriptive_error():
    """Test that invalid input raises error with helpful message"""
    service = VocabularyService()

    with pytest.raises(ValueError) as exc_info:
        service.add_word(user_id="", word="test")

    assert "user_id cannot be empty" in str(exc_info.value)
```

### Testing Database Transactions

```python
@pytest.mark.asyncio
async def test_transaction_rollback_on_error(db_session):
    """Test that transaction rolls back on error"""
    # Start with clean state
    initial_count = await db_session.scalar(select(func.count()).select_from(User))

    # Attempt operation that will fail
    try:
        user = User(username="testuser")
        db_session.add(user)
        await db_session.flush()

        # Simulate error after partial work
        raise ValueError("Simulated error")
    except ValueError:
        await db_session.rollback()

    # Verify no data was persisted
    final_count = await db_session.scalar(select(func.count()).select_from(User))
    assert final_count == initial_count
```

---

## Anti-Patterns to Avoid

### ❌ Testing Implementation Details

```python
# ❌ BAD - Testing internal method calls
def test_service_calls_internal_method():
    service = VocabularyService()
    with patch.object(service, '_internal_helper') as mock_helper:
        service.add_word("user-id", "word")
        mock_helper.assert_called_once()  # Don't test this!


# ✅ GOOD - Testing behavior
def test_service_adds_word_to_database():
    service = VocabularyService()
    result = service.add_word("user-id", "word")
    assert result.word == "word"  # Test the outcome
```

### ❌ Sharing State Between Tests

```python
# ❌ BAD - Shared mutable state
class TestVocabularyService:
    words = []  # Shared across all tests!

    def test_add_word(self):
        self.words.append("Hallo")
        assert len(self.words) == 1

    def test_remove_word(self):
        # Will fail if test_add_word ran first!
        assert len(self.words) == 0


# ✅ GOOD - Isolated state
class TestVocabularyService:
    def test_add_word(self):
        words = []  # Fresh state
        words.append("Hallo")
        assert len(self.words) == 1

    def test_remove_word(self):
        words = []  # Fresh state
        assert len(self.words) == 0
```

### ❌ Over-Mocking

```python
# ❌ BAD - Mocking everything makes test meaningless
def test_service_with_too_many_mocks():
    mock_repo = Mock()
    mock_validator = Mock()
    mock_logger = Mock()
    mock_cache = Mock()

    service = Service(mock_repo, mock_validator, mock_logger, mock_cache)
    # Test tells us nothing about actual behavior


# ✅ GOOD - Mock only external dependencies
def test_service_with_real_logic():
    mock_api = Mock()  # Only mock external API
    service = Service(api_client=mock_api)
    result = service.process_data({"key": "value"})  # Real logic runs
    assert result.is_valid
```

### ❌ Vague Test Names

```python
# ❌ BAD
def test_1():
    pass

def test_user():
    pass

def test_something():
    pass


# ✅ GOOD
def test_user_registration_with_valid_data_creates_new_user():
    pass

def test_invalid_email_format_raises_validation_error():
    pass

def test_duplicate_username_returns_409_conflict():
    pass
```

### ❌ Testing Multiple Things in One Test

```python
# ❌ BAD - Test does too much
def test_complete_user_flow():
    user = create_user()
    assert user.id is not None

    updated_user = update_user(user.id, {"email": "new@test.com"})
    assert updated_user.email == "new@test.com"

    delete_user(user.id)
    assert get_user(user.id) is None
    # If any assertion fails, we don't know which part broke


# ✅ GOOD - Separate tests for each behavior
def test_create_user_generates_id():
    user = create_user()
    assert user.id is not None

def test_update_user_email_changes_email():
    user = create_user()
    updated = update_user(user.id, {"email": "new@test.com"})
    assert updated.email == "new@test.com"

def test_delete_user_removes_from_database():
    user = create_user()
    delete_user(user.id)
    assert get_user(user.id) is None
```

---

## Test Quality Checklist

Before submitting a test, verify:

### Functionality

- [ ] Test has a clear, descriptive name
- [ ] Test verifies behavior, not implementation
- [ ] Test is focused on one scenario
- [ ] Test uses Arrange-Act-Assert structure
- [ ] Expected outcomes are clearly asserted

### Independence

- [ ] Test does not depend on other tests
- [ ] Test does not share mutable state
- [ ] Test cleans up after itself
- [ ] Test can run in any order

### Maintainability

- [ ] Test uses fixtures appropriately
- [ ] Test avoids duplication (DRY principle)
- [ ] Test has docstring explaining what it verifies
- [ ] Test is easy to understand

### Performance

- [ ] Unit test runs in < 100ms
- [ ] Integration test runs in < 1s
- [ ] Test does not sleep unnecessarily
- [ ] Test uses appropriate mocking

### Coverage

- [ ] Test covers happy path
- [ ] Test covers error cases
- [ ] Test covers edge cases
- [ ] Test validates error messages

---

## Quick Reference

### Essential Test Decorators

```python
@pytest.mark.asyncio              # Mark async test
@pytest.mark.parametrize          # Run test with multiple inputs
@pytest.mark.skip                 # Skip test temporarily
@pytest.mark.skipif               # Conditional skip
@pytest.mark.xfail                # Expected to fail
@pytest.fixture                   # Define fixture
@pytest.fixture(scope="module")   # Fixture with custom scope
```

### Common Assertions

```python
assert value == expected
assert value is not None
assert value in collection
assert isinstance(value, Type)
assert len(collection) == 3

with pytest.raises(ValueError):
    function_that_should_raise()

with pytest.raises(ValueError, match="error message"):
    function_that_should_raise()
```

### Running Specific Tests

```bash
# Run single file
pytest tests/unit/test_service.py

# Run single test
pytest tests/unit/test_service.py::test_function_name

# Run tests matching pattern
pytest -k "auth"

# Run tests with marker
pytest -m "asyncio"

# Run in parallel
pytest -n auto

# Show print statements
pytest -s

# Stop on first failure
pytest -x
```

---

## Additional Resources

- **Test Report**: [TEST_REPORT.md](TEST_REPORT.md) - Current test suite status
- **Project Standards**: [CLAUDE.md](../CLAUDE.md) - Overall development guidelines
- **Pytest Documentation**: https://docs.pytest.org/
- **Async Testing**: https://pytest-asyncio.readthedocs.io/

---

**Document Version**: 1.0
**Last Updated**: 2025-10-03
**Next Review**: 2025-11-03
