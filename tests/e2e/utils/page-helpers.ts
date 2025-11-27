/**
 * Page helpers - Reusable test utilities that encapsulate common operations
 * Reduces boilerplate and makes tests more maintainable
 */

import { Page, expect } from '@playwright/test';
import { TEST_CONFIG, apiUrl } from './test-config';
import { TestUser } from './test-data-manager';

/**
 * Get token from user, throwing if not set
 */
function getToken(user: TestUser): string {
  if (!user.token) {
    throw new Error('User token is not set - did you login first?');
  }
  return user.token;
}

/**
 * Login helper - handles the entire login flow
 */
export async function loginUser(page: Page, user: TestUser): Promise<void> {
  await page.goto('/login');
  await page.locator(TEST_CONFIG.SELECTORS.EMAIL_INPUT).fill(user.email);
  await page.locator(TEST_CONFIG.SELECTORS.PASSWORD_INPUT).fill(user.password);
  await page.locator(TEST_CONFIG.SELECTORS.SUBMIT_BUTTON).click();

  // Wait for authentication
  await expect(page.locator(TEST_CONFIG.SELECTORS.USER_MENU)).toBeVisible({
    timeout: TEST_CONFIG.DEFAULT_TIMEOUT,
  });
}

/**
 * Logout helper
 */
export async function logoutUser(page: Page): Promise<void> {
  const logoutButton = page.locator(TEST_CONFIG.SELECTORS.LOGOUT_BUTTON);

  if ((await logoutButton.count()) > 0) {
    await logoutButton.click();
    await page.waitForLoadState('networkidle');
  }
}

/**
 * Navigate to vocabulary library
 */
export async function navigateToVocabulary(page: Page): Promise<boolean> {
  const vocabNav = page.locator(TEST_CONFIG.SELECTORS.VOCABULARY_NAV);

  if ((await vocabNav.count()) > 0) {
    await vocabNav.click();
    await page.waitForLoadState('networkidle');
    return true;
  }
  return false;
}

/**
 * Make authenticated API request
 * Accepts either a token string or a TestUser object
 */
export async function authenticatedGet(
  page: Page,
  endpoint: string,
  tokenOrUser: string | TestUser
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const token = typeof tokenOrUser === 'string' ? tokenOrUser : getToken(tokenOrUser);
  const response = await page.request.get(apiUrl(endpoint), {
    headers: { Authorization: `Bearer ${token}` },
  });

  return {
    ok: response.ok(),
    status: response.status(),
    data: response.ok() ? await response.json() : await response.text(),
  };
}

export async function authenticatedPost(
  page: Page,
  endpoint: string,
  tokenOrUser: string | TestUser,
  body?: unknown
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const token = typeof tokenOrUser === 'string' ? tokenOrUser : getToken(tokenOrUser);
  const response = await page.request.post(apiUrl(endpoint), {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    data: body,
  });

  return {
    ok: response.ok(),
    status: response.status(),
    data: response.ok() ? await response.json() : await response.text(),
  };
}

/**
 * Unauthenticated GET request
 */
export async function unauthenticatedGet(
  page: Page,
  endpoint: string
): Promise<{ ok: boolean; status: number; data: unknown }> {
  const response = await page.request.get(apiUrl(endpoint));

  return {
    ok: response.ok(),
    status: response.status(),
    data: response.ok() ? await response.json() : await response.text(),
  };
}

/**
 * Wait for element with multiple fallback selectors
 */
export async function waitForAnySelector(
  page: Page,
  selectors: string[],
  timeout = TEST_CONFIG.DEFAULT_TIMEOUT
): Promise<string | null> {
  for (const selector of selectors) {
    try {
      await page.locator(selector).waitFor({ state: 'visible', timeout: timeout / selectors.length });
      return selector;
    } catch {
      // Try next selector
    }
  }
  return null;
}

/**
 * Check if backend is healthy
 */
export async function checkBackendHealth(page: Page): Promise<boolean> {
  const response = await page.request.get(apiUrl(TEST_CONFIG.ENDPOINTS.HEALTH));
  return response.status() === 200;
}

/**
 * Verify user is on a protected page (not login/register)
 */
export async function verifyOnProtectedPage(page: Page): Promise<boolean> {
  const url = page.url();
  return !url.includes('/login') && !url.includes('/register');
}

/**
 * Verify user is redirected to login
 */
export async function verifyRedirectedToLogin(page: Page, timeout = TEST_CONFIG.NAVIGATION_TIMEOUT): Promise<void> {
  await page.waitForURL((url) => url.pathname.includes('/login'), { timeout });
  await expect(page.locator(TEST_CONFIG.SELECTORS.EMAIL_INPUT)).toBeVisible();
}
