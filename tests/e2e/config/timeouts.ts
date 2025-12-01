/**
 * Centralized timeout configuration for E2E tests.
 * Avoids magic numbers scattered throughout tests.
 */
export const TIMEOUTS = {
  /** Registration/login - password hashing (Argon2) is slow */
  REGISTRATION: 30_000,
  
  /** Page navigation waits */
  NAVIGATION: 10_000,
  
  /** Element visibility checks */
  ELEMENT_VISIBLE: 10_000,
  
  /** Toast messages (they auto-dismiss) */
  TOAST: 5_000,
  
  /** Short waits for UI updates */
  SHORT_WAIT: 1_000,
  
  /** Form submission feedback */
  FORM_RESPONSE: 15_000,
} as const;
