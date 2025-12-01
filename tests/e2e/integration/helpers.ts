/**
 * E2E Test Helpers
 *
 * Utilities for setting up test scenarios that match actual user flows
 */

import { Page } from '@playwright/test';

export interface TestVocabularyWord {
  concept_id: string;
  word: string;
  difficulty_level: string;
  translation?: string;
  definition?: string;
  lemma: string;
}

export interface VideoInfo {
  path: string;
  series: string;
  episode: string;
  title: string;
  duration: number;
}

/**
 * Set up authentication tokens in localStorage and mock auth endpoints
 * Simulates a logged-in user
 */
export async function setupAuth(page: Page) {
  await page.addInitScript(() => {
    // Set the authToken that useAuthStore looks for
    localStorage.setItem('authToken', 'test-auth-token-12345');

    // Also set the auth-storage state that Zustand persist uses
    const authState = {
      state: {
        user: {
          id: 'test-user-uuid-12345',
          email: 'test@example.com',
          username: 'testuser',
          name: 'Test User',
          is_verified: true
        },
        isAuthenticated: true,
        token: 'test-auth-token-12345',
        redirectPath: null
      },
      version: 0
    };
    localStorage.setItem('auth-storage', JSON.stringify(authState));
  });

  // Mock the /api/auth/me endpoint that checkAuth() calls
  await page.route('**/api/auth/me', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'test-user-uuid-12345',
        email: 'test@example.com',
        username: 'testuser',
        is_active: true,
        is_verified: true,
        is_superuser: false
      })
    });
  });
}

/**
 * Mock user profile API endpoint
 * Returns native and target language preferences
 */
export async function mockUserProfile(page: Page) {
  await page.route('**/api/profile', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        native_language: {
          code: 'en',
          name: 'English'
        },
        target_language: {
          code: 'de',
          name: 'German'
        }
      })
    });
  });
}

/**
 * Mock chunk processing API to complete immediately
 * This speeds up tests by bypassing the actual processing phase
 */
export async function mockChunkProcessing(
  page: Page,
  vocabulary: TestVocabularyWord[]
) {
  const taskId = 'test-task-id-12345';

  // Mock the initial chunk processing request (POST /api/process/chunk)
  await page.route('**/api/process/chunk', async route => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          task_id: taskId,
          status: 'processing'
        })
      });
    } else {
      await route.continue();
    }
  });

  // Mock progress polling - immediately return completed status
  // Matches both /api/process/progress/:taskId and any task ID
  await page.route('**/api/process/progress/**', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'completed',
        progress: 100,
        current_step: 'Completed',
        message: 'Processing complete',
        vocabulary: vocabulary,
        subtitle_path: '/test/path/subtitles.srt',
        translation_path: '/test/path/translations.srt'
      })
    });
  });
}

/**
 * Mock vocabulary mark-known API endpoint
 */
export async function mockMarkKnownAPI(
  page: Page,
  callback?: (request: any) => void
) {
  await page.route('**/api/vocabulary/mark-known', async route => {
    const requestData = await route.request().postDataJSON();

    if (callback) {
      callback(requestData);
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        success: true,
        word: 'test',
        lemma: 'test',
        level: 'A1'
      })
    });
  });
}

/**
 * Navigate to the learning flow and wait for VocabularyGame to appear
 * This follows the actual user flow through the app
 *
 * Uses sessionStorage to inject videoInfo, which ChunkedLearningPage reads as a fallback
 * This allows us to test the actual app route without complex state manipulation
 */
export async function navigateToVocabularyGame(
  page: Page,
  vocabulary: TestVocabularyWord[],
  videoInfo: VideoInfo = {
    path: '/test/videos/test-episode.mp4',
    series: 'TestSeries',
    episode: 'E01',
    title: 'Test Episode',
    duration: 25
  }
) {
  // Set up authentication and inject videoInfo into sessionStorage
  await setupAuth(page);

  // Add videoInfo to sessionStorage so ChunkedLearningPage can read it
  await page.addInitScript((info) => {
    sessionStorage.setItem('testVideoInfo', JSON.stringify(info));
  }, videoInfo);

  // Mock APIs before navigation
  await mockUserProfile(page);
  await mockChunkProcessing(page, vocabulary);

  // Navigate to the actual learning route
  const url = `/learn/${encodeURIComponent(videoInfo.series)}/${encodeURIComponent(videoInfo.episode)}`;

  await page.goto(url, {
    waitUntil: 'networkidle'
  });

  // Wait for the VocabularyGame to appear (after processing completes)
  // If vocabulary is empty, wait for empty-state instead
  if (vocabulary.length === 0) {
    await page.waitForSelector('[data-testid="empty-state"]', {
      timeout: 15000,
      state: 'visible'
    });
  } else {
    await page.waitForSelector('[data-testid="vocabulary-word"]', {
      timeout: 15000,
      state: 'visible'
    });
  }
}

/**
 * Create a simple vocabulary word for testing
 */
export function createTestWord(
  word: string,
  difficulty: string = 'A1',
  translation?: string
): TestVocabularyWord {
  return {
    concept_id: `test-uuid-${word}-${Math.random()}`,
    word,
    difficulty_level: difficulty,
    translation: translation || `${word} translation`,
    definition: translation || `${word} definition`,
    lemma: word.toLowerCase()
  };
}
