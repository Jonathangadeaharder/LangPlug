/**
 * Custom hooks for API interactions with error handling and caching
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { api, ApiResponse, ApiError } from '@/services/api-client'
import { useAppStore } from '@/store/useAppStore'

export interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  reset: () => void
}

export interface UseApiOptions {
  immediate?: boolean
  cache?: boolean
  cacheTtl?: number
  retries?: number
  retryDelay?: number
}

/**
 * Generic hook for API calls with error handling and loading states
 */
export function useApi<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  deps: React.DependencyList = [],
  options: UseApiOptions = {}
): UseApiState<T> {
  const {
    immediate = true,
    cache = false,
    cacheTtl = 5 * 60 * 1000,
    retries = 3,
    retryDelay = 1000,
  } = options

  const [state, setState] = useState<{
    data: T | null
    loading: boolean
    error: string | null
  }>({
    data: null,
    loading: false,
    error: null,
  })

  const setError = useAppStore((state) => state.setError)
  const retryCount = useRef(0)
  const cacheRef = useRef<{ data: T; timestamp: number } | null>(null)

  const fetchData = useCallback(async () => {
    // Check cache first
    if (cache && cacheRef.current) {
      const { data, timestamp } = cacheRef.current
      if (Date.now() - timestamp < cacheTtl) {
        setState({ data, loading: false, error: null })
        return
      }
    }

    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await apiCall()
      const data = response.data

      // Cache the data
      if (cache) {
        cacheRef.current = { data, timestamp: Date.now() }
      }

      setState({ data, loading: false, error: null })
      retryCount.current = 0
    } catch (error) {
      const apiError = error as ApiError
      const errorMessage = apiError.message || 'An unexpected error occurred'

      setState((prev) => ({ ...prev, loading: false, error: errorMessage }))
      setError(errorMessage)

      // Retry logic
      if (retryCount.current < retries && apiError.status !== 401 && apiError.status !== 403) {
        retryCount.current++
        setTimeout(() => {
          fetchData()
        }, retryDelay * retryCount.current)
      }
    }
  }, [apiCall, cache, cacheTtl, retries, retryDelay, setError])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
    retryCount.current = 0
    cacheRef.current = null
  }, [])

  useEffect(() => {
    if (immediate) {
      fetchData()
    }
  }, [fetchData, immediate, ...deps])

  return {
    ...state,
    refetch: fetchData,
    reset,
  }
}

/**
 * Hook for authentication-related API calls
 */
export function useAuth() {
  const setError = useAppStore((state) => state.setError)

  const login = useCallback(
    async (credentials: { username: string; password: string }) => {
      try {
        const response = await api.auth.login(credentials)
        const { access_token } = response.data as { access_token: string }
        localStorage.setItem('authToken', access_token)
        return response.data
      } catch (error) {
        const apiError = error as ApiError
        setError(apiError.message)
        throw error
      }
    },
    [setError]
  )

  const register = useCallback(
    async (userData: { username: string; email: string; password: string }) => {
      try {
        const response = await api.auth.register(userData)
        return response.data
      } catch (error) {
        const apiError = error as ApiError
        setError(apiError.message)
        throw error
      }
    },
    [setError]
  )

  const logout = useCallback(() => {
    api.auth.logout()
    localStorage.removeItem('authToken')
  }, [])

  const getCurrentUser = useApi(
    () => api.auth.getCurrentUser(),
    [],
    { cache: true, cacheTtl: 60000 }
  )

  return {
    login,
    register,
    logout,
    currentUser: getCurrentUser,
  }
}

/**
 * Hook for vocabulary-related API calls
 */
