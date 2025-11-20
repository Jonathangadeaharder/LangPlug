import { describe, it, expect } from 'vitest'
import { subtitleSyncService } from '../subtitleSyncService'

const SAMPLE_SRT = `1
00:00:01,000 --> 00:00:03,500
Hello world

2
00:00:04,000 --> 00:00:06,500
This is a test

3
00:00:07,000 --> 00:00:10,000
Multiple words here`

describe('subtitleSyncService', () => {
  describe('parseSRT', () => {
    it('should parse valid SRT format', () => {
      const segments = subtitleSyncService.parseSRT(SAMPLE_SRT)

      expect(segments).toHaveLength(3)
      expect(segments[0].id).toBe('segment-1-3.5')
      expect(segments[0].text).toBe('Hello world')
      expect(segments[0].start).toBeCloseTo(1.0, 1)
      expect(segments[0].end).toBeCloseTo(3.5, 1)
    })

    it('should parse timestamps correctly', () => {
      const segments = subtitleSyncService.parseSRT(SAMPLE_SRT)

      expect(segments[1].start).toBeCloseTo(4.0, 1)
      expect(segments[1].end).toBeCloseTo(6.5, 1)
    })

    it('should handle empty SRT', () => {
      const segments = subtitleSyncService.parseSRT('')
      expect(segments).toHaveLength(0)
    })

    it('should skip malformed entries', () => {
      const malformedSRT = `1
00:00:01,000 --> 00:00:03,500
Valid entry

invalid entry without timestamp

2
00:00:04,000 --> 00:00:06,500
Another valid entry`

      const segments = subtitleSyncService.parseSRT(malformedSRT)
      expect(segments).toHaveLength(2)
      expect(segments[0].text).toBe('Valid entry')
      expect(segments[1].text).toBe('Another valid entry')
    })

    it('should handle multiline text', () => {
      const multilineSRT = `1
00:00:01,000 --> 00:00:03,500
First line
Second line
Third line`

      const segments = subtitleSyncService.parseSRT(multilineSRT)
      expect(segments).toHaveLength(1)
      expect(segments[0].text).toContain('First line')
      expect(segments[0].text).toContain('Second line')
    })
  })

  describe('generateWordTimestamps', () => {
    it('should generate word timestamps for segment', () => {
      const segment = {
        id: '1',
        start: 1.0,
        end: 3.0,
        text: 'Hello world test',
        words: []
      }

      const wordTimestamps = subtitleSyncService.generateWordTimestamps(segment)

      expect(wordTimestamps).toHaveLength(3)
      expect(wordTimestamps[0].word).toBe('Hello')
      expect(wordTimestamps[1].word).toBe('world')
      expect(wordTimestamps[2].word).toBe('test')
    })

    it('should distribute time evenly across words', () => {
      const segment = {
        id: '1',
        start: 0.0,
        end: 3.0,
        text: 'one two three',
        words: []
      }

      const wordTimestamps = subtitleSyncService.generateWordTimestamps(segment)

      expect(wordTimestamps[0].start).toBeCloseTo(0.0, 1)
      expect(wordTimestamps[0].end).toBeCloseTo(1.0, 1)
      expect(wordTimestamps[1].start).toBeCloseTo(1.0, 1)
      expect(wordTimestamps[1].end).toBeCloseTo(2.0, 1)
      expect(wordTimestamps[2].start).toBeCloseTo(2.0, 1)
      expect(wordTimestamps[2].end).toBeCloseTo(3.0, 1)
    })

    it('should handle single word', () => {
      const segment = {
        id: '1',
        start: 1.0,
        end: 2.0,
        text: 'hello',
        words: []
      }

      const wordTimestamps = subtitleSyncService.generateWordTimestamps(segment)

      expect(wordTimestamps).toHaveLength(1)
      expect(wordTimestamps[0].start).toBe(1.0)
      expect(wordTimestamps[0].end).toBe(2.0)
    })

    it('should handle empty text', () => {
      const segment = {
        id: '1',
        start: 1.0,
        end: 2.0,
        text: '',
        words: []
      }

      const wordTimestamps = subtitleSyncService.generateWordTimestamps(segment)

      expect(wordTimestamps).toHaveLength(0)
    })
  })

  describe('getActiveWordAtTime', () => {
    const segments = [
      {
        id: '1',
        start: 0.0,
        end: 3.0,
        text: 'one two three',
        words: [
          { word: 'one', start: 0.0, end: 1.0 },
          { word: 'two', start: 1.0, end: 2.0 },
          { word: 'three', start: 2.0, end: 3.0 }
        ]
      }
    ]

    it('should return active word at specific time', () => {
      const word = subtitleSyncService.getActiveWordAtTime(segments, 1.5)
      expect(word?.word).toBe('two')
    })

    it('should return null when time is before all segments', () => {
      const word = subtitleSyncService.getActiveWordAtTime(segments, -1.0)
      expect(word).toBeNull()
    })

    it('should return null when time is after all segments', () => {
      const word = subtitleSyncService.getActiveWordAtTime(segments, 10.0)
      expect(word).toBeNull()
    })

    it('should return first word at start time', () => {
      const word = subtitleSyncService.getActiveWordAtTime(segments, 0.0)
      expect(word?.word).toBe('one')
    })

    it('should return last word at end time', () => {
      const word = subtitleSyncService.getActiveWordAtTime(segments, 2.5)
      expect(word?.word).toBe('three')
    })
  })

  describe('getActiveSegmentAtTime', () => {
    const segments = [
      {
        id: '1',
        start: 0.0,
        end: 3.0,
        text: 'first segment',
        words: []
      },
      {
        id: '2',
        start: 4.0,
        end: 7.0,
        text: 'second segment',
        words: []
      }
    ]

    it('should return active segment at specific time', () => {
      const segment = subtitleSyncService.getActiveSegmentAtTime(segments, 5.0)
      expect(segment?.id).toBe('2')
      expect(segment?.text).toBe('second segment')
    })

    it('should return null when time is in gap between segments', () => {
      const segment = subtitleSyncService.getActiveSegmentAtTime(segments, 3.5)
      expect(segment).toBeNull()
    })

    it('should return null when time is before all segments', () => {
      const segment = subtitleSyncService.getActiveSegmentAtTime(segments, -1.0)
      expect(segment).toBeNull()
    })

    it('should return null when time is after all segments', () => {
      const segment = subtitleSyncService.getActiveSegmentAtTime(segments, 10.0)
      expect(segment).toBeNull()
    })

    it('should return segment at exact start time', () => {
      const segment = subtitleSyncService.getActiveSegmentAtTime(segments, 4.0)
      expect(segment?.id).toBe('2')
    })

    it('should return segment at exact end time', () => {
      const segment = subtitleSyncService.getActiveSegmentAtTime(segments, 3.0)
      expect(segment?.id).toBe('1')
    })
  })

  describe('getPreviousSegment', () => {
    const segments = [
      { id: '1', start: 0.0, end: 3.0, text: 'first', words: [] },
      { id: '2', start: 4.0, end: 7.0, text: 'second', words: [] },
      { id: '3', start: 8.0, end: 11.0, text: 'third', words: [] }
    ]

    it('should return previous segment', () => {
      const segment = subtitleSyncService.getPreviousSegment(segments, 5.0)
      expect(segment?.id).toBe('1')
    })

    it('should return null when at first segment', () => {
      const segment = subtitleSyncService.getPreviousSegment(segments, 1.0)
      expect(segment).toBeNull()
    })

    it('should return null when before all segments', () => {
      const segment = subtitleSyncService.getPreviousSegment(segments, -1.0)
      expect(segment).toBeNull()
    })
  })

  describe('getNextSegment', () => {
    const segments = [
      { id: '1', start: 0.0, end: 3.0, text: 'first', words: [] },
      { id: '2', start: 4.0, end: 7.0, text: 'second', words: [] },
      { id: '3', start: 8.0, end: 11.0, text: 'third', words: [] }
    ]

    it('should return next segment', () => {
      const segment = subtitleSyncService.getNextSegment(segments, 2.0)
      expect(segment?.id).toBe('2')
    })

    it('should return null when at last segment', () => {
      const segment = subtitleSyncService.getNextSegment(segments, 9.0)
      expect(segment).toBeNull()
    })

    it('should return null when after all segments', () => {
      const segment = subtitleSyncService.getNextSegment(segments, 20.0)
      expect(segment).toBeNull()
    })

    it('should return first segment when before all segments', () => {
      const segment = subtitleSyncService.getNextSegment(segments, -1.0)
      expect(segment?.id).toBe('1')
    })
  })
})
