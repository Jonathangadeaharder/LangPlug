/**
 * SRT API Client
 *
 * This module provides a TypeScript client for the backend SRT utilities API.
 * It replaces the duplicate SRT parsing logic in the frontend, ensuring the
 * backend is the single source of truth for SRT processing.
 */

export interface SRTSegment {
  index: number
  start_time: number
  end_time: number
  text: string
  original_text: string
  translation: string
}

export interface ParseSRTResponse {
  segments: SRTSegment[]
  total_segments: number
  duration: number
}

export interface ValidationResult {
  valid: boolean
  total_segments?: number
  issues: string[]
  error?: string
}

/**
 * SRT API client class for handling all SRT-related operations
 */
export class SRTApiClient {
  private baseUrl: string

  constructor(baseUrl = '/api/srt') {
    this.baseUrl = baseUrl
  }

  /**
   * Parse SRT content using the backend API
   *
   * @param content - SRT file content as string
   * @returns Promise with parsed SRT data
   */
  async parseSRTContent(content: string): Promise<ParseSRTResponse> {
    const response = await fetch(`${this.baseUrl}/parse`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to parse SRT content')
    }

    return response.json()
  }

  /**
   * Parse an SRT file using the backend API
   *
   * @param file - SRT file to upload and parse
   * @returns Promise with parsed SRT data
   */
  async parseSRTFile(file: File): Promise<ParseSRTResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseUrl}/parse-file`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to parse SRT file')
    }

    return response.json()
  }

  /**
   * Convert SRT segments back to SRT format
   *
   * @param segments - Array of SRT segments
   * @returns Promise with SRT content as string
   */
  async convertToSRT(segments: SRTSegment[]): Promise<string> {
    const response = await fetch(`${this.baseUrl}/convert-to-srt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ segments }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to convert to SRT format')
    }

    return response.text()
  }

  /**
   * Validate SRT content
   *
   * @param content - SRT content to validate
   * @returns Promise with validation results
   */
  async validateSRT(content: string): Promise<ValidationResult> {
    const params = new URLSearchParams({ content })
    const response = await fetch(`${this.baseUrl}/validate?${params}`)

    if (!response.ok) {
      throw new Error('Failed to validate SRT content')
    }

    return response.json()
  }

  /**
   * Download SRT segments as a file
   *
   * @param segments - Array of SRT segments
   * @param filename - Desired filename for download
   */
  async downloadAsSRT(segments: SRTSegment[], filename = 'subtitles.srt'): Promise<void> {
    const srtContent = await this.convertToSRT(segments)

    // Create blob and download
    const blob = new Blob([srtContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
}

/**
 * Default SRT API client instance
 */
export const srtApi = new SRTApiClient()

/**
 * Utility functions for working with SRT data
 */
export const srtUtils = {
  /**
    * Format time in seconds to SRT timestamp format (HH:MM:SS,mmm)
    */
  formatTimestamp(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    const milliseconds = Math.round((seconds % 1) * 1000)

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${secs.toString().padStart(2, '0')},${milliseconds
      .toString()
      .padStart(3, '0')}`
  },

  /**
   * Parse SRT timestamp to seconds
   */
  parseTimestamp(timestamp: string): number {
    const match = timestamp.match(/(\d{2}):(\d{2}):(\d{2}),(\d{3})/)
    if (!match) {
      throw new Error(`Invalid timestamp format: ${timestamp}`)
    }

    const [, hours, minutes, seconds, milliseconds] = match.map(Number)
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
  },

  /**
   * Get total duration from segments
   */
  getTotalDuration(segments: SRTSegment[]): number {
    if (segments.length === 0) return 0
    return Math.max(...segments.map(s => s.end_time))
  },

  /**
   * Filter segments by time range
   */
  filterByTimeRange(segments: SRTSegment[], startTime: number, endTime: number): SRTSegment[] {
    return segments.filter(segment =>
      segment.start_time >= startTime && segment.end_time <= endTime
    )
  },

  /**
   * Find segment at specific time
   */
  findSegmentAtTime(segments: SRTSegment[], time: number): SRTSegment | undefined {
    return segments.find(segment =>
      time >= segment.start_time && time <= segment.end_time
    )
  }
}
