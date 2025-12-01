/**
 * Pre-seeded test users from seed_test_data.py
 * These users exist in the database with pre-hashed passwords,
 * avoiding the 30s Argon2 hashing delay during tests.
 * 
 * Run `python src/backend/scripts/seed_test_data.py` before tests
 * to ensure these users exist.
 */

export interface SeededUser {
  email: string;
  username: string;
  password: string;
}

/**
 * Pre-seeded users that exist in the test database.
 * Passwords are already hashed - login is instant.
 */
export const SEEDED_USERS = {
  /** Default E2E test user - always available after seeding */
  default: {
    email: 'e2etest@example.com',
    username: 'e2etest',
    password: 'TestPassword123!',
  },
} as const satisfies Record<string, SeededUser>;

/**
 * Get a seeded user by key.
 * Use these for tests that need a logged-in user without registration delay.
 */
export function getSeededUser(key: keyof typeof SEEDED_USERS = 'default'): SeededUser {
  return SEEDED_USERS[key];
}
