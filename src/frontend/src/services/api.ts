/**
 * API Configuration and Utilities
 * 
 * Uses the OpenAPI-generated client for type-safe API calls.
 * 
 * Usage:
 * - Import generated services from @/client/services.gen
 * - Use handleApiError for consistent error handling
 * - Use buildVideoStreamUrl for video streaming URLs
 */
import { toast } from 'react-hot-toast'
import { logger } from './logger'
import { OpenAPI } from '@/client/core/OpenAPI'
import { ApiError } from '@/client/core/ApiError'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Configure OpenAPI client
OpenAPI.BASE = API_BASE_URL
OpenAPI.HEADERS = {
  'Content-Type': 'application/json',
}
OpenAPI.TOKEN = async () => localStorage.getItem('authToken') ?? ''

export { OpenAPI, ApiError }

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
  let isNetworkError = false

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
      code?: string
      response?: { status?: number; data?: { detail?: string } | unknown }
    }
    status = errObj.response?.status ?? errObj.status
    const detail = (errObj.response?.data as { detail?: string })?.detail

    // Check for network errors
    if (
      errObj.code === 'ECONNREFUSED' ||
      errObj.code === 'ERR_NETWORK' ||
      errObj.message?.includes('Network Error') ||
      errObj.message?.includes('Failed to fetch')
    ) {
      isNetworkError = true
      message =
        'Cannot connect to server. Please check your internet connection or ensure the backend is running.'
    } else if (typeof detail === 'string' && detail) {
      message = detail
    } else if (typeof errObj.message === 'string' && errObj.message) {
      message = errObj.message
    }
  } else if (error instanceof Error) {
    message = error.message
    // Check for network/timeout errors in Error objects
    if (message.includes('timeout') || message.includes('ETIMEDOUT')) {
      message = 'Request timed out. The server is taking too long to respond.'
    } else if (message.includes('Network') || message.includes('fetch')) {
      isNetworkError = true
      message = 'Network error. Please check your connection.'
    }
  }

  logger.error(`API error in ${context}`, String(error))

  // Show appropriate error messages
  if (isNetworkError) {
    toast.error(message, { duration: 5000 })
  } else if (status === 401) {
    toast.error('Session expired. Please log in again.')
  } else if (status === 403) {
    toast.error('Access denied. You do not have permission to perform this action.')
  } else if (status === 404) {
    toast.error('Resource not found. The requested item may have been deleted.')
  } else if (status === 422) {
    toast.error('Invalid input. Please check your data and try again.')
  } else if (status === 429) {
    toast.error('Too many requests. Please wait a moment and try again.')
  } else if (status === 500) {
    toast.error('Internal server error. Our team has been notified.')
  } else if (status === 502 || status === 503) {
    toast.error('Service temporarily unavailable. Please try again in a few moments.')
  } else if (status === 504) {
    toast.error('Gateway timeout. The server is taking too long to respond.')
  } else if (status && status >= 500) {
    toast.error('Server error. Please try again later.')
  } else {
    toast.error(message)
  }

  throw error
}
