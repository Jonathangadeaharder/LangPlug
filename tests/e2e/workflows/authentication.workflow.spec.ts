import { test, expect, Page } from '@playwright/test';
import { TestDataManager } from '../utils/test-data-manager';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';

test.describe('Authentication Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let loginPage: LoginPage;
  let registerPage: RegisterPage;
  let testUser: any;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();
    // Skip registration flow - use API-created user for login testing
    loginPage = new LoginPage(page);
    registerPage = new RegisterPage(page);
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData();
  });

  test('WhenUserLogsInWithExistingUser_ThenCanAccessProtectedFeatures @smoke', async ({ page }) => {
    await test.step('Navigate to login page', async () => {
      await loginPage.goto();
      await loginPage.login(testUser.email, testUser.password);
    });

    await test.step('Verify successful authentication', async () => {
      // Wait for login to complete
      await page.waitForLoadState('networkidle');
      
      // Verify we're not on login page anymore - this proves authentication worked
      const currentUrl = page.url();
      const isAuthenticated = !currentUrl.includes('/login');
      
      if (!isAuthenticated) {
        throw new Error('Authentication verification failed - still on login page after login');
      }
      
      // Additional verification: check if we're on a protected route like /videos or /
      const isOnProtectedPage = currentUrl.includes('/videos') || currentUrl.endsWith('/');
      expect(isOnProtectedPage).toBeTruthy();
    });

    await test.step('Access protected features after authentication', async () => {
      // After successful registration, user should be redirected to a protected page
      // Verify we're not on login or register page anymore
      await page.waitForURL((url) => !url.pathname.includes('/login') && !url.pathname.includes('/register'), {
        timeout: 10000
      });
      
      // Verify we're on a protected page (videos, vocabulary, etc.)
      const currentUrl = page.url();
      const isProtectedPage = currentUrl.includes('/videos') || currentUrl.includes('/vocabulary') || currentUrl.includes('/profile');
      expect(isProtectedPage, `Expected protected page but got ${currentUrl}`).toBeTruthy();
    });
  });

  test('WhenUserLogsOut_ThenCannotAccessProtectedFeatures @smoke', async ({ page }) => {
    // First log in
    const user = await testDataManager.createTestUser();

    await test.step('Log in user', async () => {
      await page.goto('/');

      // Landing page uses button navigation, not links
      const loginButton = page.getByRole('button', { name: /sign in|login/i }).or(
        page.locator('a[href*="login"]')
      );

      await loginButton.click();
      await loginPage.login(user.email, user.password);

      // Wait for successful login - check user menu appears
      await expect(loginPage.header.logoutButton).toBeVisible({ timeout: 10000 });
    });

    await test.step('Log out user', async () => {
      await loginPage.header.clickLogout();

      // Verify logout by checking for Sign In button on landing page
      await expect(
        page.getByRole('button', { name: /sign in|login/i }).or(
          page.locator('a[href*="login"]')
        )
      ).toBeVisible();
    });

    await test.step('Verify cannot access protected features', async () => {
      // Try to access vocabulary directly
      await page.goto('/vocabulary');

      // Should redirect to login - check for login page indicators
      await page.waitForLoadState('networkidle');

      // Verify we're on login page by checking URL or login form elements
      const isOnLoginPage = page.url().includes('/login') ||
                            await page.locator('input[type="password"]').isVisible();

      expect(isOnLoginPage).toBeTruthy();
    });
  });

  test('WhenInvalidCredentials_ThenShowsErrorAndDoesNotAuthenticate @smoke', async ({ page }) => {
    await test.step('Attempt login with invalid credentials', async () => {
      await page.goto('/');

      // Landing page uses button navigation, not links
      const loginButton = page.getByRole('button', { name: /sign in|login/i }).or(
        page.locator('a[href*="login"]')
      );

      await loginButton.click();
      await loginPage.login('invalid@email.com', 'wrongpassword');
    });

    await test.step('Verify error message appears', async () => {
      const errorVisible = await loginPage.isErrorVisible();
      expect(errorVisible).toBe(true);
    });

    await test.step('Verify user remains unauthenticated', async () => {
      // Should still see login form
      await expect(loginPage.emailInput).toBeVisible();
      await expect(loginPage.passwordInput).toBeVisible();

      // Should not see user menu or protected elements
      const isUserMenuVisible = await loginPage.header.isLoggedIn();
      expect(isUserMenuVisible).toBe(false);
    });
  });
});
