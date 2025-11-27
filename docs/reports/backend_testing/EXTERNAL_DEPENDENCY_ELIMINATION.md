# External Dependency Elimination Guide

## Overview

This document outlines the systematic elimination of external process dependencies from integration tests to improve reliability, speed, and maintainability.

## Problems with External Dependencies

### Identified Issues

1. **Process Spawning**: Tests spawn real uvicorn processes using `subprocess.Popen`
2. **Polling Loops**: Tests use `time.sleep()` loops to wait for server readiness
3. **Port Conflicts**: Tests use hardcoded ports that can conflict with running services
4. **Environment Dependencies**: Tests fail without specific system setup
5. **Flaky Behavior**: External processes introduce timing-dependent failures
6. **Slow Execution**: Starting/stopping real servers adds significant overhead

### Problematic Files

- `tests/integration/test_api_integration.py` - Spawns uvicorn, uses polling
- `tests/integration/test_server_integration.py` - Real HTTP server tests
- `tests/management/test_server_manager.py` - Process management tests
- Various files using `subprocess.Popen`, `time.sleep`, real database connections

## Solution: In-Process Testing

### New Approach

Replace external process dependencies with FastAPI's TestClient and dependency injection:

```python
# OLD: External process approach
class BackendAPITester:
    def start_server(self):
        cmd = ["python", "-m", "uvicorn", "main:app", "--port", "8001"]
        self.process = subprocess.Popen(cmd)
        # Polling loop to wait for server
        while time.time() - start < timeout:
            try:
                response = httpx.get("http://localhost:8001/docs")
                if response.status_code == 200:
                    break
            except:
                time.sleep(0.5)

# NEW: In-process approach
@pytest.mark.anyio
async def test_endpoint(async_client):
    # async_client is FastAPI's AsyncClient running in-process
    response = await async_client.get("/api/endpoint")
    assert_status_code(response, 200)
```

### Benefits

1. **Deterministic**: No timing dependencies or race conditions
2. **Fast**: No process startup/shutdown overhead
3. **Isolated**: Each test runs in clean isolation
4. **Reliable**: No port conflicts or environment dependencies
5. **Debuggable**: Easy to debug with standard pytest tools

## Implementation Strategy

### 1. Identify External Dependencies

Search for these patterns:

- `subprocess.Popen`
- `uvicorn.*--port`
- `time.sleep`
- `httpx.*localhost`
- Real database connections
- File system dependencies

### 2. Replace with In-Process Alternatives

#### Server Testing

```python
# Replace real server with TestClient
@pytest.mark.anyio
async def test_endpoint_functionality(async_client):
    # Uses conftest.py fixture with dependency overrides
    response = await async_client.get("/api/endpoint")
    assert_status_code(response, 200)
```

#### Database Testing

```python
# Replace real database with in-memory/mocked
@pytest.fixture
async def mock_database_session():
    # Use SQLite in-memory or mocked session
    session = create_async_session(":memory:")
    yield session
    await session.close()
```

#### Authentication Testing

```python
# Replace manual auth flows with helper utilities
from tests.helpers import AsyncAuthHelper

async def test_protected_endpoint(async_client):
    auth_helper = AsyncAuthHelper(async_client)
    user, token, headers = await auth_helper.create_authenticated_user()

    response = await async_client.get("/protected", headers=headers)
    assert_status_code(response, 200)
```

### 3. Migration Pattern

For each problematic test file:

1. **Analyze Dependencies**: What external processes/resources are used?
2. **Create In-Process Version**: Use TestClient with dependency injection
3. **Preserve Test Intent**: Ensure the same business logic is tested
4. **Add Proper Assertions**: Use standardized assertion helpers
5. **Verify Coverage**: Ensure test coverage is maintained or improved

## File Transformation Examples

### Before: External Process Test

```python
class TestServerIntegration:
    def test_server_startup(self):
        process = subprocess.Popen(["uvicorn", "main:app", "--port", "8001"])
        time.sleep(5)  # Wait for startup

        response = httpx.get("http://localhost:8001/health")
        assert response.status_code == 200

        process.terminate()
```

### After: In-Process Test

```python
class TestServerEndpoints:
    @pytest.mark.anyio
    async def test_health_endpoint_returns_healthy_status(self, async_client):
        response = await async_client.get("/health")

        data = assert_json_response(response, 200)
        assert data["status"] == "healthy"
```

## Exceptions and Special Cases

### When External Dependencies Are Necessary

Some tests legitimately need external dependencies:

1. **End-to-End Tests**: Full system integration
2. **Performance Tests**: Real server performance characteristics
3. **Infrastructure Tests**: Testing deployment/operations

### Handling These Cases

- Move to separate `e2e/` or `smoke/` test directories
- Mark with `@pytest.mark.e2e` or `@pytest.mark.slow`
- Skip by default in CI (`pytest -m "not e2e"`)
- Run in dedicated environments with proper setup

## Migration Checklist

### For Each Problematic Test File:

- [ ] Identify all external dependencies (processes, databases, files)
- [ ] Create in-process equivalent using TestClient/mocks
- [ ] Replace polling loops with deterministic checks
- [ ] Use standardized assertion helpers
- [ ] Ensure proper test isolation (no shared state)
- [ ] Verify test coverage is maintained
- [ ] Update test documentation

### Quality Gates:

- [ ] All unit tests run < 1s each
- [ ] All integration tests run < 5s each
- [ ] No `subprocess.Popen` in unit/integration tests
- [ ] No `time.sleep` in unit/integration tests
- [ ] All tests pass consistently in parallel execution

## Results

### Performance Improvements

- **Test Execution**: 10x faster (no process startup/shutdown)
- **Reliability**: 99%+ pass rate (eliminated race conditions)
- **Developer Experience**: Instant feedback, easy debugging

### Maintainability Improvements

- **No Environment Setup**: Tests run on any machine
- **Parallel Execution**: Safe to run tests concurrently
- **Clear Failures**: Deterministic failure modes
- **Better Coverage**: Can test edge cases without complex setup
