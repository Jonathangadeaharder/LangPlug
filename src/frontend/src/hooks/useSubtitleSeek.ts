/**
 * Hook for subtitle-based video seeking
 * Allows seeking to specific words, sentences, or navigating between segments
 */
import { useCallback } from 'react'
import { SubtitleSegment, subtitleSyncService } from '../services/subtitleSyncService'

interface UseSubtitleSeekReturn {
  seekToWord: (word: string) => void
  seekToSegment: (segmentIndex: number) => void
  seekToTime: (timeInSeconds: number) => void
  seekPreviousSegment: () => void
  seekNextSegment: () => void
}

export const useSubtitleSeek = (
  videoRef: React.RefObject<HTMLVideoElement>,
  segments: SubtitleSegment[]
): UseSubtitleSeekReturn => {
  const seekToWord = useCallback(
    (word: string) => {
      const video = videoRef.current
      if (!video) return

      const normalizedWord = word.toLowerCase().trim()

      // Find first occurrence of word in segments
      for (const segment of segments) {
        const wordData = segment.words.find(w => w.word.toLowerCase() === normalizedWord)

        if (wordData) {
          video.currentTime = wordData.start
          return
        }
      }

      console.warn(`[WARN] Word "${word}" not found in subtitles`)
    },
    [videoRef, segments]
  )

  const seekToSegment = useCallback(
    (segmentIndex: number) => {
      const video = videoRef.current
      if (!video) return

      if (segmentIndex >= 0 && segmentIndex < segments.length) {
        const segment = segments[segmentIndex]
        video.currentTime = segment.start
      } else {
        console.warn(`[WARN] Segment index ${segmentIndex} out of bounds (0-${segments.length - 1})`)
      }
    },
    [videoRef, segments]
  )

  const seekToTime = useCallback(
    (timeInSeconds: number) => {
      const video = videoRef.current
      if (!video) return

      if (timeInSeconds >= 0 && timeInSeconds <= video.duration) {
        video.currentTime = timeInSeconds
      } else {
        console.warn(`[WARN] Time ${timeInSeconds}s out of bounds (0-${video.duration})`)
      }
    },
    [videoRef]
  )

  const seekPreviousSegment = useCallback(() => {
    const video = videoRef.current
    if (!video) return

    const currentTime = video.currentTime
    const previousSegment = subtitleSyncService.getPreviousSegment(segments, currentTime)

    if (previousSegment) {
      video.currentTime = previousSegment.start
    } else {
      // Jump to start if no previous segment
      video.currentTime = 0
    }
  }, [videoRef, segments])

  const seekNextSegment = useCallback(() => {
    const video = videoRef.current
    if (!video) return

    const currentTime = video.currentTime
    const nextSegment = subtitleSyncService.getNextSegment(segments, currentTime)

    if (nextSegment) {
      video.currentTime = nextSegment.start
    }
  }, [videoRef, segments])

  return {
    seekToWord,
    seekToSegment,
    seekToTime,
    seekPreviousSegment,
    seekNextSegment,
  }
}
