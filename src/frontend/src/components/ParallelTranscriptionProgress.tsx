/**
 * Parallel Transcription Progress Component
 *
 * Displays real-time progress for parallel transcription jobs.
 * Polls job status API and updates progress bar.
 */
import React, { useEffect, useState, useCallback } from 'react'
import './ParallelTranscriptionProgress.css'

interface JobStatus {
  job_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  started_at: number
  updated_at: number
  completed_at?: number
  error?: string
  result?: {
    srt_path: string
    chunks_processed: number
    video_path: string
    language: string
  }
}

interface ParallelTranscriptionProgressProps {
  jobId: string
  onComplete?: (result: JobStatus['result']) => void
  onError?: (error: string) => void
  className?: string
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const POLL_INTERVAL = 1000 // Poll every second

const ParallelTranscriptionProgress: React.FC<ParallelTranscriptionProgressProps> = ({
  jobId,
  onComplete,
  onError,
  className = '',
}) => {
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [elapsedTime, setElapsedTime] = useState<number>(0)

  const fetchJobStatus = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/processing/transcribe-parallel/status/${jobId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      )

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Job not found')
        }
        throw new Error(`Failed to fetch job status: ${response.statusText}`)
      }

      const data: JobStatus = await response.json()
      setJobStatus(data)

      // Handle completion
      if (data.status === 'completed' && onComplete && data.result) {
        onComplete(data.result)
      }

      // Handle failure
      if (data.status === 'failed' && onError && data.error) {
        onError(data.error)
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      if (onError) {
        onError(errorMessage)
      }
    }
  }, [jobId, onComplete, onError])

  // Poll job status
  useEffect(() => {
    fetchJobStatus()

    const interval = setInterval(() => {
      fetchJobStatus()
    }, POLL_INTERVAL)

    return () => clearInterval(interval)
  }, [fetchJobStatus])

  // Update elapsed time
  useEffect(() => {
    if (!jobStatus || jobStatus.status === 'completed' || jobStatus.status === 'failed') {
      return
    }

    const interval = setInterval(() => {
      const elapsed = Date.now() / 1000 - jobStatus.started_at
      setElapsedTime(elapsed)
    }, 100)

    return () => clearInterval(interval)
  }, [jobStatus])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getStatusColor = (status: JobStatus['status']): string => {
    switch (status) {
      case 'queued':
        return '#2196f3'
      case 'processing':
        return '#ff9800'
      case 'completed':
        return '#4caf50'
      case 'failed':
        return '#f44336'
      default:
        return '#9e9e9e'
    }
  }

  if (error) {
    return (
      <div className={`transcription-progress error ${className}`}>
        <div className="error-icon">✕</div>
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      </div>
    )
  }

  if (!jobStatus) {
    return (
      <div className={`transcription-progress loading ${className}`}>
        <div className="loading-spinner"></div>
        <p>Loading job status...</p>
      </div>
    )
  }

  const isActive = jobStatus.status === 'queued' || jobStatus.status === 'processing'
  const progress = Math.min(100, Math.max(0, jobStatus.progress))

  return (
    <div className={`transcription-progress ${jobStatus.status} ${className}`}>
      <div className="progress-header">
        <div className="status-badge" style={{ backgroundColor: getStatusColor(jobStatus.status) }}>
          {jobStatus.status.toUpperCase()}
        </div>
        {isActive && (
          <div className="elapsed-time">
            {formatTime(elapsedTime)}
          </div>
        )}
      </div>

      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{
            width: `${progress}%`,
            backgroundColor: getStatusColor(jobStatus.status),
          }}
        >
          <span className="progress-percentage">{progress.toFixed(0)}%</span>
        </div>
      </div>

      <div className="progress-message">{jobStatus.message}</div>

      {jobStatus.status === 'completed' && jobStatus.result && (
        <div className="completion-details">
          <div className="detail-item">
            <strong>Chunks Processed:</strong> {jobStatus.result.chunks_processed}
          </div>
          <div className="detail-item">
            <strong>SRT File:</strong> {jobStatus.result.srt_path}
          </div>
          <div className="detail-item">
            <strong>Duration:</strong>{' '}
            {formatTime((jobStatus.completed_at || 0) - jobStatus.started_at)}
          </div>
        </div>
      )}

      {jobStatus.status === 'failed' && jobStatus.error && (
        <div className="error-details">
          <strong>Error:</strong> {jobStatus.error}
        </div>
      )}

      <div className="job-info">
        <small>Job ID: {jobStatus.job_id}</small>
      </div>
    </div>
  )
}

export default ParallelTranscriptionProgress
