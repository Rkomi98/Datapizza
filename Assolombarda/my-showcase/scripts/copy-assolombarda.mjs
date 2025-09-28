import { cpSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const distDir = join(process.cwd(), 'dist')
const repoTargetDir = join(process.cwd(), '..', 'Assolombarda')

try {
  rmSync(repoTargetDir, { recursive: true, force: true })
  cpSync(distDir, repoTargetDir, { recursive: true })
  console.log('✓ Copiati i file di build in ../Assolombarda/')
} catch (error) {
  console.error('Errore durante la pubblicazione locale della pagina Assolombarda:', error)
  process.exit(1)
}
