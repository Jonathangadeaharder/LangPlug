/**
 * Vocabulary query hooks using React Query
 * Uses OpenAPI generated client for type-safe API calls
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import {
  getVocabularyLevelApiVocabularyLibraryLevelGet,
  searchVocabularyApiVocabularySearchPost,
  getVocabularyStatsApiVocabularyStatsGet,
  getVocabularyLibraryApiVocabularyLibraryGet,
} from '@/client/services.gen'
import { queryKeys } from '@/config/queryClient'
import type { VocabularyWord, UserProgressRecord, VocabularyStats } from '../types'

// ========== Queries ==========

/**
 * Fetch words by difficulty level
 * @param level - CEFR level (A1, A2, B1, B2, C1, C2)
 * @param language - Language code (default: 'de')
 */
export const useWordsByLevel = (
  level: string,
  language = 'de',
  options?: Omit<UseQueryOptions<VocabularyWord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.vocabulary.list({ level, language }),
    queryFn: async (): Promise<VocabularyWord[]> => {
      const response: { words?: VocabularyWord[] } = await getVocabularyLevelApiVocabularyLibraryLevelGet({
        level,
        targetLanguage: language,
      }) as { words?: VocabularyWord[] }
      return response.words || []
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
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
  language = 'de',
  limit = 20,
  options?: Omit<UseQueryOptions<VocabularyWord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.vocabulary.search(query, language),
    queryFn: async (): Promise<VocabularyWord[]> => {
      if (!query || query.trim().length === 0) {
        return []
      }
      const response: { results?: VocabularyWord[] } = await searchVocabularyApiVocabularySearchPost({
        requestBody: {
          search_term: query,
          language,
          limit,
        },
      }) as { results?: VocabularyWord[] }
      return response.results || []
    },
    enabled: query.trim().length > 0,
    staleTime: 2 * 60 * 1000,
    ...options,
  })
}

/**
 * Fetch random words for practice
 * Uses vocabulary library with random selection
 * @param language - Language code (default: 'de')
 * @param levels - Array of CEFR levels to include
 * @param limit - Number of words to fetch (default: 10)
 */
export const useRandomWords = (
  language = 'de',
  levels?: string[],
  limit = 10,
  options?: Omit<UseQueryOptions<VocabularyWord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.vocabulary.random(language, levels, limit),
    queryFn: async (): Promise<VocabularyWord[]> => {
      // Get vocabulary library and randomly select words
      const level = levels?.[0] // Use first level if specified
      const response: { words?: VocabularyWord[] } = await getVocabularyLibraryApiVocabularyLibraryGet({
        language,
        level,
        limit: limit * 3, // Get more to enable random selection
      }) as { words?: VocabularyWord[] }
      const words = response.words || []
      // Shuffle and take limit
      return words.sort(() => Math.random() - 0.5).slice(0, limit)
    },
    staleTime: 0, // Random words should be refetched each time
    ...options,
  })
}

/**
 * Fetch user's progress for all words
 * Uses vocabulary library which includes progress info
 * @param language - Language code (default: 'de')
 */
export const useUserProgress = (
  language = 'de',
  options?: Omit<UseQueryOptions<UserProgressRecord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.progress.list(language),
    queryFn: async (): Promise<UserProgressRecord[]> => {
      // Get vocabulary library which includes is_known status
      const response: { words?: Array<{ id: number; is_known?: boolean }> } = await getVocabularyLibraryApiVocabularyLibraryGet({
        language,
        limit: 10000, // Get all words
      }) as { words?: Array<{ id: number; is_known?: boolean }> }
      // Convert to progress format
      return (response.words || []).map((w) => ({
        vocabulary_id: w.id,
        is_known: w.is_known || false,
        language,
      }))
    },
    staleTime: 5 * 60 * 1000,
    ...options,
  })
}

/**
 * Fetch user's vocabulary statistics
 * @param language - Language code (default: 'de')
 */
export const useVocabularyStats = (
  language = 'de',
  options?: Omit<UseQueryOptions<VocabularyStats>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.progress.stats(language),
    queryFn: async () => {
      const response = await getVocabularyStatsApiVocabularyStatsGet({
        targetLanguage: language,
      })
      return response as VocabularyStats
    },
    staleTime: 2 * 60 * 1000,
    refetchOnWindowFocus: true,
    ...options,
  })
}

// ========== Derived Selectors ==========

/**
 * Get progress for a specific word
 * Uses memoized selector to prevent unnecessary re-renders
 * @param vocabularyId - Word ID
 * @param language - Language code (default: 'de')
 */
export const useWordProgress = (vocabularyId: number, language = 'de') => {
  return useQuery({
    queryKey: queryKeys.progress.list(language),
    queryFn: async (): Promise<UserProgressRecord[]> => {
      const response: { words?: Array<{ id: number; is_known?: boolean }> } = await getVocabularyLibraryApiVocabularyLibraryGet({
        language,
        limit: 10000,
      }) as { words?: Array<{ id: number; is_known?: boolean }> }
      return (response.words || []).map((w) => ({
        vocabulary_id: w.id,
        is_known: w.is_known || false,
        language,
      }))
    },
    select: (allProgress) => allProgress.find(p => p.vocabulary_id === vocabularyId) || null,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Check if a word is known by the user
 * Uses memoized selector to prevent unnecessary re-renders
 * @param vocabularyId - Word ID
 * @param language - Language code (default: 'de')
 */
export const useIsWordKnown = (vocabularyId: number, language = 'de') => {
  return useQuery({
    queryKey: queryKeys.progress.list(language),
    queryFn: async (): Promise<UserProgressRecord[]> => {
      const response: { words?: Array<{ id: number; is_known?: boolean }> } = await getVocabularyLibraryApiVocabularyLibraryGet({
        language,
        limit: 10000,
      }) as { words?: Array<{ id: number; is_known?: boolean }> }
      return (response.words || []).map((w) => ({
        vocabulary_id: w.id,
        is_known: w.is_known || false,
        language,
      }))
    },
    select: (allProgress) => {
      const progress = allProgress.find(p => p.vocabulary_id === vocabularyId)
      return progress?.is_known || false
    },
    staleTime: 5 * 60 * 1000,
  })
}
