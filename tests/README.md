# Test Infrastructure

## Overview

This test infrastructure has been completely rebuilt to eliminate anti-patterns and provide reliable, behavior-focused testing. The new system emphasizes business outcomes over implementation details.

## Anti-Patterns Eliminated

### ❌ What Was Removed

- **DOM Element Counting**: Tests that pass by counting elements containing words like "vocab"
- **Status Code Tolerance**: Tests accepting multiple HTTP status codes (e.g., `status in [200, 500]`)
- **Array Index Selectors**: Brittle selectors like `elements[0].click()`
- **Print-and-Exit Scripts**: Scripts that print results and exit(0) without real assertions
- **Hard-coded URLs**: Mixed usage of localhost:3000, localhost:3001, 127.0.0.1:8000
- **Mock Call Verification**: Testing internal implementation instead of business outcomes

### ✅ What Was Added

- **Semantic Selectors**: Using `data-testid`, semantic CSS selectors, and role-based queries
- **Behavior Assertions**: Verifying actual business outcomes and user workflows
- **Isolated Test Sessions**: Proper test data management with automatic cleanup
- **Cross-Platform Support**: Unified path handling and environment detection
- **Structured Reporting**: JUnit XML, JSON, and console reports with detailed failure information

## Test Structure

```
tests/
├── shared/                          # Shared test infrastructure
│   ├── config/
│   │   └── test-environment.ts      # Cross-platform environment detection
│   ├── fixtures/
│   │   └── test-fixtures.ts         # Test data management and cleanup
│   └── assertions/
│       └── behavior-assertions.ts   # Semantic assertion library
├── integration/
│   └── frontend-behavior-tests.test.ts  # Frontend integration tests
├── e2e/
│   └── workflow-tests.test.ts       # End-to-end workflow tests
└── run-all-tests.ts                # Unified test orchestrator
```

## Running Tests

### Quick Start

```bash
# Run all tests
npm run test:all

# Or with Node.js/ts-node
npx ts-node tests/run-all-tests.ts
```

### Specific Test Suites

```bash
# Backend tests only
npm run test:backend
python Backend/tests/run_backend_tests.py

# Frontend integration tests
npm run test:frontend

# E2E tests only
npm run test:e2e
npx ts-node tests/run-all-tests.ts --skip-backend --skip-frontend
```

### Options

```bash
# With coverage
npx ts-node tests/run-all-tests.ts --coverage

# Verbose output
npx ts-node tests/run-all-tests.ts --verbose

# Sequential execution (for debugging)
npx ts-node tests/run-all-tests.ts --sequential

# Skip specific suites
npx ts-node tests/run-all-tests.ts --skip-e2e

# Generate JUnit report
npx ts-node tests/run-all-tests.ts --junit

# Timeout configuration
npx ts-node tests/run-all-tests.ts --timeout=60
```

## Writing Good Tests

### ✅ Do This

```typescript
// Use semantic selectors
await page.click('[data-testid="login-button"]');

// Assert specific outcomes
expect(response.status).toBe(200);
assert(response.data.access_token.length > 50);

// Verify business workflows
const authResult = await WorkflowAssertions.assertAuthenticationWorkflow(
  page,
  credentials,
  "/dashboard",
);
assertResult(authResult, "login-workflow");

// Use isolated test sessions
await withTestSession("test-name", async (session) => {
  // Test logic with automatic cleanup
});
```

### ❌ Don't Do This

```typescript
// DOM element counting (NEVER)
const elements = await page.$$(".vocab-word");
expect(elements.length).toBeGreaterThan(0); // ❌

// Status code tolerance (NEVER)
expect([200, 500]).toContain(response.status); // ❌

// Array index selectors (NEVER)
await page.click("button:nth-child(1)"); // ❌

// Mock call counting (NEVER)
expect(mockFn).toHaveBeenCalledTimes(3); // ❌
```

## Test Categories

### Unit Tests (Backend)

**Location**: `Backend/tests/unit/`
**Purpose**: Test individual components in isolation
**Technology**: pytest with proper fixtures

```python
def test_register_request_valid_data_passes():
    """Test that valid registration data passes validation"""
    request = RegisterRequest(username="test", email="test@example.com", password="Valid123!")
    assert request.username == "test"
```

### API Tests (Backend)

**Location**: `Backend/tests/api/`
**Purpose**: Test API endpoints with real HTTP requests
**Technology**: pytest + httpx

