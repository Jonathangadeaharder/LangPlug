import React, { useEffect, useState } from 'react'
import styled, { keyframes } from 'styled-components'
import { ClockIcon } from '@heroicons/react/24/solid'
import type { ProcessingStatus } from '@/types'

const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`

const pulse = keyframes`
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
`

const ProcessingContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #141414 0%, #1f1f1f 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  animation: ${fadeIn} 0.5s ease-out;
`

const ContentCard = styled.div`
  background: rgb(0 0 0 / 80%);
  border-radius: 16px;
  padding: 48px;
  max-width: 600px;
  width: 100%;
  box-shadow: 0 20px 60px rgb(0 0 0 / 50%);
  border: 1px solid rgb(255 255 255 / 10%);
`

const Title = styled.h1`
  font-size: 32px;
  font-weight: bold;
  color: white;
  text-align: center;
  margin-bottom: 12px;
`

const Subtitle = styled.p`
  font-size: 18px;
  color: #b3b3b3;
  text-align: center;
  margin-bottom: 40px;
`

const ProgressSection = styled.div`
  margin-bottom: 32px;
`

const StepIndicator = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
`

const StepIcon = styled.div`
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #e50914, #b00610);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ${pulse} 2s ease-in-out infinite;
`

const StepName = styled.h2`
  font-size: 20px;
  font-weight: 600;
  color: #e50914;
`

const ProgressBarContainer = styled.div`
  width: 100%;
  height: 12px;
  background: rgb(255 255 255 / 10%);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 16px;
`

const ProgressBarFill = styled.div<{ $progress: number }>`
  width: ${props => props.$progress}%;
  height: 100%;
  background: linear-gradient(90deg, #e50914, #ff6b6b);
  border-radius: 6px;
  transition: width 0.5s ease-out;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgb(255 255 255 / 30%), transparent);
    animation: shimmer 2s infinite;
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }

    100% {
      transform: translateX(100%);
    }
  }
`

const ProgressText = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`

const ProgressPercentage = styled.span`
  font-size: 24px;
  font-weight: bold;
  color: white;
`

const TimeEstimate = styled.span`
  font-size: 14px;
  color: #b3b3b3;
  display: flex;
  align-items: center;
  gap: 6px;
`

const StatusMessage = styled.p`
  font-size: 16px;
  color: #b3b3b3;
  text-align: center;
  font-style: italic;
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
`

const ChunkInfo = styled.div`
  background: rgb(255 255 255 / 5%);
  border-radius: 8px;
  padding: 16px;
  margin-top: 24px;
  text-align: center;
`

const ChunkLabel = styled.div`
  font-size: 14px;
  color: #b3b3b3;
  margin-bottom: 8px;
`

const ChunkDetails = styled.div`
  font-size: 18px;
  color: white;
  font-weight: 500;
`

const ConnectionIndicator = styled.div<{ $isRealtime: boolean }>`
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: ${props => (props.$isRealtime ? '#4ade80' : '#b3b3b3')};
  margin-top: 16px;
  justify-content: center;

  &::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: ${props => (props.$isRealtime ? '#4ade80' : '#b3b3b3')};
    animation: ${props => (props.$isRealtime ? 'pulse 2s infinite' : 'none')};
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
`

interface ProcessingScreenProps {
  status: ProcessingStatus
  chunkNumber?: number
  totalChunks?: number
  chunkDuration?: string // e.g., "0:00 - 5:00"
  connectionMethod?: 'websocket' | 'polling' | 'disconnected' // Real-time connection indicator
}

export const ProcessingScreen: React.FC<ProcessingScreenProps> = ({
  status,
  chunkNumber = 1,
  totalChunks = 1,
  chunkDuration = '0:00 - 5:00',
  connectionMethod,
}) => {
  const [estimatedTime, setEstimatedTime] = useState<string>('calculating...')
  const [startTime] = useState<number>(Date.now())

  useEffect(() => {
    // Calculate estimated time based on progress
    if (status.progress > 0 && status.progress < 100) {
      // Use local start time instead of relying on status.started_at
      const elapsedTime = Date.now() - startTime
      const totalTime = (elapsedTime / status.progress) * 100
      const remainingTime = totalTime - elapsedTime

      // Sanity check: don't show ridiculous times
      if (remainingTime < 0 || remainingTime > 3600000) {
        // More than 1 hour
        setEstimatedTime('calculating...')
      } else {
        const minutes = Math.floor(remainingTime / 60000)
        const seconds = Math.floor((remainingTime % 60000) / 1000)

        if (minutes > 0) {
          setEstimatedTime(`${minutes}m ${seconds}s remaining`)
        } else {
          setEstimatedTime(`${seconds}s remaining`)
        }
      }
    } else if (status.progress === 100) {
      setEstimatedTime('Completing...')
    } else if (status.progress === 0) {
      setEstimatedTime('Starting...')
    }
  }, [status.progress, startTime])

  const getStepIcon = () => {
    switch (status.current_step?.toLowerCase()) {
      case 'transcribing':
      case 'transcription':
        return '🎙️'
      case 'filtering':
        return '🔍'
      case 'translating':
      case 'translation':
        return '🌐'
      case 'processing':
        return '⚙️'
      default:
        return '📝'
    }
  }

  return (
    <ProcessingContainer>
      <ContentCard>
        <Title>Processing Episode</Title>
        <Subtitle>Preparing your learning experience...</Subtitle>

        <ProgressSection>
          <StepIndicator>
            <StepIcon>
              <span style={{ fontSize: '24px' }}>{getStepIcon()}</span>
            </StepIcon>
            <StepName>{status.current_step || 'Processing'}</StepName>
          </StepIndicator>

          <ProgressText>
            <ProgressPercentage>{Math.round(status.progress)}%</ProgressPercentage>
            <TimeEstimate>
              <ClockIcon className="w-4 h-4" />
              {estimatedTime}
            </TimeEstimate>
          </ProgressText>

          <ProgressBarContainer>
            <ProgressBarFill $progress={status.progress} />
          </ProgressBarContainer>

          <StatusMessage>{status.message || 'Processing your episode...'}</StatusMessage>
        </ProgressSection>

        {totalChunks > 1 && (
          <ChunkInfo>
            <ChunkLabel>Processing Chunk</ChunkLabel>
            <ChunkDetails>
              {chunkNumber} of {totalChunks} • {chunkDuration}
            </ChunkDetails>
          </ChunkInfo>
        )}

        {connectionMethod && (
          <ConnectionIndicator $isRealtime={connectionMethod === 'websocket'}>
            {connectionMethod === 'websocket'
              ? 'Real-time updates active'
              : connectionMethod === 'polling'
                ? 'Checking for updates...'
                : 'Connecting...'}
          </ConnectionIndicator>
        )}
      </ContentCard>
    </ProcessingContainer>
  )
}
