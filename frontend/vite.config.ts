import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // During development, send /api/... calls to the FastAPI backend.
    // The browser only ever talks to localhost:5173, so no CORS problems.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
