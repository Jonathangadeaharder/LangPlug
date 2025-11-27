import React, { useRef, useState, useEffect, useCallback } from 'react'
import styled from 'styled-components'
import ReactPlayer from 'react-player'
import { ArrowLeftIcon } from '@heroicons/react/24/solid'

import { ChunkedLearningPlayerProps } from './types'
import { usePlayerControls } from './hooks/usePlayerControls'
import { useSubtitleSystem } from './hooks/useSubtitleSystem'
import { buildVideoStreamUrl } from '@/services/api'
import { logger } from '@/services/logger'

// Components
import { PlayerControlsOverlay } from './components/PlayerControlsOverlay'
import { SubtitleDisplay } from './components/SubtitleDisplay'
import { SettingsMenu } from './components/SettingsMenu'
import { CompletionOverlay } from './components/CompletionOverlay'

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

  &.show-cursor { cursor: default; }
  &.fullscreen { position: fixed; inset: 0; z-index: 9999; }
`

const StickyBackButton = styled.button`
  position: absolute;
  top: 16px;
  left: 24px;
  z-index: 30;
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
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.12);
  }
`

export const ChunkedLearningPlayer: React.FC<ChunkedLearningPlayerProps> = (props) => {
  const playerRef = useRef<ReactPlayer>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [showCompletion, setShowCompletion] = useState(false)
  const [videoReady, setVideoReady] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  // 1. Player Logic Hook
  const { state, actions } = usePlayerControls({
    playerRef,
    startTime: props.startTime,
    endTime: props.endTime,
    onComplete: () => {
      actions.setPlaying(false)
      setShowCompletion(true)
    },
    onSkip: () => {
      actions.setPlaying(false)
      props.onSkipChunk ? props.onSkipChunk() : props.onComplete()
    }
  })

  // 2. Subtitle Logic Hook
  const { 
    subtitleMode, 
    setSubtitleMode, 
    currentSubtitle, 
    subtitleModeLabels 
  } = useSubtitleSystem({
    subtitlePath: props.subtitlePath,
    translationPath: props.translationPath,
    translationIndices: props.translationIndices,
    series: props.series,
    startTime: props.startTime,
    endTime: props.endTime,
    currentTime: state.currentTime,
    targetLanguageName: props.targetLanguage?.name,
    nativeLanguageName: props.nativeLanguage?.name
  })

  // Mobile detection
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 768)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // 3. Video Ready Handler
  const handleVideoReady = () => {
    if (videoReady) return
    logger.info('Player', 'Video ready', { start: props.startTime })
    setVideoReady(true)
    playerRef.current?.seekTo(props.startTime, 'seconds')
    // Small delay to prevent seek-back glitch
    setTimeout(() => actions.setPlaying(true), 200)
  }

  // Reset ready state on chunk change
  useEffect(() => {
    setVideoReady(false)
    actions.setPlaying(false)
    setShowCompletion(false)
  }, [props.startTime, props.endTime])

  // Handle Seek Click
  const handleSeekClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
      const bounds = e.currentTarget.getBoundingClientRect()
      const x = e.clientX - bounds.left
      const percentage = x / bounds.width
      const seekTime = props.startTime + (props.endTime - props.startTime) * percentage
      actions.handleSeek(seekTime)
  }, [props.startTime, props.endTime, actions])

  // Subtitle options for menu
  const subtitleOptions = Object.entries(subtitleModeLabels).map(([value, label]) => ({
    value: value as any,
    label
  }))

  return (
    <PlayerContainer ref={containerRef}>
      <VideoWrapper 
        className={`${state.showControls ? 'show-cursor' : ''} ${state.isFullscreen ? 'fullscreen' : ''}`}
        onMouseMove={() => actions.setShowControls(true)}
      >
        <ReactPlayer
          ref={playerRef}
          url={buildVideoStreamUrl(props.series, props.episode)}
          width="100%"
          height="100%"
          playing={state.playing}
          volume={state.volume}
          muted={state.muted}
          playbackRate={state.playbackRate}
          controls={false}
          onReady={handleVideoReady}
          onProgress={(p) => {
            actions.setCurrentTime(p.playedSeconds)
            // Auto-pause at end of chunk
            if (p.playedSeconds >= props.endTime && !showCompletion) {
                actions.setPlaying(false)
                setShowCompletion(true)
            }
          }}
          progressInterval={100}
        />

        {props.onBack && (
          <StickyBackButton onClick={props.onBack}>
            <ArrowLeftIcon className="w-5 h-5" />
            <span>Back to Episodes</span>
          </StickyBackButton>
        )}

        <SubtitleDisplay 
          mode={subtitleMode}
          original={currentSubtitle.original}
          translation={currentSubtitle.translation}
        />

        {!showCompletion && (
          <PlayerControlsOverlay
            visible={state.showControls}
            playing={state.playing}
            muted={state.muted}
            currentTime={state.currentTime - props.startTime}
            duration={props.endTime - props.startTime}
            progress={state.progress}
            chunkInfo={props.chunkInfo}
            learnedCount={props.learnedWords?.length || 0}
            subtitleMode={subtitleMode}
            subtitleLabel={subtitleModeLabels[subtitleMode]}
            isMobile={isMobile}
            onPlayToggle={() => actions.setPlaying(!state.playing)}
            onMuteToggle={() => actions.setMuted(!state.muted)}
            onSeek={handleSeekClick}
            onSkip={() => {
               actions.setPlaying(false)
               props.onSkipChunk ? props.onSkipChunk() : props.onComplete()
            }}
            onSubtitleToggle={() => {
               const modes = ['off', 'original', 'translation', 'both']
               const next = modes[(modes.indexOf(subtitleMode) + 1) % modes.length]
               setSubtitleMode(next as any)
            }}
            onSettingsToggle={() => setShowSettings(!showSettings)}
            onFullscreenToggle={actions.toggleFullscreen}
          />
        )}

        <SettingsMenu
          visible={showSettings}
          playbackRate={state.playbackRate}
          subtitleMode={subtitleMode}
          subtitleOptions={subtitleOptions}
          onSpeedChange={actions.setPlaybackRate}
          onSubtitleChange={setSubtitleMode}
        />

        {showCompletion && (
          <CompletionOverlay
            learnedCount={props.learnedWords?.length || 0}
            chunkInfo={props.chunkInfo}
            onContinue={props.onComplete}
          />
        )}
      </VideoWrapper>
    </PlayerContainer>
  )
}