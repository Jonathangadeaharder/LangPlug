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
    await expect(page.locator(`text=Welcome, ${username}`)).toBeVisible();
  },

  assertUserLoggedOut: async (page: any) => {
    await expect(page.locator('text=Sign In')).toBeVisible();
  },

  assertVocabularyStatsUpdated: async (page: any, expectedKnownWords: number) => {
    const statsText = page.locator('text=Words Known');
    await expect(statsText).toBeVisible();
  },

  assertValidationError: async (page: any, errorText: string) => {
    const errorElement = page.locator(`text=${errorText}`);
    await expect(errorElement).toBeVisible();
  },
};

/**
 * Common navigation helpers
 */
export const navigation = {
  goToLogin: async (page: any) => {
    await page.goto(ROUTES.login);
    await page.waitForSelector('text=Sign In');
  },

  goToRegister: async (page: any) => {
    await page.goto(ROUTES.register);
    await page.waitForSelector('text=Sign Up');
  },

  goToVocabulary: async (page: any) => {
    await page.click('button:has-text("Vocabulary Library")');
    await page.waitForURL(ROUTES.vocabulary);
  },

  goToVideos: async (page: any) => {
    await page.click('button:has-text("LangPlug")');
    await page.waitForURL(ROUTES.videos);
  },
};

/**
 * Common action helpers
 */
export const actions = {
  register: async (page: any, email: string, username: string, password: string) => {
    await page.fill('input[type="email"]', email);
    await page.fill('input[placeholder*="Username"]', username);

    const passwordFields = page.locator('[type="password"]');
    await passwordFields.nth(0).fill(password);
    await passwordFields.nth(1).fill(password);

    await page.click('button:has-text("Sign Up")');
    await page.waitForLoadState('networkidle');
  },

  login: async (page: any, email: string, password: string) => {
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button:has-text("Sign In")');
    await page.waitForURL(ROUTES.videos);
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
    await page.click('button:has-text("Logout")');
    await page.waitForURL(ROUTES.login);
  },
};
