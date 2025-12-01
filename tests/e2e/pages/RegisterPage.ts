import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { ROUTES } from '../config/urls';
import { TIMEOUTS } from '../config/timeouts';

export class RegisterPage extends BasePage {
  readonly emailInput: Locator;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly submitButton: Locator;
  readonly loginLink: Locator;
  readonly errorText: Locator;

  constructor(page: Page) {
    super(page);
    this.emailInput = page.getByTestId('email-input');
    this.usernameInput = page.getByTestId('username-input');
    this.passwordInput = page.getByTestId('password-input');
    this.confirmPasswordInput = page.getByTestId('confirm-password-input');
    this.submitButton = page.getByTestId('register-submit');
    this.loginLink = page.getByTestId('login-link');
    // Matches any text containing "error" or "special character" or "short"
    // or generic error container
    this.errorText = page.locator('.text-red-500, [role="alert"], text=/special character/i, text=/must be at least/i');
  }

  async goto() {
    await this.page.goto(ROUTES.REGISTER);
    await this.waitForLoad();
  }

  async isLoaded(): Promise<boolean> {
    try {
      await expect(this.emailInput).toBeVisible({ timeout: TIMEOUTS.ELEMENT_VISIBLE });
      return true;
    } catch {
      return false;
    }
  }

  async register(email: string, username: string, password: string) {
    await this.emailInput.fill(email);
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.confirmPasswordInput.fill(password);
    await this.submitButton.click();
    
    // Wait for either navigation (success) or error message (validation failure)
    // This handles both successful registration and validation failures efficiently
    try {
      await this.page.waitForURL((url) => !url.pathname.includes('/register'), { timeout: 5000 });
    } catch {
      // If we're still on register page, check for validation errors
      // This is expected for password validation tests
      await this.page.waitForTimeout(1000); // Brief wait for error message to appear
    }
  }

  async clickLogin() {
    await this.loginLink.click();
  }

  async getErrorMessage(): Promise<string | null> {
    try {
      await expect(this.errorText.first()).toBeVisible({ timeout: 5000 });
      return await this.errorText.first().textContent();
    } catch {
      return null;
    }
  }
}