import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';

test.describe('Vocabulary Learning Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();

    // Log in user
    await page.goto('/');
    const loginLink = page.locator('a[href*="login"]').or(
      page.getByRole('link', { name: /login/i })
    );

    await loginLink.click();
    await page.locator('input[name="email"]').fill(testUser.email);
    await page.locator('input[name="password"]').fill(testUser.password);
    await page.locator('button[type="submit"]').click();

    // Wait for authentication
    await expect(
      page.locator('[data-testid="user-menu"]').or(
        page.getByRole('button', { name: /logout/i })
      )
    ).toBeVisible();
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  test('WhenUserPlaysVocabularyGame_ThenProgressIsTrackedCorrectly @smoke', async ({ page }) => {
    // Create test vocabulary through API
    await testDataManager.createTestVocabulary(testUser, {
      word: 'Hallo',
      translation: 'Hello',
      difficulty_level: 'beginner'
    });

    await testDataManager.createTestVocabulary(testUser, {
      word: 'Tschüss',
      translation: 'Goodbye',
      difficulty_level: 'beginner'
    });

    await test.step('Navigate to vocabulary game', async () => {
      const vocabLink = page.locator('a[href*="vocabulary"]').or(
        page.locator('[data-testid="vocabulary-nav"]').or(
          page.getByRole('link', { name: /vocabulary/i })
        )
      );

      await vocabLink.first().click();

      // Look for start game button
      const startGameButton = page.locator('[data-testid="start-game"]').or(
        page.locator('[data-testid="vocabulary-game-start"]').or(
          page.getByRole('button', { name: /start.*game|play.*game|practice/i })
        )
      );

      await expect(startGameButton).toBeVisible();
      await startGameButton.click();
    });

    await test.step('Play vocabulary game and verify progress tracking', async () => {
      // Wait for game interface to load
      await expect(
        page.locator('[data-testid="vocabulary-game"]').or(
          page.locator('.vocabulary-game-interface')
        )
      ).toBeVisible();

      // Verify game shows vocabulary word
      const wordDisplay = page.locator('[data-testid="current-word"]').or(
        page.locator('.word-display')
      );

      await expect(wordDisplay).toBeVisible();
      const displayedWord = await wordDisplay.textContent();
      expect(['Hallo', 'Tschüss']).toContain(displayedWord?.trim());

      // Verify progress indicator
      const progressIndicator = page.locator('[data-testid="game-progress"]').or(
        page.locator('.progress-indicator')
      );

      await expect(progressIndicator).toBeVisible();
      const initialProgress = await progressIndicator.textContent();
      expect(initialProgress).toMatch(/1.*of.*\d+/); // Should show "1 of X"

      // Answer the word correctly using semantic selector
      const knowButton = page.locator('[data-testid="know-button"]').or(
        page.getByRole('button', { name: /know|correct|yes/i }).or(
          page.locator('.know-answer-button')
        )
      );

      await expect(knowButton).toBeVisible();
      await knowButton.click();

      // Verify progress updates
      const updatedProgress = await progressIndicator.textContent();
      expect(updatedProgress).toMatch(/2.*of.*\d+/); // Should advance
    });

    await test.step('Complete game and verify results', async () => {
      // Continue until game completion
      let gameCompleted = false;
      let attempts = 0;
      const maxAttempts = 10;

      while (!gameCompleted && attempts < maxAttempts) {
        attempts++;

        const knowButton = page.locator('[data-testid="know-button"]').or(
          page.getByRole('button', { name: /know|correct|yes/i })
        );

        if (await knowButton.isVisible()) {
          await knowButton.click();

          // Wait for question transition or game completion (deterministic wait)
          await Promise.race([
            page.locator('[data-testid="current-word"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-complete"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-progress"]').waitFor({ state: 'visible', timeout: 3000 })
          ]).catch(() => {
            // Only use timeout as absolute fallback when no observable state changes occur
            return page.waitForTimeout(1000);
          });
        } else {
          gameCompleted = true;
        }
      }

      // Verify game completion
      const completionMessage = page.locator('[data-testid="game-complete"]').or(
        page.locator('.game-completion').or(
          page.getByText(/completed|finished|well done|congratulations/i)
        )
      );

      await expect(completionMessage).toBeVisible({ timeout: 10000 });

      // Verify score or results display
      const scoreDisplay = page.locator('[data-testid="game-score"]').or(
        page.locator('.score-display').or(
          page.locator('.results-summary')
        )
      );

      await expect(scoreDisplay).toBeVisible();
    });
  });

  test('WhenUserAddsCustomVocabulary_ThenItAppearsInLearningSession @smoke', async ({ page }) => {
    await test.step('Navigate to vocabulary management', async () => {
      const vocabLink = page.locator('a[href*="vocabulary"]').or(
        page.getByRole('link', { name: /vocabulary/i })
      );

      await vocabLink.first().click();

      // Find add vocabulary button
      const addButton = page.locator('[data-testid="add-vocabulary"]').or(
        page.getByRole('button', { name: /add.*word|new.*word/i })
      );

      await expect(addButton).toBeVisible();
      await addButton.click();
    });

    await test.step('Add custom vocabulary word', async () => {
      // Wait for add vocabulary form/modal
      const addForm = page.locator('[data-testid="add-vocabulary-form"]').or(
        page.locator('.add-vocabulary-modal').or(
          page.locator('form').filter({ hasText: /add.*vocabulary|new.*word/i })
        )
      );

      await expect(addForm).toBeVisible();

      const customWord = {
        word: 'Wunderbar',
        translation: 'Wonderful'
      };

      // Fill form fields
      await page.locator('input[name="word"]').or(
        page.locator('[data-testid="word-input"]')
      ).fill(customWord.word);

      await page.locator('input[name="translation"]').or(
        page.locator('[data-testid="translation-input"]')
      ).fill(customWord.translation);

      // Select difficulty if available
      const difficultySelect = page.locator('select[name="difficulty"]').or(
        page.locator('[data-testid="difficulty-select"]')
      );

      if (await difficultySelect.isVisible()) {
        await difficultySelect.selectOption('intermediate');
      }

      // Submit form
      const submitButton = page.locator('button[type="submit"]').or(
        page.getByRole('button', { name: /save|add|create/i })
      );

      await submitButton.click();

      // Verify success message or return to list
      const successIndicator = page.locator('[data-testid="success-message"]').or(
        page.getByText(/added|created|saved/i).or(
          page.locator('.vocabulary-list')
        )
      );

      await expect(successIndicator).toBeVisible();
    });

    await test.step('Verify custom word appears in learning game', async () => {
      // Start a vocabulary game
      const startGameButton = page.locator('[data-testid="start-game"]').or(
        page.getByRole('button', { name: /start.*game|play.*game|practice/i })
      );

      await startGameButton.click();

      // Look for our custom word in the game
      await expect(
        page.locator('[data-testid="vocabulary-game"]')
      ).toBeVisible();

      let foundCustomWord = false;
      let attempts = 0;
      const maxAttempts = 5;

      while (!foundCustomWord && attempts < maxAttempts) {
        attempts++;

        const wordDisplay = page.locator('[data-testid="current-word"]').or(
          page.locator('.word-display')
        );

        const displayedWord = await wordDisplay.textContent();

        if (displayedWord?.includes('Wunderbar')) {
          foundCustomWord = true;
          expect(displayedWord).toContain('Wunderbar');
        } else {
          // Skip to next word if available
          const skipButton = page.locator('[data-testid="skip-button"]').or(
            page.getByRole('button', { name: /skip|next/i })
          );

          if (await skipButton.isVisible()) {
            await skipButton.click();

            // Wait for next word to appear (deterministic wait on state change)
            await Promise.race([
              page.locator('[data-testid="current-word"]').waitFor({ state: 'visible', timeout: 3000 }),
              page.locator('[data-testid="game-complete"]').waitFor({ state: 'visible', timeout: 3000 })
            ]).catch(() => {
              // Minimal fallback only when state doesn't change as expected
              return page.waitForTimeout(1000);
            });
          } else {
            break;
          }
        }
      }

      // Custom word should appear in game (may require multiple attempts)
      expect(foundCustomWord).toBeTruthy();
    });
  });

  test('WhenUserFiltersVocabularyByDifficulty_ThenOnlyRelevantWordsAppear @smoke', async ({ page }) => {
    // Create vocabulary with different difficulty levels
    await testDataManager.createTestVocabulary(testUser, {
      word: 'Ja',
      translation: 'Yes',
      difficulty_level: 'beginner'
    });

    await testDataManager.createTestVocabulary(testUser, {
      word: 'Vielleicht',
      translation: 'Maybe',
      difficulty_level: 'intermediate'
    });

    await testDataManager.createTestVocabulary(testUser, {
      word: 'Selbstverständlich',
      translation: 'Obviously',
      difficulty_level: 'advanced'
    });

    await test.step('Navigate to vocabulary list and apply difficulty filter', async () => {
      const vocabLink = page.locator('a[href*="vocabulary"]').or(
        page.getByRole('link', { name: /vocabulary/i })
      );

      await vocabLink.first().click();

      // Look for difficulty filter
      const difficultyFilter = page.locator('[data-testid="difficulty-filter"]').or(
        page.locator('select').filter({ hasText: /difficulty/i }).or(
          page.locator('.filter-dropdown')
        )
      );

      await expect(difficultyFilter).toBeVisible();

      // Select intermediate difficulty
      await difficultyFilter.selectOption('intermediate');

      // Wait for filter to apply - check for filtered results
      await page.locator('[data-testid="vocabulary-item"]').first().waitFor({ state: 'visible', timeout: 5000 });
    });

    await test.step('Verify only intermediate vocabulary appears', async () => {
      const vocabularyItems = page.locator('[data-testid="vocabulary-item"]').or(
        page.locator('.vocabulary-card').or(
          page.locator('.word-entry')
        )
      );

      await expect(vocabularyItems).toHaveCount({ min: 1 });

      // Check that visible items contain intermediate word
      const visibleText = await page.textContent('body');
      expect(visibleText).toContain('Vielleicht');

      // Should not contain beginner or advanced words when filtered
      expect(visibleText).not.toContain('Ja');
      expect(visibleText).not.toContain('Selbstverständlich');
    });

    await test.step('Start game with filtered vocabulary', async () => {
      const startGameButton = page.locator('[data-testid="start-game"]').or(
        page.getByRole('button', { name: /start.*game|practice/i })
      );

      if (await startGameButton.isVisible()) {
        await startGameButton.click();

        await expect(
          page.locator('[data-testid="vocabulary-game"]')
        ).toBeVisible();

        // Game should only show intermediate words
        const wordDisplay = page.locator('[data-testid="current-word"]').or(
          page.locator('.word-display')
        );

        const displayedWord = await wordDisplay.textContent();
        expect(displayedWord).toContain('Vielleicht');
      }
    });
  });
});
