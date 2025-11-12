/**
 * Vocabulary UI state store (client-side only)
 * Server-side data has been migrated to React Query hooks
 *
 * This store only manages:
 * - Current level selection
 * - Current language selection
 * - Search query
 *
 * For server data, use:
 * - useWordsByLevel() - Fetch words by level
 * - useSearchWords() - Search words
 * - useUserProgress() - User progress
 * - useVocabularyStats() - Statistics
 * - useMarkWord() - Mark word known/unknown
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export interface VocabularyUIState {
  // UI State
  currentLevel: string
  currentLanguage: string
  searchQuery: string

  // Actions
  setCurrentLevel: (level: string) => void
  setCurrentLanguage: (language: string) => void
  setSearchQuery: (query: string) => void
  reset: () => void
}

const initialState = {
  currentLevel: 'A1',
  currentLanguage: 'de',
  searchQuery: '',
}

export const useVocabularyUIStore = create<VocabularyUIState>()(
  devtools(
    set => ({
      ...initialState,

      setCurrentLevel: level => set({ currentLevel: level }),
      setCurrentLanguage: language => set({ currentLanguage: language }),
      setSearchQuery: query => set({ searchQuery: query }),

      reset: () => set(initialState),
    }),
    {
      name: 'vocabulary-ui-store',
    }
  )
)

// Simple selectors
export const useCurrentLevel = () => useVocabularyUIStore(state => state.currentLevel)
export const useCurrentLanguage = () => useVocabularyUIStore(state => state.currentLanguage)
export const useSearchQuery = () => useVocabularyUIStore(state => state.searchQuery)
