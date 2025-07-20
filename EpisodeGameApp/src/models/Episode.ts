export interface VocabularyWord {
  id: string;
  german: string;
  english: string;
  difficulty: 'A1' | 'A2' | 'B1' | 'B2';
  frequency: number;
  context: string;
}

export interface Episode {
  id: string;
  title: string;
  description: string;
  videoUrl: string;
  thumbnailUrl: string;
  duration: number; // in minutes
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced';
  vocabularyWords: string[];
  subtitleUrl?: string;
  // New fields for subtitle processing workflow
  isTranscribed?: boolean;
  hasFilteredSubtitles?: boolean;
  hasTranslatedSubtitles?: boolean;
  filteredSubtitleUrl?: string;
  translatedSubtitleUrl?: string;
  vocabularyAnalysis?: {
    totalWords: number;
    knownCount: number;
    unknownCount: number;
    actualDifficultyLevel?: 'beginner' | 'intermediate' | 'advanced';
  };
}

export const defaultEpisodes: Episode[] = [
  {
    id: 'ep1',
    title: 'Episode 1 - Call the Midwife',
    description: 'Episode 1 Staffel 1 von Call the Midwife - Ruf des Lebens with German subtitles for A1 level learning.',
    videoUrl: 'videos/episode1.mp4',
    thumbnailUrl: 'assets/thumbnails/episode1.jpg',
    duration: 60,
    difficultyLevel: 'beginner',
    vocabularyWords: ['hello', 'goodbye', 'please', 'thank you', 'yes', 'no'],
    subtitleUrl: 'subtitles/episode1.srt',
    isTranscribed: true,
    hasFilteredSubtitles: true,
    hasTranslatedSubtitles: true
  },
  {
    id: 'ep2',
    title: 'Episode 2 - Call the Midwife',
    description: 'Episode 2 Staffel 1 von Call the Midwife - Ruf des Lebens with German subtitles for A1 level learning.',
    videoUrl: 'videos/episode2.mp4',
    thumbnailUrl: 'assets/thumbnails/episode2.jpg',
    duration: 60,
    difficultyLevel: 'beginner',
    vocabularyWords: ['family', 'mother', 'father', 'community', 'help', 'care'],
    subtitleUrl: 'subtitles/episode2.srt',
    isTranscribed: true,
    hasFilteredSubtitles: true,
    hasTranslatedSubtitles: true
  },
  {
    id: 'ep3',
    title: 'Episode 3 - Call the Midwife',
    description: 'Episode 3 Staffel 1 von Call the Midwife - Ruf des Lebens with German subtitles for A1 level learning.',
    videoUrl: 'videos/episode3.mp4',
    thumbnailUrl: 'assets/thumbnails/episode3.jpg',
    duration: 60,
    difficultyLevel: 'beginner',
    vocabularyWords: ['midwife', 'baby', 'hospital', 'doctor', 'nurse', 'birth'],
    subtitleUrl: 'subtitles/episode3.srt',
    isTranscribed: true,
    hasFilteredSubtitles: true,
    hasTranslatedSubtitles: true
  }
];