import React from 'react'
import styled from 'styled-components'
import { SubtitleMode } from '@/hooks/useSubtitlePreferences'

const Container = styled.div`
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

const TextBox = styled.div`
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

const OriginalText = styled.div`
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

const TranslatedText = styled.div`
  color: #fff;
  font-size: 16px;
  line-height: 1.3;
  opacity: 0.9;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);

  @media (max-width: 768px) {
    font-size: 14px;
  }
`

interface SubtitleDisplayProps {
  mode: SubtitleMode
  original: string
  translation: string
}

export const SubtitleDisplay: React.FC<SubtitleDisplayProps> = ({ mode, original, translation }) => {
  if (mode === 'off') return null
  
  const showOriginal = mode === 'original' || mode === 'both'
  const showTranslation = mode === 'translation' || mode === 'both'

  if ((!showOriginal && !showTranslation) || (!original && !translation)) return null

  return (
    <Container>
      <TextBox>
        {showOriginal && original && <OriginalText>{original}</OriginalText>}
        {showTranslation && translation && <TranslatedText>{translation}</TranslatedText>}
      </TextBox>
    </Container>
  )
}
