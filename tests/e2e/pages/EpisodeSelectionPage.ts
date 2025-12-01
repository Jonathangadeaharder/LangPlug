import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { Header } from './components/Header';

export class EpisodeSelectionPage extends BasePage {
  readonly header: Header;
  readonly backButton: Locator;
  readonly seriesTitle: Locator;
  readonly episodeCards: Locator;
  readonly playButtons: Locator;
  readonly loadingIndicator: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);
    this.header = new Header(page);
    // Back button says "Back to Series"
    this.backButton = page.getByRole('button', { name: /back to series/i });
    // Series title is the first h1 after header (e.g., "Fargo", "Superstore")
    this.seriesTitle = page.locator('h1').nth(1); // Skip "LangPlug" logo
    // Episode cards - look for elements containing "Episode X" pattern
    this.episodeCards = page.locator('text=/Episode \\d+/');
    // Play buttons - exact match for "Play" button text
    this.playButtons = page.getByRole('button', { name: 'Play' });
    this.loadingIndicator = page.locator('.loading-spinner');
    this.errorMessage = page.locator('[class*="ErrorMessage"]').or(
      page.getByRole('alert')
    );
  }

  async gotoSeries(seriesName: string) {
    await this.page.goto(`/episodes/${encodeURIComponent(seriesName)}`);
    await this.waitForLoad();
  }

  async goto() {
    // Default: navigate to episodes page requires a series name
    // Use gotoSeries() instead for specific series
    throw new Error('Use gotoSeries(seriesName) instead');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForLoadState('networkidle');
      // Either episodes visible or series title visible
      const hasContent = await this.seriesTitle.isVisible() || 
                         await this.episodeCards.first().isVisible();
      return hasContent;
    } catch {
      return false;
    }
  }

  async getSeriesTitle(): Promise<string> {
    return await this.seriesTitle.textContent() || '';
  }

  async getEpisodeCount(): Promise<number> {
    await this.page.waitForLoadState('networkidle');
    // Wait for at least one play button to appear
    try {
      await this.playButtons.first().waitFor({ state: 'visible', timeout: 5000 });
    } catch {
      // No play buttons found
      return 0;
    }
    return await this.playButtons.count();
  }

  async selectEpisode(episodeNumber: number) {
    // Click the play button for the specified episode
    await this.playButtons.nth(episodeNumber - 1).click();
  }

  async selectFirstEpisode() {
    // Wait for play buttons to be visible
    await this.playButtons.first().waitFor({ state: 'visible', timeout: 10000 });
    await this.playButtons.first().click();
  }

  async clickBack() {
    await this.backButton.click();
  }

  async hasEpisodesAvailable(): Promise<boolean> {
    await this.page.waitForLoadState('networkidle');
    return await this.playButtons.count() > 0;
  }

  async getEpisodeNames(): Promise<string[]> {
    const names: string[] = [];
    const count = await this.playButtons.count();
    for (let i = 0; i < count; i++) {
      names.push(`Episode ${i + 1}`);
    }
    return names;
  }

  async waitForEpisodesToLoad(timeout = 10000): Promise<void> {
    await this.page.waitForLoadState('networkidle');
    await this.playButtons.first().waitFor({ state: 'visible', timeout });
  }
}
