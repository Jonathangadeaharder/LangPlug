import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { ProcessingScreen } from './ProcessingScreen'
import { VocabularyGame } from './VocabularyGame'
import { ChunkedLearningPlayer } from './ChunkedLearningPlayer'
import { videoService, handleApiError } from '@/services/api'
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
  const { series, episode } = useParams<{ series: string; episode: string }>()
  
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
  const [taskId, setTaskId] = useState<string | null>(null)
  const [gameWords, setGameWords] = useState<VocabularyWord[]>([])
  const [learnedWords, setLearnedWords] = useState<Set<string>>(new Set())

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
        isProcessed: false
      })
    }
    console.log(`[ChunkedLearningFlow] Created ${newChunks.length} chunks`)
    setChunks(newChunks)
  }, [videoInfo.duration, chunkDurationMinutes])

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
        
        logger.userAction(`Start processing chunk ${currentChunk + 1}`, {
          chunkRange: `${formatTime(chunks[currentChunk].startTime)} - ${formatTime(chunks[currentChunk].endTime)}`,
          videoTitle: videoInfo.title
        })
        
        setCurrentPhase('processing')
        const chunk = chunks[currentChunk]
        
        try {
          logger.chunkProcessing(`Starting chunk ${currentChunk + 1} processing`, {
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
            const response = await videoService.processChunk(videoInfo.path, chunk.startTime, chunk.endTime)
            setTaskId(response.task_id)
            
            logger.chunkProcessing('Backend task started', {
              taskId: response.task_id,
              chunkIndex: currentChunk + 1,
              status: response.status
            })
            console.log(`[ChunkedLearningFlow] Task ID received: ${response.task_id}`)
            
            // Start polling for progress
            console.log(`[ChunkedLearningFlow] Starting progress polling...`)
            pollProgress(response.task_id, chunkIndex)
          } catch (error) {
            console.error('[ChunkedLearningFlow] ❌ Failed to start chunk processing:', error)
            handleApiError(error)
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
      const response = await videoService.processChunk(videoInfo.path, chunk.startTime, chunk.endTime)
      setTaskId(response.task_id)
      
      logger.chunkProcessing('Backend task started', {
        taskId: response.task_id,
        chunkIndex: currentChunk + 1,
        status: response.status
      })
      console.log(`[ChunkedLearningFlow] Task ID received: ${response.task_id}`)
      
      // Start polling for progress
      console.log(`[ChunkedLearningFlow] Starting progress polling...`)
      pollProgress(response.task_id, chunkIndex)
    } catch (error) {
      console.error('[ChunkedLearningFlow] ❌ Failed to start chunk processing:', error)
      handleApiError(error)
      toast.error('Failed to process chunk')
    }
  }

  // Poll for processing progress
  const pollProgress = async (taskId: string, chunkIndex: number) => {
    console.log(`[ChunkedLearningFlow] 🔄 Starting progress polling for task: ${taskId}, chunk: ${chunkIndex}`)
    const maxAttempts = 180 // 15 minutes max
    let attempts = 0

    const poll = async () => {
      try {
        logger.debug('ChunkedLearningFlow', `Polling attempt ${attempts + 1}/${maxAttempts}`, { taskId })
        const progress = await videoService.getTaskProgress(taskId)
        logger.chunkProcessing('Progress update', {
          status: progress.status,
          progress: progress.progress,
          step: progress.current_step,
          vocabularyCount: progress.vocabulary?.length || 0
        })
        setProcessingStatus(progress)

        if (progress.status === 'completed') {
          logger.chunkProcessing('✅ PROCESSING COMPLETED!', {
            chunkIndex: currentChunk + 1,
            vocabularyCount: progress.vocabulary?.length || 0,
            subtitlePath: progress.subtitle_path,
            translationPath: progress.translation_path
          })
          
          // Update chunk data with results
          const updatedChunks = [...chunks]
          updatedChunks[chunkIndex] = {
            ...updatedChunks[chunkIndex],
            vocabulary: progress.vocabulary || [],
            subtitlePath: progress.subtitle_path,
            translationPath: progress.translation_path,
            isProcessed: true
          }
          setChunks(updatedChunks)
          setGameWords(progress.vocabulary || [])
          
          logger.userAction('🎮 Entering vocabulary game phase', {
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
      } catch (error) {
        console.error('[ChunkedLearningFlow] ❌ Error polling progress:', error)
        attempts++
        if (attempts < maxAttempts) {
          console.log(`[ChunkedLearningFlow] Retrying poll in 3 seconds...`)
          setTimeout(poll, 3000)
        } else {
          console.error(`[ChunkedLearningFlow] Failed after ${maxAttempts} attempts`)
        }
      }
    }

    poll()
  }

  // Handle game completion
  const handleGameComplete = (knownWords: string[], unknownWords: string[]) => {
    logger.userAction('🎮 Vocabulary game completed', {
      knownWords: knownWords.length,
      unknownWords: unknownWords.length,
      totalWords: knownWords.length + unknownWords.length,
      chunkIndex: currentChunk + 1
    })
    
    setLearnedWords(prev => new Set([...prev, ...knownWords]))
    logger.userAction('📺 Entering video playback phase', {
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
        translationPath: processingStatus.translation_path
      }
      setChunks(updatedChunks)
      logger.chunkProcessing('Updated chunk with subtitle paths', {
        chunkIndex: currentChunk + 1,
        subtitlePath: processingStatus.subtitle_path,
        translationPath: processingStatus.translation_path
      })
    }
    
    logger.userAction('⏭️ Skipped vocabulary game', {
      chunkIndex: currentChunk + 1,
      vocabularyCount: processingStatus?.vocabulary?.length || 0
    })
    setCurrentPhase('video')
  }

  // Handle video completion
  const handleVideoComplete = () => {
    if (currentChunk < chunks.length - 1) {
      logger.userAction('📹 Chunk video completed, advancing', {
        completedChunk: currentChunk + 1,
        nextChunk: currentChunk + 2,
        totalChunks: chunks.length,
        progressPercent: Math.round(((currentChunk + 1) / chunks.length) * 100)
      })
      setCurrentChunk(prev => prev + 1)
      setCurrentPhase('processing')
    } else {
      logger.userAction('🎉 Episode completed!', {
        totalChunks: chunks.length,
        totalLearnedWords: learnedWords.size,
        videoTitle: videoInfo?.title
      })
      onComplete?.()
    }
  }

  // Start processing first chunk on mount
  useEffect(() => {
    console.log(`[ChunkedLearningFlow] useEffect triggered - chunks.length: ${chunks.length}, currentChunk: ${currentChunk}, currentPhase: ${currentPhase}`)
    if (chunks.length > 0 && currentChunk === 0 && currentPhase === 'processing') {
      console.log(`[ChunkedLearningFlow] 🚀 Starting processing of first chunk`)
      processChunk(0)
    }
  }, [chunks])

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
            words={gameWords}
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
          chunkIndex: currentChunk
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
            learnedWords={Array.from(learnedWords)}
            chunkInfo={{
              current: currentChunk + 1,
              total: chunks.length,
              duration: `${formatTime(chunk.startTime)} - ${formatTime(chunk.endTime)}`
            }}
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