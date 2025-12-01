/**
 * Factory for creating unique test user credentials.
 * Eliminates duplicate user generation logic across tests.
 */
export interface TestUser {
  email: string;
  username: string;
  password: string;
}

export class UserFactory {
  private static counter = 0;

  /**
   * Creates a unique test user with timestamp-based credentials.
   * @param prefix - Optional prefix for the username (default: 'test')
   * @param password - Optional custom password (default: secure password)
   */
  static create(prefix = 'test', password = 'SecurePassword123!'): TestUser {
    const timestamp = Date.now();
    const id = `${timestamp}${++this.counter}`;
    
    return {
      email: `${prefix}${id}@example.com`,
      username: `${prefix}${id}`.slice(0, 20), // Keep username reasonable length
      password,
    };
  }

  /**
   * Creates a user with an invalid password (too short, no special char).
   */
  static createWithWeakPassword(prefix = 'weak'): TestUser {
    return this.create(prefix, 'weak123');
  }

  /**
   * Creates a user with password missing special character.
   */
  static createWithNoSpecialChar(prefix = 'nospec'): TestUser {
    return this.create(prefix, 'NoSpecialChar123456');
  }
}
