/**
 * Role-Based Locators (Best Practice #2)
 * Use user-facing roles instead of CSS selectors.
 * These are more resilient to DOM changes.
 */
import { Page, Locator } from '@playwright/test';

/**
 * Get form elements by their label text (most accessible approach)
 */
export function getFormLocators(page: Page) {
  return {
    // Login form
    emailInput: () => page.getByLabel('Email'),
    passwordInput: () => page.getByLabel('Password'),
    usernameInput: () => page.getByLabel('Username'),
    confirmPasswordInput: () => page.getByLabel('Confirm Password'),
    
    // Buttons by role and name
    signInButton: () => page.getByRole('button', { name: 'Sign In' }),
    signUpButton: () => page.getByRole('button', { name: 'Sign Up' }),
    logoutButton: () => page.getByRole('button', { name: /logout/i }),
    submitButton: () => page.getByRole('button', { name: 'Submit' }),
  };
}

/**
 * Get navigation elements by role
 */
export function getNavLocators(page: Page) {
  return {
    // Links
    loginLink: () => page.getByRole('link', { name: /sign in/i }),
    registerLink: () => page.getByRole('link', { name: /sign up/i }),
    
    // Navigation buttons
    backButton: () => page.getByRole('button', { name: /back/i }),
    vocabularyButton: () => page.getByRole('button', { name: /vocabulary/i }),
    profileButton: () => page.getByRole('button', { name: /profile/i }),
    
    // Headings
    pageTitle: (name: string | RegExp) => page.getByRole('heading', { name }),
  };
}

/**
 * Get content elements by role
 */
export function getContentLocators(page: Page) {
  return {
    // Lists
    wordList: () => page.getByRole('list'),
    wordItems: () => page.getByRole('listitem'),
    
    // Alerts and status
    errorAlert: () => page.getByRole('alert'),
    statusMessage: () => page.getByRole('status'),
    
    // Tabs
    tabList: () => page.getByRole('tablist'),
    tab: (name: string) => page.getByRole('tab', { name }),
    
    // Text content
    textContent: (text: string | RegExp) => page.getByText(text),
  };
}

/**
 * Page Object with role-based locators
 */
export class RoleBasedPage {
  readonly page: Page;
  readonly form: ReturnType<typeof getFormLocators>;
  readonly nav: ReturnType<typeof getNavLocators>;
  readonly content: ReturnType<typeof getContentLocators>;

  constructor(page: Page) {
    this.page = page;
    this.form = getFormLocators(page);
    this.nav = getNavLocators(page);
    this.content = getContentLocators(page);
  }

  /**
   * Wait for page to be ready (no loading spinners)
   */
  async waitForReady(): Promise<void> {
    // Wait for any loading indicators to disappear
    const loadingIndicator = this.page.locator('[data-testid*="loading"]');
    await loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {});
  }

  /**
   * Assert page title
   */
  async expectHeading(text: string | RegExp): Promise<void> {
    const heading = this.nav.pageTitle(text);
    await heading.waitFor({ state: 'visible' });
  }
}
