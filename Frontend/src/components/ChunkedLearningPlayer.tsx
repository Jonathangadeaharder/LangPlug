import React, { useState, useEffect, useRef, useCallback } from 'react'
import styled from 'styled-components'
import ReactPlayer from 'react-player'
import {
  PlayIcon,
  PauseIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  CheckCircleIcon,
  MinusIcon,
  PlusIcon,
  ArrowLeftIcon,
  ForwardIcon,
  LanguageIcon,
  EyeSlashIcon
} from '@heroicons/react/24/solid'
import axios from 'axios'
import { buildVideoStreamUrl } from '@/services/api'
import { logger } from '@/services/logger'

// Styled Components
const PlayerContainer = styled.div`
  background: #000;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
`

const VideoWrapper = styled.div`
  position: relative;
  width: 100%;
  height: 100vh;
  background: #000;
  cursor: none;

  &.show-cursor {
    cursor: default;
  }

  &.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 9999;
  }
`

const ControlsOverlay = styled.div<{ $visible: boolean; $mobile?: boolean }>`
  position: absolute;
  inset: 0;
  background: linear-gradient(
    transparent 0%,
    transparent 60%,
    rgba(0, 0, 0, 0.3) 85%,
    rgba(0, 0, 0, 0.9) 100%
  );
  opacity: ${props => props.$visible ? 1 : 0};
  transition: opacity 0.3s ease;
  pointer-events: ${props => props.$visible ? 'auto' : 'none'};
  z-index: 10;

  ${props => props.$mobile && `
    padding: 12px;
    background: rgba(0, 0, 0, 0.7);
  `}
`

const TopControls = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  pointer-events: auto;

  @media (max-width: 768px) {
    padding: 16px;
  }
`

const TopLeftControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  @media (max-width: 768px) {
    gap: 12px;
  }
`

const ChunkInfo = styled.div`
  background: rgba(0, 0, 0, 0.8);
  border-radius: 8px;
  padding: 12px 20px;
  color: white;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);

  @media (max-width: 768px) {
    padding: 8px 16px;
    font-size: 14px;
  }
`

const ChunkLabel = styled.div`
  font-size: 12px;
  color: #b3b3b3;
  margin-bottom: 4px;

  @media (max-width: 768px) {
    font-size: 11px;
  }
`

const ChunkDetails = styled.div`
  font-size: 16px;
  font-weight: 500;

  @media (max-width: 768px) {
    font-size: 14px;
  }
`

const PlayerControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  @media (max-width: 768px) {
    gap: 12px;
  }
`

const StickyBackButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.65);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }

  @media (max-width: 768px) {
    padding: 8px 12px;
    font-size: 14px;
  }
`

const StickyNavContainer = styled.div`
  position: absolute;
  top: 16px;
  left: 24px;
  z-index: 30;

  @media (max-width: 768px) {
    left: 16px;
    top: 12px;
  }
`

const LearnedWordsBadge = styled.div`
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid #22c55e;
  color: #22c55e;
  border-radius: 8px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(10px);

  @media (max-width: 768px) {
    padding: 6px 12px;
    font-size: 14px;
  }
`

const BottomControls = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px 24px;
  pointer-events: auto;

  @media (max-width: 768px) {
    padding: 12px 16px 16px;
  }
`

const ProgressContainer = styled.div`
  margin-bottom: 16px;
`

const ProgressBar = styled.div`
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
  transition: height 0.2s;

  &:hover {
    height: 8px;
  }

  @media (max-width: 768px) {
    height: 8px;
  }
`

const ProgressFill = styled.div<{ $progress: number }>`
  width: ${props => props.$progress}%;
  height: 100%;
  background: #e50914;
  border-radius: 3px;
  position: relative;
  transition: width 0.1s ease;

  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: 50%;
    width: 12px;
    height: 12px;
    background: #e50914;
    border: 2px solid white;
    border-radius: 50%;
    transform: translate(50%, -50%);
    opacity: 0;
    transition: opacity 0.2s;
  }

  ${ProgressBar}:hover &::after {
    opacity: 1;
  }
`

const ControlsRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;

  @media (max-width: 768px) {
    gap: 8px;
  }
`

const LeftControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  @media (max-width: 768px) {
    gap: 12px;
  }
`

const RightControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  @media (max-width: 768px) {
    gap: 12px;
  }
`

