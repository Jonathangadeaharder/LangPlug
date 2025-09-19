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
  getAvailableVideosApiVideosGet: vi.fn(),
  getVideoStatusApiVideosVideoIdStatusGet: vi.fn(),
  uploadVideoApiVideosUploadSeriesPost: vi.fn(),
  uploadVideoGenericApiVideosUploadPost: vi.fn(),
  fullPipelineApiProcessFullPipelinePost: vi.fn(),
  getTaskProgressApiProcessProgressTaskIdGet: vi.fn(),
  loginApiAuthLoginPost: vi.fn(),
  registerApiAuthRegisterPost: vi.fn(),
  getCurrentUserInfoApiAuthMeGet: vi.fn()
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

      assertMockResolvedValue(mockSdk.getAvailableVideosApiVideosGet, { data: mockVideos });

      const result = await getVideos();

      assertApiCallMade(mockSdk.getAvailableVideosApiVideosGet);
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
      
      mockSdk.fullPipelineApiProcessFullPipelinePost.mockResolvedValue({ data: mockResponse });
      
      const result = await processVideo('video-123');
      
      expect(mockSdk.fullPipelineApiProcessFullPipelinePost).toHaveBeenCalledWith({
        body: { video_id: 'video-123' }
      });
      expect(result).toEqual(mockResponse);
    });

    it('gets processing status', async () => {
      const mockStatus = {
        taskId: 'task-123',
        status: 'completed',
        progress: 100,
        result: { videoId: 'video-123' }
      };
      
      mockSdk.getTaskProgressApiProcessProgressTaskIdGet.mockResolvedValue({ data: mockStatus });
      
      const result = await getProcessingStatus('task-123');
      
      expect(mockSdk.getTaskProgressApiProcessProgressTaskIdGet).toHaveBeenCalledWith({
        path: { task_id: 'task-123' }
      });
      expect(result).toEqual(mockStatus);
    });
  });

  describe('Authentication API', () => {
    it('logs in user successfully', async () => {
      const mockLoginResponse = {
        access_token: 'jwt-token-123',
        user: { id: '1', email: 'test@example.com', name: 'Test User' }
      };
      
      mockSdk.loginApiAuthLoginPost.mockResolvedValue({ data: mockLoginResponse });
      
      const result = await login('test@example.com', 'password123');
      
      expect(mockSdk.loginApiAuthLoginPost).toHaveBeenCalledWith({
        body: { username: 'test@example.com', password: 'password123' }
      });
      expect(result).toEqual({
        token: 'jwt-token-123',
        user: { id: '1', email: 'test@example.com', name: 'Test User' }
      });
    });

    it('registers user successfully', async () => {
      const mockRegisterResponse = {
        access_token: 'jwt-token-456',
        user: { id: '2', email: 'new@example.com', name: 'New User' }
      };
      
      mockSdk.registerApiAuthRegisterPost.mockResolvedValue({ data: mockRegisterResponse });
      
      const result = await register('new@example.com', 'password123', 'New User');
      
      expect(mockSdk.registerApiAuthRegisterPost).toHaveBeenCalledWith({
        body: { email: 'new@example.com', password: 'password123', name: 'New User' }
      });
      expect(result).toEqual({
        token: 'jwt-token-456',
        user: { id: '2', email: 'new@example.com', name: 'New User' }
      });
    });

    it('gets user profile', async () => {
      const mockProfile = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User'
      };
      
      mockSdk.getCurrentUserInfoApiAuthMeGet.mockResolvedValue({ data: mockProfile });
      
      const result = await getProfile();
      
      expect(mockSdk.getCurrentUserInfoApiAuthMeGet).toHaveBeenCalled();
      expect(result).toEqual(mockProfile);
    });
  });

  describe('Error Handling', () => {
    it('WhenNetworkErrorOccurs_ThenThrowsError', async () => {
      const networkError = new Error('Network Error');
      assertMockRejectedValue(mockSdk.getAvailableVideosApiVideosGet, networkError);

      await expect(getVideos()).rejects.toThrow('Network Error');
    });

    it('WhenApiErrorWithStatusCode_ThenThrowsApiError', async () => {
      const apiError = { status: 404, message: 'Video not found' };
      assertMockRejectedValue(mockSdk.getVideoStatusApiVideosVideoIdStatusGet, apiError);

      await expect(getVideoDetails('nonexistent')).rejects.toEqual(apiError);
    });
  });
});