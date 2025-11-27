import { useState, useEffect, useCallback } from 'react'
import { SubtitleEntry, SubtitleState } from '../types'
import { useSubtitlePreferences } from '@/hooks/useSubtitlePreferences'
import { logger } from '@/services/logger'

// Helper to parse SRT content
const parseSRT = (srtContent: string): SubtitleEntry[] => {
  const entries: SubtitleEntry[] = []
  const blocks = srtContent.trim().split(/\n\s*\n/)

  for (const block of blocks) {
    const lines = block.split('\n')
    if (lines.length >= 3) {
      const timeMatch = lines[1].match(
        /(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})/)
      if (timeMatch) {
        const start =
          parseInt(timeMatch[1]) * 3600 +
          parseInt(timeMatch[2]) * 60 +
          parseInt(timeMatch[3]) +
          parseInt(timeMatch[4]) / 1000
        const end =
          parseInt(timeMatch[5]) * 3600 +
          parseInt(timeMatch[6]) * 60 +
          parseInt(timeMatch[7]) +
          parseInt(timeMatch[8]) / 1000

        const textLines = lines.slice(2)
        let originalText = ''
        let translation = ''

        if (textLines.length > 0 && textLines[0].includes('|')) {
          const parts = textLines[0].split('|')
          originalText = parts[0].trim()
          translation = parts[1]?.trim() || ''
        } else {
          originalText = textLines.join(' ')
        }

        entries.push({ start, end, text: originalText, translation })
      }
    }
  }
  return entries
}

interface UseSubtitleSystemProps {
  subtitlePath?: string
  translationPath?: string
  translationIndices?: number[]
  series: string
  startTime: number
  endTime: number
  currentTime: number
  targetLanguageName?: string
  nativeLanguageName?: string
}

export const useSubtitleSystem = ({
  subtitlePath,
  translationPath,
  translationIndices,
  series,
  startTime,
  endTime,
  currentTime,
  targetLanguageName = 'German',
  nativeLanguageName = 'Spanish'
}: UseSubtitleSystemProps) => {
  // State
  const [subtitleMode, setSubtitleMode] = useSubtitlePreferences('original')
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>([])
  const [translations, setTranslations] = useState<SubtitleEntry[]>([])
  const [currentSubtitle, setCurrentSubtitle] = useState<{ original: string; translation: string }>({
    original: '',
    translation: '',
  })

  // Build URL helper
  const buildSubtitleUrl = useCallback((path: string): string => {
      let subtitleUrl = ''
      if (path.includes('\\') || path.includes(':')) {
        const pathParts = path.replace(/\\/g, '/').split('/')
        const videosIndex = pathParts.findIndex(p => p.toLowerCase() === 'videos')
        if (videosIndex !== -1 && videosIndex < pathParts.length - 1) {
          const relativePath = pathParts.slice(videosIndex + 1).join('/')
          subtitleUrl = `/api/videos/subtitles/${encodeURIComponent(relativePath)}`
        } else {
          const filename = pathParts[pathParts.length - 1]
          subtitleUrl = `/api/videos/subtitles/${encodeURIComponent(`${series}/${filename}`)}`
        }
      } else {
        subtitleUrl = `/api/videos/subtitles/${encodeURIComponent(path)}`
      }

      return subtitleUrl.startsWith('http')
        ? subtitleUrl
        : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${subtitleUrl}`
    }, [series])

  // Load subtitles effect
  useEffect(() => {
    const normalizeEntries = (entries: SubtitleEntry[]): SubtitleEntry[] => {
      const duration = endTime - startTime
      return entries
        .map(entry => {
          const isAbsolute = entry.start >= startTime && startTime > 0
          const relativeStart = isAbsolute ? entry.start - startTime : entry.start
          const relativeEnd = isAbsolute ? entry.end - startTime : entry.end
          return {
            ...entry,
            start: Math.max(0, relativeStart),
            end: Math.max(0, relativeEnd),
          }
        })
        .filter(entry => entry.start <= duration && entry.end >= 0)
    }

    const fetchSubtitles = async () => {
      try {
        const headers = { Authorization: `Bearer ${localStorage.getItem('authToken') || ''}` }
        
        if (subtitlePath) {
          const res = await fetch(`${buildSubtitleUrl(subtitlePath)}?_ts=${Date.now()}`, { headers })
          const text = await res.text()
          setSubtitles(normalizeEntries(parseSRT(text)))
        }

        if (translationPath) {
          const res = await fetch(`${buildSubtitleUrl(translationPath)}?_ts=${Date.now()}`, { headers })
          const text = await res.text()
          setTranslations(normalizeEntries(parseSRT(text)))
        }
      } catch (error) {
        logger.error('useSubtitleSystem', 'Failed to load subtitles', error)
      }
    }

    fetchSubtitles()
  }, [subtitlePath, translationPath, startTime, endTime, buildSubtitleUrl])

  // Sync current subtitle
  useEffect(() => {
    const chunkDuration = endTime - startTime
    const relativeTime = Math.max(0, currentTime - startTime)
    const clampedTime = Math.min(relativeTime, chunkDuration)

    const currentSubIndex = subtitles.findIndex(
      sub => clampedTime >= sub.start && clampedTime <= sub.end
    )
    const currentSub = currentSubIndex >= 0 ? subtitles[currentSubIndex] : null

    const currentTranslation = translations.find(
      trans => clampedTime >= trans.start && clampedTime <= trans.end
    )

    const shouldShowTranslation = translationIndices
      ? translationIndices.includes(currentSubIndex)
      : true

    const translationText = shouldShowTranslation && currentTranslation
      ? (currentTranslation.translation?.trim() || currentTranslation.text || '')
      : ''

    setCurrentSubtitle({
      original: currentSub?.text || '',
      translation: translationText,
    })
  }, [currentTime, subtitles, translations, translationIndices, startTime, endTime])

  return {
    subtitleMode,
    setSubtitleMode,
    currentSubtitle,
    subtitleModeLabels: {
        off: 'Off',
        original: `${targetLanguageName} Only`,
        translation: `${nativeLanguageName} Only`,
        both: 'Both Languages',
    }
  }
}
