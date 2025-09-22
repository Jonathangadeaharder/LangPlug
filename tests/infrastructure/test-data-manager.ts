/**
 * Test Data Manager - Centralized test data management
 * Provides consistent fixtures, mocks, and test data generation
 */

import { faker } from '@faker-js/faker';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs-extra';
import * as path from 'path';

export interface TestUser {
  id: string;
  username: string;
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
  role?: 'user' | 'admin' | 'moderator';
  createdAt?: Date;
  token?: string;
}

export interface TestVideo {
  id: string;
  title: string;
  description?: string;
  url?: string;
  duration?: number;
  language?: string;
  difficulty?: 'beginner' | 'intermediate' | 'advanced';
  tags?: string[];
  subtitles?: TestSubtitle[];
  createdBy?: string;
  createdAt?: Date;
}

export interface TestSubtitle {
  id: string;
  videoId: string;
  language: string;
  startTime: number;
  endTime: number;
  text: string;
  translation?: string;
}

export interface TestVocabulary {
  id: string;
  word: string;
  translation: string;
  language: string;
  difficulty: number;
  frequency: number;
  examples?: string[];
  tags?: string[];
  userId?: string;
}

export interface TestProgress {
  id: string;
  userId: string;
  videoId?: string;
  vocabularyId?: string;
  progress: number;
  score?: number;
  startedAt: Date;
  completedAt?: Date;
}

export class TestDataManager {
  private users: Map<string, TestUser> = new Map();
  private videos: Map<string, TestVideo> = new Map();
  private vocabulary: Map<string, TestVocabulary> = new Map();
  private progress: Map<string, TestProgress> = new Map();
  private fixtures: Map<string, any> = new Map();
  
  constructor() {
    this.loadDefaultFixtures();
  }

  /**
   * Load default fixtures
   */
  private loadDefaultFixtures(): void {
    // Default admin user
    this.fixtures.set('admin', {
      id: 'admin-user-id',
      username: 'admin',
      email: 'admin@langplug.com',
      password: 'Admin123!',
      role: 'admin',
    });

    // Default test user
    this.fixtures.set('testUser', {
      id: 'test-user-id',
      username: 'testuser',
      email: 'test@example.com',
      password: 'TestPassword123!',
      role: 'user',
    });

    // Sample video
    this.fixtures.set('sampleVideo', {
      id: 'sample-video-id',
      title: 'German Learning Video',
      description: 'Learn basic German phrases',
      duration: 300,
      language: 'de',
      difficulty: 'beginner',
      tags: ['german', 'basics', 'phrases'],
    });

    // Sample vocabulary
    this.fixtures.set('sampleVocabulary', [
      { word: 'Hallo', translation: 'Hello', difficulty: 1 },
      { word: 'Danke', translation: 'Thank you', difficulty: 1 },
      { word: 'Auf Wiedersehen', translation: 'Goodbye', difficulty: 2 },
      { word: 'Entschuldigung', translation: 'Excuse me', difficulty: 3 },
    ]);
  }

  /**
   * Generate a unique test user
   */
  generateUser(overrides: Partial<TestUser> = {}): TestUser {
    const user: TestUser = {
      id: overrides.id || uuidv4(),
      username: overrides.username || faker.internet.userName().toLowerCase(),
      email: overrides.email || faker.internet.email().toLowerCase(),
      password: overrides.password || this.generatePassword(),
      firstName: overrides.firstName || faker.person.firstName(),
      lastName: overrides.lastName || faker.person.lastName(),
      role: overrides.role || 'user',
      createdAt: overrides.createdAt || new Date(),
      ...overrides,
    };
    
    this.users.set(user.id, user);
    return user;
  }

  /**
   * Generate multiple users
   */
  generateUsers(count: number, overrides: Partial<TestUser> = {}): TestUser[] {
    return Array.from({ length: count }, () => this.generateUser(overrides));
  }

  /**
   * Generate a secure password
   */
  generatePassword(): string {
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const numbers = '0123456789';
    const special = '!@#$%^&*()_+-=[]{}|;:,.<>?';
    
    let password = '';
    password += faker.helpers.arrayElement(uppercase.split(''));
    password += faker.helpers.arrayElement(lowercase.split(''));
    password += faker.helpers.arrayElement(numbers.split(''));
    password += faker.helpers.arrayElement(special.split(''));
    
    const remaining = 8 + Math.floor(Math.random() * 8);
    const all = lowercase + uppercase + numbers + special;
    
    for (let i = 0; i < remaining; i++) {
      password += faker.helpers.arrayElement(all.split(''));
    }
    
    return password.split('').sort(() => Math.random() - 0.5).join('');
  }

