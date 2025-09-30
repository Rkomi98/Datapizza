# Setup workflow salari Datapizza

## Panoramica

Il sistema permette agli utenti di ricevere una valutazione del proprio stipendio tramite:
1. Compilazione form
2. Analisi automatica tramite Zapier
3. Visualizzazione risultato personalizzato via email

## Configurazione Zapier workflow

### Step 1: Trigger - Ricezione form

Configura il trigger per ricevere i dati dal form (Webhook, Typeform, Google Forms, etc.).

### Step 2: Generazione unique ID

Aggiungi uno step **Code by Zapier** o usa **Formatter by Zapier** per generare un ID univoco:

```javascript
// Esempio con Code by Zapier
output = {
  unique_id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
};
```

Oppure usa l'email dell'utente o un altro identificatore univoco già disponibile.

### Step 3: Analisi stipendio (AI/Custom Logic)

Esegui la logica che calcola lo score (1-5) basandoti su:
- Ruolo
- Località
- Stipendio
- Anni di esperienza

Output esempio:
```json
{
  "score": 3,
  "rationale": "Il tuo stipendio è in linea con la media per la tua esperienza e località."
}
```

### Step 4: Salva in Storage by Zapier

**Action:** Storage by Zapier - Set Value

**Configurazione:**
- **Key:** `dp_result_{{unique_id}}` (usa l'ID generato nello Step 2)
- **Value:** JSON completo con tutti i dati
  
  ```json
  {
    "score": {{score_step.score}},
    "rationale": "{{score_step.rationale}}",
    "inputs": {
      "ruolo": "{{trigger.ruolo}}",
      "localita": "{{trigger.localita}}",
      "stipendio": {{trigger.stipendio}}
    }
  }
  ```

**IMPORTANTE:** Il formato della chiave deve essere esattamente `dp_result_` seguito dall'unique ID.

### Step 5: Invia email

**Action:** Email by Zapier (o Gmail, etc.)

**Configurazione:**
- **To:** `{{trigger.email}}`
- **Subject:** `Il tuo risultato è pronto!`
- **Body:** Includi il link al viewer:
  
  ```
  Ciao {{trigger.nome}},
  
  Il tuo risultato è pronto!
  
  Clicca qui per visualizzarlo:
  https://tuo-dominio.com/viewer.html?tracking={{unique_id}}
  
  Il link rimarrà valido per 30 giorni.
  
  Team Datapizza
  ```

## Configurazione viewer.html

### 1. Ottieni il secret di Zapier Storage

1. Vai su https://store.zapier.com
2. Trova il tuo datastore con ID: `6b68283a-a4a5-4fbe-9fac-726d7c536a37`
3. Clicca su "View API Documentation" o "Settings"
4. Copia il **secret key**
5. Se disponibile, crea una **read-only key** per maggiore sicurezza

### 2. Aggiorna viewer.html

Apri `viewer.html` e sostituisci:

```javascript
const ZAPIER_STORE_SECRET = 'REPLACE_WITH_ZAPIER_STORE_SECRET';
```

con:

```javascript
const ZAPIER_STORE_SECRET = 'il-tuo-secret-qui';
```

### 3. Deploy

Carica i file su hosting statico:
- `viewer.html`
- `heyyou1.html`
- `heyyou2.html`
- `heyyou3.html`
- `heyyou4.html`
- `heyyou5.html`
- Cartella `images/` con le immagini

## Mappatura score → pagine

Il sistema mostra pagine diverse in base allo score:

- Score 1 → `heyyou1.html` (Sotto la media)
- Score 2 → `heyyou2.html` (In media)
- Score 3 → `heyyou3.html` (Nella media) [default]
- Score 4 → `heyyou4.html` (Sopra la media - Milano)
- Score 5 → `heyyou5.html` (Molto sopra la media)

## Flusso completo

```
Utente compila form
        ↓
    Zapier riceve dati
        ↓
    Genera unique_id
        ↓
    Calcola score (1-5)
        ↓
Salva in Storage by Zapier
   Key: dp_result_{{unique_id}}
   Value: {score, rationale, inputs}
        ↓
Invia email con link:
viewer.html?tracking={{unique_id}}
        ↓
Utente clicca link
        ↓
viewer.html carica
        ↓
Polling Zapier Storage ogni 1.5s
(max 20 tentativi = ~30s)
        ↓
Trova record → Mostra pagina corrispondente in iframe
```

## Troubleshooting

### "Missing rid" o "tracking mancante"
- Verifica che l'URL nell'email contenga `?tracking=ID`
- Controlla che l'ID sia generato correttamente nel workflow

### "Ancora nessun risultato"
- Verifica che lo step Storage by Zapier salvi correttamente
- Controlla che la chiave sia formato `dp_result_{{ID}}`
- Verifica che il secret in viewer.html sia corretto
- Controlla i log del workflow Zapier

### Score sempre 3 (default)
- Verifica che il campo `score` sia un numero (non stringa)
- Controlla il JSON salvato in Storage

### CORS errors
- Zapier Storage API supporta richieste cross-origin
- Se hai problemi, verifica network tab nel browser

## Note di sicurezza

**ATTENZIONE:** Il secret di Zapier Storage è esposto nel codice client. Considera:

1. **Opzione sicura:** Crea un proxy server-side che faccia le chiamate a Zapier Storage
2. **Opzione media:** Usa una read-only key se Zapier la supporta
3. **Opzione rapida:** Usa il secret principale ma accetta il rischio

Per maggiore sicurezza, implementa un backend che:
- Riceva richieste da viewer.html
- Verifichi rate limiting
- Chiami Zapier Storage con il secret lato server
- Ritorni solo i dati necessari al client

## Mantenimento

### Pulizia Storage
Zapier Storage potrebbe avere limiti. Considera di:
- Impostare TTL sui record (se supportato)
- Creare uno Zap schedulato che elimini record vecchi
- Monitorare l'utilizzo dello storage

### Backup
Storage by Zapier non ha backup automatici. Considera di salvare i dati anche su:
- Google Sheets
- Database esterno
- CSV via email periodiche
