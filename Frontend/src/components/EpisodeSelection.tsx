import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { ArrowLeftIcon, PlayIcon, ClockIcon, CheckCircleIcon } from '@heroicons/react/24/solid'
import { toast } from 'react-hot-toast'
import { Container, NetflixButton, ErrorMessage } from '@/styles/GlobalStyles'
import { handleApiError } from '@/services/api'
import {
  filterSubtitlesApiProcessFilterSubtitlesPost,
  getTaskProgressApiProcessProgressTaskIdGet,
  getVideosApiVideosGet,
  translateSubtitlesApiProcessTranslateSubtitlesPost,
} from '@/client/services.gen'
import { useAuthStore } from '@/store/useAuthStore'
import type { VideoInfo, ProcessingStatus } from '@/types'

const Header = styled.header`
  padding: 20px 0;
  background: rgba(0, 0, 0, 0.9);
  position: sticky;
  top: 0;
  z-index: 100;
`

const Nav = styled.nav`
  display: flex;
  align-items: center;
  gap: 24px;
`

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: white;
  border: none;
  font-size: 16px;
  cursor: pointer;
  transition: color 0.3s ease;

  &:hover {
    color: #e50914;
  }
`

const Logo = styled.h1`
  color: #e50914;
  font-size: 28px;
  font-weight: bold;
`

const SeriesHeader = styled.section`
  padding: 40px 0;
  text-align: center;
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.8) 0%,
    rgba(0, 0, 0, 0.4) 50%,
    rgba(0, 0, 0, 0.8) 100%
  );
`

const SeriesTitle = styled.h1`
  font-size: 42px;
  font-weight: bold;
  margin-bottom: 16px;
  color: white;

  @media (max-width: 768px) {
    font-size: 28px;
  }
`

const SeriesInfo = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 24px;
  color: #b3b3b3;
  font-size: 16px;
  margin-bottom: 24px;

  @media (max-width: 768px) {
    flex-direction: column;
    gap: 12px;
  }
`

const InfoItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
`

const SeriesDescription = styled.p`
  font-size: 18px;
  color: #b3b3b3;
  max-width: 800px;
  margin: 0 auto 32px;
  line-height: 1.6;
`

const EpisodeGrid = styled.div`
  display: grid;
  gap: 24px;
  max-width: 1000px;
  margin: 0 auto;
`

const EpisodeCard = styled.div`
  display: grid;
  grid-template-columns: 200px 1fr auto;
  gap: 20px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid transparent;

  &:hover {
    background: rgba(0, 0, 0, 0.8);
    border-color: #e50914;
    transform: translateY(-2px);
  }

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 16px;
  }
`

const EpisodeThumbnail = styled.div`
  height: 120px;
  background: linear-gradient(135deg, #e50914, #b00610);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
  }
`

const PlayIconOverlay = styled.div`
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
`

const EpisodeInfo = styled.div`
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
`

const EpisodeTitle = styled.h3`
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
  color: white;
`

const EpisodeNumber = styled.span`
  color: #e50914;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
`

const EpisodeMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #b3b3b3;
`

const EpisodeDescription = styled.p`
  color: #b3b3b3;
  font-size: 14px;
  line-height: 1.4;
`

const EpisodeActions = styled.div`
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
`