const ControlButton = styled.button<{ $large?: boolean }>`
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: ${props => props.$large ? '12px' : '8px'};
  border-radius: 6px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: ${props => props.$large ? '48px' : '40px'};
  min-height: ${props => props.$large ? '48px' : '40px'};

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
  }

  &:active {
    transform: scale(0.95);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  @media (max-width: 768px) {
    min-width: ${props => props.$large ? '44px' : '36px'};
    min-height: ${props => props.$large ? '44px' : '36px'};
    padding: ${props => props.$large ? '10px' : '6px'};
  }
`

const VolumeControl = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;

  @media (max-width: 768px) {
    gap: 6px;
  }
`

const VolumeSlider = styled.input`
  width: 80px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  outline: none;
  border-radius: 2px;
  cursor: pointer;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: white;
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid #e50914;
  }

  &::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: white;
    border-radius: 50%;
    cursor: pointer;
    border: 2px solid #e50914;
  }

  @media (max-width: 768px) {
    width: 60px;
  }
`

const TimeDisplay = styled.div`
  color: white;
  font-size: 14px;
  font-weight: 500;
  min-width: 100px;
  text-align: right;

  @media (max-width: 768px) {
    font-size: 12px;
    min-width: 80px;
  }
`

const SubtitleDisplay = styled.div`
  position: absolute;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  max-width: 90%;
  pointer-events: none;
  z-index: 5;

  @media (max-width: 768px) {
    bottom: 100px;
    max-width: 95%;
  }
`

const SubtitleText = styled.div`
  background: rgba(0, 0, 0, 0.9);
  padding: 12px 24px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
  display: inline-block;
  border: 1px solid rgba(255, 255, 255, 0.1);

  @media (max-width: 768px) {
    padding: 8px 16px;
  }
`

// SubtitleLabel removed - labels are no longer shown as it's obvious which language is which
// const SubtitleLabel = styled.span`
//   display: block;
//   font-size: 12px;
//   letter-spacing: 0.12em;
//   text-transform: uppercase;
//   margin-bottom: 4px;
//   color: rgba(248, 250, 252, 0.65);
//
//   @media (max-width: 768px) {
//     font-size: 10px;
//     margin-bottom: 2px;
//   }
// `

const OriginalSubtitle = styled.div`
  color: #ffd700;
  font-size: 20px;
  line-height: 1.4;
  font-weight: 600;
  margin-bottom: 8px;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);

  @media (max-width: 768px) {
    font-size: 16px;
    margin-bottom: 6px;
  }
`

const TranslatedSubtitle = styled.div`
  color: #ffffff;
  font-size: 16px;
  line-height: 1.3;
  opacity: 0.9;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);

  @media (max-width: 768px) {
    font-size: 14px;
  }
`

const SettingsMenu = styled.div<{ $visible: boolean }>`
  position: absolute;
  bottom: 60px;
  right: 24px;
  background: rgba(0, 0, 0, 0.95);
  border-radius: 8px;
  padding: 16px;
  min-width: 200px;
  opacity: ${props => props.$visible ? 1 : 0};
  transform: ${props => props.$visible ? 'translateY(0)' : 'translateY(10px)'};
  transition: all 0.2s ease;
  pointer-events: ${props => props.$visible ? 'auto' : 'none'};
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 20;

  @media (max-width: 768px) {
    right: 16px;
    min-width: 180px;
  }
`

const MenuSection = styled.div`
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }
`

const MenuLabel = styled.div`
  color: #b3b3b3;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
  text-transform: uppercase;
`

const MenuButton = styled.button<{ $active?: boolean }>`
  width: 100%;
  background: ${props => props.$active ? 'rgba(229, 9, 20, 0.2)' : 'transparent'};
  border: none;
  color: ${props => props.$active ? '#e50914' : 'white'};
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }
`

const CompletionOverlay = styled.div`
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: white;
  z-index: 100;
  backdrop-filter: blur(10px);
`

const CompletionContent = styled.div`
  text-align: center;
  max-width: 500px;
  padding: 20px;

  @media (max-width: 768px) {
    padding: 16px;
    max-width: 90%;
  }
`

const CompletionTitle = styled.h2`
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 16px;

  @media (max-width: 768px) {
    font-size: 24px;
  }
`

const CompletionMessage = styled.p`
  font-size: 18px;
  color: #b3b3b3;
  margin-bottom: 32px;
  line-height: 1.5;

  @media (max-width: 768px) {
    font-size: 16px;
    margin-bottom: 24px;
  }
`

