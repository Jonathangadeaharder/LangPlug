/// <reference types="vitest" />
import { defineConfig, configDefaults } from 'vitest/config'
import react from '@vitejs/plugin-react-swc'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react() as any],
  test: {
    // Global test configuration
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    
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
        'src/**/*.{test,spec}.{js,jsx,ts,tsx}',
        'src/**/__tests__/**',
        'src/**/__mocks__/**',
        'src/test/**',
        'src/**/*.d.ts',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
    
    // Reporter configuration
    reporters: ['default', 'html'],
    outputFile: {
      html: './test-results/index.html',
      json: './test-results/results.json',
    },
    
    // Performance optimizations
    threads: true,
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
  
  // Path resolution
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@components': resolve(__dirname, './src/components'),
      '@services': resolve(__dirname, './src/services'),
      '@hooks': resolve(__dirname, './src/hooks'),
      '@utils': resolve(__dirname, './src/utils'),
      '@store': resolve(__dirname, './src/store'),
      '@types': resolve(__dirname, './src/types'),
      '@test': resolve(__dirname, './src/test'),
    },
  },
  
  // Build configuration for test environment
  build: {
    sourcemap: true,
  },
})