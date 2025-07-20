// Jest setup for React Native

// Define __DEV__ global for React Native
global.__DEV__ = true;

// Set global test timeout
jest.setTimeout(10000);

// Mock environment variables
process.env.NODE_ENV = 'test';

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Note: afterEach cleanup should be done in individual test files