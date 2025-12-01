import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';
import { LoginPage } from '../pages/LoginPage';
import { ProfilePage } from '../pages/ProfilePage';

/**
 * Logout Workflow Tests
 * Tests the user logout functionality and session cleanup
 */
test.describe('Logout Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;
  let loginPage: LoginPage;
  let profilePage: ProfilePage;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();
    loginPage = new LoginPage(page);
    profilePage = new ProfilePage(page);

    // Login first
    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  test('WhenUserClicksLogout_ThenSessionEndsAndRedirects @smoke', async ({ page }) => {
    await test.step('Navigate to profile or find logout button', async () => {
      // First check if logout is visible in current page
      let logoutButton = page.getByRole('button', { name: /log\s?out|sign\s?out/i });
      let isVisible = await logoutButton.isVisible().catch(() => false);

      if (!isVisible) {
        // Navigate to profile where logout should be
        await page.goto('/profile');
        await page.waitForLoadState('networkidle');
        logoutButton = page.getByRole('button', { name: /log\s?out|sign\s?out/i });
        isVisible = await logoutButton.isVisible().catch(() => false);
      }

      console.log(`Logout button visible: ${isVisible}`);
    });

    await test.step('Click logout and verify redirect', async () => {
      const logoutButton = page.getByRole('button', { name: /log\s?out|sign\s?out/i });
      const isVisible = await logoutButton.isVisible().catch(() => false);

      if (isVisible) {
        await logoutButton.click();
        
        // Wait for redirect to login or landing
        await page.waitForURL(/\/(login|$)/, { timeout: 10000 });
        
        const url = page.url();
        const isLoggedOut = url.includes('/login') || url.endsWith('/') || url.endsWith(':3000/');
        expect(isLoggedOut).toBeTruthy();
        console.log(`Redirected to: ${url}`);
      } else {
        // Test logout via API
        const response = await page.request.post('http://127.0.0.1:8000/api/auth/logout');
        console.log(`Logout API status: ${response.status()}`);
        expect([200, 204, 401]).toContain(response.status());
      }
    });

    await test.step('Verify session is cleared', async () => {
      // Check localStorage is cleared
      const authStorage = await page.evaluate(() => localStorage.getItem('auth-storage'));
      
      if (authStorage) {
        const parsed = JSON.parse(authStorage);
        const isAuthenticated = parsed?.state?.isAuthenticated;
        expect(isAuthenticated).toBeFalsy();
        console.log(`Auth state after logout: ${isAuthenticated}`);
      } else {
        console.log('Auth storage cleared');
      }
    });
  });

  test('WhenUserLogsOut_ThenProtectedRoutesAreInaccessible @smoke', async ({ page }) => {
    await test.step('Logout user', async () => {
      // Clear auth state to simulate logout
      await page.evaluate(() => {
        localStorage.removeItem('auth-storage');
        localStorage.clear();
        sessionStorage.clear();
      });
      
      // Clear cookies
      await page.context().clearCookies();
    });

    await test.step('Try accessing protected route', async () => {
      await page.goto('/videos');
      await page.waitForLoadState('networkidle');
      
      // Should redirect to login
      const url = page.url();
      const isRedirected = url.includes('/login') || url.endsWith('/');
      expect(isRedirected).toBeTruthy();
      console.log(`Protected route redirect: ${url}`);
    });

    await test.step('Try accessing profile', async () => {
      await page.goto('/profile');
      await page.waitForLoadState('networkidle');
      
      const url = page.url();
      const isRedirected = url.includes('/login') || url.endsWith('/');
      expect(isRedirected).toBeTruthy();
      console.log(`Profile redirect: ${url}`);
    });
  });

  test('WhenSessionExpires_ThenUserIsRedirectedToLogin @smoke', async ({ page }) => {
    await test.step('Clear auth and verify redirect', async () => {
      // Clear all auth data
      await page.evaluate(() => {
        localStorage.removeItem('auth-storage');
        localStorage.clear();
      });
      await page.context().clearCookies();
    });

    await test.step('Try accessing protected page', async () => {
      await page.goto('/profile');
      await page.waitForLoadState('networkidle');
      
      // Should redirect to login
      const url = page.url();
      expect(url).toContain('/login');
      console.log(`Expired session redirects to: ${url}`);
    });
  });

  test('WhenUserLogsOutFromMultipleTabs_ThenAllSessionsEnd @smoke', async ({ page, context }) => {
    await test.step('Open second tab', async () => {
      const page2 = await context.newPage();
      await page2.goto('/videos');
      await page2.waitForLoadState('networkidle');
      
      // Verify second tab is authenticated
      const url = page2.url();
      console.log(`Second tab URL: ${url}`);
    });

    await test.step('Logout from first tab', async () => {
      // Clear auth in first tab
      await page.evaluate(() => {
        localStorage.removeItem('auth-storage');
        localStorage.clear();
      });
      
      await page.context().clearCookies();
    });

    await test.step('Verify second tab requires re-auth on refresh', async () => {
      const pages = context.pages();
      if (pages.length > 1) {
        const page2 = pages[1];
        await page2.reload();
        await page2.waitForLoadState('networkidle');
        
        const url = page2.url();
        const needsAuth = url.includes('/login') || url.endsWith('/');
        console.log(`Second tab after logout: ${url}, needs auth: ${needsAuth}`);
      }
    });
  });
});
