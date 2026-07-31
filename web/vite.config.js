import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    css: true,
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon-72.png', 'icon-96.png', 'icon-144.png', 'icon-192.png', 'icon-512.png'],
      manifest: {
        name: 'Pantry Helper',
        short_name: 'Pantry',
        description: 'Smart pantry inventory management with AI vision',
        theme_color: '#2563eb',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        scope: '/',
        start_url: '/',
        categories: ['utilities', 'food', 'home'],
        icons: [
          { src: '/icon-72.png', sizes: '72x72', type: 'image/png' },
          { src: '/icon-96.png', sizes: '96x96', type: 'image/png' },
          { src: '/icon-144.png', sizes: '144x144', type: 'image/png' },
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/.*\/v1\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24
              },
              networkTimeoutSeconds: 10
            }
          },
          {
            urlPattern: /^https?:\/\/.*\/health.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'health-cache',
              expiration: {
                maxEntries: 5,
                maxAgeSeconds: 60 * 5
              }
            }
          }
        ]
      }
    })
  ],
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
