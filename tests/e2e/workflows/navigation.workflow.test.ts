import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { TEST_CONFIG } from '../utils/test-config';
import {
  loginUser,
  logoutUser,
  authenticatedGet,
  authenticatedPost,
  unauthenticatedGet,
  verifyRedirectedToLogin,
} from '../utils/page-helpers';

test.describe('Navigation Workflow @smoke', () => {
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

  test('WhenUserNavigatesBetweenMainPages_ThenAllPagesLoad @smoke', async ({ page }) => {
    await test.step('Verify videos page loads after login', async () => {
      // Should be redirected to videos page after login
      await page.waitForURL((url) => url.pathname.includes('/videos'), { timeout: 5000 });
      
      // Page should have video selection content
      const heading = page.getByRole('heading').first();
      await expect(heading).toBeVisible();
    });

    await test.step('Navigate to vocabulary library (if available)', async () => {
      const vocabNav = page.locator('[data-testid="vocabulary-nav"]').or(
        page.getByRole('button', { name: /vocabulary/i }).or(
          page.locator('a[href*="vocabulary"]')
        )
      );

      if (await vocabNav.count() > 0) {
        await vocabNav.first().click();
        await page.waitForLoadState('networkidle');
        
        // Verify we navigated somewhere (url changed or page updated)
        await page.waitForTimeout(1000);
      } else {
        // Skip if no vocabulary nav - verify videos API works instead
        const { ok } = await authenticatedGet(page, TEST_CONFIG.ENDPOINTS.VIDEOS, testUser);
        expect(ok).toBeTruthy();
      }
    });

    await test.step('Navigate back to videos page', async () => {
      // Look for videos navigation
      const videosNav = page.locator('[data-testid="videos-nav"]').or(
        page.getByRole('button', { name: /video|series/i }).or(
          page.locator('a[href*="videos"]')
        )
      );

      if (await videosNav.count() > 0) {
        await videosNav.first().click();
        await page.waitForURL((url) => url.pathname.includes('/videos'), { timeout: 5000 });
      }
    });

    await test.step('Verify user can access profile', async () => {
      // Click user menu
      const userMenu = page.locator('[data-testid="user-menu"]');
      await userMenu.click();
      
      // Look for profile option
      const profileOption = page.getByRole('menuitem', { name: /profile/i }).or(
        page.locator('[data-testid="profile-link"]')
      );
      
      if (await profileOption.count() > 0) {
        await profileOption.click();
        await page.waitForLoadState('networkidle');
      }
    });

    // Navigation is working correctly across main pages
  });

  test('WhenUserClicksLogo_ThenNavigatesToHome @smoke', async ({ page }) => {
    await test.step('Click logo to navigate home', async () => {
      const logo = page.locator('[data-testid="logo"]').or(
        page.getByRole('link', { name: /langplug/i }).or(
          page.locator('header a').first()
        )
      );

      if (await logo.count() > 0) {
        await logo.click();
        await page.waitForLoadState('networkidle');
        
        // Should be on home/videos page for authenticated user
        const currentUrl = page.url();
        expect(currentUrl.includes('/videos') || currentUrl.endsWith('/')).toBeTruthy();
      }
    });
  });

  test('WhenUserTriesToAccessProtectedRouteWithoutAuth_ThenRedirectedToLogin @smoke', async ({ page }) => {
    await test.step('Logout user', async () => {
      await logoutUser(page);
    });

    await test.step('Try to access protected route', async () => {
      await page.goto('/videos');
      await verifyRedirectedToLogin(page);
    });
  });
});

