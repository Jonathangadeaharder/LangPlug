import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import styled from 'styled-components'
import ReactPlayer from 'react-player'
import {
  PlayIcon,
  PauseIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ArrowLeftIcon,
  ForwardIcon,
  LanguageIcon
} from '@heroicons/react/24/solid'
import { toast } from 'react-hot-toast'
import { Container, NetflixButton } from '@/styles/GlobalStyles'
import { VocabularyGame } from './VocabularyGame'
import { buildVideoStreamUrl, handleApiError } from '@/services/api'
import { getBlockingWordsApiVocabularyBlockingWordsGet } from '@/client/services.gen'
import { useGameStore } from '@/store/useGameStore'
import type { VideoInfo, VocabularyWord } from '@/types'

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
  padding: 20px;
  background: linear-gradient(
    rgba(0, 0, 0, 0.8) 0%,
    transparent 100%
  );
  display: flex;
  align-items: center;
  gap: 16px;
`

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: rgba(0, 0, 0, 0.9);
  }
`

const VideoTitle = styled.h1`
  font-size: 24px;
  font-weight: bold;
  color: white;
  flex: 1;
`

const SegmentInfo = styled.div`
  color: #b3b3b3;
  font-size: 14px;
  text-align: right;
`

const BottomControls = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
`

const ProgressSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

const ProgressBar = styled.div`
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
`

const ProgressFill = styled.div<{ $progress: number }>`
  height: 100%;
  background: #e50914;
  border-radius: 2px;
  width: ${props => props.$progress}%;
  transition: width 0.1s ease;
`

const TimeInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #b3b3b3;
`

const SegmentProgress = styled.div`
  text-align: center;
  color: white;
`

const Controls = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`

const PlayControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`

const ControlButton = styled.button`
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: scale(1.1);
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
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  outline: none;
  cursor: pointer;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 12px;
    height: 12px;
    background: #e50914;
    border-radius: 50%;
    cursor: pointer;
  }
`

const RightControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`

const SubtitleToggle = styled(NetflixButton)<{ $mode: string }>`
  padding: 8px 16px;
  font-size: 14px;
  background: ${props => props.$mode !== 'OFF' ? '#e50914' : 'rgba(255, 255, 255, 0.2)'};
  min-width: 80px;

  &:hover {
    background: ${props => props.$mode !== 'OFF' ? '#f40612' : 'rgba(255, 255, 255, 0.3)'};
  }
`

const NextSegmentButton = styled(NetflixButton)`
  padding: 8px 16px;
  font-size: 14px;
`

const FileInput = styled.input`
  display: none;
`

const SubtitleDisplay = styled.div`
  position: absolute;
  bottom: 150px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 80%;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
`

const SubtitleLine = styled.div<{ $language: 'DE' | 'ES' | 'UPLOAD' }>`
  background: rgba(0, 0, 0, 0.85);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 500;
  border-left: 4px solid ${props => {
    switch (props.$language) {
      case 'DE': return '#ffd700'; // Gold for German
      case 'ES': return '#00ff88'; // Green for Spanish/English
      case 'UPLOAD': return '#ff6b35'; // Orange for uploaded
      default: return '#ffffff';
    }
  }};
  color: ${props => {
    switch (props.$language) {
      case 'DE': return '#ffd700';
      case 'ES': return '#00ff88';
      case 'UPLOAD': return '#ff6b35';
      default: return '#ffffff';
    }
  }};
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
`

const LoadingOverlay = styled.div`
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  color: white;
  z-index: 10;
