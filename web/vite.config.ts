/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// In development the UI talks to the Python API (python server.py, port 8090) through this proxy.
// In production `server.py` serves web/dist itself, so the same relative /api paths work.
export default defineConfig({
  build: {
    // The server's content policy allows same-origin fonts only, so none may be inlined
    assetsInlineLimit: 0,
  },
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: { '/api': 'http://127.0.0.1:8090' },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
    css: false,
  },
})
