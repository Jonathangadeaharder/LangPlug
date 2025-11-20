import { describe, it, expect, beforeEach, afterEach, vi, beforeAll } from 'vitest'

// Mock axios BEFORE importing api-client
// Define axiosInstance inside the factory to avoid hoisting issues
vi.mock('axios', () => {
  const axiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
  }

  return {
    default: {
      create: vi.fn(() => axiosInstance),
    },
  }
})

vi.mock('react-hot-toast', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
    loading: vi.fn(),
  },
}))

vi.mock('../logger', () => ({
  logger: {
    debug: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
  },
}))

// Import AFTER mocks are set up
import { apiClient, api } from '../api-client'
import { toast } from 'react-hot-toast'
import axios from 'axios'

const mockedAxios = axios as any

// Get the axiosInstance from the mocked create call
// @ts-expect-error - accessing mock internals
const axiosInstance = mockedAxios.create.mock.results[0]?.value

describe('ApiClient', () => {
  beforeAll(() => {
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
      configurable: true,
    })
  })

  beforeEach(() => {
    // Clear all mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('initialization', () => {
    it('should create axios instance with correct config', () => {
      expect(mockedAxios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
          timeout: 30000,
          headers: {
            'Content-Type': 'application/json',
          },
        })
      )
    })

    it('should setup request and response interceptors', () => {
      expect(axiosInstance.interceptors.request.use).toHaveBeenCalled()
      expect(axiosInstance.interceptors.response.use).toHaveBeenCalled()
    })
  })

  describe('get method', () => {
    it('should make GET request and return data', async () => {
      const mockData = { id: 1, name: 'Test' }
      axiosInstance.get.mockResolvedValueOnce({
        data: mockData,
        status: 200,
      })

      const result = await apiClient.get('/test')

      expect(axiosInstance.get).toHaveBeenCalledWith('/test', {})
      expect(result).toEqual({
        data: mockData,
        status: 200,
      })
    })

    it('should pass config to axios', async () => {
      axiosInstance.get.mockResolvedValueOnce({ data: {}, status: 200 })

      await apiClient.get('/test', { params: { id: 1 } })

      expect(axiosInstance.get).toHaveBeenCalledWith('/test', { params: { id: 1 } })
    })

    it('should use cache when enabled', async () => {
      const mockData = { id: 1, name: 'Cached' }
      axiosInstance.get.mockResolvedValueOnce({ data: mockData, status: 200 })

      // First call - should hit API
      const result1 = await apiClient.get('/test', { cache: true })
      expect(axiosInstance.get).toHaveBeenCalledTimes(1)
      expect(result1.data).toEqual(mockData)

      // Second call - should use cache
      const result2 = await apiClient.get('/test', { cache: true })
      expect(axiosInstance.get).toHaveBeenCalledTimes(1) // Still 1
      expect(result2.data).toEqual(mockData)
    })

    it('should respect cache TTL', async () => {
      const mockData = { id: 1, name: 'Expired' }
      axiosInstance.get.mockResolvedValue({ data: mockData, status: 200 })

      // First call with very short TTL
      await apiClient.get('/test', { cache: true, cacheTtl: 10 })

      // Wait for cache to expire
      await new Promise(resolve => setTimeout(resolve, 20))

      // Second call - should hit API again
      await apiClient.get('/test', { cache: true, cacheTtl: 10 })

      expect(axiosInstance.get).toHaveBeenCalledTimes(2)
    })

    it('should generate different cache keys for different params', async () => {
      axiosInstance.get.mockResolvedValue({ data: {}, status: 200 })

      await apiClient.get('/test', { cache: true, params: { id: 1 } })
      await apiClient.get('/test', { cache: true, params: { id: 2 } })

      // Different params = different cache keys = 2 API calls
      expect(axiosInstance.get).toHaveBeenCalledTimes(2)
    })
  })

  describe('post method', () => {
    it('should make POST request with data', async () => {
      const postData = { username: 'test', password: 'pass' }
      const responseData = { token: 'abc123' }
      axiosInstance.post.mockResolvedValueOnce({ data: responseData, status: 201 })

      const result = await apiClient.post('/auth/login', postData)

      expect(axiosInstance.post).toHaveBeenCalledWith('/auth/login', postData, undefined)
      expect(result).toEqual({
        data: responseData,
        status: 201,
      })
    })

    it('should pass config to axios', async () => {
      axiosInstance.post.mockResolvedValueOnce({ data: {}, status: 200 })

      const config = { headers: { 'Custom-Header': 'value' } }
      await apiClient.post('/test', { data: 'test' }, config)

      expect(axiosInstance.post).toHaveBeenCalledWith('/test', { data: 'test' }, config)
    })
  })

  describe('put method', () => {
    it('should make PUT request with data', async () => {
      const putData = { name: 'Updated' }
      axiosInstance.put.mockResolvedValueOnce({ data: putData, status: 200 })

      const result = await apiClient.put('/users/1', putData)

      expect(axiosInstance.put).toHaveBeenCalledWith('/users/1', putData, undefined)
      expect(result.data).toEqual(putData)
    })
  })

  describe('delete method', () => {
    it('should make DELETE request', async () => {
      axiosInstance.delete.mockResolvedValueOnce({ data: { success: true }, status: 204 })

      const result = await apiClient.delete('/users/1')

      expect(axiosInstance.delete).toHaveBeenCalledWith('/users/1', undefined)
      expect(result.status).toBe(204)
    })

    it('should pass config to axios', async () => {
      axiosInstance.delete.mockResolvedValueOnce({ data: {}, status: 204 })

      const config = { params: { force: true } }
      await apiClient.delete('/test', config)

      expect(axiosInstance.delete).toHaveBeenCalledWith('/test', config)
    })
  })

  describe('cache management', () => {
    beforeEach(() => {
      axiosInstance.get.mockResolvedValue({ data: {}, status: 200 })
    })

    it('should clear all cache', async () => {
      // Cache some data
      await apiClient.get('/test1', { cache: true })
      await apiClient.get('/test2', { cache: true })

      // Clear cache
      apiClient.clearCache()

      // Next calls should hit API
      await apiClient.get('/test1', { cache: true })
      await apiClient.get('/test2', { cache: true })

      expect(axiosInstance.get).toHaveBeenCalledTimes(4) // 2 initial + 2 after clear
    })

    it('should clear cache by pattern', async () => {
      // Cache multiple endpoints
      await apiClient.get('/users/list', { cache: true })
      await apiClient.get('/users/details', { cache: true })
      await apiClient.get('/posts/list', { cache: true })

      // Clear only users-related cache
      apiClient.clearCachePattern('/users')

      // Users cache cleared, posts cache still valid
      await apiClient.get('/users/list', { cache: true })
      await apiClient.get('/posts/list', { cache: true })

      expect(axiosInstance.get).toHaveBeenCalledTimes(4) // 3 initial + 1 users after clear
    })

    it('should not throw when clearing empty cache', () => {
      expect(() => apiClient.clearCache()).not.toThrow()
      expect(() => apiClient.clearCachePattern('test')).not.toThrow()
    })
  })

  describe('convenience API methods', () => {
    describe('auth', () => {
      it('should login with credentials', async () => {
        const credentials = { username: 'user', password: 'pass' }
        axiosInstance.post.mockResolvedValueOnce({
          data: { token: 'abc' },
          status: 200,
        })

        await api.auth.login(credentials)

        expect(axiosInstance.post).toHaveBeenCalledWith('/auth/login', credentials, undefined)
      })

      it('should register user', async () => {
        const userData = { username: 'user', email: 'user@test.com', password: 'pass' }
        axiosInstance.post.mockResolvedValueOnce({ data: { id: 1 }, status: 201 })

        await api.auth.register(userData)

        expect(axiosInstance.post).toHaveBeenCalledWith('/auth/register', userData, undefined)
      })

      it('should get current user with cache', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: { id: 1 }, status: 200 })

        await api.auth.getCurrentUser()

        expect(axiosInstance.get).toHaveBeenCalledWith('/auth/me', {
          cache: true,
          cacheTtl: 60000,
        })
      })

      it('should logout and clear cache', () => {
        localStorage.setItem('authToken', 'test-token')

        api.auth.logout()

        expect(localStorage.getItem('authToken')).toBeNull()
      })
    })

    describe('vocabulary', () => {
      it('should search vocabulary with cache', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: [], status: 200 })

        await api.vocabulary.search('Haus', 'de', 20)

        expect(axiosInstance.get).toHaveBeenCalledWith('/vocabulary/search', {
          params: { query: 'Haus', language: 'de', limit: 20 },
          cache: true,
          cacheTtl: 10 * 60 * 1000,
        })
      })

      it('should get vocabulary by level', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: [], status: 200 })

        await api.vocabulary.getByLevel('A1', 'de', 0, 100)

        expect(axiosInstance.get).toHaveBeenCalledWith('/vocabulary/level/A1', {
          params: { language: 'de', skip: 0, limit: 100 },
          cache: true,
          cacheTtl: 30 * 60 * 1000,
        })
      })

      it('should get random vocabulary', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: [], status: 200 })

        await api.vocabulary.getRandom('de', ['A1', 'A2'], 10)

        expect(axiosInstance.get).toHaveBeenCalledWith('/vocabulary/random', {
          params: { language: 'de', levels: ['A1', 'A2'], limit: 10 },
          cache: true,
          cacheTtl: 5 * 60 * 1000,
        })
      })

      it('should mark word as known/unknown', async () => {
        axiosInstance.post.mockResolvedValueOnce({ data: { success: true }, status: 200 })

        await api.vocabulary.markWord(123, true)

        expect(axiosInstance.post).toHaveBeenCalledWith(
          '/vocabulary/mark',
          { vocabulary_id: 123, is_known: true },
          undefined
        )
      })

      it('should bulk mark words', async () => {
        axiosInstance.post.mockResolvedValueOnce({ data: { success: true }, status: 200 })

        await api.vocabulary.bulkMarkWords([1, 2, 3], false)

        expect(axiosInstance.post).toHaveBeenCalledWith(
          '/vocabulary/mark-bulk',
          { vocabulary_ids: [1, 2, 3], is_known: false },
          undefined
        )
      })

      it('should get progress with cache', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: { progress: 50 }, status: 200 })

        await api.vocabulary.getProgress('de')

        expect(axiosInstance.get).toHaveBeenCalledWith('/vocabulary/progress', {
          params: { language: 'de' },
          cache: true,
          cacheTtl: 30 * 1000,
        })
      })

      it('should get stats with cache', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: { total: 1000 }, status: 200 })

        await api.vocabulary.getStats('de')

        expect(axiosInstance.get).toHaveBeenCalledWith('/vocabulary/stats', {
          params: { language: 'de' },
          cache: true,
          cacheTtl: 60 * 1000,
        })
      })
    })

    describe('videos', () => {
      it('should get video list with cache', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: [], status: 200 })

        await api.videos.getList()

        expect(axiosInstance.get).toHaveBeenCalledWith('/api/videos', { cache: true })
      })

      it('should get episodes for series with cache', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: [], status: 200 })

        await api.videos.getEpisodes('dark')

        expect(axiosInstance.get).toHaveBeenCalledWith('/api/videos/dark', { cache: true })
      })

      it('should generate stream URL without token', () => {
        const url = api.videos.getStreamUrl('dark', 'S01E01')

        expect(url).toContain('/api/videos/dark/S01E01')
        expect(url).not.toContain('token=')
      })

      it('should generate stream URL with token', () => {
        localStorage.setItem('authToken', 'test-token-123')

        const url = api.videos.getStreamUrl('dark', 'S01E01')

        expect(url).toContain('/api/videos/dark/S01E01')
        expect(url).toContain('token=test-token-123')
      })

      it('should URL-encode series and episode names', () => {
        const url = api.videos.getStreamUrl('Series With Spaces', 'S01 E01')

        expect(url).toContain('Series%20With%20Spaces')
        expect(url).toContain('S01%20E01')
      })
    })

    describe('processing', () => {
      it('should start transcription', async () => {
        axiosInstance.post.mockResolvedValueOnce({ data: { taskId: 'task-1' }, status: 200 })

        await api.processing.startTranscription('dark', 'S01E01')

        expect(axiosInstance.post).toHaveBeenCalledWith(
          '/process/transcribe',
          { series: 'dark', episode: 'S01E01' },
          undefined
        )
      })

      it('should get processing progress', async () => {
        axiosInstance.get.mockResolvedValueOnce({ data: { progress: 50 }, status: 200 })

        await api.processing.getProgress('task-123')

        expect(axiosInstance.get).toHaveBeenCalledWith('/process/progress/task-123', undefined)
      })

      it('should prepare episode', async () => {
        axiosInstance.post.mockResolvedValueOnce({ data: { success: true }, status: 200 })

        await api.processing.prepareEpisode('dark', 'S01E01')

        expect(axiosInstance.post).toHaveBeenCalledWith(
          '/process/prepare-episode',
          { series: 'dark', episode: 'S01E01' },
          undefined
        )
      })
    })
  })
})
