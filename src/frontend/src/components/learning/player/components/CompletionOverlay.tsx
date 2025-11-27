import React from 'react'
import styled from 'styled-components'
import { ChunkInfo } from '../types'

const Overlay = styled.div`
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

const Content = styled.div`
  text-align: center;
  max-width: 500px;
  padding: 20px;
`

const Title = styled.h2`
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 16px;
`

const Message = styled.p`
  font-size: 18px;
  color: #b3b3b3;
  margin-bottom: 32px;
  line-height: 1.5;
`

const Button = styled.button`
  background: #e50914;
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #f40612;
    transform: translateY(-2px);
  }
`

interface CompletionOverlayProps {
  learnedCount: number
  chunkInfo?: ChunkInfo
  onContinue: () => void
}

export const CompletionOverlay: React.FC<CompletionOverlayProps> = ({
  learnedCount,
  chunkInfo,
  onContinue
}) => {
  const isLast = chunkInfo && chunkInfo.current >= chunkInfo.total

  return (
    <Overlay>
      <Content>
        <Title>Chunk Complete! 🎉</Title>
        <Message>
          Excellent work! You've completed this segment and learned {learnedCount} new words.
          {!isLast && " Ready for the next chunk?"}
        </Message>
        <Button onClick={onContinue}>
          {isLast ? 'Complete Episode' : 'Continue to Next Chunk'}
        </Button>
      </Content>
    </Overlay>
  )
}
