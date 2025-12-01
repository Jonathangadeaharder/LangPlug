/**
 * Test Mode Fixture
 * Injects test-optimized CSS to speed up animations and toasts.
 */
import { test as base } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Read the test mode CSS once at module load
const testModeCssPath = path.join(__dirname, '../../../src/frontend/public/test-mode.css');
let testModeCss: string;
try {
  testModeCss = fs.readFileSync(testModeCssPath, 'utf-8');
} catch {
  // Fallback inline CSS if file not found
  testModeCss = `
    *, *::before, *::after {
      animation-duration: 0.01s !important;
      transition-duration: 0.01s !important;
    }
  `;
}

/**
 * Extended test with test mode optimizations.
 * Injects CSS that speeds up animations for faster tests.
 */
export const testWithOptimizations = base.extend<{
  /** Page with test-mode CSS injected */
  optimizedPage: typeof base;
}>({
  // Inject test-mode CSS into every page
  page: async ({ page }, use) => {
    // Add CSS before any navigation
    await page.addInitScript(() => {
      // This runs in browser context before page load
    });
    
    // Inject CSS after page loads
    page.on('load', async () => {
      try {
        await page.addStyleTag({ content: testModeCss });
      } catch {
        // Page might have navigated away
      }
    });

    await use(page);
  },
});

export { expect } from '@playwright/test';
