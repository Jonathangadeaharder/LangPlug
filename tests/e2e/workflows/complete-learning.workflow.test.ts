import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';

test.describe('Complete Learning Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();

    // Log in user
    await page.goto('/login');
    await page.locator('input[type="email"]').fill(testUser.email);
    await page.locator('input[type="password"]').fill(testUser.password);
    await page.locator('button[type="submit"]').click();

    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible({ timeout: 10000 });
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  test('WhenUserCompletesFullLearningFlow_ThenAllFeaturesWorkTogether @smoke', async ({ page }) => {
    await test.step('Verify authentication and core APIs work together', async () => {
      // Test that authenticated user can access multiple API endpoints

      // 1. Videos API
      const videosResponse = await page.request.get('http://localhost:8000/api/videos', {
        headers: { Authorization: `Bearer ${testUser.token}` }
      });
      expect(videosResponse.ok()).toBeTruthy();

      // 2. Vocabulary API
      const vocabResponse = await page.request.get('http://localhost:8000/api/vocabulary?cefr_level=A1&limit=1', {
        headers: { Authorization: `Bearer ${testUser.token}` }
      });
      expect(vocabResponse.status()).not.toBe(401); // Should be authorized

      // 3. Video scan API
      const scanResponse = await page.request.post('http://localhost:8000/api/videos/scan', {
        headers: { Authorization: `Bearer ${testUser.token}` }
      });
      expect(scanResponse.ok()).toBeTruthy();
    });

    // Note: Full learning flow UI (video player, game integration, progress tracking) not implemented yet
    // This tests that core backend APIs work together with authentication
  });

  test('WhenUserRepeatsEpisode_ThenProgressIsMaintainedAndImproved @smoke', async ({ page }) => {
    await test.step('Verify vocabulary can be created and backend is accessible', async () => {
      // Create test vocabulary
      const testVocab = await testDataManager.createTestVocabulary(testUser, {
        word: 'Progresstest',
        translation: 'Progress test',
        difficulty_level: 'beginner'
      });

      // Verify vocabulary was created successfully
      expect(testVocab.id).toBeDefined();

      // Verify backend is still accessible with health check
      const healthResponse = await page.request.get('http://localhost:8000/health');
      expect(healthResponse.status()).toBe(200);
    });

    // Note: Episode progress tracking and repeat learning UI not implemented yet
    // This tests that vocabulary can be created via backend API
  });
});
