import { test, expect } from '@playwright/test';
import { VideosPage } from '../pages/VideosPage';
import { VocabularyPage } from '../pages/VocabularyPage';
import { LoginPage } from '../pages/LoginPage';
import { BASE_URL, ROUTES } from '../config/urls';

test.describe('Navigation E2E Tests', () => {
  let videosPage: VideosPage;
  let vocabularyPage: VocabularyPage;

  test.beforeEach(async ({ page }) => {
    videosPage = new VideosPage(page);
    vocabularyPage = new VocabularyPage(page);
    
    // Start at videos (assuming auth via storageState)
    await videosPage.goto();
  });

  test.describe('Main Navigation', () => {
    test('should navigate between Videos and Vocabulary', async ({ page }) => {
      // Go to Vocabulary
      await videosPage.clickVocabularyLibrary();
      expect(await vocabularyPage.isLoaded()).toBe(true);

      // Go back
      await vocabularyPage.clickBackToVideos();
      expect(await videosPage.isLoaded()).toBe(true);
    });

    test('should navigate via Header logout', async ({ page }) => {
      // Check Header
      await expect(videosPage.header.logoutButton).toBeVisible();
      
      // Logout
      await videosPage.header.clickLogout();
      await expect(page).toHaveURL(ROUTES.LOGIN);
    });
  });

  test.describe('Deep Linking', () => {
    test('should allow direct navigation to vocabulary', async ({ page }) => {
      await vocabularyPage.goto();
      expect(await vocabularyPage.isLoaded()).toBe(true);
    });
  });
  
  test.describe('Edge Cases', () => {
    test('should handle invalid routes', async ({ page }) => {
      await page.goto(`${BASE_URL}/invalid-page-12345`);
      // Should not crash (white screen), likely shows 404 or redirects to home
      // or shows the app shell.
      // We check that the body is visible.
      await expect(page.locator('body')).toBeVisible();
    });
  });
});

// Separate describe for unauthenticated access (needs clean context)
test.describe('Unauthenticated Navigation', () => {
    test('should redirect to login when accessing protected pages', async ({ browser }) => {
        const context = await browser.newContext({ storageState: { cookies: [], origins: [] } }); // Ensure no auth
        const page = await context.newPage();
        
        try {
            // Try accessing videos
            await page.goto(ROUTES.VIDEOS);
            await expect(page).toHaveURL(new RegExp(ROUTES.LOGIN));
        } finally {
            await context.close();
        }
    });
});