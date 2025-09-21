import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  getVideos,
  getVideoDetails,
  uploadVideo,
  processVideo,
  getProcessingStatus,
  login,
  register,
  getProfile
} from '../api';
import { assertApiCallMade, assertMockResolvedValue, assertMockRejectedValue } from '@/test/assertion-helpers';

// Mock the generated SDK
vi.mock('@/client/sdk.gen', () => ({
  getVideosApiVideosGet: vi.fn(),
  getVideoStatusApiVideosVideoIdStatusGet: vi.fn(),
  uploadVideoToSeriesApiVideosUploadSeriesPost: vi.fn(),
  uploadVideoGenericApiVideosUploadPost: vi.fn(),
  fullPipelineApiProcessFullPipelinePost: vi.fn(),
  getTaskProgressApiProcessProgressTaskIdGet: vi.fn(),
  getSubtitlesApiVideosSubtitlesSubtitlePathGet: vi.fn(),
  filterSubtitlesApiProcessFilterSubtitlesPost: vi.fn(),
  translateSubtitlesApiProcessTranslateSubtitlesPost: vi.fn(),
  getVocabularyStatsApiVocabularyStatsGet: vi.fn(),
  getBlockingWordsApiVocabularyBlockingWordsGet: vi.fn(),
  markWordKnownApiVocabularyMarkKnownPost: vi.fn(),
  preloadVocabularyApiVocabularyPreloadPost: vi.fn(),
  getVocabularyLevelApiVocabularyLibraryLevelGet: vi.fn(),
  bulkMarkLevelApiVocabularyLibraryBulkMarkPost: vi.fn(),
  // Authentication functions
  authJwtBearerLoginApiAuthLoginPost: vi.fn(),
  registerRegisterApiAuthRegisterPost: vi.fn(),
  authJwtBearerLogoutApiAuthLogoutPost: vi.fn(),
  authGetCurrentUserApiAuthMeGet: vi.fn()
}));

// Mock the client
vi.mock('@/client/client.gen', () => ({
  client: {
    setConfig: vi.fn()
  },
  createConfig: vi.fn((config) => config)
}));

import * as sdk from '@/client/sdk.gen';
const mockSdk = vi.mocked(sdk);

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Video API', () => {
    it('WhenVideosRequested_ThenReturnsVideoList', async () => {
      const mockVideos = [
        { id: '1', title: 'Test Video 1', description: 'Description 1' },
        { id: '2', title: 'Test Video 2', description: 'Description 2' }
      ];

      assertMockResolvedValue(mockSdk.getVideosApiVideosGet, { data: mockVideos });

      const result = await getVideos();

      assertApiCallMade(mockSdk.getVideosApiVideosGet);
      expect(result).toEqual(mockVideos);
    });

    it('WhenVideoDetailsRequested_ThenReturnsVideoInfo', async () => {
      const mockVideoDetails = {
        id: '1', title: 'Test Video', description: 'Test Description',
        episodes: [{ id: '1', title: 'Episode 1', duration: 1800 }]
      };

      assertMockResolvedValue(mockSdk.getVideoStatusApiVideosVideoIdStatusGet, { data: mockVideoDetails });

      const result = await getVideoDetails('1');

      assertApiCallMade(mockSdk.getVideoStatusApiVideosVideoIdStatusGet, { path: { video_id: '1' } });
      expect(result).toEqual(mockVideoDetails);
    });

    it('handles video upload', async () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' });
      const mockResponse = { taskId: 'task-123', status: 'processing' };

      mockSdk.uploadVideoGenericApiVideosUploadPost.mockResolvedValue({ data: mockResponse });

      const result = await uploadVideo(mockFile);

      expect(mockSdk.uploadVideoGenericApiVideosUploadPost).toHaveBeenCalledWith({
        body: expect.any(FormData)
      });
      expect(result).toEqual(mockResponse);
    });

    it('processes video successfully', async () => {
      const mockResponse = { taskId: 'task-456', status: 'started' };
      const mockStatus = { taskId: 'task-456', status: 'processing' };

      assertMockResolvedValue(mockSdk.fullPipelineApiProcessFullPipelinePost, { data: mockResponse });

      const result = await processVideo('video-123');

      assertMockResolvedValue(mockSdk.getTaskProgressApiProcessProgressTaskIdGet, { data: mockStatus });

      const statusResult = await getProcessingStatus('task-123');

      expect(mockSdk.getTaskProgressApiProcessProgressTaskIdGet).toHaveBeenCalledWith({
        path: { task_id: 'task-123' }
      });
      expect(statusResult).toEqual(mockStatus);
    });
  });

  describe('Authentication API', () => {
    it('logs in user successfully', async () => {
      const mockLoginResponse = {
        access_token: 'jwt-token-123',
        token_type: 'bearer',
        user: { id: '1', email: 'test@example.com', name: 'Test User' }
      };

      assertMockResolvedValue(mockSdk.authJwtBearerLoginApiAuthLoginPost, { data: mockLoginResponse });

      const result = await login('test@example.com', 'password123');

      expect(mockSdk.authJwtBearerLoginApiAuthLoginPost).toHaveBeenCalledWith({
        body: expect.objectContaining({
          username: 'test@example.com',
          password: 'password123'
        })
      });
      expect(result).toEqual({
        token: 'jwt-token-123',
        user: { id: '', email: 'test@example.com', name: '' },
        expires_at: ''
      });
    });

    it('registers user successfully', async () => {
      const mockRegisterResponse = { success: true };
      assertMockResolvedValue(mockSdk.registerRegisterApiAuthRegisterPost, { data: mockRegisterResponse });

      // login() is called after register to obtain token
      const mockLoginAfterRegister = { access_token: 'jwt-token-456', token_type: 'bearer' };
      assertMockResolvedValue(mockSdk.authJwtBearerLoginApiAuthLoginPost, { data: mockLoginAfterRegister });

      const result = await register('new@example.com', 'password123', 'New User');

      expect(mockSdk.registerRegisterApiAuthRegisterPost).toHaveBeenCalledWith({
        body: { email: 'new@example.com', password: 'password123', username: 'New User' }
      });
      expect(result).toEqual({
        token: 'jwt-token-456',
        user: { id: '', email: 'new@example.com', name: '' },
        expires_at: ''
      });
    });

    it('gets user profile', async () => {
      const mockProfile = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User'
      };

      assertMockResolvedValue(mockSdk.authGetCurrentUserApiAuthMeGet, {
        data: {
          id: '1',
          email: 'test@example.com',
          username: 'Test User',
          is_superuser: false,
          is_active: true,
          created_at: '2023-01-01T00:00:00Z'
        }
      });

      const result = await getProfile();

      expect(mockSdk.authGetCurrentUserApiAuthMeGet).toHaveBeenCalled();
      expect(result).toEqual({
        id: '1',
        email: 'test@example.com',
        name: 'Test User'
      });
    });
  });

  describe('Error Handling', () => {
    it('WhenNetworkErrorOccurs_ThenThrowsError', async () => {
      const networkError = new Error('Network Error');
      assertMockRejectedValue(mockSdk.getVideosApiVideosGet, networkError);

      await expect(getVideos()).rejects.toThrow('Network Error');
    });

    it('WhenApiErrorWithStatusCode_ThenThrowsApiError', async () => {
      const apiError = { status: 404, message: 'Video not found' };
      assertMockRejectedValue(mockSdk.getVideoStatusApiVideosVideoIdStatusGet, apiError);

      await expect(getVideoDetails('nonexistent')).rejects.toEqual(apiError);
    });
  });
});