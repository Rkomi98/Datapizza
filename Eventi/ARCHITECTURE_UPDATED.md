# Architettura sistema eventi (Aggiornata)

## Panoramica

Il sistema è ora completamente automatizzato e genera pagine HTML dinamiche per ogni livello.

## Struttura file

```
Eventi/
├── index.html                      # Dashboard principale (GENERATO)
├── events_index.json               # Indice globale (GENERATO)
│
├── AperipizzaAI0925/
│   ├── responses.csv               # Input: dati profilazione
│   ├── responses(1).csv            # Input: dati feedback
│   ├── analysis.json               # Output: dati analizzati (GENERATO)
│   └── index.html                  # Output: pagina evento (GENERATO)
│
└── [scripts Python]
```

## Flusso di lavoro

### 1. Input utente
```
Cartella evento con CSV
├── responses.csv      (profilazione)
└── responses(1).csv   (feedback)
```

### 2. Esecuzione analisi
```bash
python analyze_all_events.py
```

### 3. Processing
```
analyze_event.py
    ↓
[Legge CSV] → [Analizza dati] → [Chiama GPT] 
    ↓
[Genera analysis.json]
    ↓
[Chiama generate_event_page.py]
    ↓
[Genera <evento>/index.html con dati embedded]
```

### 4. Aggregazione
```
analyze_all_events.py
    ↓
[Raccoglie tutti analysis.json]
    ↓
[Genera events_index.json]
    ↓
[Chiama generate_dashboard.py]
    ↓
[Genera index.html principale con dati embedded]
```

### 5. Output finale
```
✅ index.html                    # Dashboard principale
✅ events_index.json             # Indice dati
✅ AperipizzaAI0925/
   ✅ analysis.json              # Dati analizzati
   ✅ index.html                 # Pagina evento dinamica
```

## Componenti

### Script Python

1. **`analyze_event.py`**
   - Input: cartella con CSV
   - Output: `analysis.json` + `<evento>/index.html`
   - Funzioni: parsing CSV, calcolo KPI, analisi GPT
   - Chiama automaticamente: `generate_event_page.py`

2. **`analyze_all_events.py`**
   - Input: cartelle eventi
   - Output: `events_index.json` + `index.html` principale
   - Funzioni: coordinamento batch
   - Chiama automaticamente: `generate_dashboard.py`

3. **`generate_event_page.py`**
   - Input: `analysis.json`
   - Output: `<evento>/index.html`
   - Funzioni: genera HTML con dati embedded

4. **`generate_dashboard.py`**
   - Input: `events_index.json`
   - Output: `index.html` principale
   - Funzioni: genera dashboard con dati embedded

5. **`extract_kpi_from_html.py`**
   - Input: HTML legacy
   - Output: `kpi_extracted.json`
   - Funzioni: estrae dati da HTML esistenti

### File HTML

#### Dashboard principale (`index.html`)
- **Tipo:** Generato automaticamente
- **Dati:** Embedded da `events_index.json`
- **Contenuto:**
  - Statistiche aggregate (totale partecipanti, aziende, etc.)
  - Card per ogni evento
  - Link a pagine evento

#### Pagina evento (`<evento>/index.html`)
- **Tipo:** Generato automaticamente
- **Dati:** Embedded da `analysis.json`
- **Contenuto:**
  - KPI principali
  - Profilazione dettagliata
  - Feedback e valutazioni
  - Analisi GPT
  - Lista aziende

## Perché dati embedded?

**Problema CORS:**
Quando apri un file HTML direttamente dal filesystem (`file://`), i browser moderni bloccano richieste `fetch()` per motivi di sicurezza.

**Soluzione:**
Embeddiamo i dati JSON direttamente nell'HTML come variabile JavaScript:
```javascript
const eventData = { /* dati JSON */ };
```

**Vantaggio:**
- ✅ Funziona ovunque (filesystem, web server, file condivisi)
- ✅ Nessuna configurazione server necessaria
- ✅ Una singola pagina HTML autocontenuta

**Svantaggio:**
- ❌ File HTML più grandi (~25KB invece di ~5KB)
- ❌ Dati duplicati (in JSON e HTML)

## Workflow tipico utente

```bash
# 1. Creare cartella evento con CSV
mkdir NuovoEvento
cp dati_profilazione.csv NuovoEvento/responses.csv
cp dati_feedback.csv NuovoEvento/responses2.csv

# 2. Analizzare tutto
python analyze_all_events.py
# → Genera automaticamente tutti i file necessari

# 3. Visualizzare
xdg-open index.html                  # Dashboard generale
xdg-open NuovoEvento/index.html      # Report specifico
```

## Aggiornamenti futuri

Quando aggiungi un nuovo evento:

```bash
# 1. Aggiungi cartella con CSV
mkdir EventoNuovo2025
# ... aggiungi CSV ...

# 2. Ri-analizza tutto
python analyze_all_events.py

# 3. Done! Tutte le pagine si aggiornano automaticamente
```

## Performance

- **Analisi singolo evento:** ~2-5 secondi (con GPT)
- **Analisi 10 eventi:** ~20-50 secondi
- **Generazione HTML:** < 1 secondo per file
- **Dimensione file:**
  - `analysis.json`: ~50-100KB
  - `<evento>/index.html`: ~25-30KB
  - `index.html` principale: ~25KB + (5KB * numero eventi)

## Sicurezza

- ✅ API keys in `.env` (non committate)
- ✅ Dati sensibili gestiti secondo GDPR
- ✅ HTML sanitizzato (no injection)
- ✅ Nessun server-side code (solo file statici)

## Troubleshooting

**Pagina evento non aggiornata?**
```bash
python generate_event_page.py <evento>
```

**Dashboard non aggiornata?**
```bash
python generate_dashboard.py
```

**Dati mancanti?**
```bash
python analyze_all_events.py  # Rigenera tutto
```

