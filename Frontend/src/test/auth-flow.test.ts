// ***********************************************
// Puppeteer Authentication Flow Tests
// ***********************************************

import puppeteer, { Browser, Page } from 'puppeteer';
import { spawn } from 'child_process';
import { expect, test } from 'vitest';

describe('Authentication Flow', () => {
  let browser: Browser | undefined;
  let page: Page;
  let serverProcess: ReturnType<typeof spawn> | undefined;

  const BASE_URL = 'http://localhost:3000';
  const SERVER_STARTUP_TIMEOUT = 60000; // 60 seconds for safety

  // Polling function to check if server is ready
  const waitForServer = async (timeout: number): Promise<void> => {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      try {
        const response = await fetch(BASE_URL);
        if (response.ok) {
          return;
        }
      } catch (error) {
        // Server not ready yet, continue polling
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    throw new Error('Server startup timeout');
  };

  beforeAll(async () => {
    // Kill any processes on port 3000 to ensure it's free
    try {
      await new Promise<void>((resolve, reject) => {
        const killProcess = spawn('npx', ['kill-port', '3000'], {
          cwd: process.cwd(),
          stdio: 'pipe',
          shell: true,
        });

        killProcess.on('close', (code) => {
          if (code === 0 || code === 1) { // kill-port returns 1 if no process found, which is fine
            resolve();
          } else {
            reject(new Error(`Failed to kill port 3000, exit code: ${code}`));
          }
        });

        killProcess.on('error', reject);
      });
      console.log('Cleared port 3000');
    } catch (error) {
      console.warn('Could not clear port 3000, proceeding anyway:', error);
    }

    // Start the Vite dev server automatically using npm run dev
    serverProcess = spawn('npm', ['run', 'dev'], {
      cwd: process.cwd(),
      stdio: 'pipe',
      shell: true,
    });

    // Attach listeners immediately to catch all output
    serverProcess.stdout?.on('data', (data) => {
      console.log(`Server stdout: ${data.toString()}`);
    });
    serverProcess.stderr?.on('data', (data) => {
      console.error(`Server stderr: ${data.toString()}`);
    });

    // Wait for server to be ready using polling
    await waitForServer(SERVER_STARTUP_TIMEOUT);

    // Launch Puppeteer browser
    browser = await puppeteer.launch({
      headless: true, // Use headless mode
      slowMo: 100, // Slow down for better test visibility/debugging
      args: ['--no-sandbox', '--disable-setuid-sandbox'], // For CI/headless
    });
  }, SERVER_STARTUP_TIMEOUT + 10000);

  beforeEach(async () => {
    if (!browser) throw new Error('Browser not initialized');
    page = await browser.newPage();
    // Clear any existing sessions/cookies
    await page.deleteCookie(...(await page.cookies()));
    await page.goto(BASE_URL);
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
    // Kill server process if it was started
    if (serverProcess) {
      serverProcess.kill();
    }
  });

  // Helper function to wait for text visibility
  const waitForText = async (text: string, timeout = 5000) => {
    await page.waitForFunction(
      (t) => document.body.textContent?.includes(t),
      { timeout },
      text
    );
  };

  // Helper function to click element by text
  const clickByText = async (text: string, selector = 'button, a, span') => {
    await page.waitForFunction(
      (t, s) => Array.from(document.querySelectorAll(s)).some(el => el.textContent?.includes(t)),
      { timeout: 5000 },
      text, selector
    );
    await page.evaluate((t, s) => {
      const elements = Array.from(document.querySelectorAll(s));
      const element = elements.find(el => el.textContent?.includes(t));
      if (element && 'click' in element) {
        (element as HTMLElement).click();
      }
    }, text, selector);
  };

  test('should display login form and allow navigation to register', async () => {
    await page.goto(`${BASE_URL}/login`);

    // Should see login form elements
    await waitForText('Sign In');
    await page.waitForSelector('input[placeholder="Username"]', { visible: true });
    await page.waitForSelector('input[placeholder="Password"]', { visible: true });
    await waitForText('Sign In'); // For button

    // Should be able to navigate to register
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'load' }),
      clickByText('Sign up now')
    ]);
    expect(page.url()).toMatch(/\/register$/);
  }, 30000);

  test('should handle invalid login credentials', async () => {
    await page.goto(`${BASE_URL}/login`);

    await page.type('input[placeholder="Username"]', 'invaliduser');
    await page.type('input[placeholder="Password"]', 'wrongpassword');
    await clickByText('Sign In');

    // Wait for potential error handling (e.g., API call or validation)
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Should stay on login page with form still visible
    expect(page.url()).toContain('/login');
    await waitForText('Sign In');
  }, 30000);

  test('should redirect to login when accessing protected routes', async () => {
    // Try to access a protected route without auth (assuming '/' is protected)
    await page.goto(BASE_URL);

    // Wait for potential redirect
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Should redirect to login
    expect(page.url()).toContain('/login');
    await waitForText('Sign In');
  }, 30000);
});