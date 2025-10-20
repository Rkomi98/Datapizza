import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const repoBase = '/Datapizza/'

export default defineConfig(({ command }) => ({
  base: command === 'serve' ? '/' : repoBase,
  plugins: [react()],
}))
