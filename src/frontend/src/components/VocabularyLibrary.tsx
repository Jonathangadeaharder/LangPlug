import axios from 'axios'
import React, { useState, useEffect, memo, useCallback, useMemo } from 'react'
import { toast } from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { Grid } from 'react-window'
import type { CellComponentProps } from 'react-window'
import {
  bulkMarkLevelApiVocabularyLibraryBulkMarkPost,
  createVocabularyApiVocabularyPost,
  getVocabularyLevelApiVocabularyLibraryLevelGet,
  getVocabularyStatsApiVocabularyStatsGet,
  markWordKnownApiVocabularyMarkKnownPost,
} from '@/client/services.gen'
import { logger } from '@/services/logger'
import { formatApiError, isRateLimitError, getRetryAfter } from '@/utils/error-formatter'
import type { VocabularyLevel, VocabularyStats, VocabularyLibraryWord } from '@/types'

const Container = styled.div`
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
`

const BackButton = styled.button`
  background: #34495e;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: background-color 0.2s;

  &:hover {
    background: #2c3e50;
  }

  &::before {
    content: '←';
    font-size: 1.2rem;
  }
`

const Header = styled.div`
  text-align: center;
  margin-bottom: 2rem;

  h1 {
    color: #2c3e50;
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  p {
    color: #7f8c8d;
    font-size: 1.1rem;
  }
`

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`

const StatCard = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;

  .stat-number {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
  }

  .stat-label {
    font-size: 0.9rem;
    opacity: 0.9;
  }
`

const LevelTabs = styled.div`
  display: flex;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 0.5rem;
  margin-bottom: 2rem;
  gap: 0.5rem;
`

const LevelTab = styled.button<{ $active: boolean }>`
  flex: 1;
  padding: 1rem;
  border: none;
  background: ${props => (props.$active ? '#667eea' : 'transparent')};
  color: ${props => (props.$active ? 'white' : '#2c3e50')};
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${props => (props.$active ? '#667eea' : '#e9ecef')};
  }
`

const LevelHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgb(0 0 0 / 10%);

  .level-info {
    h2 {
      color: #2c3e50;
      margin: 0 0 0.5rem;
    }

    .progress-bar {
      width: 200px;
      height: 8px;
      background: #ecf0f1;
      border-radius: 4px;
      overflow: hidden;

      .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #52c41a, #389e0d);
        transition: width 0.3s ease;
      }
    }

    .progress-text {
      font-size: 0.9rem;
      color: #7f8c8d;
      margin-top: 0.5rem;
    }
  }

  .level-actions {
    display: flex;
    gap: 1rem;
  }
