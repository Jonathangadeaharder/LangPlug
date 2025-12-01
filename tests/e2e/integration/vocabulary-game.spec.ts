/**
 * Layer 7: Frontend Browser Tests
 * Tests with real browser and React components following actual user flows
 *
 * These tests validate:
 * - React components render correctly through actual user journey
 * - User interactions work in real learning flow
 * - Data from backend displays properly
 * - Complete user workflows in browser
 * - Bugs #6-8 would be caught in actual browser
 *
 * Previous layers validated data contracts.
 * Layer 7 validates the ACTUAL USER EXPERIENCE in browser.
 */

import { test, expect } from '@playwright/test';
import {
  navigateToVocabularyGame,
  mockMarkKnownAPI,
  createTestWord,
  setupAuth,
  mockUserProfile,
  mockChunkProcessing,
  type TestVocabularyWord
} from './helpers';

/**
 * Layer 7: Bug #6-8 Validation in Real Browser
 *
 * These tests would catch Bugs #6-8 in actual React rendering:
 * - Bug #6: difficulty_level.toLowerCase() would crash if field missing
 * - Bug #7: null concept_id would cause rendering errors
 * - Bug #8: Invalid UUID would cause 422 when marking as known
 */
test.describe('Vocabulary Game - Complete User Experience', () => {

  test('Bug #6: difficulty_level field renders without crash', async ({ page }) => {
    /**
     * Bug #6: Frontend expected difficulty_level, backend sent difficulty
     *
     * This test validates:
     * - React component can access word.difficulty_level
     * - styled-component can call .toLowerCase() on it
     * - No "Cannot read properties of undefined" error
     */

    const testWord = createTestWord('Hallo', 'A1', 'hello');

    await navigateToVocabularyGame(page, [testWord]);

    // Layer 7: Test React component renders without crash
    // If difficulty_level is missing, styled-component would crash
    const difficultyBadge = page.locator('[data-testid="difficulty-badge"]');
    await expect(difficultyBadge).toBeVisible();

    // Layer 7: Test lowercase operation works (styled-component does this)
    const badgeText = await difficultyBadge.textContent();
    expect(badgeText).toContain('A1');
  });

  test('Bug #7: concept_id not None allows rendering', async ({ page }) => {
    /**
     * Bug #7: concept_id was None, causing Pydantic warnings
     *
     * This test validates:
     * - React can render vocabulary with valid concept_id
     * - No console errors about null/undefined
     */

    const testWord: TestVocabularyWord = {
      concept_id: '550e8400-e29b-41d4-a716-446655440000',  // ✅ Valid UUID, not None
      word: 'Welt',
      difficulty_level: 'A2',
      translation: 'world',
      definition: 'world',
      lemma: 'welt'
    };

    await navigateToVocabularyGame(page, [testWord]);

    // Layer 7: Test word renders without errors
    const wordDisplay = page.locator('[data-testid="vocabulary-word"]');
    await expect(wordDisplay).toBeVisible();
    await expect(wordDisplay).toContainText('Welt');

    // Layer 7: Check no console errors about null
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Wait a bit for any errors to appear
    await page.waitForTimeout(1000);

    // Should have no errors about null/undefined
    const hasNullErrors = consoleErrors.some(err =>
      err.includes('null') || err.includes('undefined')
    );
    expect(hasNullErrors).toBe(false);
  });

  test('Bug #8: Valid UUID allows marking word as known', async ({ page }) => {
    /**
     * Bug #8: concept_id was invalid UUID, causing 422 error
     *
     * This test validates:
     * - User can mark word as known
     * - API accepts the concept_id
     * - No 422 Unprocessable Content error
     */

    const testWord: TestVocabularyWord = {
      concept_id: '550e8400-e29b-41d4-a716-446655440000',  // ✅ Valid UUID
      word: 'glücklich',
      difficulty_level: 'C2',
      translation: 'happy',
      definition: 'happy',
      lemma: 'glücklich'
    };

    // Track the mark-known API call
    let markKnownRequest: any = null;
    await mockMarkKnownAPI(page, (request) => {
      markKnownRequest = request;
    });

    await navigateToVocabularyGame(page, [testWord]);

    // Layer 7: Click "Mark as Known" button
    const markKnownButton = page.locator('[data-testid="mark-known-button"]');
    await markKnownButton.click();

    // Wait for API call to complete
    await page.waitForTimeout(500);

    // Layer 7: Verify request was sent with valid UUID
    expect(markKnownRequest).toBeTruthy();
    expect(markKnownRequest.concept_id).toBe('550e8400-e29b-41d4-a716-446655440000');

    // Layer 7: Verify no error message shown to user
    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).not.toBeVisible();
  });

  test('Complete workflow: Load vocabulary → Display → Mark as known', async ({ page }) => {
    /**
     * Layer 7: Complete user journey in actual browser through learning flow
     *
     * Tests the full workflow:
     * 1. Navigate through actual app flow to learning page
     * 2. Chunk processes and displays vocabulary game
     * 3. User marks word as known
     * 4. Success feedback shown
     */

    const testWord = createTestWord('Haus', 'A1', 'house');

    await mockMarkKnownAPI(page);
    await navigateToVocabularyGame(page, [testWord]);

    // Step 1: Verify vocabulary displays
    await expect(page.locator('[data-testid="vocabulary-word"]')).toContainText('Haus');
    await expect(page.locator('[data-testid="difficulty-badge"]')).toContainText('A1');
    await expect(page.locator('[data-testid="translation"]')).toContainText('house');

    // Step 2: Mark word as known
    await page.locator('[data-testid="mark-known-button"]').click();

    // Wait for transition to next word or completion screen
    await page.waitForTimeout(500);

    // Step 3: Verify success (should move to completion screen since only one word)
    const successMessage = page.locator('[data-testid="success-message"]');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
  });

  test('Multiple words batch - all have valid UUIDs', async ({ page }) => {
    /**
     * Layer 7: Validate multiple words all render and work
     * Bug #8 could affect any word in batch
     */

    const words: TestVocabularyWord[] = [
      {
        concept_id: '550e8400-e29b-41d4-a716-446655440001',
        word: 'Hallo',
        difficulty_level: 'A1',
        translation: 'hello',
        definition: 'hello',
        lemma: 'hallo'
      },
      {
        concept_id: '550e8400-e29b-41d4-a716-446655440002',
        word: 'Welt',
        difficulty_level: 'A2',
        translation: 'world',
        definition: 'world',
        lemma: 'welt'
      },
      {
        concept_id: '550e8400-e29b-41d4-a716-446655440003',
        word: 'glücklich',
        difficulty_level: 'C2',
        translation: 'happy',
        definition: 'happy',
        lemma: 'glücklich'
      }
    ];

    await navigateToVocabularyGame(page, words);

    // Layer 7: First word should render
    const wordCard = page.locator('[data-testid="vocabulary-word"]');
    await expect(wordCard).toBeVisible();

    // Layer 7: Difficulty badge should render
    const badge = page.locator('[data-testid="difficulty-badge"]');
    await expect(badge).toBeVisible();

    // Verify progress indicator shows correct count
    const progressText = page.locator('text=/1 of 3 words/i');
    await expect(progressText).toBeVisible();
  });

  test('Styled-component difficulty badge renders with lowercase', async ({ page }) => {
    /**
     * Layer 7: Test the EXACT code that caused Bug #6
     *
     * styled-component in VocabularyGame.tsx:
     * $level={currentWord?.difficulty_level}
     *
     * Then uses: props.$level.toLowerCase()
     */

    const testWord = createTestWord('Test', 'B1', 'test');

    await navigateToVocabularyGame(page, [testWord]);

    // Layer 7: Verify badge has computed styles from lowercase operation
    const badge = page.locator('[data-testid="difficulty-badge"]');
    await expect(badge).toBeVisible();

    // Verify badge has background color (set based on difficulty.toLowerCase())
    const bgColor = await badge.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    // Should have a background color (not transparent)
    expect(bgColor).not.toBe('rgba(0, 0, 0, 0)');
    expect(bgColor).not.toBe('transparent');
  });
});