  /**
   * Generate a test video
   */
  generateVideo(overrides: Partial<TestVideo> = {}): TestVideo {
    const germanWords = ['Lernen', 'Sprechen', 'Verstehen', 'Üben', 'Hören'];
    const video: TestVideo = {
      id: overrides.id || uuidv4(),
      title: overrides.title || `${faker.helpers.arrayElement(germanWords)} - ${faker.lorem.words(3)}`,
      description: overrides.description || faker.lorem.paragraph(),
      url: overrides.url || faker.internet.url(),
      duration: overrides.duration || faker.number.int({ min: 60, max: 3600 }),
      language: overrides.language || 'de',
      difficulty: overrides.difficulty || faker.helpers.arrayElement(['beginner', 'intermediate', 'advanced']),
      tags: overrides.tags || faker.lorem.words(3).split(' '),
      createdAt: overrides.createdAt || new Date(),
      ...overrides,
    };
    
    this.videos.set(video.id, video);
    return video;
  }

  /**
   * Generate subtitles for a video
   */
  generateSubtitles(videoId: string, count: number = 10): TestSubtitle[] {
    const subtitles: TestSubtitle[] = [];
    let currentTime = 0;
    
    for (let i = 0; i < count; i++) {
      const duration = faker.number.int({ min: 2, max: 8 });
      const subtitle: TestSubtitle = {
        id: uuidv4(),
        videoId,
        language: 'de',
        startTime: currentTime,
        endTime: currentTime + duration,
        text: faker.lorem.sentence(),
        translation: faker.lorem.sentence(),
      };
      
      subtitles.push(subtitle);
      currentTime += duration;
    }
    
    return subtitles;
  }

  /**
   * Generate vocabulary items
   */
  generateVocabulary(count: number, overrides: Partial<TestVocabulary> = {}): TestVocabulary[] {
    const germanWords = [
      'Apfel', 'Baum', 'Computer', 'Deutschland', 'Essen', 'Familie', 'Garten',
      'Haus', 'Internet', 'Jahr', 'Kind', 'Lehrer', 'Musik', 'Nacht', 'Opa',
      'Pizza', 'Qualität', 'Regen', 'Sonne', 'Tag', 'Universität', 'Vater',
      'Wasser', 'Xylophon', 'Yoga', 'Zeit',
    ];
    
    return Array.from({ length: count }, () => {
      const word = faker.helpers.arrayElement(germanWords) + faker.number.int({ min: 1, max: 999 });
      const vocab: TestVocabulary = {
        id: uuidv4(),
        word,
        translation: faker.lorem.word(),
        language: 'de',
        difficulty: faker.number.int({ min: 1, max: 10 }),
        frequency: faker.number.int({ min: 1, max: 1000 }),
        examples: [faker.lorem.sentence(), faker.lorem.sentence()],
        tags: faker.lorem.words(2).split(' '),
        ...overrides,
      };
      
      this.vocabulary.set(vocab.id, vocab);
      return vocab;
    });
  }

  /**
   * Generate progress data
   */
  generateProgress(userId: string, itemId: string, type: 'video' | 'vocabulary'): TestProgress {
    const progress: TestProgress = {
      id: uuidv4(),
      userId,
      videoId: type === 'video' ? itemId : undefined,
      vocabularyId: type === 'vocabulary' ? itemId : undefined,
      progress: faker.number.int({ min: 0, max: 100 }),
      score: faker.number.int({ min: 0, max: 100 }),
      startedAt: faker.date.past(),
      completedAt: faker.datatype.boolean() ? faker.date.recent() : undefined,
    };
    
    this.progress.set(progress.id, progress);
    return progress;
  }

