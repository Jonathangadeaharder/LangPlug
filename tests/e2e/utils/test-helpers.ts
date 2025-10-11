import { Page, Locator } from '@playwright/test';

/**
 * Find element using semantic selector strategy with clear error messages.
 * Prefers data-testid, falls back to semantic HTML, fails fast with helpful message.
 */
export async function findElement(
  page: Page,
  testId: string,
  semanticFallback: () => Locator,
  elementDescription: string
): Promise<Locator> {
  const primarySelector = page.locator(`[data-testid="${testId}"]`);

  if (await primarySelector.isVisible({ timeout: 2000 }).catch(() => false)) {
    return primarySelector;
  }

  const fallbackSelector = semanticFallback();
  if (await fallbackSelector.isVisible({ timeout: 2000 }).catch(() => false)) {
    console.warn(`Missing data-testid="${testId}" for ${elementDescription} - using semantic fallback`);
    return fallbackSelector;
  }

  throw new Error(
    `${elementDescription} not found. ` +
    `Add data-testid="${testId}" to the element for reliable testing. ` +
    `Semantic fallback also failed.`
  );
}

/**
 * Wait for any of multiple conditions to be met (useful for detecting state changes).
 */
export async function waitForAnyCondition(
  page: Page,
  conditions: Array<{ testId: string; state?: 'visible' | 'hidden' }>,
  timeout: number = 5000
): Promise<void> {
  const promises = conditions.map(({ testId, state = 'visible' }) =>
    page.locator(`[data-testid="${testId}"]`).waitFor({ state, timeout })
  );

  await Promise.race(promises).catch(() => {
    throw new Error(
      `None of the expected conditions were met: ${conditions.map(c => c.testId).join(', ')}`
    );
  });
}
