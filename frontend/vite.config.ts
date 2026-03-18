import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const flaskProxyTarget = env.VITE_FLASK_PROXY_TARGET || 'http://127.0.0.1:5000'

  return {
    plugins: [react()],
    resolve: {
      dedupe: ['react', 'react-dom'],
    },
    server: {
      proxy: {
        '/api': {
          target: flaskProxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
