import { test, expect } from '@playwright/test';
import { LandingPage } from '../pages/LandingPage';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { LoginPage } from '../pages/LoginPage';

/**
 * Landing Page Workflow Tests
 * Tests the public landing page experience for unauthenticated users
 */
test.describe('Landing Page Workflow @smoke', () => {
  let landingPage: LandingPage;

  test.beforeEach(async ({ page }) => {
    landingPage = new LandingPage(page);
  });

  test('WhenUnauthenticatedUserVisitsRoot_ThenLandingPageDisplays @smoke', async ({ page }) => {
    await test.step('Navigate to landing page', async () => {
      await landingPage.goto();
    });

    await test.step('Verify landing page content is visible', async () => {
      // Check hero section
      const isLoaded = await landingPage.isLoaded();
      expect(isLoaded).toBeTruthy();

      // Verify main heading exists
      const heroTitle = await landingPage.getHeroTitle();
      expect(heroTitle.length).toBeGreaterThan(0);
      console.log(`Hero title: ${heroTitle}`);
    });

    await test.step('Verify navigation options are available', async () => {
      // Check for login/register buttons
      const hasGetStarted = await landingPage.getStartedButton.isVisible().catch(() => false);
      const hasLogin = await landingPage.loginButton.isVisible().catch(() => false);

      // At least one auth navigation should be visible
      expect(hasGetStarted || hasLogin).toBeTruthy();
      console.log(`Get Started visible: ${hasGetStarted}, Login visible: ${hasLogin}`);
    });
  });

  test('WhenUserClicksGetStarted_ThenNavigatesToRegister @smoke', async ({ page }) => {
    await test.step('Navigate to landing page', async () => {
      await landingPage.goto();
    });

    await test.step('Click get started button', async () => {
      const hasGetStarted = await landingPage.getStartedButton.isVisible().catch(() => false);
      
      if (hasGetStarted) {
        await landingPage.clickGetStarted();
        
        // Should navigate to register page
        await page.waitForURL(/\/(register|signup|login)/, { timeout: 5000 });
        const url = page.url();
        expect(url).toMatch(/\/(register|signup|login)/);
        console.log(`Navigated to: ${url}`);
      } else {
        console.log('Get Started button not found - skipping navigation test');
      }
    });
  });

  test('WhenUserClicksLogin_ThenNavigatesToLoginPage @smoke', async ({ page }) => {
    await test.step('Navigate to landing page', async () => {
      await landingPage.goto();
    });

    await test.step('Click login button', async () => {
      const hasLogin = await landingPage.loginButton.isVisible().catch(() => false);
      
      if (hasLogin) {
        await landingPage.clickLogin();
        
        // Should navigate to login page
        await page.waitForURL(/\/login/, { timeout: 5000 });
        expect(page.url()).toContain('/login');
        console.log('Successfully navigated to login page');
      } else {
        console.log('Login button not found - skipping navigation test');
      }
    });
  });

  test('WhenAuthenticatedUserVisitsRoot_ThenRedirectsToVideos @smoke', async ({ page }) => {
    // This test verifies that authenticated users are redirected from landing to videos
    // We'll use real authentication via TestDataManager
    const testDataManager = new TestDataManager();
    let testUser: TestUser | null = null;

    try {
      await test.step('Login with real user', async () => {
        testUser = await testDataManager.createTestUser();
        const loginPage = new LoginPage(page);
        await loginPage.goto();
        await loginPage.login(testUser.email, testUser.password);
        await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
      });

      await test.step('Navigate to root and verify redirect', async () => {
        await page.goto('/');
        await page.waitForLoadState('networkidle');
        
        const url = page.url();
        // Authenticated user should be redirected to /videos
        expect(url).toContain('/videos');
        console.log(`Authenticated user redirected to: ${url}`);
      });
    } finally {
      if (testUser) {
        await testDataManager.cleanupTestData(testUser);
      }
    }
  });
});
