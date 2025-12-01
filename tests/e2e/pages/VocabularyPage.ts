import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { ROUTES } from '../config/urls';
import { TIMEOUTS } from '../config/timeouts';

export class VocabularyPage extends BasePage {
  readonly backButton: Locator;
  readonly searchInput: Locator;
  readonly loadingIndicator: Locator;
  readonly addWordButton: Locator;

  constructor(page: Page) {
    super(page);
    this.backButton = page.getByTestId('back-to-videos');
    this.searchInput = page.getByTestId('vocabulary-search');
    this.loadingIndicator = page.getByTestId('vocabulary-loading');
    this.addWordButton = page.getByRole('button', { name: '+' });
  }

  async goto() {
    await this.page.goto(ROUTES.VOCABULARY);
    await this.waitForLoad();
  }

  async isLoaded(): Promise<boolean> {
    // Wait for either the search input OR a level tab
    try {
      await Promise.race([
        expect(this.searchInput).toBeVisible({ timeout: TIMEOUTS.ELEMENT_VISIBLE }),
        expect(this.page.getByText('Vocabulary Library')).toBeVisible({ timeout: TIMEOUTS.ELEMENT_VISIBLE })
      ]);
      return true;
    } catch {
      return false;
    }
  }

  async clickBackToVideos() {
    await this.backButton.click();
  }

  async selectLevel(level: string) {
    // Robust selector: try testid first, then role with text
    const tab = this.page.getByTestId(`level-tab-${level}`)
      .or(this.page.getByRole('button', { name: new RegExp(level, 'i') }));
    await tab.click();
  }

  async isLevelActive(level: string): Promise<boolean> {
    try {
      // Check for text indicating the level is active (e.g., "A1 Level" heading)
      await expect(this.page.getByText(new RegExp(`${level}.*Level`, 'i'))).toBeVisible({ timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  async getWordCount(): Promise<number> {
    return await this.page.locator('[data-testid^="word-card-"]').count();
  }
}
