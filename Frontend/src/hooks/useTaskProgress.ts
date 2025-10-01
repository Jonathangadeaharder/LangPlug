import { useState, useEffect, useCallback, useRef } from 'react'
import { getTaskProgressApiProcessProgressTaskIdGet } from '@/client/services.gen'
import type { ProcessingStatus } from '@/types'

type TaskState = 'idle' | 'monitoring' | 'processing' | 'completed' | 'failed' | 'error'

export const useTaskProgress = () => {
  const [taskId, setTaskId] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [status, setStatus] = useState<TaskState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState<boolean>(false)
  const [result, setResult] = useState<any>(null)
  const intervalRef = useRef<number | null>(null)

  const clearTimer = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const poll = useCallback(async (currentTaskId?: string) => {
    const idToUse = currentTaskId || taskId
    if (!idToUse) return
    try {
      const res = await getTaskProgressApiProcessProgressTaskIdGet({ taskId: idToUse }) as ProcessingStatus & {
        result?: unknown
      }
      setProgress(res?.progress ?? 0)

      if (res?.status === 'processing') {
        setStatus('processing')
      } else if (res?.status === 'completed') {
        setStatus('completed')
        setIsComplete(true)
        setResult(res?.result ?? null)
        clearTimer()
      } else if (res?.status === 'failed' || res?.status === 'error') {
        setStatus('failed') // Always set to 'failed' for both 'failed' and 'error' statuses
        setError((res as any)?.error || res?.message || 'Processing failed')
        clearTimer()
      } else {
        // Unknown status: keep processing
        setStatus('processing')
      }
    } catch (e: any) {
      setStatus('error')
      setError(e?.message || 'Network error')
      clearTimer()
    }
  }, [taskId, clearTimer])

  const startMonitoring = useCallback((id: string) => {
    setTaskId(id)
    setStatus('monitoring')
    setIsComplete(false)
    setError(null)
    setProgress(0)
    setResult(null)
    clearTimer()
    // Start polling every 2 seconds
    intervalRef.current = setInterval(() => poll(id), 2000) as any
  }, [poll, clearTimer])

  const stopMonitoring = useCallback(() => {
    clearTimer()
    setStatus('idle')
  }, [clearTimer])

  const reset = useCallback(() => {
    clearTimer()
    setTaskId(null)
    setProgress(0)
    setStatus('idle')
    setError(null)
    setIsComplete(false)
    setResult(null)
  }, [clearTimer])

  useEffect(() => {
    return () => {
      clearTimer()
    }
  }, [clearTimer])

  return {
    taskId,
    progress,
    status,
    error,
    isComplete,
    result,
    startMonitoring,
    stopMonitoring,
    reset,
  }
}
