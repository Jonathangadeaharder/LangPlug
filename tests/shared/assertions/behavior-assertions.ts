/**
 * Behavior-Focused Assertion Library
 *
 * Provides semantic assertions that verify business outcomes
 * rather than implementation details. Prevents anti-patterns like
 * DOM counting, status code tolerance, and mock call verification.
 */

import { Page } from 'puppeteer';

export interface AssertionResult {
  success: boolean;
  message: string;
  actualValue?: any;
  expectedValue?: any;
}

/**
 * API Response Assertions - Verify exact business outcomes
 */
export class ApiAssertions {
  /**
   * Assert specific HTTP status code (no tolerance for multiple codes)
   */
  static assertStatusCode(actual: number, expected: number): AssertionResult {
    const success = actual === expected;
    return {
      success,
      message: success
        ? `HTTP status ${actual} matches expected ${expected}`
        : `Expected HTTP status ${expected}, but got ${actual}`,
      actualValue: actual,
      expectedValue: expected
    };
  }

  /**
   * Assert authentication success with token presence
   */
  static assertAuthenticationSuccess(response: any): AssertionResult {
    const hasAccessToken = response.access_token && typeof response.access_token === 'string';
    const tokenLength = hasAccessToken ? response.access_token.length : 0;

    const success = hasAccessToken && tokenLength > 20; // JWT tokens are longer than 20 chars

    return {
      success,
      message: success
        ? `Authentication successful with valid token (${tokenLength} chars)`
        : `Authentication failed: ${hasAccessToken ? 'token too short' : 'no access token'}`,
      actualValue: { hasToken: hasAccessToken, tokenLength },
      expectedValue: { hasToken: true, minTokenLength: 20 }
    };
  }

  /**
   * Assert API error response with specific error code/message
   */
  static assertApiError(response: any, expectedErrorCode?: string): AssertionResult {
    const hasError = response.error || response.detail || response.message;
    const errorCode = response.error_code || response.code;

    if (expectedErrorCode) {
      const success = errorCode === expectedErrorCode;
      return {
        success,
        message: success
          ? `API returned expected error code: ${expectedErrorCode}`
          : `Expected error code ${expectedErrorCode}, got ${errorCode || 'none'}`,
        actualValue: errorCode,
        expectedValue: expectedErrorCode
      };
    }

    const success = !!hasError;
    return {
      success,
      message: success
        ? `API returned error as expected: ${hasError}`
        : 'API should have returned an error but did not',
      actualValue: hasError,
      expectedValue: 'error response'
    };
  }

  /**
   * Assert data structure matches expected schema
   */
  static assertDataStructure(data: any, expectedKeys: string[]): AssertionResult {
    const actualKeys = Object.keys(data || {});
    const missingKeys = expectedKeys.filter(key => !actualKeys.includes(key));
    const success = missingKeys.length === 0;

    return {
      success,
      message: success
        ? `Data contains all expected keys: ${expectedKeys.join(', ')}`
        : `Data missing keys: ${missingKeys.join(', ')}`,
      actualValue: actualKeys,
      expectedValue: expectedKeys
    };
  }
}

/**
 * DOM Assertions - Use semantic selectors and verify actual behavior
 */
export class DomAssertions {
  /**
   * Assert element exists using semantic selector (data-testid preferred)
   */
  static async assertElementExists(
    page: Page,
    selector: string,
    timeout: number = 5000
  ): Promise<AssertionResult> {
    try {
      await page.waitForSelector(selector, { visible: true, timeout });
      return {
        success: true,
        message: `Element found with selector: ${selector}`,
        actualValue: 'element exists',
        expectedValue: 'element exists'
      };
    } catch (error) {
      return {
        success: false,
        message: `Element not found with selector: ${selector} (timeout: ${timeout}ms)`,
        actualValue: 'element not found',
        expectedValue: 'element exists'
      };
    }
  }

