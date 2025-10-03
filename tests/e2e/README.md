# E2E Testing with Playwright

This directory contains end-to-end (E2E) workflow tests for the LangPlug application using Playwright. These tests have been designed to eliminate anti-patterns and focus on business outcome verification.

## Anti-Patterns Eliminated

### ❌ What We Removed

- **Array Index Selectors**: No more `buttons[0]` or `elements[1]`
- **DOM Element Counting**: No more testing number of elements as primary assertion
- **Status Code Tolerance**: No more accepting multiple status codes as valid
- **Hard-coded Paths**: No more Windows-specific or absolute paths
- **Implementation Coupling**: No more testing internal CSS colors or computed styles
- **Mock Call Counting**: No more relying on mock method calls as primary assertions
- **Puppeteer Anti-patterns**: Removed brittle querySelector arrays and style-based selections

### ✅ What We Implemented

- **Semantic Selectors**: `data-testid`, `role` queries, semantic CSS selectors
- **Business Outcome Verification**: Testing actual user workflows and results
- **Robust Element Selection**: Multiple fallback selectors with proper error handling
- **Proper Test Isolation**: Independent test data and cleanup
- **Cross-Platform Compatibility**: Dynamic URL detection and path resolution
- **Deterministic Waits**: Explicit waits on selectors and events instead of timeouts

## Test Structure

```
e2e/
├── playwright.config.ts           # Playwright configuration
├── setup/
│   ├── global-setup.ts           # Test environment setup
│   └── global-teardown.ts        # Test environment cleanup
├── utils/
│   ├── test-environment-manager.ts  # Server management
│   └── test-data-manager.ts         # API-based test data creation
└── workflows/
    ├── authentication.workflow.test.ts     # Auth flows
    ├── vocabulary-learning.workflow.test.ts # Vocabulary features
    ├── video-processing.workflow.test.ts   # Video processing
    └── complete-learning.workflow.test.ts  # Full user journey
```

## Key Improvements

### 1. Semantic Element Selection

```typescript
// ❌ Old anti-pattern
const button = buttons[0];
await button.click();

// ✅ New approach
const knowButton = page
  .locator('[data-testid="know-button"]')
  .or(
    page
      .getByRole("button", { name: /know|correct|yes/i })
      .or(page.locator(".know-answer-button")),
  );
await expect(knowButton).toBeVisible();
await knowButton.click();
```

### 2. Business Outcome Verification

```typescript
// ❌ Old anti-pattern
expect(buttons.length).toBe(3);

// ✅ New approach
await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
// Verify user can access protected features
const vocabularySection = page.locator('[data-testid="vocabulary-list"]');
await expect(vocabularySection).toBeVisible();
```

### 3. Proper Error Handling

```typescript
// ✅ Robust element selection with fallbacks
const submitButton = page
  .locator('button[type="submit"]')
  .or(page.getByRole("button", { name: /register/i }));

if (!(await submitButton.isVisible())) {
  throw new Error("Registration submit button not found");
}
await submitButton.click();
```

### 4. API-Based Test Data

```typescript
// ✅ Create test data through API, not UI manipulation
const testUser = await testDataManager.createTestUser({
  username: "e2euser",
  email: "e2e@langplug.com",
  password: "TestPassword123!",
});
```

## Running Tests

### Prerequisites

```bash
cd tests
npm install
npm run playwright:install
```

### Test Execution

```bash
# Run all E2E tests
npm run playwright:test

# Run with UI mode (interactive)
npm run playwright:test:ui

# Debug mode
npm run playwright:test:debug

# View test reports
npm run playwright:report
```

### Through Unified Test Runner

```bash
# Run only E2E tests
npm run test:e2e

# Run all tests including E2E
npm run test:all
```

## Test Environment

### Automatic Setup

The E2E tests automatically:

1. Start backend server on port 8001
2. Start frontend server on port 3001
3. Set up test database with clean state
4. Create isolated test data for each test

### Configuration

- **Backend**: `http://localhost:8001` (test environment)
- **Frontend**: `http://localhost:3001` (test environment)
- **Database**: SQLite test database with automatic cleanup
- **Timeouts**: 60s for tests, 30s for actions, 10s for expectations

## Workflow Tests

### Authentication Workflow

- User registration and login
- Access control verification
- Error handling for invalid credentials
- Logout and session management

### Vocabulary Learning Workflow

- Vocabulary game progression
- Custom vocabulary creation
- Difficulty-based filtering
- Progress tracking

### Video Processing Workflow

- Video upload and processing
- Processing status monitoring
- Error handling and retry
- Vocabulary extraction verification

### Complete Learning Workflow

- Full user journey from video upload to vocabulary mastery
- Integration between all features
- Progress tracking across sessions
- Episode repetition with improvement tracking

## Best Practices

### Element Selection Priority

1. **data-testid attributes**: `[data-testid="element-id"]`
2. **Role-based queries**: `page.getByRole('button', { name: /text/i })`
3. **Semantic CSS selectors**: `input[type="email"]`, `button[type="submit"]`
4. **Text-based fallbacks**: `page.getByText(/pattern/i)`

### Assertions

- Test business outcomes, not implementation details
- Use specific, meaningful error messages
- Wait for elements to be visible before interaction
- Verify actual data persistence through API when possible

### Test Data Management

- Create data through API, not UI
- Clean up after each test
- Use unique identifiers (timestamps, UUIDs)
- Isolate tests completely from each other

## Debugging

### Common Issues

1. **Element not found**: Check selector priority and fallbacks
2. **Test timeouts**: Verify services are running and responsive
3. **Flaky tests**: Add proper waits and stable selectors
4. **Cross-platform issues**: Use relative paths and dynamic URLs

### Debug Tools

```bash
# Run specific test with debug
npx playwright test authentication.workflow.test.ts --debug

# Run with headed browser
npx playwright test --headed

# Generate trace files
npx playwright test --trace on
```

## Migration from Puppeteer

The old Puppeteer-based tests had several anti-patterns that have been eliminated:

1. **Brittle selectors**: Replaced CSS color detection with semantic selectors
2. **Implementation coupling**: Removed dependency on computed styles
3. **Array indexing**: Replaced with semantic element selection
4. **Manual browser management**: Automated through Playwright configuration
5. **Hardcoded delays**: Replaced with explicit waits on elements

This new Playwright setup provides robust, maintainable E2E tests that focus on user workflows and business outcomes rather than implementation details.
