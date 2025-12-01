import { test, expect } from '@playwright/test';
import { VocabularyPage } from '../pages/VocabularyPage';

test.describe('Vocabulary E2E Tests', () => {
  let vocabularyPage: VocabularyPage;

  test.beforeEach(async ({ page }) => {
    vocabularyPage = new VocabularyPage(page);
    await vocabularyPage.goto();
  });

  test.describe('Library Display', () => {
    test('should load vocabulary library', async () => {
      expect(await vocabularyPage.isLoaded()).toBe(true);
    });

    test('should display vocabulary levels', async ({ page }) => {
      // Verify level tabs are visible
      await expect(page.getByRole('button', { name: /A1/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /B1/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /C2/i })).toBeVisible();
    });

    test('should show search input', async () => {
      await expect(vocabularyPage.searchInput).toBeVisible();
    });
  });

  test.describe('Level Navigation', () => {
    test('should switch between vocabulary levels', async () => {
      // Start on A1 (default) - wait for it to be active
      // Note: Default level might depend on user or app state, but usually it's A1 or All
      // We check if A1 is active or switch to it.
      if (!await vocabularyPage.isLevelActive('A1')) {
          await vocabularyPage.selectLevel('A1');
      }
      expect(await vocabularyPage.isLevelActive('A1')).toBe(true);

      // Switch to A2
      await vocabularyPage.selectLevel('A2');
      expect(await vocabularyPage.isLevelActive('A2')).toBe(true);

      // Switch to B1
      await vocabularyPage.selectLevel('B1');
      expect(await vocabularyPage.isLevelActive('B1')).toBe(true);
    });
  });

  test.describe('UI Elements', () => {
    test('should have add word button', async () => {
      await expect(vocabularyPage.addWordButton).toBeVisible();
    });

    test('should have back to videos button', async () => {
      await expect(vocabularyPage.backButton).toBeVisible();
    });
  });
});