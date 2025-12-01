import { Page, Locator, expect } from '@playwright/test';
import { TIMEOUTS } from '../config/timeouts';
import { Header } from './components/Header';

/**
 * Base Page Object Model with common utility methods.
 * Follows Playwright best practices.
 */
export abstract class BasePage {
  readonly header: Header;

  constructor(protected page: Page) {
    this.header = new Header(page);
  }

  abstract goto(): Promise<void>;
  abstract isLoaded(): Promise<boolean>;

  /**
   * Waits for the page to be fully loaded.
   * Uses domcontentloaded state + a check for a key element.
   */
  async waitForLoad() {
    await this.page.waitForLoadState('domcontentloaded');
    await this.isLoaded();
  }

  /**
   * Robustly navigates to a URL and waits for load.
   */
  async navigateTo(path: string) {
    await this.page.goto(path);
    await this.waitForLoad();
  }

  /**
   * Safe check if an element is visible without throwing.
   */
  async isVisible(selector: string | Locator): Promise<boolean> {
    if (typeof selector === 'string') {
      return this.page.isVisible(selector);
    }
    return selector.isVisible();
  }

  async getCurrentUrl(): Promise<string> {
    return this.page.url();
  }
}
