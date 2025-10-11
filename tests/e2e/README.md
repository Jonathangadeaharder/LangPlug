# E2E Test Suite

End-to-end testing for LangPlug using Playwright. Tests verify critical user workflows across the full stack (frontend + backend).

## Test Coverage

**16 tests across 5 workflow suites (100% passing):**

### Authentication Workflow (3 tests)
- User registration and authentication
- Logout and access control
- Invalid credentials handling

### Vocabulary Learning Workflow (3 tests)
- Library access and statistics display
- Custom vocabulary addition
- Filtering by difficulty level

### Video Processing Workflow (4 tests)
- Video listing via API
- Processing status checking
- Video scanning
- Health checks

### Complete Learning Workflow (2 tests)
- Multi-API integration (videos, vocabulary, scan)
- Vocabulary creation and backend health

### User Profile Workflow (4 tests)
- Profile access and viewing
- Language preference support
- Progress statistics data
- Password change workflow

## Prerequisites

### Required Services
1. **Backend API** running on `http://localhost:8000`
2. **Frontend dev server** running on `http://localhost:5173`
3. **PostgreSQL** database configured and accessible

### Environment Setup
```bash
# From project root
cd tests/e2e
npm install  # Install Playwright dependencies

# Install browsers (first time only)
npx playwright install chromium
```

## Running Tests

### All E2E Tests
```bash
# Set environment variable and run tests
$env:E2E_SMOKE_TESTS='1'; npx playwright test

# Or using helper script (Windows)
./run-test.bat
```

### Specific Test Suite
```bash
$env:E2E_SMOKE_TESTS='1'; npx playwright test workflows/authentication.workflow.test.ts
$env:E2E_SMOKE_TESTS='1'; npx playwright test workflows/vocabulary-learning.workflow.test.ts
$env:E2E_SMOKE_TESTS='1'; npx playwright test workflows/video-processing.workflow.test.ts
$env:E2E_SMOKE_TESTS='1'; npx playwright test workflows/complete-learning.workflow.test.ts
$env:E2E_SMOKE_TESTS='1'; npx playwright test workflows/user-profile.workflow.test.ts
```

### Single Test
```bash
$env:E2E_SMOKE_TESTS='1'; npx playwright test --grep "WhenUserRegistersAndLogs"
```

### Debug Mode
```bash
$env:E2E_SMOKE_TESTS='1'; npx playwright test --debug
$env:E2E_SMOKE_TESTS='1'; npx playwright test --headed  # See browser
```

### View Test Reports
```bash
npx playwright show-report
```

## Test Structure

```
tests/e2e/
├── workflows/                    # Test suites organized by user workflow
│   ├── authentication.workflow.test.ts
│   ├── vocabulary-learning.workflow.test.ts
│   ├── video-processing.workflow.test.ts
│   ├── complete-learning.workflow.test.ts
│   └── user-profile.workflow.test.ts
├── utils/                        # Test utilities
│   ├── test-data-manager.ts     # Test data creation/cleanup
│   ├── test-environment-manager.ts  # Environment validation
│   └── test-helpers.ts          # Shared test helpers
├── playwright.config.ts          # Playwright configuration
├── package.json                  # Dependencies
├── run-test.bat                  # Helper script
├── cleanup-playwright.bat        # Process cleanup
└── README.md                     # This file
```

## Test Data Management

### TestDataManager
Handles creation and cleanup of test data via backend API:

```typescript
const testDataManager = new TestDataManager();

// Create test user with auth token
const testUser = await testDataManager.createTestUser();
// Returns: { username, email, password, token }

// Create test vocabulary
const vocab = await testDataManager.createTestVocabulary(testUser, {
  word: 'TestWord',
  translation: 'Test translation',
  difficulty_level: 'beginner'  // Maps to A1
});

// Cleanup after test
await testDataManager.cleanupTestData(testUser);
```

### Test Isolation
- Each test creates its own user with unique timestamp
- Test data is cleaned up in `afterEach` hooks
- No shared state between tests
- Tests run sequentially (workers=1) for stability

## Configuration

### Environment Variables
```bash
# Required for @smoke tagged tests
E2E_SMOKE_TESTS=1
```

### Playwright Config (`playwright.config.ts`)
- **Base URL**: `http://localhost:5173` (frontend)
- **Timeout**: 30s per test
- **Retries**: 2 (reduces flaky test failures)
- **Workers**: 1 (sequential execution for stability)
- **Browsers**: Chromium only (fastest, most stable)
- **Artifacts**: Screenshots/videos on failure

## Writing New Tests

### Test Naming Convention
```typescript
test('WhenX_ThenY @smoke', async ({ page }) => {
  // Arrange, Act, Assert pattern with explicit test.step blocks
});
```

### Best Practices

#### 1. Use test.step() for Clear Test Phases
```typescript
await test.step('Login user', async () => {
  await page.goto('/login');
  await page.locator('input[type="email"]').fill(testUser.email);
  await page.locator('input[type="password"]').fill(testUser.password);
  await page.locator('button[type="submit"]').click();
});
```

#### 2. Flexible Selectors with Fallbacks
```typescript
// Primary selector with fallback
const loginButton = page.locator('[data-testid="login-button"]').or(
  page.getByRole('button', { name: /login|sign in/i })
);
await loginButton.click();
```

#### 3. Explicit Waits for Form Hydration
```typescript
// Wait for form to be ready
await page.waitForLoadState('networkidle');

// Wait for element with timeout
const input = page.locator('[data-testid="username-input"]');
await input.waitFor({ state: 'visible', timeout: 3000 });
await input.fill(username);
```

