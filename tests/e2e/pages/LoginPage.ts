import { Page, expect } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('http://127.0.0.1:3000/login');
    await this.page.waitForLoadState('networkidle');
  }

  async fillEmail(email: string) {
    await this.page.locator('[data-testid="login-email-input"]').fill(email);
  }

  async fillPassword(password: string) {
    await this.page.locator('[data-testid="login-password-input"]').fill(password);
  }

  async clickSubmit() {
    await this.page.locator('[data-testid="login-submit-button"]').click();
  }

  async login(email: string, password: string) {
    await this.fillEmail(email);
    await this.fillPassword(password);
    await this.clickSubmit();
    await this.page.waitForLoadState('networkidle');
  }

  async getErrorMessage(): Promise<string | null> {
    const errorElement = this.page.locator('[data-testid="login-error"]');
    const isVisible = await errorElement.isVisible({ timeout: 3000 }).catch(() => false);
    if (isVisible) {
      return await errorElement.textContent();
    }
    return null;
  }

  async isErrorVisible(): Promise<boolean> {
    return await this.page.locator('[data-testid="login-error"]').isVisible({ timeout: 3000 }).catch(() => false);
  }

  async clickRegisterLink() {
    await this.page.locator('[data-testid="register-link"]').click();
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    return await this.page.locator('[data-testid="login-email-input"]').isVisible({ timeout: 5000 }).catch(() => false);
  }

  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }
}
