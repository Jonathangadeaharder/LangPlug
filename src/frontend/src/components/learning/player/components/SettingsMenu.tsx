import React from 'react'
import styled from 'styled-components'
import { PlaybackSpeed } from '../types'
import { SubtitleMode } from '@/hooks/useSubtitlePreferences'

const MenuContainer = styled.div<{ $visible: boolean }>`
  position: absolute;
  bottom: 70px;
  right: 24px;
  background: rgba(0, 0, 0, 0.95);
  border-radius: 8px;
  padding: 16px;
  min-width: 200px;
  opacity: ${props => (props.$visible ? 1 : 0)};
  transform: ${props => (props.$visible ? 'translateY(0)' : 'translateY(10px)')};
  transition: all 0.2s ease;
  pointer-events: ${props => (props.$visible ? 'auto' : 'none')};
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 20;
`

const Section = styled.div`
  margin-bottom: 16px;
  &:last-child { margin-bottom: 0; }
`

const Label = styled.div`
  color: #b3b3b3;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
  text-transform: uppercase;
`

const Button = styled.button<{ $active?: boolean }>`
  width: 100%;
  background: ${props => (props.$active ? 'rgba(229, 9, 20, 0.2)' : 'transparent')};
  border: none;
  color: ${props => (props.$active ? '#e50914' : 'white')};
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
  font-size: 14px;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }
`

interface SettingsMenuProps {
  visible: boolean
  playbackRate: number
  subtitleMode: SubtitleMode
  subtitleOptions: Array<{ value: SubtitleMode; label: string }>
  onSpeedChange: (speed: PlaybackSpeed) => void
  onSubtitleChange: (mode: SubtitleMode) => void
}

export const SettingsMenu: React.FC<SettingsMenuProps> = ({
  visible,
  playbackRate,
  subtitleMode,
  subtitleOptions,
  onSpeedChange,
  onSubtitleChange
}) => {
  const speeds: PlaybackSpeed[] = [0.5, 0.75, 1, 1.25, 1.5, 2]

  return (
    <MenuContainer $visible={visible}>
      <Section>
        <Label>Playback Speed</Label>
        {speeds.map(speed => (
          <Button
            key={speed}
            $active={playbackRate === speed}
            onClick={() => onSpeedChange(speed)}
          >
            {speed}x {speed === 1 && '(Normal)'}
          </Button>
        ))}
      </Section>

      <Section>
        <Label>Subtitles</Label>
        {subtitleOptions.map(opt => (
          <Button
            key={opt.value}
            $active={subtitleMode === opt.value}
            onClick={() => onSubtitleChange(opt.value)}
          >
            {opt.label}
          </Button>
        ))}
      </Section>
    </MenuContainer>
  )
}
