import axios, { AxiosInstance } from 'axios';
import { faker } from '@faker-js/faker';

export interface TestUser {
  id?: string;
  username: string;
  email: string;
  password: string;
  token?: string;
}

export interface TestVocabulary {
  id?: string;
  word: string;
  translation: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
}

export interface TestVideo {
  id?: string;
  title: string;
  series: string;
  episode: string;
  path: string;
  duration: number;
}

export class TestDataManager {
  private api: AxiosInstance;
  private readonly baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8001') {
    this.baseUrl = baseUrl;
    this.api = axios.create({
      baseURL: baseUrl,
      timeout: 10000,
    });
  }

  async createTestUser(overrides: Partial<TestUser> = {}): Promise<TestUser> {
    const timestamp = Date.now();
    const user: TestUser = {
      username: `e2euser_${timestamp}`,
      email: `e2e.${timestamp}@langplug.com`,
      password: 'TestPassword123!',
      ...overrides,
    };

    try {
      const response = await this.api.post('/api/auth/register', {
        username: user.username,
        email: user.email,
        password: user.password,
      });

      user.id = response.data.user?.id;
      user.token = response.data.access_token;

      return user;
    } catch (error) {
      console.error('Failed to create test user:', error.response?.data || error.message);
      throw new Error(`Failed to create test user: ${error.message}`);
    }
  }

  async loginUser(email: string, password: string): Promise<TestUser> {
    try {
      const response = await this.api.post('/api/auth/login', {
        email,
        password,
      });

      return {
        username: response.data.user?.username || '',
        email: response.data.user?.email || email,
        password,
        id: response.data.user?.id,
        token: response.data.access_token,
      };
    } catch (error) {
      console.error('Failed to login user:', error.response?.data || error.message);
      throw new Error(`Failed to login user: ${error.message}`);
    }
  }

  async createTestVocabulary(user: TestUser, overrides: Partial<TestVocabulary> = {}): Promise<TestVocabulary> {
    const vocabulary: TestVocabulary = {
      word: faker.word.sample(),
      translation: faker.word.sample(),
      difficulty_level: faker.helpers.arrayElement(['beginner', 'intermediate', 'advanced']),
      ...overrides,
    };

    try {
      const response = await this.api.post('/api/vocabulary', vocabulary, {
        headers: { Authorization: `Bearer ${user.token}` },
      });

      vocabulary.id = response.data.id;
      return vocabulary;
    } catch (error) {
      console.error('Failed to create test vocabulary:', error.response?.data || error.message);
      throw new Error(`Failed to create test vocabulary: ${error.message}`);
    }
  }

  async createTestVideo(user: TestUser, overrides: Partial<TestVideo> = {}): Promise<TestVideo> {
    const video: TestVideo = {
      title: faker.lorem.words(3),
      series: faker.lorem.words(2),
      episode: `Episode ${faker.number.int({ min: 1, max: 10 })}`,
      path: `/videos/test_${Date.now()}.mp4`,
      duration: faker.number.int({ min: 60, max: 3600 }),
      ...overrides,
    };

    try {
      const response = await this.api.post('/api/videos', video, {
        headers: { Authorization: `Bearer ${user.token}` },
      });

      video.id = response.data.id;
      return video;
    } catch (error) {
      console.error('Failed to create test video:', error.response?.data || error.message);
      throw new Error(`Failed to create test video: ${error.message}`);
    }
  }

  async startGameSession(user: TestUser, gameType: string = 'vocabulary', difficulty: string = 'beginner'): Promise<any> {
    try {
      const response = await this.api.post('/api/game/start', {
        game_type: gameType,
        difficulty,
        total_questions: 5,
      }, {
        headers: { Authorization: `Bearer ${user.token}` },
      });

      return response.data;
    } catch (error) {
      console.error('Failed to start game session:', error.response?.data || error.message);
      throw new Error(`Failed to start game session: ${error.message}`);
    }
  }

  async submitGameAnswer(user: TestUser, sessionId: string, answer: any): Promise<any> {
    try {
      const response = await this.api.post(`/api/game/sessions/${sessionId}/answer`, answer, {
        headers: { Authorization: `Bearer ${user.token}` },
      });

      return response.data;
    } catch (error) {
      console.error('Failed to submit game answer:', error.response?.data || error.message);
      throw new Error(`Failed to submit game answer: ${error.message}`);
    }
  }

  async processVideo(user: TestUser, videoId: string): Promise<string> {
    try {
      const response = await this.api.post('/api/processing/transcribe', {
        video_id: videoId,
      }, {
        headers: { Authorization: `Bearer ${user.token}` },
      });

      return response.data.task_id;
    } catch (error) {
      console.error('Failed to process video:', error.response?.data || error.message);
      throw new Error(`Failed to process video: ${error.message}`);
    }
  }

  async getProcessingStatus(user: TestUser, taskId: string): Promise<any> {
    try {
      const response = await this.api.get(`/api/processing/status/${taskId}`, {
        headers: { Authorization: `Bearer ${user.token}` },
      });

      return response.data;
    } catch (error) {
      console.error('Failed to get processing status:', error.response?.data || error.message);
      throw new Error(`Failed to get processing status: ${error.message}`);
    }
  }

  async cleanupTestData(user?: TestUser): Promise<void> {
    try {
      const headers = user?.token ? { Authorization: `Bearer ${user.token}` } : {};
      await this.api.delete('/api/test/cleanup', { headers });
    } catch (error) {
      console.error('Failed to cleanup test data:', error.response?.data || error.message);
      // Don't throw in cleanup
    }
  }

  async waitForProcessingComplete(user: TestUser, taskId: string, timeout: number = 60000): Promise<any> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      try {
        const status = await this.getProcessingStatus(user, taskId);

        if (status.status === 'completed') {
          return status;
        } else if (status.status === 'failed') {
          throw new Error(`Processing failed: ${status.error}`);
        }

        // Wait before checking again
        await new Promise(resolve => setTimeout(resolve, 2000));
      } catch (error) {
        if (error.message.includes('Processing failed')) {
          throw error;
        }
        // Continue waiting for other errors
      }
    }

    throw new Error(`Processing did not complete within ${timeout}ms`);
  }
}
