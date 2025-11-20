/**
 * Interactive Subtitle Example
 * Demonstrates usage of interactive subtitle components with real-time highlighting
 *
 * This example shows:
 * 1. SyncedSubtitleDisplay with video playback synchronization
 * 2. Hover-based word translation
 * 3. Keyboard navigation between segments
 * 4. Known/unknown word highlighting
 */
import React, { useRef, useEffect, useState } from 'react'
import SyncedSubtitleDisplay from '../SyncedSubtitleDisplay'
import InteractiveSubtitle from '../InteractiveSubtitle'
import { useSubtitleSeek } from '../../hooks/useSubtitleSeek'
import { SubtitleSegment, subtitleSyncService } from '../../services/subtitleSyncService'

const EXAMPLE_SRT = `1
00:00:01,000 --> 00:00:03,500
Guten Tag! Wie geht es Ihnen?

2
00:00:04,000 --> 00:00:06,500
Mir geht es sehr gut, danke.

3
00:00:07,000 --> 00:00:09,500
Das Wetter ist heute wunderbar.

4
00:00:10,000 --> 00:00:12,500
Ja, die Sonne scheint hell.`

const InteractiveSubtitleExample: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [segments, setSegments] = useState<SubtitleSegment[]>([])
  const [isPlaying, setIsPlaying] = useState(false)
  const [useSync, setUseSync] = useState(true)

  // Example known words (user's vocabulary)
  const knownWords = new Set(['guten', 'tag', 'wie', 'es', 'mir', 'gut', 'danke', 'ist', 'ja', 'die'])

  const { seekPreviousSegment, seekNextSegment, seekToSegment } = useSubtitleSeek(videoRef, segments)

  useEffect(() => {
    // Parse example SRT on mount
    const parsedSegments = subtitleSyncService.parseSRT(EXAMPLE_SRT)
    setSegments(parsedSegments)
  }, [])

  useEffect(() => {
    // Keyboard controls
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.code === 'ArrowLeft') {
        e.preventDefault()
        seekPreviousSegment()
      } else if (e.code === 'ArrowRight') {
        e.preventDefault()
        seekNextSegment()
      } else if (e.code === 'Space') {
        e.preventDefault()
        togglePlayPause()
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [seekPreviousSegment, seekNextSegment])

  const togglePlayPause = () => {
    const video = videoRef.current
    if (!video) return

    if (video.paused) {
      video.play()
      setIsPlaying(true)
    } else {
      video.pause()
      setIsPlaying(false)
    }
  }

  const handleWordClick = (_word: string) => {
    // Here you could trigger additional actions like:
    // - Mark word as known/unknown
    // - Add to vocabulary list
    // - Show detailed word information panel
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Interactive Subtitle Demo</h2>

      <div style={styles.videoContainer}>
        {/* Placeholder video element */}
        <video
          ref={videoRef}
          style={styles.video}
          controls
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        >
          <source src="/path/to/example/video.mp4" type="video/mp4" />
          <track kind="captions" src="/path/to/example/captions.vtt" srcLang="de" label="German" />
          Your browser does not support the video tag.
        </video>

        {/* Subtitle overlay */}
        <div style={styles.subtitleOverlay}>
          {useSync ? (
            <SyncedSubtitleDisplay
              segments={segments}
              videoRef={videoRef}
              knownWords={knownWords}
              language="de"
              showTranslation={true}
              onWordClick={handleWordClick}
            />
          ) : (
            segments.length > 0 && (
              <InteractiveSubtitle
                text={segments[0].text}
                language="de"
                knownWords={knownWords}
                showTranslation={true}
              />
            )
          )}
        </div>
      </div>

      {/* Controls */}
      <div style={styles.controls}>
        <button onClick={togglePlayPause} style={styles.button}>
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button onClick={seekPreviousSegment} style={styles.button}>
          Previous Sentence (←)
        </button>
        <button onClick={seekNextSegment} style={styles.button}>
          Next Sentence (→)
        </button>
        <button onClick={() => seekToSegment(0)} style={styles.button}>
          Restart
        </button>
        <button onClick={() => setUseSync(!useSync)} style={styles.button}>
          {useSync ? 'Static Mode' : 'Sync Mode'}
        </button>
      </div>

      {/* Segment list */}
      <div style={styles.segmentList}>
        <h3 style={styles.subtitle}>Subtitle Segments</h3>
        {segments.map((segment, index) => (
          <div
            key={segment.id}
            style={styles.segmentItem}
            role="button"
            tabIndex={0}
            onClick={() => seekToSegment(index)}
            onKeyDown={e => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                seekToSegment(index)
              }
            }}
          >
            <strong>{index + 1}.</strong> {segment.text}
            <span style={styles.timestamp}>
              ({segment.start.toFixed(1)}s - {segment.end.toFixed(1)}s)
            </span>
          </div>
        ))}
      </div>

      {/* Feature explanation */}
      <div style={styles.infoBox}>
        <h3 style={styles.subtitle}>Features Demonstrated</h3>
        <ul style={styles.list}>
          <li>
            <strong>Real-time word highlighting:</strong> Words light up as they're spoken
          </li>
          <li>
            <strong>Hover translation:</strong> Hover over any word to see its translation
          </li>
          <li>
            <strong>Known/unknown words:</strong> Green = known, Orange = needs practice
          </li>
          <li>
            <strong>Keyboard navigation:</strong> ← Previous sentence, → Next sentence, Space = Play/Pause
          </li>
          <li>
            <strong>Click to seek:</strong> Click any segment in the list to jump to it
          </li>
          <li>
            <strong>Translation caching:</strong> Translations are cached locally for 7 days
          </li>
        </ul>
      </div>

      {/* Technical notes */}
      <div style={styles.techNotes}>
        <h3 style={styles.subtitle}>Implementation Notes</h3>
        <pre style={styles.code}>
{`// Basic usage in your component:
import SyncedSubtitleDisplay from './components/SyncedSubtitleDisplay'
import { subtitleSyncService } from './services/subtitleSyncService'

// Parse SRT file
const segments = subtitleSyncService.parseSRT(srtContent)

// Render with video
<SyncedSubtitleDisplay
  segments={segments}
  videoRef={videoRef}
  knownWords={userKnownWords}
  language="de"
  showTranslation={true}
  onWordClick={(word) => handleWordAction(word)}
/>`}
        </pre>
      </div>
    </div>
  )
}

