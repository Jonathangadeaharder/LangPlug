/**
 * Centralized E2E test configuration
 * Update these values in ONE place instead of across all test files
 */

export const TEST_CONFIG = {
  // API Configuration
  API_BASE_URL: process.env.API_BASE_URL || 'http://127.0.0.1:8000',
  FRONTEND_URL: process.env.FRONTEND_URL || 'http://localhost:3000',

  // Timeouts (ms)
  DEFAULT_TIMEOUT: 10000,
  NAVIGATION_TIMEOUT: 5000,
  API_TIMEOUT: 5000,

  // API Endpoints - Single source of truth
  ENDPOINTS: {
    // Auth
    LOGIN: '/api/auth/jwt/login',
    REGISTER: '/api/auth/register',
    LOGOUT: '/api/auth/jwt/logout',

    // User
    PROFILE: '/api/profile',
    HEALTH: '/health',
    READINESS: '/readiness',

    // Vocabulary
    VOCABULARY_LIBRARY: '/api/vocabulary/library',
    VOCABULARY_CREATE: '/api/vocabulary/create',
    VOCABULARY_SEARCH: '/api/vocabulary/search',
    VOCABULARY_WORD_INFO: '/api/vocabulary/word-info',

    // Videos
    VIDEOS: '/api/videos',
    VIDEOS_SCAN: '/api/videos/scan',
  },

  // UI Selectors - Match frontend data-testid attributes
  SELECTORS: {
    // Auth forms
    EMAIL_INPUT: 'input[type="email"]',
    PASSWORD_INPUT: 'input[type="password"]',
    SUBMIT_BUTTON: 'button[type="submit"]',

    // Navigation
    USER_MENU: '[data-testid="user-menu"]',
    VOCABULARY_NAV: '[data-testid="vocabulary-nav"]',
    PROFILE_BUTTON: '[data-testid="profile-button"]',
    LOGOUT_BUTTON: '[data-testid="logout-button"]',
    REGISTER_LINK: '[data-testid="register-link"]',

    // Pages
    ROOT: '#root',
  },
} as const;

// Helper to build full API URL
export function apiUrl(endpoint: string): string {
  return `${TEST_CONFIG.API_BASE_URL}${endpoint}`;
}

// Helper for common query params
export function vocabularyLibraryUrl(level = 'A1', limit = 50): string {
  return apiUrl(`${TEST_CONFIG.ENDPOINTS.VOCABULARY_LIBRARY}?level=${level}&limit=${limit}`);
}
