import { defineConfig, devices } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

/**
 * Playwright Configuration for LangPlug Frontend E2E Tests
 *
 * Layer 7: Browser Experience Validation
 * Tests validate actual React rendering, user interactions, and complete UI workflows
 *
 * Uses start-all.bat script to launch both backend and frontend servers
 */

// Get __dirname equivalent in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  testDir: './tests/e2e',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter to use */
  reporter: 'html',

  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: 'http://localhost:3000',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video on failure */
    video: 'retain-on-failure',
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Start backend server directly using venv Python */
  webServer: [
    {
      command: `"${path.resolve(__dirname, '..', 'backend', 'api_venv', 'Scripts', 'python.exe')}" "${path.resolve(__dirname, '..', 'backend', 'run_backend.py')}"`,
      url: 'http://localhost:8000/health',
      cwd: path.resolve(__dirname, '..', 'backend'),
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
      stdout: 'pipe',
      stderr: 'pipe',
      env: {
        ...process.env,
        TESTING: '1',
        LANGPLUG_PORT: '8000',
        LANGPLUG_DATABASE_URL: 'sqlite+aiosqlite:///./test.db',
        LANGPLUG_TRANSCRIPTION_SERVICE: 'whisper-tiny',
        LANGPLUG_TRANSLATION_SERVICE: 'opus-de-es',
        LANGPLUG_RELOAD: 'false',
      },
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      cwd: path.resolve(__dirname),
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
