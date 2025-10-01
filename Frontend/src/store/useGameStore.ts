import { create } from 'zustand'
import type { GameSession, VideoSegment, VocabularyWord } from '@/types'
import { getBlockingWordsApiVocabularyBlockingWordsGet, markWordKnownApiVocabularyMarkKnownPost } from '@/client/services.gen'

interface GameState {
  gameSession: GameSession | null
  currentWords: VocabularyWord[]
  currentWordIndex: number
  showSubtitles: boolean
  isProcessing: boolean

  // Actions
  startGame: (videoPath: string) => void
  loadSegmentWords: (segmentStart: number) => Promise<void>
  markWordKnown: (word: string, known: boolean) => Promise<void>
  nextWord: () => void
  toggleSubtitles: () => void
  nextSegment: () => Promise<void>
  resetGame: () => void
  reset: () => void
}

export const useGameStore = create<GameState>((set, get) => ({
  gameSession: null,
  currentWords: [],
  currentWordIndex: 0,
  showSubtitles: false,
  isProcessing: false,

  startGame: (videoPath: string) => {
    const initialSession: GameSession = {
      video_path: videoPath,
      current_segment: 0,
      segments: [],
      user_progress: {},
      completed: false
    }

    set({
      gameSession: initialSession,
      currentWords: [],
      currentWordIndex: 0,
      showSubtitles: false,
      isProcessing: false
    })
  },

  loadSegmentWords: async (segmentStart: number) => {
    const { gameSession } = get()
    if (!gameSession) return

    set({ isProcessing: true })

    try {
      const blockingWordsResponse = await getBlockingWordsApiVocabularyBlockingWordsGet({
        videoPath: gameSession.video_path,
      }) as { blocking_words?: VocabularyWord[] } | VocabularyWord[]

      const words = Array.isArray(blockingWordsResponse)
        ? blockingWordsResponse
        : blockingWordsResponse?.blocking_words ?? []

      set({
        currentWords: words,
        currentWordIndex: 0,
        isProcessing: false
      })
    } catch (error) {
      console.error('Failed to load segment words:', error)
      set({ isProcessing: false })
    }
  },

  markWordKnown: async (word: string, known: boolean) => {
    const { gameSession, currentWords } = get()
    if (!gameSession) return

    try {
      const targetWord = currentWords.find(w => w.word === word)
      if (!targetWord) {
        throw new Error(`Unknown word: ${word}`)
      }

      await markWordKnownApiVocabularyMarkKnownPost({
        requestBody: {
          concept_id: targetWord.concept_id,
          known,
        },
      })

      // Update local progress
      const updatedProgress = {
        ...gameSession.user_progress,
        [targetWord.concept_id]: known
      }

      // Update current words
      const updatedWords = currentWords.map(w =>
        w.word === word ? { ...w, known } : w
      )

      set({
        gameSession: {
          ...gameSession,
          user_progress: updatedProgress
        },
        currentWords: updatedWords
      })
    } catch (error) {
      console.error('Failed to mark word:', error)
      // Don't update state on error, but don't throw either
    }
  },

  nextWord: () => {
    const { currentWords, currentWordIndex } = get()
    if (currentWordIndex < currentWords.length - 1) {
      set({ currentWordIndex: currentWordIndex + 1 })
    }
  },

  toggleSubtitles: () => {
    set(state => ({ showSubtitles: !state.showSubtitles }))
  },

  nextSegment: async () => {
    const { gameSession } = get()
    if (!gameSession) return

    const nextSegmentIndex = gameSession.current_segment + 1
    const segmentStart = nextSegmentIndex * 300 // 5 minutes per segment

    set({
      gameSession: {
        ...gameSession,
        current_segment: nextSegmentIndex
      },
      currentWords: [],
      currentWordIndex: 0
    })

    // Load words for next segment
    await get().loadSegmentWords(segmentStart)
  },

  resetGame: () => {
    set({
      gameSession: null,
      currentWords: [],
      currentWordIndex: 0,
      showSubtitles: false,
      isProcessing: false
    })
  },

  reset: () => {
    set({
      gameSession: null,
      currentWords: [],
      currentWordIndex: 0,
      showSubtitles: false,
      isProcessing: false
    })
  }
}))
