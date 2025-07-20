# Testing Guide for EpisodeGameApp

This document provides comprehensive information about the testing setup and how to run tests for the EpisodeGameApp project.

## Overview

The project includes both unit and integration tests for:
- **Frontend**: React Native components, services, and context
- **Backend**: Express.js server API endpoints

## Test Structure

### Frontend Tests
Location: `src/` directory with `__tests__` subdirectories

#### Unit Tests
- **GameContext** (`src/context/__tests__/GameContext.test.tsx`)
  - Tests game state management
  - Covers starting/completing games, processing stages, episode status

- **SubtitleService** (`src/services/__tests__/SubtitleService.test.ts`)
  - Tests subtitle processing logic
  - Covers episode processing, vocabulary loading, progress updates

- **PythonBridgeService** (`src/services/__tests__/PythonBridgeService.test.ts`)
  - Tests backend communication
  - Covers health checks, subtitle processing, vocabulary analysis

#### Integration Tests
- **A1DeciderGameScreen** (`src/screens/__tests__/A1DeciderGameScreen.test.tsx`)
  - Tests complete game flow
  - Covers processing, vocabulary check, word selection, navigation

- **VideoPlayerScreen** (`src/screens/__tests__/VideoPlayerScreen.test.tsx`)
  - Tests video playback integration
  - Covers subtitle display, processing status, error handling

### Backend Tests
Location: `backend/__tests__/` directory

#### Integration Tests
- **Server API** (`backend/__tests__/server.test.js`)
  - Tests all API endpoints
  - Covers health checks, dependency validation, subtitle processing
  - Tests error handling and edge cases

## Testing Dependencies

### Frontend
- `@testing-library/react-native` - React Native testing utilities
- `@testing-library/jest-native` - Additional Jest matchers
- `jest-fetch-mock` - Mock fetch API calls
- `react-test-renderer` - React component rendering

### Backend
- `jest` - Testing framework
- `supertest` - HTTP assertion library
- Mocked dependencies: `child_process`, `fs`

## Running Tests

### Individual Test Suites

#### Frontend Tests Only
```bash
# From project root
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch

# Specific test file
npm test -- GameContext.test.tsx
```

#### Backend Tests Only
```bash
# From backend directory
cd backend
npm test

# With coverage
npm test -- --coverage

# Specific test file
npm test -- server.test.js
```

### All Tests
```bash
# From project root - runs both frontend and backend tests
npm run test:all
```

This command will:
1. Run all frontend tests
2. Run all backend tests
3. Provide a summary of results
4. Exit with appropriate code (0 for success, 1 for failure)

## Test Configuration

### Frontend Jest Config (`jest.config.js`)
- **Environment**: React Native
- **Setup**: `jest.setup.js` with mocks for React Native modules
- **Coverage**: Collects from `src/` directory
- **Transform**: Handles TypeScript and React Native modules

### Backend Jest Config (`backend/jest.config.js`)
- **Environment**: Node.js
- **Setup**: `jest.setup.js` with environment configuration
- **Coverage**: Collects from server files
- **Mocks**: File system and child process modules

## Mock Strategy

### Frontend Mocks
- **React Native modules**: Animated, Alert, navigation
- **Fetch API**: Using `jest-fetch-mock`
- **PythonBridgeService**: Mocked in service tests

### Backend Mocks
- **File system**: Mock file existence checks
- **Child process**: Mock Python script execution
- **Express app**: Recreated for each test suite

## Coverage Reports

Generate coverage reports:

```bash
# Frontend coverage
npm test -- --coverage

# Backend coverage
cd backend && npm test -- --coverage
```

Coverage reports are generated in:
- Frontend: `coverage/` directory
- Backend: `backend/coverage/` directory

## Writing New Tests

### Frontend Test Template
```typescript
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import YourComponent from '../YourComponent';

describe('YourComponent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render correctly', () => {
    const { getByText } = render(<YourComponent />);
    expect(getByText('Expected Text')).toBeTruthy();
  });

  it('should handle user interaction', async () => {
    const { getByTestId } = render(<YourComponent />);
    fireEvent.press(getByTestId('button'));
    
    await waitFor(() => {
      expect(/* assertion */).toBeTruthy();
    });
  });
});
```

### Backend Test Template
```javascript
const request = require('supertest');
const app = require('../server');

describe('API Endpoint', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return expected response', async () => {
    const response = await request(app)
      .get('/api/endpoint')
      .expect(200);

    expect(response.body).toHaveProperty('expectedProperty');
  });

  it('should handle errors', async () => {
    const response = await request(app)
      .post('/api/endpoint')
      .send({ invalid: 'data' })
      .expect(400);

    expect(response.body).toHaveProperty('error');
  });
});
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies and APIs
3. **Coverage**: Aim for high test coverage on critical paths
4. **Descriptive**: Use clear, descriptive test names
5. **Setup/Teardown**: Clean up after each test
6. **Edge Cases**: Test error conditions and edge cases
7. **Integration**: Test component interactions and data flow

## Troubleshooting

### Common Issues

1. **Module not found errors**
   - Check Jest configuration for module mapping
   - Ensure all dependencies are installed

2. **React Native component errors**
   - Verify mocks in `jest.setup.js`
   - Check for missing native module mocks

3. **Async test failures**
   - Use `waitFor` for async operations
   - Ensure proper cleanup in `afterEach`

4. **Backend test failures**
   - Check mock implementations
   - Verify Express app setup

### Debug Mode

Run tests with debug output:
```bash
# Frontend
npm test -- --verbose

# Backend
cd backend && npm test -- --verbose
```

## Continuous Integration

For CI/CD pipelines, use:
```bash
# Install dependencies
npm install
cd backend && npm install

# Run all tests
npm run test:all
```

This ensures both frontend and backend tests pass before deployment.