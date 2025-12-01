import { useState, useEffect, useCallback, RefObject } from 'react'
import ReactPlayer from 'react-player'
import { PlaybackSpeed } from '../types'

interface UsePlayerControlsProps {
  playerRef: RefObject<ReactPlayer>
  startTime: number
  endTime: number
  onComplete: () => void
  onSkip: () => void
}

export const usePlayerControls = ({
  playerRef,
  startTime,
  endTime,
  onComplete,
  onSkip
}: UsePlayerControlsProps) => {
  // State
  const [playing, setPlaying] = useState(false)
  const [volume, setVolume] = useState(1)
  const [muted, setMuted] = useState(false)
  const [playbackRate, setPlaybackRate] = useState<PlaybackSpeed>(1)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [showControls, setShowControls] = useState(true)
  const [currentTime, setCurrentTime] = useState(startTime)

  // Computed
  const chunkDuration = endTime - startTime
  const progress = Math.max(0, Math.min(100, ((currentTime - startTime) / chunkDuration) * 100))

  // Check for chunk completion
  useEffect(() => {
    if (currentTime >= endTime && playing) {
      setPlaying(false)
      onComplete()
    }
  }, [currentTime, endTime, playing, onComplete])

  // Fullscreen toggler
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return

      switch (e.code) {
        case 'Space':
          e.preventDefault()
          setPlaying(prev => !prev)
          break
        case 'ArrowLeft':
          e.preventDefault()
          if (playerRef.current) {
            const newTime = Math.max(startTime, currentTime - 10)
            playerRef.current.seekTo(newTime)
            setCurrentTime(newTime)
          }
          break
        case 'ArrowRight':
          e.preventDefault()
          if (playerRef.current) {
            const newTime = Math.min(endTime, currentTime + 10)
            playerRef.current.seekTo(newTime)
            setCurrentTime(newTime)
          }
          break
        case 'KeyF':
          e.preventDefault()
          toggleFullscreen()
          break
        case 'KeyM':
          e.preventDefault()
          setMuted(prev => !prev)
          break
      }
      setShowControls(true)
    }

    document.addEventListener('keydown', handleKeyPress)
    return () => document.removeEventListener('keydown', handleKeyPress)
  }, [currentTime, startTime, endTime, playerRef, toggleFullscreen])

  // Update fullscreen state
  useEffect(() => {
    const onFsChange = () => setIsFullscreen(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', onFsChange)
    return () => document.removeEventListener('fullscreenchange', onFsChange)
  }, [])

  return {
    state: {
      playing,
      volume,
      muted,
      playbackRate,
      isFullscreen,
      showControls,
      currentTime,
      progress
    },
    actions: {
      setPlaying,
      setVolume,
      setMuted,
      setPlaybackRate,
      setShowControls,
      setCurrentTime,
      toggleFullscreen,
      handleSeek: (time: number) => {
        playerRef.current?.seekTo(time)
        setCurrentTime(time)
      },
      handleSkip: onSkip
    }
  }
}
