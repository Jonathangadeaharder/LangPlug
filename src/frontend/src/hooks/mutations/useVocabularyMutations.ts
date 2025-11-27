/**
 * Vocabulary mutation hooks using React Query
 * Uses OpenAPI generated client for type-safe API calls
 */
import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import {
  markWordKnownApiVocabularyMarkKnownPost,
  bulkMarkLevelApiVocabularyLibraryBulkMarkPost,
} from '@/client/services.gen'
import { queryKeys } from '@/config/queryClient'

// ========== Mutation Inputs ==========

interface MarkWordParams {
  lemma: string
  isKnown: boolean
  language: string
}

interface BulkMarkLevelParams {
  level: string
  isKnown: boolean
  language: string
}

// ========== Mutations ==========

/**
 * Mark a single word as known/unknown
 * Automatically invalidates progress and stats queries
 */
export const useMarkWord = (
  options?: Omit<
    UseMutationOptions<unknown, Error, MarkWordParams>,
    'mutationFn'
  >
) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ lemma, isKnown, language }: MarkWordParams) => {
      return await markWordKnownApiVocabularyMarkKnownPost({
        requestBody: {
          lemma,
          language,
          known: isKnown,
        },
      })
    },

    onSuccess: (_data, variables) => {
      const { language } = variables

      // Invalidate progress and stats to trigger refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.list(language) })
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.stats(language) })
      queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary.all })

      // Show success message
      toast.success(variables.isKnown ? 'Word marked as known' : 'Word marked as unknown')
    },

    onError: error => {
      console.error('Failed to mark word:', error)
      toast.error('Failed to update word status')
    },

    ...options,
  })
}

/**
 * Mark all words in a level as known/unknown
 * Automatically invalidates progress and stats queries
 */
export const useBulkMarkLevel = (
  options?: Omit<
    UseMutationOptions<unknown, Error, BulkMarkLevelParams>,
    'mutationFn'
  >
) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ level, isKnown, language }: BulkMarkLevelParams) => {
      return await bulkMarkLevelApiVocabularyLibraryBulkMarkPost({
        requestBody: {
          level,
          target_language: language,
          known: isKnown,
        },
      })
    },

    onSuccess: (_data, variables) => {
      const { language, level } = variables

      // Invalidate progress and stats to trigger refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.list(language) })
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.stats(language) })
      queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary.all })

      // Show success message
      toast.success(
        variables.isKnown
          ? `All ${level} words marked as known`
          : `All ${level} words marked as unknown`
      )
    },

    onError: error => {
      console.error('Failed to bulk mark level:', error)
      toast.error('Failed to update words')
    },

    ...options,
  })
}

/**
 * Refresh all vocabulary data
 * Forces refetch of all vocabulary-related queries
 */
export const useRefreshVocabulary = () => {
  const queryClient = useQueryClient()

  return () => {
    // Invalidate all vocabulary queries
    queryClient.invalidateQueries({ queryKey: queryKeys.vocabulary.all })
    queryClient.invalidateQueries({ queryKey: queryKeys.progress.all })

    toast.success('Vocabulary data refreshed')
  }
}
