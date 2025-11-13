/**
 * Vocabulary mutation hooks using React Query
 * Handles write operations and cache invalidation
 */
import { useMutation, useQueryClient, UseMutationOptions } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { api } from '@/services/api-client'
import { queryKeys } from '@/config/queryClient'
import type { UserVocabularyProgress } from '../types'

// ========== Mutation Inputs ==========

interface MarkWordParams {
  vocabularyId: number
  isKnown: boolean
  language?: string
}

interface BulkMarkWordsParams {
  vocabularyIds: number[]
  isKnown: boolean
  language?: string
}

// ========== Mutations ==========

/**
 * Mark a single word as known/unknown
 * Automatically invalidates progress and stats queries
 */
export const useMarkWord = (
  options?: Omit<
    UseMutationOptions<UserVocabularyProgress, Error, MarkWordParams>,
    'mutationFn'
  >
) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ vocabularyId, isKnown }: MarkWordParams) => {
      const response = await api.vocabulary.markWord(vocabularyId, isKnown)
      return response.data as UserVocabularyProgress
    },

    onSuccess: (data, variables) => {
      const language = variables.language || 'de'

      // Update progress cache optimistically
      queryClient.setQueryData<UserVocabularyProgress[]>(
        queryKeys.progress.list(language),
        oldData => {
          if (!oldData) return [data]

          const exists = oldData.some(p => p.vocabulary_id === variables.vocabularyId)
          if (exists) {
            return oldData.map(p => (p.vocabulary_id === variables.vocabularyId ? data : p))
          } else {
            return [...oldData, data]
          }
        }
      )

      // Invalidate stats to trigger refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.stats(language) })

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
 * Mark multiple words as known/unknown at once
 * Automatically invalidates progress and stats queries
 */
export const useBulkMarkWords = (
  options?: Omit<
    UseMutationOptions<UserVocabularyProgress[], Error, BulkMarkWordsParams>,
    'mutationFn'
  >
) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ vocabularyIds, isKnown }: BulkMarkWordsParams) => {
      const response = await api.vocabulary.bulkMarkWords(vocabularyIds, isKnown)
      return response.data as UserVocabularyProgress[]
    },

    onSuccess: (data, variables) => {
      const language = variables.language || 'de'

      // Update progress cache optimistically
      queryClient.setQueryData<UserVocabularyProgress[]>(
        queryKeys.progress.list(language),
        oldData => {
          if (!oldData) return data

          const updatedIds = new Set(data.map(p => p.vocabulary_id))
          const unchanged = oldData.filter(p => !updatedIds.has(p.vocabulary_id))
          return [...unchanged, ...data]
        }
      )

      // Invalidate stats to trigger refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.stats(language) })

      // Show success message
      const count = variables.vocabularyIds.length
      toast.success(
        variables.isKnown
          ? `${count} word${count > 1 ? 's' : ''} marked as known`
          : `${count} word${count > 1 ? 's' : ''} marked as unknown`
      )
    },

    onError: error => {
      console.error('Failed to bulk mark words:', error)
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