```python
async def test_login_with_email_succeeds(test_user_credentials):
    """Test login with email returns valid access token"""
    response = await client.post("/api/auth/login", data=form_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Integration Tests (Frontend)

**Location**: `tests/integration/`
**Purpose**: Test React components with backend integration
**Technology**: Puppeteer + Jest with semantic selectors

```typescript
it("should complete full registration workflow", async () => {
  await withTestSession("registration", async (session) => {
    const formExists = await DomAssertions.assertElementExists(
      page,
      '[data-testid="registration-form"]',
    );
    assertResult(formExists, "registration-form-presence");
  });
});
```

### E2E Tests (Full Workflows)

**Location**: `tests/e2e/`
**Purpose**: Test complete user workflows across the entire application
**Technology**: Playwright with behavior assertions

```typescript
test("complete user registration and login flow", async ({ page }) => {
  await withTestSession("e2e-auth-flow", async (session) => {
    await page.fill('[data-testid="email-input"]', session.user.email);
    await page.click('[data-testid="register-button"]');
    await expect(page).toHaveURL(/\/(dashboard|videos)/);
  });
});
```

## Environment Configuration

The test infrastructure automatically detects:

- **Frontend URL**: Checks ports 3000, 3001 or uses environment variables
- **Backend URL**: Checks ports 8000, 8001 or uses environment variables
- **Platform**: Windows, Linux, macOS with appropriate command handling
- **CI Environment**: GitHub Actions, other CI systems

### Environment Variables

```bash
# Override server URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Test configuration
TEST_HEADLESS=true
TEST_TIMEOUT=30000
TEST_SLOWMO=0

# CI configuration
CI=true
GITHUB_ACTIONS=true
```

## Test Data Management

### Test Sessions

All tests use isolated test sessions with automatic cleanup:

```typescript
// Creates unique user, videos, vocabulary for this test
await withTestSession("test-name", async (session) => {
  // session.user - unique test user
  // session.videos - test video files
  // session.vocabulary - test vocabulary data
  // Automatic cleanup after test
});

// For authenticated tests
await withAuthenticatedUser("test-name", async (session, user) => {
  // user.accessToken - valid auth token
  // Automatic user cleanup
});
```

### Test Fixtures

The fixture system provides:

- **User Management**: Create/cleanup test users with valid credentials
- **Data Seeding**: Add test videos, vocabulary, and other data
- **Token Management**: Handle authentication tokens
- **File Management**: Temporary file creation and cleanup
- **API Integration**: Interact with backend APIs for setup/teardown

## Reporting

### Console Output

```
=====================================
TEST ORCHESTRATION SUMMARY
=====================================
Total Test Suites: 3
Passed: 3
Failed: 0
Skipped: 0

SUITE DETAILS:
  ✓ backend    |  12.45s | Backend tests completed successfully
  ✓ frontend   |   8.23s | Frontend tests completed successfully
  ✓ e2e        |  45.67s | E2E tests completed successfully

OVERALL STATUS: PASSED (66.35s)
```

### JUnit XML

```bash
npx ts-node tests/run-all-tests.ts --junit
# Generates: test-results-all.xml
```

### JSON Reports

```bash
npx ts-node tests/run-all-tests.ts --json
# Generates: test-results-all.json, test-summary.json
```

## CI Integration

### GitHub Actions

```yaml
- name: Run All Tests
  run: npx ts-node tests/run-all-tests.ts --junit --coverage

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-results
    path: |
      test-results-*.xml
      test-results-*.json
      coverage/
```

## Troubleshooting

### Common Issues

**Tests fail with "Element not found"**

- Check that `data-testid` attributes exist in components
- Verify selectors match actual DOM structure
- Use browser dev tools to inspect elements

**API tests fail with connection errors**

- Ensure backend server is running
- Check environment variables for correct URLs
- Verify firewall/network settings

**E2E tests timeout**

- Increase timeout with `--timeout=60`
- Check if frontend/backend servers are responding
- Run with `--verbose` for detailed logs

### Debug Mode

```bash
# Run specific test with full output
npx ts-node tests/run-all-tests.ts --verbose --skip-e2e --skip-frontend

# Run single backend test module
python -m pytest Backend/tests/api/test_auth_login_workflow.py -v

# Run frontend tests in watch mode
cd Frontend && npm test -- --watch
```

### Test Development

**Adding New Tests**

1. Use semantic selectors (`data-testid` preferred)
2. Test business outcomes, not implementation
3. Use test sessions for proper isolation
4. Follow assertion patterns from existing tests
5. Add appropriate cleanup

**Semantic Selector Guidelines**

```html
<!-- Good: Semantic, stable selectors -->
<button data-testid="login-button">Sign In</button>
<input data-testid="email-input" type="email" />
<div data-testid="error-message" class="error">Error text</div>

<!-- Avoid: Implementation-dependent selectors -->
<button class="btn btn-primary">Sign In</button>
<!-- Styling classes -->
<input id="input_1234" />
<!-- Generated IDs -->
<div>Error text</div>
<!-- No semantic meaning -->
```

## Migration Notes

### From Old Test System

The old test files have been removed:

- `tests/integration/frontend-integration.test.ts` → `tests/integration/frontend-behavior-tests.test.ts`
- `tests/e2e/simple-*.ts` → `tests/e2e/workflow-tests.test.ts`
- `Backend/test_login.py` → `Backend/tests/api/test_auth_login_workflow.py`
- `Backend/test_coverage_validation.py` → `Backend/tests/unit/test_validation_comprehensive.py`

### Key Changes

- All tests now use semantic selectors
- No more DOM element counting or status code tolerance
- Proper test isolation with fixtures
- Structured reporting with JUnit/JSON output
- Cross-platform compatibility
- Unified test orchestration

The new system ensures every test fails meaningfully when the feature it tests is broken, and passes only when the feature works correctly.
