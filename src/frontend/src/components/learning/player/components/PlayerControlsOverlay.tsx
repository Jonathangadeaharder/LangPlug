import React from 'react'
import styled from 'styled-components'
import {
  PlayIcon,
  PauseIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  MinusIcon,
  PlusIcon,
  ForwardIcon,
  LanguageIcon,
  EyeSlashIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/solid'
import { ChunkInfo } from '../types'
import { SubtitleMode } from '@/hooks/useSubtitlePreferences'

const Overlay = styled.div<{ $visible: boolean; $mobile?: boolean }>`
  position: absolute;
  inset: 0;
  background: linear-gradient(
    transparent 0%,
    transparent 60%,
    rgba(0, 0, 0, 0.3) 85%,
    rgba(0, 0, 0, 0.9) 100%
  );
  opacity: ${props => (props.$visible ? 1 : 0)};
  transition: opacity 0.3s ease;
  pointer-events: ${props => (props.$visible ? 'auto' : 'none')};
  z-index: 10;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 20px 24px;

  ${props => props.$mobile && `
    padding: 12px;
    background: rgba(0, 0, 0, 0.7);
  `}
`

const TopBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
`

const ChunkBadge = styled.div`
  background: rgba(0, 0, 0, 0.8);
  border-radius: 8px;
  padding: 8px 16px;
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 14px;

  @media (max-width: 768px) {
    padding: 8px 12px;
    font-size: 12px;
  }
`

const LearnedBadge = styled.div`
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid #22c55e;
  color: #22c55e;
  border-radius: 8px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;

  @media (max-width: 768px) {
    padding: 6px 12px;
    font-size: 14px;
  }
`

const BottomBar = styled.div`
  padding-bottom: 16px;
`

const ProgressBar = styled.div`
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  cursor: pointer;
  margin-bottom: 16px;
  position: relative;

  &:hover {
    height: 8px;
  }
`

const ProgressFill = styled.div<{ $progress: number }>`
  width: ${props => props.$progress}%;
  height: 100%;
  background: #e50914;
  border-radius: 3px;
`

const ControlsRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`

const LeftGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  
  @media (max-width: 768px) {
    gap: 12px;
  }
`

const RightGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;

  @media (max-width: 768px) {
    gap: 12px;
  }
`

const IconButton = styled.button`
  background: transparent;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.1);
  }
`

const TimeDisplay = styled.div`
  color: white;
  font-size: 14px;
  font-weight: 500;
  min-width: 100px;

  @media (max-width: 768px) {
    font-size: 12px;
    min-width: 80px;
  }
`

interface PlayerControlsOverlayProps {
  visible: boolean
  playing: boolean
  muted: boolean
  currentTime: number
  duration: number
  progress: number
  chunkInfo?: ChunkInfo
  learnedCount: number
  subtitleMode: SubtitleMode
  subtitleLabel: string
  isMobile: boolean
  onPlayToggle: () => void
  onMuteToggle: () => void
  onSeek: (e: React.MouseEvent<HTMLDivElement>) => void
  onSkip: () => void
  onSubtitleToggle: () => void
  onSettingsToggle: () => void
  onFullscreenToggle: () => void
}

export const PlayerControlsOverlay: React.FC<PlayerControlsOverlayProps> = ({
  visible,
  playing,
  muted,
  currentTime,
  duration,
  progress,
  chunkInfo,
  learnedCount,
  subtitleMode,
  subtitleLabel,
  isMobile,
  onPlayToggle,
  onMuteToggle,
  onSeek,
  onSkip,
  onSubtitleToggle,
  onSettingsToggle,
  onFullscreenToggle
}) => {
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  return (
    <Overlay $visible={visible} $mobile={isMobile}>
      <TopBar>
        <div style={{ display: 'flex', gap: '12px' }}>
          {chunkInfo && (
            <ChunkBadge>
              Chunk {chunkInfo.current}/{chunkInfo.total}
            </ChunkBadge>
          )}
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          {learnedCount > 0 && (
            <LearnedBadge>
              <CheckCircleIcon className="w-4 h-4" />
              <span>{learnedCount} learned</span>
            </LearnedBadge>
          )}
          <IconButton onClick={onSettingsToggle}>⚙️</IconButton>
        </div>
      </TopBar>

      <BottomBar>
        <ProgressBar onClick={onSeek}>
          <ProgressFill $progress={progress} />
        </ProgressBar>

        <ControlsRow>
          <LeftGroup>
            <IconButton onClick={onPlayToggle}>
              {playing ? <PauseIcon className="w-8 h-8" /> : <PlayIcon className="w-8 h-8" />}
            </IconButton>
            
            <IconButton onClick={onMuteToggle}>
              {muted ? <SpeakerXMarkIcon className="w-5 h-5" /> : <SpeakerWaveIcon className="w-5 h-5" />}
            </IconButton>

            <TimeDisplay>
              {formatTime(currentTime)} / {formatTime(duration)}
            </TimeDisplay>
          </LeftGroup>

          <RightGroup>
            <IconButton onClick={onSkip}>
              <ForwardIcon className="w-5 h-5" />
              <span>Skip</span>
            </IconButton>

            <IconButton onClick={onSubtitleToggle} title={subtitleLabel}>
              {subtitleMode === 'off' ? (
                <EyeSlashIcon className="w-5 h-5" />
              ) : (
                <LanguageIcon className="w-5 h-5" />
              )}
            </IconButton>

            <IconButton onClick={onFullscreenToggle}>
              {document.fullscreenElement ? <MinusIcon className="w-5 h-5" /> : <PlusIcon className="w-5 h-5" />}
            </IconButton>
          </RightGroup>
        </ControlsRow>
      </BottomBar>
    </Overlay>
  )
}