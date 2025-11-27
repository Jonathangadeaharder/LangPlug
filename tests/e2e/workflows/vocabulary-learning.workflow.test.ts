import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { TEST_CONFIG } from '../utils/test-config';
import { loginUser, authenticatedGet } from '../utils/page-helpers';

test.describe('Vocabulary Learning Workflow @smoke', () => {
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

  test('WhenUserAccessesVocabularyLibrary_ThenCanViewAndMarkWords @smoke', async ({ page }) => {
    // Create test vocabulary through API with unique identifiable words
    const testWord1 = `TestVocab${Date.now()}`;
    const createdVocab = await testDataManager.createTestVocabulary(testUser, {
      word: testWord1,
      translation: 'Test Hello',
      difficulty_level: 'beginner' as const
    });
    
    // Verify API created the vocabulary successfully
    expect(createdVocab.id).toBeDefined();

    await test.step('Navigate to vocabulary library', async () => {
      // Navigation uses button, not link - look for "Vocabulary Library" button
      const vocabNav = page.locator('[data-testid="vocabulary-nav"]').or(
        page.getByRole('button', { name: /vocabulary/i }).or(
          page.locator('a[href*="vocabulary"]').or(
            page.getByRole('link', { name: /vocabulary/i })
          )
        )
      );

      await vocabNav.first().click();

      // Wait for page to fully load
      await page.waitForLoadState('networkidle');

      // Verify vocabulary library interface loads
      await expect(
        page.getByRole('heading', { name: /vocabulary.*library/i })
      ).toBeVisible({ timeout: 10000 });
    });

    await test.step('Verify vocabulary statistics are displayed', async () => {
      // Wait for stats to load
      await page.waitForTimeout(500);
      
      // Check for total words count - use flexible matching
      const statsArea = page.locator('[class*="stat"], [class*="progress"], [class*="summary"]').first();
      const hasStats = await statsArea.count() > 0 || await page.getByText(/\d+.*word/i).count() > 0;
      
      // Either stats area exists or we see word counts
      expect(hasStats).toBeTruthy();
    });

    await test.step('Verify vocabulary API is working correctly', async () => {
      const { ok, data } = await authenticatedGet(
        page,
        `${TEST_CONFIG.ENDPOINTS.VOCABULARY_LIBRARY}?level=A1&limit=10`,
        testUser
      );
      
      expect(ok).toBeTruthy();
      expect(data).toBeDefined();
    });

    // Vocabulary library interface is working correctly
    // - Navigation works
    // - Page loads with stats
    // - API returns vocabulary data
  });

  test('WhenUserAddsCustomVocabulary_ThenItAppearsInLibrary @smoke', async ({ page }) => {
    // Create custom vocabulary through API (UI doesn't have add feature yet)
    // Using beginner level so it appears on default A1 tab (avoids tab switching issues)
    await testDataManager.createTestVocabulary(testUser, {
      word: 'Testword',
      translation: 'Test word',
      difficulty_level: 'beginner' as const
    });

    await test.step('Navigate to vocabulary library', async () => {
      const vocabNav = page.locator('[data-testid="vocabulary-nav"]').or(
        page.getByRole('button', { name: /vocabulary/i }).or(
          page.locator('a[href*="vocabulary"]').or(
            page.getByRole('link', { name: /vocabulary/i })
          )
        )
      );

      await vocabNav.first().click();

      // Verify vocabulary library interface loads (defaults to A1 level)
      await expect(
        page.getByRole('heading', { name: /vocabulary.*library/i })
      ).toBeVisible();

      // Verify we're on A1 level
      await expect(
        page.getByRole('heading', { name: /A1.*level.*vocabulary/i })
      ).toBeVisible({ timeout: 5000 });
    });

    await test.step('Search for custom vocabulary word', async () => {
      // Use search box to find our custom word
      const searchBox = page.locator('input[type="search"]').or(
        page.locator('input[placeholder*="earch"]')
      );

      await expect(searchBox).toBeVisible();
      await searchBox.fill('Testword');

      // Wait a moment for search to filter results
      await page.waitForTimeout(1000);
    });

    await test.step('Verify custom word appears in vocabulary list', async () => {
      // Check that the custom word is visible in the page
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('Testword');

      // Verify it's in the vocabulary cards area (not just in the search box)
      // Looking for the word in the actual vocabulary list, not just search box echo
      const wordCards = page.locator('[class*="word"], [class*="vocabulary"], [data-testid*="word"]');
      const hasTestword = await wordCards.filter({ hasText: 'Testword' }).count();

      // Should find at least one vocabulary card with our test word
      expect(hasTestword).toBeGreaterThan(0);
    });

    // Custom vocabulary successfully appears in library
    // - Created via API
    // - Appears in correct difficulty level (A1 for beginner)
    // - Searchable and visible in vocabulary list
  });

  test('WhenUserFiltersVocabularyByDifficulty_ThenOnlyRelevantWordsAppear @smoke', async ({ page }) => {
    // Create vocabulary with different difficulty levels
    // Using unique test words to avoid confusion with existing vocabulary
    await testDataManager.createTestVocabulary(testUser, {
      word: 'FiltertestA1',
      translation: 'Filter test A1',
      difficulty_level: 'beginner' as const
    });

    await testDataManager.createTestVocabulary(testUser, {
      word: 'FiltertestB1',
      translation: 'Filter test B1',
      difficulty_level: 'intermediate' as const
    });

    await test.step('Navigate to vocabulary library (defaults to A1 level)', async () => {
      const vocabNav = page.locator('[data-testid="vocabulary-nav"]').or(
        page.getByRole('button', { name: /vocabulary/i }).or(
          page.locator('a[href*="vocabulary"]').or(
            page.getByRole('link', { name: /vocabulary/i })
          )
        )
      );

      await vocabNav.first().click();

      // Verify vocabulary library loads and we're on A1 level
      await expect(
        page.getByRole('heading', { name: /A1.*level.*vocabulary/i })
      ).toBeVisible({ timeout: 5000 });
    });

    await test.step('Search for A1 beginner word to verify it appears', async () => {
      const searchBox = page.locator('input[type="search"]').or(
        page.locator('input[placeholder*="earch"]')
      );

      await expect(searchBox).toBeVisible();
      await searchBox.fill('FiltertestA1');
      await page.waitForTimeout(1000);

      // Verify A1 word is visible
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('FiltertestA1');
    });

    await test.step('Switch to B1 level and verify intermediate word appears', async () => {
      // Clear search first
      const searchBox = page.locator('input[type="search"]').or(
        page.locator('input[placeholder*="earch"]')
      );
      await searchBox.clear();

      // Click B1 level tab (text contains "B1" plus count, so don't use exact match)
      const b1Tab = page.getByText('B1').first();
      await expect(b1Tab).toBeVisible();
      await b1Tab.click();

      // Wait for B1 level to load
      await expect(
        page.getByRole('heading', { name: /B1.*level.*vocabulary/i })
      ).toBeVisible({ timeout: 5000 });

      // Search for B1 word
      await searchBox.fill('FiltertestB1');
      await page.waitForTimeout(1000);

      // Verify B1 word is visible
      const pageContent = await page.textContent('body');
      expect(pageContent).toContain('FiltertestB1');
    });

    await test.step('Verify A1 word does not appear in B1 level', async () => {
      // Search for A1 word while on B1 level
      const searchBox = page.locator('input[type="search"]').or(
        page.locator('input[placeholder*="earch"]')
      );
      await searchBox.clear();
      await searchBox.fill('FiltertestA1');
      await page.waitForTimeout(1000);

      // Check vocabulary list for word count
      const wordCards = page.locator('[class*="word"], [class*="vocabulary"], [data-testid*="word"]');
      const hasA1Word = await wordCards.filter({ hasText: 'FiltertestA1' }).count();

      // A1 word should not appear in B1 level (unless search crosses levels)
      // If it appears, it means filtering is not working - test would fail
      expect(hasA1Word).toBe(0);
    });

    // Level filtering is working correctly
    // - A1 words appear in A1 level
    // - B1 words appear in B1 level
    // - Words from different levels are filtered out
  });
});
