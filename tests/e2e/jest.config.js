module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts'],
  testTimeout: 60000, // 60 seconds for E2E tests
  setupFilesAfterEnv: [],
  maxWorkers: 1, // Run tests serially to avoid resource conflicts
  transform: {
    '^.+\\.ts$': ['ts-jest', {
      useESM: false,
    }],
  },
  forceExit: true, // Force exit to prevent hanging
  detectOpenHandles: true, // Help detect what keeps Jest running
};
