import { AxiosRequestConfig, AxiosResponse } from 'axios'
import { OpenAPI } from '@/client/core/OpenAPI'
import { logger } from './logger'
import { clearAuthState } from '@/store/useAuthStore'

// Request interceptor (No longer adds token, cookies handle it)
export const authRequestInterceptor = async (
  config: AxiosRequestConfig
): Promise<AxiosRequestConfig> => {
  // Ensure withCredentials is true for all requests
  config.withCredentials = true
  return config
}

// Response interceptor to handle 401 errors
export const authResponseInterceptor = async (response: AxiosResponse): Promise<AxiosResponse> => {
  // If response is successful, just return it
  if (response.status !== 401) {
    return response
  }

  // If we get a 401, it means our cookie is invalid/expired
  logger.warn('auth-interceptor', 'Unauthorized (401) received, clearing auth')

  // Clear auth state
  clearAuthState()

  // Redirect to login (if not already there)
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }

  return response
}

// Setup function to register interceptors
export const setupAuthInterceptors = () => {
  // Register request interceptor
  OpenAPI.interceptors.request.use(authRequestInterceptor)

  // Register response interceptor
  OpenAPI.interceptors.response.use(authResponseInterceptor)

  // We no longer need to set OpenAPI.TOKEN
  OpenAPI.TOKEN = undefined

  logger.info('auth-interceptor', 'Auth interceptors registered (Cookie mode)')
}
