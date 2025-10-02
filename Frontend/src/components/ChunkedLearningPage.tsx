import React from 'react'
import { useLocation } from 'react-router-dom'
import { ChunkedLearningFlow } from './ChunkedLearningFlow'
import type { VideoInfo } from '@/types'

export const ChunkedLearningPage: React.FC = () => {
  const location = useLocation()
  let videoInfo = location.state?.videoInfo as VideoInfo

  // Fallback for E2E tests: check sessionStorage
  // This allows tests to inject videoInfo without fighting React Router's state management
  if (!videoInfo && typeof window !== 'undefined' && sessionStorage) {
    try {
      const testVideoInfo = sessionStorage.getItem('testVideoInfo')
      if (testVideoInfo) {
        videoInfo = JSON.parse(testVideoInfo) as VideoInfo
      }
    } catch (error) {
      console.warn('Failed to parse test videoInfo from sessionStorage', error)
    }
  }

  if (!videoInfo) {
    return (
      <div style={{
        color: 'white',
        padding: '40px',
        textAlign: 'center',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#141414'
      }}>
        <h1>Video information not found. Please go back and select an episode.</h1>
      </div>
    )
  }

  return <ChunkedLearningFlow videoInfo={videoInfo} chunkDurationMinutes={0.5} />
}
