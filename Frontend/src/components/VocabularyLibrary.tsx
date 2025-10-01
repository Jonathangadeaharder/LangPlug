import React, { useState, useEffect } from 'react'
import { toast } from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import {
  bulkMarkLevelApiVocabularyLibraryBulkMarkPost,
  getVocabularyLevelApiVocabularyLibraryLevelGet,
  getVocabularyStatsApiVocabularyStatsGet,
  markWordKnownApiVocabularyMarkKnownPost,
} from '@/client/services.gen'
import { logger } from '@/services/logger'
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

export const VocabularyLibrary: React.FC = () => {
  const navigate = useNavigate()
  const [activeLevel, setActiveLevel] = useState<string>('A1')
  const [levelData, setLevelData] = useState<VocabularyLevel | null>(null)
  const [stats, setStats] = useState<VocabularyStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [bulkLoading, setBulkLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(0)

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
      const errorMessage = error?.body?.detail || error?.message || 'Failed to load vocabulary statistics'
      logger.error('VocabularyLibrary', 'Failed to load stats', { error: errorMessage })
      toast.error(errorMessage, {
        duration: 4000
      })
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
          id: word.concept_id,
          known: Boolean(word.known),
        })),
      }

      setLevelData(normalizedLevel)
    } catch (error: any) {
      const errorMessage = error?.body?.detail || error?.message || `Failed to load ${level} vocabulary`
      logger.error('VocabularyLibrary', 'Failed to load level data', { level, error: errorMessage })

      // Check for rate limiting
      if (error?.status === 429) {
        const retryAfter = error?.headers?.['retry-after'] || 60
        toast.error(`Rate limit exceeded. Please wait ${retryAfter} seconds before trying again.`)
      } else {
        toast.error(errorMessage, {
          duration: 4000
        })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleWordClick = async (word: VocabularyLibraryWord) => {
    const newStatus = !word.known
    logger.userAction('word-toggle', 'VocabularyLibrary', {
      word: word.word,
      level: activeLevel,
      fromKnown: word.known,
      toKnown: newStatus
    })

    try {
      await markWordKnownApiVocabularyMarkKnownPost({
        requestBody: {
          concept_id: word.concept_id,
          known: newStatus,
        },
      })

      // Update local state
      if (levelData) {
        const updatedWords = levelData.words.map(w =>
          w.id === word.id ? { ...w, known: newStatus } : w
        )
        const knownCount = updatedWords.filter(w => w.known).length

        setLevelData({
          ...levelData,
          words: updatedWords,
          known_count: knownCount
        })

        logger.info('VocabularyLibrary', 'Word status updated successfully', {
          word: word.word,
          newStatus,
          newKnownCount: knownCount,
          totalWords: updatedWords.length
        })
      }

      // Reload stats
      await loadStats()

      toast.success(`${word.word} marked as ${newStatus ? 'known' : 'unknown'}`)
    } catch (error: any) {
      logger.error('VocabularyLibrary', 'Failed to update word status', {
        word: word.word,
        error: error?.message || 'Unknown error'
      }, error as Error)

      // Show error with context
      const errorMessage = error?.body?.detail || 'Failed to update word status'
      toast.error(`${errorMessage}. The change was not saved.`, {
        duration: 4000
      })

      // Revert visual state
      setLevelData((prev) => {
        if (!prev) return null
        return {
          ...prev,
          words: prev.words.map((w) =>
            w.concept_id === word.concept_id ? { ...w, known: word.known } : w
          ),
        }
      })
    }
  }

  const handleBulkMark = async (known: boolean) => {
    logger.userAction('bulk-mark', 'VocabularyLibrary', {
      level: activeLevel,
      operation: known ? 'mark-all-known' : 'unmark-all',
      wordCount: levelData?.words.length || 0
    })

    setBulkLoading(true)
    try {
      const result = await bulkMarkLevelApiVocabularyLibraryBulkMarkPost({
        requestBody: {
          level: activeLevel,
          known,
          target_language: 'de',
        },
      }) as { success?: boolean; message?: string }
      logger.info('VocabularyLibrary', 'Bulk mark operation completed', {
        level: activeLevel,
        known,
        result
      })
      toast.success(result.message || `Successfully ${known ? 'marked all words as known' : 'unmarked all words'}`)

      // Reload data
      await loadLevelData(activeLevel)
      await loadStats()
    } catch (error: any) {
      const errorMessage = error?.body?.detail || error?.message || 'Operation failed'
      logger.error('VocabularyLibrary', 'Bulk mark operation failed', {
        level: activeLevel,
        known,
        error: errorMessage
      }, error as Error)

      toast.error(`Failed to ${known ? 'mark all as known' : 'unmark all words'}: ${errorMessage}`, {
        duration: 4000
      })
    } finally {
      setBulkLoading(false)
    }
  }

  const getProgressPercentage = (level: string) => {
    if (!stats?.levels[level]) return 0
    const { total_words, user_known } = stats.levels[level]
    return total_words > 0 ? (user_known / total_words) * 100 : 0
  }

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
          <StatCard>
            <div className="stat-number">{stats.total_words}</div>
            <div className="stat-label">Total Words</div>
          </StatCard>
          <StatCard>
            <div className="stat-number">{stats.total_known}</div>
            <div className="stat-label">Words Known</div>
          </StatCard>
          <StatCard>
            <div className="stat-number">
              {stats.total_words > 0 ? Math.round((stats.total_known / stats.total_words) * 100) : 0}%
            </div>
            <div className="stat-label">Progress</div>
          </StatCard>
          <StatCard>
            <div className="stat-number">{LEVELS.length}</div>
            <div className="stat-label">Levels Available</div>
          </StatCard>
        </StatsGrid>
      )}

      <LevelTabs>
        {LEVELS.map(level => (
          <LevelTab
            key={level}
            $active={activeLevel === level}
            onClick={() => setActiveLevel(level)}
          >
            {level}
            {stats && (
              <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
                {stats.levels[level]?.user_known || 0} / {stats.levels[level]?.total_words || 0}
              </div>
            )}
          </LevelTab>
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
          <WordsGrid>
            {levelData.words.map(word => (
              <WordCard
                key={word.id}
                $known={word.known}
                onClick={() => handleWordClick(word)}
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
            ))}
          </WordsGrid>

          {!searchTerm && levelData.total_count > ITEMS_PER_PAGE && (
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