`

const Button = styled.button<{ $variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;

  ${props => {
    switch (props.$variant) {
      case 'primary':
        return `
          background: #52c41a;
          color: white;
          &:hover { background: #389e0d; }
        `
      case 'danger':
        return `
          background: #ff4d4f;
          color: white;
          &:hover { background: #d32f2f; }
        `
      default:
        return `
          background: #f0f0f0;
          color: #2c3e50;
          &:hover { background: #e0e0e0; }
        `
    }
  }}
`

const WordsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
`

const WordCard = styled.div<{ $known: boolean }>`
  background: white;
  border: 2px solid ${props => (props.$known ? '#52c41a' : '#e9ecef')};
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;

  &:hover {
    border-color: ${props => (props.$known ? '#389e0d' : '#667eea')};
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgb(0 0 0 / 10%);
  }

  .word-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;

    .word {
      font-size: 1.2rem;
      font-weight: 600;
      color: #2c3e50;
    }

    .known-badge {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: ${props => (props.$known ? '#52c41a' : '#dee2e6')};
      display: flex;
      align-items: center;
      justify-content: center;

      &::after {
        content: '✓';
        color: white;
        font-size: 12px;
        opacity: ${props => (props.$known ? 1 : 0)};
      }
    }
  }

  .word-details {
    .part-of-speech {
      font-size: 0.8rem;
      color: #667eea;
      background: #f0f2ff;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 0.5rem;
    }

    .definition {
      font-size: 0.9rem;
      color: #7f8c8d;
      line-height: 1.4;
    }
  }
`

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }

    100% {
      transform: rotate(360deg);
    }
  }
`

const SearchContainer = styled.div`
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: center;
`

const SearchInput = styled.input`
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;

  &:focus {
    outline: none;
    border-color: #667eea;
  }

  &::placeholder {
    color: #a0a0a0;
  }
`

const Modal = styled.div<{ $isOpen: boolean }>`
  display: ${props => (props.$isOpen ? 'flex' : 'none')};
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
`

const ModalContent = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease;

  @keyframes slideUp {
    from {
      transform: translateY(20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
`

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;

  h3 {
    color: #2c3e50;
    font-size: 1.5rem;
    margin: 0;
  }
`

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #7f8c8d;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;

  &:hover {
    background: #f0f0f0;
    color: #2c3e50;
  }
`

const AddWordForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  label {
    font-weight: 600;
    color: #2c3e50;
    font-size: 0.9rem;
  }
`

const FormInput = styled.input`
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;

  &:focus {
    outline: none;
    border-color: #667eea;
  }
`

const FormSelect = styled.select`
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  background: white;
  transition: border-color 0.2s;

  &:focus {
    outline: none;
    border-color: #667eea;
  }
`

const SubmitButton = styled.button`
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
  margin-top: 0.5rem;

  &:hover {
    background: #5568d3;
  }

  &:disabled {
    background: #a0a0a0;
    cursor: not-allowed;
  }
`

const FloatingActionButton = styled.button`
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;

  &:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 30px rgba(102, 126, 234, 0.6);
  }

  &:active {
    transform: scale(0.95);
  }

  &::before {
    content: '+';
    line-height: 1;
  }
`

const Tooltip = styled.div`
  position: absolute;
  bottom: calc(100% + 8px);
  right: 0;
  background: #2c3e50;
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.85rem;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
  z-index: 1001;

  &::after {
    content: '';
    position: absolute;
    top: 100%;
    right: 16px;
    border: 6px solid transparent;
    border-top-color: #2c3e50;
  }
`

const ConfirmDialog = styled(ModalContent)`
  max-width: 400px;
  text-align: center;

  h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
  }

  p {
    color: #7f8c8d;
    margin-bottom: 1.5rem;
    line-height: 1.5;
  }
`

const DialogActions = styled.div`
  display: flex;
  gap: 1rem;
  justify-content: center;
`

const DeleteButtonWrapper = styled.div`
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;

  ${WordCard}:hover & {
    opacity: 1;
  }

  &:hover ${Tooltip} {
    opacity: 1;
  }
`

const DeleteButton = styled.button`
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #ff4d4f;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: background 0.2s, transform 0.2s;

  &:hover {
    background: #cf1322;
    transform: scale(1.1);
  }

  &::before {
    content: '×';
    font-weight: bold;
    line-height: 1;
  }
`

const PaginationContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin: 2rem 0;
`

const PaginationButton = styled.button<{ $disabled?: boolean }>`
  padding: 0.5rem 1rem;
  border: 2px solid #667eea;
  background: ${props => (props.$disabled ? '#f0f0f0' : 'white')};
  color: ${props => (props.$disabled ? '#a0a0a0' : '#667eea')};
  border-radius: 6px;
  cursor: ${props => (props.$disabled ? 'not-allowed' : 'pointer')};
  font-weight: 500;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: #667eea;
    color: white;
  }
`

const PageInfo = styled.span`
  color: #2c3e50;
  font-weight: 500;
`

const LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
const ITEMS_PER_PAGE = 100

// Language code to full name mapping
const getLanguageName = (code: string | null | undefined): string => {
  if (!code) return 'Language'
  const languageMap: Record<string, string> = {
    de: 'German',
    en: 'English',
    es: 'Spanish',
    fr: 'French',
    it: 'Italian',
    pt: 'Portuguese',
    ru: 'Russian',
    zh: 'Chinese',
    ja: 'Japanese',
    ko: 'Korean',
  }
  return languageMap[code.toLowerCase()] || code.toUpperCase()
}

// Constants for virtual scrolling
const CARD_WIDTH = 296 // 280px card + 16px gap
const CARD_HEIGHT = 140 // Approximate card height
const MIN_COLUMNS = 1
const MAX_COLUMNS = 4

// Hook to track window size for responsive grid
const useWindowSize = () => {
  const [size, setSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1200,
    height: typeof window !== 'undefined' ? window.innerHeight : 800,
  })

  useEffect(() => {
    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      })
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return size
}

// Memoized components to prevent unnecessary re-renders

interface WordCardItemProps {
  word: VocabularyLibraryWord
  onWordClick: (word: VocabularyLibraryWord) => void
  onDelete?: (word: VocabularyLibraryWord) => void
}

const WordCardItem = memo(({ word, onWordClick, onDelete }: WordCardItemProps) => {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onDelete) {
      onDelete(word)
    }
  }

  return (
    <WordCard $known={word.known} onClick={() => onWordClick(word)} data-testid={`word-card-${word.id}`}>
      {onDelete && (
        <DeleteButtonWrapper>
          <DeleteButton onClick={handleDelete} />
          <Tooltip>Remove word progress</Tooltip>
        </DeleteButtonWrapper>
      )}
      <div className="word-header">
        <div className="word">{word.word}</div>
        <div className="known-badge" />
      </div>

      <div className="word-details">
        {word.translation && <div className="definition">{word.translation}</div>}
      </div>
    </WordCard>
  )
})
WordCardItem.displayName = 'WordCardItem'

interface StatCardItemProps {
  label: string
  value: string | number
}

const StatCardItem = memo(({ label, value }: StatCardItemProps) => {
  return (
    <StatCard>
      <div className="stat-number">{value}</div>
      <div className="stat-label">{label}</div>
    </StatCard>
  )
})
StatCardItem.displayName = 'StatCardItem'

interface LevelTabItemProps {
  level: string
  active: boolean
  userKnown: number
  totalWords: number
  onClick: (level: string) => void
}

const LevelTabItem = memo(
  ({ level, active, userKnown, totalWords, onClick }: LevelTabItemProps) => {
    return (
      <LevelTab $active={active} onClick={() => onClick(level)} data-testid={`level-tab-${level}`}>
        {level}
        <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
          {userKnown} / {totalWords}
        </div>
      </LevelTab>
    )
  }
)
LevelTabItem.displayName = 'LevelTabItem'

export const VocabularyLibrary: React.FC = () => {
  const navigate = useNavigate()
  const windowSize = useWindowSize()
  const [activeLevel, setActiveLevel] = useState<string>('A1')
  const [levelData, setLevelData] = useState<VocabularyLevel | null>(null)
  const [stats, setStats] = useState<VocabularyStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(0)
  const [useVirtualScrolling, setUseVirtualScrolling] = useState(false)
  const [newWord, setNewWord] = useState('')
  const [newTranslation, setNewTranslation] = useState('')
  const [newLevel, setNewLevel] = useState('beginner')
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [deleteConfirmWord, setDeleteConfirmWord] = useState<VocabularyLibraryWord | null>(null)

  useEffect(() => {
    logger.info('VocabularyLibrary', 'Component mounted, loading vocabulary stats')
    loadStats()
  }, [])

  useEffect(() => {
    if (activeLevel) {
      logger.userAction('level-change', 'VocabularyLibrary', { level: activeLevel })
      setCurrentPage(0) // Reset to first page when level changes
      setSearchTerm('') // Clear search when changing levels
      loadLevelData(activeLevel)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLevel]) // loadLevelData is not stable and would cause infinite loop

  useEffect(() => {
    if (activeLevel) {
      const delayedSearch = setTimeout(() => {
        loadLevelData(activeLevel)
      }, 300) // Debounce search input
      return () => clearTimeout(delayedSearch)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, currentPage, activeLevel]) // loadLevelData is not stable and would cause infinite loop

  const loadStats = async () => {
    try {
      const statsData = await getVocabularyStatsApiVocabularyStatsGet()
      setStats(statsData as VocabularyStats)
    } catch (error: unknown) {
      const errorMessage = formatApiError(error, 'Failed to load vocabulary statistics')
      logger.error('VocabularyLibrary', 'Failed to load stats', { error: errorMessage })
      toast.error(errorMessage, { duration: 4000 })
    }
  }

  const loadLevelData = async (level: string) => {
    setLoading(true)
    try {
      logger.info('VocabularyLibrary', 'Loading level data', {
        level,
        searchTerm,
        currentPage,
        offset: searchTerm ? 0 : currentPage * ITEMS_PER_PAGE,
      })

      const params: {
        level: string
        targetLanguage: string
        limit: number
        search?: string
        offset?: number
      } = {
        level,
        targetLanguage: 'de',
        limit: searchTerm ? 1000 : ITEMS_PER_PAGE, // Show all results when searching
        search: searchTerm || undefined,
      }

      // Add offset separately as it might not be in the type definition
      if (!searchTerm) {
        params.offset = currentPage * ITEMS_PER_PAGE
      }

      const data = (await getVocabularyLevelApiVocabularyLibraryLevelGet(params)) as VocabularyLevel

      logger.info('VocabularyLibrary', 'Level data loaded', {
        level,
        wordCount: data.words?.length || 0,
        totalCount: data.total_count,
        knownCount: data.known_count,
      })

      // Map API response to VocabularyLibraryWord with proper type handling
      let filteredWords = (data.words ?? []).map((word, index) => ({
        ...word,
        id: word.id || word.lemma || `temp-${index}-${word.word}`, // Ensure id is always a string
        known: Boolean((word as unknown as Record<string, unknown>).is_known ?? word.known),
      })) as VocabularyLibraryWord[]

      // Client-side search filtering
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase()
        filteredWords = filteredWords.filter(
          word =>
            word.word?.toLowerCase().includes(searchLower) ||
            word.lemma?.toLowerCase().includes(searchLower) ||
            word.translation?.toLowerCase().includes(searchLower)
        )
      }

      const normalizedLevel: VocabularyLevel = {
        ...data,
        words: filteredWords,
        total_count: searchTerm ? filteredWords.length : data.total_count,
        known_count: filteredWords.filter(w => w.known).length,
      }

      setLevelData(normalizedLevel)
    } catch (error: unknown) {
      const errorMessage = formatApiError(error, `Failed to load ${level} vocabulary`)
      logger.error('VocabularyLibrary', 'Failed to load level data', { level, error: errorMessage })

      // Check for rate limiting
      if (isRateLimitError(error)) {
        const retryAfter = getRetryAfter(error)
        toast.error(`Rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`)
      } else {
        toast.error(errorMessage, { duration: 4000 })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleWordClick = useCallback(
    async (word: VocabularyLibraryWord) => {
      const newStatus = !word.known
      logger.userAction('word-toggle', 'VocabularyLibrary', {
        word: word.word,
        level: activeLevel,
        fromKnown: word.known,
        toKnown: newStatus,
      })

      // Optimistically update local state
      setLevelData(prevLevelData => {
        if (!prevLevelData) return null

        const updatedWords = prevLevelData.words.map(w =>
          w.id === word.id ? { ...w, known: newStatus } : w
        )
        const knownCount = updatedWords.filter(w => w.known).length

        return {
          ...prevLevelData,
          words: updatedWords,
          known_count: knownCount,
        }
      })

      // Update stats optimistically
      setStats(prevStats => {
        if (!prevStats) return null

        const delta = newStatus ? 1 : -1
        return {
          ...prevStats,
          total_known: prevStats.total_known + delta,
          levels: {
            ...prevStats.levels,
            [activeLevel]: {
              ...prevStats.levels[activeLevel],
              user_known: prevStats.levels[activeLevel].user_known + delta,
            },
          },
        }
      })

      try {
        await markWordKnownApiVocabularyMarkKnownPost({
          requestBody: {
            lemma: word.lemma || word.word,
            language: 'de',
            known: newStatus,
          },
        })

        logger.info('VocabularyLibrary', 'Word status updated', {
          word: word.word,
          newStatus,
        })

        toast.success(`${word.word} ${newStatus ? 'known' : 'unknown'}`)
      } catch (error: unknown) {
        const errorMessage = formatApiError(error, 'Unknown error')
        logger.error(
          'VocabularyLibrary',
          'Failed to update word status',
          {
            word: word.word,
            error: errorMessage,
          },
          error as Error
        )

        toast.error('Failed to save. Change reverted.', { duration: 4000 })

        // Revert both levelData and stats on error
        setLevelData(prev => {
          if (!prev) return null
          return {
            ...prev,
            words: prev.words.map(w => (w.id === word.id ? { ...w, known: word.known } : w)),
            known_count: prev.words.filter(w => w.known).length,
          }
        })

        setStats(prevStats => {
          if (!prevStats) return null

          const delta = newStatus ? -1 : 1 // Reverse the optimistic update
          return {
            ...prevStats,
            total_known: prevStats.total_known + delta,
            levels: {
              ...prevStats.levels,
              [activeLevel]: {
                ...prevStats.levels[activeLevel],
                user_known: prevStats.levels[activeLevel].user_known + delta,
              },
            },
          }
        })
      }
    },
    [activeLevel]
  )

  const handleBulkMark = async (known: boolean) => {
    if (!levelData) return

    logger.userAction('bulk-mark', 'VocabularyLibrary', {
      level: activeLevel,
      operation: known ? 'mark-all-known' : 'unmark-all',
      totalWords: levelData.total_count,
    })

    setBulkLoading(true)
    try {
      const result = (await bulkMarkLevelApiVocabularyLibraryBulkMarkPost({
        requestBody: {
          level: activeLevel,
          known,
          target_language: 'de',
        },
      })) as { success?: boolean; word_count?: number }

      const wordCount = result.word_count || levelData.total_count

      // Update local state immediately for instant feedback
      setLevelData({
        ...levelData,
        words: levelData.words.map(w => ({ ...w, known })),
        known_count: known ? levelData.total_count : 0,
      })

      // Update stats locally
      if (stats && stats.levels[activeLevel]) {
        const previousKnown = stats.levels[activeLevel].user_known
        const newKnown = known ? stats.levels[activeLevel].total_words : 0
        const delta = newKnown - previousKnown

        setStats({
          ...stats,
          total_known: stats.total_known + delta,
          levels: {
            ...stats.levels,
            [activeLevel]: {
              ...stats.levels[activeLevel],
              user_known: newKnown,
            },
          },
        })
      }

      toast.success(`${wordCount} words ${known ? 'marked as known' : 'unmarked'}`)

      logger.info('VocabularyLibrary', 'Bulk mark completed', {
        level: activeLevel,
        known,
        wordCount,
      })
    } catch (error: unknown) {
      const errorMessage = formatApiError(error, 'Operation failed')
      logger.error(
        'VocabularyLibrary',
        'Bulk mark operation failed',
        {
          level: activeLevel,
          known,
          error: errorMessage,
        },
        error as Error
      )

      toast.error(`Failed: ${errorMessage}`, { duration: 4000 })

      // Reload on error to get correct state from backend
      await Promise.all([loadLevelData(activeLevel), loadStats()])
    } finally {
      setBulkLoading(false)
    }
  }

  const handleAddWord = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!newWord.trim() || !newTranslation.trim()) {
      toast.error('Word and translation are required')
      return
    }

    logger.userAction('add-custom-word', 'VocabularyLibrary', {
      word: newWord,
      level: newLevel,
    })

    try {
      await createVocabularyApiVocabularyPost({
        requestBody: {
          word: newWord.trim(),
          translation: newTranslation.trim(),
          difficulty_level: newLevel,
          language: stats?.target_language || 'de',
        },
      })

      toast.success(`Added "${newWord}" to vocabulary`)
      logger.info('VocabularyLibrary', 'Custom word added', {
        word: newWord,
        level: newLevel,
      })

      // Clear form and close modal
      setNewWord('')
      setNewTranslation('')
      setNewLevel('beginner')
      setIsAddModalOpen(false)

      // Reload current level and stats
      await Promise.all([loadLevelData(activeLevel), loadStats()])
    } catch (error: unknown) {
      const errorMessage = formatApiError(error, 'Failed to add word')
      logger.error('VocabularyLibrary', 'Failed to add custom word', {
        word: newWord,
        error: errorMessage,
      })
      toast.error(errorMessage, { duration: 4000 })
    }
  }

  const handleDeleteClick = (word: VocabularyLibraryWord) => {
    setDeleteConfirmWord(word)
  }

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmWord) return

    const word = deleteConfirmWord
    setDeleteConfirmWord(null) // Close dialog

    logger.userAction('delete-word-progress', 'VocabularyLibrary', {
      word: word.word,
      lemma: word.lemma,
    })

    // Optimistically remove from UI
    setLevelData(prevLevelData => {
      if (!prevLevelData) return null

      const updatedWords = prevLevelData.words.filter(w => w.id !== word.id)
      const knownCount = updatedWords.filter(w => w.known).length

      return {
        ...prevLevelData,
        words: updatedWords,
        known_count: knownCount,
        total_count: prevLevelData.total_count - 1,
      }
    })

    // Update stats optimistically
    if (word.known) {
      setStats(prevStats => {
        if (!prevStats) return null

        return {
          ...prevStats,
          total_known: prevStats.total_known - 1,
          levels: {
            ...prevStats.levels,
            [activeLevel]: {
              ...prevStats.levels[activeLevel],
              user_known: prevStats.levels[activeLevel].user_known - 1,
            },
          },
        }
      })
    }

    try {
      const lemma = word.lemma || word.word
      // Using axios directly since generated client might not have DELETE endpoint mapped yet
      // or to ensure consistent behavior with other manual calls
      await axios.delete(`/api/vocabulary/progress/${encodeURIComponent(lemma)}`, {
        params: { language: 'de' },
        withCredentials: true
      })

      toast.success(`Removed progress for "${word.word}"`)
      logger.info('VocabularyLibrary', 'Word progress deleted', {
        word: word.word,
        lemma,
      })
    } catch (error: unknown) {
      const errorMessage = formatApiError(error, 'Failed to delete word progress')
      logger.error('VocabularyLibrary', 'Failed to delete word progress', {
        word: word.word,
        error: errorMessage,
      })

      toast.error('Failed to delete. Reverting changes.', { duration: 4000 })

      // Reload data to get correct state from backend
      await Promise.all([loadLevelData(activeLevel), loadStats()])
    }
  }

  const handleDeleteCancel = () => {
    setDeleteConfirmWord(null)
  }

  const getProgressPercentage = (level: string) => {
    if (!stats?.levels[level]) return 0
    const { total_words, user_known } = stats.levels[level]
    return total_words > 0 ? (user_known / total_words) * 100 : 0
  }

  const handleLevelChange = useCallback((level: string) => {
    setActiveLevel(level)
  }, [])

  // Calculate grid dimensions for virtual scrolling
  const gridConfig = useMemo(() => {
    const containerWidth = Math.min(windowSize.width - 64, 1200) // Account for padding
    const columnCount = Math.max(
      MIN_COLUMNS,
      Math.min(MAX_COLUMNS, Math.floor(containerWidth / CARD_WIDTH))
    )
    const rowCount = levelData?.words ? Math.ceil(levelData.words.length / columnCount) : 0

    return {
      columnCount,
      rowCount,
      containerWidth,
      containerHeight: Math.min(windowSize.height - 500, 800), // Leave space for header/controls
    }
  }, [windowSize.width, windowSize.height, levelData?.words])

  // Enable virtual scrolling for large datasets (>200 words)
  useEffect(() => {
    if (levelData && levelData.words.length > 200) {
      setUseVirtualScrolling(true)
    } else {
      setUseVirtualScrolling(false)
    }
  }, [levelData])

  // Create Grid Cell component for virtual scrolling
  type CellData = {
    words: VocabularyLibraryWord[]
    columnCount: number
    onWordClick: (word: VocabularyLibraryWord) => void
    onDelete: (word: VocabularyLibraryWord) => void
  }

  const cellData = useMemo<CellData>(() => {
    // Handle case where no words data is available
    if (!levelData?.words || levelData.words.length === 0) {
      // Return empty data instead of throwing error
      return {
        words: [],
        columnCount: gridConfig.columnCount,
        onWordClick: handleWordClick,
        onDelete: handleDeleteClick,
      }
    }

    return {
      words: levelData.words,
      columnCount: gridConfig.columnCount,
      onWordClick: handleWordClick,
      onDelete: handleDeleteClick,
    }
  }, [levelData?.words, gridConfig.columnCount, handleWordClick])

  const GridCell = useCallback((props: CellComponentProps<CellData>) => {
    const { columnIndex, rowIndex, style, words, columnCount, onWordClick, onDelete } = props

    const index = rowIndex * columnCount + columnIndex
    if (index >= words.length) return null

    const word = words[index]

    return (
      <div style={{ ...style, padding: '8px' }}>
        <WordCardItem word={word} onWordClick={onWordClick} onDelete={onDelete} />
      </div>
    )
  }, [])

  return (
    <Container>
      <BackButton onClick={() => navigate('/')} data-testid="back-to-videos">Back to Videos</BackButton>

      <Header>
        <h1>📚 Vocabulary Library</h1>
        <p>Manage your German vocabulary knowledge from A1 to C2 level</p>
      </Header>

      {stats && (
        <StatsGrid>
          <StatCardItem label="Total Words" value={stats.total_words} />
          <StatCardItem label="Words Known" value={stats.total_known} />
          <StatCardItem
            label="Progress"
            value={`${stats.total_words > 0 ? Math.round((stats.total_known / stats.total_words) * 100) : 0}%`}
          />
          <StatCardItem label="Levels Available" value={LEVELS.length} />
        </StatsGrid>
      )}

      <LevelTabs>
        {LEVELS.map(level => (
          <LevelTabItem
            key={level}
            level={level}
            active={activeLevel === level}
            userKnown={stats?.levels[level]?.user_known || 0}
            totalWords={stats?.levels[level]?.total_words || 0}
            onClick={handleLevelChange}
          />
        ))}
      </LevelTabs>

      {levelData && (
        <>
          <LevelHeader>
            <div className="level-info">
              <h2>{levelData.level} Level Vocabulary</h2>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${getProgressPercentage(levelData.level)}%` }}
                />
              </div>
              <div className="progress-text">
                {levelData.known_count} of {levelData.total_count} words known (
                {Math.round(getProgressPercentage(levelData.level))}%)
              </div>
            </div>

            <div className="level-actions">
              <Button
                $variant="primary"
                onClick={() => handleBulkMark(true)}
                disabled={bulkLoading}
              >
                {bulkLoading ? 'Loading...' : 'Mark All Known'}
              </Button>
              <Button
                $variant="danger"
                onClick={() => handleBulkMark(false)}
                disabled={bulkLoading}
              >
                {bulkLoading ? 'Loading...' : 'Unmark All'}
              </Button>
            </div>
          </LevelHeader>

          <SearchContainer>
            <SearchInput
              type="text"
              placeholder={`Search ${levelData.level} vocabulary...`}
              value={searchTerm}
              data-testid="vocabulary-search"
              onChange={e => {
                const newSearchTerm = e.target.value
                logger.userAction('search', 'VocabularyLibrary', {
                  level: levelData.level,
                  searchTerm: newSearchTerm,
                })
                setSearchTerm(newSearchTerm)
                setCurrentPage(0) // Reset to first page when searching
              }}
            />
          </SearchContainer>
        </>
      )}

      {loading ? (
        <LoadingSpinner data-testid="vocabulary-loading">
          <div className="spinner" />
        </LoadingSpinner>
      ) : levelData && levelData.words && levelData.words.length > 0 ? (
        <>
          {useVirtualScrolling ? (
            <div style={{ margin: '0 auto', maxWidth: `${gridConfig.containerWidth}px` }}>
              <Grid
                columnCount={gridConfig.columnCount}
                columnWidth={CARD_WIDTH}
                defaultHeight={gridConfig.containerHeight}
                rowCount={gridConfig.rowCount}
                rowHeight={CARD_HEIGHT}
                cellComponent={GridCell}
                cellProps={cellData}
              />
            </div>
          ) : (
            <WordsGrid>
              {levelData.words.map(word => (
                <WordCardItem
                  key={word.id}
                  word={word}
                  onWordClick={handleWordClick}
                  onDelete={handleDeleteClick}
                />
              ))}
            </WordsGrid>
          )}

          {!searchTerm && !useVirtualScrolling && levelData.total_count > ITEMS_PER_PAGE && (
            <PaginationContainer>
              <PaginationButton
                $disabled={currentPage === 0}
                onClick={() => {
                  const newPage = Math.max(0, currentPage - 1)
                  logger.userAction('pagination', 'VocabularyLibrary', {
                    action: 'previous',
                    fromPage: currentPage,
                    toPage: newPage,
                  })
                  setCurrentPage(newPage)
                }}
              >
                Previous
              </PaginationButton>

              <PageInfo>
                Page {currentPage + 1} of {Math.ceil(levelData.total_count / ITEMS_PER_PAGE)} (
                {Math.min((currentPage + 1) * ITEMS_PER_PAGE, levelData.total_count)} of{' '}
                {levelData.total_count} words)
              </PageInfo>

              <PaginationButton
                $disabled={(currentPage + 1) * ITEMS_PER_PAGE >= levelData.total_count}
                onClick={() => {
                  const newPage = currentPage + 1
                  logger.userAction('pagination', 'VocabularyLibrary', {
                    action: 'next',
                    fromPage: currentPage,
                    toPage: newPage,
                    totalPages: Math.ceil(levelData.total_count / ITEMS_PER_PAGE),
                  })
                  setCurrentPage(newPage)
                }}
              >
                Next
              </PaginationButton>
            </PaginationContainer>
          )}
        </>
      ) : levelData ? (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#7f8c8d' }}>
          <h3>No words found for {activeLevel} level</h3>
          <p>
            This level may not have vocabulary data yet, or all words may be filtered out by your
            search.
          </p>
        </div>
      ) : null}

      {/* Floating Action Button for Adding Words */}
      <FloatingActionButton onClick={() => setIsAddModalOpen(true)} title="Add test word" />

      {/* Add Word Modal */}
      <Modal $isOpen={isAddModalOpen} onClick={() => setIsAddModalOpen(false)}>
        <ModalContent onClick={e => e.stopPropagation()}>
          <ModalHeader>
            <h3>Add Custom Test Word</h3>
            <CloseButton onClick={() => setIsAddModalOpen(false)}>×</CloseButton>
          </ModalHeader>
          <AddWordForm onSubmit={handleAddWord}>
            <FormGroup>
              <label htmlFor="word">{getLanguageName(stats?.target_language)} Word</label>
              <FormInput
                id="word"
                type="text"
                placeholder={`e.g., ${stats?.target_language === 'de' ? 'Hallo' : 'Word'}`}
                value={newWord}
                onChange={e => setNewWord(e.target.value)}
                required
              />
            </FormGroup>
            <FormGroup>
              <label htmlFor="translation">{getLanguageName(stats?.translation_language)} Translation</label>
              <FormInput
                id="translation"
                type="text"
                placeholder={`e.g., ${stats?.translation_language === 'en' ? 'Hello' : 'Translation'}`}
                value={newTranslation}
                onChange={e => setNewTranslation(e.target.value)}
                required
              />
            </FormGroup>
            <FormGroup>
              <label htmlFor="level">Difficulty Level</label>
              <FormSelect id="level" value={newLevel} onChange={e => setNewLevel(e.target.value)}>
                <option value="beginner">Beginner (A1)</option>
                <option value="elementary">Elementary (A2)</option>
                <option value="intermediate">Intermediate (B1)</option>
                <option value="upper_intermediate">Upper Intermediate (B2)</option>
                <option value="advanced">Advanced (C1)</option>
                <option value="proficient">Proficient (C2)</option>
              </FormSelect>
            </FormGroup>
            <SubmitButton type="submit">Add Word</SubmitButton>
          </AddWordForm>
        </ModalContent>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <Modal $isOpen={!!deleteConfirmWord} onClick={handleDeleteCancel}>
        <ConfirmDialog onClick={e => e.stopPropagation()}>
          <h3>Remove Word Progress?</h3>
          <p>
            Are you sure you want to remove your progress for <strong>{deleteConfirmWord?.word}</strong>?
            <br />
            This will reset it to unknown status.
          </p>
          <DialogActions>
            <Button $variant="secondary" onClick={handleDeleteCancel}>
              Cancel
            </Button>
            <Button $variant="danger" onClick={handleDeleteConfirm}>
              Remove Progress
            </Button>
          </DialogActions>
        </ConfirmDialog>
      </Modal>
    </Container>
  )
}
