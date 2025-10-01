import { AxiosRequestConfig, AxiosResponse } from 'axios'
import { OpenAPI } from '@/client/core/OpenAPI'
import { ApiError } from '@/client/core/ApiError'
import { logger } from './logger'

// Token refresh endpoint
const refreshAccessToken = async (): Promise<string | null> => {
  const refreshToken = localStorage.getItem('refresh_token')

  if (!refreshToken) {
    logger.warn('auth-interceptor', 'No refresh token available')
    return null
  }

  try {
    const response = await fetch(`${OpenAPI.BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (response.ok) {
      const data = await response.json()
      const newAccessToken = data.access_token

      // Store the new access token
      localStorage.setItem('access_token', newAccessToken)
      localStorage.setItem('authToken', newAccessToken) // Legacy key

      logger.info('auth-interceptor', 'Token refreshed successfully')
      return newAccessToken
    } else {
      logger.error('auth-interceptor', `Token refresh failed: ${response.status}`)
      return null
    }
  } catch (error) {
    logger.error('auth-interceptor', 'Error refreshing token', error)
    return null
  }
}

// Track if we're currently refreshing to prevent multiple refresh attempts
let isRefreshing = false
let refreshPromise: Promise<string | null> | null = null

// Request interceptor to add auth token
export const authRequestInterceptor = async (config: AxiosRequestConfig): Promise<AxiosRequestConfig> => {
  // Get the current access token
  const accessToken = localStorage.getItem('access_token') || localStorage.getItem('authToken')

  if (accessToken) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${accessToken}`
  }

  return config
}

// Response interceptor to handle 401 errors and refresh token
export const authResponseInterceptor = async (response: AxiosResponse): Promise<AxiosResponse> => {
  // If response is successful, just return it
  if (response.status !== 401) {
    return response
  }

  // If we're already refreshing, wait for that to complete
  if (isRefreshing) {
    if (refreshPromise) {
      const newToken = await refreshPromise
      if (newToken) {
        // Retry the original request with the new token
        const originalConfig = response.config
        if (originalConfig) {
          originalConfig.headers = originalConfig.headers || {}
          originalConfig.headers['Authorization'] = `Bearer ${newToken}`

          // Retry the request
          try {
            const retryResponse = await fetch(originalConfig.url!, {
              method: originalConfig.method || 'GET',
              headers: originalConfig.headers as Record<string, string>,
              body: originalConfig.data ? JSON.stringify(originalConfig.data) : undefined,
            })

            return {
              ...response,
              status: retryResponse.status,
              statusText: retryResponse.statusText,
              data: await retryResponse.json(),
            } as AxiosResponse
          } catch (error) {
            logger.error('auth-interceptor', 'Retry after refresh failed', error)
          }
        }
      }
    }
    return response
  }

  // Start token refresh
  isRefreshing = true
  refreshPromise = refreshAccessToken()

  try {
    const newToken = await refreshPromise

    if (newToken) {
      // Retry the original request with the new token
      const originalConfig = response.config
      if (originalConfig) {
        originalConfig.headers = originalConfig.headers || {}
        originalConfig.headers['Authorization'] = `Bearer ${newToken}`

        // Retry the request
        try {
          const retryResponse = await fetch(originalConfig.url!, {
            method: originalConfig.method || 'GET',
            headers: originalConfig.headers as Record<string, string>,
            body: originalConfig.data ? JSON.stringify(originalConfig.data) : undefined,
          })

          return {
            ...response,
            status: retryResponse.status,
            statusText: retryResponse.statusText,
            data: await retryResponse.json(),
          } as AxiosResponse
        } catch (error) {
          logger.error('auth-interceptor', 'Retry after refresh failed', error)
        }
      }
    } else {
      // Token refresh failed - clear tokens and redirect to login
      logger.warn('auth-interceptor', 'Token refresh failed, clearing auth')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('authToken')
      localStorage.removeItem('user_id')

      // Redirect to login (if not already there)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
  } finally {
    isRefreshing = false
    refreshPromise = null
  }

  return response
}

// Setup function to register interceptors
export const setupAuthInterceptors = () => {
  // Register request interceptor
  OpenAPI.interceptors.request.use(authRequestInterceptor)

  // Register response interceptor
  OpenAPI.interceptors.response.use(authResponseInterceptor)

  // Also update the TOKEN function to use the new tokens
  OpenAPI.TOKEN = async () => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('authToken')
    return token ?? ''
  }

  logger.info('auth-interceptor', 'Auth interceptors registered')
}
