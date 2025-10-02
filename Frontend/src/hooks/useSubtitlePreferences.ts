import { useState, useEffect } from 'react'
import { logger } from '@/services/logger'

export type SubtitleMode = 'off' | 'original' | 'translation' | 'both'

const STORAGE_KEY = 'langplug_subtitle_mode'

/**
 * Custom hook for managing subtitle preferences with localStorage persistence
 * @param defaultMode - Default subtitle mode if none is saved
 * @returns [subtitleMode, setSubtitleMode] - Current mode and setter function
 */
export function useSubtitlePreferences(defaultMode: SubtitleMode = 'original'): [SubtitleMode, (mode: SubtitleMode) => void] {
  const [subtitleMode, setSubtitleMode] = useState<SubtitleMode>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved && ['off', 'original', 'translation', 'both'].includes(saved)) {
        return saved as SubtitleMode
      }
    } catch (error) {
      logger.warn('useSubtitlePreferences', 'Failed to load saved preferences', error)
    }
    return defaultMode
  })

  // Save preference whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, subtitleMode)
      logger.info('useSubtitlePreferences', 'Subtitle preference saved', { mode: subtitleMode })
    } catch (error) {
      logger.error('useSubtitlePreferences', 'Failed to save preference', error)
    }
  }, [subtitleMode])

  return [subtitleMode, setSubtitleMode]
}