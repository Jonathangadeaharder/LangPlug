export interface SubtitleSegment {
  id: string
  startTime: number  // in seconds
  endTime: number    // in seconds
  originalText: string  // German text
  translatedText?: string  // English/user's language translation
  difficulty: 'easy' | 'medium' | 'hard'
  containsDifficultWords: boolean
  difficultWords?: string[]
  shouldShowSubtitle: boolean  // Based on difficulty threshold
}

export interface SubtitleTrack {
  segments: SubtitleSegment[]
  language: string
  targetLanguage: string
  difficultyThreshold: 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2'
}

export interface UserLanguageSettings {
  nativeLanguage: string  // e.g., 'en' for English
  learningLanguage: string  // e.g., 'de' for German
  proficiencyLevel: 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2'
  showSubtitlesFor: 'all' | 'difficult' | 'none'
  translateSubtitles: boolean
}
