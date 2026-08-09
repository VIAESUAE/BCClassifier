import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// GitHub project Pages need base like "/BusinessCardClassifier/"
const base = process.env.VITE_BASE || '/'

export default defineConfig({
  base,
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/ingest': 'http://127.0.0.1:8000',
      '/cards': 'http://127.0.0.1:8000',
      '/rag': 'http://127.0.0.1:8000',
    },
  },
})
