/**
 * Type exports for vocabulary hooks
 * Centralized type definitions for React Query hooks
 */

// Core vocabulary types (moved from deprecated useVocabularyStore)
export interface VocabularyWord {
  concept_id?: string | number | null  // Matches API VocabularyWord from OpenAPI schema
  word: string
  lemma: string
  language: string
  difficulty_level: string
  part_of_speech?: string
  gender?: string
  translation_en?: string
  translation_native?: string
  pronunciation?: string
  notes?: string
  frequency_rank?: number
  created_at: string
  updated_at: string
}

export interface UserVocabularyProgress {
  id: number
  user_id: number
  vocabulary_id: number
  lemma: string
  language: string
  is_known: boolean
  confidence_level: number
  review_count: number
  first_seen_at: string
  last_reviewed_at?: string
  vocabulary?: VocabularyWord
}

/**
 * Simplified progress record for vocabulary list queries
 * Contains only the fields returned by the vocabulary library API
 */
export interface UserProgressRecord {
  vocabulary_id: number
  is_known: boolean
  language: string
}

export interface VocabularyStats {
  total_reviewed: number
  known_words: number
  unknown_words: number
  percentage_known: number
  level_breakdown?: Record<string, number>
}

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
  lemma: string
  isKnown: boolean
  language: string
}

export interface BulkMarkWordsParams {
  lemmas: string[]
  isKnown: boolean
  language: string
}