// Inline styles for demo purposes
const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    color: '#333',
  },
  title: {
    fontSize: '28px',
    fontWeight: 'bold',
    marginBottom: '20px',
    color: '#1a1a1a',
  },
  subtitle: {
    fontSize: '20px',
    fontWeight: '600',
    marginBottom: '12px',
    color: '#333',
  },
  videoContainer: {
    position: 'relative',
    backgroundColor: '#000',
    borderRadius: '8px',
    overflow: 'hidden',
    marginBottom: '20px',
  },
  video: {
    width: '100%',
    display: 'block',
  },
  subtitleOverlay: {
    position: 'absolute',
    bottom: '60px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '90%',
    maxWidth: '800px',
  },
  controls: {
    display: 'flex',
    gap: '10px',
    flexWrap: 'wrap',
    marginBottom: '30px',
  },
  button: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '500',
    backgroundColor: '#2196f3',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  segmentList: {
    marginBottom: '30px',
  },
  segmentItem: {
    padding: '12px',
    marginBottom: '8px',
    backgroundColor: '#f5f5f5',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    lineHeight: '1.6',
  },
  timestamp: {
    fontSize: '12px',
    color: '#666',
    marginLeft: '8px',
  },
  infoBox: {
    backgroundColor: '#e3f2fd',
    padding: '20px',
    borderRadius: '8px',
    marginBottom: '30px',
  },
  list: {
    lineHeight: '1.8',
  },
  techNotes: {
    backgroundColor: '#f5f5f5',
    padding: '20px',
    borderRadius: '8px',
  },
  code: {
    backgroundColor: '#1a1a1a',
    color: '#81c784',
    padding: '16px',
    borderRadius: '6px',
    overflow: 'auto',
    fontSize: '13px',
    lineHeight: '1.5',
  },
}

export default InteractiveSubtitleExample
