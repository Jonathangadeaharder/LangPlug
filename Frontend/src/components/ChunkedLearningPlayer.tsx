import React, { useState, useEffect, useRef } from 'react'
import styled from 'styled-components'
import ReactPlayer from 'react-player'
import { 
  PlayIcon, 
  PauseIcon, 
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  CheckCircleIcon
} from '@heroicons/react/24/solid'
import axios from 'axios'
import { videoService } from '@/services/api'
import { logger } from '@/services/logger'

const PlayerContainer = styled.div`
  background: #000;
  min-height: 100vh;
  position: relative;
`

const VideoWrapper = styled.div`
  position: relative;
  width: 100%;
  height: 100vh;
  background: #000;
`

const ControlsOverlay = styled.div<{ $visible: boolean }>`
  position: absolute;
  inset: 0;
  background: linear-gradient(
    transparent 0%,
    rgba(0, 0, 0, 0.3) 70%,
    rgba(0, 0, 0, 0.8) 100%
  );
  opacity: ${props => props.$visible ? 1 : 0};
  transition: opacity 0.3s ease;
  pointer-events: ${props => props.$visible ? 'auto' : 'none'};
`

const TopControls = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
`

const ChunkInfo = styled.div`
  background: rgba(0, 0, 0, 0.7);
  border-radius: 8px;
  padding: 12px 20px;
  color: white;
`

const ChunkLabel = styled.div`
  font-size: 14px;
  color: #b3b3b3;
  margin-bottom: 4px;
`

const ChunkDetails = styled.div`
  font-size: 18px;
  font-weight: 500;
`

const LearnedWordsBadge = styled.div`
  background: rgba(70, 211, 105, 0.2);
  border: 1px solid #46d369;
  color: #46d369;
  border-radius: 8px;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
`

const BottomControls = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24px;
`

const ProgressBar = styled.div`
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  margin-bottom: 16px;
  cursor: pointer;
`

const ProgressFill = styled.div<{ $progress: number }>`
  width: ${props => props.$progress}%;
  height: 100%;
  background: #e50914;
  border-radius: 2px;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: -4px;
    width: 12px;
    height: 12px;
    background: white;
    border-radius: 50%;
    transform: translateX(50%);
  }
`

const ControlButtons = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`

const ControlButton = styled.button`
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background 0.2s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

const VolumeControl = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`

const VolumeSlider = styled.input`
  width: 100px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  outline: none;
  border-radius: 2px;
  cursor: pointer;
  
  &::-webkit-slider-thumb {
    appearance: none;
    width: 12px;
    height: 12px;
    background: white;
    border-radius: 50%;
    cursor: pointer;
  }
`

const TimeDisplay = styled.div`
  color: white;
  font-size: 14px;
  margin-left: auto;
`

const SubtitleDisplay = styled.div`
  position: absolute;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  max-width: 80%;
  pointer-events: none;
`

const SubtitleText = styled.div`
  background: rgba(0, 0, 0, 0.85);
  padding: 12px 24px;
  border-radius: 8px;
  backdrop-filter: blur(10px);
  display: inline-block;
`

const OriginalSubtitle = styled.div`
  color: #ffd700;
  font-size: 22px;
  line-height: 1.4;
  font-weight: 500;
  margin-bottom: 8px;
`

const TranslatedSubtitle = styled.div`
  color: #ffffff;
  font-size: 18px;
  line-height: 1.3;
  opacity: 0.9;
`

const CompletionOverlay = styled.div`
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: white;
  z-index: 100;
`

const CompletionContent = styled.div`
  text-align: center;
  max-width: 500px;
`

const CompletionTitle = styled.h2`
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 16px;
`

const CompletionMessage = styled.p`
  font-size: 18px;
  color: #b3b3b3;
  margin-bottom: 32px;
`

const ContinueButton = styled.button`
  background: #e50914;
  color: white;
  border: none;
  padding: 12px 32px;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  
  &:hover {
    background: #f40612;
  }
