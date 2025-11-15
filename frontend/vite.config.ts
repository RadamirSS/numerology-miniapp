import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/numerology-miniapp/',   // <-- добавили для GitHub Pages
  server: {
    port: 5173                    // <-- оставили как было
  }
})