/**
 * Hook for interactive subtitle hover functionality
 * Provides word translation on hover with caching
 */
import { useState, useCallback, useRef } from 'react'
import { useTranslationStore } from '../store/useTranslationStore'

interface WordTranslationData {
  word: string
  translation: string
  level?: string
  partOfSpeech?: string
  confidence?: number
}

interface UseSubtitleHoverReturn {
  hoveredWord: string | null
  translationData: WordTranslationData | null
  isLoading: boolean
  error: string | null
  onWordHover: (word: string, event: React.MouseEvent) => Promise<void>
  onWordLeave: () => void
  tooltipPosition: { x: number; y: number } | null
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useSubtitleHover = (language = 'de'): UseSubtitleHoverReturn => {
  const [hoveredWord, setHoveredWord] = useState<string | null>(null)
  const [translationData, setTranslationData] = useState<WordTranslationData | null>(null)
  const [tooltipPosition, setTooltipPosition] = useState<{ x: number; y: number } | null>(null)

  const {
    getWordTranslation,
    cacheTranslation,
    isWordLoading,
    setLoading,
    getError,
    setError,
    clearError,
  } = useTranslationStore()

  // Track the current hover request to prevent race conditions
  const currentHoverRequest = useRef<string | null>(null)

  const onWordHover = useCallback(
    async (word: string, event: React.MouseEvent) => {
      const normalizedWord = word.toLowerCase().trim()

      // Ignore empty strings or punctuation
      if (!normalizedWord || !/[a-z]/i.test(normalizedWord)) {
        return
      }

      setHoveredWord(word)
      currentHoverRequest.current = normalizedWord

      // Set tooltip position based on mouse coordinates
      setTooltipPosition({
        x: event.clientX,
        y: event.clientY,
      })

      // Check cache first
      const cached = getWordTranslation(normalizedWord)
      if (cached) {
        // Only update if this is still the current hover request
        if (currentHoverRequest.current === normalizedWord) {
          setTranslationData({
            word,
            translation: cached.translation,
            level: cached.level,
            partOfSpeech: cached.partOfSpeech,
            confidence: cached.confidence,
          })
        }
        return
      }

      // Fetch from backend if not cached
      if (!isWordLoading(normalizedWord)) {
        setLoading(normalizedWord, true)
        clearError(normalizedWord)

        try {
          const response = await fetch(
            `${API_BASE_URL}/api/vocabulary/word-info/${encodeURIComponent(word)}?language=${language}`
          )

          if (!response.ok) {
            if (response.status === 404) {
              throw new Error(`Word "${word}" not found in vocabulary database`)
            }
            throw new Error(`Failed to fetch translation: ${response.statusText}`)
          }

          const data = await response.json()

          // Extract translation (handle both array and string formats)
          const translation = Array.isArray(data.translations)
            ? data.translations[0]
            : data.translation || 'Translation not available'

          // Cache the translation
          cacheTranslation(normalizedWord, translation, {
            level: data.level,
            partOfSpeech: data.part_of_speech,
            confidence: 1.0,
          })

          // Only update state if this is still the current hover request
          if (currentHoverRequest.current === normalizedWord) {
            setTranslationData({
              word,
              translation,
              level: data.level,
              partOfSpeech: data.part_of_speech,
              confidence: 1.0,
            })
          }
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Translation failed'
          setError(normalizedWord, errorMessage)

          // Only update error if this is still the current hover request
          if (currentHoverRequest.current === normalizedWord) {
            setTranslationData({
              word,
              translation: 'Translation unavailable',
              confidence: 0,
            })
          }

          console.error(`[ERROR] Translation fetch failed for "${word}":`, error)
        } finally {
          setLoading(normalizedWord, false)
        }
      }
    },
    [language, getWordTranslation, cacheTranslation, isWordLoading, setLoading, setError, clearError]
  )

  const onWordLeave = useCallback(() => {
    setHoveredWord(null)
    setTranslationData(null)
    setTooltipPosition(null)
    currentHoverRequest.current = null
  }, [])

  const isLoading = hoveredWord ? isWordLoading(hoveredWord) : false
  const error = hoveredWord ? getError(hoveredWord) : null

  return {
    hoveredWord,
    translationData,
    isLoading,
    error,
    onWordHover,
    onWordLeave,
    tooltipPosition,
  }
}
