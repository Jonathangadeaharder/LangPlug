import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class ChunkedLearningPage extends BasePage {
  // Processing phase
  readonly processingIndicator: Locator;
  readonly progressBar: Locator;
  readonly progressText: Locator;
  
  // Video player phase
  readonly videoPlayer: Locator;
  readonly playPauseButton: Locator;
  readonly subtitleDisplay: Locator;
  readonly nextChunkButton: Locator;
  readonly previousChunkButton: Locator;
  
  // Vocabulary game phase
  readonly vocabularyGame: Locator;
  readonly wordDisplay: Locator;
  readonly knowButton: Locator;
  readonly dontKnowButton: Locator;
  readonly translationDisplay: Locator;
  readonly difficultyBadge: Locator;
  readonly skipRemainingButton: Locator;
  readonly gameProgressText: Locator;
  readonly gameCompletionScreen: Locator;
  readonly emptyStateScreen: Locator;
  readonly continueWatchingButton: Locator;
  
  // Common elements
  readonly backButton: Locator;
  readonly chunkIndicator: Locator;
  readonly errorMessage: Locator;
  readonly noVideoMessage: Locator;

  constructor(page: Page) {
    super(page);
    
    // Processing phase locators - matches ProcessingScreen.tsx
    this.processingIndicator = page.getByRole('heading', { name: 'Processing Episode' }).or(
      page.getByText('Preparing your learning experience...')
    ).first();
    this.progressBar = page.locator('[data-testid="progress-bar"]').or(
      page.locator('[role="progressbar"]')
    );
    this.progressText = page.locator('[data-testid="progress-text"]').or(
      page.getByText(/\d+%/)
    );
    
    // Video player locators
    this.videoPlayer = page.locator('video').or(
      page.locator('[data-testid="video-player"]')
    );
    this.playPauseButton = page.getByRole('button', { name: /play|pause/i });
    this.subtitleDisplay = page.locator('[data-testid="subtitles"]').or(
      page.locator('.subtitles').or(
        page.locator('[class*="subtitle"]')
      )
    );
    this.nextChunkButton = page.getByRole('button', { name: /next|continue/i });
    this.previousChunkButton = page.getByRole('button', { name: /previous|back/i });
    
    // Vocabulary game locators - using actual data-testid from VocabularyGame.tsx
    this.vocabularyGame = page.getByText('Vocabulary Check').or(
      page.getByText('Do you know this word?')
    );
    this.wordDisplay = page.locator('[data-testid="vocabulary-word"]');
    this.knowButton = page.locator('[data-testid="mark-known-button"]');
    this.dontKnowButton = page.locator('[data-testid="mark-unknown-button"]');
    this.translationDisplay = page.locator('[data-testid="translation"]');
    this.difficultyBadge = page.locator('[data-testid="difficulty-badge"]');
    this.skipRemainingButton = page.locator('[data-testid="skip-remaining-button"]');
    this.gameProgressText = page.getByText(/\d+ of \d+ words/);
    this.gameCompletionScreen = page.locator('[data-testid="success-message"]');
    this.emptyStateScreen = page.locator('[data-testid="empty-state"]');
    this.continueWatchingButton = page.getByRole('button', { name: /continue watching|watch this segment/i });
    
    // Common locators
    this.backButton = page.locator('[data-testid="back-button"]').or(
      page.getByRole('button', { name: /back|exit/i })
    );
    this.chunkIndicator = page.locator('[data-testid="chunk-indicator"]').or(
      page.getByText(/chunk|part|segment/i)
    );
    this.errorMessage = page.locator('[data-testid="error"]').or(
      page.getByRole('alert')
    );
    this.noVideoMessage = page.getByText(/video information not found|go back/i);
  }

  async gotoLearn(series: string, episode: string) {
    await this.page.goto(`/learn/${encodeURIComponent(series)}/${encodeURIComponent(episode)}`);
    await this.page.waitForLoadState('networkidle');
  }

  async goto() {
    // Learning page requires series and episode params
    throw new Error('Use gotoLearn(series, episode) instead');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForLoadState('networkidle');
      // Check if any learning phase is visible
      const isProcessing = await this.processingIndicator.isVisible();
      const isPlaying = await this.videoPlayer.isVisible();
      const isGame = await this.vocabularyGame.isVisible();
      const hasError = await this.noVideoMessage.isVisible();
      
      return isProcessing || isPlaying || isGame || hasError;
    } catch {
      return false;
    }
  }

  // Phase detection
  async getCurrentPhase(): Promise<'processing' | 'video' | 'game' | 'error' | 'unknown'> {
    try {
      if (await this.noVideoMessage.isVisible()) return 'error';
    } catch { /* ignore */ }
    
    try {
      if (await this.processingIndicator.isVisible()) return 'processing';
    } catch { /* ignore */ }
    
    try {
      if (await this.videoPlayer.isVisible()) return 'video';
    } catch { /* ignore */ }
    
    try {
      if (await this.vocabularyGame.isVisible()) return 'game';
    } catch { /* ignore */ }
    
    try {
      if (await this.wordDisplay.isVisible()) return 'game';
    } catch { /* ignore */ }
    
    return 'unknown';
  }

  async waitForPhase(phase: 'processing' | 'video' | 'game', timeout = 60000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      const currentPhase = await this.getCurrentPhase();
      if (currentPhase === phase) return;
      await this.page.waitForTimeout(1000);
    }
    throw new Error(`Timeout waiting for phase: ${phase}`);
  }

  // Processing phase actions
  async getProcessingProgress(): Promise<number> {
    const text = await this.progressText.textContent();
    const match = text?.match(/(\d+)%/);
    return match ? parseInt(match[1]) : 0;
  }

  async waitForProcessingComplete(timeout = 120000) {
    await this.waitForPhase('game', timeout);
  }

  // Video phase actions
  async playVideo() {
    await this.playPauseButton.click();
  }

  async pauseVideo() {
    await this.playPauseButton.click();
  }

  async goToNextChunk() {
    await this.nextChunkButton.click();
  }

  async goToPreviousChunk() {
    await this.previousChunkButton.click();
  }

  // Vocabulary game actions
  async markWordAsKnown() {
    await this.knowButton.click();
  }

  async markWordAsUnknown() {
    await this.dontKnowButton.click();
  }

  async getCurrentWord(): Promise<string> {
    return await this.wordDisplay.textContent() || '';
  }

  async getTranslation(): Promise<string> {
    return await this.translationDisplay.textContent() || '';
  }

  async completeVocabularyGame(markAllAsKnown = true) {
    // Complete all words in the current game
    let attempts = 0;
    const maxAttempts = 50;
    const wordsAnswered: string[] = [];
    
    while (attempts < maxAttempts) {
      // Check if game is complete
      const isComplete = await this.gameCompletionScreen.isVisible().catch(() => false);
      const isEmpty = await this.emptyStateScreen.isVisible().catch(() => false);
      
      if (isComplete || isEmpty) {
        break;
      }
      
      const knowButtonVisible = await this.knowButton.isVisible().catch(() => false);
      
      if (!knowButtonVisible) {
        // Game might be complete or phase changed
        break;
      }
      
      // Get current word before answering
      const currentWord = await this.getCurrentWord();
      if (currentWord) {
        wordsAnswered.push(currentWord);
      }
      
      // Mark word as known or unknown based on parameter
      if (markAllAsKnown) {
        await this.knowButton.click();
      } else {
        await this.dontKnowButton.click();
      }
      
      await this.page.waitForTimeout(400);
      attempts++;
    }
    
    return wordsAnswered;
  }

  async skipRemainingWords() {
    await this.skipRemainingButton.click();
  }

  async isGameComplete(): Promise<boolean> {
    return await this.gameCompletionScreen.isVisible().catch(() => false);
  }

  async isGameEmpty(): Promise<boolean> {
    return await this.emptyStateScreen.isVisible().catch(() => false);
  }

  async getGameProgress(): Promise<{ current: number; total: number } | null> {
    const text = await this.gameProgressText.textContent().catch(() => null);
    if (!text) return null;
    
    const match = text.match(/(\d+) of (\d+) words/);
    if (match) {
      return { current: parseInt(match[1]), total: parseInt(match[2]) };
    }
    return null;
  }

  async getDifficultyLevel(): Promise<string> {
    return await this.difficultyBadge.textContent() || '';
  }

  async waitForGameToStart(timeout = 120000) {
    // Wait for vocabulary game to appear after processing
    await this.wordDisplay.waitFor({ state: 'visible', timeout });
  }

  async clickContinueWatching() {
    await this.continueWatchingButton.click();
  }

  // Navigation
  async exitLearning() {
    await this.backButton.click();
  }
}
