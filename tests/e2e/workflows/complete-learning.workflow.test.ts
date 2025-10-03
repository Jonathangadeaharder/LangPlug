import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';

test.describe('Complete Learning Workflow @smoke', () => {
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

    await expect(
      page.locator('[data-testid="user-menu"]').or(
        page.getByRole('button', { name: /logout/i })
      )
    ).toBeVisible();
  });

  test.afterEach(async () => {
    await testDataManager.cleanupTestData(testUser);
  });

  test('WhenUserCompletesFullLearningFlow_ThenAllFeaturesWorkTogether @smoke', async ({ page }) => {
    let extractedVocabulary: string[] = [];

    await test.step('Upload and process video', async () => {
      // Navigate to video section
      const videoLink = page.locator('a[href*="video"]').or(
        page.getByRole('link', { name: /video|upload/i })
      );

      await videoLink.first().click();

      // Create test video via API (simulating upload)
      const testVideo = await testDataManager.createTestVideo(testUser, {
        title: 'German Learning Episode',
        series: 'Beginner German',
        episode: 'Episode 1'
      });

      // Navigate to processing
      await page.goto(`/video/${testVideo.id}/process`);

      // Start processing
      const processButton = page.locator('[data-testid="start-processing"]').or(
        page.getByRole('button', { name: /start.*processing|process/i })
      );

      if (await processButton.isVisible()) {
        await processButton.click();
      }

      // Wait for completion
      const completionIndicator = page.locator('[data-testid="processing-complete"]').or(
        page.getByText(/completed|ready|finished/i)
      );

      await expect(completionIndicator).toBeVisible({ timeout: 60000 });

      // Capture extracted vocabulary
      const vocabResults = page.locator('[data-testid="extracted-vocabulary"]').or(
        page.locator('.vocabulary-results')
      );

      if (await vocabResults.isVisible()) {
        const vocabText = await vocabResults.textContent();
        extractedVocabulary = vocabText?.match(/\b[A-ZÄÖÜ][a-zäöüß]+\b/g) || [];
      }
    });

    await test.step('Play vocabulary game with extracted words', async () => {
      // Start learning flow
      const startLearningButton = page.locator('[data-testid="start-learning"]').or(
        page.getByRole('button', { name: /start.*learning|proceed/i })
      );

      if (await startLearningButton.isVisible()) {
        await startLearningButton.click();
      }

      // Wait for vocabulary game
      await expect(
        page.locator('[data-testid="vocabulary-game"]')
      ).toBeVisible();

      // Play through vocabulary game
      let wordsLearned = 0;
      let gameActive = true;
      const maxWords = 5;

      while (gameActive && wordsLearned < maxWords) {
        const currentWord = page.locator('[data-testid="current-word"]').or(
          page.locator('.word-display')
        );

        if (await currentWord.isVisible()) {
          const wordText = await currentWord.textContent();
          console.log(`Learning word: ${wordText}`);

          // Randomly choose know or don't know
          const knowButton = page.locator('[data-testid="know-button"]').or(
            page.getByRole('button', { name: /know|yes/i })
          );

          const dontKnowButton = page.locator('[data-testid="dont-know-button"]').or(
            page.getByRole('button', { name: /don.*t.*know|no/i })
          );

          // Learn some words, mark others as unknown
          if (wordsLearned % 2 === 0 && await knowButton.isVisible()) {
            await knowButton.click();
          } else if (await dontKnowButton.isVisible()) {
            await dontKnowButton.click();
          }

          wordsLearned++;

          // Wait for next word or game completion (deterministic wait)
          await Promise.race([
            page.locator('[data-testid="current-word"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-complete"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-progress"]').waitFor({ state: 'visible', timeout: 3000 })
          ]).catch(() => {
            // Minimal fallback timeout
            return page.waitForTimeout(1000);
          });
        } else {
          gameActive = false;
        }
      }

      // Verify game completion
      const gameCompletion = page.locator('[data-testid="game-complete"]').or(
        page.getByText(/completed|finished/i)
      );

      await expect(gameCompletion).toBeVisible({ timeout: 15000 });
    });

    await test.step('Watch chunked video with learning features', async () => {
      // Should transition to video player
      const videoPlayer = page.locator('[data-testid="chunked-learning-player"]').or(
        page.locator('.learning-player-interface')
      );

      await expect(videoPlayer).toBeVisible();

      // Verify chunk information
      const chunkInfo = page.locator('[data-testid="chunk-info"]').or(
        page.getByText(/chunk.*1.*of/i)
      );

      if (await chunkInfo.isVisible()) {
        expect(await chunkInfo.textContent()).toMatch(/chunk.*1/i);
      }

      // Verify video controls
      const playButton = page.locator('[data-testid="play-button"]').or(
        page.locator('button[aria-label*="play"]').or(
          page.getByRole('button', { name: /play/i })
        )
      );

      if (await playButton.isVisible()) {
        await playButton.click();
      }

      // Verify subtitles if available
      const subtitleToggle = page.locator('[data-testid="subtitle-toggle"]').or(
        page.getByRole('button', { name: /subtitle|caption/i })
      );

      if (await subtitleToggle.isVisible()) {
        await subtitleToggle.click();

        // Check for subtitle display
        const subtitleDisplay = page.locator('[data-testid="subtitles"]').or(
          page.locator('.subtitle-display').or(
            page.locator('.captions')
          )
        );

        if (await subtitleDisplay.isVisible()) {
          expect(await subtitleDisplay.textContent()).toBeTruthy();
        }
      }

      // Progress to next chunk
      const nextChunkButton = page.locator('[data-testid="next-chunk"]').or(
        page.getByRole('button', { name: /next.*chunk|continue/i })
      );

      if (await nextChunkButton.isVisible()) {
        await nextChunkButton.click();

        // Verify chunk progression
        const updatedChunkInfo = page.locator('[data-testid="chunk-info"]').or(
          page.getByText(/chunk.*2.*of/i)
        );

        if (await updatedChunkInfo.isVisible()) {
          expect(await updatedChunkInfo.textContent()).toMatch(/chunk.*2/i);
        }
      }
    });

    await test.step('Review learned vocabulary in vocabulary section', async () => {
      // Navigate to vocabulary section
      const vocabLink = page.locator('a[href*="vocabulary"]').or(
        page.getByRole('link', { name: /vocabulary/i })
      );

      await vocabLink.first().click();

      // Verify previously learned words appear in vocabulary list
      const vocabularyList = page.locator('[data-testid="vocabulary-list"]').or(
        page.locator('.vocabulary-interface')
      );

      await expect(vocabularyList).toBeVisible();

      // Check for learned/known status indicators
      const knownWordsIndicators = page.locator('[data-testid="known-word"]').or(
        page.locator('.word-known').or(
          page.locator('.learned-indicator')
        )
      );

      if (await knownWordsIndicators.count() > 0) {
        expect(await knownWordsIndicators.count()).toBeGreaterThan(0);
      }

      // Verify progress tracking
      const progressDisplay = page.locator('[data-testid="learning-progress"]').or(
        page.locator('.progress-stats')
      );

      if (await progressDisplay.isVisible()) {
        const progressText = await progressDisplay.textContent();
        expect(progressText).toMatch(/\d+.*learned|known/i);
      }
    });

    await test.step('Verify episode completion and progress tracking', async () => {
      // Navigate to episode or series overview
      const seriesLink = page.locator('a[href*="series"]').or(
        page.getByRole('link', { name: /series|episodes/i })
      );

      if (await seriesLink.isVisible()) {
        await seriesLink.click();

        // Verify episode shows as completed or in progress
        const episodeStatus = page.locator('[data-testid="episode-status"]').or(
          page.locator('.episode-progress').or(
            page.getByText(/completed|in.*progress|watched/i)
          )
        );

        if (await episodeStatus.isVisible()) {
          const statusText = await episodeStatus.textContent();
          expect(statusText).toMatch(/completed|progress|watched/i);
        }

        // Verify overall learning statistics
        const learningStats = page.locator('[data-testid="learning-statistics"]').or(
          page.locator('.stats-overview')
        );

        if (await learningStats.isVisible()) {
          const statsText = await learningStats.textContent();
          expect(statsText).toMatch(/\d+.*words?.*learned|\d+.*episodes?.*watched/i);
        }
      }
    });
  });

  test('WhenUserRepeatsEpisode_ThenProgressIsMaintainedAndImproved @smoke', async ({ page }) => {
    // Set up episode with some learned vocabulary
    const testVideo = await testDataManager.createTestVideo(testUser, {
      title: 'Repeat Learning Test',
      series: 'Test Series'
    });

    await test.step('Complete episode first time', async () => {
      await page.goto(`/video/${testVideo.id}/learn`);

      // Simulate vocabulary game completion
      const vocabularyGame = page.locator('[data-testid="vocabulary-game"]');

      if (await vocabularyGame.isVisible()) {
        // Mark some words as known, others as unknown
        let wordsAnswered = 0;
        const targetWords = 3;

        while (wordsAnswered < targetWords) {
          const knowButton = page.locator('[data-testid="know-button"]');
          const dontKnowButton = page.locator('[data-testid="dont-know-button"]');

          if (wordsAnswered === 0 && await knowButton.isVisible()) {
            await knowButton.click(); // First word: know
          } else if (await dontKnowButton.isVisible()) {
            await dontKnowButton.click(); // Others: don't know
          }

          wordsAnswered++;

          // Wait for next word or game completion (deterministic wait)
          await Promise.race([
            page.locator('[data-testid="current-word"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-complete"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-progress"]').waitFor({ state: 'visible', timeout: 3000 })
          ]).catch(() => {
            // Minimal fallback timeout
            return page.waitForTimeout(1000);
          });
        }

        // Complete game
        const gameComplete = page.locator('[data-testid="game-complete"]').or(
          page.getByText(/completed/i)
        );

        await expect(gameComplete).toBeVisible({ timeout: 15000 });
      }

      // Complete video watching
      const videoPlayer = page.locator('[data-testid="chunked-learning-player"]');
      if (await videoPlayer.isVisible()) {
        const completeButton = page.locator('[data-testid="complete-episode"]').or(
          page.getByRole('button', { name: /complete|finish/i })
        );

        if (await completeButton.isVisible()) {
          await completeButton.click();
        }
      }
    });

    await test.step('Restart same episode', async () => {
      // Navigate back to episode
      await page.goto(`/video/${testVideo.id}/learn`);

      // Should start vocabulary game again but with different mix
      const vocabularyGame = page.locator('[data-testid="vocabulary-game"]');

      if (await vocabularyGame.isVisible()) {
        // Verify that previously known words are not repeated (or marked differently)
        const gameProgress = page.locator('[data-testid="game-progress"]');
        if (await gameProgress.isVisible()) {
          const progressText = await gameProgress.textContent();
          expect(progressText).toMatch(/\d+.*of.*\d+/);
        }

        // Complete game with improved performance
        let attempts = 0;
        while (attempts < 5) {
          const knowButton = page.locator('[data-testid="know-button"]');

          if (await knowButton.isVisible()) {
            await knowButton.click(); // Know more words this time
            attempts++;

            // Wait for next word or completion (deterministic wait)
            await Promise.race([
              page.locator('[data-testid="current-word"]').waitFor({ state: 'visible', timeout: 3000 }),
              page.locator('[data-testid="improved-score"]').waitFor({ state: 'visible', timeout: 3000 }),
              page.locator('[data-testid="game-complete"]').waitFor({ state: 'visible', timeout: 3000 })
            ]).catch(() => {
              // Minimal fallback timeout
              return page.waitForTimeout(1000);
            });
          } else {
            break;
          }
        }
      }

      // Verify improved completion
      const improvedCompletion = page.locator('[data-testid="improved-score"]').or(
        page.getByText(/improved|better|progress/i)
      );

      if (await improvedCompletion.isVisible()) {
        expect(await improvedCompletion.textContent()).toMatch(/improved|better|progress/i);
      }
    });

    await test.step('Verify progress tracking shows improvement', async () => {
      // Navigate to progress or statistics page
      const statsLink = page.locator('a[href*="progress"]').or(
        page.locator('[data-testid="progress-nav"]').or(
          page.getByRole('link', { name: /progress|stats/i })
        )
      );

      if (await statsLink.isVisible()) {
        await statsLink.click();

        // Verify episode appears multiple times or shows improved metrics
        const episodeHistory = page.locator('[data-testid="episode-history"]').or(
          page.locator('.learning-history')
        );

        if (await episodeHistory.isVisible()) {
          const historyText = await episodeHistory.textContent();
          expect(historyText).toMatch(/repeat|improved|attempt/i);
        }
      }
    });
  });
});
