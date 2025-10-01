import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useGameStore } from '../useGameStore'
import * as sdk from '@/client/services.gen'
import type { VocabularyWord } from '@/types'

vi.mock('@/services/api', () => ({}))

vi.mock('@/client/services.gen', () => ({
  getBlockingWordsApiVocabularyBlockingWordsGet: vi.fn(),
  markWordKnownApiVocabularyMarkKnownPost: vi.fn(),
}))

const mockWords: VocabularyWord[] = [
  {
    concept_id: '1',
    word: 'hello',
    translation: 'hola',
    difficulty_level: 'beginner',
    known: false
  },
  {
    concept_id: '2',
    word: 'goodbye',
    translation: 'adiós',
    difficulty_level: 'beginner',
    known: false
  }
]

describe('useGameStore', () => {
  const sdkMock = vi.mocked(sdk)
  beforeEach(() => {
    vi.clearAllMocks()
    useGameStore.getState().resetGame()
  })

  describe('Initial State', () => {
    it('has correct initial state', () => {
      const { result } = renderHook(() => useGameStore())

      expect(result.current.gameSession).toBeNull()
      expect(result.current.currentWords).toEqual([])
      expect(result.current.currentWordIndex).toBe(0)
      expect(result.current.showSubtitles).toBe(false)
      expect(result.current.isProcessing).toBe(false)
    })
  })

  describe('Game Management', () => {
    it('starts new game with video path', () => {
      const { result } = renderHook(() => useGameStore())

      act(() => {
        result.current.startGame('test-video.mp4')
      })

      expect(result.current.gameSession).toEqual({
        video_path: 'test-video.mp4',
        current_segment: 0,
        segments: [],
        user_progress: {},
        completed: false
      })
    })

    it('loads segment words from API', async () => {
    const { result } = renderHook(() => useGameStore())

      sdkMock.getBlockingWordsApiVocabularyBlockingWordsGet.mockResolvedValue({
        blocking_words: mockWords,
      })

      act(() => {
        result.current.startGame('test-video.mp4')
      })

      await act(async () => {
        await result.current.loadSegmentWords(0)
      })

      expect(sdkMock.getBlockingWordsApiVocabularyBlockingWordsGet).toHaveBeenCalledWith({
        videoPath: 'test-video.mp4',
      })
      expect(result.current.currentWords).toEqual(mockWords)
    })

    it('marks words as known via API', async () => {
      const { result } = renderHook(() => useGameStore())

      sdkMock.markWordKnownApiVocabularyMarkKnownPost.mockResolvedValue({ success: true })

      act(() => {
        result.current.startGame('test-video.mp4')
        useGameStore.setState({
          currentWords: mockWords,
          gameSession: {
            video_path: 'test-video.mp4',
            current_segment: 0,
            segments: [],
            user_progress: {},
            completed: false,
          },
        })
      })

      await act(async () => {
        await result.current.markWordKnown('hello', true)
      })

      expect(sdkMock.markWordKnownApiVocabularyMarkKnownPost).toHaveBeenCalledWith({
        requestBody: {
          concept_id: '1',
          known: true,
        },
      })
    })

    it('advances to next word', () => {
      const { result } = renderHook(() => useGameStore())

      // Set up initial state with words
      act(() => {
        result.current.startGame('test-video.mp4')
        useGameStore.setState({ currentWords: mockWords })
      })

      expect(result.current.currentWordIndex).toBe(0)

      act(() => {
        result.current.nextWord()
      })

      expect(result.current.currentWordIndex).toBe(1)
    })

    it('toggles subtitles visibility', () => {
      const { result } = renderHook(() => useGameStore())

      expect(result.current.showSubtitles).toBe(false)

      act(() => {
        result.current.toggleSubtitles()
      })

      expect(result.current.showSubtitles).toBe(true)
    })

    it('resets game to initial state', () => {
      const { result } = renderHook(() => useGameStore())

      // Set up some state
      act(() => {
        result.current.startGame('test-video.mp4')
        result.current.toggleSubtitles()
      })

      // Reset game
      act(() => {
        result.current.resetGame()
      })

      expect(result.current.gameSession).toBeNull()
      expect(result.current.currentWords).toEqual([])
      expect(result.current.currentWordIndex).toBe(0)
      expect(result.current.showSubtitles).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully', async () => {
      const { result } = renderHook(() => useGameStore())

      // Mock console.error to suppress error output during test
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      sdkMock.getBlockingWordsApiVocabularyBlockingWordsGet.mockRejectedValue(new Error('API Error'))

      act(() => {
        result.current.startGame('test-video.mp4')
      })

      await act(async () => {
        await result.current.loadSegmentWords(0)
      })

      expect(result.current.isProcessing).toBe(false)
      expect(result.current.currentWords).toEqual([])
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to load segment words:', expect.any(Error))

      consoleErrorSpy.mockRestore()
    })
  })
})
