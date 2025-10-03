/**
 * SRT API integration tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { SRTApiClient, srtUtils } from '../utils/srtApi'

const testSRT = `1
00:00:01,000 --> 00:00:04,000
This is a test subtitle

2
00:00:05,000 --> 00:00:08,000
This is another test subtitle | This is the translation

3
00:00:10,000 --> 00:00:13,000
Single language subtitle
`

const mockApiResponse = {
  segments: [
    {
      index: 1,
      start_time: 1,
      end_time: 4,
      text: 'This is a test subtitle',
      original_text: 'This is a test subtitle',
      translation: ''
    },
    {
      index: 2,
      start_time: 5,
      end_time: 8,
      text: 'This is another test subtitle',
      original_text: 'This is another test subtitle',
      translation: 'This is the translation'
    },
    {
      index: 3,
      start_time: 10,
      end_time: 13,
      text: 'Single language subtitle',
      original_text: 'Single language subtitle',
      translation: ''
    }
  ],
  total_segments: 3,
  duration: 13
}

describe('SRT API Integration', () => {
  let srtClient: SRTApiClient
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockFetch = vi.fn()
    global.fetch = mockFetch
    srtClient = new SRTApiClient('/api/srt')
  })

  it('parses SRT content via backend API', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockApiResponse
    })

    const result = await srtClient.parseSRTContent(testSRT)

    expect(mockFetch).toHaveBeenCalledWith('/api/srt/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: testSRT })
    })

    expect(result.total_segments).toBe(3)
    expect(result.segments).toHaveLength(3)
    expect(result.segments[0].text).toBe('This is a test subtitle')
  })

  it('handles API parsing errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Invalid SRT format' })
    })

    await expect(srtClient.parseSRTContent('invalid content'))
      .rejects.toThrow('Invalid SRT format')
  })

  it('validates SRT content', async () => {
    const validationResult = {
      valid: true,
      total_segments: 3,
      issues: []
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => validationResult
    })

    const result = await srtClient.validateSRT(testSRT)

    expect(result.valid).toBe(true)
    expect(result.total_segments).toBe(3)
    expect(result.issues).toHaveLength(0)
  })

  it('converts segments to SRT format', async () => {
    const expectedSRT = '1\n00:00:01,000 --> 00:00:04,000\nThis is a test subtitle\n\n'

    mockFetch.mockResolvedValueOnce({
      ok: true,
      text: async () => expectedSRT
    })

    const result = await srtClient.convertToSRT(mockApiResponse.segments)
    expect(result).toBe(expectedSRT)
  })
})

describe('SRT Utilities', () => {
  it('formats timestamps correctly', () => {
    expect(srtUtils.formatTimestamp(0)).toBe('00:00:00,000')
    expect(srtUtils.formatTimestamp(3661.5)).toBe('01:01:01,500')
    expect(srtUtils.formatTimestamp(125.678)).toBe('00:02:05,678')
  })

  it('parses timestamps correctly', () => {
    expect(srtUtils.parseTimestamp('00:00:00,000')).toBe(0)
    expect(srtUtils.parseTimestamp('01:01:01,500')).toBe(3661.5)
    expect(srtUtils.parseTimestamp('00:02:05,678')).toBe(125.678)
  })

  it('calculates total duration from segments', () => {
    const duration = srtUtils.getTotalDuration(mockApiResponse.segments)
    expect(duration).toBe(13)
  })

  it('finds segment at specific time', () => {
    const segment = srtUtils.findSegmentAtTime(mockApiResponse.segments, 6)
    expect(segment?.text).toBe('This is another test subtitle')

    const noSegment = srtUtils.findSegmentAtTime(mockApiResponse.segments, 20)
    expect(noSegment).toBeUndefined()
  })
})
