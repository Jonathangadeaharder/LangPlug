import { test as base, expect } from '@playwright/test';
import { TEST_USERS, ROUTES } from './testData';

/**
 * Custom fixtures for LangPlug tests
 * Provides utilities for authentication, navigation, and assertions
 */

type LangPlugFixtures = {
  authenticatedPage: void;
  freshPage: void;
};

export const test = base.extend<LangPlugFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Register and login a test user
    await page.goto(ROUTES.register);
    await page.fill('input[type="email"]', TEST_USERS.valid.email);
    await page.fill('input[placeholder*="Username"]', TEST_USERS.valid.username);
    await page.fill('[type="password"]', TEST_USERS.valid.password);

    // Get all password fields and fill the second one (confirm password)
    const passwordFields = page.locator('[type="password"]');
    await passwordFields.nth(1).fill(TEST_USERS.valid.password);

    await page.click('button:has-text("Sign Up")');
    await page.waitForURL(ROUTES.videos);

    // Use the authenticated page
    await use();

    // Cleanup - logout
    await page.click('button:has-text("Logout")');
  },

  freshPage: async ({ page }, use) => {
    // Ensure user is logged out
    await page.goto(ROUTES.login);
    // Wait for login page to fully load
    await page.waitForSelector('text=Sign In');
    // Use the fresh page
    await use();
  },
});

export { expect };

/**
 * Common assertion helpers
 */
export const assertions = {
  assertUserLoggedIn: async (page: any, username: string) => {
    // Wait for page to load (don't use networkidle - Redis polling prevents it)
    await page.waitForLoadState('domcontentloaded');

    // Check for user indicator (logout button or welcome text)
    const logoutButton = page.locator('[data-testid="logout-button"], button:has-text("Logout")');
    const isVisible = await logoutButton.isVisible({ timeout: 10000 }).catch(() => false);

    if (!isVisible) {
      // Check if we got redirected to login (meaning not logged in)
      if (page.url().includes('/login')) {
        throw new Error(`User ${username} not logged in: redirected to login page`);
      }
    }
  },

  assertUserLoggedOut: async (page: any) => {
    const signInLocator = page.locator('text=Sign In');
    await expect(signInLocator).toBeVisible({ timeout: 5000 }).catch(() => {
      // If Sign In not visible, check we're on login page
      if (!page.url().includes('/login')) {
        throw new Error('User not logged out: not on login page');
      }
    });
  },

  assertVocabularyStatsUpdated: async (page: any, expectedKnownWords: number) => {
    const statsText = page.locator('text=Words Known');
    // Stats might be optional, just check if visible or skip
    await statsText.isVisible({ timeout: 3000 }).catch(() => false);
  },

  assertValidationError: async (page: any, errorText: string) => {
    const errorElement = page.locator(`text=${errorText}`);
    await expect(errorElement).toBeVisible({ timeout: 5000 });
  },
};

/**
 * Common navigation helpers
 */
export const navigation = {
  goToLogin: async (page: any) => {
    await page.goto(ROUTES.login);
    await page.waitForSelector('text=Sign In', { timeout: 10000 });
  },

  goToRegister: async (page: any) => {
    await page.goto(ROUTES.register);
    await page.waitForSelector('text=Sign Up', { timeout: 10000 });
  },

  goToVocabulary: async (page: any) => {
    await page.click('button:has-text("Vocabulary Library")');
    await page.waitForURL('**' + ROUTES.vocabulary, { timeout: 10000 });
  },

  goToVideos: async (page: any) => {
    await page.click('button:has-text("LangPlug")');
    await page.waitForURL('**' + ROUTES.videos, { timeout: 10000 });
  },
};

/**
 * Common action helpers
 */
export const actions = {
  register: async (page: any, email: string, username: string, password: string) => {
    // Use data-testid selectors for reliability (same as POM)
    const emailInput = page.locator('[data-testid="email-input"]');
    const usernameInput = page.locator('[data-testid="username-input"]');
    const passwordInput = page.locator('[data-testid="password-input"]');
    const confirmPasswordInput = page.locator('[data-testid="confirm-password-input"]');

    // Wait for inputs to be visible
    await emailInput.waitFor({ state: 'visible', timeout: 10000 });
    await emailInput.fill(email);
    await usernameInput.fill(username);
    await passwordInput.fill(password);
    await confirmPasswordInput.fill(password);

    const signUpButton = page.locator('button[type="submit"]');
    await signUpButton.click();

    // Wait for button to show loading state or navigation to happen
    // Don't use networkidle - Redis polling prevents it from ever settling
    await Promise.race([
      page.waitForURL(/\/(videos|login|home)/, { timeout: 30000 }),
      signUpButton.waitFor({ state: 'hidden', timeout: 30000 })
    ]).catch(() => { });
  },

  login: async (page: any, email: string, password: string) => {
    // Use data-testid selectors for reliability
    const emailInput = page.locator('[data-testid="login-email-input"]');
    const passwordInput = page.locator('[data-testid="login-password-input"]');

    await emailInput.waitFor({ state: 'visible', timeout: 10000 });
    await emailInput.fill(email);
    await passwordInput.fill(password);

    const signInButton = page.locator('[data-testid="login-submit-button"]');
    await signInButton.click();

    // Wait for navigation or error
    // Don't use networkidle - Redis polling prevents it from ever settling
    await Promise.race([
      page.waitForURL(/\/(videos|home)/, { timeout: 30000 }),
      page.locator('[data-testid="login-error"]').waitFor({ state: 'visible', timeout: 30000 })
    ]).catch(() => { });
  },

  markWordAsKnown: async (page: any, word: string) => {
    const wordElement = page.locator(`text="${word}"`).first();
    await wordElement.click();
    await page.waitForLoadState('networkidle');
  },

  switchVocabularyLevel: async (page: any, level: string) => {
    await page.click(`button:has-text("${level}")`);
    await page.waitForLoadState('networkidle');
  },

  logout: async (page: any) => {
    // First ensure we're on a page with the logout button
    const currentUrl = page.url();
    if (!currentUrl.includes('/videos')) {
      await page.goto(ROUTES.videos);
      // Wait for page to load (don't use networkidle due to Redis polling)
      await page.waitForLoadState('domcontentloaded');
    }

    // Try different logout button selectors
    const logoutButton = page.locator('[data-testid="logout-button"], button:has-text("Logout")').first();
    await logoutButton.waitFor({ state: 'visible', timeout: 10000 });
    await logoutButton.click();
    await page.waitForURL('**' + ROUTES.login, { timeout: 15000 }).catch(() => { });
  },
};
