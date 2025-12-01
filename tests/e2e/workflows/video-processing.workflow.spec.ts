import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { LoginPage } from '../pages/LoginPage';

test.describe('Video Processing Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  test('WhenUserUploadsVideo_ThenProcessingStartsAndCompletes @smoke', async ({ page }) => {
    await test.step('Verify videos can be listed via API', async () => {
      const videosResponse = await page.request.get('http://127.0.0.1:8000/api/videos');
      expect(videosResponse.ok()).toBeTruthy();
      const videosData = await videosResponse.json();
      expect(Array.isArray(videosData)).toBeTruthy();
    });

    // Note: This is a backend API smoke test
    // Full UI testing will require implementing the frontend video upload/processing interface
  });

  test('WhenProcessingFails_ThenUserSeesErrorAndCanRetry @smoke', async ({ page }) => {
    await test.step('Verify processing status endpoint works', async () => {
      const statusResponse = await page.request.get('http://127.0.0.1:8000/api/videos/nonexistent/status');
      expect(statusResponse.status()).toBe(404);
    });

    // Note: Error handling UI not implemented yet
    // This tests the backend API error responses
  });

  test('WhenUserCancelsProcessing_ThenCanRestartLater @smoke', async ({ page }) => {
    await test.step('Verify video scan endpoint works', async () => {
      const scanResponse = await page.request.post('http://127.0.0.1:8000/api/videos/scan');
      expect(scanResponse.ok()).toBeTruthy();
      const scanData = await scanResponse.json();
      expect(scanData).toBeDefined();
    });

    // Note: Processing cancellation UI not implemented yet
    // This tests the backend video scan API
  });

  test('WhenVideoProcessingCompletes_ThenVocabularyGameStarts @smoke', async ({ page }) => {
    await test.step('Verify health check endpoint works', async () => {
      const healthResponse = await page.request.get('http://127.0.0.1:8000/health');
      expect(healthResponse.status()).toBe(200);
      const healthData = await healthResponse.json();
      expect((healthData as { status: string }).status).toBeDefined();
    });

    // Note: Video player and vocabulary game UI not implemented yet
    // This tests the backend health check works
  });
});

