/**
 * Game UI state store (client-side only)
 * Server-side data has been migrated to React Query hooks
 *
 * This store only manages:
 * - Current word index
 * - Subtitle visibility
 * - Processing state
 * - Game session metadata (client-side)
 *
 * For server data, use:
 * - useBlockingWords() - Fetch blocking words for video
 * - useMarkWord() - Mark word as known/unknown
 */
import { create } from 'zustand'
import type { GameSession } from '@/types'

interface GameUIState {
  // Game session (client-side metadata only)
  gameSession: GameSession | null
  currentWordIndex: number
  showSubtitles: boolean
  isProcessing: boolean

  // Actions
  startGame: (videoPath: string) => void
  setCurrentWordIndex: (index: number) => void
  nextWord: () => void
  toggleSubtitles: () => void
  nextSegment: () => void
  setProcessing: (processing: boolean) => void
  resetGame: () => void
  reset: () => void
}

export const useGameUIStore = create<GameUIState>((set, get) => ({
  gameSession: null,
  currentWordIndex: 0,
  showSubtitles: false,
  isProcessing: false,

  startGame: (videoPath: string) => {
    const initialSession: GameSession = {
      video_path: videoPath,
      current_segment: 0,
      segments: [],
      user_progress: {},
      completed: false,
    }

    set({
      gameSession: initialSession,
      currentWordIndex: 0,
      showSubtitles: false,
      isProcessing: false,
    })
  },

  setCurrentWordIndex: (index: number) => {
    set({ currentWordIndex: index })
  },

  nextWord: () => {
    set(state => ({ currentWordIndex: state.currentWordIndex + 1 }))
  },

  toggleSubtitles: () => {
    set(state => ({ showSubtitles: !state.showSubtitles }))
  },

  nextSegment: () => {
    const { gameSession } = get()
    if (!gameSession) return

    const nextSegmentIndex = gameSession.current_segment + 1

    set({
      gameSession: {
        ...gameSession,
        current_segment: nextSegmentIndex,
      },
      currentWordIndex: 0,
    })
  },

  setProcessing: (processing: boolean) => {
    set({ isProcessing: processing })
  },

  resetGame: () => {
    set({
      gameSession: null,
      currentWordIndex: 0,
      showSubtitles: false,
      isProcessing: false,
    })
  },

  reset: () => {
    set({
      gameSession: null,
      currentWordIndex: 0,
      showSubtitles: false,
      isProcessing: false,
    })
  },
}))