`

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
  startTime: number
  endTime: number
  onComplete: () => void
  learnedWords?: string[]
  chunkInfo?: {
    current: number
    total: number
    duration: string
  }
}

export const ChunkedLearningPlayer: React.FC<ChunkedLearningPlayerProps> = ({
  videoPath,
  series,
  episode,
  subtitlePath,
  translationPath,
  startTime,
  endTime,
  onComplete,
  learnedWords = [],
  chunkInfo
}) => {
  const playerRef = useRef<ReactPlayer>(null)
  const [playing, setPlaying] = useState(false)
  const [volume, setVolume] = useState(1)
  const [muted, setMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(startTime)
  const [showControls, setShowControls] = useState(true)
  const [showCompletion, setShowCompletion] = useState(false)
  const [currentSubtitle, setCurrentSubtitle] = useState<{ original: string; translation: string }>({ original: '', translation: '' })
  const [subtitles, setSubtitles] = useState<SubtitleEntry[]>([])
  const [translations, setTranslations] = useState<SubtitleEntry[]>([])
  const controlsTimeoutRef = useRef<NodeJS.Timeout>()

  // Calculate duration of this chunk
  const chunkDuration = endTime - startTime
  const progress = ((currentTime - startTime) / chunkDuration) * 100

  // Format time display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Parse SRT format subtitles
  const parseSRT = (srtContent: string): SubtitleEntry[] => {
    const entries: SubtitleEntry[] = []
    const blocks = srtContent.trim().split(/\n\s*\n/)
    
    for (const block of blocks) {
      const lines = block.split('\n')
      if (lines.length >= 3) {
        const timeMatch = lines[1].match(/(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})/)
        if (timeMatch) {
          const start = parseInt(timeMatch[1]) * 3600 + parseInt(timeMatch[2]) * 60 + parseInt(timeMatch[3]) + parseInt(timeMatch[4]) / 1000
          const end = parseInt(timeMatch[5]) * 3600 + parseInt(timeMatch[6]) * 60 + parseInt(timeMatch[7]) + parseInt(timeMatch[8]) / 1000
          
          // Join remaining lines as subtitle text
          const textLines = lines.slice(2)
          let originalText = ''
          let translation = ''
          
          // Check if this is a dual-language subtitle (original | translation)
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

  // Helper function to build subtitle URL
  const buildSubtitleUrl = (path: string): string => {
    let subtitleUrl = ''
    if (path.includes('\\') || path.includes(':')) {
      // This is a Windows absolute path - extract series and filename
      const pathParts = path.replace(/\\/g, '/').split('/')
      const videosIndex = pathParts.findIndex(p => p.toLowerCase() === 'videos')
      if (videosIndex !== -1 && videosIndex < pathParts.length - 1) {
        const relativePath = pathParts.slice(videosIndex + 1).join('/')
        subtitleUrl = `/api/videos/subtitles/${encodeURIComponent(relativePath)}`
      } else {
        // Fallback: try to construct from series
        const filename = pathParts[pathParts.length - 1]
        subtitleUrl = `/api/videos/subtitles/${encodeURIComponent(`${series}/${filename}`)}`
      }
    } else {
      // Already a relative path
      subtitleUrl = `/api/videos/subtitles/${encodeURIComponent(path)}`
    }
    
    // Use backend URL with token
    const fullSubtitleUrl = subtitleUrl.startsWith('http') 
      ? subtitleUrl 
      : `${import.meta.env.VITE_API_BASE_URL || 'http://172.30.96.1:8000'}${subtitleUrl.replace('/api', '')}`
    
    return fullSubtitleUrl
  }

  // Load subtitles and translations
  useEffect(() => {
    logger.info('ChunkedLearningPlayer', 'Loading subtitles...', {
      subtitlePath,
      translationPath,
      startTime,
      endTime
    })
    
    const token = localStorage.getItem('authToken')
    
    // Load main subtitles (German transcription)
    if (subtitlePath) {
      logger.info('ChunkedLearningPlayer', 'Building subtitle URL for:', subtitlePath)
      const fullSubtitleUrl = buildSubtitleUrl(subtitlePath)
      logger.info('ChunkedLearningPlayer', 'Full subtitle URL:', fullSubtitleUrl)
      
      axios.get(fullSubtitleUrl, {
        params: token ? { token, _ts: Date.now() } : { _ts: Date.now() }
      })
        .then(response => {
          logger.info('ChunkedLearningPlayer', `Subtitle response received, length: ${response.data.length}`)
          const parsedSubs = parseSRT(response.data)
          logger.info('ChunkedLearningPlayer', `Parsed subtitles before filtering: ${parsedSubs.length}`)
          // Filter subtitles for this chunk
          const chunkSubs = parsedSubs.filter(sub => 
            sub.start >= startTime && sub.end <= endTime
          )
          setSubtitles(chunkSubs)
          logger.info('ChunkedLearningPlayer', `Loaded German subtitles: ${chunkSubs.length} entries`)
        })
        .catch(error => {
          logger.error('ChunkedLearningPlayer', 'Failed to load subtitles', error)
        })
    } else {
      logger.warn('ChunkedLearningPlayer', 'No subtitle path provided')
    }
    
    // Load translations (English translation for difficult segments)
    if (translationPath) {
      const fullTranslationUrl = buildSubtitleUrl(translationPath)
      
      axios.get(fullTranslationUrl, {
        params: token ? { token, _ts: Date.now() } : { _ts: Date.now() }
      })
        .then(response => {
          const parsedTranslations = parseSRT(response.data)
          // Filter translations for this chunk
          const chunkTranslations = parsedTranslations.filter(trans => 
            trans.start >= startTime && trans.end <= endTime
          )
          setTranslations(chunkTranslations)
          console.log('[ChunkedLearningPlayer] Loaded English translations:', chunkTranslations.length, 'entries')
        })
        .catch(error => {
          console.error('Failed to load translations:', error)
          // Translation file is optional, so don't show error to user
        })
    }
  }, [subtitlePath, translationPath, series, startTime, endTime])

  // Auto-hide controls
  useEffect(() => {
    const handleMouseMove = () => {
      setShowControls(true)
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current)
      }
      controlsTimeoutRef.current = setTimeout(() => {
        if (playing) {
          setShowControls(false)
        }
      }, 3000)
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current)
      }
    }
  }, [playing])

  // Start playing when component mounts
  useEffect(() => {
    if (playerRef.current) {
      playerRef.current.seekTo(startTime)
      setPlaying(true)
    }
  }, [startTime])

  // Handle video progress
  const handleProgress = (state: { playedSeconds: number }) => {
    setCurrentTime(state.playedSeconds)
    
    // Update current subtitle based on playback time
    // Find current German subtitle (always shown)
    const currentSub = subtitles.find(sub => 
      state.playedSeconds >= sub.start && state.playedSeconds <= sub.end
    )
    
    // Find current English translation (only shown when available)
    const currentTranslation = translations.find(trans => 
      state.playedSeconds >= trans.start && state.playedSeconds <= trans.end
    )
    
    setCurrentSubtitle({
      original: currentSub?.text || '',
      translation: currentTranslation?.text || ''
    })
    
    // Check if we've reached the end of the chunk
    if (state.playedSeconds >= endTime && !showCompletion) {
      setPlaying(false)
      setShowCompletion(true)
    }
  }

  // Handle seeking
  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const bounds = e.currentTarget.getBoundingClientRect()
    const x = e.clientX - bounds.left
    const percentage = x / bounds.width
    const seekTime = startTime + (chunkDuration * percentage)
    
    if (playerRef.current) {
      playerRef.current.seekTo(seekTime)
      setCurrentTime(seekTime)
    }
  }

  // Handle continue to next chunk
  const handleContinue = () => {
    onComplete()
  }

  // Construct video URL from backend API
  // Pass the full episode title as the backend matches by checking if it's in the filename
  const videoUrl = videoService.getVideoStreamUrl(series, episode)

  return (
    <PlayerContainer>
      <VideoWrapper>
        <ReactPlayer
          ref={playerRef}
          url={videoUrl}
          width="100%"
          height="100%"
          playing={playing}
          volume={volume}
          muted={muted}
          controls={false}
          onProgress={handleProgress}
          progressInterval={100}
        />

        <ControlsOverlay $visible={true}>
          <TopControls>
            {chunkInfo && (
              <ChunkInfo>
                <ChunkLabel>Playing Chunk</ChunkLabel>
                <ChunkDetails>
                  {chunkInfo.current} of {chunkInfo.total} • {chunkInfo.duration}
                </ChunkDetails>
              </ChunkInfo>
            )}
            
            {learnedWords.length > 0 && (
              <LearnedWordsBadge>
                <CheckCircleIcon className="w-5 h-5" />
                <span>{learnedWords.length} words learned</span>
              </LearnedWordsBadge>
            )}
          </TopControls>

          <BottomControls>
            {(currentSubtitle.original || currentSubtitle.translation) && (
              <SubtitleDisplay>
                <SubtitleText>
                  {currentSubtitle.original && (
                    <OriginalSubtitle>{currentSubtitle.original}</OriginalSubtitle>
                  )}
                  {currentSubtitle.translation && (
                    <TranslatedSubtitle>{currentSubtitle.translation}</TranslatedSubtitle>
                  )}
                </SubtitleText>
              </SubtitleDisplay>
            )}

            <ProgressBar onClick={handleSeek}>
              <ProgressFill $progress={progress} />
            </ProgressBar>

            <ControlButtons>
              <ControlButton onClick={() => setPlaying(!playing)}>
                {playing ? (
                  <PauseIcon className="w-6 h-6" />
                ) : (
                  <PlayIcon className="w-6 h-6" />
                )}
              </ControlButton>

              <VolumeControl>
                <ControlButton onClick={() => setMuted(!muted)}>
                  {muted ? (
                    <SpeakerXMarkIcon className="w-6 h-6" />
                  ) : (
                    <SpeakerWaveIcon className="w-6 h-6" />
                  )}
                </ControlButton>
                <VolumeSlider
                  type="range"
                  min={0}
                  max={1}
                  step={0.1}
                  value={volume}
                  onChange={(e) => setVolume(parseFloat(e.target.value))}
                />
              </VolumeControl>

              <TimeDisplay>
                {formatTime(currentTime - startTime)} / {formatTime(chunkDuration)}
              </TimeDisplay>
            </ControlButtons>
          </BottomControls>
        </ControlsOverlay>

        {showCompletion && (
          <CompletionOverlay>
            <CompletionContent>
              <CompletionTitle>Chunk Complete! 🎉</CompletionTitle>
              <CompletionMessage>
                Great job! You've completed this segment and learned {learnedWords.length} new words.
                {chunkInfo && chunkInfo.current < chunkInfo.total && (
                  <> Ready for the next chunk?</>
                )}
              </CompletionMessage>
              <ContinueButton onClick={handleContinue}>
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