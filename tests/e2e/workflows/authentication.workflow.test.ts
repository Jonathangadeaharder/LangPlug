import { test, expect, Page } from '@playwright/test';
import { TestDataManager } from '../utils/test-data-manager';

test.describe('Authentication Workflow @smoke', () => {
  let testDataManager: TestDataManager;

  test.beforeEach(async () => {
    testDataManager = new TestDataManager();
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData();
  });

  test('WhenUserRegistersAndLogs_ThenCanAccessProtectedFeatures @smoke', async ({ page }) => {
    await test.step('Navigate to login page', async () => {
      await page.goto('/login');
      await expect(page.locator('#root')).toBeVisible();
      // Wait for lazy-loaded login form to render
      await page.waitForLoadState('networkidle');
    });

    await test.step('Navigate to registration', async () => {
      // Wait for login form to be fully loaded (lazy component)
      const registerLink = page.locator('[data-testid="register-link"]');
      await registerLink.waitFor({ state: 'visible', timeout: 10000 });
      await registerLink.click();

      // Verify registration form appears and wait for it to be fully rendered
      await expect(page.locator('form')).toBeVisible();

      // Wait for form inputs to be ready (fixes flaky test - form needs time to hydrate)
      await page.waitForLoadState('networkidle');

      // Fill registration form with semantic selectors
      const timestamp = Date.now();
      const testUser = {
        username: `e2euser_${timestamp}`,
        email: `e2e.${timestamp}@langplug.com`,
        password: `TestPass${timestamp}!`
      };

      // Username input with explicit validation and timeout
      const usernameInput = page.locator('[data-testid="username-input"]');
      try {
        await usernameInput.waitFor({ state: 'visible', timeout: 3000 });
        await usernameInput.fill(testUser.username);
      } catch {
        const nameInput = page.locator('input[name="username"]');
        await expect(nameInput).toBeVisible({ timeout: 3000 });
        await nameInput.fill(testUser.username);
      }

      // Email input with explicit validation and timeout
      const emailInput = page.locator('[data-testid="email-input"]');
      try {
        await emailInput.waitFor({ state: 'visible', timeout: 3000 });
        await emailInput.fill(testUser.email);
      } catch {
        const typeEmailInput = page.locator('input[type="email"]');
        await expect(typeEmailInput).toBeVisible({ timeout: 3000 });
        await typeEmailInput.fill(testUser.email);
      }

      // Password input with explicit validation and timeout
      const passwordInput = page.locator('[data-testid="password-input"]');
      try {
        await passwordInput.waitFor({ state: 'visible', timeout: 3000 });
        await passwordInput.fill(testUser.password);
      } catch {
        const typePasswordInput = page.locator('input[type="password"]').first();
        await expect(typePasswordInput).toBeVisible({ timeout: 3000 });
        await typePasswordInput.fill(testUser.password);
      }

      // Confirm Password input with explicit validation and timeout
      const confirmPasswordInput = page.locator('[data-testid="confirm-password-input"]');
      try {
        await confirmPasswordInput.waitFor({ state: 'visible', timeout: 3000 });
        await confirmPasswordInput.fill(testUser.password);
      } catch {
        // Use label-based selection instead of array index for better semantic matching
        const labeledConfirmInput = page.locator('input[type="password"]').filter({
          has: page.locator('label:has-text("Confirm")')
        }).or(
          page.locator('input[placeholder*="confirm" i]')
        );

        await expect(labeledConfirmInput).toBeVisible({ timeout: 3000 });
        await labeledConfirmInput.fill(testUser.password);
      }

      // Submit button with explicit validation
      const submitButton = page.locator('[data-testid="register-submit"]');
      if (!(await submitButton.isVisible())) {
        const typeSubmitButton = page.locator('button[type="submit"]');
        if (!(await typeSubmitButton.isVisible())) {
          const roleSubmitButton = page.getByRole('button', { name: /register/i });
          if (!(await roleSubmitButton.isVisible())) {
            throw new Error('Register submit button not found - missing data-testid="register-submit" instrumentation');
          }
          await roleSubmitButton.click();
        } else {
          await typeSubmitButton.click();
        }
      } else {
        await submitButton.click();
      }
    });

    await test.step('Verify successful authentication', async () => {
      // Wait for redirect and authentication (registration has 2s delay + navigation time)
      // Extended timeout to handle: submit -> 2s delay -> redirect to / -> redirect to /videos -> render
      const userMenu = page.locator('[data-testid="user-menu"]');

      try {
        await expect(userMenu).toBeVisible({ timeout: 15000 });
      } catch {
        console.warn('Missing data-testid="user-menu" - using fallback authentication indicators');

        const userProfile = page.locator('.user-profile');
        const logoutButton = page.getByRole('button', { name: /logout/i });

        try {
          await expect(userProfile.or(logoutButton)).toBeVisible({ timeout: 5000 });
        } catch {
          throw new Error('Authentication verification failed - no user menu, profile, or logout button found. Missing instrumentation.');
        }
      }

      // User menu presence confirms successful authentication - no need for additional dashboard checks
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
      await expect(page.locator('form')).toBeVisible();

      await page.locator('input[name="email"]').or(
        page.locator('input[type="email"]')
      ).fill(user.email);

      await page.locator('input[name="password"]').or(
        page.locator('input[type="password"]')
      ).fill(user.password);

      await page.locator('button[type="submit"]').or(
        page.getByRole('button', { name: /login/i })
      ).click();

      // Wait for successful login - check user menu appears
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible({ timeout: 10000 });
    });

    await test.step('Log out user', async () => {
      const logoutButton = page.locator('[data-testid="logout-button"]').or(
        page.getByRole('button', { name: /logout/i })
      );

      await logoutButton.click();

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
      await expect(page.locator('form')).toBeVisible();

      // Enter invalid credentials
      await page.locator('input[name="email"]').or(
        page.locator('input[type="email"]')
      ).fill('invalid@email.com');

      await page.locator('input[name="password"]').or(
        page.locator('input[type="password"]')
      ).fill('wrongpassword');

      await page.locator('button[type="submit"]').or(
        page.getByRole('button', { name: /login/i })
      ).click();
    });

    await test.step('Verify error message appears', async () => {
      const errorMessage = page.locator('[data-testid="error-message"]').or(
        page.locator('.error').or(
          page.locator('.alert-error').or(
            page.getByText(/invalid|incorrect|unauthorized/i)
          )
        )
      );

      await expect(errorMessage).toBeVisible();
    });

    await test.step('Verify user remains unauthenticated', async () => {
      // Should still see login form
      await expect(page.locator('form')).toBeVisible();
      await expect(page.locator('input[type="password"]')).toBeVisible();

      // Should not see user menu or protected elements
      const userMenu = page.locator('[data-testid="user-menu"]');
      await expect(userMenu).not.toBeVisible();
    });
  });
});
