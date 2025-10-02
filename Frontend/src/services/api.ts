import { toast } from 'react-hot-toast'
import { logger } from './logger'
import { OpenAPI } from '@/client/core/OpenAPI'
import { ApiError } from '@/client/core/ApiError'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

OpenAPI.BASE = API_BASE_URL
OpenAPI.HEADERS = {
  'Content-Type': 'application/json'
}
OpenAPI.TOKEN = async () => localStorage.getItem('authToken') ?? ''

export { OpenAPI }

export const buildVideoStreamUrl = (series: string, episode: string): string => {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const token = localStorage.getItem('authToken')
  const url = `${base}/api/videos/${encodeURIComponent(series)}/${encodeURIComponent(episode)}`

  // Add token as query parameter for video streaming (ReactPlayer can't send headers)
  if (token) {
    return `${url}?token=${encodeURIComponent(token)}`
  }

  return url
}

export const handleApiError = (error: unknown, context: string) => {
  let status: number | undefined
  let message = 'An unexpected error occurred'

  if (error instanceof ApiError) {
    status = error.status
    const body = error.body as { detail?: string }
    if (body?.detail && typeof body.detail === 'string') {
      message = body.detail
    } else if (typeof error.statusText === 'string' && error.statusText) {
      message = error.statusText
    }
  } else if (typeof error === 'object' && error !== null) {
    const errObj = error as {
      status?: number
      message?: string
      response?: { status?: number; data?: { detail?: string } | unknown }
    }
    status = errObj.response?.status ?? errObj.status
    const detail = (errObj.response?.data as { detail?: string })?.detail
    if (typeof detail === 'string' && detail) {
      message = detail
    } else if (typeof errObj.message === 'string' && errObj.message) {
      message = errObj.message
    }
  } else if (error instanceof Error) {
    message = error.message
  }

  logger.error(`API error in ${context}`, String(error))

  if (status === 401) {
    toast.error('Authentication required')
  } else if (status === 403) {
    toast.error('Access denied')
  } else if (status === 404) {
    toast.error('Resource not found')
  } else if (status && status >= 500) {
    toast.error('Server error. Please try again later.')
  } else {
    toast.error(message)
  }

  throw error
}