#### 4. Descriptive Error Messages
```typescript
if (!response.ok()) {
  const body = await response.text();
  throw new Error(`API failed with status ${response.status()}: ${body}`);
}
```

#### 5. Test Backend APIs When UI Missing
```typescript
// UI not implemented yet - test backend API
const response = await page.request.get('http://localhost:8000/api/profile', {
  headers: { Authorization: `Bearer ${testUser.token}` }
});
expect(response.ok()).toBeTruthy();
```

### Example Test
```typescript
test('WhenUserDoesX_ThenSystemDoesY @smoke', async ({ page }) => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;

  test.beforeEach(async () => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();
    // Login...
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  await test.step('Action phase', async () => {
    const button = page.getByRole('button', { name: /submit/i });
    await button.click();
  });

  await test.step('Verification phase', async () => {
    await expect(page.locator('[data-testid="success"]')).toBeVisible();
  });
});
```

## Troubleshooting

### Tests Hang Silently
**Symptoms**: Tests start but produce no output

**Solutions**:
- Check TypeScript compilation: `npx tsc --noEmit`
- Ensure `E2E_SMOKE_TESTS=1` is set
- Verify backend/frontend are running
- Check for orphaned Node processes: `./cleanup-playwright.bat`

### "User Menu Not Found" / Timeout Errors
**Symptoms**: Elements not found that should exist

**Solutions**:
- Add `await page.waitForLoadState('networkidle')` after navigation
- Add explicit timeout: `waitFor({ state: 'visible', timeout: 5000 })`
- Check if form needs hydration time
- Verify element actually exists in current UI state

### Authentication Failures
**Symptoms**: Login fails or returns 401/403

**Solutions**:
- Check backend is running on port 8000
- Verify database is accessible
- Check backend logs for errors
- Verify test user was created successfully

### Flaky Tests (Pass Sometimes, Fail Other Times)
**Symptoms**: Tests pass on retry but fail on first run

**Solutions**:
- Add `waitForLoadState('networkidle')` after form appears
- Use explicit timeouts on all `isVisible()` checks
- Replace `isVisible()` with `waitFor({ state: 'visible', timeout: 3000 })`
- Avoid array indices, use semantic selectors
- Add `await page.waitForTimeout(500)` as last resort

### "Endpoint not found in API contract"
**Symptoms**: API returns 404 with contract validation error

**Solutions**:
- Check if endpoint path is correct
- Verify endpoint is registered in app.py
- Check if middleware is rejecting the endpoint
- Try different query parameters or HTTP method

### Cleanup Orphaned Processes
**Symptoms**: Multiple Node/Chrome processes running

**Solutions**:
```bash
# Windows
./cleanup-playwright.bat

# Or manually
taskkill /F /IM node.exe
taskkill /F /IM chrome.exe
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        working-directory: tests/e2e
        run: npm install

      - name: Install Playwright browsers
        working-directory: tests/e2e
        run: npx playwright install chromium

      - name: Start services
        run: ./scripts/start-all.bat
        shell: cmd

      - name: Wait for services
        run: timeout 30
        shell: cmd

      - name: Run E2E tests
        working-directory: tests/e2e
        run: npx playwright test
        env:
          E2E_SMOKE_TESTS: 1

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/
```

## Performance

- **Average test time**: 3-5 seconds per test
- **Full suite**: ~2 minutes (16 tests sequential)
- **Retry overhead**: +30-60s if flaky tests retry

## Maintenance

### Adding New Test Suites
When adding new features:
1. Create new `workflow-name.workflow.test.ts` file
2. Follow naming convention: `WhenX_ThenY @smoke`
3. Add test data helpers to `TestDataManager` if needed
4. Update this README with new test count
5. Run full suite to verify no regressions

### Updating Selectors
When UI changes:
1. Add `data-testid` attributes to new components
2. Update primary selectors in tests
3. Keep fallback selectors for robustness
4. Run affected tests to verify

### Test Failures in CI
1. Check GitHub Actions artifacts for screenshots/videos
2. Check backend logs in CI output
3. Run locally with same environment
4. Add debug logging if needed

## Anti-Patterns Eliminated

### ❌ What We Avoid
- **Array Index Selectors**: No `buttons[0]` or `elements[1]`
- **DOM Element Counting**: No testing number of elements as primary assertion
- **Status Code Tolerance**: No accepting multiple status codes (e.g., `status in {200, 500}`)
- **Hard-coded Paths**: No Windows-specific or absolute paths
- **Implementation Coupling**: No testing CSS colors or computed styles
- **Silent Failures**: No bare try/catch that swallows errors

### ✅ What We Use
- **Semantic Selectors**: `data-testid`, role queries, type attributes
- **Business Outcome Verification**: Test actual user workflows
- **Explicit Error Handling**: Descriptive errors with status codes
- **Flexible Selectors**: Multiple fallback strategies
- **Proper Test Isolation**: Independent test data and cleanup
- **Explicit Waits**: No arbitrary timeouts, wait for specific conditions

## Future Improvements

- [ ] Add visual regression testing
- [ ] Parallel execution (increase workers once stable)
- [ ] Cross-browser testing (Firefox, WebKit)
- [ ] API contract testing with OpenAPI validation
- [ ] Performance benchmarking tests
- [ ] Accessibility testing with axe-core
- [ ] Mobile viewport testing
- [ ] Network condition simulation
