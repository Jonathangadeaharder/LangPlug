/**
 * Centralized selectors for authentication-related elements.
 * Use data-testid attributes for stability.
 */
export const AUTH_SELECTORS = {
  // Registration form
  REGISTER: {
    EMAIL_INPUT: '[data-testid="email-input"]',
    USERNAME_INPUT: '[data-testid="username-input"]',
    PASSWORD_INPUT: '[data-testid="password-input"]',
    CONFIRM_PASSWORD_INPUT: '[data-testid="confirm-password-input"]',
    SUBMIT_BUTTON: '[data-testid="register-submit"]',
    SIGN_UP_LINK: 'text=Sign up now',
  },

  // Login form
  LOGIN: {
    EMAIL_INPUT: '[data-testid="email-input"]',
    PASSWORD_INPUT: '[data-testid="password-input"]',
    SUBMIT_BUTTON: '[data-testid="submit-button"]',
    SIGN_IN_BUTTON: 'button:has-text("Sign In")',
  },

  // Navigation/Header
  NAV: {
    LOGOUT_BUTTON: '[data-testid="logout-button"], button:has-text("Logout")',
    PROFILE_BUTTON: '[data-testid="profile-button"]',
    VOCAB_BUTTON: 'button:has-text("Vocabulary Library")',
    BACK_TO_VIDEOS: 'button:has-text("Back to Videos")',
    LOGO: 'text=LangPlug',
  },

  // Messages/Feedback
  MESSAGES: {
    ERROR: '[data-testid="error-message"], .text-red-500, [role="alert"]',
    SUCCESS_TOAST: 'div[role="status"]',
    SPECIAL_CHAR_ERROR: 'text=/special character/i',
  },

  // Vocabulary Library
  VOCABULARY: {
    BACK_BUTTON: '[data-testid="back-to-videos"]',
    SEARCH_INPUT: '[data-testid="vocabulary-search"]',
    LOADING: '[data-testid="vocabulary-loading"]',
    WORD_CARD: '[data-testid^="word-card-"]',
    LEVEL_TAB: '[data-testid^="level-tab-"]',
  },
} as const;
