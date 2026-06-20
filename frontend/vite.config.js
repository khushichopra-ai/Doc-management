import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy /api to the Django backend so the SPA is same-origin with the API:
// HttpOnly auth cookies are sent automatically and there are no CORS concerns.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