  /**
   * Assert element contains specific text content
   */
  static async assertElementText(
    page: Page,
    selector: string,
    expectedText: string
  ): Promise<AssertionResult> {
    try {
      const element = await page.waitForSelector(selector, { visible: true });
      if (!element) {
        return {
          success: false,
          message: `Element not found: ${selector}`,
          actualValue: null,
          expectedValue: expectedText
        };
      }

      const actualText = await element.evaluate(el => el.textContent?.trim() || '');
      const success = actualText === expectedText;

      return {
        success,
        message: success
          ? `Element text matches expected: "${expectedText}"`
          : `Expected text "${expectedText}", but got "${actualText}"`,
        actualValue: actualText,
        expectedValue: expectedText
      };
    } catch (error) {
      return {
        success: false,
        message: `Error checking element text: ${error}`,
        actualValue: error,
        expectedValue: expectedText
      };
    }
  }

  /**
   * Assert form submission succeeds (page navigates or shows success)
   */
  static async assertFormSubmissionSuccess(
    page: Page,
    expectedUrl?: string,
    successSelector?: string
  ): Promise<AssertionResult> {
    const initialUrl = page.url();

    try {
      // Wait for either URL change or success indicator
      if (expectedUrl) {
        await page.waitForFunction(
          (targetUrl: string) => window.location.href.includes(targetUrl),
          { timeout: 10000 },
          expectedUrl
        );
        const currentUrl = page.url();
        return {
          success: true,
          message: `Form submission successful - navigated to: ${currentUrl}`,
          actualValue: currentUrl,
          expectedValue: expectedUrl
        };
      }

      if (successSelector) {
        await page.waitForSelector(successSelector, { visible: true, timeout: 10000 });
        return {
          success: true,
          message: `Form submission successful - success indicator appeared: ${successSelector}`,
          actualValue: 'success indicator visible',
          expectedValue: 'success indicator visible'
        };
      }

      // Generic check - URL changed
      await page.waitForFunction(
        (oldUrl: string) => window.location.href !== oldUrl,
        { timeout: 10000 },
        initialUrl
      );

      return {
        success: true,
        message: 'Form submission successful - page navigated',
        actualValue: page.url(),
        expectedValue: 'different from initial URL'
      };
    } catch (error) {
      return {
        success: false,
        message: `Form submission failed or timed out: ${error}`,
        actualValue: page.url(),
        expectedValue: expectedUrl || 'URL change or success indicator'
      };
    }
  }

  /**
   * Assert element is clickable and responds to clicks
   */
  static async assertElementClickable(
    page: Page,
    selector: string
  ): Promise<AssertionResult> {
    try {
      const element = await page.waitForSelector(selector, { visible: true });
      if (!element) {
        return {
          success: false,
          message: `Element not found: ${selector}`,
          actualValue: null,
          expectedValue: 'clickable element'
        };
      }

      // Check if element is actually clickable
      const isEnabled = await element.evaluate(el => {
        if (el instanceof HTMLButtonElement || el instanceof HTMLInputElement) {
          return !el.disabled;
        }
        return true; // Assume other elements are clickable
      });

      const isVisible = await element.evaluate(el => {
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
      });

      const success = isEnabled && isVisible;
      return {
        success,
        message: success
          ? `Element is clickable: ${selector}`
          : `Element not clickable (enabled: ${isEnabled}, visible: ${isVisible}): ${selector}`,
        actualValue: { enabled: isEnabled, visible: isVisible },
        expectedValue: { enabled: true, visible: true }
      };
    } catch (error) {
      return {
        success: false,
        message: `Error checking element clickability: ${error}`,
        actualValue: error,
        expectedValue: 'clickable element'
      };
    }
  }
}

/**
 * Workflow Assertions - Verify complete business flows
 */
