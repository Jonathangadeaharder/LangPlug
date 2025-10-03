import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'
import { viteLogger } from './vite-plugin-logger'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      viteLogger({
        logFile: 'frontend.log',
        includeTimestamp: true
      }),
      react()
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@/components': path.resolve(__dirname, './src/components'),
        '@/pages': path.resolve(__dirname, './src/pages'),
        '@/hooks': path.resolve(__dirname, './src/hooks'),
        '@/services': path.resolve(__dirname, './src/services'),
        '@/store': path.resolve(__dirname, './src/store'),
        '@/types': path.resolve(__dirname, './src/types'),
        '@/styles': path.resolve(__dirname, './src/styles'),
        '@/client': path.resolve(__dirname, './src/client')
      }
    },
    server: {
      port: 3000,
      host: true, // Allow access from external connections (WSL, localhost, network)
      proxy: {
        '/api': {
          target: env.VITE_BACKEND_URL || 'http://localhost:8000',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: true
    },
    define: {
      __APP_ENV__: JSON.stringify(env.VITE_APP_ENV),
    }
  }
})
