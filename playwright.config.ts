import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright Configuration with Best Practices:
 * 1. Auth Setup Project - authenticate once, reuse state
 * 2. Parallel execution with sharding support
 * 3. CI-optimized settings
 */
export default defineConfig({
  testDir: './tests/e2e',
  testMatch: ['features/**/*.spec.ts', 'workflows/**/*.spec.ts', 'integration/**/*.spec.ts'],

  // Best Practice #5: Parallel execution
  fullyParallel: false, // Disable parallelism per user request
  forbidOnly: process.env.CI ? true : false,
  retries: process.env.CI ? 2 : 0, // No retries locally - stop at first error
  workers: 1, // Use 1 worker per user request
  maxFailures: 1, // Stop at first error

  // Best Practice #5: Sharding support
  // Run with: npx playwright test --shard=1/3

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['json', { outputFile: 'test-results.json' }],
    ['list'],
  ],

  // Best Practice: Global assertion timeout
  globalTimeout: 10 * 60 * 1000, // 10 minutes max for entire suite
  expect: {
    timeout: 10000, // 10s for all expect() calls
  },

  use: {
    baseURL: process.env.E2E_FRONTEND_URL || 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',

    // Performance optimizations
    launchOptions: {
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu',
      ],
    },

    // Best Practice #4: Reasonable timeouts
    actionTimeout: 15000,   // 15s for clicks, fills, etc.
    navigationTimeout: 30000, // 30s for page navigation
  },

  projects: [
    // Best Practice #1: Auth Setup Project (runs first)
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Authenticated tests (depend on setup)
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Best Practice #1: Reuse auth state
        storageState: path.join(__dirname, 'tests/playwright/.auth/user.json'),
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        storageState: path.join(__dirname, 'tests/playwright/.auth/user.json'),
      },
      dependencies: ['setup'],
    },

    // Unauthenticated tests (for login/register testing)
    {
      name: 'chromium-no-auth',
      testMatch: /auth.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: undefined, // No pre-auth for auth tests
      },
    },
    // Workflow tests (handle their own authentication)
    {
      name: 'chromium-workflows',
      testMatch: /workflows\/.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: undefined, // Workflows handle their own auth
      },
    },
  ],

  // webServer is enabled to ensure services are running
  webServer: process.env.E2E_FRONTEND_URL ? undefined : [
    {
      command: 'npm run dev',
      url: 'http://127.0.0.1:3000',
      reuseExistingServer: !process.env.CI,
      cwd: './src/frontend',
      timeout: 120 * 1000,
    },
  ],
});
