# E2E Test Optimization Plan

## Current Issues

### 1. Inconsistent Architecture
- `auth.spec.ts` uses action helpers from `fixtures.ts`
- `auth-pom.spec.ts` uses Page Object Model classes
- Mixed patterns make maintenance difficult

### 2. Code Duplication
```typescript
// This pattern appears 8+ times:
const timestamp = Date.now();
const uniqueEmail = `test${timestamp}@example.com`;
const uniqueUsername = `user${timestamp}`;
await actions.register(page, uniqueEmail, uniqueUsername, 'Password123!');
await page.waitForURL(/\/videos/, { timeout: 30000 });
```

### 3. Hardcoded Values
- Timeouts: 30000, 15000, 10000, 5000, 1000, 500 scattered everywhere
- URLs: `http://127.0.0.1:3000` hardcoded in POMs
- Selectors: Duplicated across files

### 4. `networkidle` Still Present
- `RegisterPage.ts` line 8 and 38 still use `networkidle`

### 5. No Test Data Factory
- User credentials generated inline in each test
- No centralized test data management

---

## Recommended Optimizations

### 1. Create Test Data Factory

```typescript
// tests/e2e/factories/userFactory.ts
export class UserFactory {
  static createUnique(prefix = 'test') {
    const timestamp = Date.now();
    return {
      email: `${prefix}${timestamp}@example.com`,
      username: `${prefix}${timestamp}`,
      password: 'SecurePassword123!'
    };
  }
}
```

### 2. Create Authenticated Fixture

```typescript
// tests/e2e/fixtures/auth.fixture.ts
import { test as base } from '@playwright/test';

export const test = base.extend<{
  authenticatedPage: Page;
  testUser: { email: string; username: string; password: string };
}>({
  testUser: async ({}, use) => {
    const user = UserFactory.createUnique();
    await use(user);
  },
  
  authenticatedPage: async ({ page, testUser }, use) => {
    // Register and login once, reuse for tests needing auth
    await registerAndLogin(page, testUser);
    await use(page);
  }
});
```

### 3. Centralize Timeouts Configuration

```typescript
// tests/e2e/config/timeouts.ts
export const TIMEOUTS = {
  REGISTRATION: 30_000,  // Password hashing is slow
  NAVIGATION: 10_000,
  ELEMENT_VISIBLE: 5_000,
  TOAST: 3_000,
  SHORT_WAIT: 1_000
};
```

### 4. Standardize on Page Object Model

Convert all tests to use POMs consistently:

```typescript
// tests/e2e/pages/BasePage.ts
export abstract class BasePage {
  constructor(protected page: Page) {}
  
  protected async waitForNavigation(pattern: RegExp, timeout = TIMEOUTS.NAVIGATION) {
    await this.page.waitForURL(pattern, { timeout });
  }
  
  protected async waitForElement(selector: string, timeout = TIMEOUTS.ELEMENT_VISIBLE) {
    await this.page.locator(selector).waitFor({ state: 'visible', timeout });
  }
  
  // Don't use networkidle!
  async goto(path: string) {
    await this.page.goto(`${BASE_URL}${path}`);
    await this.page.waitForLoadState('domcontentloaded');
  }
}
```

### 5. Create Selector Constants

```typescript
// tests/e2e/selectors/auth.selectors.ts
export const AUTH_SELECTORS = {
  // Registration
  EMAIL_INPUT: '[data-testid="email-input"]',
  USERNAME_INPUT: '[data-testid="username-input"]',
  PASSWORD_INPUT: '[data-testid="password-input"]',
  CONFIRM_PASSWORD_INPUT: '[data-testid="confirm-password-input"]',
  SUBMIT_BUTTON: 'button[type="submit"]',
  
  // Login
  LOGIN_EMAIL: '[data-testid="login-email-input"]',
  LOGIN_PASSWORD: '[data-testid="login-password-input"]',
  LOGIN_SUBMIT: '[data-testid="login-submit-button"]',
  
  // Navigation
  LOGOUT_BUTTON: '[data-testid="logout-button"]',
  VOCAB_BUTTON: 'button:has-text("Vocabulary Library")',
  
  // Messages
  ERROR_MESSAGE: '[data-testid="error-message"], .text-red-500',
  SUCCESS_TOAST: 'div[role="status"]'
};
```

### 6. Refactored Test Structure

```
tests/e2e/
├── config/
│   ├── timeouts.ts
│   └── urls.ts
├── factories/
│   └── userFactory.ts
├── fixtures/
│   ├── auth.fixture.ts      # Authenticated page fixture
│   └── index.ts             # Re-exports all fixtures
├── pages/
│   ├── BasePage.ts
│   ├── LoginPage.ts
│   ├── RegisterPage.ts
│   └── VideosPage.ts
├── selectors/
│   └── auth.selectors.ts
├── specs/
│   ├── auth/
│   │   ├── registration.spec.ts
│   │   ├── login.spec.ts
│   │   ├── logout.spec.ts
│   │   └── session.spec.ts
│   └── vocabulary/
│       └── ...
└── utils/
    └── waitHelpers.ts
```

### 7. Example Refactored Test

```typescript
// tests/e2e/specs/auth/registration.spec.ts
import { test, expect } from '../../fixtures';
import { RegisterPage } from '../../pages/RegisterPage';
import { UserFactory } from '../../factories/userFactory';
import { TIMEOUTS } from '../../config/timeouts';

test.describe('Registration', () => {
  test('should register with valid credentials', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    const user = UserFactory.createUnique();
    
    await registerPage.goto();
    await registerPage.register(user);
    await registerPage.waitForSuccessfulRegistration();
    
    expect(page.url()).not.toContain('/register');
  });

  test('should reject invalid password', async ({ page }) => {
    const registerPage = new RegisterPage(page);
    const user = UserFactory.createUnique();
    user.password = 'weak'; // Override with invalid
    
    await registerPage.goto();
    await registerPage.register(user);
    await registerPage.expectPasswordError();
  });
});
```

---

## Implementation Priority

| Priority | Task | Impact | Status |
|----------|------|--------|--------|
| 1. High | Fix `networkidle` in POMs | Prevents flaky tests | ✅ DONE |
| 2. High | Create UserFactory | Eliminates 50+ lines of duplication | ✅ DONE |
| 3. Medium | Centralize timeouts | Single source of truth | ✅ DONE |
| 4. Medium | Create authenticated fixture | Speeds up tests needing login | ✅ DONE |
| 5. Low | Reorganize folder structure | Better discoverability | ✅ DONE |
| 6. Low | Full POM migration | Consistent architecture | Partial |

---

## Completed Optimizations

1. ✅ **Fixed POMs** - Removed `networkidle` from RegisterPage and LoginPage
2. ✅ **Created UserFactory** - `factories/userFactory.ts` eliminates duplicate user generation
3. ✅ **Created TIMEOUTS constant** - `config/timeouts.ts` centralizes all timeout values
4. ✅ **Created AUTH_SELECTORS** - `selectors/auth.selectors.ts` centralizes all selectors
5. ✅ **Created authenticated fixture** - `fixtures/auth.fixture.ts` for pre-authenticated tests
6. ✅ **Updated auth.spec.ts** - Now uses UserFactory and centralized config

## Remaining (Optional)

1. Create more domain-specific POMs (VideosPage, VocabularyPage)
2. Migrate other spec files to use new fixtures
3. Add more test data factories (VideoFactory, etc.)