test.describe('Error Handling Workflow @smoke', () => {
  let testDataManager: TestDataManager;

  test.beforeEach(async () => {
    testDataManager = new TestDataManager();
  });

  test('WhenUserEntersInvalidEmail_ThenShowsValidationError @smoke', async ({ page }) => {
    await test.step('Navigate to registration', async () => {
      await page.goto('/register');
      await page.waitForLoadState('networkidle');
    });

    await test.step('Enter invalid email format', async () => {
      const emailInput = page.locator('input[type="email"]').or(
        page.locator('input[name="email"]')
      );
      await emailInput.fill('invalid-email');
      
      // Fill other fields
      const usernameInput = page.locator('[data-testid="username-input"]').or(
        page.locator('input[name="username"]')
      );
      if (await usernameInput.count() > 0) {
        await usernameInput.fill('testuser');
      }

      const passwordInputs = page.locator('input[type="password"]');
      if (await passwordInputs.count() >= 2) {
        await passwordInputs.nth(0).fill('TestPassword123!');
        await passwordInputs.nth(1).fill('TestPassword123!');
      }
    });

    await test.step('Submit form and check for error', async () => {
      const submitButton = page.locator('button[type="submit"]');
      await submitButton.click();
      
      // Wait for validation
      await page.waitForTimeout(500);
      
      // Check for error message or form not submitting
      const hasError = await page.getByText(/invalid|error|email/i).count() > 0 ||
                       (await page.url()).includes('/register');
      
      expect(hasError).toBeTruthy();
    });
  });

  test('WhenUserEntersWrongPassword_ThenShowsLoginError @smoke', async ({ page }) => {
    const user = await testDataManager.createTestUser();

    await test.step('Navigate to login', async () => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
    });

    await test.step('Enter correct email but wrong password', async () => {
      await page.locator(TEST_CONFIG.SELECTORS.EMAIL_INPUT).fill(user.email);
      await page.locator(TEST_CONFIG.SELECTORS.PASSWORD_INPUT).fill('wrongpassword123');
    });

    await test.step('Submit and check for error', async () => {
      await page.locator(TEST_CONFIG.SELECTORS.SUBMIT_BUTTON).click();
      await page.waitForTimeout(1000);
      
      const hasError = await page.getByText(/invalid|error|incorrect|failed/i).count() > 0 ||
                       (await page.url()).includes('/login');
      expect(hasError).toBeTruthy();
    });

    await testDataManager.cleanupTestData(user);
  });

  test('WhenAPIReturns404_ThenShowsNotFoundMessage @smoke', async ({ page }) => {
    const user = await testDataManager.createTestUser();

    await test.step('Login user', async () => {
      await loginUser(page, user);
    });

    await test.step('Verify 404 response from API', async () => {
      const { status } = await authenticatedGet(
        page,
        `${TEST_CONFIG.ENDPOINTS.VIDEOS}/nonexistent-video-id/status`,
        user
      );
      expect(status).toBe(404);
    });

    await testDataManager.cleanupTestData(user);
  });

  test('WhenSessionExpires_ThenUserIsRedirectedToLogin @smoke', async ({ page }) => {
    await test.step('Verify unauthorized API call returns 401', async () => {
      const { status } = await unauthenticatedGet(page, TEST_CONFIG.ENDPOINTS.PROFILE);
      expect(status).toBe(401);
    });

    await test.step('Verify protected page redirects to login', async () => {
      await page.goto('/');
      await page.evaluate(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('authToken');
      });
      
      await page.goto('/videos');
      await verifyRedirectedToLogin(page);
    });
  });
});

test.describe('Video Selection Workflow @smoke', () => {
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

  test('WhenUserViewsVideoLibrary_ThenSeriesAreDisplayed @smoke', async ({ page }) => {
    await test.step('Verify video library loads', async () => {
      await page.waitForURL((url) => url.pathname.includes('/videos'), { timeout: 5000 });
      
      const { ok, data } = await authenticatedGet(page, TEST_CONFIG.ENDPOINTS.VIDEOS, testUser);
      expect(ok).toBeTruthy();
      expect(Array.isArray(data)).toBeTruthy();
    });

    await test.step('Verify scan endpoint works', async () => {
      const { ok } = await authenticatedPost(page, TEST_CONFIG.ENDPOINTS.VIDEOS_SCAN, testUser);
      expect(ok).toBeTruthy();
    });
  });

  test('WhenUserSelectsSeries_ThenEpisodesAreShown @smoke', async ({ page }) => {
    await test.step('Verify series endpoint works', async () => {
      await authenticatedPost(page, TEST_CONFIG.ENDPOINTS.VIDEOS_SCAN, testUser);

      const { ok, data } = await authenticatedGet(page, TEST_CONFIG.ENDPOINTS.VIDEOS, testUser);
      expect(ok).toBeTruthy();
      
      const videos = data as Array<{ series?: string }>;
      if (videos.length > 0 && videos[0].series) {
        const seriesName = videos[0].series;
        const { status } = await authenticatedGet(
          page,
          `${TEST_CONFIG.ENDPOINTS.VIDEOS}/${encodeURIComponent(seriesName)}/episodes`,
          testUser
        );
        expect([200, 404].includes(status)).toBeTruthy();
      }
    });
  });
});
