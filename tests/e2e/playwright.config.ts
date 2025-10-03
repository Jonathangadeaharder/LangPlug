import { defineConfig, devices } from '@playwright/test';
import * as path from 'path';

export default defineConfig({
  testDir: './workflows',
  timeout: 60000,
  expect: {
    timeout: 10000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 1,
  // Mark E2E tests as manual/smoke - skip in CI unless explicitly enabled
  grep: process.env.E2E_SMOKE_TESTS ? undefined : /^(?!.*@smoke).*$/,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/playwright-results.json' }],
    ['line']
  ],
  use: {
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 30000,
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  outputDir: 'test-results/',
  // Commented out - violates process isolation rules
  // globalSetup: path.resolve(__dirname, 'setup/global-setup.ts'),
  // globalTeardown: path.resolve(__dirname, 'setup/global-teardown.ts'),
});
