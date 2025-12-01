import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * Page Object for the Landing Page (/)
 * Public page shown to unauthenticated users
 */
export class LandingPage extends BasePage {
  readonly heroTitle: Locator;
  readonly heroSubtitle: Locator;
  readonly getStartedButton: Locator;
  readonly loginButton: Locator;
  readonly featureCards: Locator;
  readonly logo: Locator;

  constructor(page: Page) {
    super(page);
    
    this.heroTitle = page.getByRole('heading', { level: 1 }).first();
    this.heroSubtitle = page.locator('p').filter({ hasText: /learn|language|watch/i }).first();
    this.getStartedButton = page.getByRole('button', { name: /get started|sign up|register/i }).or(
      page.getByRole('link', { name: /get started|sign up|register/i })
    );
    this.loginButton = page.getByRole('button', { name: /login|sign in/i }).or(
      page.getByRole('link', { name: /login|sign in/i })
    );
    this.featureCards = page.locator('[class*="feature"], [class*="card"]');
    this.logo = page.locator('[class*="logo"], img[alt*="logo"]').first();
  }

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.heroTitle.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickGetStarted() {
    await this.getStartedButton.click();
  }

  async clickLogin() {
    await this.loginButton.click();
  }

  async getHeroTitle(): Promise<string> {
    return await this.heroTitle.textContent() || '';
  }

  async getFeatureCount(): Promise<number> {
    return await this.featureCards.count();
  }
}
