/**
 * Vocabulary query hooks using React Query
 * Replaces server-side data fetching from useVocabularyStore
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { api } from '@/services/api-client'
import { queryKeys } from '@/lib/queryClient'
import type { VocabularyWord, UserVocabularyProgress, VocabularyStats } from '@/store/useVocabularyStore'

// ========== Queries ==========

/**
 * Fetch words by difficulty level
 * @param level - CEFR level (A1, A2, B1, B2, C1, C2)
 * @param language - Language code (default: 'de')
 */
export const useWordsByLevel = (
  level: string,
  language: string = 'de',
  options?: Omit<UseQueryOptions<VocabularyWord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.vocabulary.list({ level, language }),
    queryFn: async () => {
      const response = await api.vocabulary.getByLevel(level, language)
      return response.data as VocabularyWord[]
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - same as Zustand cache
    ...options,
  })
}

/**
 * Search words by query string
 * @param query - Search query
 * @param language - Language code (default: 'de')
 * @param limit - Max results (default: 20)
 */
export const useSearchWords = (
  query: string,
  language: string = 'de',
  limit: number = 20,
  options?: Omit<UseQueryOptions<VocabularyWord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.vocabulary.search(query, language),
    queryFn: async () => {
      if (!query || query.trim().length === 0) {
        return []
      }
      const response = await api.vocabulary.search(query, language, limit)
      return response.data as VocabularyWord[]
    },
    enabled: query.trim().length > 0, // Only run query if there's a search term
    staleTime: 2 * 60 * 1000, // 2 minutes - search results go stale faster
    ...options,
  })
}

/**
 * Fetch random words for practice
 * @param language - Language code (default: 'de')
 * @param levels - Array of CEFR levels to include
 * @param limit - Number of words to fetch (default: 10)
 */
export const useRandomWords = (
  language: string = 'de',
  levels?: string[],
  limit: number = 10,
  options?: Omit<UseQueryOptions<VocabularyWord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.vocabulary.random(language, levels, limit),
    queryFn: async () => {
      const response = await api.vocabulary.getRandom(language, levels, limit)
      return response.data as VocabularyWord[]
    },
    staleTime: 0, // Random words should be refetched each time
    ...options,
  })
}

/**
 * Fetch user's progress for all words
 * @param language - Language code (default: 'de')
 */
export const useUserProgress = (
  language: string = 'de',
  options?: Omit<UseQueryOptions<UserVocabularyProgress[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.progress.list(language),
    queryFn: async () => {
      const response = await api.vocabulary.getProgress(language)
      return response.data as UserVocabularyProgress[]
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  })
}

/**
 * Fetch user's vocabulary statistics
 * @param language - Language code (default: 'de')
 */
export const useVocabularyStats = (
  language: string = 'de',
  options?: Omit<UseQueryOptions<VocabularyStats>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.progress.stats(language),
    queryFn: async () => {
      const response = await api.vocabulary.getStats(language)
      return response.data as VocabularyStats
    },
    staleTime: 2 * 60 * 1000, // 2 minutes - stats change frequently
    refetchOnWindowFocus: true, // Always refresh stats when user returns
    ...options,
  })
}

// ========== Derived Selectors ==========

/**
 * Get progress for a specific word
 * @param vocabularyId - Word ID
 * @param language - Language code (default: 'de')
 */
export const useWordProgress = (vocabularyId: number, language: string = 'de') => {
  const { data: allProgress } = useUserProgress(language)

  return allProgress?.find(p => p.vocabulary_id === vocabularyId) || null
}

/**
 * Check if a word is known by the user
 * @param vocabularyId - Word ID
 * @param language - Language code (default: 'de')
 */
export const useIsWordKnown = (vocabularyId: number, language: string = 'de'): boolean => {
  const progress = useWordProgress(vocabularyId, language)
  return progress?.is_known || false
}
