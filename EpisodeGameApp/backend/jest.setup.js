// Jest setup for backend tests

// Mock console methods to reduce noise during testing
global.console = {
  ...console,
  // Uncomment to ignore specific console methods during tests
  // log: jest.fn(),
  // warn: jest.fn(),
  // error: jest.fn(),
};

// Set up global test timeout
jest.setTimeout(10000);

// Mock environment variables
process.env.NODE_ENV = 'test';
process.env.PORT = '3001';

// Global test setup
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
});

afterEach(() => {
  // Clean up after each test
  jest.restoreAllMocks();
});