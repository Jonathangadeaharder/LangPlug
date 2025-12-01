/**
 * Authentication Setup Project
 * Runs once before all tests, saves auth state for reuse.
 * This eliminates per-test login overhead.
 */
import { test as setup, expect } from '@playwright/test';
import path from 'path';
import { SEEDED_USERS } from './fixtures/seeded-users';
import { BASE_URL, ROUTES } from './config/urls';
import { LoginPage } from './pages/LoginPage';

const authFile = path.join(__dirname, '../playwright/.auth/user.json');

setup('authenticate', async ({ page }) => {
  const user = SEEDED_USERS.default;
  const loginPage = new LoginPage(page);

  // Navigate to login
  await loginPage.goto();
  
  // Login using POM
  await loginPage.login(user.email, user.password);

  // Wait for successful login using web-first assertion (Best Practice #4)
  await expect(page).toHaveURL(/\/videos/, { timeout: 30000 });
  
  // Verify we're actually logged in
  await expect(page.getByRole('button', { name: /logout/i })).toBeVisible();

  // Save authentication state for all other tests
  await page.context().storageState({ path: authFile });
});
