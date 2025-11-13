/**
 * Vocabulary store with improved caching and state management
 *
 * @deprecated This store is being phased out in favor of React Query hooks.
 * For new components, please use:
 * - useWordsByLevel() - Fetch words by level
 * - useSearchWords() - Search words
 * - useUserProgress() - Get user progress
 * - useVocabularyStats() - Get statistics
 * - useMarkWord() - Mark words as known/unknown
 * - useVocabularyUIStore - For UI state (currentLevel, searchQuery, etc.)
 *
 * See: docs/guides/REACT_QUERY_MIGRATION.md
 * See: docs/guides/PHASE3_COMPONENT_MIGRATION_EXAMPLES.md
 */
import { create } from 'zustand'
import { subscribeWithSelector, devtools } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { api } from '@/services/api-client'

export interface VocabularyWord {
  id: number
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

export interface VocabularyStats {
  total_reviewed: number
  known_words: number
  unknown_words: number
  percentage_known: number
  level_breakdown?: Record<string, number>
}

export interface VocabularyState {
  // Data
  words: Record<number, VocabularyWord>
  userProgress: Record<number, UserVocabularyProgress>
  searchResults: VocabularyWord[]
  stats: VocabularyStats | null

  // UI State
  isLoading: boolean
  isSearching: boolean
  currentLevel: string
  currentLanguage: string
  searchQuery: string

  // Cache state
  lastFetch: Record<string, number>
  cacheExpiry: number

  // Actions
  setWords: (words: VocabularyWord[]) => void
  setUserProgress: (progress: UserVocabularyProgress[]) => void
  setStats: (stats: VocabularyStats) => void
  setSearchResults: (results: VocabularyWord[]) => void
  setLoading: (loading: boolean) => void
  setSearching: (searching: boolean) => void
  setCurrentLevel: (level: string) => void
  setCurrentLanguage: (language: string) => void
  setSearchQuery: (query: string) => void

