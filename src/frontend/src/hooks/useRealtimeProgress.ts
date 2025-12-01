/**
 * Real-time Progress Hook
 *
 * Professional progress tracking using HTTP polling.
 * Uses cookie-based authentication which is incompatible with WebSocket.
 *
 * Features:
 * - HTTP polling for progress updates (2 second interval)
 * - Clean state management
 * - Type-safe progress data
 * - Automatic cleanup on completion or unmount
 *
 * Usage:
 * ```tsx
 * const {
 *   startMonitoring,
 *   stopMonitoring,
 *   progress,
 *   status,
 *   message,
 *   isComplete,
 *   error,
 * } = useRealtimeProgress()
 *
 * // Start monitoring a task
 * startMonitoring(taskId)
 *
 * // Component automatically receives updates
 * <ProgressBar value={progress} />
 * <StatusText>{message}</StatusText>
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import { getTaskProgressApiProcessProgressTaskIdGet } from '@/client/services.gen'
import { logger } from '@/services/logger'
import type { ProcessingStatus } from '@/types'

// Connection state
type ConnectionMethod = 'websocket' | 'polling' | 'disconnected'
type TaskState = 'idle' | 'connecting' | 'processing' | 'completed' | 'failed'

// Configuration
const POLLING_INTERVAL_MS = 2000

export interface RealtimeProgressState {
  taskId: string | null
  progress: number
  status: TaskState
  currentStep: string
  message: string
  error: string | null
  isComplete: boolean
  connectionMethod: ConnectionMethod
  result: unknown
}

export interface RealtimeProgressActions {
  startMonitoring: (taskId: string) => void
  stopMonitoring: () => void
  reset: () => void
}

export type UseRealtimeProgressReturn = RealtimeProgressState & RealtimeProgressActions

/**
 * Hook for real-time task progress monitoring
 *
 * Provides HTTP polling-based progress updates.
 * Handles connection management and state cleanup.
 */
export function useRealtimeProgress(): UseRealtimeProgressReturn {
  // State
  const [taskId, setTaskId] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [status, setStatus] = useState<TaskState>('idle')
  const [currentStep, setCurrentStep] = useState<string>('')
  const [message, setMessage] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState<boolean>(false)
  const [connectionMethod, setConnectionMethod] = useState<ConnectionMethod>('disconnected')
  const [result, setResult] = useState<unknown>(null)

  // Refs for cleanup
  const pollingIntervalRef = useRef<number | null>(null)
  const currentTaskIdRef = useRef<string | null>(null)

  // Cleanup functions
  const clearPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
  }, [])

  const cleanup = useCallback(() => {
    clearPolling()
    setConnectionMethod('disconnected')
  }, [clearPolling])

  // Handle progress update from any source
  const handleProgressUpdate = useCallback(
    (data: ProcessingStatus & { result?: unknown }) => {
      setProgress(data.progress ?? 0)
      setCurrentStep(data.current_step ?? '')
      setMessage(data.message ?? '')

      if (data.status === 'processing') {
        setStatus('processing')
      } else if (data.status === 'completed') {
        setStatus('completed')
        setIsComplete(true)
        // Store the entire response as result for vocabulary data access
        setResult(data)
        cleanup()
      } else if (data.status === 'failed' || data.status === 'error') {
        setStatus('failed')
        setError(
          (data as ProcessingStatus & { error?: string }).error ||
            data.message ||
            'Processing failed'
        )
        cleanup()
      }
    },
    [cleanup]
  )

  // HTTP polling fallback
  const poll = useCallback(async () => {
    const id = currentTaskIdRef.current
    if (!id) return

    try {
      const res = (await getTaskProgressApiProcessProgressTaskIdGet({
        taskId: id,
      })) as ProcessingStatus & { result?: unknown }

      logger.debug('Progress', 'Poll response', {
        status: res.status,
        progress: res.progress,
        hasVocabulary: !!res.vocabulary,
        vocabularyCount: res.vocabulary?.length,
      })

      handleProgressUpdate(res)
    } catch (e) {
      logger.error('Progress', 'Polling error', { error: String(e) })
      // Don't fail immediately on network errors - might be transient
    }
  }, [handleProgressUpdate])

  const startPolling = useCallback(() => {
    clearPolling()
    setConnectionMethod('polling')
    logger.debug('Progress', 'Starting HTTP polling fallback')

    // Initial poll
    poll()

    // Start interval
    pollingIntervalRef.current = window.setInterval(poll, POLLING_INTERVAL_MS)
  }, [clearPolling, poll])

  // WebSocket connection
  // NOTE: This app uses cookie-based authentication (HttpOnly cookies).
  // WebSocket cannot access cookies, so we fall back to HTTP polling for progress updates.
  // This is more reliable and avoids issues with stale localStorage tokens.
  const connectWebSocket = useCallback(() => {
    // Cookie-based auth: WebSocket cannot use HttpOnly cookies, use polling instead
    logger.debug('Progress', 'Using HTTP polling for progress updates (cookie-based auth)')
    startPolling()
  }, [startPolling])

  // Start monitoring a task
  const startMonitoring = useCallback(
    (id: string) => {
      // Reset state
      setTaskId(id)
      currentTaskIdRef.current = id
      setProgress(0)
      setStatus('connecting')
      setCurrentStep('')
      setMessage('Initializing...')
      setError(null)
      setIsComplete(false)
      setResult(null)

      // Clean up any existing connections
      cleanup()

      // Start HTTP polling for progress updates
      connectWebSocket()
    },
    [cleanup, connectWebSocket]
  )

  // Stop monitoring
  const stopMonitoring = useCallback(() => {
    cleanup()
    currentTaskIdRef.current = null
    setStatus('idle')
  }, [cleanup])

  // Reset all state
  const reset = useCallback(() => {
    cleanup()
    currentTaskIdRef.current = null
    setTaskId(null)
    setProgress(0)
    setStatus('idle')
    setCurrentStep('')
    setMessage('')
    setError(null)
    setIsComplete(false)
    setResult(null)
  }, [cleanup])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [cleanup])

  return {
    taskId,
    progress,
    status,
    currentStep,
    message,
    error,
    isComplete,
    connectionMethod,
    result,
    startMonitoring,
    stopMonitoring,
    reset,
  }
}
