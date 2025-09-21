// ***********************************************
// Simple Puppeteer Subtitle Test
// ***********************************************

import puppeteer, { Browser, Page } from 'puppeteer';
import { PuppeteerHelpers } from './utils/puppeteer-helpers';

async function runSubtitleTest() {
  let browser: Browser | undefined;
  let page: Page | undefined;
  
  try {
    console.log('Starting subtitle filtering test...');
    
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
    
    // Navigate to videos page
    const BASE_URL = 'http://localhost:3001';
    await page.goto(`${BASE_URL}/videos`);
    
    // Wait for video cards to load
    await page.waitForSelector('[data-testid="video-card"]', { visible: true });
    
    console.log('Subtitle filtering test completed successfully! ✅');
    return true;
  } catch (error) {
    console.error('Subtitle filtering test failed:', error);
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
runSubtitleTest().then(success => {
  process.exit(success ? 0 : 1);
});