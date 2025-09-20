/**
 * DEPRECATED: Legacy SRT parsing utility
 * 
 * This file contained duplicate SRT parsing logic that has been replaced
 * with a proper API-based approach. The frontend no longer parses SRT files
 * directly - instead, it uses the backend API as the single source of truth.
 * 
 * Migration Guide:
 * ================
 * 
 * OLD APPROACH (deprecated):
 * ```ts
 * import { parseSRT } from './utils'
 * const parsed = parseSRT(srtContent)
 * ```
 * 
 * NEW APPROACH (recommended):
 * ```ts
 * import { srtApi } from '../utils/srtApi'
 * const result = await srtApi.parseSRTContent(srtContent)
 * const segments = result.segments
 * ```
 * 
 * Benefits of the new approach:
 * - Single source of truth for SRT parsing logic (backend)
 * - Better error handling and validation
 * - Consistent parsing behavior across the application
 * - Proper testing with mocked API responses
 * - No code duplication between frontend and backend
 * 
 * For proper tests, see: subtitle-parsing.test.ts
 */

// Re-export the API client for migration compatibility
export { srtApi as SRTApi, srtUtils } from '../utils/srtApi'

console.warn(
  'DEPRECATION WARNING: This test utility file is deprecated. ' +
  'Use the new SRT API client from ../utils/srtApi instead. ' +
  'See subtitle-parsing.test.ts for proper test examples.'
)

/**
 * DEPRECATED: Legacy synchronous SRT parser for backward compatibility
 * Only used in deprecated tests. New code should use srtApi.parseSRTContent()
 */
export function parseSRT(content: string): Array<{ start: number; end: number; text: string; translation: string }> {
  if (!content.trim()) return []

  const blocks = content.split(/\n\s*\n/).filter(block => block.trim())
  const result: Array<{ start: number; end: number; text: string; translation: string }> = []

  for (const block of blocks) {
    const lines = block.split('\n').filter(line => line.trim())
    if (lines.length < 3) continue // Need at least index, timestamp, text

    const timestampLine = lines[1]
    const timestampMatch = timestampLine.match(/(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})/)
    if (!timestampMatch) continue

    const [, startStr, endStr] = timestampMatch

    // Parse timestamps to seconds
    const start = parseTimestamp(startStr)
    const end = parseTimestamp(endStr)

    // Get text lines
    const textLines = lines.slice(2)
    let text = ''
    let translation = ''

    for (const line of textLines) {
      if (line.includes('|')) {
        const parts = line.split('|').map(p => p.trim())
        text = parts[0] || ''
        translation = parts[1] || ''
      } else {
        text += (text ? '\n' : '') + line
      }
    }

    result.push({ start, end, text, translation })
  }

  return result
}

function parseTimestamp(timestamp: string): number {
  const match = timestamp.match(/(\d{2}):(\d{2}):(\d{2}),(\d{3})/)
  if (!match) return 0

  const [, hours, minutes, seconds, milliseconds] = match.map(Number)
  return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
}