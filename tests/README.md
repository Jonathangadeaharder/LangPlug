# Unified Test Suite

This directory contains the unified test orchestration system that manages all testing for the LangPlug application.

## Structure

- `/e2e` - End-to-end tests using Puppeteer
- `/utils` - Shared utilities for test orchestration
- `/scripts` - Automation scripts for test execution

## Test Execution

### Running All Tests

To run all tests (backend, frontend unit, and E2E):

```bash
npm run test:all
```

This will:
1. Start backend server
2. Start frontend server
3. Run backend tests
4. Run frontend unit tests
5. Run E2E tests
6. Shutdown all servers
7. Generate test reports

### Running E2E Tests Only

To run only the E2E tests:

```bash
npm run test:e2e
```

### Running Individual Test Files

To run individual test files:

```bash
cd e2e && npx ts-node simple-auth-test.ts
cd e2e && npx ts-node simple-video-test.ts
cd e2e && npx ts-node simple-vocabulary-test.ts
cd e2e && npx ts-node simple-subtitle-test.ts
```

## Test Architecture

The test suite is organized as follows:

1. **Backend Tests** - Python tests using pytest
2. **Frontend Unit Tests** - React component and service tests using Vitest
3. **E2E Tests** - Browser automation tests using Puppeteer

## CI/CD Integration

For CI/CD environments, use the CI-specific test runner:

```bash
npm run test:ci
```

This runner includes proper timeouts and error handling for automated environments.

## Prerequisites

Before running tests, ensure you have:

1. Backend dependencies installed
2. Frontend dependencies installed
3. Database configured and running
4. All required environment variables set

## Test Utilities

The test suite includes several utility functions:

- **Server Management** - Automatic startup and shutdown of backend and frontend servers
- **Database Helpers** - Seeding and cleanup of test data
- **Puppeteer Helpers** - Common browser automation functions
- **Test Runners** - Orchestrated execution of all test types

## Troubleshooting

### Common Issues

1. **ECONNREFUSED Errors** - Ensure backend server is running before running E2E tests
2. **localStorage Access Errors** - These are warnings and can be ignored
3. **Timeout Errors** - Increase timeout values in test configuration

### Debugging

To debug tests, you can:

1. Run individual test files to isolate issues
2. Add console.log statements to track execution
3. Use browser dev tools when running E2E tests in non-headless mode