const PlayButton = styled(NetflixButton)`
  padding: 12px 20px;
  font-size: 14px;
  min-width: 120px;
`

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
`

export const EpisodeSelection: React.FC = () => {
  const { series } = useParams<{ series: string }>()
  const [episodes, setEpisodes] = useState<VideoInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [processingTasks, setProcessingTasks] = useState<Set<string>>(new Set())
  const [progressData, setProgressData] = useState<Record<string, ProcessingStatus>>({})

  const { user: _user } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (series) {
      loadEpisodes()
    }
  }, [series])

  const loadEpisodes = async () => {
    try {
      setLoading(true)
      const videoList = await getVideosApiVideosGet()
      const seriesEpisodes = videoList.filter(video => video.series === series)

      // Sort episodes by episode number
      const sortedEpisodes = seriesEpisodes.sort((a, b) => {
        const aNum = parseInt(a.episode.match(/\d+/)?.[0] || '0')
        const bNum = parseInt(b.episode.match(/\d+/)?.[0] || '0')
        return aNum - bNum
      })

      setEpisodes(sortedEpisodes)
    } catch (error) {
      handleApiError(error, 'EpisodeSelection.loadEpisodes')
      setError('Failed to load episodes')
    } finally {
      setLoading(false)
    }
  }

  // Poll for progress updates with exponential backoff
  const pollProgress = async (taskId: string, episodePath: string, taskType: 'transcription' | 'filtering' | 'translation' = 'transcription') => {
    const maxAttempts = 120 // Reduced from 180, with longer intervals
    let attempts = 0
    let pollInterval = 5000 // Start at 5 seconds

    const poll = async () => {
      try {
        const progress = await getTaskProgressApiProcessProgressTaskIdGet({ taskId }) as ProcessingStatus
        setProgressData(prev => ({ ...prev, [episodePath]: progress }))

        if (progress.status === 'completed') {
          handleTaskComplete(episodePath, taskType)
          return
        }

        if (progress.status === 'error') {
          handleTaskError(episodePath, progress.message || 'Unknown error')
          return
        }

        attempts++
        if (attempts < maxAttempts) {
          // Exponential backoff: increase interval each time, max 30 seconds
          pollInterval = Math.min(pollInterval * 1.5, 30000)
          setTimeout(poll, pollInterval)
        } else {
          handleTaskError(episodePath, 'Processing timeout')
        }
      } catch (error) {
        console.error('Error polling progress:', error)
        attempts++
        if (attempts < maxAttempts) {
          // Exponential backoff on error
          pollInterval = Math.min(pollInterval * 1.5, 30000)
          setTimeout(poll, pollInterval)
        } else {
          handleTaskError(episodePath, 'Failed to get progress')
        }
      }
    }

    poll()
  }

  // Handle progress completion
  const handleTaskComplete = (episodePath: string, taskType: 'transcription' | 'filtering' | 'translation') => {
    // Remove from processing tasks
    setProcessingTasks(prev => {
      const newSet = new Set(prev)
      newSet.delete(episodePath)
      return newSet
    })

    // Clear progress data
    setProgressData(prev => {
      const newData = { ...prev }
      delete newData[episodePath]
      return newData
    })

    if (taskType === 'transcription') {
      toast.success('Episode is ready for learning!', { id: 'transcription' })
      // Update episode status
      setEpisodes(prev => prev.map(ep =>
        ep.path === episodePath ? { ...ep, has_subtitles: true } : ep
      ))
    } else if (taskType === 'filtering') {
      toast.success('Episode filtering completed!', { id: 'filtering' })
    } else if (taskType === 'translation') {
      toast.success('Episode translation completed!', { id: 'translation' })
    }
  }

  // Handle progress error
  const handleTaskError = (episodePath: string, errorMessage: string) => {
    // Remove from processing tasks
    setProcessingTasks(prev => {
      const newSet = new Set(prev)
      newSet.delete(episodePath)
      return newSet
    })

    // Clear progress data
    setProgressData(prev => {
      const newData = { ...prev }
      delete newData[episodePath]
      return newData
    })

    toast.error(`Processing failed: ${errorMessage}`, { id: 'transcription' })
  }

  const handlePlayEpisode = async (episode: VideoInfo) => {
    // Navigate directly to the chunked learning flow
    navigate(`/learn/${encodeURIComponent(episode.series)}/${encodeURIComponent(episode.episode)}`, {
      state: { videoInfo: episode }
    })
  }

  const _handleFilterEpisode = async (episode: VideoInfo) => {
    try {
      setProcessingTasks(prev => new Set(prev).add(episode.path))
      toast.loading('Filtering episode subtitles...', { id: 'filtering' })

      // Start filtering
      const result = await filterSubtitlesApiProcessFilterSubtitlesPost({
        requestBody: { video_path: episode.path },
      }) as { task_id: string }

      // Start polling progress
      pollProgress(result.task_id, episode.path, 'filtering')
    } catch (error) {
      setProcessingTasks(prev => {
        const newSet = new Set(prev)
        newSet.delete(episode.path)
        return newSet
      })
      handleApiError(error, 'EpisodeSelection.startFiltering')
      toast.error('Failed to start filtering', { id: 'filtering' })
    }
  }

  const _handleTranslateEpisode = async (episode: VideoInfo) => {
    try {
      setProcessingTasks(prev => new Set(prev).add(episode.path))
      toast.loading('Translating episode subtitles...', { id: 'translating' })

      // Start translation (for now, we'll use German as source and English as target)
      // In a real implementation, these would be configurable
      const result = await translateSubtitlesApiProcessTranslateSubtitlesPost({
        requestBody: {
          video_path: episode.path,
          source_lang: 'de',
          target_lang: 'en',
        },
      }) as { task_id: string }

      // Start polling progress
      pollProgress(result.task_id, episode.path, 'translation')
    } catch (error) {
      setProcessingTasks(prev => {
        const newSet = new Set(prev)
        newSet.delete(episode.path)
        return newSet
      })
      handleApiError(error, 'EpisodeSelection.startTranslation')
      toast.error('Failed to start translation', { id: 'translating' })
    }
  }

  const _handleRunFullPipeline = (episode: VideoInfo) => {
    // Navigate to the dedicated pipeline page
    navigate(`/pipeline/${encodeURIComponent(series || '')}/${encodeURIComponent(episode.episode)}`)
  }

  const getEpisodeStatus = (episode: VideoInfo) => {
    if (processingTasks.has(episode.path)) return 'processing'
    if (episode.has_subtitles) return 'ready'
    return 'available'
  }

  const _getStatusText = (status: string) => {
    switch (status) {
      case 'ready': return 'Ready to Learn'
      case 'processing': return 'Processing...'
      default: return 'Will Process'
    }
  }

  const _getProgressData = (episode: VideoInfo): ProcessingStatus | null => {
    return progressData[episode.path] || null
  }

  if (!series) {
    return <ErrorMessage>Series not found</ErrorMessage>
  }

  return (
    <>
      <Header>
        <Container>
          <Nav>
            <BackButton onClick={() => navigate('/')}>
              <ArrowLeftIcon className="w-5 h-5" />
              Back to Series
            </BackButton>
            <Logo>LangPlug</Logo>
          </Nav>
        </Container>
      </Header>

      <SeriesHeader>
        <Container>
          <SeriesTitle>{decodeURIComponent(series)}</SeriesTitle>
          <SeriesInfo>
            <InfoItem>
              <CheckCircleIcon className="w-5 h-5" />
              {episodes.length} Episodes
            </InfoItem>
            <InfoItem>
              <ClockIcon className="w-5 h-5" />
              ~5 min segments
            </InfoItem>
            <InfoItem>
              German Learning
            </InfoItem>
          </SeriesInfo>
          <SeriesDescription>
            Learn German through engaging TV episodes. Our interactive system will help you master new vocabulary
            by focusing on the most challenging words for your level.
          </SeriesDescription>
        </Container>
      </SeriesHeader>

      <Container>
        <div style={{ padding: '40px 0' }}>
          {loading && (
            <LoadingContainer>
              <div className="loading-spinner" />
            </LoadingContainer>
          )}

          {error && <ErrorMessage>{error}</ErrorMessage>}

          {!loading && !error && episodes.length > 0 && (
            <EpisodeGrid>
              {episodes.map((episode, index) => {
                const status = getEpisodeStatus(episode)
                const isProcessing = status === 'processing'

                return (
                  <EpisodeCard key={episode.path}>
                    <EpisodeThumbnail>
                      <PlayIconOverlay>
                        <PlayIcon className="w-4 h-4 text-gray-800" />
                      </PlayIconOverlay>
                    </EpisodeThumbnail>

                    <EpisodeInfo>
                      <EpisodeNumber>Episode {index + 1}</EpisodeNumber>
                      <EpisodeTitle>{episode.title}</EpisodeTitle>
                      <EpisodeMeta>
                        <span>Season {episode.season}</span>
                        <span>•</span>
                        <span>German Audio</span>
                        {episode.has_subtitles && (
                          <>
                            <span>•</span>
                            <span>Subtitles Ready</span>
                          </>
                        )}
                      </EpisodeMeta>
                      <EpisodeDescription>
                        Interactive German learning experience with vocabulary games
                        and subtitle-based comprehension exercises.
                      </EpisodeDescription>
                    </EpisodeInfo>

                    <EpisodeActions>
                      <PlayButton
                        onClick={() => handlePlayEpisode(episode)}
                        disabled={isProcessing}
                      >
                        <PlayIcon className="w-5 h-5 mr-2" />
                        Play
                      </PlayButton>
                    </EpisodeActions>
                  </EpisodeCard>
                )
              })}
            </EpisodeGrid>
          )}
        </div>
      </Container>
    </>
  )
}
