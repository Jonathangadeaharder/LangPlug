import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSubtitleSeek } from '../useSubtitleSeek'
import { SubtitleSegment } from '../../services/subtitleSyncService'
import { RefObject } from 'react'

describe('useSubtitleSeek', () => {
  let videoRef: RefObject<HTMLVideoElement>
  let mockVideo: Partial<HTMLVideoElement>

  const segments: SubtitleSegment[] = [
    {
      id: '1',
      start: 0.0,
      end: 3.0,
      text: 'First segment',
      words: [
        { word: 'First', start: 0.0, end: 1.0 },
        { word: 'segment', start: 1.0, end: 3.0 },
      ],
    },
    {
      id: '2',
      start: 4.0,
      end: 7.0,
      text: 'Second segment',
      words: [
        { word: 'Second', start: 4.0, end: 5.5 },
        { word: 'segment', start: 5.5, end: 7.0 },
      ],
    },
    {
      id: '3',
      start: 8.0,
      end: 11.0,
      text: 'Third segment',
      words: [
        { word: 'Third', start: 8.0, end: 9.5 },
        { word: 'segment', start: 9.5, end: 11.0 },
      ],
    },
  ]

  beforeEach(() => {
    mockVideo = {
      currentTime: 0,
      duration: 15,
    }

    videoRef = {
      current: mockVideo as HTMLVideoElement,
    }
  })

  describe('seekToWord', () => {
    it('should seek to the first occurrence of a word', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToWord('Second')
      })

      expect(mockVideo.currentTime).toBe(4.0)
    })

    it('should handle case-insensitive word search', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToWord('FIRST')
      })

      expect(mockVideo.currentTime).toBe(0.0)
    })

    it('should trim whitespace from word', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToWord('  Third  ')
      })

      expect(mockVideo.currentTime).toBe(8.0)
    })

    it('should handle word not found gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToWord('nonexistent')
      })

      expect(mockVideo.currentTime).toBe(0) // Unchanged
      expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('nonexistent'))

      consoleWarnSpy.mockRestore()
    })

    it('should do nothing if videoRef is null', () => {
      const nullRef: RefObject<HTMLVideoElement> = { current: null }
      const { result } = renderHook(() => useSubtitleSeek(nullRef, segments))

      act(() => {
        result.current.seekToWord('First')
      })

      // No error should be thrown
      expect(nullRef.current).toBeNull()
    })
  })

  describe('seekToSegment', () => {
    it('should seek to the specified segment by index', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToSegment(1) // Second segment
      })

      expect(mockVideo.currentTime).toBe(4.0)
    })

    it('should seek to first segment (index 0)', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 5.0 // Start at different time

      act(() => {
        result.current.seekToSegment(0)
      })

      expect(mockVideo.currentTime).toBe(0.0)
    })

    it('should seek to last segment', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToSegment(2) // Third segment
      })

      expect(mockVideo.currentTime).toBe(8.0)
    })

    it('should handle negative index gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToSegment(-1)
      })

      expect(mockVideo.currentTime).toBe(0) // Unchanged
      expect(consoleWarnSpy).toHaveBeenCalled()

      consoleWarnSpy.mockRestore()
    })

    it('should handle out of bounds index gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToSegment(10) // Way out of bounds
      })

      expect(mockVideo.currentTime).toBe(0) // Unchanged
      expect(consoleWarnSpy).toHaveBeenCalled()

      consoleWarnSpy.mockRestore()
    })
  })

  describe('seekToTime', () => {
    it('should seek to the specified time', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToTime(5.5)
      })

      expect(mockVideo.currentTime).toBe(5.5)
    })

    it('should seek to start (time 0)', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 10.0

      act(() => {
        result.current.seekToTime(0)
      })

      expect(mockVideo.currentTime).toBe(0)
    })

    it('should seek to end of video', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToTime(15) // video.duration
      })

      expect(mockVideo.currentTime).toBe(15)
    })

    it('should handle negative time gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToTime(-5)
      })

      expect(mockVideo.currentTime).toBe(0) // Unchanged
      expect(consoleWarnSpy).toHaveBeenCalled()

      consoleWarnSpy.mockRestore()
    })

    it('should handle time beyond duration gracefully', () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))

      act(() => {
        result.current.seekToTime(100) // Way beyond duration
      })

      expect(mockVideo.currentTime).toBe(0) // Unchanged
      expect(consoleWarnSpy).toHaveBeenCalled()

      consoleWarnSpy.mockRestore()
    })
  })

  describe('seekPreviousSegment', () => {
    it('should seek to previous segment when in middle of current segment', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 5.0 // In second segment

      act(() => {
        result.current.seekPreviousSegment()
      })

      expect(mockVideo.currentTime).toBe(0.0) // First segment
    })

    it('should seek to start when already at first segment', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 1.0 // In first segment

      act(() => {
        result.current.seekPreviousSegment()
      })

      expect(mockVideo.currentTime).toBe(0) // Jump to start
    })

    it('should seek to start when before all segments', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = -1.0 // Before any segment

      act(() => {
        result.current.seekPreviousSegment()
      })

      expect(mockVideo.currentTime).toBe(0)
    })

    it('should work from third segment', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 9.0 // In third segment

      act(() => {
        result.current.seekPreviousSegment()
      })

      expect(mockVideo.currentTime).toBe(4.0) // Second segment
    })
  })

  describe('seekNextSegment', () => {
    it('should seek to next segment when in current segment', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 1.0 // In first segment

      act(() => {
        result.current.seekNextSegment()
      })

      expect(mockVideo.currentTime).toBe(4.0) // Second segment
    })

    it('should do nothing when already at last segment', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 9.0 // In third segment

      act(() => {
        result.current.seekNextSegment()
      })

      expect(mockVideo.currentTime).toBe(9.0) // Unchanged
    })

    it('should seek to first segment when before all segments', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = -1.0 // Before any segment

      act(() => {
        result.current.seekNextSegment()
      })

      expect(mockVideo.currentTime).toBe(0.0) // First segment
    })

    it('should work from second segment', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, segments))
      mockVideo.currentTime = 5.0 // In second segment

      act(() => {
        result.current.seekNextSegment()
      })

      expect(mockVideo.currentTime).toBe(8.0) // Third segment
    })
  })

  describe('edge cases', () => {
    it('should handle empty segments array', () => {
      const { result } = renderHook(() => useSubtitleSeek(videoRef, []))

      act(() => {
        result.current.seekToWord('test')
        result.current.seekToSegment(0)
        result.current.seekPreviousSegment()
        result.current.seekNextSegment()
      })

      // Should not crash
      expect(videoRef.current).toBeTruthy()
    })

    it('should update when segments change', () => {
      const { result, rerender } = renderHook(
        ({ segs }) => useSubtitleSeek(videoRef, segs),
        { initialProps: { segs: segments } }
      )

      const newSegments: SubtitleSegment[] = [
        {
          id: '1',
          start: 0.0,
          end: 5.0,
          text: 'New segment',
          words: [{ word: 'New', start: 0.0, end: 2.5 }, { word: 'segment', start: 2.5, end: 5.0 }],
        },
      ]

      rerender({ segs: newSegments })

      act(() => {
        result.current.seekToWord('New')
      })

      expect(mockVideo.currentTime).toBe(0.0)
    })
  })
})