export class WorkflowAssertions {
  /**
   * Assert authentication workflow completes successfully
   */
  static async assertAuthenticationWorkflow(
    page: Page,
    credentials: { email: string; password: string },
    expectedRedirectUrl?: string
  ): Promise<AssertionResult> {
    try {
      // Fill login form using semantic selectors
      const emailInput = await page.waitForSelector('[data-testid="email-input"], input[type="email"], input[placeholder*="email" i]');
      const passwordInput = await page.waitForSelector('[data-testid="password-input"], input[type="password"], input[placeholder*="password" i]');
      const submitButton = await page.waitForSelector('[data-testid="login-button"], button[type="submit"], button:has-text("sign in")');

      if (!emailInput || !passwordInput || !submitButton) {
        return {
          success: false,
          message: 'Login form elements not found',
          actualValue: 'missing form elements',
          expectedValue: 'complete login form'
        };
      }

      // Fill and submit form
      await emailInput.type(credentials.email);
      await passwordInput.type(credentials.password);
      await submitButton.click();

      // Wait for authentication result
      const redirectUrl = expectedRedirectUrl || '/dashboard';
      await page.waitForFunction(
        (targetUrl: string) => window.location.href.includes(targetUrl) ||
                             window.localStorage.getItem('auth_token') !== null ||
                             document.querySelector('[data-testid="user-menu"], .user-menu') !== null,
        { timeout: 10000 },
        redirectUrl
      );

      const currentUrl = page.url();
      const hasAuthToken = await page.evaluate(() =>
        localStorage.getItem('auth_token') !== null ||
        localStorage.getItem('access_token') !== null
      );

      const success = currentUrl.includes(redirectUrl) || hasAuthToken;
      return {
        success,
        message: success
          ? `Authentication workflow successful (URL: ${currentUrl}, hasToken: ${hasAuthToken})`
          : `Authentication workflow failed (URL: ${currentUrl}, hasToken: ${hasAuthToken})`,
        actualValue: { url: currentUrl, hasToken: hasAuthToken },
        expectedValue: { url: redirectUrl, hasToken: true }
      };
    } catch (error) {
      return {
        success: false,
        message: `Authentication workflow failed: ${error}`,
        actualValue: error,
        expectedValue: 'successful authentication'
      };
    }
  }

  /**
   * Assert data loading workflow completes
   */
  static async assertDataLoadingWorkflow(
    page: Page,
    loadingSelector: string,
    dataSelector: string,
    timeout: number = 15000
  ): Promise<AssertionResult> {
    try {
      // Wait for loading indicator to appear
      const loadingElement = await page.waitForSelector(loadingSelector, { visible: true, timeout: 5000 });

      // Wait for loading to complete and data to appear
      await page.waitForSelector(loadingSelector, { hidden: true, timeout });
      const dataElement = await page.waitForSelector(dataSelector, { visible: true, timeout: 5000 });

      const hasData = await dataElement.evaluate(el => {
        const text = el.textContent?.trim() || '';
        return text.length > 0 && !text.includes('no data') && !text.includes('empty');
      });

      return {
        success: hasData,
        message: hasData
          ? 'Data loading workflow completed successfully'
          : 'Data loading completed but no meaningful data found',
        actualValue: hasData ? 'data loaded' : 'no data',
        expectedValue: 'data loaded'
      };
    } catch (error) {
      return {
        success: false,
        message: `Data loading workflow failed: ${error}`,
        actualValue: error,
        expectedValue: 'data loaded successfully'
      };
    }
  }
}

/**
 * Anti-Pattern Prevention - Functions that explicitly fail on bad practices
 */
export class AntiPatternPrevention {
  /**
   * Prevent DOM element counting (always fails with helpful message)
   */
  static preventDomCounting(): AssertionResult {
    return {
      success: false,
      message: 'DOM element counting is prohibited. Use semantic assertions that verify business outcomes instead.',
      actualValue: 'element count assertion attempted',
      expectedValue: 'behavior-focused assertion'
    };
  }

  /**
   * Prevent status code tolerance (always fails with helpful message)
   */
  static preventStatusCodeTolerance(): AssertionResult {
    return {
      success: false,
      message: 'Status code tolerance (e.g., status in [200, 500]) is prohibited. Assert exact expected status codes.',
      actualValue: 'multiple status codes accepted',
      expectedValue: 'single expected status code'
    };
  }

  /**
   * Prevent array index selectors (always fails with helpful message)
   */
  static preventArrayIndexSelectors(): AssertionResult {
    return {
      success: false,
      message: 'Array index selectors (e.g., elements[0]) are prohibited. Use semantic selectors like data-testid.',
      actualValue: 'array index selector',
      expectedValue: 'semantic selector'
    };
  }
}

/**
 * Utility function to execute assertion and throw on failure
 */
export function assertResult(result: AssertionResult, context?: string): void {
  if (!result.success) {
    const contextStr = context ? ` [${context}]` : '';
    throw new Error(`${contextStr} ${result.message}`);
  }
}
