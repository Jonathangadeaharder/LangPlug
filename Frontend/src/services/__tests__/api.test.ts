import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  login,
  register,
  logout,
  getProfile,
  getVideos,
  getVideoDetails,
  uploadVideo,
  processVideo,
  getProcessingStatus
} from '../api';

// Mock the generated Services client
vi.mock('@/client/services.gen', () => ({
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

// No need to mock OpenAPI client directly for these unit tests

import * as Services from '@/client/services.gen';
const mockServices = vi.mocked(Services as any);

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
        { id: '1', title: 'Video 1', duration: 120 },
        { id: '2', title: 'Video 2', duration: 240 },
      ];

      mockServices.getVideosApiVideosGet.mockResolvedValue(mockVideos);

      const result = await getVideos();

      expect(mockServices.getVideosApiVideosGet).toHaveBeenCalled();
      expect(result).toEqual(mockVideos);
    });

    it('WhenVideoDetailsRequested_ThenReturnsVideoInfo', async () => {
      const mockVideoDetails = {
        id: '1', title: 'Test Video', description: 'Test Description',
        episodes: [{ id: '1', title: 'Episode 1', duration: 1800 }]
      } as any;

      mockServices.getVideoStatusApiVideosVideoIdStatusGet.mockResolvedValue(mockVideoDetails);

      const result = await getVideoDetails('1');

      expect(mockServices.getVideoStatusApiVideosVideoIdStatusGet).toHaveBeenCalledWith({ videoId: '1' });
      expect(result).toEqual(mockVideoDetails);
    });

    it('handles video upload', async () => {
      const mockFile = new File(['test'], 'test.mp4', { type: 'video/mp4' });
      const mockResponse = { ok: true } as any;

      mockServices.uploadVideoGenericApiVideosUploadPost.mockResolvedValue(mockResponse);

      const result = await uploadVideo(mockFile);

      expect(mockServices.uploadVideoGenericApiVideosUploadPost).toHaveBeenCalledWith(
        expect.objectContaining({ formData: expect.any(FormData) })
      );
      expect(result).toEqual(mockResponse);
    });

    it('processes video successfully', async () => {
      const mockStatus = { taskId: 'task-456', status: 'processing' } as any;
      mockServices.fullPipelineApiProcessFullPipelinePost.mockResolvedValue(mockStatus);

      const result = await processVideo('video-123');
      expect(mockServices.fullPipelineApiProcessFullPipelinePost).toHaveBeenCalledWith({
        requestBody: { video_id: 'video-123' }
      });
      expect(result).toEqual(mockStatus);
    });
  });

  describe('Authentication API', () => {
    it('logs in user successfully', async () => {
      const mockLogin = { access_token: 'jwt-token-123', token_type: 'bearer' } as any;
      mockServices.authJwtBearerLoginApiAuthLoginPost.mockResolvedValue(mockLogin);
      mockServices.authGetCurrentUserApiAuthMeGet.mockResolvedValue({
        id: '1', email: 'test@example.com', username: 'Test User'
      } as any);

      const result = await login('test@example.com', 'password123');
      expect(mockServices.authJwtBearerLoginApiAuthLoginPost).toHaveBeenCalledWith({
        formData: { username: 'test@example.com', password: 'password123' }
      });
      expect(result.token).toBe('jwt-token-123');
      expect(result.user.email).toBe('test@example.com');
    });

    it('registers user successfully (then logs in)', async () => {
      mockServices.registerRegisterApiAuthRegisterPost.mockResolvedValue({
        id: 'u1', email: 'new@example.com', username: 'New User'
      } as any);
      mockServices.authJwtBearerLoginApiAuthLoginPost.mockResolvedValue({
        access_token: 'jwt-token-456', token_type: 'bearer'
      } as any);
      mockServices.authGetCurrentUserApiAuthMeGet.mockResolvedValue({
        id: '1', email: 'new@example.com', username: 'New User'
      } as any);

      const result = await register('new@example.com', 'password123', 'New User');
      expect(mockServices.registerRegisterApiAuthRegisterPost).toHaveBeenCalledWith({
        requestBody: { email: 'new@example.com', password: 'password123', username: 'New User' }
      });
      expect(result.token).toBe('jwt-token-456');
    });

    it('gets user profile', async () => {
      mockServices.authGetCurrentUserApiAuthMeGet.mockResolvedValue({
        id: '1', email: 'test@example.com', username: 'Test User'
      } as any);

      const profile = await getProfile();
      expect(mockServices.authGetCurrentUserApiAuthMeGet).toHaveBeenCalled();
      expect(profile).toEqual({ id: '1', email: 'test@example.com', name: 'Test User' });
    });
  });

  describe('Error Handling', () => {
    it('WhenNetworkErrorOccurs_ThenThrowsError', async () => {
      const networkError = new Error('Network Error');
      mockServices.getVideosApiVideosGet.mockRejectedValue(networkError);

      await expect(getVideos()).rejects.toThrow('Network Error');
    });

    it('WhenApiErrorWithStatusCode_ThenThrowsApiError', async () => {
      const apiError = { status: 404, message: 'Video not found' };
      mockServices.getVideoStatusApiVideosVideoIdStatusGet.mockRejectedValue(apiError);

      await expect(getVideoDetails('nonexistent')).rejects.toEqual(apiError);
    });
  });
});