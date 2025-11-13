/**
 * Barrel export for all React Query hooks
 * Makes imports cleaner: import { useWordsByLevel, useMarkWord } from '@/hooks'
 */

// Types
export * from './types'

// Vocabulary queries
export {
  useWordsByLevel,
  useSearchWords,
  useRandomWords,
  useUserProgress,
  useVocabularyStats,
  useWordProgress,
  useIsWordKnown,
} from './queries/useVocabulary'

// Vocabulary mutations
export {
  useMarkWord,
  useBulkMarkWords,
  useRefreshVocabulary,
} from './mutations/useVocabularyMutations'

// Auth queries
export { useCurrentUser } from './queries/useAuth'

// Game queries
export { useBlockingWords } from './queries/useGame'
