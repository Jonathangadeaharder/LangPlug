import { defineConfig, devices } from '@playwright/test';
import * as path from 'path';

/**
 * Smoke Test Configuration for E2E Tests
 *
 * These tests are classified as @smoke and require manual setup:
 * 1. Backend server running on localhost:8001
 * 2. Frontend server running on localhost:3001
 *
 * Run with: E2E_SMOKE_TESTS=1 npm run playwright:smoke
 */
export default defineConfig({
  testDir: './workflows',
  timeout: 120000, // Longer timeout for smoke tests
  expect: {
    timeout: 15000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0, // No retries in manual mode
  workers: 1, // Single worker for smoke tests

  // Only run tests marked with @smoke
  grep: /@smoke/,

  reporter: [
    ['html', { outputFolder: 'smoke-test-report' }],
    ['json', { outputFile: 'test-results/smoke-test-results.json' }],
    ['line']
  ],

  use: {
    // Expect servers to be manually started
    baseURL: process.env.FRONTEND_URL || 'http://localhost:3001',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 30000,
    navigationTimeout: 30000,
  },

  projects: [
    {
      name: 'smoke-chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  outputDir: 'smoke-test-results/',
});
