import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { ProcessingScreen } from './ProcessingScreen'
import { VocabularyGame } from './VocabularyGame'
import { ChunkedLearningPlayer } from './ChunkedLearningPlayer'
import { handleApiError, OpenAPI } from '@/services/api'
import {
  getTaskProgressApiProcessProgressTaskIdGet,
  processChunkApiProcessChunkPost,
  profileGetApiProfileGet,
  markWordKnownApiVocabularyMarkKnownPost,
} from '@/client/services.gen'
import { logger } from '@/services/logger'
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
  chunkDurationMinutes?: number // Default 5 minutes
  onComplete?: () => void // Called when entire episode is completed
}

export const ChunkedLearningFlow: React.FC<ChunkedLearningFlowProps> = ({
  videoInfo,
  chunkDurationMinutes = 5,
  onComplete
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
    message: 'Starting processing...'
  })
  const [_taskId, setTaskId] = useState<string | null>(null)
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

    logger.info('ChunkedLearningFlow', `Video duration: ${videoDurationMinutes} min, Chunk size: ${chunkDurationMinutes} min, Total chunks: ${totalChunks}`)

    const newChunks: ChunkData[] = []
    for (let i = 0; i < totalChunks; i++) {
      newChunks.push({
        chunkNumber: i + 1,
        startTime: i * chunkDurationMinutes * 60,
        endTime: Math.min((i + 1) * chunkDurationMinutes * 60, videoDurationMinutes * 60),
        vocabulary: [],
        isProcessed: false  // Always mark as not processed to force reprocessing
      })
    }
    console.log(`[ChunkedLearningFlow] Created ${newChunks.length} chunks (all marked for reprocessing)`)
    setChunks(newChunks)
  }, [videoInfo.duration, chunkDurationMinutes, videoInfo.path])

  useEffect(() => {
    let isMounted = true

    const loadProfileLanguages = async () => {
      try {
        const profile = await profileGetApiProfileGet() as unknown as UserProfileResponse
        if (!isMounted || !profile) {
          return
        }

        logger.info('ChunkedLearningFlow', 'Loaded user profile with languages', {
          native: profile.native_language?.name,
          target: profile.target_language?.name,
        })
        console.log('[ChunkedLearningFlow] Profile loaded:', {
          native: profile.native_language,
          target: profile.target_language,
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
    console.log(`[ChunkedLearningFlow] 🎬 processChunk called with index: ${chunkIndex}/${chunks.length}`)

    if (chunkIndex >= chunks.length) {
      console.log(`[ChunkedLearningFlow] 🎉 All chunks processed! Episode completed!`)
      // All chunks processed
      toast.success('Episode completed!')
      const handleProcessChunk = async () => {
        if (!videoInfo) return

        logger.userAction(`Start processing chunk ${currentChunk + 1}`, 'ChunkedLearningFlow', {
          chunkRange: `${formatTime(chunks[currentChunk].startTime)} - ${formatTime(chunks[currentChunk].endTime)}`,
          videoTitle: videoInfo.title
        })

        setCurrentPhase('processing')
        const chunk = chunks[currentChunk]

        try {
          logger.info('ChunkedLearningFlow', `Starting chunk ${currentChunk + 1} processing`, {
            startTime: chunk.startTime,
            endTime: chunk.endTime,
            videoPath: videoInfo.path,
            totalChunks: chunks.length
          })

          console.log(`[ChunkedLearningFlow] Setting phase to PROCESSING`)
          setCurrentPhase('processing')
          setProcessingStatus({
            status: 'processing',
            progress: 0,
            current_step: 'Processing chunk',
            message: `Processing segment ${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`
          })

          try {
            console.log(`[ChunkedLearningFlow] 📡 Calling backend to process chunk...`)
            // Call backend to process this specific chunk
            const response = await processChunkApiProcessChunkPost({
              requestBody: {
                video_path: videoInfo.path,
                start_time: chunk.startTime,
                end_time: chunk.endTime,
              },
            }) as { task_id: string; status?: string }
            setTaskId(response.task_id)

            logger.info('ChunkedLearningFlow', 'Backend task started', {
              taskId: response.task_id,
              chunkIndex: currentChunk + 1,
              status: response.status || 'started'
            })
            console.log(`[ChunkedLearningFlow] Task ID received: ${response.task_id}`)

            // Start polling for progress
            console.log(`[ChunkedLearningFlow] Starting progress polling...`)
            pollProgress(response.task_id, chunkIndex)
          } catch (error) {
            console.error('[ChunkedLearningFlow] ❌ Failed to start chunk processing:', error)
            handleApiError(error, 'ChunkedLearningFlow.processChunk')
            toast.error('Failed to process chunk')
          }
        } catch (error) {
          console.error('[ChunkedLearningFlow] ❌ Error processing chunk:', error)
        }
      }
      handleProcessChunk()
      return
    }

    const chunk = chunks[chunkIndex]
    console.log(`[ChunkedLearningFlow] Processing chunk details:`, {
      chunkNumber: chunk.chunkNumber,
      startTime: chunk.startTime,
      endTime: chunk.endTime,
      videoPath: videoInfo.path
    })

    console.log(`[ChunkedLearningFlow] Setting phase to PROCESSING`)
    setCurrentPhase('processing')
    setProcessingStatus({
      status: 'processing',
      progress: 0,
      current_step: 'Processing chunk',
      message: `Processing segment ${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`
    })

    try {
      console.log(`[ChunkedLearningFlow] 📡 Calling backend to process chunk...`)
      // Call backend to process this specific chunk
      const response = await processChunkApiProcessChunkPost({
        requestBody: {
          video_path: videoInfo.path,
          start_time: chunk.startTime,
          end_time: chunk.endTime,
        },
      }) as { task_id: string; status?: string }
      setTaskId(response.task_id)

      logger.info('ChunkedLearningFlow', 'Backend task started', {
        taskId: response.task_id,
        chunkIndex: currentChunk + 1,
        status: response.status || 'started'
      })
      console.log(`[ChunkedLearningFlow] Task ID received: ${response.task_id}`)

      // Start polling for progress
      console.log(`[ChunkedLearningFlow] Starting progress polling...`)
      pollProgress(response.task_id, chunkIndex)
    } catch (error) {
      console.error('[ChunkedLearningFlow] ❌ Failed to start chunk processing:', error)
      handleApiError(error, 'ChunkedLearningFlow.handleProcessChunk')
      toast.error('Failed to process chunk')
    }
  }

  // Poll for processing progress with exponential backoff
  const pollProgress = async (taskId: string, chunkIndex: number) => {
    console.log(`[ChunkedLearningFlow] 🔄 Starting progress polling for task: ${taskId}, chunk: ${chunkIndex}`)
    const maxAttempts = 120 // Reduced from 180, with longer intervals
    let attempts = 0
    let pollInterval = 5000 // Start at 5 seconds

    const poll = async () => {
      try {
        logger.debug('ChunkedLearningFlow', `Polling attempt ${attempts + 1}/${maxAttempts}`, { taskId })
        const progress = await getTaskProgressApiProcessProgressTaskIdGet({ taskId }) as ProcessingStatus
        logger.info('ChunkedLearningFlow', 'Progress update', {
          status: progress.status,
          progress: progress.progress,
          step: progress.current_step,
          vocabularyCount: progress.vocabulary?.length || 0
        })
        setProcessingStatus(progress)

        if (progress.status === 'completed') {
          logger.info('ChunkedLearningFlow', '✅ PROCESSING COMPLETED!', {
            chunkIndex: currentChunk + 1,
            vocabularyCount: progress.vocabulary?.length || 0,
            subtitlePath: progress.subtitle_path,
            translationPath: progress.translation_path
          })

          // Update chunk data with results
          // Add fallback concept_id for backwards compatibility
          const vocabularyWithIds = (progress.vocabulary || []).map((word: any) => ({
            ...word,
            concept_id: word.concept_id || `${word.lemma || word.word}-${word.difficulty_level || 'unknown'}`,
            lemma: word.lemma || word.word  // Ensure lemma is always set
          }))

          const updatedChunks = [...chunks]
          updatedChunks[chunkIndex] = {
            ...updatedChunks[chunkIndex],
            vocabulary: vocabularyWithIds,
            subtitlePath: progress.subtitle_path,
            translationPath: progress.translation_path || undefined,
            isProcessed: true
          }
          setChunks(updatedChunks)
          setGameWords(vocabularyWithIds)

          logger.userAction('Entering vocabulary game phase', 'ChunkedLearningFlow', {
            wordsToLearn: progress.vocabulary?.length || 0,
            chunkIndex: currentChunk + 1
          })
          // Move to game phase
          setCurrentPhase('game')
          return
        }

        if (progress.status === 'error') {
          console.error(`[ChunkedLearningFlow] ❌ Processing FAILED: ${progress.message}`)
          toast.error(`Processing failed: ${progress.message}`)
          return
        }

        attempts++
        if (attempts < maxAttempts) {
          console.log(`[ChunkedLearningFlow] Status: ${progress.status}, Progress: ${progress.progress}%, will poll again in 3s`)
          setTimeout(poll, 3000) // Poll every 3 seconds
        } else {
          console.error(`[ChunkedLearningFlow] ⏱️ Processing TIMEOUT after ${maxAttempts} attempts`)
          toast.error('Processing timeout')
        }
      } catch (error: any) {
        console.error('[ChunkedLearningFlow] ❌ Error polling progress:', error)

        // Check if this is an authentication error (401 Unauthorized)
        if (error?.response?.status === 401 || error?.status === 401 ||
            error?.message?.includes('401') || error?.message?.includes('Unauthorized')) {
          console.error('[ChunkedLearningFlow] 🔒 Authentication failed - stopping polling')
          toast.error('Session expired. Please log in again.')

          // Clear authentication and redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_id')

          // Navigate to login page
          navigate('/login')
          return // Stop polling completely
        }

        attempts++
        if (attempts < maxAttempts) {
          // Exponential backoff: increase interval each time, max 30 seconds
          pollInterval = Math.min(pollInterval * 1.5, 30000)
          console.log(`[ChunkedLearningFlow] Retrying poll in ${pollInterval/1000} seconds...`)
          setTimeout(poll, pollInterval)
        } else {
          console.error(`[ChunkedLearningFlow] Failed after ${maxAttempts} attempts`)
          toast.error('Processing failed. Please try again.')
        }
      }
    }

    poll()
  }

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
      // Use existing mark-known endpoint with concept_id
      // If no concept_id, skip saving (will be fixed after server restart)
      if (!wordData.concept_id) {
        logger.warn('ChunkedLearningFlow', 'Skipping save - no concept_id (needs server restart)', { word })
        toast.error(`Cannot save "${word}" - server restart needed`, { duration: 2000 })
        return
      }

      const res = await markWordKnownApiVocabularyMarkKnownPost({
        requestBody: {
          concept_id: wordData.concept_id,
          known: known
        }
      }) as any

      const respWord = res?.word ?? word
      const respLemma = res?.lemma ?? undefined
      const respLevel = res?.level ?? undefined
      logger.info('ChunkedLearningFlow', 'Word progress saved to database', {
        word: respWord,
        lemma: respLemma,
        level: respLevel,
        known
      })

      // Dismiss loading toast and show success
      toast.dismiss(loadingToast)
      toast.success('✓ Progress saved', { duration: 1500 })
    } catch (error) {
      logger.error('ChunkedLearningFlow', 'Failed to save word progress', { word, error })

      // Dismiss loading toast and show error
      toast.dismiss(loadingToast)
      toast.error(`Failed to save progress for "${word}". Will retry automatically.`, { duration: 3000 })

      // Retry once after delay
      setTimeout(async () => {
        try {
          if (!wordData.concept_id) {
            return  // Skip retry if no concept_id
          }
          await markWordKnownApiVocabularyMarkKnownPost({
            requestBody: {
              concept_id: wordData.concept_id,
              known: known
            }
          })
          toast.success('Progress saved on retry')
        } catch (retryError) {
          // Silent fail on retry - don't block the game
          logger.error('ChunkedLearningFlow', 'Retry also failed', { word, retryError })
        }
      }, 2000)
    }
  }

  // Handle game completion with second-pass filtering
  const handleGameComplete = async (knownWords: string[], unknownWords: string[]) => {
    logger.userAction('Vocabulary game completed', 'ChunkedLearningFlow', {
      knownWords: knownWords.length,
      unknownWords: unknownWords.length,
      totalWords: knownWords.length + unknownWords.length,
      chunkIndex: currentChunk + 1
    })

    setLearnedWords(prev => new Set([...prev, ...knownWords]))

    // Apply selective translations if there are known words
    if (knownWords.length > 0 && chunks[currentChunk]?.subtitlePath) {
      logger.info('ChunkedLearningFlow', 'Applying selective translations', {
        knownWords: knownWords.length,
        subtitlePath: chunks[currentChunk].subtitlePath
      })

      try {
        // Call backend to apply selective translations based on known words
        const response = await fetch(`${OpenAPI.BASE}/api/process/apply-selective-translations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            srt_path: chunks[currentChunk].subtitlePath,
            known_words: knownWords,
            user_id: localStorage.getItem('user_id') || ''
          })
        })

        if (response.ok) {
          const result = await response.json()
          logger.info('ChunkedLearningFlow', 'Selective translations applied', {
            newTranslationPath: result.translation_path
          })

          // Update the chunk with the new translation file path
          const updatedChunks = [...chunks]
          updatedChunks[currentChunk] = {
            ...updatedChunks[currentChunk],
            translationPath: result.translation_path
          }
          setChunks(updatedChunks)
        } else {
          logger.warn('ChunkedLearningFlow', 'Selective translation failed', {
            status: response.status
          })
        }
      } catch (error) {
        logger.error('ChunkedLearningFlow', 'Error applying selective translations', { error })
        // Continue with existing translations
      }
    }

    logger.userAction('Entering video playback phase', 'ChunkedLearningFlow', {
      chunkIndex: currentChunk + 1,
      totalLearnedWords: learnedWords.size + knownWords.length
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
        translationPath: processingStatus.translation_path || undefined
      }
      setChunks(updatedChunks)
      logger.info('ChunkedLearningFlow', 'Updated chunk with subtitle paths', {
        chunkIndex: currentChunk + 1,
        subtitlePath: processingStatus.subtitle_path,
        translationPath: processingStatus.translation_path || undefined
      })
    }

    logger.userAction('Skipped vocabulary game', 'ChunkedLearningFlow', {
      chunkIndex: currentChunk + 1,
      vocabularyCount: processingStatus?.vocabulary?.length || 0
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
          progressPercent: Math.round(((currentChunk + 1) / chunks.length) * 100)
        }
      )
      setCurrentChunk(prev => prev + 1)
      setCurrentPhase('processing')
    } else {
      logger.userAction(
        reason === 'completed'
          ? 'Episode completed!'
          : 'Episode skipped to completion',
        'ChunkedLearningFlow',
        {
          totalChunks: chunks.length,
          totalLearnedWords: learnedWords.size,
          videoTitle: videoInfo?.title
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
      totalChunks: chunks.length
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
  }, [chunks, profileLoaded])

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
          />
        )

      case 'game':
        return (
          <VocabularyGame
            words={gameWords as any}
            onWordAnswered={handleWordAnswered}
            onComplete={handleGameComplete}
            onSkip={handleSkipGame}
            episodeTitle={videoInfo.title}
            chunkInfo={{
              current: currentChunk + 1,
              total: chunks.length,
              duration: `${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`
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
              duration: `${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`
            }}
            targetLanguage={activeLanguages?.target}
            nativeLanguage={activeLanguages?.native}
          />
        )

      default:
        return null
    }
  }

  return (
    <>
      {renderPhase()}
    </>
  )
}
