import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { ProcessingScreen } from './ProcessingScreen'
import { VocabularyGame } from './VocabularyGame'
import { ChunkedLearningPlayer } from './ChunkedLearningPlayer'
import { handleApiError } from '@/services/api'
import {
  processChunkApiProcessChunkPost,
  profileGetApiProfileGet,
  markWordKnownApiVocabularyMarkKnownPost,
} from '@/client/services.gen'
import { logger } from '@/services/logger'
import { useRealtimeProgress } from '@/hooks/useRealtimeProgress'
import type { VideoInfo, ProcessingStatus, VocabularyWord } from '@/types'

interface ChunkData {
  chunkNumber: number
  startTime: number // in seconds
  endTime: number // in seconds
  vocabulary: VocabularyWord[]
  subtitlePath?: string
  translationPath?: string
  isProcessed: boolean
}

interface ProfileLanguageSummary {
  code: string
  name: string
}

interface UserProfileResponse {
  native_language: ProfileLanguageSummary
  target_language: ProfileLanguageSummary
  language_runtime?: {
    native: string
    target: string
    translation_service?: string
    translation_model?: string
  }
}

interface ChunkedLearningFlowProps {
  videoInfo: VideoInfo
  chunkDurationMinutes?: number // Default 20 minutes
  onComplete?: () => void // Called when entire episode is completed
}

