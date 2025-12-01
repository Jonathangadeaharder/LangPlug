import React, { useState, useEffect } from 'react'
import axios from 'axios'
import styled from 'styled-components'
import { OpenAPI } from '@/services/api'

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #141414 0%, #1a1a1a 100%);
  color: white;
  padding: 20px;
`

const LoadingContent = styled.div`
  text-align: center;
  max-width: 600px;
`

const Logo = styled.h1`
  font-size: 48px;
  font-weight: bold;
  color: #e50914;
  margin-bottom: 20px;
`

const LoadingText = styled.p`
  font-size: 18px;
  color: #b3b3b3;
  margin-bottom: 30px;
  line-height: 1.5;
`

const ProgressDots = styled.div`
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
`

const Dot = styled.div<{ $delay: number }>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #e50914;
  animation: pulse 1.4s infinite ease-in-out both;
  animation-delay: ${props => props.$delay}s;

  @keyframes pulse {
    0%,
    80%,
    100% {
      transform: scale(0);
      opacity: 0.5;
    }

    40% {
      transform: scale(1);
      opacity: 1;
    }
  }
`

const StatusText = styled.div`
  font-size: 14px;
  color: #666;
  margin-top: 30px;
`

const ProgressBar = styled.div`
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
  margin: 20px auto;
`

const ProgressFill = styled.div<{ $progress: number }>`
  height: 100%;
  width: ${props => props.$progress}%;
  background: linear-gradient(90deg, #e50914 0%, #ff2d3a 100%);
  transition: width 0.3s ease;
  border-radius: 4px;
`

const RetryButton = styled.button`
  background: #e50914;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 20px;
  transition: background 0.2s;

  &:hover {
    background: #f40612;
  }

  &:active {
    transform: scale(0.98);
  }
`

const ErrorText = styled.p`
  color: #f44;
  font-size: 16px;
  margin: 20px 0;
`

const HelpText = styled.div`
  font-size: 14px;
  color: #888;
  margin-top: 30px;
  line-height: 1.6;

  ul {
    text-align: left;
    margin: 10px auto;
    max-width: 400px;
    padding-left: 20px;
  }

  li {
    margin: 8px 0;
  }
`

interface BackendReadinessCheckProps {
  children: React.ReactNode
}

export const BackendReadinessCheck: React.FC<BackendReadinessCheckProps> = ({ children }) => {
  const [isReady, setIsReady] = useState(false)
  const [message, setMessage] = useState('Initializing server...')
  const [attemptCount, setAttemptCount] = useState(0)
  const [hasError, setHasError] = useState(false)
  const [errorDetails, setErrorDetails] = useState('')
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let mounted = true
    let timeoutId: NodeJS.Timeout

    const check = async () => {
      if (!mounted) return

      try {
        const response = await axios.get(`${OpenAPI.BASE}/readiness`, {
          validateStatus: () => true
        })

        if (!mounted) return

        if (response.status === 200) {
          const data = response.data
          setMessage(data.message || 'Server is ready!')
          setProgress(100)
          setIsReady(true)
          setHasError(false)
          return
        } else if (response.status === 503) {
          const data = response.data
          setMessage(data.message || 'Services are still initializing. Please wait...')
          setAttemptCount(prev => prev + 1)
          setProgress(prev => Math.min(prev + 5, 90))
          setHasError(false)
        } else {
          setMessage('Unexpected server response. Retrying...')
          setAttemptCount(prev => prev + 1)
          setProgress(prev => Math.min(prev + 2, 80))
        }
      } catch (error) {
        if (!mounted) return
        setMessage('Waiting for backend server to start...')
        setAttemptCount(prev => {
          const newCount = prev + 1
          if (newCount > 30) {
            setHasError(true)
            setErrorDetails('Cannot connect to backend server. Please ensure the server is running.')
          }
          return newCount
        })
        setProgress(prev => Math.min(prev + 3, 70))
      }

      // Schedule next check
      timeoutId = setTimeout(check, 2000)
    }

    check()

    return () => {
      mounted = false
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [])

  const handleRetry = () => {
    setAttemptCount(0)
    setHasError(false)
    setErrorDetails('')
    setProgress(0)
    setMessage('Retrying connection...')
    // Polling loop is already running or will pick up the state change
  }

  if (!isReady) {
    return (
      <LoadingContainer>
        <LoadingContent>
          <Logo>LangPlug</Logo>
          <LoadingText>
            {message}
            {attemptCount > 5 && !hasError && (
              <>
                <br />
                <br />
                This may take 5-10 minutes on first run while AI models are downloaded.
              </>
            )}
          </LoadingText>

          {hasError ? (
            <>
              <ErrorText>{errorDetails}</ErrorText>
              <HelpText>
                <strong>Troubleshooting steps:</strong>
                <ul>
                  <li>Ensure the backend server is running on port 8000</li>
                  <li>Check that no firewall is blocking the connection</li>
                  <li>Verify the backend URL is correctly configured</li>
                  <li>Try refreshing the page or clicking retry below</li>
                </ul>
              </HelpText>
              <RetryButton onClick={handleRetry}>Retry Connection</RetryButton>
            </>
          ) : (
            <>
              <ProgressBar>
                <ProgressFill $progress={progress} />
              </ProgressBar>
              <ProgressDots>
                <Dot $delay={0} />
                <Dot $delay={0.2} />
                <Dot $delay={0.4} />
              </ProgressDots>
              <StatusText>
                {progress > 0 && `${progress}% • `}
                Attempt {attemptCount}{' '}
                {attemptCount > 10 && '(This is taking longer than usual...)'}
              </StatusText>
            </>
          )}
        </LoadingContent>
      </LoadingContainer>
    )
  }

  return <>{children}</>
}
