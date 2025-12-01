import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { ROUTES } from '../config/urls';
import { TIMEOUTS } from '../config/timeouts';

export class LoginPage extends BasePage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly registerLink: Locator;

  constructor(page: Page) {
    super(page);
    // Best Practice: Initialize locators in constructor using getByTestId
    this.emailInput = page.getByTestId('email-input');
    this.passwordInput = page.getByTestId('password-input');
    this.submitButton = page.getByTestId('submit-button');
    this.errorMessage = page.getByTestId('error-message');
    this.registerLink = page.getByTestId('register-link');
  }

  async goto() {
    await this.page.goto(ROUTES.LOGIN);
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

  async fillEmail(email: string) {
    await this.emailInput.fill(email);
  }

  async fillPassword(password: string) {
    await this.passwordInput.fill(password);
  }

  async clickSubmit() {
    await this.submitButton.click();
  }

  async login(email: string, password: string) {
    await this.fillEmail(email);
    await this.fillPassword(password);
    await this.clickSubmit();
    // Note: We don't wait here because the next step might be success or failure.
    // The test should decide what to wait for next (e.g. waitForURL or errorMessage).
  }

  async clickRegister() {
    await this.registerLink.click();
  }

  async waitForError() {
    await expect(this.errorMessage).toBeVisible({ timeout: TIMEOUTS.FORM_RESPONSE });
  }

  async isErrorVisible(): Promise<boolean> {
    try {
      await expect(this.errorMessage).toBeVisible({ timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async getErrorText(): Promise<string> {
    return await this.errorMessage.textContent() || '';
  }
}
