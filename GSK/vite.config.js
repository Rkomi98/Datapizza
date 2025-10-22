import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const repoBase = '/GSK/'

export default defineConfig(({ command }) => ({
  base: command === 'serve' ? '/' : repoBase,
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
}))
