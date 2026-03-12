import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND_PORT = process.env.BACKEND_PORT || 18080
const DASHBOARD_PORT = process.env.DASHBOARD_PORT || 18300

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: Number(DASHBOARD_PORT),
    strictPort: true,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${BACKEND_PORT}`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
