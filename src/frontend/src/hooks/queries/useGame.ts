/**
 * Game query hooks using React Query
 * Replaces server-side data fetching from useGameStore
 */
import { useQuery, UseQueryOptions } from '@tanstack/react-query'
import { getBlockingWordsApiVocabularyBlockingWordsGet } from '@/client/services.gen'
import { queryKeys } from '@/lib/queryClient'
import type { VocabularyWord } from '@/store/useVocabularyStore'

/**
 * Fetch blocking words for a video
 * These are words the user should learn before watching
 */
export const useBlockingWords = (
  videoPath: string,
  options?: Omit<UseQueryOptions<VocabularyWord[]>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: queryKeys.game.blockingWords(videoPath),
    queryFn: async () => {
      const response = await getBlockingWordsApiVocabularyBlockingWordsGet({
        videoPath,
      })

      // Handle both response formats
      const words = Array.isArray(response)
        ? response
        : ((response as { blocking_words?: VocabularyWord[] }).blocking_words ?? [])

      return words as VocabularyWord[]
    },
    enabled: !!videoPath,
    staleTime: 10 * 60 * 1000, // 10 minutes - blocking words don't change often
    ...options,
  })
}