  // API Actions
  searchWords: (query: string, language?: string, limit?: number) => Promise<void>
  fetchWordsByLevel: (level: string, language?: string) => Promise<void>
  fetchRandomWords: (
    language?: string,
    levels?: string[],
    limit?: number
  ) => Promise<VocabularyWord[]>
  markWord: (vocabularyId: number, isKnown: boolean) => Promise<void>
  bulkMarkWords: (vocabularyIds: number[], isKnown: boolean) => Promise<void>
  fetchUserProgress: (language?: string) => Promise<void>
  fetchStats: (language?: string) => Promise<void>
  refreshAll: () => Promise<void>
  reset: () => void
}

const initialState = {
  words: {},
  userProgress: {},
  searchResults: [],
  stats: null,
  isLoading: false,
  isSearching: false,
  currentLevel: 'A1',
  currentLanguage: 'de',
  searchQuery: '',
  lastFetch: {},
  cacheExpiry: 5 * 60 * 1000, // 5 minutes
}

export const useVocabularyStore = create<VocabularyState>()(
  devtools(
    subscribeWithSelector(
      immer((set, get) => ({
        ...initialState,

        setWords: words => {
          set(state => {
            words.forEach(word => {
              state.words[word.id] = word
            })
          })
        },

        setUserProgress: progress => {
          set(state => {
            progress.forEach(p => {
              state.userProgress[p.vocabulary_id] = p
            })
          })
        },

        setStats: stats => {
          set(state => {
            state.stats = stats
          })
        },

        setSearchResults: results => {
          set(state => {
            state.searchResults = results
          })
        },

        setLoading: loading => {
          set(state => {
            state.isLoading = loading
          })
        },

        setSearching: searching => {
          set(state => {
            state.isSearching = searching
          })
        },

        setCurrentLevel: level => {
          set(state => {
            state.currentLevel = level
          })
        },

        setCurrentLanguage: language => {
          set(state => {
            state.currentLanguage = language
          })
        },

        setSearchQuery: query => {
          set(state => {
            state.searchQuery = query
          })
        },

        searchWords: async (query, language = 'de', limit = 20) => {
          const state = get()
          state.setSearching(true)
          state.setSearchQuery(query)

          try {
            const response = await api.vocabulary.search(query, language, limit)
            const words = response.data as VocabularyWord[]
            state.setSearchResults(words)
            state.setWords(words)
          } catch (error) {
            console.error('Failed to search words:', error)
            state.setSearchResults([])
          } finally {
            state.setSearching(false)
          }
        },

        fetchWordsByLevel: async (level, language = 'de') => {
          const state = get()
          const cacheKey = `words_${level}_${language}`
          const now = Date.now()

          // Check cache
          if (state.lastFetch[cacheKey] && now - state.lastFetch[cacheKey] < state.cacheExpiry) {
            return
          }

          state.setLoading(true)

          try {
            const response = await api.vocabulary.getByLevel(level, language)
            const words = response.data as VocabularyWord[]
            state.setWords(words)
            set(s => {
              s.lastFetch[cacheKey] = now
            })
          } catch (error) {
            console.error('Failed to fetch words by level:', error)
          } finally {
            state.setLoading(false)
          }
        },

        fetchRandomWords: async (
          language = 'de',
          levels,
          limit = 10
        ): Promise<VocabularyWord[]> => {
          const state = get()
          state.setLoading(true)

          try {
            const response = await api.vocabulary.getRandom(language, levels, limit)
            const words = response.data as VocabularyWord[]
            state.setWords(words)
            return words
          } catch (error) {
            console.error('Failed to fetch random words:', error)
            return []
          } finally {
            state.setLoading(false)
          }
        },

        markWord: async (vocabularyId, isKnown) => {
          const state = get()

          try {
            const response = await api.vocabulary.markWord(vocabularyId, isKnown)
            const progress = response.data as UserVocabularyProgress

            set(s => {
              s.userProgress[vocabularyId] = progress
            })

            // Refresh stats after marking
            await state.fetchStats()
          } catch (error) {
            console.error('Failed to mark word:', error)
            throw error
          }
        },

        bulkMarkWords: async (vocabularyIds, isKnown) => {
          const state = get()

          try {
            const response = await api.vocabulary.bulkMarkWords(vocabularyIds, isKnown)
            const progressList = response.data as UserVocabularyProgress[]

            set(s => {
              progressList.forEach(progress => {
                s.userProgress[progress.vocabulary_id] = progress
              })
            })

            // Refresh stats after bulk marking
            await state.fetchStats()
          } catch (error) {
            console.error('Failed to bulk mark words:', error)
            throw error
          }
        },

        fetchUserProgress: async (language = 'de') => {
          const state = get()
          const cacheKey = `progress_${language}`
          const now = Date.now()

          // Check cache
          if (state.lastFetch[cacheKey] && now - state.lastFetch[cacheKey] < state.cacheExpiry) {
            return
          }

          try {
            const response = await api.vocabulary.getProgress(language)
            const progress = response.data as UserVocabularyProgress[]
            state.setUserProgress(progress)
            set(s => {
              s.lastFetch[cacheKey] = now
            })
          } catch (error) {
            console.error('Failed to fetch user progress:', error)
          }
        },

        fetchStats: async (language = 'de') => {
          const state = get()

          try {
            const response = await api.vocabulary.getStats(language)
            const stats = response.data as VocabularyStats
            state.setStats(stats)
          } catch (error) {
            console.error('Failed to fetch stats:', error)
          }
        },

        refreshAll: async () => {
          const state = get()
          const { currentLanguage, currentLevel } = state

          // Clear cache
          set(s => {
            s.lastFetch = {}
          })

          await Promise.all([
            state.fetchWordsByLevel(currentLevel, currentLanguage),
            state.fetchUserProgress(currentLanguage),
            state.fetchStats(currentLanguage),
          ])
        },

        reset: () => {
          set(initialState)
        },
      }))
    ),
    {
      name: 'vocabulary-store',
    }
  )
)

// Selectors for better performance
export const useVocabularyWords = () => useVocabularyStore(state => Object.values(state.words))
export const useVocabularySearchResults = () => useVocabularyStore(state => state.searchResults)
export const useVocabularyStats = () => useVocabularyStore(state => state.stats)
export const useVocabularyLoading = () => useVocabularyStore(state => state.isLoading)
export const useVocabularySearching = () => useVocabularyStore(state => state.isSearching)
export const useUserProgress = () => useVocabularyStore(state => Object.values(state.userProgress))

// Helper function to get word progress
export const useWordProgress = (vocabularyId: number) =>
  useVocabularyStore(state => state.userProgress[vocabularyId] || null)

// Helper function to check if word is known
export const useIsWordKnown = (vocabularyId: number) =>
  useVocabularyStore(state => state.userProgress[vocabularyId]?.is_known || false)
