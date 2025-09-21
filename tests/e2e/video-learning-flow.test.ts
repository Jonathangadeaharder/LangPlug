// ***********************************************
// Puppeteer Video Learning Flow Tests
// ***********************************************

import puppeteer, { Browser, Page } from 'puppeteer';
import { PuppeteerHelpers } from './utils/puppeteer-helpers';

describe('Video Learning Flow', () => {
  let browser: Browser | undefined;
  let page: Page;

  const BASE_URL = 'http://localhost:3000';

  beforeAll(async () => {
    // Launch Puppeteer browser
    browser = await puppeteer.launch({
      headless: true,
      slowMo: 50,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
  }, 60000);

  beforeEach(async () => {
    if (!browser) throw new Error('Browser not initialized');
    page = await browser.newPage();
    // Clear any existing sessions/cookies
    await PuppeteerHelpers.clearAllStorage(page);
    
    // Seed test data
    await PuppeteerHelpers.seedTestData();
  });

  afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  afterAll(async () => {
    // Close browser if it was created
    if (browser) {
      await browser.close();
    }
    
    // Clean test data
    await PuppeteerHelpers.cleanTestData();
  });

  test('should complete full video learning workflow', async () => {
    // Navigate to video library
    await page.goto(`${BASE_URL}/videos`);
    await page.waitForSelector('[data-testid="video-library"]', { visible: true });
    
    // Select a video
    await page.waitForSelector('[data-testid="video-card"]', { visible: true });
    await page.click('[data-testid="video-card"]');
    
    // Should navigate to video player
    await page.waitForFunction(() => window.location.href.includes('/videos/'));
    await page.waitForSelector('[data-testid="video-player"]', { visible: true });
    
    // Play video
    await page.click('[data-testid="play-button"]');
    const playingState = await page.$eval('[data-testid="video-player"]', el => el.getAttribute('data-playing'));
    expect(playingState).toBe('true');
    
    // Check subtitles are available
    await page.click('[data-testid="subtitle-toggle"]');
    await page.waitForSelector('[data-testid="subtitles"]', { visible: true });
    
    // Interact with vocabulary features
    await page.click('[data-testid="vocabulary-panel-toggle"]');
    await page.waitForSelector('[data-testid="vocabulary-panel"]', { visible: true });
    
    // Mark a word as known
    const firstWordSelector = '[data-testid="vocabulary-word"]';
    await page.waitForSelector(firstWordSelector, { visible: true });
    await page.click(`${firstWordSelector} [data-testid="mark-known-button"]`);
    
    // Verify word is marked as known
    const knownState = await page.$eval(firstWordSelector, el => el.getAttribute('data-known'));
    expect(knownState).toBe('true');
    
    // Check progress tracking
    await page.waitForSelector('[data-testid="progress-indicator"]', { visible: true });
    const progressText = await page.$eval('[data-testid="progress-percentage"]', el => el.textContent);
    expect(progressText).not.toContain('0%');
  }, 30000);

  test('should handle video upload workflow', async () => {
    await page.goto(`${BASE_URL}/upload`);
    
    // Check that all upload elements are present
    await page.waitForSelector('[data-testid="video-upload-input"]', { visible: true });
    await page.waitForSelector('[data-testid="video-title-input"]', { visible: true });
    await page.waitForSelector('[data-testid="video-series-input"]', { visible: true });
    await page.waitForSelector('[data-testid="upload-button"]', { visible: true });
    
    // Fill in metadata
    await page.type('[data-testid="video-title-input"]', 'Test Video');
    await page.type('[data-testid="video-series-input"]', 'Test Series');
    
    // Note: Actual file upload testing would require:
    // 1. A test video file
    // 2. Mocking the file input or using a real file
    // 3. Waiting for upload progress and completion
    // For now, we'll just verify the UI elements
    
    console.log('Video upload page loads and metadata fields work correctly');
  }, 30000);

  test('should handle vocabulary learning game', async () => {
    await page.goto(`${BASE_URL}/vocabulary/game`);
    
    // Start vocabulary game
    await page.waitForSelector('[data-testid="start-game-button"]', { visible: true });
    await page.click('[data-testid="start-game-button"]');
    
    // Should show game interface
    await page.waitForSelector('[data-testid="game-interface"]', { visible: true });
    await page.waitForSelector('[data-testid="game-question"]', { visible: true });
    
    // Answer a few questions (just click first option for testing)
    for (let i = 0; i < 3; i++) {
      await page.waitForSelector('[data-testid="game-option"]', { visible: true });
      await page.click('[data-testid="game-option"]');
      
      // Wait for next question or results
      try {
        await page.waitForSelector('[data-testid="next-question-button"]', { timeout: 5000 });
        await page.click('[data-testid="next-question-button"]');
      } catch (e) {
        // If next button doesn't appear, we might be at results
        break;
      }
    }
    
    // Should show results
    await page.waitForSelector('[data-testid="game-results"]', { visible: true });
    await page.waitForSelector('[data-testid="game-score"]', { visible: true });
    
    // Should update user progress
    await page.goto(`${BASE_URL}/profile`);
    await page.waitForSelector('[data-testid="vocabulary-stats"]', { visible: true });
  }, 30000);

  test('should handle subtitle filtering and processing', async () => {
    await page.goto(`${BASE_URL}/videos`);
    
    // Select video with subtitles
    await page.waitForSelector('[data-testid="video-card"]', { visible: true });
    await page.click('[data-testid="video-card"]');
    
    // Open subtitle tools
    await page.waitForSelector('[data-testid="subtitle-tools-button"]', { visible: true });
    await page.click('[data-testid="subtitle-tools-button"]');
    await page.waitForSelector('[data-testid="subtitle-tools-panel"]', { visible: true });
    
    // Filter subtitles by difficulty
    await page.select('[data-testid="difficulty-filter"]', 'beginner');
    await page.click('[data-testid="apply-filter-button"]');
    
    // Should show filtered subtitles
    await page.waitForSelector('[data-testid="filtered-subtitles"]', { visible: true });
    const subtitleCount = await page.$$eval('[data-testid="subtitle-segment"]', elements => elements.length);
    expect(subtitleCount).toBeGreaterThan(0);
  }, 30000);
});