const ContinueButton = styled.button`
  background: #e50914;
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #f40612;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(229, 9, 20, 0.3);
  }

  &:active {
    transform: translateY(0);
  }

  @media (max-width: 768px) {
    padding: 12px 24px;
    font-size: 15px;
  }
`

// Types
interface SubtitleEntry {
  start: number
  end: number
  text: string
  translation?: string
}

interface ChunkedLearningPlayerProps {
  videoPath: string
  series: string
  episode: string
  subtitlePath?: string
  translationPath?: string
  translationIndices?: number[]  // Indices of subtitles that still need translation
  startTime: number
  endTime: number
  onComplete: () => void
  onSkipChunk?: () => void
  onBack?: () => void
  learnedWords?: string[]
  chunkInfo?: {
    current: number
    total: number
    duration: string
  }
  targetLanguage?: { code: string; name: string }
  nativeLanguage?: { code: string; name: string }
}

type PlaybackSpeed = 0.5 | 0.75 | 1 | 1.25 | 1.5 | 2
type SubtitleMode = 'off' | 'original' | 'translation' | 'both'

export const ChunkedLearningPlayer: React.FC<ChunkedLearningPlayerProps> = ({
  videoPath: _videoPath,
  series,
  episode,
  subtitlePath,
  translationPath,
  translationIndices,
  startTime,
  endTime,
  onComplete,
  onSkipChunk,
  onBack,
  learnedWords = [],
  chunkInfo,
  targetLanguage,
  nativeLanguage,
}) => {
  // Refs
  const playerRef = useRef<ReactPlayer>(null)
  const controlsTimeoutRef = useRef<NodeJS.Timeout>()
  const containerRef = useRef<HTMLDivElement>(null)

  // Core player state
  const [playing, setPlaying] = useState(false)
  const [volume, setVolume] = useState(1)
  const [muted, setMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(startTime)
  const [playbackRate, setPlaybackRate] = useState<PlaybackSpeed>(1)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // UI state
  const [showControls, setShowControls] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [showCompletion, setShowCompletion] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // Subtitle state
  const [subtitleMode, setSubtitleMode] = useState<SubtitleMode>('original')
  const [currentSubtitle, setCurrentSubtitle] = useState<{ original: string; translation: string }>({
    original: '',
    translation: ''
  })
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>([])
  const [translations, setTranslations] = useState<SubtitleEntry[]>([])

  // Log to check what languages are being passed
  useEffect(() => {
    if (targetLanguage || nativeLanguage) {
      console.log('ChunkedLearningPlayer languages:', {
        targetLanguage,
        nativeLanguage,
      })
    }
  }, [targetLanguage, nativeLanguage])

  // Debug language preferences
  console.log('[ChunkedLearningPlayer] Language props:', {
    targetLanguage,
    nativeLanguage,
  })

  const targetLanguageName = targetLanguage?.name || 'German'
  const nativeLanguageName = nativeLanguage?.name || 'Spanish'

  console.log('[ChunkedLearningPlayer] Language names:', {
    targetLanguageName,
    nativeLanguageName,
  })
  const subtitleModeLabels: Record<SubtitleMode, string> = {
    off: 'Off',
    original: `${targetLanguageName} Only`,
    translation: `${nativeLanguageName} Only`,
    both: 'Both Languages',
  }
  const isLastChunk = chunkInfo ? chunkInfo.current >= chunkInfo.total : false
  const skipButtonLabel = isLastChunk ? 'Finish Episode' : 'Skip Chunk'
  const subtitleOptions: Array<{ value: SubtitleMode; label: string }> = [
    { value: 'off', label: subtitleModeLabels.off },
    { value: 'original', label: subtitleModeLabels.original },
    { value: 'translation', label: subtitleModeLabels.translation },
    { value: 'both', label: subtitleModeLabels.both },
  ]

  // Calculate progress and duration
  const chunkDuration = endTime - startTime
  const progress = Math.max(0, Math.min(100, ((currentTime - startTime) / chunkDuration) * 100))

  // Format time display
  const formatTime = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }, [])

  // Parse SRT format subtitles
  const parseSRT = useCallback((srtContent: string): SubtitleEntry[] => {
    const entries: SubtitleEntry[] = []
    const blocks = srtContent.trim().split(/\n\s*\n/)

    for (const block of blocks) {
      const lines = block.split('\n')
      if (lines.length >= 3) {
        const timeMatch = lines[1].match(/(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})/)
        if (timeMatch) {
          const start = parseInt(timeMatch[1]) * 3600 + parseInt(timeMatch[2]) * 60 + parseInt(timeMatch[3]) + parseInt(timeMatch[4]) / 1000
          const end = parseInt(timeMatch[5]) * 3600 + parseInt(timeMatch[6]) * 60 + parseInt(timeMatch[7]) + parseInt(timeMatch[8]) / 1000

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
  }, [])

  // Build subtitle URL
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

    const fullSubtitleUrl = subtitleUrl.startsWith('http')
      ? subtitleUrl
      : `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}${subtitleUrl}`

    return fullSubtitleUrl
  }, [series])

  // Auto-hide controls
  const resetControlsTimeout = useCallback(() => {
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current)
    }

    setShowControls(true)

    if (playing && !showSettings) {
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false)
      }, 3000)
    }
  }, [playing, showSettings])

  // Keyboard shortcuts
  const handleKeyPress = useCallback((e: KeyboardEvent) => {
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
      case 'KeyS':
        e.preventDefault()
        setSubtitleMode(prev => {
          const modes: SubtitleMode[] = ['off', 'original', 'translation', 'both']
          const currentIndex = modes.indexOf(prev)
          return modes[(currentIndex + 1) % modes.length]
        })
        break
    }

    resetControlsTimeout()
  }, [currentTime, startTime, endTime, resetControlsTimeout])

  // Fullscreen handling
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return

    if (!isFullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen()
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen()
      }
    }
  }, [isFullscreen])

  // Handle fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  // Mobile detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768)
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Keyboard event listeners
  useEffect(() => {
    document.addEventListener('keydown', handleKeyPress)
    return () => document.removeEventListener('keydown', handleKeyPress)
  }, [handleKeyPress])

  // Mouse move handler
  useEffect(() => {
    const handleMouseMove = () => resetControlsTimeout()

    if (containerRef.current) {
      containerRef.current.addEventListener('mousemove', handleMouseMove)
      return () => {
        if (containerRef.current) {
          containerRef.current.removeEventListener('mousemove', handleMouseMove)
        }
      }
    }
  }, [resetControlsTimeout])

  // Load subtitles
  useEffect(() => {
    logger.info('ChunkedLearningPlayer', 'Loading subtitles...', {
      subtitlePath,
      translationPath,
      translationIndices,
      startTime,
      endTime
    })

    const token = localStorage.getItem('authToken')

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

    // Load target-language subtitles
    if (subtitlePath) {
      const fullSubtitleUrl = buildSubtitleUrl(subtitlePath)

      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      axios.get(fullSubtitleUrl, {
        headers,
        params: { _ts: Date.now() }
      })
        .then(response => {
          const parsedSubs = parseSRT(response.data)
          const normalizedSubs = normalizeEntries(parsedSubs)
          setSubtitles(normalizedSubs)
          logger.info('ChunkedLearningPlayer', `Loaded ${targetLanguageName} subtitles: ${normalizedSubs.length} entries`)
        })
        .catch(error => {
          logger.error('ChunkedLearningPlayer', 'Failed to load subtitles', error)
        })
    } else {
      logger.warn('ChunkedLearningPlayer', 'No subtitle path provided')
    }

    // Load native-language translations
    if (translationPath) {
      const fullTranslationUrl = buildSubtitleUrl(translationPath)

      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      }

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      axios.get(fullTranslationUrl, {
        headers,
        params: { _ts: Date.now() }
      })
        .then(response => {
          const parsedTranslations = parseSRT(response.data)
          const normalizedTranslations = normalizeEntries(parsedTranslations)
          setTranslations(normalizedTranslations)
          logger.info('ChunkedLearningPlayer', `Loaded ${nativeLanguageName} translations: ${normalizedTranslations.length} entries`)
        })
        .catch(error => {
          logger.warn('ChunkedLearningPlayer', 'Failed to load translations', error)
        })
    }
  }, [subtitlePath, translationPath, series, startTime, endTime, buildSubtitleUrl, parseSRT])

  // Auto-play when component mounts
  useEffect(() => {
    if (playerRef.current) {
      playerRef.current.seekTo(startTime)
      setTimeout(() => setPlaying(true), 100)
    }
  }, [startTime])

  // Handle video progress
  const handleProgress = useCallback((state: { playedSeconds: number }) => {
    setCurrentTime(state.playedSeconds)

    const relativeTime = Math.max(0, state.playedSeconds - startTime)
    const clampedTime = Math.min(relativeTime, chunkDuration)

    // Update current subtitles
    const currentSubIndex = subtitles.findIndex(sub =>
      clampedTime >= sub.start && clampedTime <= sub.end
    )
    const currentSub = currentSubIndex >= 0 ? subtitles[currentSubIndex] : null

    const currentTranslation = translations.find(trans =>
      clampedTime >= trans.start && clampedTime <= trans.end
    )

    // Check if this subtitle index needs translation
    // If translationIndices is provided, only show translation for those indices
    // If not provided, show all translations (backward compatibility)
    const shouldShowTranslation = translationIndices
      ? translationIndices.includes(currentSubIndex)
      : true

    // Log when translation filtering is applied
    if (translationIndices && currentSubIndex >= 0) {
      logger.debug('ChunkedLearningPlayer', 'Translation filtering', {
        subtitleIndex: currentSubIndex,
        shouldShowTranslation,
        translationIndices: translationIndices.slice(0, 5) // Log first 5 for brevity
      })
    }

    const translationText = shouldShowTranslation && currentTranslation
      ? (currentTranslation.translation && currentTranslation.translation.trim().length > 0
        ? currentTranslation.translation
        : currentTranslation.text || '')
      : ''

    setCurrentSubtitle({
      original: currentSub?.text || '',
      translation: translationText
    })

    // Check if chunk is complete
    if (state.playedSeconds >= endTime && !showCompletion) {
      setPlaying(false)
      setShowCompletion(true)
    }
  }, [subtitles, translations, translationIndices, endTime, showCompletion, startTime, chunkDuration])

  // Handle seeking
  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const bounds = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - bounds.left
    const percentage = x / bounds.width
    const seekTime = startTime + (chunkDuration * percentage)

    if (playerRef.current) {
      playerRef.current.seekTo(seekTime)
      setCurrentTime(seekTime)
    }
  }, [startTime, chunkDuration])

  // Render subtitles based on mode
  const renderSubtitles = () => {
    if (subtitleMode === 'off') return null

    const showOriginal = subtitleMode === 'original' || subtitleMode === 'both'
    const showTranslation = subtitleMode === 'translation' || subtitleMode === 'both'

    if (!showOriginal && !showTranslation) return null
    if (!currentSubtitle.original && !currentSubtitle.translation) return null

    return (
      <SubtitleDisplay>
        <SubtitleText>
          {showOriginal && currentSubtitle.original && (
            <OriginalSubtitle>
              {currentSubtitle.original}
            </OriginalSubtitle>
          )}
          {showTranslation && currentSubtitle.translation && (
            <TranslatedSubtitle>
              {currentSubtitle.translation}
            </TranslatedSubtitle>
          )}
        </SubtitleText>
      </SubtitleDisplay>
    )
  }

  // Video URL
  const videoUrl = buildVideoStreamUrl(
    series,
    episode
  )

  const handleSkip = useCallback(() => {
    setPlaying(false)
    setShowCompletion(false)
    if (onSkipChunk) {
      onSkipChunk()
    } else {
      onComplete()
    }
  }, [onSkipChunk, onComplete])

  return (
    <PlayerContainer ref={containerRef}>
      <VideoWrapper
        className={`${showControls ? 'show-cursor' : ''} ${isFullscreen ? 'fullscreen' : ''}`}
        onClick={resetControlsTimeout}
      >
        <ReactPlayer
          ref={playerRef}
          url={videoUrl}
          width="100%"
          height="100%"
          playing={playing}
          volume={volume}
          muted={muted}
          playbackRate={playbackRate}
          controls={false}
          onProgress={handleProgress}
          progressInterval={100}
        />

        {onBack && (
          <StickyNavContainer>
            <StickyBackButton onClick={onBack}>
              <ArrowLeftIcon className="w-5 h-5" />
              <span>Back to Episodes</span>
            </StickyBackButton>
          </StickyNavContainer>
        )}

        <ControlsOverlay $visible={showControls} $mobile={isMobile}>
          <TopControls>
            <TopLeftControls>
              {chunkInfo && (
                <ChunkInfo>
                  <ChunkLabel>Playing Chunk</ChunkLabel>
                  <ChunkDetails>
                    {chunkInfo.current} of {chunkInfo.total} • {chunkInfo.duration}
                  </ChunkDetails>
                </ChunkInfo>
              )}
            </TopLeftControls>

            <PlayerControls>
              {learnedWords.length > 0 && (
                <LearnedWordsBadge>
                  <CheckCircleIcon className="w-4 h-4" />
                  <span>{learnedWords.length} learned</span>
                </LearnedWordsBadge>
              )}

              <ControlButton onClick={() => setShowSettings(!showSettings)}>
                ⚙️
              </ControlButton>
            </PlayerControls>
          </TopControls>

          {renderSubtitles()}

          <BottomControls>
            <ProgressContainer>
              <ProgressBar onClick={handleSeek}>
                <ProgressFill $progress={progress} />
              </ProgressBar>
            </ProgressContainer>

            <ControlsRow>
              <LeftControls>
                <ControlButton $large onClick={() => setPlaying(!playing)}>
                  {playing ? (
                    <PauseIcon className="w-6 h-6" />
                  ) : (
                    <PlayIcon className="w-6 h-6" />
                  )}
                </ControlButton>

                <VolumeControl>
                  <ControlButton onClick={() => setMuted(!muted)}>
                    {muted ? (
                      <SpeakerXMarkIcon className="w-5 h-5" />
                    ) : (
                      <SpeakerWaveIcon className="w-5 h-5" />
                    )}
                  </ControlButton>
                  {!isMobile && (
                    <VolumeSlider
                      type="range"
                      min={0}
                      max={1}
                      step={0.1}
                      value={volume}
                      onChange={(e) => setVolume(parseFloat(e.target.value))}
                    />
                  )}
                </VolumeControl>

                <TimeDisplay>
                  {formatTime(currentTime - startTime)} / {formatTime(chunkDuration)}
                </TimeDisplay>
              </LeftControls>

              <RightControls>
                <ControlButton
                  onClick={handleSkip}
                  title={skipButtonLabel}
                >
                  <ForwardIcon className="w-5 h-5" />
                  <span>{skipButtonLabel}</span>
                </ControlButton>

                <ControlButton
                  onClick={() => {
                    const modes: SubtitleMode[] = ['off', 'original', 'translation', 'both']
                    const currentIndex = modes.indexOf(subtitleMode)
                    setSubtitleMode(modes[(currentIndex + 1) % modes.length])
                  }}
                  title={`Subtitles: ${subtitleModeLabels[subtitleMode]}`}
                >
                  {subtitleMode === 'off' ? (
                    <EyeSlashIcon className="w-5 h-5" />
                  ) : (
                    <LanguageIcon className="w-5 h-5" />
                  )}
                </ControlButton>

                <ControlButton onClick={toggleFullscreen}>
                  {isFullscreen ? (
                    <MinusIcon className="w-5 h-5" />
                  ) : (
                    <PlusIcon className="w-5 h-5" />
                  )}
                </ControlButton>
              </RightControls>
            </ControlsRow>
          </BottomControls>
        </ControlsOverlay>

        <SettingsMenu $visible={showSettings}>
          <MenuSection>
            <MenuLabel>Playback Speed</MenuLabel>
            {([0.5, 0.75, 1, 1.25, 1.5, 2] as PlaybackSpeed[]).map(speed => (
              <MenuButton
                key={speed}
                $active={playbackRate === speed}
                onClick={() => setPlaybackRate(speed)}
              >
                {speed}x {speed === 1 && '(Normal)'}
              </MenuButton>
            ))}
          </MenuSection>

          <MenuSection>
            <MenuLabel>Subtitles</MenuLabel>
            {subtitleOptions.map(option => (
              <MenuButton
                key={option.value}
                $active={subtitleMode === option.value}
                onClick={() => setSubtitleMode(option.value)}
              >
                {option.label}
              </MenuButton>
            ))}
          </MenuSection>
        </SettingsMenu>

        {showCompletion && (
          <CompletionOverlay>
            <CompletionContent>
              <CompletionTitle>Chunk Complete! 🎉</CompletionTitle>
              <CompletionMessage>
                Excellent work! You&apos;ve completed this segment and learned {learnedWords.length} new words.
                {chunkInfo && chunkInfo.current < chunkInfo.total && (
                  <> Ready for the next chunk?</>
                )}
              </CompletionMessage>
              <ContinueButton onClick={onComplete}>
                {chunkInfo && chunkInfo.current < chunkInfo.total
                  ? 'Continue to Next Chunk'
                  : 'Complete Episode'
                }
              </ContinueButton>
            </CompletionContent>
          </CompletionOverlay>
        )}
      </VideoWrapper>
    </PlayerContainer>
  )
}
