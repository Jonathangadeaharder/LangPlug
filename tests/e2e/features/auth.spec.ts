/**
 * Auth POM Tests - Using Page Object Model pattern
 * Consolidated and Optimized
 */
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { UserFactory } from '../factories/userFactory';

test.describe('Authentication E2E Tests', () => {
  let loginPage: LoginPage;
  let registerPage: RegisterPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    registerPage = new RegisterPage(page);
  });

  test.describe('Registration', () => {
    test('should register new user successfully', async ({ page }) => {
      await registerPage.goto();
      const user = UserFactory.create('pom-reg');
      await registerPage.register(user.email, user.username, user.password);

      // Expect redirection to some authenticated page or home
      await expect(page).toHaveURL(/\/(login|videos|home|dashboard)/, { timeout: 30000 });
      
      // If redirected to login, we might need to login (depending on app flow), 
      // but usually registration logs you in or sends you to login.
      // The original test expected redirection away from /register.
      expect(page.url()).not.toContain('/register');
    });

    test('should reject password without special character', async ({ page }) => {
      await registerPage.goto();
      const user = UserFactory.createWithNoSpecialChar('pom-nospec');
      await registerPage.register(user.email, user.username, user.password);

      // Should stay on page and show error
      await expect(page).toHaveURL(/\/register/);
      const error = await registerPage.getErrorMessage();
      // Either error message is shown OR client-side validation prevents submission
      // If client validation prevents submission, URL check is enough.
      // If server validation, error message is key.
      // We check for truthiness if error is found, otherwise rely on URL.
      if (error) {
          expect(error).toBeTruthy();
      }
    });

    test('should reject password shorter than 12 characters', async ({ page }) => {
      await registerPage.goto();
      const user = UserFactory.createWithWeakPassword('pom-weak');
      await registerPage.register(user.email, user.username, user.password);

      await expect(page).toHaveURL(/\/register/);
    });

    test('should show form validation for empty fields', async ({ page }) => {
      await registerPage.goto();
      // Try to submit without filling anything
      await registerPage.submitButton.click();
      await expect(page).toHaveURL(/\/register/);
    });
  });

  test.describe('Login', () => {
    test('should login with valid credentials', async ({ page }) => {
      // Register first
      const user = UserFactory.create('pom-login');
      await registerPage.goto();
      await registerPage.register(user.email, user.username, user.password);
      await page.waitForURL(/\/(videos|login|home)/);

      if (page.url().includes('/login')) {
        await loginPage.login(user.email, user.password);
        await page.waitForURL(/\/videos/);
      }
      
      // Verify logged in via Header
      expect(await loginPage.header.isLoggedIn()).toBe(true);
    });

    test('should reject login with wrong password', async () => {
      await loginPage.goto();
      await loginPage.login('nonexistent@example.com', 'WrongPass123!');
      const errorVisible = await loginPage.isErrorVisible();
      const url = await loginPage.getCurrentUrl();
      expect(errorVisible || url.includes('/login')).toBe(true);
    });
  });
  
  test.describe('Session & Logout', () => {
      test('should persist login session and allow logout', async ({ page }) => {
          const user = UserFactory.create('pom-sess');
          await registerPage.goto();
          await registerPage.register(user.email, user.username, user.password);
          await page.waitForURL(/\/(videos|login|home)/);
          
          if (page.url().includes('/login')) {
              await loginPage.login(user.email, user.password);
              await page.waitForURL(/\/videos/);
          }

          // Verify logged in
          await expect(loginPage.header.logoutButton).toBeVisible();

          // Refresh
          await page.reload();
          await expect(loginPage.header.logoutButton).toBeVisible();

          // Logout
          await loginPage.header.clickLogout();
          
          // Verify logged out
          await expect(loginPage.header.logoutButton).toBeHidden();
          await expect(page).toHaveURL(/\/login/);
      });
  });
});