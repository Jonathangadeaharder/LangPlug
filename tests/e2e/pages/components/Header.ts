import { Page, Locator, expect } from '@playwright/test';

export class Header {
  readonly page: Page;
  readonly logoutButton: Locator;
  readonly vocabButton: Locator;
  readonly profileButton: Locator;

  constructor(page: Page) {
    this.page = page;
    // Using robust selectors that fallback to text if testid is missing
    this.logoutButton = page.getByTestId('logout-button').or(page.getByRole('button', { name: 'Logout' }));
    this.vocabButton = page.getByRole('button', { name: 'Vocabulary Library' });
    this.profileButton = page.getByTestId('profile-button');
  }

  async clickLogout() {
    await this.logoutButton.click();
  }

  async clickVocabulary() {
    await this.vocabButton.click();
  }

  async isLoggedIn(): Promise<boolean> {
    try {
      await expect(this.logoutButton).toBeVisible({ timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }
  
  async isLoggedOut(): Promise<boolean> {
      try {
          await expect(this.logoutButton).toBeHidden({ timeout: 5000 });
          return true;
      } catch {
          return false;
      }
  }
}
