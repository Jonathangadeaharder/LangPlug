import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { ArrowLeftIcon } from '@heroicons/react/24/solid'
import { Container, NetflixButton, ErrorMessage } from '@/styles/GlobalStyles'
import { handleApiError } from '@/services/api'
import {
  getVideosApiVideosGet,
  prepareEpisodeApiProcessPrepareEpisodePost,
} from '@/client/services.gen'
import { useTaskProgress } from '@/hooks/useTaskProgress'
import { ProcessingScreen } from '@/components/ProcessingScreen'
import type { VideoInfo } from '@/types'

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

const PipelineContainer = styled.div`
  padding: 40px 0;
  max-width: 800px;
  margin: 0 auto;
`

const PipelineHeader = styled.div`
  text-align: center;
  margin-bottom: 30px;
`

const PipelineTitle = styled.h1`
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 16px;
  color: white;
`

const PipelineDescription = styled.p`
  font-size: 18px;
  color: #b3b3b3;
  margin-bottom: 24px;
  line-height: 1.6;
`

const EpisodeInfo = styled.div`
  background: rgba(0, 0, 0, 0.6);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
`

const EpisodeTitle = styled.h2`
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 12px;
  color: white;
`

const EpisodeDetails = styled.div`
  display: flex;
  gap: 20px;
  color: #b3b3b3;
  font-size: 16px;
`

const ActionButton = styled(NetflixButton)`
  width: 100%;
  padding: 16px;
  font-size: 18px;
  margin-top: 20px;
`

export const PipelineProgress: React.FC = () => {
  const { series, episode: episodeParam } = useParams<{ series: string; episode: string }>()
  const navigate = useNavigate()

  const [episode, setEpisode] = useState<VideoInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isRunning, setIsRunning] = useState(false)

  const { progress, status, error: progressError, startMonitoring } = useTaskProgress()

  useEffect(() => {
    const loadEpisode = async () => {
      try {
        setLoading(true)
        const videoList = await getVideosApiVideosGet()
        const seriesEpisodes = videoList.filter(video => video.series === series)

        // Find the specific episode
        const foundEpisode = seriesEpisodes.find(ep =>
          ep.episode === episodeParam
        )

        if (foundEpisode) {
          setEpisode(foundEpisode)
        } else {
          setError('Episode not found')
        }
      } catch (err) {
        handleApiError(err, 'PipelineProgress.loadData')
        setError('Failed to load episode')
      } finally {
        setLoading(false)
      }
    }

    if (series && episodeParam) {
      loadEpisode()
    }
  }, [series, episodeParam])

  const handleStartPipeline = async () => {
    if (!episode) return

    try {
      setIsRunning(true)
      const result = await prepareEpisodeApiProcessPrepareEpisodePost({
        requestBody: {
          video_path: episode.path,
        },
      }) as { task_id: string }
      startMonitoring(result.task_id)
    } catch (error) {
      handleApiError(error, 'PipelineProgress.unknownError')
      setIsRunning(false)
    }
  }

  const handleViewEpisode = () => {
    if (episode && series) {
      navigate(`/learn/${encodeURIComponent(series)}/${encodeURIComponent(episode.episode)}`, {
        state: { videoInfo: episode }
      })
    }
  }

  const handleBack = () => {
    if (series) {
      navigate(`/episodes/${encodeURIComponent(series)}`)
    } else {
      navigate('/')
    }
  }

  if (loading) {
    return (
      <Container>
        <div style={{ padding: '40px 0', textAlign: 'center', color: 'white' }}>
          Loading episode...
        </div>
      </Container>
    )
  }

  if (error || !episode) {
    return (
      <Container>
        <ErrorMessage>{error || 'Episode not found'}</ErrorMessage>
      </Container>
    )
  }

  return (
    <>
      <Header>
        <Container>
          <Nav>
            <BackButton onClick={handleBack}>
              <ArrowLeftIcon className="w-5 h-5" />
              Back to Episodes
            </BackButton>
            <Logo>LangPlug</Logo>
          </Nav>
        </Container>
      </Header>

      <PipelineContainer>
        <PipelineHeader>
          <PipelineTitle>Processing Pipeline</PipelineTitle>
          <PipelineDescription>
            Automatically transcribe, filter, and translate your episode for the best learning experience.
          </PipelineDescription>
        </PipelineHeader>

        <EpisodeInfo>
          <EpisodeTitle>{episode.title}</EpisodeTitle>
          <EpisodeDetails>
            <span>Series: {episode.series}</span>
            <span>•</span>
            <span>Season {episode.season}, Episode {episode.episode}</span>
          </EpisodeDetails>
        </EpisodeInfo>

        {!isRunning ? (
          <ActionButton onClick={handleStartPipeline}>
            Start Full Processing Pipeline
          </ActionButton>
        ) : (
          <>
            {status !== 'idle' && <ProcessingScreen status={{ status, progress, message: progressError || undefined, current_step: status }} />}

            {status === 'completed' && (
              <ActionButton onClick={handleViewEpisode}>
                Start Learning
              </ActionButton>
            )}

            {(progressError || status === 'failed' || status === 'error') && (
              <ErrorMessage>
                Failed to process episode: {progressError}
                <br />
                <NetflixButton
                  variant="secondary"
                  onClick={handleStartPipeline}
                  style={{ marginTop: '10px' }}
                >
                  Retry
                </NetflixButton>
              </ErrorMessage>
            )}
          </>
        )}
      </PipelineContainer>
    </>
  )
}
