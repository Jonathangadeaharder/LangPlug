/**
 * API Mocking Utilities (Best Practice #3)
 * Mock external dependencies to improve test reliability.
 */
import { Page, Route } from '@playwright/test';

/**
 * Mock API response helper
 */
export async function mockApiResponse(
  page: Page,
  urlPattern: string | RegExp,
  response: {
    status?: number;
    body?: unknown;
    headers?: Record<string, string>;
  }
): Promise<void> {
  await page.route(urlPattern, async (route: Route) => {
    await route.fulfill({
      status: response.status ?? 200,
      contentType: 'application/json',
      body: JSON.stringify(response.body ?? {}),
      headers: response.headers,
    });
  });
}

/**
 * Mock slow API to test loading states
 */
export async function mockSlowApi(
  page: Page,
  urlPattern: string | RegExp,
  delayMs: number,
  response: unknown
): Promise<void> {
  await page.route(urlPattern, async (route: Route) => {
    await new Promise(resolve => setTimeout(resolve, delayMs));
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

/**
 * Mock API error
 */
export async function mockApiError(
  page: Page,
  urlPattern: string | RegExp,
  statusCode: number = 500,
  errorMessage: string = 'Internal Server Error'
): Promise<void> {
  await page.route(urlPattern, async (route: Route) => {
    await route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({ error: errorMessage }),
    });
  });
}

/**
 * Block external resources (images, fonts, etc.) for faster tests
 */
export async function blockExternalResources(page: Page): Promise<void> {
  await page.route(/\.(png|jpg|jpeg|gif|webp|svg|woff|woff2|ttf)$/, route => route.abort());
}

/**
 * Common API mocks for vocabulary tests
 */
export const VOCABULARY_MOCKS = {
  emptyLibrary: {
    words: [],
    total_count: 0,
    known_count: 0,
    level: 'A1',
  },
  sampleWords: {
    words: [
      { id: '1', word: 'Hallo', lemma: 'hallo', translation: 'Hello', known: false },
      { id: '2', word: 'Welt', lemma: 'welt', translation: 'World', known: true },
    ],
    total_count: 2,
    known_count: 1,
    level: 'A1',
  },
};

/**
 * Common API mocks for video tests
 */
export const VIDEO_MOCKS = {
  emptySeries: [],
  sampleSeries: [
    {
      series: 'TestSeries',
      episode: 1,
      title: 'Episode 1',
      has_subtitles: true,
      path: '/videos/TestSeries/episode1.mp4',
    },
  ],
};
