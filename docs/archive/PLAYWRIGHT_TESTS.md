# LangPlug Playwright End-to-End Tests

Comprehensive E2E test suite for LangPlug using Playwright, with Chrome DevTools MCP validation.

## Overview

This test suite covers:
- **Authentication**: Registration, login, logout, session management
- **Vocabulary**: Mark/unmark words, search, pagination, level navigation
- **Navigation**: Page navigation, URL routing, state persistence
- **Total Test Cases**: 50+ comprehensive tests

## Setup

### Prerequisites
```bash
npm install -D @playwright/test
```

### Configuration
Tests are configured in `playwright.config.ts` with:
- Auto-starting servers (Frontend + Backend)
- Chrome & Firefox browser testing
- Screenshots and videos on failure
- HTML report generation

## Running Tests

### Run all tests
```bash
npx playwright test
```

### Run specific test file
```bash
npx playwright test tests/e2e/auth.spec.ts
```

### Run tests in headed mode (see browser)
```bash
npx playwright test --headed
```

### Run tests in debug mode (step through)
```bash
npx playwright test --debug
```

### Run single test
```bash
npx playwright test -g "should register with valid credentials"
```

### Run specific browser only
```bash
npx playwright test --project=chromium
```

## Test Structure

### Authentication Tests (`auth.spec.ts`)
- **Registration**
  - Valid credentials
  - Invalid password (no special char)
  - Password too short
  - Empty fields validation

- **Login**
  - Valid credentials
  - Wrong password
  - Non-existent email
  - Session persistence

- **Logout**
  - Clear session
  - Redirect to login
  - Success message

- **Session Management**
  - Preserve user info on refresh

### Vocabulary Tests (`vocabulary.spec.ts`)
- **Library Display**
  - Word count accuracy
  - All levels display
  - Pagination controls

- **Mark Words as Known**
  - Single word marking
  - Multiple words
  - Mark all functionality
  - Real-time stats update

- **Unmark Words**
  - Unmark by clicking again
  - Unmark all
  - Remove via × button

- **Search**
  - Exact word search
  - Partial matches
  - Clear search
  - No results handling

- **Level Navigation**
  - Switch between levels
  - Preserve word knowledge
  - Word count accuracy

- **Pagination**
  - Next/previous navigation
  - Words per page (100)
  - Total pages (8 for A1)

- **Statistics**
  - Progress percentage
  - Total words tracked
  - Per-level tracking

### Navigation Tests (`navigation.spec.ts`)
- **Main Navigation**
  - Videos ↔ Vocabulary
  - Header buttons
  - User profile display
  - Logout button

- **URL Routing**
  - Direct navigation via URL
  - Protected page access
  - Login redirect

- **State Persistence**
  - Vocabulary data
  - Login state
  - Word marking persistence

- **Back Navigation**
  - Back button visibility
  - Return to correct page

- **Error Handling**
  - Invalid routes
  - Network error recovery

## Test Fixtures

### Custom Fixtures (`tests/fixtures/fixtures.ts`)

#### `authenticatedPage`
Provides a page with a logged-in user for tests that need authentication.
```typescript
test('should access vocabulary', async ({ authenticatedPage: page }) => {
  await page.goto('/vocabulary');
});
```

#### `freshPage`
Ensures user is logged out for testing login/registration flows.
```typescript
test('should login', async ({ freshPage: page }) => {
  // page is logged out
});
```

### Helper Functions

#### `assertions`
- `assertUserLoggedIn(page, username)`
- `assertUserLoggedOut(page)`
- `assertVocabularyStatsUpdated(page, expectedCount)`
- `assertValidationError(page, errorText)`

#### `navigation`
- `goToLogin(page)`
- `goToRegister(page)`
- `goToVocabulary(page)`
- `goToVideos(page)`

#### `actions`
- `register(page, email, username, password)`
- `login(page, email, password)`
- `markWordAsKnown(page, word)`
- `switchVocabularyLevel(page, level)`
- `logout(page)`

## Test Data

Located in `tests/fixtures/testData.ts`:

### Test Users
```typescript
TEST_USERS.valid: { email, username, password }
TEST_USERS.validAlternate: { ... }
TEST_USERS.invalid: { ... }
```

### Vocabulary Data
```typescript
VOCABULARY_DATA.a1: { level, totalWords: 715, ... }
VOCABULARY_DATA.a2: { level, totalWords: 574, ... }
// ... etc
```

### Endpoints
```typescript
API_ENDPOINTS.auth.register
API_ENDPOINTS.vocabulary.markKnown
// ... etc
```

### Routes
```typescript
ROUTES.login: '/login'
ROUTES.vocabulary: '/vocabulary'
// ... etc
```

## Reports

After running tests, view reports:

### HTML Report
```bash
npx playwright show-report
```

### JSON Results
Check `test-results.json` for detailed test metrics.

## CI/CD Integration

Add to GitHub Actions:

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm install

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## Known Issues

### 1. Password Validation Error Display [HIGH]
**Status**: Identified in Chrome DevTools testing
**Issue**: Generic error message instead of specific validation error
**Location**: Frontend registration form
**Fix Required**: Update error handling to display backend error details

### 2. Logout Response Contract [MEDIUM]
**Status**: Identified in logs
**Issue**: 204 No Content not defined in contract validation
**Location**: POST /api/auth/logout
**Fix Required**: Define contract for 204 response

### 3. Videos Path [LOW]
**Status**: Expected
**Issue**: No test videos available
**Workaround**: Tests focus on available features

## Best Practices

1. **Use fixtures** for common setup/teardown
2. **Use test data** from `testData.ts`
3. **Use helper functions** from `fixtures.ts`
4. **One assertion per test idea** (but can have multiple assertions)
5. **Use descriptive test names**
6. **Keep tests independent** (don't rely on test order)
7. **Use `--headed` mode** when debugging
8. **Check reports** for failures

## Extending Tests

### Add new test
```typescript
test('should do something', async ({ page }) => {
  // Setup
  await navigation.goToLogin(page);

  // Action
  await actions.login(page, TEST_USERS.valid.email, TEST_USERS.valid.password);

  // Assert
  await expect(page).toHaveURL(ROUTES.videos);
});
```

### Add new fixture
Edit `tests/fixtures/fixtures.ts` and extend `test` with new fixture.

### Add new test data
Add to `tests/fixtures/testData.ts` and import in tests.

## Troubleshooting

### Tests can't find elements
- Use `--headed` mode to see what's on screen
- Check selectors in browser DevTools
- Verify element visibility with `isVisible()`

### Tests are flaky
- Increase timeouts in test
- Add `waitForLoadState('networkidle')`
- Use proper waits instead of sleep

### Server won't start
- Check ports 3000 and 8000 are free
- Check `webServer` config in `playwright.config.ts`
- Run servers manually and set `reuseExistingServer: true`

### Authentication fails
- Verify test user credentials in `testData.ts`
- Check backend is running and healthy
- Look for validation errors in browser console

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Test Report Format](https://playwright.dev/docs/test-reporters)

## Contact

For questions or issues, refer to `TEST_EXECUTION_RESULTS.md` for detailed test logs and findings.
