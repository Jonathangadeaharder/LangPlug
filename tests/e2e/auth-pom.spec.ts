import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

const TEST_USER_EMAIL = `test${Date.now()}@example.com`;
const TEST_USER_PASSWORD = 'TestPassword123!';
const TEST_USERNAME = 'testuser' + Date.now().toString().slice(-6);

test.describe('Authentication E2E Tests', () => {
  let loginPage: LoginPage;
  let registerPage: RegisterPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    registerPage = new RegisterPage(page);
  });

  test('should register new user successfully', async ({ page }) => {
    // Navigate to register page
    await registerPage.goto();
    expect(await registerPage.isLoaded()).toBe(true);

    // Register new user
    await registerPage.register(TEST_USER_EMAIL, TEST_USERNAME, TEST_USER_PASSWORD);

    // Should be redirected away from register page
    const url = await page.url();
    const isRedirected = url !== 'http://127.0.0.1:3000/register';
    expect(isRedirected).toBe(true);
  });

  test('should navigate between auth pages', async () => {
    // Go to register page
    await registerPage.goto();
    expect(await registerPage.isLoaded()).toBe(true);

    // Verify we're on register page
    const url = await registerPage.getCurrentUrl();
    expect(url).toContain('/register');
  });

  test('should reject login with wrong password', async () => {
    await loginPage.goto();
    expect(await loginPage.isLoaded()).toBe(true);

    // Try to login with wrong password
    await loginPage.login('nonexistent@example.com', 'WrongPass123!');

    // Should either show error message or stay on login page
    const errorVisible = await loginPage.isErrorVisible();
    const url = await loginPage.getCurrentUrl();
    const isStillOnLogin = url.includes('/login');
    
    // Either error shown OR still on login page is acceptable
    expect(errorVisible || isStillOnLogin).toBe(true);
  });

  test('should reject empty email', async () => {
    await loginPage.goto();
    expect(await loginPage.isLoaded()).toBe(true);

    // Try with empty email - fill only password
    await loginPage.fillPassword(TEST_USER_PASSWORD);
    await loginPage.clickSubmit();

    // Should either show error or stay on login page
    const errorVisible = await loginPage.isErrorVisible();
    const url = await loginPage.getCurrentUrl();
    const isStillOnLogin = url.includes('/login');
    
    expect(errorVisible || isStillOnLogin).toBe(true);
  });
});
