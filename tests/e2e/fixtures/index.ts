/**
 * Central export for all E2E test fixtures and utilities.
 * 
 * Best Practices Implemented:
 * 1. Auth Setup Project - authenticate once, reuse state
 * 2. Role-Based Locators - use getByRole, getByLabel
 * 3. API Mocking - mock external dependencies
 * 4. Web-First Assertions - no hard waits
 * 5. Parallel Execution - sharding support
 */

// Fixtures
export { test, expect, UserFactory, TestUser } from './auth.fixture';
export { testWithOptimizations } from './test-mode.fixture';
export { SEEDED_USERS, getSeededUser, type SeededUser } from './seeded-users';

// API Mocking (Best Practice #3)
export { 
  mockApiResponse, 
  mockSlowApi, 
  mockApiError, 
  blockExternalResources,
  VOCABULARY_MOCKS,
  VIDEO_MOCKS,
} from './api-mocks';

// Config
export { TIMEOUTS } from '../config/timeouts';
export { BASE_URL, ROUTES, getFullUrl } from '../config/urls';

// Selectors
export { AUTH_SELECTORS } from '../selectors/auth.selectors';

// Role-Based Locators (Best Practice #2)
export { 
  getFormLocators, 
  getNavLocators, 
  getContentLocators, 
  RoleBasedPage,
} from '../selectors/role-locators';

// Page Objects
export { LoginPage } from '../pages/LoginPage';
export { RegisterPage } from '../pages/RegisterPage';
