/**
 * React Query client configuration
 * Centralized configuration for all React Query behavior
 */
import { QueryClient, DefaultOptions } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

const queryConfig: DefaultOptions = {
  queries: {
    // Stale time: How long data is considered fresh (5 minutes)
    staleTime: 5 * 60 * 1000,

    // Cache time: How long inactive data stays in cache (10 minutes)
    gcTime: 10 * 60 * 1000,

    // Retry failed requests
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors (client errors)
      const status = (error as { status?: number }).status
      if (status && status >= 400 && status < 500) {
        return false
      }
      // Retry up to 2 times for other errors
      return failureCount < 2
    },

    // Retry delay with exponential backoff
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),

    // Refetch on window focus for critical data
    refetchOnWindowFocus: true,

    // Don't refetch on mount if data is fresh
    refetchOnMount: false,

    // Don't refetch on reconnect by default (queries can override)
    refetchOnReconnect: false,
  },
  mutations: {
    // Global error handling for mutations
    onError: (error) => {
      const message = (error as { message?: string }).message || 'An error occurred'
      toast.error(message)
    },

    // Retry mutations once on network error
    retry: (failureCount, error) => {
      const status = (error as { status?: number }).status
      // Only retry on network errors, not on 4xx/5xx
      if (status !== undefined && status !== 0) {
        return false
      }
      return failureCount < 1
    },
  },
}

export const queryClient = new QueryClient({
  defaultOptions: queryConfig,
})

/**
 * Query keys factory for consistent key management
 * This ensures cache invalidation works correctly across the app
 */
export const queryKeys = {
  // Vocabulary keys
  vocabulary: {
    all: ['vocabulary'] as const,
    lists: () => [...queryKeys.vocabulary.all, 'list'] as const,
    list: (filters: { level?: string; language?: string }) =>
      [...queryKeys.vocabulary.lists(), filters] as const,
    search: (query: string, language?: string) =>
      [...queryKeys.vocabulary.all, 'search', query, language] as const,
    random: (language?: string, levels?: string[], limit?: number) =>
      [...queryKeys.vocabulary.all, 'random', { language, levels, limit }] as const,
    detail: (id: number) => [...queryKeys.vocabulary.all, 'detail', id] as const,
  },

  // User progress keys
  progress: {
    all: ['progress'] as const,
    list: (language?: string) => [...queryKeys.progress.all, 'list', language] as const,
    stats: (language?: string) => [...queryKeys.progress.all, 'stats', language] as const,
    word: (vocabularyId: number) => [...queryKeys.progress.all, 'word', vocabularyId] as const,
  },

  // Auth keys
  auth: {
    all: ['auth'] as const,
    user: () => [...queryKeys.auth.all, 'user'] as const,
    session: () => [...queryKeys.auth.all, 'session'] as const,
  },

  // Game keys
  game: {
    all: ['game'] as const,
    blockingWords: (videoPath: string) =>
      [...queryKeys.game.all, 'blocking-words', videoPath] as const,
    session: (sessionId?: string) => [...queryKeys.game.all, 'session', sessionId] as const,
  },
} as const
