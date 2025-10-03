/**
 * Unified Test Fixtures Framework
 *
 * Provides isolated test data, user management, and cleanup mechanisms
 * for all test types with proper isolation
 */

import { testEnvironment, TestEnvironment } from '../config/test-environment';
import path from 'path';
import { randomBytes } from 'crypto';

export interface TestUser {
  id?: string;
  username: string;
  email: string;
  password: string;
  accessToken?: string;
  refreshToken?: string;
}

export interface TestVideo {
  id?: string;
  filename: string;
  originalPath: string;
  tempPath?: string;
  userId?: string;
  processed?: boolean;
}

export interface TestVocabulary {
  id?: string;
  german: string;
  english: string;
  level: string;
  userId?: string;
}

export interface TestSession {
  id: string;
  user: TestUser;
  videos: TestVideo[];
  vocabulary: TestVocabulary[];
  tempFiles: string[];
  cleanup: () => Promise<void>;
}

class TestFixtureManager {
  private static instance: TestFixtureManager;
  private activeSessions: Map<string, TestSession> = new Map();
  private environment: TestEnvironment | null = null;

  private constructor() {}

  static getInstance(): TestFixtureManager {
    if (!TestFixtureManager.instance) {
      TestFixtureManager.instance = new TestFixtureManager();
    }
    return TestFixtureManager.instance;
  }

  /**
   * Create an isolated test session with user, data, and cleanup
   */
  async createTestSession(testName: string): Promise<TestSession> {
    if (!this.environment) {
      this.environment = await testEnvironment.getEnvironment();
    }

    const sessionId = this.generateSessionId(testName);
    const user = await this.createTestUser(sessionId);

    const session: TestSession = {
      id: sessionId,
      user,
      videos: [],
      vocabulary: [],
      tempFiles: [],
      cleanup: async () => {
        await this.cleanupSession(sessionId);
      }
    };

    this.activeSessions.set(sessionId, session);
    console.log(`[FIXTURE] Created test session: ${sessionId}`);

    return session;
  }

  /**
   * Create a test user with unique credentials
   */
  async createTestUser(sessionId: string): Promise<TestUser> {
    const timestamp = Date.now();
    const randomSuffix = randomBytes(4).toString('hex');

    const user: TestUser = {
      username: `test_${sessionId}_${randomSuffix}`,
      email: `test.${sessionId}.${timestamp}@example.com`,
      password: 'TestPassword123!'
    };

    // Register user via API if backend is available
    try {
      await this.registerUserViaAPI(user);
      console.log(`[FIXTURE] Registered test user: ${user.username}`);
    } catch (error) {
      console.log(`[WARN] Could not register user via API: ${error}. User data available for manual registration.`);
    }

    return user;
  }

