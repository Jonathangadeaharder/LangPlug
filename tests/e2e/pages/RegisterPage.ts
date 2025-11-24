import { Page } from '@playwright/test';

export class RegisterPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('http://127.0.0.1:3000/register');
    await this.page.waitForLoadState('networkidle');
  }

  async fillEmail(email: string) {
    await this.page.locator('[data-testid="email-input"]').fill(email);
  }

  async fillUsername(username: string) {
    await this.page.locator('[data-testid="username-input"]').fill(username);
  }

  async fillPassword(password: string) {
    await this.page.locator('[data-testid="password-input"]').fill(password);
  }

  async fillConfirmPassword(password: string) {
    await this.page.locator('[data-testid="confirm-password-input"]').fill(password);
  }

  async clickSubmit() {
    // Register button uses text selector, let's find it by button role
    await this.page.locator('button[type="submit"]').click();
  }

  async register(email: string, username: string, password: string) {
    await this.fillEmail(email);
    await this.fillUsername(username);
    await this.fillPassword(password);
    await this.fillConfirmPassword(password);
    await this.clickSubmit();
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    return await this.page.locator('[data-testid="email-input"]').isVisible({ timeout: 5000 }).catch(() => false);
  }

  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }

  async hasErrorMessage(): Promise<boolean> {
    // Look for error messages which are typically in ErrorMessage styled component
    const errorLocators = await this.page.locator('div:has-text("required"), div:has-text("Invalid")').count();
    return errorLocators > 0;
  }
}
