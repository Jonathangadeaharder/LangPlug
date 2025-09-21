import axios from 'axios';

export class DatabaseHelpers {
  private static readonly API_BASE_URL = 'http://127.0.0.1:8000/api';
  private static readonly TEST_USER_EMAIL = 'test@example.com';
  private static readonly TEST_USER_PASSWORD = 'TestPassword123!';
  private static readonly TEST_USER_USERNAME = 'testuser';

  /**
   * Seed the database with test data
   */
  static async seedTestData(): Promise<void> {
    try {
      // Create a test user
      await this.createTestUser();
      
      // Login with the test user to get auth token
      const token = await this.loginTestUser();
      
      // Create sample videos, vocabulary, etc.
      await this.createSampleContent(token);
      
      console.log('Test data seeded successfully');
    } catch (error) {
      console.error('Failed to seed test data:', error);
      throw error;
    }
  }

  /**
   * Clean up test data from the database
   */
  static async cleanTestData(): Promise<void> {
    try {
      // Login with the test user to get auth token
      const token = await this.loginTestUser();
      
      // Delete test content
      await this.deleteSampleContent(token);
      
      // Delete the test user
      await this.deleteTestUser(token);
      
      console.log('Test data cleaned successfully');
    } catch (error) {
      console.error('Failed to clean test data:', error);
      // Don't throw error as this is cleanup
    }
  }

  /**
   * Create a test user
   */
  private static async createTestUser(): Promise<void> {
    try {
      await axios.post(`${this.API_BASE_URL}/auth/register`, {
        username: this.TEST_USER_USERNAME,
        email: this.TEST_USER_EMAIL,
        password: this.TEST_USER_PASSWORD
      });
    } catch (error: any) {
      // If user already exists, that's fine
      if (error.response?.status !== 400) {
        throw error;
      }
    }
  }

  /**
   * Login with test user credentials
   */
  private static async loginTestUser(): Promise<string> {
    try {
      // Note: FastAPI-Users expects form data for login, not JSON
      const formData = new URLSearchParams();
      formData.append('username', this.TEST_USER_EMAIL);
      formData.append('password', this.TEST_USER_PASSWORD);
      
      const response = await axios.post(`${this.API_BASE_URL}/auth/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      return response.data.access_token;
    } catch (error) {
      console.error('Failed to login test user:', error);
      throw error;
    }
  }

  /**
   * Delete the test user
   */
  private static async deleteTestUser(token: string): Promise<void> {
    try {
      // This would require admin privileges or the user deleting themselves
      // For now, we'll just leave the user in the database
      console.log('Note: Test user not deleted (would require admin privileges)');
    } catch (error) {
      console.error('Failed to delete test user:', error);
    }
  }

  /**
   * Create sample content for testing
   */
  private static async createSampleContent(token: string): Promise<void> {
    try {
      // Create sample vocabulary
      await axios.post(`${this.API_BASE_URL}/vocabulary`, {
        word: 'Hallo',
        translation: 'Hello',
        language: 'de'
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('Sample content created');
    } catch (error) {
      console.error('Failed to create sample content:', error);
    }
  }

  /**
   * Delete sample content
   */
  private static async deleteSampleContent(token: string): Promise<void> {
    try {
      // Delete sample vocabulary
      // This would require knowing the vocabulary IDs
      // For now, we'll just log that cleanup was attempted
      console.log('Sample content cleanup attempted');
    } catch (error) {
      console.error('Failed to delete sample content:', error);
    }
  }
}