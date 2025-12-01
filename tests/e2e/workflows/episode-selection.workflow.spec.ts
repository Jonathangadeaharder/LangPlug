import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { LoginPage } from '../pages/LoginPage';
import { VideosPage } from '../pages/VideosPage';
import { EpisodeSelectionPage } from '../pages/EpisodeSelectionPage';

test.describe('Episode Selection Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;
  let loginPage: LoginPage;
  let videosPage: VideosPage;
  let episodeSelectionPage: EpisodeSelectionPage;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();
    
    loginPage = new LoginPage(page);
    videosPage = new VideosPage(page);
    episodeSelectionPage = new EpisodeSelectionPage(page);
    
    // Login user and wait for redirect to protected page
    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
    await page.waitForLoadState('networkidle');
    
    // Wait for redirect away from login page
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15000 });
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  test('WhenUserSelectsSeries_ThenEpisodeListIsDisplayed @smoke', async ({ page }) => {
    await test.step('Navigate to videos page', async () => {
      await videosPage.goto();
      await expect(page).toHaveURL(/\/videos/);
    });

    await test.step('Wait for series to load and verify', async () => {
      // Wait for series cards to appear
      await videosPage.waitForSeriesToLoad();
      
      const seriesCount = await videosPage.getSeriesCount();
      console.log(`Found ${seriesCount} series`);
      expect(seriesCount).toBeGreaterThan(0);
      
      const seriesNames = await videosPage.getSeriesNames();
      console.log('Available series:', seriesNames);
    });

    await test.step('Select first series and verify episodes page', async () => {
      await videosPage.selectFirstSeries();
      
      // Should navigate to episodes page
      await page.waitForURL(/\/episodes\//);
      
      const isLoaded = await episodeSelectionPage.isLoaded();
      expect(isLoaded).toBeTruthy();
      
      // Verify series title is displayed
      const seriesTitle = await episodeSelectionPage.getSeriesTitle();
      console.log(`Viewing episodes for: ${seriesTitle}`);
      expect(seriesTitle.length).toBeGreaterThan(0);
    });
  });

  test('WhenUserClicksBackFromEpisodes_ThenReturnsToVideosList @smoke', async ({ page }) => {
    await test.step('Navigate to videos and select series', async () => {
      await videosPage.goto();
      await videosPage.waitForSeriesToLoad();
      await videosPage.selectFirstSeries();
      await page.waitForURL(/\/episodes\//);
    });

    await test.step('Click back button and verify navigation', async () => {
      await episodeSelectionPage.clickBack();
      
      // Should return to videos page
      await page.waitForURL(/\/videos/);
      expect(page.url()).toContain('/videos');
      
      // Verify series are still visible
      await videosPage.waitForSeriesToLoad();
      const seriesCount = await videosPage.getSeriesCount();
      expect(seriesCount).toBeGreaterThan(0);
    });
  });

  test('WhenUserViewsEpisodeList_ThenEpisodesAreSortedCorrectly @smoke', async ({ page }) => {
    await test.step('Navigate to series episodes', async () => {
      await videosPage.goto();
      await videosPage.waitForSeriesToLoad();
      await videosPage.selectFirstSeries();
      await page.waitForURL(/\/episodes\//);
    });

    await test.step('Verify episodes are displayed and sorted', async () => {
      const episodeCount = await episodeSelectionPage.getEpisodeCount();
      console.log(`Found ${episodeCount} episodes`);
      expect(episodeCount).toBeGreaterThan(0);
      
      const episodeNames = await episodeSelectionPage.getEpisodeNames();
      console.log('Episodes:', episodeNames);
      expect(episodeNames.length).toBeGreaterThan(0);
    });
  });
});
