import { Page, Locator } from '@playwright/test';

/**
 * Instrumentation Helper for E2E Tests
 *
 * Addresses "No Silent Fallbacks" violation from ~/.claude/CLAUDE.md
 * Provides explicit validation and error reporting instead of silent fallbacks
 */

export interface SelectorOptions {
  primary: string;
  fallbacks?: string[];
  description: string;
}

/**
 * Gets a locator with explicit fallback validation
 * Reports missing instrumentation instead of silently falling back
 */
export async function getInstrumentedLocator(
  page: Page,
  options: SelectorOptions
): Promise<Locator> {
  const primaryLocator = page.locator(options.primary);

  if (await primaryLocator.isVisible()) {
    return primaryLocator;
  }

  // Log missing primary instrumentation
  console.warn(`Missing primary instrumentation for ${options.description}: ${options.primary}`);

  if (options.fallbacks) {
    for (const fallback of options.fallbacks) {
      const fallbackLocator = page.locator(fallback);
      if (await fallbackLocator.isVisible()) {
        console.warn(`Using fallback selector for ${options.description}: ${fallback}`);
        return fallbackLocator;
      }
    }
  }

  throw new Error(`Element not found for ${options.description}. Primary: ${options.primary}, Fallbacks: ${options.fallbacks?.join(', ') || 'none'}`);
}

/**
 * Validates that critical elements have proper data-testid instrumentation
 */
export async function validateInstrumentation(
  page: Page,
  testId: string,
  description: string
): Promise<Locator> {
  const element = page.locator(`[data-testid="${testId}"]`);

  if (!(await element.isVisible())) {
    throw new Error(`Critical element missing instrumentation: data-testid="${testId}" for ${description}`);
  }

  return element;
}

/**
 * Logs missing instrumentation for monitoring and improvement
 */
export function logMissingInstrumentation(elementType: string, context: string): void {
  console.warn(`[INSTRUMENTATION] Missing data-testid for ${elementType} in ${context}`);
}
