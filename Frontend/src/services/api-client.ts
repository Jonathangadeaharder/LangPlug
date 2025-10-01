/**
 * Enhanced API client with better error handling and caching
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { toast } from 'react-hot-toast'
import { logger } from './logger'

export interface ApiResponse<T = any> {
  data: T
  status: number
  message?: string
}

export interface ApiError {
  status: number
  message: string
  code?: string
  details?: any
}

class ApiClient {
  private client: AxiosInstance
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>()

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor for auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request ID for tracing
        config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

        logger.debug('ApiClient', 'Sending request', {
          method: config.method?.toUpperCase(),
          url: config.url,
          headers: config.headers,
        })

        return config
      },
      (error) => {
        logger.error('API Request Error', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        logger.debug('ApiClient', 'Received response', {
          status: response.status,
          url: response.config.url,
          data: response.data,
        })
        return response
      },
      (error) => {
        const apiError = this.handleApiError(error)
        logger.error('ApiClient', 'API error occurred', apiError)

        // Show toast for user-facing errors
        if (apiError.status !== 401) {
          toast.error(apiError.message)
        }

        return Promise.reject(apiError)
      }
    )
  }

  private handleApiError(error: any): ApiError {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      const message = data?.detail || data?.message || error.message || 'Server error'

      return {
        status,
        message,
        code: data?.code,
        details: data,
      }
    } else if (error.request) {
      // Network error
      return {
        status: 0,
        message: 'Network error - please check your connection',
        code: 'NETWORK_ERROR',
      }
    } else {
      // Other error
      return {
        status: 0,
        message: error.message || 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
      }
    }
  }

  private getCacheKey(url: string, params?: any): string {
    return `${url}${params ? `?${JSON.stringify(params)}` : ''}`
  }

  private getFromCache<T>(key: string): T | null {
    const cached = this.cache.get(key)
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data
    }
    this.cache.delete(key)
    return null
  }

  private setCache<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
  }

  async get<T>(
    url: string,
    config?: AxiosRequestConfig & { cache?: boolean; cacheTtl?: number }
  ): Promise<ApiResponse<T>> {
    const { cache = false, cacheTtl = 5 * 60 * 1000, ...axiosConfig } = config || {}

    if (cache) {
      const cacheKey = this.getCacheKey(url, axiosConfig.params)
      const cached = this.getFromCache<T>(cacheKey)
      if (cached) {
        return { data: cached, status: 200 }
      }
    }

    const response = await this.client.get<T>(url, axiosConfig)

    if (cache) {
      const cacheKey = this.getCacheKey(url, axiosConfig.params)
      this.setCache(cacheKey, response.data, cacheTtl)
    }

    return {
      data: response.data,
      status: response.status,
    }
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.post<T>(url, data, config)
    return {
      data: response.data,
      status: response.status,
    }
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.put<T>(url, data, config)
    return {
      data: response.data,
      status: response.status,
    }
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    const response = await this.client.delete<T>(url, config)
    return {
      data: response.data,
      status: response.status,
    }
  }

  clearCache(): void {
    this.cache.clear()
  }

  clearCachePattern(pattern: string): void {
    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key)
      }
    }
  }
}

// Global API client instance
export const apiClient = new ApiClient()

// Convenience methods for common patterns
export const api = {
  // Authentication
  auth: {
    login: (credentials: { username: string; password: string }) =>
      apiClient.post('/auth/login', credentials),
    register: (userData: { username: string; email: string; password: string }) =>
      apiClient.post('/auth/register', userData),
    getCurrentUser: () => apiClient.get('/auth/me', { cache: true, cacheTtl: 60000 }),
    logout: () => {
      localStorage.removeItem('authToken')
      apiClient.clearCache()
    },
  },

  // Vocabulary
  vocabulary: {
    search: (query: string, language = 'de', limit = 20) =>
      apiClient.get('/vocabulary/search', {
        params: { query, language, limit },
        cache: true,
        cacheTtl: 10 * 60 * 1000, // 10 minutes
      }),
    getByLevel: (level: string, language = 'de', skip = 0, limit = 100) =>
      apiClient.get(`/vocabulary/level/${level}`, {
        params: { language, skip, limit },
        cache: true,
        cacheTtl: 30 * 60 * 1000, // 30 minutes
      }),
    getRandom: (language = 'de', levels?: string[], limit = 10) =>
      apiClient.get('/vocabulary/random', {
        params: { language, levels, limit },
        cache: true,
        cacheTtl: 5 * 60 * 1000, // 5 minutes
      }),
    markWord: (vocabularyId: number, isKnown: boolean) =>
      apiClient.post('/vocabulary/mark', { vocabulary_id: vocabularyId, is_known: isKnown }),
    bulkMarkWords: (vocabularyIds: number[], isKnown: boolean) =>
      apiClient.post('/vocabulary/mark-bulk', { vocabulary_ids: vocabularyIds, is_known: isKnown }),
    getProgress: (language = 'de') =>
      apiClient.get('/vocabulary/progress', {
        params: { language },
        cache: true,
        cacheTtl: 30 * 1000, // 30 seconds
      }),
    getStats: (language = 'de') =>
      apiClient.get('/vocabulary/stats', {
        params: { language },
        cache: true,
        cacheTtl: 60 * 1000, // 1 minute
      }),
  },

  // Videos and processing
  videos: {
    getList: () => apiClient.get('/api/videos', { cache: true }),
    getEpisodes: (series: string) =>
      apiClient.get(`/api/videos/${series}`, { cache: true }),
    getStreamUrl: (series: string, episode: string) => {
      const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const token = localStorage.getItem('authToken')
      const url = `${base}/api/videos/${encodeURIComponent(series)}/${encodeURIComponent(episode)}`
      return token ? `${url}?token=${encodeURIComponent(token)}` : url
    },
  },

  // Processing
  processing: {
    startTranscription: (series: string, episode: string) =>
      apiClient.post('/process/transcribe', { series, episode }),
    getProgress: (taskId: string) =>
      apiClient.get(`/process/progress/${taskId}`),
    prepareEpisode: (series: string, episode: string) =>
      apiClient.post('/process/prepare-episode', { series, episode }),
  },
}
