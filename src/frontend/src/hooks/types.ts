/**
 * Type exports for vocabulary hooks
 * Re-export types to make migration easier
 */

// Re-export types from store for convenience
export type {
  VocabularyWord,
  UserVocabularyProgress,
  VocabularyStats,
} from '@/store/useVocabularyStore'

// Hook option types
export interface UseWordsByLevelOptions {
  enabled?: boolean
  staleTime?: number
  refetchOnWindowFocus?: boolean
}

export interface UseSearchWordsOptions {
  enabled?: boolean
  staleTime?: number
}

export interface MarkWordParams {
  vocabularyId: number
  isKnown: boolean
  language?: string
}

export interface BulkMarkWordsParams {
  vocabularyIds: number[]
  isKnown: boolean
  language?: string
}
