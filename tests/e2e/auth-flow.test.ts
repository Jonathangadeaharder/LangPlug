// ***********************************************
// Puppeteer Authentication Flow Tests
// ***********************************************

import puppeteer, { Browser, Page } from 'puppeteer';
import { PuppeteerHelpers } from './utils/puppeteer-helpers';

describe('Authentication Flow', () => {
  let browser: Browser | undefined;
  let page: Page;

  const BASE_URL = 'http://localhost:3000';
  const TEST_USER_EMAIL = 'test@example.com';
  const TEST_USER_PASSWORD = 'TestPassword123!';

  beforeAll(async () => {
    // Launch Puppeteer browser
    browser = await puppeteer.launch({
      headless: true, // Use headless mode
      slowMo: 50, // Slow down for better test visibility/debugging
      args: ['--no-sandbox', '--disable-setuid-sandbox'], // For CI/headless
    });
  }, 60000);

  beforeEach(async () => {
    if (!browser) throw new Error('Browser not initialized');
    page = await browser.newPage();
    // Clear any existing sessions/cookies
    await PuppeteerHelpers.clearAllStorage(page);
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
  });

  test('should display login form and allow navigation to register', async () => {
    await page.goto(`${BASE_URL}/login`);

    // Should see login form elements
    await PuppeteerHelpers.waitForText(page, 'Sign In');
    await page.waitForSelector('input[placeholder="Username"]', { visible: true });
    await page.waitForSelector('input[placeholder="Password"]', { visible: true });
    await PuppeteerHelpers.waitForText(page, 'Sign In'); // For button

    // Should be able to navigate to register
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'load' }),
      PuppeteerHelpers.clickByText(page, 'Sign up now')
    ]);
    expect(page.url()).toMatch(/\/register$/);
  }, 30000);

  test('should handle invalid login credentials', async () => {
    await page.goto(`${BASE_URL}/login`);

    await page.type('input[placeholder="Username"]', 'invaliduser');
    await page.type('input[placeholder="Password"]', 'wrongpassword');
    await PuppeteerHelpers.clickByText(page, 'Sign In');

    // Wait for potential error handling (e.g., API call or validation)
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Should stay on login page with form still visible
    expect(page.url()).toContain('/login');
    await PuppeteerHelpers.waitForText(page, 'Sign In');
 }, 30000);

  test('should redirect to login when accessing protected routes', async () => {
    // Try to access a protected route without auth (assuming '/' is protected)
    await page.goto(BASE_URL);

    // Wait for potential redirect
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Should redirect to login
    expect(page.url()).toContain('/login');
    await PuppeteerHelpers.waitForText(page, 'Sign In');
  }, 300);
});