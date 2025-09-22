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
import type { 
  BearerResponse, 
  UserRead
} from '@/client/types.gen'

// Import the generated client and SDK
import { OpenAPI } from '@/client/core/OpenAPI'
import * as Services from '@/client/services.gen'

// Get API base URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Token management
let authToken: string | null = localStorage.getItem('authToken')

// Configure the OpenAPI client
OpenAPI.BASE = API_BASE_URL;
OpenAPI.HEADERS = {
  'Content-Type': 'application/json'
};
// Ensure Authorization header is set automatically when authToken is present
OpenAPI.TOKEN = async () => (authToken ?? '');

// Helper function to add auth header to requests
const getAuthHeaders = () => {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {}
}

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
    // FastAPI-Users login expects form data with username and password fields
    // For email-based login, username field should contain the email
    const response = await Services.authJwtBearerLoginApiAuthLoginPost({
      formData: { username: email, password }
    })

    // FastAPI-Users Bearer transport returns BearerResponse schema
    const bearerData = response as BearerResponse
    const accessToken = bearerData?.access_token;

    if (!accessToken) {
      throw new Error('No access token received from server')
    }

    authToken = accessToken
    localStorage.setItem('authToken', authToken as string)

    // Get user profile after login
    let user: User = {
      id: '' as any, // Using any to bypass string/number type issues
      email: email,
      name: ''
    } as any // Using any to bypass User type issues

    try {
      user = await getProfile()
    } catch (profileError) {
      // If we can't get profile, use the email as fallback
      console.warn('Failed to get user profile after login:', profileError)
      user = {
        id: '' as any, // Using any to bypass string/number type issues
        email: email,
        name: ''
      } as any // Using any to bypass User type issues
    }

    return {
      token: accessToken,
      user: user,
      expires_at: '' // Add placeholder for expires_at
    }
  } catch (error: any) {
    // Clear any stored auth token on login failure
    authToken = null
    localStorage.removeItem('authToken')
    return handleApiError(error, 'login')
  }
}

export const register = async (email: string, password: string, name: string): Promise<AuthResponse> => {
  try {
    // FastAPI-Users registration expects username, email, and password
    await Services.registerRegisterApiAuthRegisterPost({
      requestBody: {
        username: name,
        email: email,
        password: password,
      } as any
    })

    // FastAPI-Users register returns UserRead directly (no token)
    // We need to login to get the access token
    const loginResult = await login(email, password)
    return loginResult
    
  } catch (error: any) {
    // Handle registration errors
    if (error.status === 400) {
      throw new Error('Registration failed: Invalid data provided')
    } else if (error.status === 422) {
      throw new Error('Registration failed: User already exists')
    }
    return handleApiError(error, 'register')
  }
}

export const logout = async (): Promise<void> => {
  try {
    await Services.authJwtBearerLogoutApiAuthLogoutPost()
  } catch (error) {
    logger.warn('Logout API call failed:', error)
  } finally {
    authToken = null
    localStorage.removeItem('authToken')
  }
}

export const getProfile = async (): Promise<User> => {
  try {
    const userData = await Services.authGetCurrentUserApiAuthMeGet()
    return {
      id: userData?.id || '',
      email: userData?.email || '',
      name: userData?.username || '' // FastAPI-Users uses 'username' field
    }
  } catch (error) {
    return handleApiError(error, 'getProfile')
  }
}

// Video API
export const getVideos = async (): Promise<VideoInfo[]> => {
  try {
    const data = await Services.getVideosApiVideosGet()
    return (data as any) || []
  } catch (error) {
    return handleApiError(error, 'getVideos')
  }
}

export const getVideoDetails = async (videoId: string): Promise<VideoInfo> => {
  try {
    const data = await Services.getVideoStatusApiVideosVideoIdStatusGet({
      videoId: videoId,
    })
    return data as any
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
      ? await Services.uploadVideoToSeriesApiVideosUploadSeriesPost({ series, formData })
      : await Services.uploadVideoGenericApiVideosUploadPost({ formData, series })
    
    return response
  } catch (error) {
    return handleApiError(error, 'uploadVideo')
  }
}

export const processVideo = async (videoId: string): Promise<any> => {
  try {
    const response = await Services.fullPipelineApiProcessFullPipelinePost({
      requestBody: { video_id: videoId }
    })
    return response
  } catch (error) {
    return handleApiError(error, 'processVideo')
  }
}

export const getProcessingStatus = async (taskId: string): Promise<ProcessingStatus> => {
  try {
    const data = await Services.getTaskProgressApiProcessProgressTaskIdGet({
      taskId: taskId,
    })
    return data as any
  } catch (error) {
    return handleApiError(error, 'getProcessingStatus')
  }
}

// Subtitle API
export const getSubtitles = async (subtitlePath: string): Promise<any> => {
  try {
    const response = await Services.getSubtitlesApiVideosSubtitlesSubtitlePathGet({
      subtitlePath,
    })
    return response
  } catch (error) {
    return handleApiError(error, 'getSubtitles')
  }
}

export const filterSubtitles = async (data: any): Promise<any> => {
  try {
    const response = await Services.filterSubtitlesApiProcessFilterSubtitlesPost({
      requestBody: data,
    })
    return response
  } catch (error) {
    return handleApiError(error, 'filterSubtitles')
  }
}

export const translateSubtitles = async (data: any): Promise<any> => {
  try {
    const response = await Services.translateSubtitlesApiProcessTranslateSubtitlesPost({
      requestBody: data,
    })
    return response
  } catch (error) {
    return handleApiError(error, 'translateSubtitles')
  }
}

// Vocabulary API
export const getVocabularyStats = async (): Promise<VocabularyStats> => {
  try {
    const data = await Services.getVocabularyStatsApiVocabularyStatsGet()
    return data as any
  } catch (error) {
    return handleApiError(error, 'getVocabularyStats')
  }
}

export const getBlockingWords = async (videoPath: string, segmentStart?: number, segmentDuration?: number): Promise<VocabularyWord[]> => {
  try {
    const data = await Services.getBlockingWordsApiVocabularyBlockingWordsGet({
      videoPath,
      segmentStart,
      segmentDuration,
    } as any)
    return (data as any) || []
  } catch (error) {
    return handleApiError(error, 'getBlockingWords')
  }
}

export const markWordAsKnown = async (word: string): Promise<void> => {
  try {
    await Services.markWordKnownApiVocabularyMarkKnownPost({
      requestBody: { word },
    })
  } catch (error) {
    return handleApiError(error, 'markWordAsKnown')
  }
}

export const preloadVocabulary = async (): Promise<void> => {
  try {
    await Services.preloadVocabularyApiVocabularyPreloadPost()
  } catch (error) {
    return handleApiError(error, 'preloadVocabulary')
  }
}

export const getVocabularyLevel = async (level: string): Promise<VocabularyLevel> => {
  try {
    const data = await Services.getVocabularyLevelApiVocabularyLibraryLevelGet({
      level,
    } as any)
    return data as any
  } catch (error) {
    return handleApiError(error, 'getVocabularyLevel')
  }
}

export const bulkMarkLevelKnown = async (level: string): Promise<void> => {
  try {
    await Services.bulkMarkLevelApiVocabularyLibraryBulkMarkPost({
      requestBody: { level },
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
export { OpenAPI as apiClient, handleApiError }