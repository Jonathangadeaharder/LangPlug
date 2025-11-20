/**
 * Synced Subtitle Display Component
 * Real-time word highlighting synchronized with video playback
 * Combines interactive hover translation with playback synchronization
 */
import React, { useEffect, useState, useRef } from 'react'
import { SubtitleSegment, subtitleSyncService } from '../services/subtitleSyncService'
import { useSubtitleHover } from '../hooks/useSubtitleHover'
import './SyncedSubtitleDisplay.css'

interface SyncedSubtitleDisplayProps {
  segments: SubtitleSegment[]
  videoRef: React.RefObject<HTMLVideoElement>
  knownWords?: Set<string>
  language?: string
  showTranslation?: boolean
  onWordClick?: (word: string) => void
  className?: string
}

const SyncedSubtitleDisplay: React.FC<SyncedSubtitleDisplayProps> = ({
  segments,
  videoRef,
  knownWords = new Set(),
  language = 'de',
  showTranslation = true,
  onWordClick,
  className = '',
}) => {
  const [activeWord, setActiveWord] = useState<string | null>(null)
  const [currentSegment, setCurrentSegment] = useState<SubtitleSegment | null>(null)
  const updateIntervalRef = useRef<number | null>(null)

  const { hoveredWord, translationData, isLoading, onWordHover, onWordLeave, tooltipPosition } =
    useSubtitleHover(language)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const updateHighlight = () => {
      const currentTime = video.currentTime

      // Find active segment
      const segment = subtitleSyncService.getActiveSegmentAtTime(segments, currentTime)

      if (segment) {
        setCurrentSegment(segment)

        // Find active word
        const word = subtitleSyncService.getActiveWordAtTime(segments, currentTime)
        setActiveWord(word?.word || null)
      } else {
        setCurrentSegment(null)
        setActiveWord(null)
      }
    }

    // Update every 50ms for smooth highlighting (20 FPS)
    updateIntervalRef.current = window.setInterval(updateHighlight, 50)

    // Also update on seek
    const handleSeeked = () => updateHighlight()
    video.addEventListener('seeked', handleSeeked)

    // Initial update
    updateHighlight()

    return () => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current)
      }
      video.removeEventListener('seeked', handleSeeked)
    }
  }, [segments, videoRef])

  if (!currentSegment) {
    return (
      <div className={`synced-subtitle-display empty ${className}`}>
        <div className="no-subtitle-message">No subtitles</div>
      </div>
    )
  }

  const handleWordClick = (word: string) => {
    if (onWordClick) {
      onWordClick(word)
    }
  }

  return (
    <div className={`synced-subtitle-display ${className}`}>
      <div className="subtitle-words">
        {currentSegment.words.map((wordData, index) => {
          const isActive = wordData.word === activeWord
          const isKnown = knownWords.has(wordData.word.toLowerCase())
          const isHovered = hoveredWord?.toLowerCase() === wordData.word.toLowerCase()

          return (
            <span
              key={`${currentSegment.id}-word-${index}`}
              className={`subtitle-word ${isActive ? 'active' : ''} ${isKnown ? 'known' : 'unknown'} ${
                isHovered ? 'hovered' : ''
              }`}
              role="button"
              tabIndex={0}
              onMouseEnter={e => onWordHover(wordData.word, e)}
              onMouseLeave={onWordLeave}
              onClick={() => handleWordClick(wordData.word)}
              onKeyDown={e => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  handleWordClick(wordData.word)
                }
              }}
              data-word={wordData.word}
              data-start={wordData.start}
              data-end={wordData.end}
            >
              {wordData.word}
            </span>
          )
        })}
      </div>

      {showTranslation && tooltipPosition && (hoveredWord || isLoading) && (
        <div
          className="translation-tooltip"
          style={{
            left: `${tooltipPosition.x}px`,
            top: `${tooltipPosition.y + 20}px`,
          }}
        >
          {isLoading ? (
            <div className="tooltip-loading">Loading...</div>
          ) : translationData ? (
            <div className="tooltip-content">
              <div className="tooltip-word">{translationData.word}</div>
              <div className="tooltip-translation">{translationData.translation}</div>
              {translationData.level && (
                <div className="tooltip-level">Level: {translationData.level}</div>
              )}
              {translationData.partOfSpeech && (
                <div className="tooltip-pos">{translationData.partOfSpeech}</div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}

export default SyncedSubtitleDisplay
