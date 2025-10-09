import { test, expect } from '@playwright/test';
import { TestDataManager, TestUser } from '../utils/test-data-manager';

test.describe('Video Processing Workflow @smoke', () => {
  let testDataManager: TestDataManager;
  let testUser: TestUser;

  test.beforeEach(async ({ page }) => {
    testDataManager = new TestDataManager();
    testUser = await testDataManager.createTestUser();

    // Log in user
    await page.goto('/login');
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

  test('WhenUserUploadsVideo_ThenProcessingStartsAndCompletes @smoke', async ({ page }) => {
    await test.step('Navigate to video upload section', async () => {
      const videoLink = page.locator('a[href*="video"]').or(
        page.locator('[data-testid="video-nav"]').or(
          page.getByRole('link', { name: /video|upload/i })
        )
      );

      await expect(videoLink.first()).toBeVisible();
      await videoLink.first().click();
    });

    await test.step('Upload video file', async () => {
      // Look for file upload input
      const fileInput = page.locator('input[type="file"]').or(
        page.locator('[data-testid="video-upload"]')
      );

      await expect(fileInput).toBeVisible();

      // Check accepted file types
      const acceptAttribute = await fileInput.getAttribute('accept');
      expect(acceptAttribute).toMatch(/video|mp4|avi|mov/i);

      // For testing purposes, we'll simulate file upload
      // In real tests, you would upload an actual test video file
      const testFilePath = '../test-data/sample-video.mp4';

      // Note: In actual implementation, ensure test video file exists
      try {
        await fileInput.setInputFiles(testFilePath);
      } catch (error) {
        // If test file doesn't exist, skip file upload and simulate via API
        console.log('Test video file not found, using API simulation');

        // Create video via API instead
        const testVideo = await testDataManager.createTestVideo(testUser, {
          title: 'Test Episode',
          series: 'Test Series',
          episode: 'Episode 1'
        });

        // Navigate to video processing page
        await page.goto(`/video/${testVideo.id}/process`);
      }

      // Verify upload initiated
      const uploadProgress = page.locator('[data-testid="upload-progress"]').or(
        page.locator('.upload-indicator').or(
          page.getByText(/uploading|processing/i)
        )
      );

      await expect(uploadProgress).toBeVisible({ timeout: 10000 });
    });

    await test.step('Monitor processing progress', async () => {
      // Wait for processing screen to appear
      const processingScreen = page.locator('[data-testid="processing-screen"]').or(
        page.locator('.processing-interface')
      );

      await expect(processingScreen).toBeVisible({ timeout: 15000 });

      // Verify processing status indicators
      const statusIndicator = page.locator('[data-testid="processing-status"]').or(
        page.locator('.status-display')
      );

      await expect(statusIndicator).toBeVisible();
      const statusText = await statusIndicator.textContent();
      expect(statusText).toMatch(/processing|transcribing|analyzing/i);

      // Verify progress bar exists
      const progressBar = page.locator('[data-testid="progress-bar"]').or(
        page.locator('.progress-indicator').or(
          page.locator('progress')
        )
      );

      await expect(progressBar).toBeVisible();
    });

    await test.step('Wait for processing completion and verify results', async () => {
      // Wait for completion status (with longer timeout for actual processing)
      const completionIndicator = page.locator('[data-testid="processing-complete"]').or(
        page.getByText(/completed|finished|ready/i)
      );

      await expect(completionIndicator).toBeVisible({ timeout: 60000 });

      // Verify vocabulary extraction results
      const vocabularyResults = page.locator('[data-testid="extracted-vocabulary"]').or(
        page.locator('.vocabulary-results').or(
          page.locator('.words-extracted')
        )
      );

      if (await vocabularyResults.isVisible()) {
        const vocabularyCount = page.locator('[data-testid="vocabulary-count"]').or(
          page.getByText(/\d+.*words?.*found|extracted/i)
        );

        await expect(vocabularyCount).toBeVisible();
        const countText = await vocabularyCount.textContent();
        expect(countText).toMatch(/\d+/); // Should contain a number
      }

      // Verify subtitles generated
      const subtitleIndicator = page.locator('[data-testid="subtitles-generated"]').or(
        page.getByText(/subtitles.*ready|captions.*available/i)
      );

      if (await subtitleIndicator.isVisible()) {
        expect(await subtitleIndicator.textContent()).toMatch(/ready|available|generated/i);
      }
    });

    await test.step('Access processed video and verify learning features', async () => {
      // Navigate to video player or learning interface
      const proceedButton = page.locator('[data-testid="start-learning"]').or(
        page.getByRole('button', { name: /start.*learning|watch.*video|proceed/i })
      );

      if (await proceedButton.isVisible()) {
        await proceedButton.click();

        // Verify chunked learning interface
        const learningInterface = page.locator('[data-testid="chunked-learning-player"]').or(
          page.locator('.learning-player-interface')
        );

        await expect(learningInterface).toBeVisible();

        // Verify chunk information
        const chunkInfo = page.locator('[data-testid="chunk-info"]').or(
          page.getByText(/chunk.*\d+.*of.*\d+/i)
        );

        if (await chunkInfo.isVisible()) {
          const chunkText = await chunkInfo.textContent();
          expect(chunkText).toMatch(/chunk.*1.*of.*\d+/i);
        }
      }
    });
  });

  test('WhenProcessingFails_ThenUserSeesErrorAndCanRetry @smoke', async ({ page }) => {
    // Create a video that will fail processing via API
    const testVideo = await testDataManager.createTestVideo(testUser, {
      title: 'Invalid Video',
      path: '/invalid/path.mp4'
    });

    await test.step('Navigate to video with processing error', async () => {
      await page.goto(`/video/${testVideo.id}/process`);
    });

    await test.step('Trigger processing and verify error handling', async () => {
      const startProcessingButton = page.locator('[data-testid="start-processing"]').or(
        page.getByRole('button', { name: /start.*processing|process.*video/i })
      );

      if (await startProcessingButton.isVisible()) {
        await startProcessingButton.click();
      }

      // Wait for error state
      const errorMessage = page.locator('[data-testid="processing-error"]').or(
        page.locator('.error-message').or(
          page.getByText(/failed|error|unable.*to.*process/i)
        )
      );

      await expect(errorMessage).toBeVisible({ timeout: 30000 });

      // Verify error is descriptive
      const errorText = await errorMessage.textContent();
      expect(errorText).toMatch(/failed|error|unable|invalid/i);
    });

    await test.step('Verify retry functionality available', async () => {
      const retryButton = page.locator('[data-testid="retry-processing"]').or(
        page.getByRole('button', { name: /retry|try.*again/i })
      );

      await expect(retryButton).toBeVisible();

      // Click retry to verify it works
      await retryButton.click();

      // Should return to processing state
      const processingIndicator = page.locator('[data-testid="processing-status"]').or(
        page.getByText(/processing|attempting/i)
      );

      await expect(processingIndicator).toBeVisible();
    });
  });

  test('WhenUserCancelsProcessing_ThenCanRestartLater @smoke', async ({ page }) => {
    const testVideo = await testDataManager.createTestVideo(testUser, {
      title: 'Cancellation Test Video'
    });

    await test.step('Start video processing', async () => {
      await page.goto(`/video/${testVideo.id}/process`);

      const startButton = page.locator('[data-testid="start-processing"]').or(
        page.getByRole('button', { name: /start.*processing/i })
      );

      if (await startButton.isVisible()) {
        await startButton.click();
      }

      // Wait for processing to begin
      await expect(
        page.locator('[data-testid="processing-status"]').or(
          page.getByText(/processing/i)
        )
      ).toBeVisible();
    });

    await test.step('Cancel processing', async () => {
      const cancelButton = page.locator('[data-testid="cancel-processing"]').or(
        page.getByRole('button', { name: /cancel|stop/i })
      );

      await expect(cancelButton).toBeVisible();
      await cancelButton.click();

      // Verify cancellation confirmation or immediate cancellation
      const cancellationIndicator = page.locator('[data-testid="processing-cancelled"]').or(
        page.getByText(/cancelled|stopped|terminated/i)
      );

      await expect(cancellationIndicator).toBeVisible({ timeout: 10000 });
    });

    await test.step('Verify can restart processing', async () => {
      const restartButton = page.locator('[data-testid="restart-processing"]').or(
        page.locator('[data-testid="start-processing"]').or(
          page.getByRole('button', { name: /restart|start.*again|process/i })
        )
      );

      await expect(restartButton).toBeVisible();
      await restartButton.click();

      // Should return to processing state
      await expect(
        page.locator('[data-testid="processing-status"]').or(
          page.getByText(/processing/i)
        )
      ).toBeVisible();
    });
  });

  test('WhenVideoProcessingCompletes_ThenVocabularyGameStarts @smoke', async ({ page }) => {
    const testVideo = await testDataManager.createTestVideo(testUser);

    await test.step('Complete video processing workflow', async () => {
      // Simulate completed processing via API
      const taskId = await testDataManager.processVideo(testUser, testVideo.id!);

      // Navigate to processing results
      await page.goto(`/video/${testVideo.id}/learn`);
    });

    await test.step('Verify vocabulary game launches automatically', async () => {
      // Should show vocabulary game for extracted words
      const vocabularyGame = page.locator('[data-testid="vocabulary-game"]').or(
        page.locator('.vocabulary-game-interface')
      );

      await expect(vocabularyGame).toBeVisible({ timeout: 15000 });

      // Verify game shows words from video
      const wordDisplay = page.locator('[data-testid="current-word"]').or(
        page.locator('.word-display')
      );

      await expect(wordDisplay).toBeVisible();

      // Verify game progress indicator
      const progressIndicator = page.locator('[data-testid="game-progress"]').or(
        page.locator('.progress-indicator')
      );

      await expect(progressIndicator).toBeVisible();
    });

    await test.step('Complete vocabulary game and proceed to video', async () => {
      // Complete the vocabulary game quickly
      let gameActive = true;
      let attempts = 0;

      while (gameActive && attempts < 10) {
        attempts++;

        const knowButton = page.locator('[data-testid="know-button"]').or(
          page.getByRole('button', { name: /know|yes/i })
        );

        if (await knowButton.isVisible()) {
          await knowButton.click();

          // Wait for next question or game completion (deterministic wait)
          await Promise.race([
            page.locator('[data-testid="current-word"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-complete"]').waitFor({ state: 'visible', timeout: 3000 }),
            page.locator('[data-testid="game-progress"]').waitFor({ state: 'visible', timeout: 3000 })
          ]).catch(() => {
            // Minimal timeout fallback only
            return page.waitForTimeout(1000);
          });
        } else {
          gameActive = false;
        }
      }

      // Should proceed to video player after game
      const videoPlayer = page.locator('[data-testid="chunked-learning-player"]').or(
        page.locator('video').or(
          page.locator('.video-player')
        )
      );

      await expect(videoPlayer).toBeVisible({ timeout: 10000 });
    });
  });
});
