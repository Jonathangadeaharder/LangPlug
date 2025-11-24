import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: process.env.CI ? true : false,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 2,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['list'],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
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
  ],

  // webServer is disabled - start backends manually before running tests
  // webServer: [
  //   {
  //     command: 'npm run dev',
  //     url: 'http://localhost:3000',
  //     reuseExistingServer: !process.env.CI,
  //     cwd: './src/frontend',
  //   },
  //   {
  //     command: 'python run_backend.py',
  //     url: 'http://localhost:8000/health',
  //     reuseExistingServer: !process.env.CI,
  //     cwd: './src/backend',
  //     env: {
  //       LANGPLUG_PORT: '8000',
  //       LANGPLUG_RELOAD: '0',
  //       LANGPLUG_TRANSCRIPTION_SERVICE: 'whisper-tiny',
  //       LANGPLUG_TRANSLATION_SERVICE: 'opus-de-es',
  //       LANGPLUG_DEFAULT_LANGUAGE: 'de',
  //     },
  //   },
  // ],
});
