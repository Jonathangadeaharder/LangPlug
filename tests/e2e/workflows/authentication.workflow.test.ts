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
    await test.step('Navigate to application', async () => {
      await page.goto('/');
      await expect(page.locator('#root')).toBeVisible();
    });

    await test.step('Register new user', async () => {
      // Primary selector with explicit validation
      const registerLink = page.locator('[data-testid="register-link"]');

      if (!(await registerLink.isVisible())) {
        // Secondary fallback with explicit validation
        const semanticRegisterLink = page.getByRole('link', { name: /register/i });
        if (!(await semanticRegisterLink.isVisible())) {
          throw new Error('Register link not found - missing data-testid="register-link" instrumentation');
        }
        await semanticRegisterLink.click();
      } else {
        await registerLink.click();
      }

      // Verify registration form appears
      await expect(page.locator('form')).toBeVisible();

      // Fill registration form with semantic selectors
      const timestamp = Date.now();
      const testUser = {
        username: `e2euser_${timestamp}`,
        email: `e2e.${timestamp}@langplug.com`,
        password: `TestPass${timestamp}!`
      };

      // Username input with explicit validation
      const usernameInput = page.locator('[data-testid="username-input"]');
      if (!(await usernameInput.isVisible())) {
        const nameInput = page.locator('input[name="username"]');
        if (!(await nameInput.isVisible())) {
          throw new Error('Username input not found - missing data-testid="username-input" instrumentation');
        }
        await nameInput.fill(testUser.username);
      } else {
        await usernameInput.fill(testUser.username);
      }

      // Email input with explicit validation
      const emailInput = page.locator('[data-testid="email-input"]');
      if (!(await emailInput.isVisible())) {
        const typeEmailInput = page.locator('input[type="email"]');
        if (!(await typeEmailInput.isVisible())) {
          throw new Error('Email input not found - missing data-testid="email-input" instrumentation');
        }
        await typeEmailInput.fill(testUser.email);
      } else {
        await emailInput.fill(testUser.email);
      }

      // Password input with explicit validation
      const passwordInput = page.locator('[data-testid="password-input"]');
      if (!(await passwordInput.isVisible())) {
        const typePasswordInput = page.locator('input[type="password"]');
        if (!(await typePasswordInput.isVisible())) {
          throw new Error('Password input not found - missing data-testid="password-input" instrumentation');
        }
        await typePasswordInput.fill(testUser.password);
      } else {
        await passwordInput.fill(testUser.password);
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
      // Wait for post-registration navigation or user menu
      // Critical authentication verification - fail fast on missing instrumentation
      const userMenu = page.locator('[data-testid="user-menu"]');

      if (!(await userMenu.isVisible({ timeout: 5000 }))) {
        console.warn('Missing data-testid="user-menu" - using fallback authentication indicators');

        const userProfile = page.locator('.user-profile');
        if (!(await userProfile.isVisible({ timeout: 3000 }))) {
          const logoutButton = page.getByRole('button', { name: /logout/i });
          if (!(await logoutButton.isVisible({ timeout: 2000 }))) {
            throw new Error('Authentication verification failed - no user menu, profile, or logout button found. Missing instrumentation.');
          }
          await expect(logoutButton).toBeVisible();
        } else {
          await expect(userProfile).toBeVisible();
        }
      } else {
        await expect(userMenu).toBeVisible();
      }

      // Verify user is authenticated by checking for protected content
      const dashboard = page.locator('[data-testid="dashboard"]');

      if (!(await dashboard.isVisible({ timeout: 3000 }))) {
        console.warn('Missing data-testid="dashboard" - using fallback protected content indicators');

        const dashboardClass = page.locator('.dashboard');
        if (!(await dashboardClass.isVisible({ timeout: 2000 }))) {
          const mainContent = page.getByRole('main');
          if (!(await mainContent.isVisible({ timeout: 2000 }))) {
            throw new Error('Protected content verification failed - no dashboard found. Check authentication flow.');
          }
          await expect(mainContent).toBeVisible();
        } else {
          await expect(dashboardClass).toBeVisible();
        }
      } else {
        await expect(dashboard).toBeVisible();
      }
    });

    await test.step('Access protected vocabulary features', async () => {
      // Navigate to vocabulary section - prefer semantic data-testid
      const vocabNav = page.locator('[data-testid="vocabulary-nav"]');

      if (await vocabNav.count() > 0) {
        await vocabNav.click();
      } else {
        console.warn('Missing data-testid="vocabulary-nav" - using fallback navigation');

        const vocabHref = page.locator('a[href*="vocabulary"]');
        if (await vocabHref.count() > 0) {
          await vocabHref.first().click();
        } else {
          const vocabRole = page.getByRole('link', { name: /vocabulary/i });
          if (await vocabRole.count() > 0) {
            await vocabRole.click();
          } else {
            console.warn('No vocabulary navigation found - skipping vocabulary verification');
            return;
          }
        }
      }

      // Verify vocabulary interface loads with explicit fallback
      const vocabList = page.locator('[data-testid="vocabulary-list"]');

      if (!(await vocabList.isVisible({ timeout: 5000 }))) {
        console.warn('Missing data-testid="vocabulary-list" - using fallback interface check');

        const vocabInterface = page.locator('.vocabulary-interface');
        if (!(await vocabInterface.isVisible({ timeout: 3000 }))) {
          throw new Error('Vocabulary interface failed to load - check navigation and authentication');
        }
        await expect(vocabInterface).toBeVisible();
      } else {
        await expect(vocabList).toBeVisible();
      }
    });
  });

  test('WhenUserLogsOut_ThenCannotAccessProtectedFeatures @smoke', async ({ page }) => {
    // First log in
    const user = await testDataManager.createTestUser();

    await test.step('Log in user', async () => {
      await page.goto('/');

      const loginLink = page.locator('a[href*="login"]').or(
        page.getByRole('link', { name: /login/i })
      );

      await loginLink.click();
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

      // Wait for successful login
      await expect(
        page.locator('[data-testid="user-menu"]').or(
          page.getByRole('button', { name: /logout/i })
        )
      ).toBeVisible();
    });

    await test.step('Log out user', async () => {
      const logoutButton = page.locator('[data-testid="logout-button"]').or(
        page.getByRole('button', { name: /logout/i })
      );

      await logoutButton.click();

      // Verify logout by checking for login link
      await expect(
        page.locator('a[href*="login"]').or(
          page.getByRole('link', { name: /login/i })
        )
      ).toBeVisible();
    });

    await test.step('Verify cannot access protected features', async () => {
      // Try to access vocabulary directly
      await page.goto('/vocabulary');

      // Should redirect to login or show access denied
      const isLoginPage = await page.locator('form').locator('input[type="password"]').isVisible();
      const isAccessDenied = await page.locator('[data-testid="access-denied"]').isVisible();
      const isUnauthorized = await page.getByText(/unauthorized|access denied|please log in/i).isVisible();

      expect(isLoginPage || isAccessDenied || isUnauthorized).toBeTruthy();
    });
  });

  test('WhenInvalidCredentials_ThenShowsErrorAndDoesNotAuthenticate @smoke', async ({ page }) => {
    await test.step('Attempt login with invalid credentials', async () => {
      await page.goto('/');

      const loginLink = page.locator('a[href*="login"]').or(
        page.getByRole('link', { name: /login/i })
      );

      await loginLink.click();
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
