# Configurazione GitHub Secrets

Per far funzionare l'applicazione su GitHub Pages, devi configurare le seguenti secrets nel tuo repository:

## Come aggiungere le Secrets

1. Vai su **Settings** del tuo repository GitHub
2. Clicca su **Secrets and variables** > **Actions**
3. Clicca su **New repository secret**
4. Aggiungi le seguenti secrets una per una:

## Secrets necessarie

Devi configurare le seguenti secrets con i valori del tuo progetto Firebase:

| Nome Secret | Descrizione |
|-------------|-------------|
| `FIREBASE_API_KEY` | La tua API Key di Firebase |
| `FIREBASE_AUTH_DOMAIN` | Il dominio di autenticazione (es: `tuoprogetto.firebaseapp.com`) |
| `FIREBASE_DATABASE_URL` | L'URL del Realtime Database |
| `FIREBASE_PROJECT_ID` | L'ID del tuo progetto Firebase |
| `FIREBASE_STORAGE_BUCKET` | Il bucket di storage |
| `FIREBASE_MESSAGING_SENDER_ID` | L'ID del sender per messaggi |
| `FIREBASE_APP_ID` | L'ID dell'app Firebase |
| `FIREBASE_MEASUREMENT_ID` | L'ID per Google Analytics (opzionale) |

**Dove trovare questi valori:**
- Nel file `firebase-config-local.js` (localmente)
- Nella console Firebase del tuo progetto: Settings > General > Your apps

## Come funziona

- **Locale**: L'app usa `firebase-config-local.js` per il testing locale
- **Produzione**: GitHub Actions sostituisce automaticamente i placeholder in `app.js` con le tue secrets

## Testing locale

Per testare localmente, assicurati che il file `firebase-config-local.js` esista (è già configurato).

## Deploy

Ogni volta che fai push su `main`, GitHub Actions:
1. Sostituisce i placeholder con le secrets
2. Fa il deploy automatico su GitHub Pages

**Nota**: Dopo aver configurato le secrets, fai un nuovo commit per triggering il deploy. 