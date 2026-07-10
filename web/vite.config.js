import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    allowedHosts: [
      'pantry-helper.thelab.lan',
      'localhost',
      '.thelab.lan',
    ],
    proxy: {
      '/health': {
        target: 'http://backend:8000',
        changeOrigin: true
      },
      '/v1': {
        target: 'http://backend:8000',
        changeOrigin: true
      }
    }
  }
})
