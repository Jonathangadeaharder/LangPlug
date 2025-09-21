// ***********************************************
// Simple Puppeteer Authentication Test
// ***********************************************

import puppeteer, { Browser, Page } from 'puppeteer';
import { PuppeteerHelpers } from './utils/puppeteer-helpers';

async function runAuthTest() {
  let browser: Browser | undefined;
  let page: Page | undefined;
  
  try {
    console.log('Starting authentication test...');
    
    // Launch Puppeteer browser
    browser = await puppeteer.launch({
      headless: true,
      slowMo: 50,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    
    page = await browser.newPage();
    
    // Clear any existing sessions/cookies
    await PuppeteerHelpers.clearAllStorage(page);
    
    // Navigate to login page
    await page.goto('http://localhost:3001/login');
    
    // Check if login form is visible
    await page.waitForSelector('input[placeholder="Username"]', { visible: true });
    await page.waitForSelector('input[placeholder="Password"]', { visible: true });
    
    console.log('Login form is visible');
    
    // Test navigation to register page
    await page.click('text=Sign up now');
    await page.waitForFunction(() => window.location.href.includes('/register'));
    
    console.log('Navigation to register page works');
    
    console.log('Authentication test completed successfully! ✅');
    return true;
  } catch (error) {
    console.error('Authentication test failed:', error);
    return false;
  } finally {
    // Close browser if it was created
    if (browser) {
      await browser.close();
    }
  }
}

// Run the test
runAuthTest().then(success => {
  process.exit(success ? 0 : 1);
});