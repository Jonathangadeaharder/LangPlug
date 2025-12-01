/**
 * Styled components for LearningPlayer
 * Extracted from LearningPlayer.tsx to reduce component complexity
 */

import styled from 'styled-components'
import { NetflixButton } from '@/styles/GlobalStyles'

export const PlayerContainer = styled.div`
  background: #000;
  min-height: 100vh;
  position: relative;
`

export const VideoWrapper = styled.div`
  position: relative;
  width: 100%;
  height: 100vh;
  background: #000;
`

export const ControlsOverlay = styled.div<{ $visible: boolean }>`
  position: absolute;
  inset: 0;
  background: linear-gradient(transparent 0%, rgb(0 0 0 / 30%) 70%, rgb(0 0 0 / 80%) 100%);
  opacity: ${props => (props.$visible ? 1 : 0)};
  transition: opacity 0.3s ease;
  pointer-events: ${props => (props.$visible ? 'auto' : 'none')};
`

export const TopControls = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(rgb(0 0 0 / 80%) 0%, transparent 100%);
  display: flex;
  align-items: center;
  gap: 16px;
`

export const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgb(0 0 0 / 70%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s ease;

  &:hover {
    background: rgb(0 0 0 / 90%);
  }
`

export const VideoTitle = styled.h1`
  font-size: 24px;
  font-weight: bold;
  color: white;
  flex: 1;
`

export const SegmentInfo = styled.div`
  color: #b3b3b3;
  font-size: 14px;
  text-align: right;
`

export const BottomControls = styled.div`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
`

export const ProgressSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

export const ProgressBar = styled.div`
  height: 4px;
  background: rgb(255 255 255 / 30%);
  border-radius: 2px;
  cursor: pointer;
  position: relative;
`

export const ProgressFill = styled.div<{ $progress: number }>`
  height: 100%;
  background: #e50914;
  border-radius: 2px;
  width: ${props => props.$progress}%;
  transition: width 0.1s ease;
`

export const TimeInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #b3b3b3;
`

export const SegmentProgress = styled.div`
  text-align: center;
  color: white;
`

export const Controls = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`

export const PlayControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`

export const ControlButton = styled.button`
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;

  &:hover {
    background: rgb(255 255 255 / 10%);
    transform: scale(1.1);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`

export const VolumeControl = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`

export const VolumeSlider = styled.input`
  width: 100px;
  height: 4px;
  background: rgb(255 255 255 / 30%);
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

export const RightControls = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`

export const SubtitleToggle = styled(NetflixButton)<{ $mode: string }>`
  padding: 8px 16px;
  font-size: 14px;
  background: ${props => (props.$mode !== 'OFF' ? '#e50914' : 'rgba(255, 255, 255, 0.2)')};
  min-width: 80px;

  &:hover {
    background: ${props => (props.$mode !== 'OFF' ? '#f40612' : 'rgba(255, 255, 255, 0.3)')};
  }
`

export const NextSegmentButton = styled(NetflixButton)`
  padding: 8px 16px;
  font-size: 14px;
`

export const FileInput = styled.input`
  display: none;
`

export const SubtitleDisplayWrapper = styled.div`
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

export const SubtitleLine = styled.div<{ $language: 'DE' | 'ES' | 'UPLOAD' }>`
  background: rgb(0 0 0 / 85%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 500;
  border-left: 4px solid
    ${props => {
      switch (props.$language) {
        case 'DE':
          return '#ffd700' // Gold for German
        case 'ES':
          return '#00ff88' // Green for Spanish/English
        case 'UPLOAD':
          return '#ff6b35' // Orange for uploaded
        default:
          return '#ffffff'
      }
    }};
  color: ${props => {
    switch (props.$language) {
      case 'DE':
        return '#ffd700'
      case 'ES':
        return '#00ff88'
      case 'UPLOAD':
        return '#ff6b35'
      default:
        return '#ffffff'
    }
  }};
`

export const SubtitleText = styled.span`
  text-shadow: 2px 2px 4px rgb(0 0 0 / 80%);
`

export const ClickableWord = styled.span<{ $isBlocking?: boolean; $isKnown?: boolean }>`
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0 2px;
  border-radius: 4px;
  background: ${props => {
    if (props.$isBlocking) return 'rgba(255, 0, 0, 0.3)'
    if (props.$isKnown) return 'rgba(0, 255, 0, 0.2)'
    return 'transparent'
  }};

  &:hover {
    background: rgb(255 255 255 / 20%);
    transform: scale(1.05);
    display: inline-block;
  }
`

export const GameOverlay = styled.div`
  position: absolute;
  inset: 0;
  background: rgb(0 0 0 / 95%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 100;
`

export const LoadingOverlay = styled.div`
  position: absolute;
  inset: 0;
  background: rgb(0 0 0 / 80%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  z-index: 50;
`

export const LoadingSpinner = styled.div`
  width: 48px;
  height: 48px;
  border: 4px solid rgb(255 255 255 / 30%);
  border-top-color: #e50914;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`

export const LoadingText = styled.div`
  color: white;
  font-size: 16px;
`
