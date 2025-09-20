import { toast } from 'react-hot-toast'
import { logger } from './logger'
import type { 
  AuthResponse, 
  User, 
  VideoInfo, 
  VocabularyWord,
  ProcessingStatus,
  VocabularyLevel,
  VocabularyStats
} from '@/types'

// Import the generated client and SDK
import { client } from '@/client/client.gen'
import { createConfig } from '@/client/client/index'
import * as sdk from '@/client/sdk.gen'

// Get API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Token management
let authToken: string | null = localStorage.getItem('authToken')

// Configure the client with proper setup
client.setConfig(createConfig({
  baseUrl: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  interceptors: {
    request: [
      (request, options) => {
        const startTime = Date.now()
        
        // Add auth token if available
        if (authToken) {
          request.headers.set('Authorization', `Bearer ${authToken}`)
        }
        
        // Log API request
        const method = options.method?.toUpperCase() || 'UNKNOWN'
        const url = request.url
        logger.apiRequest(method, url, options.body)
        
        // Store start time for duration calculation
        ;(request as any)._startTime = startTime
        
        return request
      }
    ],
    response: [
      {
        onFulfilled: (response, request, options) => {
          // Log successful response
          const duration = (request as any)._startTime ? Date.now() - (request as any)._startTime : undefined
          const method = options.method?.toUpperCase() || 'UNKNOWN'
          const url = request.url
          
          logger.apiResponse(method, url, response.status, null, duration)
          
          return response
        },
        onRejected: (error, request, options) => {
          // Log error response
          const duration = (request as any)._startTime ? Date.now() - (request as any)._startTime : undefined
          const method = options?.method?.toUpperCase() || 'UNKNOWN'
          const url = request?.url || 'unknown'
          
          logger.apiResponse(method, url, error.status || 0, error, duration)
          
          // Handle auth errors
          if (error.status === 401) {
            authToken = null
            localStorage.removeItem('authToken')
            toast.error('Session expired. Please log in again.')
          }
          
          throw error
        }
      }
    ]
  }
}))

// Helper function to handle API errors
const handleApiError = (error: any, context: string) => {
  logger.error(`API Error in ${context}:`, error)
  
  if (error.status === 401) {
    toast.error('Authentication required')
  } else if (error.status === 403) {
    toast.error('Access denied')
  } else if (error.status === 404) {
    toast.error('Resource not found')
  } else if (error.status >= 500) {
    toast.error('Server error. Please try again later.')
  } else {
    toast.error(error.message || 'An unexpected error occurred')
  }
  
  throw error
}

// Authentication API
export const login = async (email: string, password: string): Promise<AuthResponse> => {
  try {
    const response = await sdk.loginApiAuthLoginPost({
      body: { username: email, password }
    })
    
    if (response.data?.access_token) {
      authToken = response.data.access_token
      localStorage.setItem('authToken', authToken)
    }
    
    return {
      token: response.data?.access_token || '',
      user: {
        id: response.data?.user?.id || '',
        email: response.data?.user?.email || email,
        name: response.data?.user?.name || ''
      }
    }
  } catch (error) {
    return handleApiError(error, 'login')
  }
}

export const register = async (email: string, password: string, name: string): Promise<AuthResponse> => {
  try {
    const response = await sdk.registerApiAuthRegisterPost({
      body: { email, password, name }
    })
    
    if (response.data?.access_token) {
      authToken = response.data.access_token
      localStorage.setItem('authToken', authToken)
    }
    
    return {
      token: response.data?.access_token || '',
      user: {
        id: response.data?.user?.id || '',
        email: response.data?.user?.email || email,
        name: response.data?.user?.name || name
      }
    }
  } catch (error) {
    return handleApiError(error, 'register')
  }
}

export const logout = async (): Promise<void> => {
  try {
    await sdk.logoutApiAuthLogoutPost({})
  } catch (error) {
    logger.warn('Logout API call failed:', error)
  } finally {
    authToken = null
    localStorage.removeItem('authToken')
  }
}

export const getProfile = async (): Promise<User> => {
  try {
    const response = await sdk.getCurrentUserInfoApiAuthMeGet({})
    return {
      id: response.data?.id || '',
      email: response.data?.email || '',
      name: response.data?.name || ''
    }
  } catch (error) {
    return handleApiError(error, 'getProfile')
  }
}

// Video API
export const getVideos = async (): Promise<VideoInfo[]> => {
  try {
    const response = await sdk.getAvailableVideosApiVideosGet({})
    return response.data || []
  } catch (error) {
    return handleApiError(error, 'getVideos')
  }
}

