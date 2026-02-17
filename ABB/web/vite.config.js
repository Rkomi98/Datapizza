import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Relative base so static assets also resolve on GitHub Pages project URLs.
export default defineConfig({
  base: './',
  plugins: [react()],
})
