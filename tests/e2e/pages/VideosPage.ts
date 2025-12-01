import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { ROUTES } from '../config/urls';
import { Header } from './components/Header';

export class VideosPage extends BasePage {
  readonly vocabButton: Locator;
  readonly header: Header;
  readonly seriesCards: Locator;
  readonly loadingIndicator: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);
    // Use the actual data-testid from VideoSelection.tsx
    this.vocabButton = page.locator('[data-testid="vocabulary-nav"]');
    this.header = new Header(page);
    // Series cards have data-testid like "series-card-superstore", "series-card-fargo"
    this.seriesCards = page.locator('[data-testid^="series-card-"]');
    this.loadingIndicator = page.locator('.loading-spinner');
    this.errorMessage = page.locator('[class*="ErrorMessage"]').or(
      page.getByRole('alert')
    );
  }

  async goto() {
    await this.page.goto(ROUTES.VIDEOS);
    await this.waitForLoad();
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForLoadState('networkidle');
      // Either vocab button or series cards visible
      const hasContent = await this.vocabButton.isVisible() || 
                         await this.seriesCards.first().isVisible();
      return hasContent;
    } catch {
      return false;
    }
  }

  async clickVocabularyLibrary() {
    await this.vocabButton.click();
  }

  async getSeriesCount(): Promise<number> {
    await this.page.waitForLoadState('networkidle');
    return await this.seriesCards.count();
  }

  async selectSeries(seriesName: string) {
    // Use the exact data-testid format: series-card-{name-lowercase-hyphenated}
    const testId = seriesName.toLowerCase().replace(/\s+/g, '-');
    const seriesCard = this.page.locator(`[data-testid="series-card-${testId}"]`);
    await seriesCard.click();
  }

  async selectFirstSeries() {
    await this.seriesCards.first().click();
  }

  async hasSeriesAvailable(): Promise<boolean> {
    // Wait for loading to complete
    await this.page.waitForLoadState('networkidle');
    // Wait a bit for React to render
    await this.page.waitForTimeout(1000);
    return await this.seriesCards.count() > 0;
  }

  async waitForSeriesToLoad(timeout = 10000): Promise<void> {
    await this.page.waitForLoadState('networkidle');
    await this.seriesCards.first().waitFor({ state: 'visible', timeout });
  }

  async getSeriesNames(): Promise<string[]> {
    const count = await this.seriesCards.count();
    const names: string[] = [];
    for (let i = 0; i < count; i++) {
      const testId = await this.seriesCards.nth(i).getAttribute('data-testid');
      if (testId) {
        // Extract series name from "series-card-superstore" -> "Superstore"
        const name = testId.replace('series-card-', '').replace(/-/g, ' ');
        names.push(name);
      }
    }
    return names;
  }
}