export function useVocabularyApi() {
  const searchWords = useCallback(
    (query: string, language = 'de', limit = 20) =>
      useApi(
        () => api.vocabulary.search(query, language, limit),
        [query, language, limit],
        { cache: true, cacheTtl: 10 * 60 * 1000, immediate: !!query }
      ),
    []
  )

  const getWordsByLevel = useCallback(
    (level: string, language = 'de') =>
      useApi(
        () => api.vocabulary.getByLevel(level, language),
        [level, language],
        { cache: true, cacheTtl: 30 * 60 * 1000 }
      ),
    []
  )

  const getRandomWords = useCallback(
    (language = 'de', levels?: string[], limit = 10) =>
      useApi(
        () => api.vocabulary.getRandom(language, levels, limit),
        [language, JSON.stringify(levels), limit],
        { cache: true, cacheTtl: 5 * 60 * 1000 }
      ),
    []
  )

  const getUserProgress = useCallback(
    (language = 'de') =>
      useApi(
        () => api.vocabulary.getProgress(language),
        [language],
        { cache: true, cacheTtl: 30 * 1000 }
      ),
    []
  )

  const getStats = useCallback(
    (language = 'de') =>
      useApi(
        () => api.vocabulary.getStats(language),
        [language],
        { cache: true, cacheTtl: 60 * 1000 }
      ),
    []
  )

  const markWord = useCallback(
    async (vocabularyId: number, isKnown: boolean) => {
      try {
        const response = await api.vocabulary.markWord(vocabularyId, isKnown)
        return response.data
      } catch (error) {
        const apiError = error as ApiError
        throw new Error(apiError.message)
      }
    },
    []
  )

  const bulkMarkWords = useCallback(
    async (vocabularyIds: number[], isKnown: boolean) => {
      try {
        const response = await api.vocabulary.bulkMarkWords(vocabularyIds, isKnown)
        return response.data
      } catch (error) {
        const apiError = error as ApiError
        throw new Error(apiError.message)
      }
    },
    []
  )

  return {
    searchWords,
    getWordsByLevel,
    getRandomWords,
    getUserProgress,
    getStats,
    markWord,
    bulkMarkWords,
  }
}

/**
 * Hook for processing-related API calls
 */
export function useProcessingApi() {
  const startTranscription = useCallback(
    async (series: string, episode: string) => {
      try {
        const response = await api.processing.startTranscription(series, episode)
        return response.data
      } catch (error) {
        const apiError = error as ApiError
        throw new Error(apiError.message)
      }
    },
    []
  )

  const getProgress = useCallback(
    (taskId: string) =>
      useApi(
        () => api.processing.getProgress(taskId),
        [taskId],
        { immediate: !!taskId }
      ),
    []
  )

  const prepareEpisode = useCallback(
    async (series: string, episode: string) => {
      try {
        const response = await api.processing.prepareEpisode(series, episode)
        return response.data
      } catch (error) {
        const apiError = error as ApiError
        throw new Error(apiError.message)
      }
    },
    []
  )

  return {
    startTranscription,
    getProgress,
    prepareEpisode,
  }
}

/**
 * Hook for videos-related API calls
 */
export function useVideosApi() {
  const getVideoList = useApi(
    () => api.videos.getList(),
    [],
    { cache: true, cacheTtl: 10 * 60 * 1000 }
  )

  const getEpisodes = useCallback(
    (series: string) =>
      useApi(
        () => api.videos.getEpisodes(series),
        [series],
        { cache: true, cacheTtl: 10 * 60 * 1000, immediate: !!series }
      ),
    []
  )

  const getStreamUrl = useCallback(
    (series: string, episode: string) => api.videos.getStreamUrl(series, episode),
    []
  )

  return {
    videoList: getVideoList,
    getEpisodes,
    getStreamUrl,
  }
}

/**
 * Hook for handling async operations with loading and error states
 */
export function useAsyncOperation<T extends (...args: any[]) => Promise<any>>(
  operation: T
): [T, { loading: boolean; error: string | null }] {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wrappedOperation = useCallback(
    async (...args: Parameters<T>) => {
      setLoading(true)
      setError(null)

      try {
        const result = await operation(...args)
        return result
      } catch (error) {
        const apiError = error as ApiError
        const errorMessage = apiError.message || 'An unexpected error occurred'
        setError(errorMessage)
        throw error
      } finally {
        setLoading(false)
      }
    },
    [operation]
  ) as T

  return [wrappedOperation, { loading, error }]
}
