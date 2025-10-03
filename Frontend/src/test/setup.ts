import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';
import React from 'react';
import { ThemeProvider } from 'styled-components';
import { act } from 'react';

// extends Vitest's expect method with methods from react-testing-library
expect.extend(matchers);

// runs a cleanup after each test case (e.g. clearing jsdom)
afterEach(() => {
  cleanup();
});

// Mock theme for styled-components
const mockTheme = {
  colors: {
    primary: '#FF6B6B',
    primaryDark: '#EE5A52',
    primaryLight: '#FF8787',
    secondary: '#4ECDC4',
    background: '#FFFFFF',
    surface: '#F8F9FA',
    surfaceHover: '#E9ECEF',
    text: '#1A1A1A',
    textSecondary: '#6C757D',
    textLight: '#ADB5BD',
    border: '#E1E4E8',
    success: '#52C41A',
    warning: '#FAAD14',
    error: '#F5222D',
    info: '#1890FF',
    overlay: 'rgba(0, 0, 0, 0.5)',
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
  },
  breakpoints: {
    xs: '0px',
    sm: '576px',
    md: '768px',
    lg: '992px',
    xl: '1200px',
    '2xl': '1400px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  },
  transitions: {
    fast: '150ms ease-in-out',
    normal: '250ms ease-in-out',
    slow: '350ms ease-in-out',
  },
  typography: {
    fontFamily: {
      primary: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      mono: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      md: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
    },
    fontWeight: {
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
    },
  },
  radius: {
    sm: '0.125rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '1rem',
    full: '9999px',
  },
  zIndex: {
    modal: 1000,
    popover: 900,
    tooltip: 800,
  },
};

// Make theme available globally for tests
(global as any).mockTheme = mockTheme;

// Helper to wrap components with theme provider
(global as any).withTheme = (component: React.ReactElement) =>
  React.createElement(ThemeProvider, { theme: mockTheme }, component);

// Make React.act available globally to replace ReactDOMTestUtils.act
(global as any).act = act;

// Enhanced act wrapper for async operations
(global as any).actAsync = async (fn: () => Promise<any>) => {
  await act(async () => {
    await fn();
  });
};

// Suppress specific warnings that come from testing libraries
const originalConsoleWarn = console.warn;
const originalConsoleError = console.error;

console.warn = (...args) => {
  const message = args[0];
  if (
    typeof message === 'string' &&
    (
      message.includes('ReactDOMTestUtils.act') ||
      message.includes('React Router Future Flag Warning') ||
      (message.includes('An update to') && message.includes('was not wrapped in act')) ||
      message.includes('Warning: `ReactDOMTestUtils.act` is deprecated')
    )
  ) {
    return; // Suppress these warnings
  }
  originalConsoleWarn.apply(console, args);
};

console.error = (...args) => {
  const message = args[0];
  if (
    typeof message === 'string' &&
    (
      message.includes('ReactDOMTestUtils.act') ||
      (message.includes('An update to') && message.includes('was not wrapped in act'))
    )
  ) {
    return; // Suppress these errors
  }
  originalConsoleError.apply(console, args);
};

// Mock IntersectionObserver
class MockIntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  readonly root = null;
  readonly rootMargin = '';
  readonly thresholds = [];
  takeRecords() { return [] };
}
global.IntersectionObserver = MockIntersectionObserver as any;

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'mocked-url');
global.URL.revokeObjectURL = vi.fn();

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
  configurable: true
});

// Fix URLSearchParams for jsdom
if (!global.URLSearchParams) {
  global.URLSearchParams = URLSearchParams;
}

// Ensure DOM is properly set up for testing
if (typeof global.document === 'undefined' || !global.document.body) {
  // Create a basic document if it doesn't exist
  const dom = new (require('jsdom')).JSDOM('<!doctype html><html><body></body></html>');
  global.document = dom.window.document;
  global.window = dom.window;

  // Ensure body exists
  if (!global.document.body) {
    global.document.documentElement.appendChild(global.document.createElement('body'));
  }
}

// Ensure DOM globals are available for tests
Object.defineProperty(global.window, 'Node', {
  value: global.window.Node,
  writable: true,
  configurable: true
});

Object.defineProperty(global.window, 'Element', {
  value: global.window.Element,
  writable: true,
  configurable: true
});

// Framer-motion is mocked via resolve.alias in vitest.config.ts

// Mock axios to prevent network requests in tests
vi.mock('axios', async () => {
  const actual = await vi.importActual('axios')
  return {
    ...actual,
    default: {
      create: vi.fn(() => ({
        get: vi.fn(() => Promise.resolve({ data: {} })),
        post: vi.fn(() => Promise.resolve({ data: {} })),
        put: vi.fn(() => Promise.resolve({ data: {} })),
        delete: vi.fn(() => Promise.resolve({ data: {} })),
        interceptors: {
          request: { use: vi.fn(), eject: vi.fn() },
          response: { use: vi.fn(), eject: vi.fn() },
        },
      })),
      get: vi.fn(() => Promise.resolve({ data: {} })),
      post: vi.fn(() => Promise.resolve({ data: {} })),
      put: vi.fn(() => Promise.resolve({ data: {} })),
      delete: vi.fn(() => Promise.resolve({ data: {} })),
    },
  }
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
  configurable: true
});
