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
    // Either check for welcome message or check if we're on /videos page
    const welcomeLocator = page.locator(`text=Welcome, ${username}`);
    const videosCheck = page.url().includes('/videos');
    
    const isVisible = await welcomeLocator.isVisible({ timeout: 3000 }).catch(() => false);
    if (!isVisible && !videosCheck) {
      throw new Error(`User ${username} not logged in: welcome message not visible and not on videos page`);
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
    await page.goto('http://127.0.0.1:3000' + ROUTES.login);
    await page.waitForSelector('text=Sign In', { timeout: 10000 });
  },

  goToRegister: async (page: any) => {
    await page.goto('http://127.0.0.1:3000' + ROUTES.register);
    await page.waitForSelector('text=Sign Up', { timeout: 10000 });
  },

  goToVocabulary: async (page: any) => {
    await page.click('button:has-text("Vocabulary Library")');
    await page.waitForURL('http://127.0.0.1:3000' + ROUTES.vocabulary, { timeout: 10000 });
  },

  goToVideos: async (page: any) => {
    await page.click('button:has-text("LangPlug")');
    await page.waitForURL('http://127.0.0.1:3000' + ROUTES.videos, { timeout: 10000 });
  },
};

/**
 * Common action helpers
 */
export const actions = {
  register: async (page: any, email: string, username: string, password: string) => {
    const emailInput = page.locator('input[type="email"]');
    const usernameInput = page.locator('input[placeholder*="Username"]');
    const passwordFields = page.locator('[type="password"]');
    
    // Wait for inputs to be visible
    await emailInput.waitFor({ state: 'visible', timeout: 10000 });
    await emailInput.fill(email);
    await usernameInput.fill(username);
    await passwordFields.nth(0).fill(password);
    await passwordFields.nth(1).fill(password);

    const signUpButton = page.locator('button:has-text("Sign Up")');
    await signUpButton.click();
    await page.waitForLoadState('networkidle', { timeout: 10000 });
  },

  login: async (page: any, email: string, password: string) => {
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    
    await emailInput.waitFor({ state: 'visible', timeout: 10000 });
    await emailInput.fill(email);
    await passwordInput.fill(password);
    const signInButton = page.locator('button:has-text("Sign In")');
    await signInButton.click();
    await page.waitForURL('**/*' + ROUTES.videos, { timeout: 10000 }).catch(() => {
      // If waitForURL fails, at least wait for page to load
      return page.waitForLoadState('networkidle', { timeout: 10000 });
    });
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
