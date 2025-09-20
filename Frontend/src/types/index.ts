export interface User {
  id: number
  username: string
  is_admin: boolean
  is_active: boolean
 created_at: string
  last_login?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
}

export interface AuthResponse {
  token: string
  user: User
  expires_at: string
}

export interface VideoInfo {
  series: string
  season: string
  episode: string
  title: string
  path: string
  has_subtitles: boolean
  duration?: number
}

export interface VocabularyWord {
  word: string
  definition?: string
  difficulty_level: string
  known: boolean
}

export interface VocabularyLibraryWord {
  id: number
  word: string
  difficulty_level: string
  part_of_speech: string
  definition?: string
  known: boolean
}

export interface VocabularyLevel {
  level: string
  words: VocabularyLibraryWord[]
  total_count: number
  known_count: number
}

export interface VocabularyStats {
  levels: Record<string, {
    total_words: number
    user_known: number
  }>
  total_words: number
  total_known: number
}

export interface ProcessingStatus {
  status: 'processing' | 'completed' | 'error'
  progress: number
  current_step: string
  message?: string
  started_at?: number
  vocabulary?: VocabularyWord[]
  subtitle_path?: string
  translation_path?: string
}

export interface VideoSegment {
  start_time: number
  duration: number
  blocking_words: VocabularyWord[]
  subtitles_processed: boolean
}

export interface GameSession {
  video_path: string
  current_segment: number
  segments: VideoSegment[]
  user_progress: Record<string, boolean>
  completed: boolean
}