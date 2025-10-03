/// <reference types="vitest" />
import { defineConfig, configDefaults } from 'vitest/config'
import react from '@vitejs/plugin-react-swc'
import { resolve } from 'path'
import { fileURLToPath, URL } from 'node:url'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [react() as any, tsconfigPaths()],
  test: {
    // Global test configuration
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',

    // Inline framer-motion to fix ESM/CommonJS issues
    server: {
      deps: {
        inline: ['framer-motion']
      }
    },

    // Timeout configuration
    testTimeout: 30000,
    hookTimeout: 10000,

    // Watch mode configuration
    watch: false, // Disable by default for CI

    // Test organization
    include: [
      'src/**/*.{test,spec}.{js,jsx,ts,tsx}',
      'src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    ],
    exclude: [
      ...configDefaults.exclude,
      'src/test/auth-flow.test.ts', // Has its own runner
      '**/node_modules/**',
      '**/dist/**',
      '**/cypress/**',
      '**/.{idea,git,cache,output,temp}/**',
    ],

    // Coverage configuration
    coverage: {
      enabled: false,
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      include: [
        'src/**/*.{js,jsx,ts,tsx}',
      ],
      exclude: [
        // Test files
        'src/**/*.{test,spec}.{js,jsx,ts,tsx}',
        'src/**/__tests__/**',
        'src/**/__mocks__/**',
        'src/test/**',
        // Auto-generated files
        '**/*.gen.ts',
        '**/*.gen.js',
        '**/generated/**',
        'src/client/core/**',
        // Type definitions and entry points
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      thresholds: {
        statements: 60,
        branches: 60,
        functions: 60,
        lines: 60,
      },
    },

    // Reporter configuration
    reporters: ['default', 'html'],
    outputFile: {
      html: './test-results/index.html',
      json: './test-results/results.json',
    },

    // Performance optimizations
    threads: false, // Disabled to avoid bus error in WSL
    maxThreads: 4,
    minThreads: 1,

    // Retry configuration
    retry: 2,

    // Mock configuration
    mockReset: true,
    clearMocks: true,
    restoreMocks: true,

    // Benchmark configuration (optional)
    benchmark: {
      include: ['**/*.bench.{js,ts}'],
    },
  },

  // Path resolution handled by vite-tsconfig-paths plugin
  resolve: {
    alias: {
      // Mock framer-motion in tests
      'framer-motion': fileURLToPath(new URL('./src/test/mocks/framer-motion.ts', import.meta.url)),
    },
  },

  // Build configuration for test environment
  build: {
    sourcemap: true,
  },
})
