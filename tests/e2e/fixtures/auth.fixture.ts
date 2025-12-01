/**
 * Authentication fixtures for E2E tests.
 * Provides authenticated page contexts to avoid repeated registration.
 */
import { test as base, Page } from '@playwright/test';
import { UserFactory, TestUser } from '../factories/userFactory';
import { SEEDED_USERS, SeededUser } from './seeded-users';
import { BASE_URL, ROUTES } from '../config/urls';
import { TIMEOUTS } from '../config/timeouts';
import { AUTH_SELECTORS } from '../selectors/auth.selectors';

/**
 * Logs in an existing user (e.g., seeded user).
 * Much faster than registration since password is already hashed.
 */
async function loginUser(page: Page, user: SeededUser): Promise<void> {
  await page.goto(`${BASE_URL}${ROUTES.LOGIN}`);
  await page.waitForLoadState('domcontentloaded');

  await page.locator('[data-testid="email-input"]').fill(user.email);
  await page.locator('[data-testid="password-input"]').fill(user.password);
  await page.locator('[data-testid="submit-button"]').click();

  await page.waitForURL(/\/videos/, { timeout: TIMEOUTS.NAVIGATION });
}

/**
 * Registers a new user and returns the authenticated page.
 */
async function registerUser(page: Page, user: TestUser): Promise<void> {
  await page.goto(`${BASE_URL}${ROUTES.REGISTER}`);
  await page.waitForLoadState('domcontentloaded');

  // Fill registration form
  await page.locator(AUTH_SELECTORS.REGISTER.EMAIL_INPUT).fill(user.email);
  await page.locator(AUTH_SELECTORS.REGISTER.USERNAME_INPUT).fill(user.username);
  await page.locator(AUTH_SELECTORS.REGISTER.PASSWORD_INPUT).fill(user.password);
  await page.locator(AUTH_SELECTORS.REGISTER.CONFIRM_PASSWORD_INPUT).fill(user.password);

  // Submit
  await page.locator(AUTH_SELECTORS.REGISTER.SUBMIT_BUTTON).click();

  // Wait for successful registration (redirect to videos)
  await page.waitForURL(/\/videos/, { timeout: TIMEOUTS.REGISTRATION });
}

/**
 * Extended test fixtures with authentication support.
 */
export const test = base.extend<{
  /** A unique test user created for this test */
  testUser: TestUser;
  /** The pre-seeded test user (instant login, no registration delay) */
  seededUser: SeededUser;
  /** A page that's already logged in with testUser (via registration) */
  authenticatedPage: Page;
  /** A page logged in with the seeded user (instant, no hashing delay) */
  fastAuthPage: Page;
}>({
  // Create a unique test user for each test
  testUser: async ({ }, use) => {
    const user = UserFactory.create();
    await use(user);
  },

  // Provide the pre-seeded user
  seededUser: async ({ }, use) => {
    await use(SEEDED_USERS.default);
  },

  // Provide an authenticated page (user already registered and logged in)
  authenticatedPage: async ({ page, testUser }, use) => {
    await registerUser(page, testUser);
    await use(page);
  },

  // Fast authenticated page using seeded user (no registration delay)
  fastAuthPage: async ({ page, seededUser }, use) => {
    await loginUser(page, seededUser);
    await use(page);
  },
});

export { expect } from '@playwright/test';
export { UserFactory, TestUser };
