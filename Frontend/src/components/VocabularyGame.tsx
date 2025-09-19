import React, { useState, useEffect } from 'react'
import styled from 'styled-components'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckIcon, XMarkIcon, ArrowPathIcon } from '@heroicons/react/24/solid'
import { toast } from 'react-hot-toast'
import { NetflixButton, FlexCenter } from '@/styles/GlobalStyles'
import type { VocabularyWord } from '@/types'

const GameContainer = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
`

const GameHeader = styled.div`
  text-align: center;
  margin-bottom: 40px;
`

const GameTitle = styled.h2`
  font-size: 28px;
  font-weight: bold;
  color: white;
  margin-bottom: 16px;
`

const GameSubtitle = styled.p`
  font-size: 16px;
  color: #b3b3b3;
  margin-bottom: 24px;
`

const ProgressBar = styled.div`
  width: 300px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
  margin: 0 auto;
`

const ProgressFill = styled.div<{ $progress: number }>`
  width: ${props => props.$progress}%;
  height: 100%;
  background: linear-gradient(90deg, #e50914, #f40612);
  transition: width 0.3s ease;
`

const ProgressText = styled.div`
  color: #b3b3b3;
  font-size: 14px;
  margin-top: 8px;
`

const CardContainer = styled.div`
  position: relative;
  width: 400px;
  height: 500px;
  margin: 40px auto;
  
  @media (max-width: 480px) {
    width: 320px;
    height: 420px;
  }
`

const VocabularyCard = styled(motion.div).withConfig({
  shouldForwardProp: (prop) => !['dragConstraints', 'drag', 'onDragEnd'].includes(prop),
})`
  position: absolute;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  cursor: grab;
  user-select: none;

  &:active {
    cursor: grabbing;
  }
`

const WordText = styled.h1`
  font-size: 48px;
  font-weight: bold;
  color: white;
  margin-bottom: 24px;
  word-break: break-word;
  
  @media (max-width: 480px) {
    font-size: 36px;
  }
`

const DifficultyBadge = styled.div<{ $level: string }>`
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 16px;
  
  ${props => {
    switch (props.$level.toLowerCase()) {
      case 'a1':
        return 'background: rgba(70, 211, 105, 0.2); color: #46d369; border: 1px solid #46d369;'
      case 'a2':
        return 'background: rgba(59, 130, 246, 0.2); color: #3b82f6; border: 1px solid #3b82f6;'
      case 'b1':
        return 'background: rgba(232, 124, 3, 0.2); color: #e87c03; border: 1px solid #e87c03;'
      case 'b2':
        return 'background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444;'
      default:
        return 'background: rgba(156, 163, 175, 0.2); color: #9ca3af; border: 1px solid #9ca3af;'
    }
  }}
`

const Definition = styled.p`
  font-size: 16px;
  color: #b3b3b3;
  line-height: 1.5;
  max-width: 280px;
  margin-bottom: 32px;
`

const SwipeHint = styled.div`
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 24px;
  font-size: 14px;
  color: #666;
`

const SwipeAction = styled.div<{ $type: 'know' | 'unknown' }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 20px;
  background: ${props => props.$type === 'know' 
    ? 'rgba(70, 211, 105, 0.1)' 
    : 'rgba(239, 68, 68, 0.1)'
  };
  border: 1px solid ${props => props.$type === 'know' 
    ? 'rgba(70, 211, 105, 0.3)' 
    : 'rgba(239, 68, 68, 0.3)'
  };
  color: ${props => props.$type === 'know' ? '#46d369' : '#ef4444'};
`

const ActionButtons = styled.div`
  display: flex;
  gap: 20px;
  margin-top: 40px;
`

const ActionButton = styled.button<{ $type: 'know' | 'unknown' }>`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  
  ${props => props.$type === 'know' ? `
    background: rgba(70, 211, 105, 0.2);
    color: #46d369;
    border: 2px solid #46d369;
    
    &:hover {
      background: rgba(70, 211, 105, 0.3);
      transform: scale(1.1);
    }
  ` : `
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
    border: 2px solid #ef4444;
    
    &:hover {
      background: rgba(239, 68, 68, 0.3);
      transform: scale(1.1);
    }
  `}
`

const CompletionScreen = styled.div`
  text-align: center;
  color: white;
`

const CompletionTitle = styled.h2`
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 16px;
`

const CompletionStats = styled.div`
  font-size: 18px;
  color: #b3b3b3;
  margin-bottom: 32px;
`

const LoadingSpinner = styled.div`
  color: white;
  text-align: center;
`

interface VocabularyGameProps {
  words: VocabularyWord[]
  onWordAnswered?: (word: string, known: boolean) => Promise<void>
  onComplete: (knownWords: string[], unknownWords: string[]) => void
  onSkip?: () => void
  episodeTitle?: string
  chunkInfo?: {
    current: number
    total: number
    duration: string
  }
  isLoading?: boolean
}

export const VocabularyGame: React.FC<VocabularyGameProps> = ({
  words,
  onWordAnswered,
  onComplete,
  onSkip,
  episodeTitle,
  chunkInfo,
  isLoading = false
}) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answeredWords, setAnsweredWords] = useState(0)
  const [knownCount, setKnownCount] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)
  const [knownWords, setKnownWords] = useState<string[]>([])
  const [unknownWords, setUnknownWords] = useState<string[]>([])

  const currentWord = words[currentIndex]
  const progress = words.length > 0 ? ((currentIndex + 1) / words.length) * 100 : 0
  const isComplete = currentIndex >= words.length

  useEffect(() => {
    if (isComplete && answeredWords > 0) {
      onComplete(knownWords, unknownWords)
    }
  }, [isComplete, answeredWords, onComplete, knownWords, unknownWords])

  const handleAnswer = async (known: boolean) => {
    if (!currentWord || isProcessing) return

    setIsProcessing(true)

    try {
      if (onWordAnswered) {
        await onWordAnswered(currentWord.word, known)
      }
      
      setAnsweredWords(prev => prev + 1)
      if (known) {
        setKnownCount(prev => prev + 1)
        setKnownWords(prev => [...prev, currentWord.word])
      } else {
        setUnknownWords(prev => [...prev, currentWord.word])
      }
      
      // Move to next word after a short delay
      setTimeout(() => {
        setCurrentIndex(prev => prev + 1)
        setIsProcessing(false)
      }, 300)
      
    } catch (error) {
      setIsProcessing(false)
      toast.error('Failed to save word progress')
    }
  }

  const handleSkip = async () => {
    if (isProcessing) return

    setIsProcessing(true)

    try {
      // Mark all remaining words as unknown
      const remainingWords = words.slice(currentIndex)
      const newUnknownWords = [...unknownWords]
      
      for (const word of remainingWords) {
        // Call onWordAnswered for each remaining word as unknown
        if (onWordAnswered) {
          await onWordAnswered(word.word, false)
        }
        newUnknownWords.push(word.word)
      }

      // Update final counts
      const finalAnsweredWords = answeredWords + remainingWords.length
      
      // Complete the game with all remaining words marked as unknown
      onComplete(knownWords, newUnknownWords)
      
    } catch (error) {
      setIsProcessing(false)
      console.error('Failed to process remaining words:', error)
      // Still allow skip even if word processing fails
      if (onSkip) {
        onSkip()
      }
    }
  }

  if (isLoading) {
    return (
      <GameContainer>
        <LoadingSpinner>
          <div className="loading-spinner" />
          <p style={{ marginTop: '16px' }}>Loading vocabulary words...</p>
        </LoadingSpinner>
      </GameContainer>
    )
  }

  if (words.length === 0) {
    return (
      <GameContainer>
        <CompletionScreen>
          <CompletionTitle>No New Words!</CompletionTitle>
          <p style={{ color: '#b3b3b3', marginBottom: '32px' }}>
            You already know all the vocabulary in this segment. Great job!
          </p>
          <NetflixButton onClick={() => onComplete([], [])}>
            Continue Watching
          </NetflixButton>
        </CompletionScreen>
      </GameContainer>
    )
  }

  if (isComplete) {
    return (
      <GameContainer>
        <CompletionScreen>
          <CompletionTitle>Segment Complete!</CompletionTitle>
          <CompletionStats>
            You knew {knownCount} out of {answeredWords} words ({Math.round((knownCount / answeredWords) * 100)}%)
          </CompletionStats>
          <NetflixButton onClick={() => onComplete(knownWords, unknownWords)}>
            Watch This Segment
          </NetflixButton>
        </CompletionScreen>
      </GameContainer>
    )
  }

  return (
    <GameContainer>
      <GameHeader>
        <GameTitle>Vocabulary Check</GameTitle>
        {chunkInfo && (
          <GameSubtitle style={{ marginBottom: '8px' }}>
            Chunk {chunkInfo.current} of {chunkInfo.total} • {chunkInfo.duration}
          </GameSubtitle>
        )}
        <GameSubtitle>Do you know this word?</GameSubtitle>
        <ProgressBar>
          <ProgressFill $progress={progress} />
        </ProgressBar>
        <ProgressText>
          {currentIndex + 1} of {words.length} words
        </ProgressText>
      </GameHeader>

      <CardContainer>
        <AnimatePresence mode="wait">
          {currentWord && (
            <VocabularyCard
              key={currentWord.word}
              initial={{ x: 100, opacity: 0, scale: 0.8 }}
              animate={{ x: 0, opacity: 1, scale: 1 }}
              exit={{ x: -100, opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.3 }}
              drag="x"
              dragConstraints={{ left: 0, right: 0 }}
              onDragEnd={(_, info) => {
                if (info.offset.x > 100) {
                  handleAnswer(true)
                } else if (info.offset.x < -100) {
                  handleAnswer(false)
                }
              }}
            >
              <WordText>{currentWord.word}</WordText>
              
              <DifficultyBadge $level={currentWord.difficulty_level}>
                {currentWord.difficulty_level?.toUpperCase() || 'UNKNOWN'} Level
              </DifficultyBadge>
              
              {currentWord.definition && (
                <Definition>{currentWord.definition}</Definition>
              )}
              
              <SwipeHint>
                <SwipeAction $type="unknown">
                  <XMarkIcon className="w-4 h-4" />
                  Swipe left if unknown
                </SwipeAction>
                <SwipeAction $type="know">
                  <CheckIcon className="w-4 h-4" />
                  Swipe right if you know
                </SwipeAction>
              </SwipeHint>
            </VocabularyCard>
          )}
        </AnimatePresence>
      </CardContainer>

      <ActionButtons>
        <ActionButton 
          $type="unknown" 
          onClick={() => handleAnswer(false)}
          disabled={isProcessing}
        >
          <XMarkIcon className="w-6 h-6" />
        </ActionButton>
        
        <ActionButton 
          $type="know" 
          onClick={() => handleAnswer(true)}
          disabled={isProcessing}
        >
          <CheckIcon className="w-6 h-6" />
        </ActionButton>
      </ActionButtons>

      <div style={{ marginTop: '24px' }}>
        <NetflixButton variant="secondary" onClick={handleSkip}>
          Skip Remaining
        </NetflixButton>
      </div>
    </GameContainer>
  )
}