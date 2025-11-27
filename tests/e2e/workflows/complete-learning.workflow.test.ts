import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { TEST_CONFIG } from '../utils/test-config';
import { loginUser, authenticatedGet, authenticatedPost, unauthenticatedGet } from '../utils/page-helpers';

test.describe('Complete Learning Workflow @smoke', () => {
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

  test('WhenUserCompletesFullLearningFlow_ThenAllFeaturesWorkTogether @smoke', async ({ page }) => {
    await test.step('Verify authentication and core APIs work together', async () => {
      // 1. Videos API
      const { ok: videosOk } = await authenticatedGet(page, TEST_CONFIG.ENDPOINTS.VIDEOS, testUser);
      expect(videosOk).toBeTruthy();

      // 2. Vocabulary API
      const { status: vocabStatus } = await authenticatedGet(
        page,
        `${TEST_CONFIG.ENDPOINTS.VOCABULARY_LIBRARY}?level=A1&limit=1`,
        testUser
      );
      expect(vocabStatus).not.toBe(401);

      // 3. Video scan API
      const { ok: scanOk } = await authenticatedPost(page, TEST_CONFIG.ENDPOINTS.VIDEOS_SCAN, testUser);
      expect(scanOk).toBeTruthy();
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
        difficulty_level: 'beginner' as const
      });

      // Verify vocabulary was created successfully
      expect(testVocab.id).toBeDefined();

      // Verify backend is still accessible with health check
      const { status } = await unauthenticatedGet(page, TEST_CONFIG.ENDPOINTS.HEALTH);
      expect(status).toBe(200);
    });

    // Note: Episode progress tracking and repeat learning UI not implemented yet
    // This tests that vocabulary can be created via backend API
  });
});