  /**
   * Add test video to session
   */
  async addTestVideo(sessionId: string, videoData: Partial<TestVideo>): Promise<TestVideo> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`Test session ${sessionId} not found`);
    }

    // Create temp video file if needed
    let tempPath = videoData.tempPath;
    if (!tempPath && videoData.originalPath) {
      tempPath = await this.copyVideoToTemp(videoData.originalPath, sessionId);
    }

    const video: TestVideo = {
      filename: videoData.filename || `test_video_${Date.now()}.mp4`,
      originalPath: videoData.originalPath || '',
      tempPath,
      userId: session.user.id,
      processed: false,
      ...videoData
    };

    session.videos.push(video);
    if (tempPath) {
      session.tempFiles.push(tempPath);
    }

    console.log(`[FIXTURE] Added test video: ${video.filename}`);
    return video;
  }

  /**
   * Add test vocabulary to session
   */
  async addTestVocabulary(sessionId: string, vocabularyData: Partial<TestVocabulary>[]): Promise<TestVocabulary[]> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`Test session ${sessionId} not found`);
    }

    const vocabulary: TestVocabulary[] = vocabularyData.map((data, index) => ({
      german: data.german || `test_german_${index}`,
      english: data.english || `test_english_${index}`,
      level: data.level || 'A1',
      userId: session.user.id,
      ...data
    }));

    session.vocabulary.push(...vocabulary);
    console.log(`[FIXTURE] Added ${vocabulary.length} test vocabulary items`);
    return vocabulary;
  }

  /**
   * Authenticate test user and get tokens
   */
  async authenticateUser(sessionId: string): Promise<TestUser> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      throw new Error(`Test session ${sessionId} not found`);
    }

    try {
      const tokens = await this.loginUserViaAPI(session.user);
      session.user.accessToken = tokens.accessToken;
      session.user.refreshToken = tokens.refreshToken;
      console.log(`[FIXTURE] Authenticated user: ${session.user.username}`);
    } catch (error) {
      console.log(`[WARN] Could not authenticate user via API: ${error}`);
    }

    return session.user;
  }

  /**
   * Get session by ID
   */
  getSession(sessionId: string): TestSession | undefined {
    return this.activeSessions.get(sessionId);
  }

  /**
   * Clean up specific session
   */
  async cleanupSession(sessionId: string): Promise<void> {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return;
    }

    try {
      // Clean temp files
      await this.cleanupTempFiles(session.tempFiles);

      // Clean user data via API
      if (session.user.accessToken) {
        await this.deleteUserViaAPI(session.user);
      }

      // Remove from active sessions
      this.activeSessions.delete(sessionId);
      console.log(`[FIXTURE] Cleaned up session: ${sessionId}`);
    } catch (error) {
      console.log(`[WARN] Session cleanup failed for ${sessionId}: ${error}`);
    }
  }

  /**
   * Clean up all active sessions (for teardown)
   */
  async cleanupAllSessions(): Promise<void> {
    const cleanupPromises = Array.from(this.activeSessions.keys()).map(sessionId =>
      this.cleanupSession(sessionId)
    );

    await Promise.allSettled(cleanupPromises);
    console.log('[FIXTURE] All sessions cleaned up');
  }

  /**
   * Private helper methods
   */
  private generateSessionId(testName: string): string {
    const timestamp = Date.now();
    const randomSuffix = randomBytes(4).toString('hex');
    return `${testName.replace(/[^a-zA-Z0-9]/g, '_')}_${timestamp}_${randomSuffix}`;
  }

  private async registerUserViaAPI(user: TestUser): Promise<void> {
    if (!this.environment) return;

    try {
      const { default: fetch } = await import('node-fetch');
      const response = await fetch(`${this.environment.backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: user.username,
          email: user.email,
          password: user.password
        })
      });

      if (!response.ok) {
        throw new Error(`Registration failed: ${response.status}`);
      }

      const result = await response.json() as any;
      user.id = result.user?.id || result.id;
    } catch (error) {
      throw new Error(`API registration failed: ${error}`);
    }
  }

  private async loginUserViaAPI(user: TestUser): Promise<{ accessToken: string; refreshToken?: string }> {
    if (!this.environment) {
      throw new Error('Environment not initialized');
    }

    try {
      const { default: fetch } = await import('node-fetch');
      const formData = new URLSearchParams({
        username: user.email, // FastAPI-Users expects email in username field
        password: user.password
      });

      const response = await fetch(`${this.environment.backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Login failed: ${response.status}`);
      }

      const result = await response.json() as any;
      return {
        accessToken: result.access_token,
        refreshToken: result.refresh_token
      };
    } catch (error) {
      throw new Error(`API login failed: ${error}`);
    }
  }

  private async deleteUserViaAPI(user: TestUser): Promise<void> {
    if (!this.environment || !user.accessToken) return;

    try {
      const { default: fetch } = await import('node-fetch');
      await fetch(`${this.environment.backendUrl}/api/users/me`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${user.accessToken}`
        }
      });
    } catch (error) {
      console.log(`[WARN] Could not delete user ${user.username}: ${error}`);
    }
  }

  private async copyVideoToTemp(originalPath: string, sessionId: string): Promise<string> {
    if (!this.environment) {
      throw new Error('Environment not initialized');
    }

    const fs = require('fs').promises;
    const tempDir = await testEnvironment.ensureTempDirectory();
    const filename = path.basename(originalPath);
    const tempPath = path.join(tempDir, `${sessionId}_${filename}`);

    try {
      await fs.copyFile(originalPath, tempPath);
      return tempPath;
    } catch (error) {
      console.log(`[WARN] Could not copy video file: ${error}`);
      return originalPath; // Fallback to original
    }
  }

  private async cleanupTempFiles(files: string[]): Promise<void> {
    const fs = require('fs').promises;

    for (const file of files) {
      try {
        await fs.unlink(file);
        console.log(`[FIXTURE] Cleaned temp file: ${file}`);
      } catch (error) {
        console.log(`[WARN] Could not clean temp file ${file}: ${error}`);
      }
    }
  }
}

// Export singleton instance
export const testFixtures = TestFixtureManager.getInstance();

// Export helper functions for common patterns
export async function withTestSession<T>(
  testName: string,
  testFn: (session: TestSession) => Promise<T>
): Promise<T> {
  const session = await testFixtures.createTestSession(testName);
  try {
    return await testFn(session);
  } finally {
    await session.cleanup();
  }
}

export async function withAuthenticatedUser<T>(
  testName: string,
  testFn: (session: TestSession, user: TestUser) => Promise<T>
): Promise<T> {
  return withTestSession(testName, async (session) => {
    const user = await testFixtures.authenticateUser(session.id);
    return testFn(session, user);
  });
}
