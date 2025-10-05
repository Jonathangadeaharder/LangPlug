import React, { useState, useEffect, memo, useCallback, useMemo } from 'react'
import { toast } from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { Grid } from 'react-window'
import type { CellComponentProps } from 'react-window'
import {
  bulkMarkLevelApiVocabularyLibraryBulkMarkPost,
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

  &:before {
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
  background: ${props => props.$active ? '#667eea' : 'transparent'};
  color: ${props => props.$active ? 'white' : '#2c3e50'};
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: ${props => props.$active ? '#667eea' : '#e9ecef'};
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
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);

  .level-info {
    h2 {
      color: #2c3e50;
      margin: 0 0 0.5rem 0;
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
        `;
      case 'danger':
        return `
          background: #ff4d4f;
          color: white;
          &:hover { background: #d32f2f; }
        `;
      default:
        return `
          background: #f0f0f0;
          color: #2c3e50;
          &:hover { background: #e0e0e0; }
        `;
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
  border: 2px solid ${props => props.$known ? '#52c41a' : '#e9ecef'};
  border-radius: 12px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;

  &:hover {
    border-color: ${props => props.$known ? '#389e0d' : '#667eea'};
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
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
      background: ${props => props.$known ? '#52c41a' : '#dee2e6'};
      display: flex;
      align-items: center;
      justify-content: center;

      &::after {
        content: '✓';
        color: white;
        font-size: 12px;
        opacity: ${props => props.$known ? 1 : 0};
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
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
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
  background: ${props => props.$disabled ? '#f0f0f0' : 'white'};
  color: ${props => props.$disabled ? '#a0a0a0' : '#667eea'};
  border-radius: 6px;
  cursor: ${props => props.$disabled ? 'not-allowed' : 'pointer'};
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

const LEVELS = ['A1', 'A2', 'B1', 'B2']
const ITEMS_PER_PAGE = 100

// Constants for virtual scrolling
const CARD_WIDTH = 296  // 280px card + 16px gap
const CARD_HEIGHT = 140  // Approximate card height
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
}

const WordCardItem = memo(({ word, onWordClick }: WordCardItemProps) => {
  return (
    <WordCard
      $known={word.known}
      onClick={() => onWordClick(word)}
    >
      <div className="word-header">
        <div className="word">{word.word}</div>
        <div className="known-badge" />
      </div>

      <div className="word-details">
        {word.translation && (
          <div className="definition">{word.translation}</div>
        )}
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

const LevelTabItem = memo(({ level, active, userKnown, totalWords, onClick }: LevelTabItemProps) => {
  return (
    <LevelTab
      $active={active}
      onClick={() => onClick(level)}
    >
      {level}
      <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
        {userKnown} / {totalWords}
      </div>
    </LevelTab>
  )
})
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
  }, [activeLevel])

  useEffect(() => {
    if (activeLevel) {
      const delayedSearch = setTimeout(() => {
        loadLevelData(activeLevel)
      }, 300) // Debounce search input
      return () => clearTimeout(delayedSearch)
    }
  }, [searchTerm, currentPage, activeLevel])

  const loadStats = async () => {
    try {
      const statsData = await getVocabularyStatsApiVocabularyStatsGet()
      setStats(statsData)
    } catch (error: any) {
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
        offset: searchTerm ? 0 : currentPage * ITEMS_PER_PAGE
      })

      const params: any = {
        level,
        targetLanguage: 'de',
        limit: searchTerm ? 1000 : ITEMS_PER_PAGE, // Show all results when searching
        search: searchTerm || undefined,
      }

      // Add offset separately as it might not be in the type definition
      if (!searchTerm) {
        params.offset = currentPage * ITEMS_PER_PAGE
      }

      const data = await getVocabularyLevelApiVocabularyLibraryLevelGet(params) as VocabularyLevel

      logger.info('VocabularyLibrary', 'Level data loaded', {
        level,
        wordCount: data.words?.length || 0,
        totalCount: data.total_count,
        knownCount: data.known_count
      })

      const normalizedLevel: VocabularyLevel = {
        ...data,
        words: (data.words ?? []).map(word => ({
          ...word,
          id: word.id || word.lemma,  // Use database id or lemma as fallback
          known: Boolean(word.known),
        })),
      }

      setLevelData(normalizedLevel)
    } catch (error: any) {
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

  const handleWordClick = useCallback(async (word: VocabularyLibraryWord) => {
    const newStatus = !word.known
    logger.userAction('word-toggle', 'VocabularyLibrary', {
      word: word.word,
      level: activeLevel,
      fromKnown: word.known,
      toKnown: newStatus
    })

    // Optimistically update local state
    setLevelData((prevLevelData) => {
      if (!prevLevelData) return null

      const updatedWords = prevLevelData.words.map(w =>
        w.id === word.id ? { ...w, known: newStatus } : w
      )
      const knownCount = updatedWords.filter(w => w.known).length

      return {
        ...prevLevelData,
        words: updatedWords,
        known_count: knownCount
      }
    })

    // Update stats optimistically
    setStats((prevStats) => {
      if (!prevStats) return null

      const delta = newStatus ? 1 : -1
      return {
        ...prevStats,
        total_known: prevStats.total_known + delta,
        levels: {
          ...prevStats.levels,
          [activeLevel]: {
            ...prevStats.levels[activeLevel],
            user_known: prevStats.levels[activeLevel].user_known + delta
          }
        }
      }
    })

    try {
      await markWordKnownApiVocabularyMarkKnownPost({
        requestBody: {
          lemma: word.lemma,
          word: word.word,
          language: 'de',
          known: newStatus,
        },
      })

      logger.info('VocabularyLibrary', 'Word status updated', {
        word: word.word,
        lemma: word.lemma,
        newStatus
      })

      toast.success(`${word.word} ${newStatus ? 'known' : 'unknown'}`)
    } catch (error: any) {
      const errorMessage = formatApiError(error, 'Unknown error')
      logger.error('VocabularyLibrary', 'Failed to update word status', {
        word: word.word,
        error: errorMessage
      }, error as Error)

      toast.error('Failed to save. Change reverted.', { duration: 4000 })

      // Revert both levelData and stats on error
      setLevelData((prev) => {
        if (!prev) return null
        return {
          ...prev,
          words: prev.words.map((w) =>
            w.id === word.id ? { ...w, known: word.known } : w
          ),
          known_count: prev.words.filter(w => w.known).length
        }
      })

      setStats((prevStats) => {
        if (!prevStats) return null

        const delta = newStatus ? -1 : 1  // Reverse the optimistic update
        return {
          ...prevStats,
          total_known: prevStats.total_known + delta,
          levels: {
            ...prevStats.levels,
            [activeLevel]: {
              ...prevStats.levels[activeLevel],
              user_known: prevStats.levels[activeLevel].user_known + delta
            }
          }
        }
      })
    }
  }, [activeLevel])

  const handleBulkMark = async (known: boolean) => {
    if (!levelData) return

    logger.userAction('bulk-mark', 'VocabularyLibrary', {
      level: activeLevel,
      operation: known ? 'mark-all-known' : 'unmark-all',
      totalWords: levelData.total_count
    })

    setBulkLoading(true)
    try {
      const result = await bulkMarkLevelApiVocabularyLibraryBulkMarkPost({
        requestBody: {
          level: activeLevel,
          known,
          target_language: 'de',
        },
      }) as { success?: boolean; word_count?: number }

      const wordCount = result.word_count || levelData.total_count

      // Update local state immediately for instant feedback
      setLevelData({
        ...levelData,
        words: levelData.words.map(w => ({ ...w, known })),
        known_count: known ? levelData.total_count : 0
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
              user_known: newKnown
            }
          }
        })
      }

      toast.success(`${wordCount} words ${known ? 'marked as known' : 'unmarked'}`)

      logger.info('VocabularyLibrary', 'Bulk mark completed', { level: activeLevel, known, wordCount })
    } catch (error: any) {
      const errorMessage = formatApiError(error, 'Operation failed')
      logger.error('VocabularyLibrary', 'Bulk mark operation failed', {
        level: activeLevel,
        known,
        error: errorMessage
      }, error as Error)

      toast.error(`Failed: ${errorMessage}`, { duration: 4000 })

      // Reload on error to get correct state from backend
      await Promise.all([loadLevelData(activeLevel), loadStats()])
    } finally {
      setBulkLoading(false)
    }
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
    const rowCount = levelData ? Math.ceil(levelData.words.length / columnCount) : 0

    return {
      columnCount,
      rowCount,
      containerWidth,
      containerHeight: Math.min(windowSize.height - 500, 800) // Leave space for header/controls
    }
  }, [windowSize.width, windowSize.height, levelData?.words.length])

  // Enable virtual scrolling for large datasets (>200 words)
  useEffect(() => {
    if (levelData && levelData.words.length > 200) {
      setUseVirtualScrolling(true)
    } else {
      setUseVirtualScrolling(false)
    }
  }, [levelData?.words.length])

  // Create Grid Cell component for virtual scrolling
  type CellData = {
    words: VocabularyLibraryWord[]
    columnCount: number
    onWordClick: (word: VocabularyLibraryWord) => void
  }

  const cellData = useMemo<CellData>(() => {
    // Fail fast if words array is missing - this should never happen
    // because we only render the grid when levelData exists (see line 864)
    if (!levelData?.words) {
      throw new Error(`Vocabulary grid rendered without words data for level ${activeLevel}`)
    }

    return {
      words: levelData.words,
      columnCount: gridConfig.columnCount,
      onWordClick: handleWordClick
    }
  }, [levelData?.words, gridConfig.columnCount, handleWordClick, activeLevel])

  const GridCell = useCallback((props: CellComponentProps<CellData>) => {
    const { columnIndex, rowIndex, style, words, columnCount, onWordClick } = props

    const index = rowIndex * columnCount + columnIndex
    if (index >= words.length) return null

    const word = words[index]

    return (
      <div style={{...style, padding: '8px'}}>
        <WordCardItem
          word={word}
          onWordClick={onWordClick}
        />
      </div>
    )
  }, [])

  return (
    <Container>
      <BackButton onClick={() => navigate('/')}>
        Back to Videos
      </BackButton>

      <Header>
        <h1>📚 Vocabulary Library</h1>
        <p>Manage your German vocabulary knowledge from A1 to B2 level</p>
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
                {levelData.known_count} of {levelData.total_count} words known
                ({Math.round(getProgressPercentage(levelData.level))}%)
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
              onChange={(e) => {
                const newSearchTerm = e.target.value
                logger.userAction('search', 'VocabularyLibrary', {
                  level: levelData.level,
                  searchTerm: newSearchTerm
                })
                setSearchTerm(newSearchTerm)
                setCurrentPage(0) // Reset to first page when searching
              }}
            />
          </SearchContainer>
        </>
      )}

      {loading ? (
        <LoadingSpinner>
          <div className="spinner" />
        </LoadingSpinner>
      ) : levelData ? (
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
                    toPage: newPage
                  })
                  setCurrentPage(newPage)
                }}
              >
                Previous
              </PaginationButton>

              <PageInfo>
                Page {currentPage + 1} of {Math.ceil(levelData.total_count / ITEMS_PER_PAGE)}
                {' '}({Math.min((currentPage + 1) * ITEMS_PER_PAGE, levelData.total_count)} of {levelData.total_count} words)
              </PageInfo>

              <PaginationButton
                $disabled={(currentPage + 1) * ITEMS_PER_PAGE >= levelData.total_count}
                onClick={() => {
                  const newPage = currentPage + 1
                  logger.userAction('pagination', 'VocabularyLibrary', {
                    action: 'next',
                    fromPage: currentPage,
                    toPage: newPage,
                    totalPages: Math.ceil(levelData.total_count / ITEMS_PER_PAGE)
                  })
                  setCurrentPage(newPage)
                }}
              >
                Next
              </PaginationButton>
            </PaginationContainer>
          )}
        </>
      ) : null}
    </Container>
  )
}
