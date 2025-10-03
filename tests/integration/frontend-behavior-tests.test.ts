/**
 * Behavior-Focused Frontend Integration Tests @smoke
 *
 * These tests require manual server setup and are classified as smoke tests
 * per ~/.claude/CLAUDE.md process isolation requirements.
 *
 * Manual Setup Required:
 * 1. Backend: cd Backend && python run_backend.py
 * 2. Frontend: cd Frontend && npm run dev
 * 3. Run: E2E_SMOKE_TESTS=1 npm test
 */

import { test, expect, Page } from '@playwright/test';
import { testEnvironment } from '../shared/config/test-environment';
import { testFixtures, withTestSession, withAuthenticatedUser, TestSession } from '../shared/fixtures/test-fixtures';

test.describe('Frontend Behavior Integration Tests @smoke', () => {
  let environment: any;

  test.beforeAll(async () => {
    // Note: No browser spawning - violates process isolation rules
    // Tests now require manual server setup per ~/.claude/CLAUDE.md
    environment = await testEnvironment.getEnvironment();

    console.log('⚠️  Smoke Test - Manual Setup Required');
    console.log(`Frontend URL: ${environment.frontendUrl}`);
    console.log(`Backend URL: ${environment.backendUrl}`);
  });

  test.afterAll(async () => {
    await testFixtures.cleanupAllSessions();
  });

  test.describe('Authentication Workflows', () => {
    test('should complete full registration workflow with form validation @smoke', async ({ page }) => {
      await withTestSession('registration-workflow', async (session: TestSession) => {

        try {
          // Navigate to registration page
          await page.goto(`${environment.frontendUrl}/register`);

          // Verify registration form exists with semantic selectors
          const formExists = await DomAssertions.assertElementExists(
            page,
            '[data-testid="registration-form"], form[action*="register"], form:has(input[type="email"])'
          );
          assertResult(formExists, 'registration-form-presence');

          // Fill registration form with test user data
          const usernameInput = await page.waitForSelector(
            '[data-testid="username-input"], input[name="username"], input[placeholder*="username" i]'
          );
          const emailInput = await page.waitForSelector(
            '[data-testid="email-input"], input[type="email"], input[name="email"]'
          );
          const passwordInput = await page.waitForSelector(
            '[data-testid="password-input"], input[type="password"], input[name="password"]'
          );
          const submitButton = await page.waitForSelector(
            '[data-testid="register-button"], button[type="submit"], button:has-text("register"), button:has-text("sign up")'
          );

          // Verify all form elements are present and functional
          expect(usernameInput).toBeTruthy();
          expect(emailInput).toBeTruthy();
          expect(passwordInput).toBeTruthy();
          expect(submitButton).toBeTruthy();

          // Fill form with valid test data
          await usernameInput.type(session.user.username);
          await emailInput.type(session.user.email);
          await passwordInput.type(session.user.password);

          // Submit form and verify success
          const submitResult = await WorkflowAssertions.assertFormSubmissionSuccess(
            page,
            '/login', // Expected redirect after registration
            '[data-testid="registration-success"], .success-message'
          );
          assertResult(submitResult, 'registration-submission');

          // Verify user can now log in (complete workflow)
          const currentUrl = page.url();
          if (currentUrl.includes('/login')) {
            // Fill login form
            const loginEmailInput = await page.waitForSelector(
              '[data-testid="email-input"], input[type="email"]'
            );
            const loginPasswordInput = await page.waitForSelector(
              '[data-testid="password-input"], input[type="password"]'
            );
            const loginButton = await page.waitForSelector(
              '[data-testid="login-button"], button[type="submit"]'
            );

            await loginEmailInput.type(session.user.email);
            await loginPasswordInput.type(session.user.password);
            await loginButton.click();

            // Verify successful login (redirect or auth token)
            await page.waitForFunction(() =>
              window.location.pathname === '/dashboard' ||
              window.location.pathname === '/videos' ||
              localStorage.getItem('access_token') !== null
            );

            const finalUrl = page.url();
            expect(finalUrl).not.toContain('/login'); // Should be redirected away from login
          }
        } finally {
          await page.close();
        }
      });
    });

    it('should handle invalid login credentials with proper error display', async () => {
      const page = await browser.newPage();

      try {
        await page.goto(`${environment.frontendUrl}/login`);

        // Fill login form with invalid credentials
        const emailInput = await page.waitForSelector('[data-testid="email-input"], input[type="email"]');
        const passwordInput = await page.waitForSelector('[data-testid="password-input"], input[type="password"]');
        const loginButton = await page.waitForSelector('[data-testid="login-button"], button[type="submit"]');

        await emailInput.type('invalid@example.com');
        await passwordInput.type('wrongpassword');
        await loginButton.click();

        // Verify error message appears
        const errorVisible = await DomAssertions.assertElementExists(
          page,
          '[data-testid="login-error"], .error-message, .alert-error',
          10000
        );
        assertResult(errorVisible, 'login-error-display');

        // Verify user remains on login page
        await page.waitForTimeout(2000); // Wait for any redirects
        const finalUrl = page.url();
        expect(finalUrl).toContain('/login');

        // Verify no auth token is stored
        const hasAuthToken = await page.evaluate(() =>
          localStorage.getItem('access_token') !== null ||
          localStorage.getItem('auth_token') !== null
        );
        expect(hasAuthToken).toBe(false);
      } finally {
        await page.close();
      }
    });
  });

  describe('Vocabulary Feature Workflows', () => {
    it('should display and interact with vocabulary learning interface', async () => {
      await withAuthenticatedUser('vocabulary-interface', async (session: TestSession, user) => {
        const page = await browser.newPage();

        try {
          // Set authentication token if available
          if (user.accessToken) {
            await page.evaluate((token) => {
              localStorage.setItem('access_token', token);
            }, user.accessToken);
          }

          // Navigate to vocabulary page
          await page.goto(`${environment.frontendUrl}/vocabulary`);

          // Verify vocabulary interface loads
          const vocabularyInterface = await DomAssertions.assertElementExists(
            page,
            '[data-testid="vocabulary-interface"], [data-testid="vocabulary-list"], .vocabulary-container'
          );
          assertResult(vocabularyInterface, 'vocabulary-interface-presence');

          // Verify vocabulary game/learning components
          const learningComponents = await Promise.allSettled([
            DomAssertions.assertElementExists(page, '[data-testid="vocabulary-game"], .vocabulary-game'),
            DomAssertions.assertElementExists(page, '[data-testid="word-list"], .word-list'),
            DomAssertions.assertElementExists(page, '[data-testid="level-selector"], select[name="level"]')
          ]);

          // At least one learning component should be present
          const hasLearningComponents = learningComponents.some(result =>
            result.status === 'fulfilled' && result.value.success
          );
          expect(hasLearningComponents).toBe(true);

          // Test vocabulary level filtering if available
          const levelSelector = await page.$('[data-testid="level-selector"], select[name="level"]');
          if (levelSelector) {
            await levelSelector.select('A1');

            // Wait for content to update
            await page.waitForTimeout(2000);

            // Verify vocabulary content updates (not counting elements!)
            const contentUpdated = await page.evaluate(() => {
              const wordElements = document.querySelectorAll('[data-testid="vocabulary-word"], .vocabulary-word');
              return wordElements.length > 0; // Just check if words are present
            });

            expect(contentUpdated).toBe(true);
          }
        } finally {
          await page.close();
        }
      });
    });

    it('should handle vocabulary game interactions correctly', async () => {
      await withAuthenticatedUser('vocabulary-game', async (session: TestSession, user) => {
        const page = await browser.newPage();

        try {
          // Set authentication token
          if (user.accessToken) {
            await page.evaluate((token) => {
              localStorage.setItem('access_token', token);
            }, user.accessToken);
          }

          // Navigate to vocabulary game
          await page.goto(`${environment.frontendUrl}/vocabulary/game`);

          // Verify game interface loads
          const gameInterface = await DomAssertions.assertElementExists(
            page,
            '[data-testid="vocabulary-game"], .vocabulary-game, .game-container'
          );
          assertResult(gameInterface, 'vocabulary-game-interface');

          // Look for game interaction elements
          const gameElements = await Promise.allSettled([
            DomAssertions.assertElementExists(page, '[data-testid="game-question"], .game-question'),
            DomAssertions.assertElementExists(page, '[data-testid="answer-options"], .answer-options'),
            DomAssertions.assertElementExists(page, '[data-testid="submit-answer"], button.submit-answer')
          ]);

          // Game should have interactive elements
          const hasGameElements = gameElements.some(result =>
            result.status === 'fulfilled' && result.value.success
          );
          expect(hasGameElements).toBe(true);

          // Test answer submission if elements exist
          const answerButton = await page.$('[data-testid="answer-option"], .answer-option, input[type="radio"]');
          const submitButton = await page.$('[data-testid="submit-answer"], button.submit-answer, button[type="submit"]');

          if (answerButton && submitButton) {
            await answerButton.click();
            await submitButton.click();

            // Verify game responds to answer
            const gameResponse = await Promise.race([
              DomAssertions.assertElementExists(page, '[data-testid="answer-feedback"], .answer-feedback'),
              DomAssertions.assertElementExists(page, '[data-testid="next-question"], .next-question'),
              new Promise(resolve => setTimeout(() => resolve({ success: false }), 5000))
            ]);

            // Game should provide feedback or progress
            expect((gameResponse as any).success).toBe(true);
          }
        } finally {
          await page.close();
        }
      });
    });
  });

  describe('Video Processing Workflows', () => {
    it('should display video processing interface with upload capability', async () => {
      await withAuthenticatedUser('video-processing', async (session: TestSession, user) => {
        const page = await browser.newPage();

        try {
          // Set authentication token
          if (user.accessToken) {
            await page.evaluate((token) => {
              localStorage.setItem('access_token', token);
            }, user.accessToken);
          }

          // Navigate to video processing page
          await page.goto(`${environment.frontendUrl}/videos`);

          // Verify video interface loads
          const videoInterface = await DomAssertions.assertElementExists(
            page,
            '[data-testid="video-interface"], .video-interface, .video-container'
          );
          assertResult(videoInterface, 'video-interface-presence');

          // Check for upload capability
          const uploadElements = await Promise.allSettled([
            DomAssertions.assertElementExists(page, '[data-testid="video-upload"], input[type="file"]'),
            DomAssertions.assertElementExists(page, '[data-testid="upload-button"], .upload-button'),
            DomAssertions.assertElementExists(page, '[data-testid="upload-area"], .upload-area')
          ]);

          // Should have upload capability
          const hasUploadCapability = uploadElements.some(result =>
            result.status === 'fulfilled' && result.value.success
          );
          expect(hasUploadCapability).toBe(true);

          // Verify video list or processing status area
          const videoListExists = await DomAssertions.assertElementExists(
            page,
            '[data-testid="video-list"], .video-list, .processed-videos'
          );

          // Either video list exists OR this is an upload-only page
          if (!videoListExists.success) {
            // If no video list, should at least have processing status area
            const statusArea = await DomAssertions.assertElementExists(
              page,
              '[data-testid="processing-status"], .processing-status, .status-area'
            );
            assertResult(statusArea, 'video-status-area');
          }
        } finally {
          await page.close();
        }
      });
    });

    it('should handle video processing progress display', async () => {
      await withAuthenticatedUser('video-progress', async (session: TestSession, user) => {
        const page = await browser.newPage();

        try {
          // Set authentication token
          if (user.accessToken) {
            await page.evaluate((token) => {
              localStorage.setItem('access_token', token);
            }, user.accessToken);
          }

          // Navigate to video processing page
          await page.goto(`${environment.frontendUrl}/videos/processing`);

          // Wait for processing interface or redirect
          await page.waitForTimeout(3000);

          const currentUrl = page.url();

          // Should either show processing interface or redirect to videos
          if (currentUrl.includes('/processing')) {
            // Verify processing interface
            const processingInterface = await DomAssertions.assertElementExists(
              page,
              '[data-testid="processing-progress"], .processing-progress, .progress-container'
            );
            assertResult(processingInterface, 'processing-interface');

            // Look for progress indicators
            const progressElements = await Promise.allSettled([
              DomAssertions.assertElementExists(page, '[data-testid="progress-bar"], .progress-bar'),
              DomAssertions.assertElementExists(page, '[data-testid="processing-status"], .processing-status'),
              DomAssertions.assertElementExists(page, '[data-testid="progress-percentage"], .progress-percentage')
            ]);

            const hasProgressIndicators = progressElements.some(result =>
              result.status === 'fulfilled' && result.value.success
            );
            expect(hasProgressIndicators).toBe(true);
          } else {
            // If redirected, verify we're on a valid page
            expect(currentUrl).toMatch(/\/(videos|dashboard)/);
          }
        } finally {
          await page.close();
        }
      });
    });
  });

  describe('Navigation and Error Handling', () => {
    it('should handle 404 pages with proper error display', async () => {
      const page = await browser.newPage();

      try {
        // Navigate to non-existent page
        await page.goto(`${environment.frontendUrl}/nonexistent-page-${Date.now()}`);

        // Verify 404 handling
        const has404Content = await Promise.race([
          DomAssertions.assertElementExists(page, '[data-testid="not-found"], .not-found, .error-404'),
          page.waitForFunction(() =>
            document.body.textContent?.includes('404') ||
            document.body.textContent?.includes('Not Found') ||
            document.body.textContent?.includes('Page not found'),
            { timeout: 10000 }
          ).then(() => ({ success: true, message: '404 text found' }))
        ]);

        assertResult(has404Content as any, '404-error-handling');

        // Verify navigation back to valid pages works
        const homeLink = await page.$('[data-testid="home-link"], a[href="/"], .nav-home');
        if (homeLink) {
          await homeLink.click();
          await page.waitForNavigation();

          const homeUrl = page.url();
          expect(homeUrl).toMatch(/\/(home|dashboard|videos)?$/);
        }
      } finally {
        await page.close();
      }
    });

    it('should maintain authentication state across navigation', async () => {
      await withAuthenticatedUser('auth-persistence', async (session: TestSession, user) => {
        const page = await browser.newPage();

        try {
          // Set authentication token
          if (user.accessToken) {
            await page.evaluate((token) => {
              localStorage.setItem('access_token', token);
            }, user.accessToken);
          }

          // Navigate through different pages
          const testPages = ['/dashboard', '/videos', '/vocabulary'];

          for (const pagePath of testPages) {
            await page.goto(`${environment.frontendUrl}${pagePath}`);
            await page.waitForTimeout(2000);

            // Verify authentication is maintained (not redirected to login)
            const currentUrl = page.url();
            expect(currentUrl).not.toContain('/login');

            // Verify auth token persists
            const hasAuthToken = await page.evaluate(() =>
              localStorage.getItem('access_token') !== null
            );
            expect(hasAuthToken).toBe(true);
          }
        } finally {
          await page.close();
        }
      });
    });
  });
});
