import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import { ChevronRightIcon, PlayIcon } from '@heroicons/react/24/solid'
import { toast } from 'react-hot-toast'
import { Container, Grid, NetflixButton, ErrorMessage } from '@/styles/GlobalStyles'
import { videoService, handleApiError } from '@/services/api'
import { useAuthStore } from '@/store/useAuthStore'
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
  justify-content: space-between;
  align-items: center;
`

const Logo = styled.h1`
  color: #e50914;
  font-size: 28px;
  font-weight: bold;
`

const NavLinks = styled.div`
  display: flex;
  align-items: center;
  gap: 24px;
`

const NavLink = styled.button`
  color: #b3b3b3;
  background: none;
  border: none;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.3s ease;
  
  &:hover {
    color: white;
  }
`

const UserSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
`

const UserName = styled.span`
  font-weight: 500;
`

const LogoutButton = styled(NetflixButton)`
  padding: 8px 16px;
  font-size: 14px;
`

const Hero = styled.section`
  padding: 80px 0 40px;
  text-align: center;
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.7) 0%,
    rgba(0, 0, 0, 0.3) 50%,
    rgba(0, 0, 0, 0.7) 100%
  );
`

const HeroTitle = styled.h1`
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 16px;
  color: white;
  
  @media (max-width: 768px) {
    font-size: 32px;
  }
`

const HeroSubtitle = styled.p`
  font-size: 20px;
  color: #b3b3b3;
  margin-bottom: 32px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  
  @media (max-width: 768px) {
    font-size: 16px;
  }
`

const Section = styled.section`
  padding: 40px 0;
`

const SectionTitle = styled.h2`
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 24px;
  color: white;
`

const SeriesCard = styled.div`
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.6));
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  
  &:hover {
    transform: scale(1.05);
    border-color: #e50914;
    box-shadow: 0 8px 25px rgba(229, 9, 20, 0.3);
  }
`

const CardImage = styled.div<{ $bgImage?: string }>`
  height: 200px;
  background: ${props => props.$bgImage ? `url(${props.$bgImage})` : 'linear-gradient(135deg, #e50914, #b00610)'};
  background-size: cover;
  background-position: center;
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

const PlayButton = styled.div`
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
  transition: all 0.3s ease;
  
  ${SeriesCard}:hover & {
    background: white;
    transform: scale(1.1);
  }
`

const CardContent = styled.div`
  padding: 20px;
`

const CardTitle = styled.h3`
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 8px;
  color: white;
  display: flex;
  align-items: center;
  gap: 8px;
`

const CardMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`

const EpisodeCount = styled.span`
  color: #b3b3b3;
  font-size: 14px;
`

const SubtitleBadge = styled.span<{ $hasSubtitles: boolean }>`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: ${props => props.$hasSubtitles ? '#46d369' : '#e87c03'};
  color: white;
`

const CardDescription = styled.p`
  color: #b3b3b3;
  font-size: 14px;
  line-height: 1.4;
`

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
`

const EmptyState = styled.div`
  text-align: center;
  padding: 60px 20px;
  color: #b3b3b3;
  
  h3 {
    font-size: 24px;
    margin-bottom: 16px;
    color: white;
  }
  
  p {
    font-size: 16px;
    margin-bottom: 24px;
  }
`

export const VideoSelection: React.FC = () => {
  const [videos, setVideos] = useState<VideoInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    loadVideos()
  }, [])

  const loadVideos = async () => {
    try {
      setLoading(true)
      const videoList = await videoService.getVideos()
      setVideos(videoList)
    } catch (error) {
      handleApiError(error)
      setError('Failed to load videos')
    } finally {
      setLoading(false)
    }
  }

  const handleSeriesSelect = (series: string) => {
    navigate(`/episodes/${encodeURIComponent(series)}`)
  }

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
      toast.success('Logged out successfully')
    } catch (error) {
      handleApiError(error)
    }
  }

  // Group videos by series (guard against undefined in tests)
  const seriesList = (videos ?? []).reduce((acc, video) => {
    const existing = acc.find(s => s.name === video.series)
    if (existing) {
      existing.episodes.push(video)
    } else {
      acc.push({
        name: video.series,
        episodes: [video],
        hasSubtitles: video.has_subtitles,
        description: `German TV series perfect for language learning`
      })
    }
    return acc
  }, [] as Array<{
    name: string
    episodes: VideoInfo[]
    hasSubtitles: boolean
    description: string
  }>)

  return (
    <>
      <Header>
        <Container>
          <Nav>
            <Logo>LangPlug</Logo>
            <NavLinks>
              <NavLink onClick={() => navigate('/vocabulary')}>
                📚 Vocabulary Library
              </NavLink>
            </NavLinks>
            <UserSection>
              <UserName>Welcome, {user?.username}</UserName>
              <LogoutButton variant="secondary" onClick={handleLogout} data-testid="logout-button">
                Logout
              </LogoutButton>
            </UserSection>
          </Nav>
        </Container>
      </Header>

      <Hero>
        <Container>
          <HeroTitle>Learn German Through TV Shows</HeroTitle>
          <HeroSubtitle>
            Watch your favorite series while improving your German vocabulary with our interactive learning system
          </HeroSubtitle>
        </Container>
      </Hero>

      <Section>
        <Container>
          <SectionTitle>Available Series</SectionTitle>
          
          {loading && (
            <LoadingContainer>
              <div className="loading-spinner" />
            </LoadingContainer>
          )}
          
          {error && <ErrorMessage>{error}</ErrorMessage>}
          
          {!loading && !error && seriesList.length === 0 && (
            <EmptyState>
              <h3>No Series Available</h3>
              <p>No video content has been added yet. Please check back later.</p>
              <NetflixButton onClick={loadVideos} data-testid="refresh-videos-button">Refresh</NetflixButton>
            </EmptyState>
          )}
          
          {!loading && !error && seriesList.length > 0 && (
            <Grid columns={3}>
              {seriesList.map((series) => (
                <SeriesCard
                  key={series.name}
                  onClick={() => handleSeriesSelect(series.name)}
                  data-testid={`series-card-${series.name.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  <CardImage>
                    <PlayButton>
                      <PlayIcon className="w-6 h-6 text-gray-800" />
                    </PlayButton>
                  </CardImage>
                  
                  <CardContent>
                    <CardTitle>
                      {series.name}
                      <ChevronRightIcon className="w-5 h-5" />
                    </CardTitle>
                    
                    <CardMeta>
                      <EpisodeCount>
                        {series.episodes.length} episode{series.episodes.length !== 1 ? 's' : ''}
                      </EpisodeCount>
                      <SubtitleBadge $hasSubtitles={series.hasSubtitles}>
                        {series.hasSubtitles ? 'Subtitles' : 'Auto-Generate'}
                      </SubtitleBadge>
                    </CardMeta>
                    
                    <CardDescription>{series.description}</CardDescription>
                  </CardContent>
                </SeriesCard>
              ))}
            </Grid>
          )}
        </Container>
      </Section>
    </>
  )
}