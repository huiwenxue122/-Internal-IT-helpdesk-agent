import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy /api/* to the FastAPI backend in dev so no CORS headers are needed
    // and the frontend uses the same URL scheme as production.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
