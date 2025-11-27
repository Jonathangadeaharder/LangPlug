import { SubtitleMode } from '@/hooks/useSubtitlePreferences'

export interface SubtitleEntry {
  start: number
  end: number
  text: string
  translation?: string
}

export interface ChunkInfo {
  current: number
  total: number
  duration: string
}

export interface LanguageConfig {
  code: string
  name: string
}

export interface ChunkedLearningPlayerProps {
  videoPath: string
  series: string
  episode: string
  subtitlePath?: string
  translationPath?: string
  translationIndices?: number[]
  startTime: number
  endTime: number
  onComplete: () => void
  onSkipChunk?: () => void
  onBack?: () => void
  learnedWords?: string[]
  chunkInfo?: ChunkInfo
  targetLanguage?: LanguageConfig
  nativeLanguage?: LanguageConfig
}

export type PlaybackSpeed = 0.5 | 0.75 | 1 | 1.25 | 1.5 | 2

export interface SubtitleState {
    mode: SubtitleMode
    current: {
        original: string
        translation: string
    }
}
