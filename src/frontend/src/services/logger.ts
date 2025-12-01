/**
 * Frontend logging service for debugging and monitoring
 * Logs to console and can send logs to backend for file storage
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

interface LogEntry {
  timestamp: string
  level: string
  category: string
  message: string
  data?: Record<string, unknown>
  error?: string
  stack?: string
  url?: string
  userAgent?: string
  userId?: string
}

class Logger {
  private logLevel: LogLevel = LogLevel.DEBUG
  private logs: LogEntry[] = []
  private maxLogs = 1000
  private apiEnabled = true
  private batchQueue: LogEntry[] = []
  private readonly batchSize = 20 // Increased for efficiency
  private readonly batchTimeout = 10000 // 10 seconds - less frequent sends
  private batchTimer: ReturnType<typeof setTimeout> | null = null
  private isSending = false

  constructor() {
    // Set log level based on environment
    const envLogLevel = import.meta.env.VITE_LOG_LEVEL || 'DEBUG'
    this.logLevel = LogLevel[envLogLevel as keyof typeof LogLevel] || LogLevel.DEBUG

    // API logging can be disabled via environment variable if needed
    this.apiEnabled = import.meta.env.VITE_ENABLE_API_LOGGING !== 'false'

    // Set up global error handler
    this.setupGlobalErrorHandler()

    // Set up unhandled promise rejection handler
    this.setupUnhandledRejectionHandler()

    // Log frontend startup
    this.info('Frontend Logger', 'Logger initialized', {
      logLevel: LogLevel[this.logLevel],
      apiEnabled: this.apiEnabled,
      maxLogs: this.maxLogs,
    })
  }

  private setupGlobalErrorHandler() {
    window.addEventListener('error', event => {
      this.error('Global Error', 'Uncaught error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error?.toString(),
        stack: event.error?.stack,
      })
    })
  }

  private setupUnhandledRejectionHandler() {
    window.addEventListener('unhandledrejection', event => {
      this.error('Unhandled Promise', 'Promise rejection', {
        reason: event.reason?.toString(),
        stack: event.reason?.stack,
      })
    })
  }

  private createLogEntry(
    level: LogLevel,
    category: string,
    message: string,
    data?: Record<string, unknown>,
    error?: Error
  ): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: LogLevel[level],
      category,
      message,
      url: window.location.href,
      userAgent: navigator.userAgent,
    }

    if (data !== undefined) {
      entry.data = data
    }

    if (error) {
      entry.error = error.toString()
      entry.stack = error.stack
    }

    // Add user ID if available
    const authStore = localStorage.getItem('auth-store')
    if (authStore) {
      try {
        const parsed = JSON.parse(authStore)
        if (parsed.state?.user?.id) {
          entry.userId = parsed.state.user.id.toString()
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }

    return entry
  }

  private shouldLog(level: LogLevel): boolean {
    return level >= this.logLevel
  }

  private addLogEntry(entry: LogEntry) {
    // Add to memory buffer
    this.logs.push(entry)

    // Keep only recent logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs)
    }

    // Send to backend if enabled (using batching)
    if (this.apiEnabled) {
      this.addToBatch(entry)
    }
  }

  private addToBatch(entry: LogEntry) {
    // Only send INFO and above to backend to avoid spam
    if (LogLevel[entry.level as keyof typeof LogLevel] < LogLevel.INFO) {
      return
    }

    this.batchQueue.push(entry)

    // If batch is full, send immediately
    if (this.batchQueue.length >= this.batchSize) {
      this.flushBatch()
    } else {
      // Otherwise, schedule batch send
      this.scheduleBatchSend()
    }
  }

  private scheduleBatchSend() {
    // Clear existing timer
    if (this.batchTimer) {
      clearTimeout(this.batchTimer)
    }

    // Schedule new batch send
    this.batchTimer = setTimeout(() => {
      this.flushBatch()
    }, this.batchTimeout)
  }

  private async flushBatch() {
    // Clear timer
    if (this.batchTimer) {
      clearTimeout(this.batchTimer)
      this.batchTimer = null
    }

    // Skip if already sending or queue is empty
    if (this.isSending || this.batchQueue.length === 0) {
      return
    }

    // Take current batch and clear queue
    const batch = [...this.batchQueue]
    this.batchQueue = []
    this.isSending = true

    try {
      await this.sendBatchToBackend(batch)
    } catch (error) {
      // Silently fail backend logging
      if (import.meta.env.DEV) {
        console.warn('Failed to send log batch:', error)
      }
    } finally {
      this.isSending = false
    }
  }

  private async sendBatchToBackend(batch: LogEntry[]) {
    // Use dynamic import for axios to avoid circular dependency issues during initialization
    // if axios tries to log something
    const axios = (await import('axios')).default
    
    const API_BASE_URL =
      import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)

    await axios.post(`${API_BASE_URL}/api/debug/frontend-logs`, { logs: batch }, {
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
      withCredentials: true
    })

    clearTimeout(timeoutId)
  }

  debug(category: string, message: string, data?: Record<string, unknown>) {
    if (!this.shouldLog(LogLevel.DEBUG)) return

    const entry = this.createLogEntry(LogLevel.DEBUG, category, message, data)
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.debug(`[${category}] ${message}`, data || '')
    }
    this.addLogEntry(entry)
  }

  info(category: string, message: string, data?: Record<string, unknown>) {
    if (!this.shouldLog(LogLevel.INFO)) return

    const entry = this.createLogEntry(LogLevel.INFO, category, message, data)
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.info(`[${category}] ${message}`, data || '')
    }
    this.addLogEntry(entry)
  }

  warn(category: string, message: string, data?: Record<string, unknown> | unknown) {
    if (!this.shouldLog(LogLevel.WARN)) return

    // Convert unknown data to Record<string, unknown> for safe logging
    const safeData = data !== undefined && data !== null && typeof data === 'object'
      ? (data as Record<string, unknown>)
      : data !== undefined ? { value: data } : undefined

    const entry = this.createLogEntry(LogLevel.WARN, category, message, safeData)
    console.warn(`[${category}] ${message}`, safeData || '')
    this.addLogEntry(entry)
  }

  error(category: string, message: string, data?: Record<string, unknown> | unknown, error?: Error) {
    if (!this.shouldLog(LogLevel.ERROR)) return

    // Convert unknown data to Record<string, unknown> for safe logging
    const safeData = data !== undefined && data !== null && typeof data === 'object'
      ? (data as Record<string, unknown>)
      : data !== undefined ? { value: data } : undefined

    const entry = this.createLogEntry(LogLevel.ERROR, category, message, safeData, error)
    console.error(`[${category}] ${message}`, safeData || '', error || '')
    this.addLogEntry(entry)
  }

  // API-specific logging methods
  apiRequest(method: string, url: string, data?: Record<string, unknown>) {
    this.debug('API', `Request: ${method} ${url}`, { method, url, data })
  }

  apiResponse(
    method: string,
    url: string,
    status: number,
    data?: Record<string, unknown>,
    duration?: number
  ) {
    const level = status >= 400 ? LogLevel.ERROR : LogLevel.DEBUG
    const entry = this.createLogEntry(level, 'API', `Response: ${status} ${method} ${url}`, {
      method,
      url,
      status,
      data,
      duration,
    })

    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      const logFn = status >= 400 ? console.error : console.debug
      logFn(`[API] ${status} ${method} ${url}${duration ? ` (${duration}ms)` : ''}`, { data })
    }
    this.addLogEntry(entry)
  }

  // User interaction logging
  userAction(action: string, component: string, data?: Record<string, unknown>) {
    this.info('User Action', `${action} in ${component}`, data)
  }

  // Navigation logging
  navigation(from: string, to: string, data?: Record<string, unknown>) {
    this.info('Navigation', `${from} → ${to}`, data)
  }

  // Performance logging
  performance(metric: string, value: number, unit = 'ms') {
    this.debug('Performance', `${metric}: ${value}${unit}`, { metric, value, unit })
  }

  // Get recent logs for debugging
  getRecentLogs(count = 50): LogEntry[] {
    return this.logs.slice(-count)
  }

  // Clear logs
  clearLogs() {
    this.logs = []
    this.info('Logger', 'Logs cleared')
  }

  // Export logs as JSON
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }
}

// Create singleton instance
export const logger = new Logger()

// Add to window for debugging
if (typeof window !== 'undefined') {
  interface WindowWithLogger extends Window {
    logger: Logger
  }
  ;(window as unknown as WindowWithLogger).logger = logger
}
