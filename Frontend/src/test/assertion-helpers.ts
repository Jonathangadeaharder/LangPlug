/**
 * Assertion helpers to keep frontend test bodies concise and follow CLAUDE.md rules
 */
import { expect } from 'vitest';

export const assertElementExists = (element: HTMLElement | null): void => {
  expect(element).toBeTruthy();
};

export const assertElementNotExists = (element: HTMLElement | null): void => {
  expect(element).toBeFalsy();
};

export const assertTextInDocument = (text: string | RegExp): void => {
  expect(document.body).toHaveTextContent(text);
};

export const assertApiCallMade = (mockFn: any, expectedArgs?: any): void => {
  expect(mockFn).toHaveBeenCalled();
  if (expectedArgs) {
    expect(mockFn).toHaveBeenCalledWith(expectedArgs);
  }
};

export const assertNavigationCalled = (mockNavigate: any, expectedPath: string): void => {
  expect(mockNavigate).toHaveBeenCalledWith(expectedPath);
};

export const assertElementVisible = (element: HTMLElement): void => {
  expect(element).toBeVisible();
  expect(element).toBeInTheDocument();
};

export const assertLoadingState = (): void => {
  const spinner = document.querySelector('.loading-spinner');
  expect(spinner).toBeTruthy();
};

export const assertErrorMessage = (message: string): void => {
  // Check if the specific error message exists in the document
  const hasMessage = document.body.textContent?.includes(message) ||
                    document.querySelector(`[data-testid*="error"]`)?.textContent?.includes(message) ||
                    document.querySelector('.error')?.textContent?.includes(message);
  expect(hasMessage).toBeTruthy();
};

export const assertArrayLength = (array: any[], expectedLength: number): void => {
  expect(array).toHaveLength(expectedLength);
};

export const assertMockResolvedValue = (mockFn: any, value: any): void => {
  mockFn.mockResolvedValue(value);
};

export const assertMockRejectedValue = (mockFn: any, error: any): void => {
  mockFn.mockRejectedValue(error);
};