export const getVideoDetails = async (videoId: string): Promise<VideoInfo> => {
  try {
    const response = await sdk.getVideoStatusApiVideosVideoIdStatusGet({
      path: { video_id: videoId }
    })
    return response.data as VideoInfo
  } catch (error) {
    return handleApiError(error, 'getVideoDetails')
  }
}

export const uploadVideo = async (file: File, series?: string, episode?: string): Promise<any> => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (series) formData.append('series', series)
    if (episode) formData.append('episode', episode)
    
    const response = series 
      ? await sdk.uploadVideoApiVideosUploadSeriesPost({ body: formData })
      : await sdk.uploadVideoGenericApiVideosUploadPost({ body: formData })
    
    return response.data
  } catch (error) {
    return handleApiError(error, 'uploadVideo')
  }
}

export const processVideo = async (videoId: string): Promise<any> => {
  try {
    const response = await sdk.fullPipelineApiProcessFullPipelinePost({
      body: { video_id: videoId }
    })
    return response.data
  } catch (error) {
    return handleApiError(error, 'processVideo')
  }
}

export const getProcessingStatus = async (taskId: string): Promise<ProcessingStatus> => {
  try {
    const response = await sdk.getTaskProgressApiProcessProgressTaskIdGet({
      path: { task_id: taskId }
    })
    return response.data as ProcessingStatus
  } catch (error) {
    return handleApiError(error, 'getProcessingStatus')
  }
}

// Subtitle API
export const getSubtitles = async (subtitlePath: string): Promise<any> => {
  try {
    const response = await sdk.getSubtitlesApiVideosSubtitlesSubtitlePathGet({
      path: { subtitle_path: subtitlePath }
    })
    return response.data
  } catch (error) {
    return handleApiError(error, 'getSubtitles')
  }
}

export const filterSubtitles = async (data: any): Promise<any> => {
  try {
    const response = await sdk.filterSubtitlesApiProcessFilterSubtitlesPost({
      body: data
    })
    return response.data
  } catch (error) {
    return handleApiError(error, 'filterSubtitles')
  }
}

export const translateSubtitles = async (data: any): Promise<any> => {
  try {
    const response = await sdk.translateSubtitlesApiProcessTranslateSubtitlesPost({
      body: data
    })
    return response.data
  } catch (error) {
    return handleApiError(error, 'translateSubtitles')
  }
}

// Vocabulary API
export const getVocabularyStats = async (): Promise<VocabularyStats> => {
  try {
    const response = await sdk.getVocabularyStatsEndpointApiVocabularyStatsGet({})
    return response.data as VocabularyStats
  } catch (error) {
    return handleApiError(error, 'getVocabularyStats')
  }
}

export const getBlockingWords = async (): Promise<VocabularyWord[]> => {
  try {
    const response = await sdk.getBlockingWordsApiVocabularyBlockingWordsGet({})
    return response.data || []
  } catch (error) {
    return handleApiError(error, 'getBlockingWords')
  }
}

export const markWordAsKnown = async (word: string): Promise<void> => {
  try {
    await sdk.markWordAsKnownApiVocabularyMarkKnownPost({
      body: { word }
    })
  } catch (error) {
    return handleApiError(error, 'markWordAsKnown')
  }
}

export const preloadVocabulary = async (): Promise<void> => {
  try {
    await sdk.preloadVocabularyApiVocabularyPreloadPost({})
  } catch (error) {
    return handleApiError(error, 'preloadVocabulary')
  }
}

export const getVocabularyLevel = async (level: string): Promise<VocabularyLevel> => {
  try {
    const response = await sdk.getVocabularyLevelApiVocabularyLibraryLevelGet({
      path: { level }
    })
    return response.data as VocabularyLevel
  } catch (error) {
    return handleApiError(error, 'getVocabularyLevel')
  }
}

export const bulkMarkLevelKnown = async (level: string): Promise<void> => {
  try {
    await sdk.bulkMarkLevelKnownApiVocabularyLibraryBulkMarkPost({
      body: { level }
    })
  } catch (error) {
    return handleApiError(error, 'bulkMarkLevelKnown')
  }
}

// Vocabulary service object for organized access
export const vocabularyService = {
  getVocabularyStats,
  getBlockingWords,
  markWordAsKnown,
  preloadVocabulary,
  getVocabularyLevel,
  bulkMarkLevelKnown
}

// Video service object for organized access
export const videoService = {
  getVideos,
  getVideoDetails,
  uploadVideo,
  processVideo,
  getProcessingStatus,
  getVideoStreamUrl: (series: string, episode: string) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    return `${baseUrl}/videos/stream/${encodeURIComponent(series)}/${encodeURIComponent(episode)}`
  }
}

// Export the configured client and utilities
export { client as apiClient, handleApiError }