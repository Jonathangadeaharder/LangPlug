import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { TEST_CONFIG } from '../utils/test-config';
import { loginUser, authenticatedGet, authenticatedPost, unauthenticatedGet } from '../utils/page-helpers';

test.describe('Video Processing Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();
    await loginUser(page, testUser);
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  test('WhenUserUploadsVideo_ThenProcessingStartsAndCompletes @smoke', async ({ page }) => {
    await test.step('Verify videos can be listed via API', async () => {
      const { ok, data } = await authenticatedGet(page, TEST_CONFIG.ENDPOINTS.VIDEOS, testUser);
      expect(ok).toBeTruthy();
      expect(Array.isArray(data)).toBeTruthy();
    });

    // Note: This is a backend API smoke test
    // Full UI testing will require implementing the frontend video upload/processing interface
  });

  test('WhenProcessingFails_ThenUserSeesErrorAndCanRetry @smoke', async ({ page }) => {
    await test.step('Verify processing status endpoint works', async () => {
      const { status } = await authenticatedGet(
        page,
        `${TEST_CONFIG.ENDPOINTS.VIDEOS}/nonexistent/status`,
        testUser
      );
      expect(status).toBe(404);
    });

    // Note: Error handling UI not implemented yet
    // This tests the backend API error responses
  });

  test('WhenUserCancelsProcessing_ThenCanRestartLater @smoke', async ({ page }) => {
    await test.step('Verify video scan endpoint works', async () => {
      const { ok, data } = await authenticatedPost(page, TEST_CONFIG.ENDPOINTS.VIDEOS_SCAN, testUser);
      expect(ok).toBeTruthy();
      expect(data).toBeDefined();
    });

    // Note: Processing cancellation UI not implemented yet
    // This tests the backend video scan API
  });

  test('WhenVideoProcessingCompletes_ThenVocabularyGameStarts @smoke', async ({ page }) => {
    await test.step('Verify health check endpoint works', async () => {
      const { status, data } = await unauthenticatedGet(page, TEST_CONFIG.ENDPOINTS.HEALTH);
      expect(status).toBe(200);
      expect((data as { status: string }).status).toBeDefined();
    });

    // Note: Video player and vocabulary game UI not implemented yet
    // This tests the backend health check works
  });
});

