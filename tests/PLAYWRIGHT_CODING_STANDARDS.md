# Playwright Coding Standards & Testability Guide

This guide focuses on **optimizing application code for testability** and writing **robust, flake-free Playwright tests**. It complements the high-level infrastructure documentation in `TESTING_BEST_PRACTICES.md`.

## 1. Optimizing Code for Testability

The most effective way to ensure stable tests is to design the application code with testing in mind.

### 1.1. Use `data-testid` for Stability
Reliable selectors are the foundation of stable tests. While user-facing attributes (text, role) are preferred, `data-testid` provides an unshakeable anchor when semantic selectors are ambiguous or prone to change.

**React Component Pattern:**
```tsx
// GOOD: Explicit test ID decoupled from styling or implementation
export const LoginForm = ({ onSubmit }) => (
  <form
    onSubmit={onSubmit}
    data-testid="login-form" // 👈 Stable anchor
    className="p-4 bg-gray-100"
  >
    <input
      type="email"
      data-testid="email-input" // 👈 Will not break if placeholder/label changes
      placeholder="Enter email"
    />
    <button type="submit">Login</button>
  </form>
);
```

**Playwright Usage:**
```typescript
// ❌ Brittle - breaks if class changes
await page.locator('.bg-gray-100 input').fill('user@example.com');

// ✅ Robust - survives redesigns
await page.getByTestId('email-input').fill('user@example.com');
```

### 1.2. Accessibility-First Selectors (`getByRole`)
Whenever possible, use accessibility attributes. This ensures your app is accessible while testing it.

**React Component:**
```tsx
<button aria-label="Close modal" onClick={close}>×</button>
```

**Playwright Usage:**
```typescript
// Tests that the button is accessible AND clickable
await page.getByRole('button', { name: 'Close modal' }).click();
```

### 1.3. Avoid "Test-Specific" Logic in Production
Do not add conditional logic like `if (window.UNDER_TEST) { ... }`. Instead:
- **Mock API responses** at the network layer (Playwright `page.route`).
- **Inject configuration** via environment variables.
- **Use Feature Flags** to control complex behaviors.

## 2. Writing Robust Playwright Tests

### 2.1. The Golden Rule: Auto-Waiting
Playwright automatically waits for elements to be **actionable** (visible, stable, enabled).
- **❌ BAD:** Manual sleeps or waiting for arbitrary states.
- **✅ GOOD:** Rely on actionability checks.

```typescript
// ❌ Flaky
await page.waitForTimeout(1000);
await page.click('#submit');

// ✅ Robust (Auto-waits for visibility + enabled + stable layout)
await page.click('#submit');
```

### 2.2. Web-First Assertions
Use assertions that retry until the condition is met.

```typescript
// ❌ BAD: Immediate check, fails if animation is running
const isVisible = await page.isVisible('#success');
expect(isVisible).toBe(true);

// ✅ GOOD: Retries for 5s (default) until true
await expect(page.locator('#success')).toBeVisible();
```

### 2.3. Isolation & Independence
Every test must start with a clean slate.
- **Use `beforeEach`** to reset state (or Playwright's `storageState` for auth).
- **Never depend on execution order**. Parallel execution will break dependent tests.
- **Database Cleanup:** Ensure DB is cleaned/seeded via API or fixtures, not UI.

### 2.4. Page Object Model (POM)
Encapsulate page structure in classes to reduce code duplication.

```typescript
// tests/pages/LoginPage.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByTestId('email-input');
    this.submitButton = page.getByRole('button', { name: 'Login' });
  }

  async login(email: string) {
    await this.emailInput.fill(email);
    await this.submitButton.click();
  }
}
```

## 3. Advanced Testability Patterns

### 3.1. Network Mocking for Determinism
Avoid relying on live 3rd-party APIs (Stripe, Auth0) for every test. Use `page.route` to mock responses.

```typescript
await page.route('**/api/users', async route => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify([{ id: 1, name: 'Test User' }]),
  });
});
```

### 3.2. Custom Test Fixtures
Extend Playwright's `test` object to provide pre-configured environments.

```typescript
// tests/fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';

export const test = base.extend<{ loginPage: LoginPage }>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.navigate();
    await use(loginPage);
  },
});
```

### 3.3. Visual Regression Testing
Use snapshots to catch unintended UI changes.
```typescript
await expect(page).toHaveScreenshot('landing-page.png');
```

## 4. Checklist for New Features

Before marking a feature as "Done", verify:
- [ ] Key interactive elements have `data-testid` or accessible roles.
- [ ] A Playwright test covers the "Happy Path".
- [ ] The test runs in isolation (doesn't need other tests to run first).
- [ ] No `waitForTimeout` is used in the test code.