`

export const LearningPlayer: React.FC = () => {
  const { series, episode } = useParams<{ series: string; episode: string }>()
  const location = useLocation()
  const navigate = useNavigate()

  const videoInfo = location.state?.videoInfo as VideoInfo

  // Player state
  const [playing, setPlaying] = useState(false)
  const [volume, setVolume] = useState(1)
  const [muted, setMuted] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [controlsVisible, setControlsVisible] = useState(true)
  const [loading, setLoading] = useState(false)

  // Learning state
  const [currentSegment, setCurrentSegment] = useState(0)
  const [segmentWords, setSegmentWords] = useState<VocabularyWord[]>([])
  const [showVocabularyGame, setShowVocabularyGame] = useState(false)
  const [segmentComplete, setSegmentComplete] = useState(false)

  // Subtitle system state
  type SubtitleMode = 'OFF' | 'DE' | 'ES' | 'DE+ES' | 'UPLOAD'
  const [subtitleMode, setSubtitleMode] = useState<SubtitleMode>('OFF')
  const [uploadedSubtitles, setUploadedSubtitles] = useState<Array<{start: number, end: number, text: string}>>([])
  const [currentUploadedSubtitle, setCurrentUploadedSubtitle] = useState('')
  const [originalSubtitles, setOriginalSubtitles] = useState<Array<{start: number, end: number, text: string}>>([])
  const [currentOriginalSubtitle, setCurrentOriginalSubtitle] = useState('')
  const [translatedSubtitles, setTranslatedSubtitles] = useState<Array<{start: number, end: number, text: string}>>([])
  const [currentTranslatedSubtitle, setCurrentTranslatedSubtitle] = useState('')

  const { showSubtitles, toggleSubtitles, markWordKnown } = useGameStore()
  const playerRef = useRef<ReactPlayer>(null)
  const controlsTimeoutRef = useRef<NodeJS.Timeout>()

  const SEGMENT_DURATION = 300 // 5 minutes

  useEffect(() => {
    if (!videoInfo) {
      navigate('/')
      return
    }

    // Start with vocabulary check for first segment
    loadSegmentWords(0)
  }, [videoInfo, navigate])

  useEffect(() => {
    // Hide controls after 3 seconds of inactivity
    if (controlsVisible && playing) {
      controlsTimeoutRef.current = setTimeout(() => {
        setControlsVisible(false)
      }, 3000)
    }

    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current)
      }
    }
  }, [controlsVisible, playing])

  const loadSegmentWords = async (segmentIndex: number) => {
    if (!videoInfo) return

    setLoading(true)
    try {
      const blockingWordsResponse = await getBlockingWordsApiVocabularyBlockingWordsGet({
        videoPath: videoInfo.path,
      }) as { blocking_words?: VocabularyWord[] } | VocabularyWord[]

      const words = Array.isArray(blockingWordsResponse)
        ? blockingWordsResponse
        : blockingWordsResponse?.blocking_words ?? []

      setSegmentWords(words)
      setShowVocabularyGame(words.length > 0)
    } catch (error) {
      handleApiError(error, 'LearningPlayer.handleError')
      toast.error('Failed to load vocabulary words')
    } finally {
      setLoading(false)
    }
  }

  const handleProgress = (state: { played: number; playedSeconds: number }) => {
    setProgress(state.played * 100)
    setCurrentTime(state.playedSeconds)

    // Update subtitles based on mode
    if (subtitleMode === 'UPLOAD' && uploadedSubtitles.length > 0) {
      const currentSub = uploadedSubtitles.find(sub =>
        state.playedSeconds >= sub.start && state.playedSeconds <= sub.end
      )
      setCurrentUploadedSubtitle(currentSub?.text || '')
    }

    if ((subtitleMode === 'DE' || subtitleMode === 'DE+ES') && originalSubtitles.length > 0) {
      const currentSub = originalSubtitles.find(sub =>
        state.playedSeconds >= sub.start && state.playedSeconds <= sub.end
      )
      setCurrentOriginalSubtitle(currentSub?.text || '')
    }

    if ((subtitleMode === 'ES' || subtitleMode === 'DE+ES') && translatedSubtitles.length > 0) {
      const currentSub = translatedSubtitles.find(sub =>
        state.playedSeconds >= sub.start && state.playedSeconds <= sub.end
      )
      setCurrentTranslatedSubtitle(currentSub?.text || '')
    }

    // Check if we've completed the current 5-minute segment
    const segmentEnd = (currentSegment + 1) * SEGMENT_DURATION
    if (state.playedSeconds >= segmentEnd && !segmentComplete) {
      setPlaying(false)
      setSegmentComplete(true)

      // Load words for next segment
      setTimeout(() => {
        const nextSegment = currentSegment + 1
        setCurrentSegment(nextSegment)
        setSegmentComplete(false)
        loadSegmentWords(nextSegment)
      }, 1000)
    }
  }

  const handleVocabularyComplete = () => {
    setShowVocabularyGame(false)
    setPlaying(true)

    // Seek to the start of current segment
    const seekTime = currentSegment * SEGMENT_DURATION
    if (playerRef.current) {
      playerRef.current.seekTo(seekTime, 'seconds')
    }
  }

  const handleWordAnswered = async (word: string, known: boolean) => {
    try {
      await markWordKnown(word, known)
    } catch (error) {
      throw error // Re-throw to let VocabularyGame handle it
    }
  }

  const handleSkipVocabulary = () => {
    setShowVocabularyGame(false)
    setPlaying(true)

    const seekTime = currentSegment * SEGMENT_DURATION
    if (playerRef.current) {
      playerRef.current.seekTo(seekTime, 'seconds')
    }
  }

  const handlePlayPause = () => {
    setPlaying(!playing)
    setControlsVisible(true)
  }

  const handleMouseMove = () => {
    setControlsVisible(true)
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current)
    }
  }

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const bounds = e.currentTarget.getBoundingClientRect()
    const clickX = e.clientX - bounds.left
    const percentage = clickX / bounds.width
    const seekTime = percentage * duration

    if (playerRef.current) {
      playerRef.current.seekTo(seekTime, 'seconds')
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const parseSRT = (srtContent: string) => {
    const subtitles: Array<{start: number, end: number, text: string}> = []
    const blocks = srtContent.trim().split(/\n\s*\n/)

    for (const block of blocks) {
      const lines = block.split('\n')
      if (lines.length >= 3) {
        const timeMatch = lines[1].match(/(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})/)
        if (timeMatch) {
          const start = parseInt(timeMatch[1]) * 3600 + parseInt(timeMatch[2]) * 60 + parseInt(timeMatch[3]) + parseInt(timeMatch[4]) / 1000
          const end = parseInt(timeMatch[5]) * 3600 + parseInt(timeMatch[6]) * 60 + parseInt(timeMatch[7]) + parseInt(timeMatch[8]) / 1000
          const text = lines.slice(2).join(' ').trim()

          subtitles.push({ start, end, text })
        }
      }
    }

    return subtitles
  }

  const handleSRTUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.name.endsWith('.srt')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        const parsedSubtitles = parseSRT(content)
        setUploadedSubtitles(parsedSubtitles)
        setSubtitleMode('UPLOAD')
        console.log('Loaded uploaded subtitles:', parsedSubtitles.length, 'entries')
      }
      reader.readAsText(file)
    }
  }

  const cycleSubtitleMode = () => {
    const modes: SubtitleMode[] = ['OFF', 'DE', 'ES', 'DE+ES', 'UPLOAD']
    const currentIndex = modes.indexOf(subtitleMode)
    const nextIndex = (currentIndex + 1) % modes.length
    setSubtitleMode(modes[nextIndex])
  }

  const getSubtitleModeDisplay = () => {
    switch (subtitleMode) {
      case 'OFF': return 'Off'
      case 'DE': return 'DE'
      case 'ES': return 'ES'
      case 'DE+ES': return 'DE+ES'
      case 'UPLOAD': return 'Upload'
      default: return 'Off'
    }
  }

  const getCurrentSegmentTime = () => {
    const segmentStart = currentSegment * SEGMENT_DURATION
    const segmentProgress = Math.max(0, currentTime - segmentStart)
    return Math.min(segmentProgress, SEGMENT_DURATION)
  }

  if (!videoInfo) {
    return null
  }

  const videoUrl = buildVideoStreamUrl(videoInfo.series, videoInfo.episode)
  const segmentProgress = (getCurrentSegmentTime() / SEGMENT_DURATION) * 100

  return (
    <PlayerContainer onMouseMove={handleMouseMove}>
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
          onDuration={setDuration}
          onReady={() => setLoading(false)}
          onBuffer={() => setLoading(true)}
          onBufferEnd={() => setLoading(false)}
          progressInterval={1000}
        />

        {loading && (
          <LoadingOverlay>
            <div className="loading-spinner" />
            <p style={{ marginTop: '16px' }}>Loading...</p>
          </LoadingOverlay>
        )}

        <ControlsOverlay $visible={controlsVisible}>
          <TopControls>
            <BackButton onClick={() => navigate(-1)}>
              <ArrowLeftIcon className="w-4 h-4" />
              Back
            </BackButton>

            <VideoTitle>{videoInfo.title}</VideoTitle>

            <SegmentInfo>
              <div>Segment {currentSegment + 1}</div>
              <div>{formatTime(getCurrentSegmentTime())} / {formatTime(SEGMENT_DURATION)}</div>
            </SegmentInfo>
          </TopControls>

          <BottomControls>
            <ProgressSection>
              <ProgressBar onClick={handleProgressClick}>
                <ProgressFill $progress={progress} />
              </ProgressBar>

              <TimeInfo>
                <span>{formatTime(currentTime)}</span>

                <SegmentProgress>
                  Segment Progress: {Math.round(segmentProgress)}%
                </SegmentProgress>

                <span>{formatTime(duration)}</span>
              </TimeInfo>
            </ProgressSection>

            <Controls>
              <PlayControls>
                <ControlButton onClick={handlePlayPause}>
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

                  <VolumeSlider
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={muted ? 0 : volume}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value)
                      setVolume(value)
                      setMuted(value === 0)
                    }}
                  />
                </VolumeControl>
              </PlayControls>

              <RightControls>
                <SubtitleToggle
                  $mode={subtitleMode}
                  onClick={() => {
                    if (subtitleMode === 'UPLOAD') {
                      // Trigger file upload when in upload mode and clicked again
                      document.getElementById('srt-upload')?.click()
                    } else {
                      cycleSubtitleMode()
                    }
                  }}
                >
                  <LanguageIcon className="w-4 h-4 inline mr-2" />
                  {getSubtitleModeDisplay()}
                </SubtitleToggle>

                <FileInput
                  type="file"
                  accept=".srt"
                  id="srt-upload"
                  onChange={handleSRTUpload}
                />

                <NextSegmentButton onClick={() => {
                  const nextSegment = currentSegment + 1
                  setCurrentSegment(nextSegment)
                  loadSegmentWords(nextSegment)
                  setPlaying(false)
                }}>
                  <ForwardIcon className="w-4 h-4 inline mr-2" />
                  Next Segment
                </NextSegmentButton>
              </RightControls>
            </Controls>
          </BottomControls>
        </ControlsOverlay>

        {subtitleMode !== 'OFF' && (
          <SubtitleDisplay>
            {subtitleMode === 'DE' && currentOriginalSubtitle && (
              <SubtitleLine $language="DE">{currentOriginalSubtitle}</SubtitleLine>
            )}

            {subtitleMode === 'ES' && currentTranslatedSubtitle && (
              <SubtitleLine $language="ES">{currentTranslatedSubtitle}</SubtitleLine>
            )}

            {subtitleMode === 'DE+ES' && (
              <>
                {currentOriginalSubtitle && (
                  <SubtitleLine $language="DE">{currentOriginalSubtitle}</SubtitleLine>
                )}
                {currentTranslatedSubtitle && (
                  <SubtitleLine $language="ES">{currentTranslatedSubtitle}</SubtitleLine>
                )}
              </>
            )}

            {subtitleMode === 'UPLOAD' && currentUploadedSubtitle && (
              <SubtitleLine $language="UPLOAD">{currentUploadedSubtitle}</SubtitleLine>
            )}
          </SubtitleDisplay>
        )}
      </VideoWrapper>

      {showVocabularyGame && (
        <VocabularyGame
          words={segmentWords as any}
          onWordAnswered={handleWordAnswered}
          onComplete={handleVocabularyComplete}
          onSkip={handleSkipVocabulary}
          isLoading={loading}
        />
      )}
    </PlayerContainer>
  )
}