  /**
   * Create a complete test scenario
   */
  async createScenario(name: string): Promise<{
    users: TestUser[];
    videos: TestVideo[];
    vocabulary: TestVocabulary[];
    progress: TestProgress[];
  }> {
    const scenario = {
      users: [] as TestUser[],
      videos: [] as TestVideo[],
      vocabulary: [] as TestVocabulary[],
      progress: [] as TestProgress[],
    };

    switch (name) {
      case 'basic':
        // Create basic scenario with minimal data
        scenario.users = [
          this.generateUser({ username: 'student1' }),
          this.generateUser({ username: 'teacher1', role: 'moderator' }),
        ];
        scenario.videos = [this.generateVideo({ difficulty: 'beginner' })];
        scenario.vocabulary = this.generateVocabulary(10);
        scenario.progress = [
          this.generateProgress(scenario.users[0].id, scenario.videos[0].id, 'video'),
        ];
        break;

      case 'comprehensive':
        // Create comprehensive scenario with full data
        scenario.users = this.generateUsers(5);
        scenario.videos = Array.from({ length: 10 }, () => this.generateVideo());
        scenario.vocabulary = this.generateVocabulary(50);
        
        // Add subtitles to videos
        scenario.videos.forEach(video => {
          video.subtitles = this.generateSubtitles(video.id);
        });
        
        // Generate progress for each user
        scenario.users.forEach(user => {
          scenario.videos.forEach(video => {
            if (Math.random() > 0.5) {
              scenario.progress.push(this.generateProgress(user.id, video.id, 'video'));
            }
          });
          
          scenario.vocabulary.slice(0, 10).forEach(vocab => {
            scenario.progress.push(this.generateProgress(user.id, vocab.id, 'vocabulary'));
          });
        });
        break;

      case 'performance':
        // Create large dataset for performance testing
        scenario.users = this.generateUsers(100);
        scenario.videos = Array.from({ length: 100 }, () => this.generateVideo());
        scenario.vocabulary = this.generateVocabulary(1000);
        break;

      default:
        throw new Error(`Unknown scenario: ${name}`);
    }

    return scenario;
  }

  /**
   * Get fixture by name
   */
  getFixture(name: string): any {
    return this.fixtures.get(name);
  }

  /**
   * Load fixtures from file
   */
  async loadFixturesFromFile(filePath: string): Promise<void> {
    const fixtures = await fs.readJson(filePath);
    for (const [key, value] of Object.entries(fixtures)) {
      this.fixtures.set(key, value);
    }
  }

  /**
   * Save current data as fixtures
   */
  async saveFixtures(filePath: string): Promise<void> {
    const data = {
      users: Array.from(this.users.values()),
      videos: Array.from(this.videos.values()),
      vocabulary: Array.from(this.vocabulary.values()),
      progress: Array.from(this.progress.values()),
    };
    
    await fs.writeJson(filePath, data, { spaces: 2 });
  }

  /**
   * Clear all test data
   */
  clearAll(): void {
    this.users.clear();
    this.videos.clear();
    this.vocabulary.clear();
    this.progress.clear();
  }

  /**
   * Get user by ID
   */
  getUser(id: string): TestUser | undefined {
    return this.users.get(id);
  }

  /**
   * Get video by ID
   */
  getVideo(id: string): TestVideo | undefined {
    return this.videos.get(id);
  }

  /**
   * Get all users
   */
  getAllUsers(): TestUser[] {
    return Array.from(this.users.values());
  }

  /**
   * Get all videos
   */
  getAllVideos(): TestVideo[] {
    return Array.from(this.videos.values());
  }

  /**
   * Create mock API responses
   */
  createMockResponse<T>(data: T, statusCode = 200, headers: Record<string, string> = {}): {
    data: T;
    status: number;
    headers: Record<string, string>;
    config: any;
  } {
    return {
      data,
      status: statusCode,
      headers: {
        'content-type': 'application/json',
        ...headers,
      },
      config: {},
    };
  }

  /**
   * Create paginated response
   */
  createPaginatedResponse<T>(
    items: T[],
    page = 1,
    pageSize = 10
  ): {
    items: T[];
    total: number;
    page: number;
    pageSize: number;
    totalPages: number;
  } {
    const start = (page - 1) * pageSize;
    const paginatedItems = items.slice(start, start + pageSize);
    
    return {
      items: paginatedItems,
      total: items.length,
      page,
      pageSize,
      totalPages: Math.ceil(items.length / pageSize),
    };
  }

  /**
   * Validate test data consistency
   */
  validateDataConsistency(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Check progress references
    this.progress.forEach(p => {
      if (!this.users.has(p.userId)) {
        errors.push(`Progress ${p.id} references non-existent user ${p.userId}`);
      }
      if (p.videoId && !this.videos.has(p.videoId)) {
        errors.push(`Progress ${p.id} references non-existent video ${p.videoId}`);
      }
      if (p.vocabularyId && !this.vocabulary.has(p.vocabularyId)) {
        errors.push(`Progress ${p.id} references non-existent vocabulary ${p.vocabularyId}`);
      }
    });
    
    // Check video subtitles
    this.videos.forEach(v => {
      if (v.subtitles) {
        v.subtitles.forEach(s => {
          if (s.videoId !== v.id) {
            errors.push(`Subtitle ${s.id} has incorrect video ID ${s.videoId}`);
          }
        });
      }
    });
    
    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

// Export singleton instance
export const testDataManager = new TestDataManager();