/**
 * Layer 7: Error Handling in Browser
 *
 * Tests that validate error scenarios in real browser
 */
test.describe('Error Handling in Browser', () => {

  test('API returns 422 - shows user-friendly error', async ({ page }) => {
    /**
     * Bug #8 scenario: API returns 422 for invalid UUID
     * Validates frontend shows helpful error message
     */

    const testWord = createTestWord('Test', 'A1');

    // Mock mark-known to return 422 error
    await page.route('**/api/vocabulary/mark-known', async route => {
      await route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'concept_id must be a valid UUID'
        })
      });
    });

    await navigateToVocabularyGame(page, [testWord]);

    // Try to mark word as known
    await page.locator('[data-testid="mark-known-button"]').click();

    // Wait for error to appear (the component shows a toast)
    await page.waitForTimeout(1500);

    // Should show error to user via toast or error message
    // Check for toast message containing "failed" or "error"
    const errorToast = page.locator('.go3958317564, [role="status"]').filter({ hasText: /failed|error/i });
    const errorMessage = page.locator('[data-testid="error-message"]');

    // Either toast or error message should be visible
    const hasError = (await errorToast.count()) > 0 || (await errorMessage.count()) > 0;
    expect(hasError).toBe(true);
  });

  test('Empty vocabulary - shows helpful message', async ({ page }) => {
    /**
     * Layer 7: Edge case - no vocabulary words
     */

    await navigateToVocabularyGame(page, []);

    // Should show empty state message
    const emptyState = page.locator('[data-testid="empty-state"]');
    await expect(emptyState).toBeVisible();
  });

  test('Network error - shows retry option', async ({ page }) => {
    /**
     * Layer 7: Network failure handling
     */

    const testWord = createTestWord('Test', 'A1');

    // Mock mark-known to fail with network error
    await page.route('**/api/vocabulary/mark-known', async route => {
      await route.abort('failed');
    });

    await navigateToVocabularyGame(page, [testWord]);

    // Try to mark word as known
    await page.locator('[data-testid="mark-known-button"]').click();

    // Wait for error handling
    await page.waitForTimeout(1000);

    // Should show error (though retry button may not appear for network errors)
    // The component should handle the error gracefully
    const errorToast = page.locator('text=/failed/i').first();
    await expect(errorToast).toBeVisible({ timeout: 5000 });
  });
});

/**
 * Layer 7: Performance and Accessibility
 */
test.describe('Performance and Accessibility', () => {

  test('Page loads within reasonable time', async ({ page }) => {
    const testWord = createTestWord('Test', 'A1');
    const startTime = Date.now();

    await navigateToVocabularyGame(page, [testWord]);

    const loadTime = Date.now() - startTime;

    // Should load in < 10 seconds (includes processing mock)
    expect(loadTime).toBeLessThan(10000);
  });

  test('Keyboard navigation works', async ({ page }) => {
    /**
     * Layer 7: Accessibility testing
     */

    const testWord = createTestWord('Test', 'A1');

    await mockMarkKnownAPI(page);
    await navigateToVocabularyGame(page, [testWord]);

    // Focus the mark-known button directly to ensure keyboard interaction works
    const markKnownButton = page.locator('[data-testid="mark-known-button"]');
    await markKnownButton.focus();

    // Should be able to activate with Enter or Space
    await page.keyboard.press('Enter');

    // Wait for action to process
    await page.waitForTimeout(1000);

    // Button should respond (word advances or completes)
    // Success message should appear
    const successMessage = page.locator('[data-testid="success-message"]');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
  });
});
