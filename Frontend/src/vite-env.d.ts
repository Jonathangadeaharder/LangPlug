/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Global test utilities available in all test files
declare global {
  const act: (callback: () => void | Promise<void>) => void | Promise<void>
  const actAsync: (fn: () => Promise<any>) => Promise<void>
  const mockTheme: any
  const withTheme: (component: React.ReactElement) => React.ReactElement

  // Node.js global object with index signature for tests
  var global: typeof globalThis & {
    [key: string]: any
    mockTheme: any
    withTheme: (component: React.ReactElement) => React.ReactElement
    act: (callback: () => void | Promise<void>) => void | Promise<void>
    actAsync: (fn: () => Promise<any>) => Promise<void>
  }

  // Allow index signature access to globalThis for tests
  interface globalThis {
    [key: string]: any
  }
}
