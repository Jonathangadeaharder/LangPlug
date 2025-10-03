import { Plugin } from 'vite'
import fs from 'fs'
import path from 'path'
import { format } from 'util'

interface LoggerOptions {
  logFile?: string
  includeTimestamp?: boolean
}

export function viteLogger(options: LoggerOptions = {}): Plugin {
  const logFile = options.logFile || 'frontend.log'
  const includeTimestamp = options.includeTimestamp !== false

  const logStream = fs.createWriteStream(path.resolve(process.cwd(), logFile), {
    flags: 'a', // append mode
    encoding: 'utf8'
  })

  const log = (level: string, message: string, ...args: any[]) => {
    const timestamp = includeTimestamp ? new Date().toISOString() : ''
    const formatted = format(message, ...args)
    const logLine = includeTimestamp
      ? `[${timestamp}] [${level}] ${formatted}\n`
      : `[${level}] ${formatted}\n`

    // Write to file
    logStream.write(logLine)

    // Also write to console
    const consoleMethod = level === 'ERROR' ? 'error' : level === 'WARN' ? 'warn' : 'log'
    console[consoleMethod](`[${level}]`, formatted)
  }

  // Override console methods to capture all logs
  const originalConsole = {
    log: console.log,
    error: console.error,
    warn: console.warn,
    info: console.info,
    debug: console.debug
  }

  console.log = (...args: any[]) => {
    const message = format(...args)
    logStream.write(`[${new Date().toISOString()}] [INFO] ${message}\n`)
    originalConsole.log(...args)
  }

  console.error = (...args: any[]) => {
    const message = format(...args)
    logStream.write(`[${new Date().toISOString()}] [ERROR] ${message}\n`)
    originalConsole.error(...args)
  }

  console.warn = (...args: any[]) => {
    const message = format(...args)
    logStream.write(`[${new Date().toISOString()}] [WARN] ${message}\n`)
    originalConsole.warn(...args)
  }

  console.info = (...args: any[]) => {
    const message = format(...args)
    logStream.write(`[${new Date().toISOString()}] [INFO] ${message}\n`)
    originalConsole.info(...args)
  }

  console.debug = (...args: any[]) => {
    const message = format(...args)
    logStream.write(`[${new Date().toISOString()}] [DEBUG] ${message}\n`)
    originalConsole.debug(...args)
  }

  return {
    name: 'vite-logger',

    configResolved(config) {
      log('INFO', 'Vite config resolved')
      log('INFO', 'Mode: %s', config.mode)
      log('INFO', 'Base URL: %s', config.base)
      log('INFO', 'Server port: %s', config.server?.port || 'default')
    },

    configureServer(server) {
      log('INFO', 'Development server starting...')

      server.httpServer?.on('listening', () => {
        const address = server.httpServer?.address()
        if (address && typeof address !== 'string') {
          log('INFO', 'Server listening on port %d', address.port)
        }
      })

      server.httpServer?.on('error', (error) => {
        log('ERROR', 'Server error: %s', error.message)
      })

      // Log incoming requests
      server.middlewares.use((req, res, next) => {
        const start = Date.now()
        const originalEnd = res.end

        res.end = function(...args: any[]) {
          const duration = Date.now() - start
          log('INFO', '%s %s - %dms - Status: %d', req.method, req.url, duration, res.statusCode)
          return originalEnd.apply(res, args as any)
        }

        next()
      })
    },

    buildStart() {
      log('INFO', 'Build started')
    },

    buildEnd() {
      log('INFO', 'Build completed')
    },

    closeBundle() {
      log('INFO', 'Bundle closed')
      logStream.end()
    }
  }
}
