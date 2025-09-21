// ***********************************************
// Simple Puppeteer Video Test
// ***********************************************

import puppeteer, { Browser, Page } from 'puppeteer';
import { PuppeteerHelpers } from './utils/puppeteer-helpers';

async function runVideoTest() {
  let browser: Browser | undefined;
  let page: Page | undefined;
  
  try {
    console.log('Starting video learning test...');
    
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
    
    // Navigate to video library
    const BASE_URL = 'http://localhost:3001';
    await page.goto(`${BASE_URL}/videos`);
    await page.waitForSelector('[data-testid="video-library"]', { visible: true });
    
    console.log('Video library page loaded successfully');
    
    // Test passed
    console.log('Video test completed successfully! ✅');
    return true;
  } catch (error) {
    console.error('Video test failed:', error);
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
runVideoTest().then(success => {
  process.exit(success ? 0 : 1);
});