export const ChunkedLearningFlow: React.FC<ChunkedLearningFlowProps> = ({
  videoInfo,
  chunkDurationMinutes = 20,
  onComplete,
}) => {
  const navigate = useNavigate()
  const { series, episode: _episode } = useParams<{ series: string; episode: string }>()

  // State management
  const [currentPhase, setCurrentPhase] = useState<'processing' | 'game' | 'video'>('processing')
  const [currentChunk, setCurrentChunk] = useState(0)
  const [chunks, setChunks] = useState<ChunkData[]>([])
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>({
    status: 'processing',
    progress: 0,
    current_step: 'Initializing',
    message: 'Starting processing...',
  })
  // Real-time progress tracking with WebSocket + polling fallback
  const {
    taskId: monitoredTaskId,
    startMonitoring,
    stopMonitoring,
    progress: realtimeProgress,
    status: realtimeStatus,
    currentStep,
    message: realtimeMessage,
    isComplete: realtimeComplete,
    error: realtimeError,
    connectionMethod,
    result: realtimeResult,
  } = useRealtimeProgress()
  const [gameWords, setGameWords] = useState<VocabularyWord[]>([])
  const [learnedWords, setLearnedWords] = useState<Set<string>>(new Set())
  const [activeLanguages, setActiveLanguages] = useState<{
    native: ProfileLanguageSummary
    target: ProfileLanguageSummary
  } | null>(null)
  const [profileLoaded, setProfileLoaded] = useState(false)

  // Calculate total chunks based on video duration
  useEffect(() => {
    logger.info('ChunkedLearningFlow', `🎬 Initializing chunks for video: ${videoInfo.path}`)
    const videoDurationMinutes = videoInfo.duration || 25 // Assume 25 minutes if not provided
    const totalChunks = Math.ceil(videoDurationMinutes / chunkDurationMinutes)

    logger.info(
      'ChunkedLearningFlow',
      `Video duration: ${videoDurationMinutes} min, Chunk size: ${chunkDurationMinutes} min, Total chunks: ${totalChunks}`
    )

    const newChunks: ChunkData[] = []
    for (let i = 0; i < totalChunks; i++) {
      newChunks.push({
        chunkNumber: i + 1,
        startTime: i * chunkDurationMinutes * 60,
        endTime: Math.min((i + 1) * chunkDurationMinutes * 60, videoDurationMinutes * 60),
        vocabulary: [],
        isProcessed: false, // Always mark as not processed to force reprocessing
      })
    }
    setChunks(newChunks)
  }, [videoInfo.duration, chunkDurationMinutes, videoInfo.path])

  useEffect(() => {
    let isMounted = true

    const loadProfileLanguages = async () => {
      try {
        const profile = (await profileGetApiProfileGet()) as unknown as UserProfileResponse
        if (!isMounted || !profile) {
          return
        }

        logger.info('ChunkedLearningFlow', 'Loaded user profile with languages', {
          native: profile.native_language?.name,
          target: profile.target_language?.name,
        })
        setActiveLanguages({
          native: profile.native_language,
          target: profile.target_language,
        })
        setProfileLoaded(true)
      } catch (error) {
        logger.warn('ChunkedLearningFlow', 'Failed to load user language preferences', error)
      }
    }

    loadProfileLanguages()

    return () => {
      isMounted = false
    }
  }, [])

  // Format time for display
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // Process current chunk
  const processChunk = async (chunkIndex: number) => {
    logger.info('ChunkedLearningFlow', `Processing chunk ${chunkIndex + 1}/${chunks.length}`)

    if (chunkIndex >= chunks.length) {
      logger.info('ChunkedLearningFlow', 'All chunks processed! Episode completed!')
      toast.success('Episode completed!')
      onComplete?.()
      return
    }

    const chunk = chunks[chunkIndex]

    logger.info('ChunkedLearningFlow', 'Processing chunk details', {
      chunkNumber: chunk.chunkNumber,
      startTime: chunk.startTime,
      endTime: chunk.endTime,
      videoPath: videoInfo.path,
    })

    setCurrentPhase('processing')
    setProcessingStatus({
      status: 'processing',
      progress: 0,
      current_step: 'Processing chunk',
      message: `Processing segment ${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`,
    })

    try {
      const response = (await processChunkApiProcessChunkPost({
        requestBody: {
          video_path: videoInfo.path,
          start_time: chunk.startTime,
          end_time: chunk.endTime,
        },
      })) as { task_id: string; status?: string }

      logger.info('ChunkedLearningFlow', 'Backend task started', {
        taskId: response.task_id,
        chunkIndex: chunkIndex + 1,
        status: response.status || 'started',
      })

      // Start real-time monitoring (WebSocket with polling fallback)
      startMonitoring(response.task_id)
      logger.info('ChunkedLearningFlow', `Started monitoring task ${response.task_id} via ${connectionMethod}`)
    } catch (error) {
      logger.error('ChunkedLearningFlow', 'Failed to start chunk processing', error)
      handleApiError(error, 'ChunkedLearningFlow.processChunk')
      toast.error('Failed to process chunk')
    }
  }

  // Sync real-time progress to processing status
  useEffect(() => {
    // Only sync if we're actively monitoring a task
    if (!monitoredTaskId) return

    // Update processing status from real-time hook
    setProcessingStatus(prev => ({
      ...prev,
      progress: realtimeProgress,
      current_step: currentStep || prev.current_step,
      message: realtimeMessage || prev.message,
      status: realtimeStatus === 'failed' ? 'error' : 
              realtimeStatus === 'completed' ? 'completed' : 'processing',
    }))

    // Log connection method for debugging
    if (connectionMethod !== 'disconnected' && realtimeProgress > 0) {
      logger.debug('ChunkedLearningFlow', `Progress via ${connectionMethod}: ${realtimeProgress}%`)
    }
  }, [realtimeProgress, currentStep, realtimeMessage, realtimeStatus, connectionMethod, monitoredTaskId])

  // Handle processing completion from real-time hook
  useEffect(() => {
    // Only process completion if we're actively monitoring a task and it completed
    if (!realtimeComplete || !monitoredTaskId) return

    const result = realtimeResult as ProcessingStatus | null
    if (!result) {
      logger.warn('ChunkedLearningFlow', 'Processing completed but no result data', {
        taskId: monitoredTaskId,
        realtimeResult,
      })
      return
    }

    logger.info('ChunkedLearningFlow', 'Processing completed (real-time)', {
      chunkIndex: currentChunk + 1,
      vocabularyCount: result.vocabulary?.length || 0,
      subtitlePath: result.subtitle_path,
      translationPath: result.translation_path,
      connectionMethod,
    })

    // Validate vocabulary data
    if (!result.vocabulary || result.vocabulary.length === 0) {
      const message = result.message || 'Processing completed but vocabulary data is missing'
      logger.error('ChunkedLearningFlow', 'No vocabulary extracted', {
        message,
        vocabularyCount: result.vocabulary?.length ?? 0,
      })
      // Show more helpful error message based on structured error code
      if (result.error_code === 'SPACY_MODEL_ERROR') {
        toast.error('Vocabulary extraction failed - check backend server logs for spaCy model errors')
      } else {
        toast.error(message)
      }
      return
    }

    const vocabularyWithIds = result.vocabulary.map((word: VocabularyWord) => {
      if (!word.lemma) {
        logger.warn('ChunkedLearningFlow', `Word "${word.word}" is missing lemma field`)
      }
      return {
        ...word,
        lemma: word.lemma || word.word,
      }
    })

    const updatedChunks = [...chunks]
    updatedChunks[currentChunk] = {
      ...updatedChunks[currentChunk],
      vocabulary: vocabularyWithIds,
      subtitlePath: result.subtitle_path,
      translationPath: result.translation_path || undefined,
      isProcessed: true,
    }

    logger.userAction('Entering vocabulary game phase', 'ChunkedLearningFlow', {
      wordsToLearn: result.vocabulary?.length || 0,
      chunkIndex: currentChunk + 1,
    })

    // Transition to game phase
    setCurrentPhase('game')
    setGameWords(vocabularyWithIds)
    setChunks(updatedChunks)
    stopMonitoring()
  }, [realtimeComplete, realtimeResult, currentChunk, chunks, connectionMethod, stopMonitoring, monitoredTaskId])

  // Handle processing errors from real-time hook
  useEffect(() => {
    if (!realtimeError) return

    logger.error('ChunkedLearningFlow', `Processing failed: ${realtimeError}`)
    toast.error(`Processing failed: ${realtimeError}`)
    stopMonitoring()
  }, [realtimeError, stopMonitoring])

  // Handle individual word answers in the game with improved error handling
  const handleWordAnswered = async (word: string, known: boolean) => {
    const wordData = gameWords.find(w => w.word === word)
    if (!wordData) {
      logger.warn('ChunkedLearningFlow', 'Cannot save word progress - word not found', { word })
      toast.error(`Cannot save progress for "${word}" - word data missing`)
      return
    }

    // Show optimistic feedback immediately
    const loadingToast = toast.loading(`Saving progress for "${word}"...`)

    try {
      // Use lemma-based API endpoint
      const res = (await markWordKnownApiVocabularyMarkKnownPost({
        requestBody: {
          lemma: wordData.lemma,
          language: 'de',
          known: known,
        },
      })) as { word?: string; lemma?: string; level?: string }

      const respWord = res?.word ?? word
      const respLemma = res?.lemma ?? wordData.lemma
      const respLevel = res?.level ?? wordData.difficulty_level
      logger.info('ChunkedLearningFlow', 'Word progress saved to database', {
        word: respWord,
        lemma: respLemma,
        level: respLevel,
        known,
      })

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast)
      toast.success('✓ Progress saved', { duration: 1500 })
    } catch (error) {
      logger.error('ChunkedLearningFlow', 'Failed to save word progress', { word, error })
      toast.dismiss(loadingToast)
      toast.error(`Failed to save progress for "${word}". Please try again.`, { duration: 3000 })
      // Let error propagate - fail fast, no silent retries
      throw error
    }
  }

  // Handle game completion with second-pass filtering
  const handleGameComplete = async (knownWords: string[], unknownWords: string[]) => {
    logger.userAction('Vocabulary game completed', 'ChunkedLearningFlow', {
      knownWords: knownWords.length,
      unknownWords: unknownWords.length,
      totalWords: knownWords.length + unknownWords.length,
      chunkIndex: currentChunk + 1,
    })

    setLearnedWords(prev => new Set([...prev, ...knownWords]))

    // Re-process chunk to get filtered subtitles with updated vocabulary
    logger.info('ChunkedLearningFlow', 'Re-processing chunk with updated vocabulary knowledge')
    toast.loading('Updating subtitles based on your progress...', { duration: 2000 })

    try {
      // Re-process the current chunk - this will fetch fresh user vocabulary progress
      await processChunk(currentChunk)

      logger.info('ChunkedLearningFlow', 'Chunk re-processed with updated vocabulary')
    } catch (error) {
      logger.error('ChunkedLearningFlow', 'Failed to reprocess chunk after game', { error })
      // Continue anyway - user can still watch with old subtitles
      toast.error('Failed to update subtitles, but you can continue watching')
    }

    logger.userAction('Entering video playback phase', 'ChunkedLearningFlow', {
      chunkIndex: currentChunk + 1,
      totalLearnedWords: learnedWords.size + knownWords.length,
    })
    setCurrentPhase('video')
  }

  // Handle skipping vocabulary game
  const handleSkipGame = () => {
    // Copy subtitle paths from processing status to chunk data
    if (processingStatus && currentChunk < chunks.length) {
      const updatedChunks = [...chunks]
      updatedChunks[currentChunk] = {
        ...updatedChunks[currentChunk],
        subtitlePath: processingStatus.subtitle_path,
        translationPath: processingStatus.translation_path || undefined,
      }
      setChunks(updatedChunks)
      logger.info('ChunkedLearningFlow', 'Updated chunk with subtitle paths', {
        chunkIndex: currentChunk + 1,
        subtitlePath: processingStatus.subtitle_path,
        translationPath: processingStatus.translation_path || undefined,
      })
    }

    logger.userAction('Skipped vocabulary game', 'ChunkedLearningFlow', {
      chunkIndex: currentChunk + 1,
      vocabularyCount: processingStatus?.vocabulary?.length || 0,
    })
    setCurrentPhase('video')
  }

  const advanceToNextChunk = (reason: 'completed' | 'skipped') => {
    if (currentChunk < chunks.length - 1) {
      logger.userAction(
        reason === 'completed'
          ? 'Chunk video completed, advancing'
          : 'Chunk skipped, advancing to next segment',
        'ChunkedLearningFlow',
        {
          completedChunk: currentChunk + 1,
          nextChunk: currentChunk + 2,
          totalChunks: chunks.length,
          progressPercent: Math.round(((currentChunk + 1) / chunks.length) * 100),
        }
      )
      setCurrentChunk(prev => prev + 1)
      setCurrentPhase('processing')
    } else {
      logger.userAction(
        reason === 'completed' ? 'Episode completed!' : 'Episode skipped to completion',
        'ChunkedLearningFlow',
        {
          totalChunks: chunks.length,
          totalLearnedWords: learnedWords.size,
          videoTitle: videoInfo?.title,
        }
      )
      onComplete?.()
    }
  }

  // Handle video completion
  const handleVideoComplete = () => {
    advanceToNextChunk('completed')
  }

  const handleSkipChunk = () => {
    advanceToNextChunk('skipped')
  }

  const handleBackToEpisodes = () => {
    const targetSeries = series || videoInfo.series
    logger.userAction('Returned to episode selection', 'ChunkedLearningFlow', {
      series: targetSeries,
      currentChunk: currentChunk + 1,
      totalChunks: chunks.length,
    })

    if (targetSeries) {
      navigate(`/episodes/${encodeURIComponent(targetSeries)}`)
    } else {
      navigate('/')
    }
  }

  // Start processing first chunk on mount (after profile is loaded)
  useEffect(() => {
    if (chunks.length > 0 && currentChunk === 0 && currentPhase === 'processing' && profileLoaded) {
      logger.info('ChunkedLearningFlow', '🚀 Starting processing of first chunk')
      processChunk(0)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chunks.length, profileLoaded]) // processChunk and currentPhase would cause infinite re-processing

  // Start processing when advancing to subsequent chunks
  useEffect(() => {
    if (chunks.length > 0 && currentChunk > 0 && currentPhase === 'processing' && profileLoaded) {
      logger.info('ChunkedLearningFlow', `🚀 Starting processing of chunk ${currentChunk + 1}`)
      processChunk(currentChunk)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentChunk, currentPhase, profileLoaded]) // chunks.length and processChunk would cause infinite re-processing

  // Render based on current phase
  const renderPhase = () => {
    const chunk = chunks[currentChunk]
    if (!chunk) return null

    switch (currentPhase) {
      case 'processing':
        return (
          <ProcessingScreen
            status={processingStatus}
            chunkNumber={currentChunk + 1}
            totalChunks={chunks.length}
            chunkDuration={`${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`}
            connectionMethod={connectionMethod}
          />
        )

      case 'game':
        return (
          <VocabularyGame
            words={gameWords}
            onWordAnswered={handleWordAnswered}
            onComplete={handleGameComplete}
            onSkip={handleSkipGame}
            episodeTitle={videoInfo.title}
            chunkInfo={{
              current: currentChunk + 1,
              total: chunks.length,
              duration: `${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`,
            }}
          />
        )

      case 'video':
        logger.info('ChunkedLearningFlow', 'Rendering video player', {
          subtitlePath: chunk.subtitlePath,
          translationPath: chunk.translationPath,
          chunkIndex: currentChunk,
          targetLanguage: activeLanguages?.target?.name,
          nativeLanguage: activeLanguages?.native?.name,
        })
        return (
          <ChunkedLearningPlayer
            videoPath={videoInfo.path}
            series={videoInfo.series}
            episode={videoInfo.episode}
            subtitlePath={chunk.subtitlePath}
            translationPath={chunk.translationPath}
            startTime={chunk.startTime}
            endTime={chunk.endTime}
            onComplete={handleVideoComplete}
            onSkipChunk={handleSkipChunk}
            onBack={handleBackToEpisodes}
            learnedWords={Array.from(learnedWords)}
            chunkInfo={{
              current: currentChunk + 1,
              total: chunks.length,
              duration: `${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`,
            }}
            targetLanguage={activeLanguages?.target}
            nativeLanguage={activeLanguages?.native}
          />
        )

      default:
        return null
    }
  }

  return <>{renderPhase()}</>
}
