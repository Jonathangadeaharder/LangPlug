// ***********************************************
// Simple Puppeteer Vocabulary Test
// ***********************************************

import puppeteer, { Browser, Page } from 'puppeteer';
import { PuppeteerHelpers } from './utils/puppeteer-helpers';

async function runVocabularyTest() {
  let browser: Browser | undefined;
  let page: Page | undefined;
  
  try {
    console.log('Starting vocabulary game test...');
    
    // Launch Puppeteer browser
    browser = await puppeteer.launch({
      headless: true,
      slowMo: 50,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    
    page = await browser.newPage();
    
    // Clear any existing sessions/cookies
    await PuppeteerHelpers.clearAllStorage(page);
    
    // Seed test data
    await PuppeteerHelpers.seedTestData();
    
    // Navigate to vocabulary game
    const BASE_URL = 'http://localhost:3001';
    await page.goto(`${BASE_URL}/vocabulary/game`);
    
    // Start vocabulary game
    await page.waitForSelector('[data-testid="start-game-button"]', { visible: true });
    await page.click('[data-testid="start-game-button"]');
    
    // Should show game interface
    await page.waitForSelector('[data-testid="game-interface"]', { visible: true });
    await page.waitForSelector('[data-testid="game-question"]', { visible: true });
    
    console.log('Vocabulary game page loaded successfully');
    
    // Test passed
    console.log('Vocabulary test completed successfully! ✅');
    return true;
  } catch (error) {
    console.error('Vocabulary test failed:', error);
    return false;
  } finally {
    // Clean test data
    await PuppeteerHelpers.cleanTestData();
    
    // Close browser if it was created
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test
runVocabularyTest().then(success => {
  process.exit(success ? 0 : 1);
});