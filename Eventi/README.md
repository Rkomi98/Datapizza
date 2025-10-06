# Datapizza Eventi - Sistema di analisi automatica

Sistema automatizzato per l'analisi dei dati degli eventi Datapizza, con generazione automatica di KPI e report HTML dinamici.

## Struttura del progetto

```
Eventi/
├── index.html                  # Dashboard principale (generata automaticamente)
├── analyze_event.py            # Script per analizzare un singolo evento
├── analyze_all_events.py       # Script per analizzare tutti gli eventi
├── generate_dashboard.py       # Script per generare la dashboard HTML
├── extract_kpi_from_html.py    # Script per estrarre KPI da HTML esistenti
├── events_index.json           # Indice generato automaticamente
├── .env                        # Configurazione API keys (non in git)
├── .env.example                # Template per configurazione
├── requirements.txt            # Dipendenze Python
├── pyproject.toml             # Configurazione progetto
├── README.md                   # Questa documentazione
└── AperipizzaAI0925/          # Esempio di cartella evento
    ├── responses.csv           # Dati profilazione partecipanti
    ├── responses(1).csv        # Dati feedback evento
    ├── index.html              # Report HTML specifico
    └── analysis.json           # Dati analizzati (generato automaticamente)
```

## Setup iniziale

### 1. Installazione dipendenze

Con pip:
```bash
pip install -r requirements.txt
```

Con uv (consigliato):
```bash
uv pip install -r requirements.txt
```

### 2. Configurazione API OpenAI

Copia il file `.env.example` in `.env` e inserisci la tua API key:

```bash
cp .env.example .env
```

Modifica `.env`:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Nota:** l'API key è opzionale. Senza API key, lo script eseguirà l'analisi standard ma non l'analisi qualitativa dei feedback testuali con GPT.

## Utilizzo

### Analizzare un singolo evento

```bash
python analyze_event.py <nome_cartella_evento>
```

Esempio:
```bash
python analyze_event.py AperipizzaAI0925
```

Questo comando:
- Analizza i file CSV nella cartella evento
- Calcola tutti i KPI automaticamente
- Usa GPT per analizzare i feedback testuali (se configurato)
- Genera un file `analysis.json` con tutti i dati

### Analizzare tutti gli eventi

```bash
python analyze_all_events.py
```

Questo comando:
- Cerca automaticamente tutte le cartelle contenenti CSV
- Analizza ogni evento trovato
- Genera l'indice `events_index.json` per la dashboard
- Crea/aggiorna i file `analysis.json` per ogni evento
- Genera automaticamente `index.html` con i dati embedded

**Nota:** la dashboard viene generata con i dati embedded per evitare problemi CORS quando aperta direttamente dal filesystem.

### Estrarre KPI da HTML esistente (opzionale)

Se hai un evento con un report HTML già creato ma senza i file CSV originali:

```bash
python extract_kpi_from_html.py <cartella_evento>/index.html
```

Esempio:
```bash
python extract_kpi_from_html.py AperipizzaAI0925/index.html
```

Questo comando estrae i KPI visibili nell'HTML e li salva in un file JSON.

### Rigenerare la dashboard manualmente (opzionale)

Se hai modificato i dati e vuoi rigenerare solo la dashboard senza rieseguire l'analisi:

```bash
python generate_dashboard.py
```

### Visualizzare la dashboard

Dopo aver eseguito l'analisi, apri `index.html` in un browser:

```bash
# Su Linux
xdg-open index.html

# Su macOS
open index.html

# Su Windows
start index.html
```

La dashboard mostrerà:
- Statistiche aggregate di tutti gli eventi
- Card per ogni evento con KPI principali
- Link ai report dettagliati di ciascun evento

## Struttura dei file CSV

### File di profilazione (responses.csv o simile)

Deve contenere almeno alcuni di questi campi (i nomi possono variare):
- Email partecipante
- Anno di nascita
- Status (studente/lavoratore)
- Job title / Ruolo
- Anni di esperienza
- Azienda
- Motivo partecipazione
- Interesse per eventi futuri
- Topic di interesse

### File di feedback (responses(1).csv o simile)

Deve contenere almeno alcuni di questi campi:
- Email partecipante
- Valutazione complessiva (stelle)
- Valutazione networking (stelle)
- Suggerimenti per migliorare (testo libero)
- Interesse a partecipare in futuro

**Importante:** lo script è progettato per essere flessibile e funziona anche se alcuni campi sono mancanti o hanno nomi diversi. Usa il riconoscimento automatico dei campi basato su keyword.

## Aggiungere un nuovo evento

1. Crea una nuova cartella con il nome dell'evento (es: `AperipizzaAI1125`)

2. Aggiungi i file CSV con i dati:
   - Un file con i dati di profilazione
   - Un file con i feedback (opzionale)

3. Esegui l'analisi:
   ```bash
   python analyze_all_events.py
   ```

4. (Opzionale) Crea un file `index.html` personalizzato nella cartella evento usando come template quello di `AperipizzaAI0925`

5. La dashboard principale si aggiornerà automaticamente

## KPI calcolati automaticamente

### Dati di profilazione
- Numero totale di risposte
- Distribuzione per età
- Percentuale studenti vs professionisti
- Livelli di esperienza
- Categorizzazione professionale (Data & AI, Management, Software Engineering, Marketing)
- Numero di aziende rappresentate
- Motivazioni di partecipazione
- Interesse per eventi futuri
- Topic di interesse

### Dati di feedback
- Numero di feedback ricevuti
- Valutazione media complessiva
- Distribuzione delle valutazioni
- Valutazione networking
- Analisi qualitativa dei suggerimenti (con GPT)
- Tasso di retention (interesse futuro)

### KPI aggregati
- Tasso di feedback (feedback / profilazioni)
- Percentuale di soddisfazione (rating 5 stelle)
- Tasso di partecipazione futura
- Diversità aziendale

## Personalizzazione

### Modificare le categorie professionali

Modifica il metodo `_categorize_jobs` in `analyze_event.py`:

```python
categories = {
    'Nuova Categoria': {
        'keywords': ['keyword1', 'keyword2'],
        'count': 0,
        'jobs': []
    }
}
```

### Modificare il prompt GPT

Modifica il metodo `analyze_suggestions_with_gpt` in `analyze_event.py` per cambiare come GPT analizza i feedback.

### Personalizzare la dashboard

Modifica `index.html` per cambiare:
- Stili e colori (sezione `<style>`)
- Layout delle statistiche
- Informazioni visualizzate nelle card degli eventi

## Troubleshooting

### Errore: file CSV non trovato

Verifica che i file CSV siano nella cartella corretta e abbiano estensione `.csv`.

### Errore: encoding del CSV

Lo script prova automaticamente diversi encoding (UTF-8, Latin-1, CP1252). Se continua a dare errore, salva il CSV come UTF-8.

### Analisi GPT non funziona

Verifica che:
- Il file `.env` esista e contenga una API key valida
- Hai crediti disponibili sul tuo account OpenAI
- La tua connessione internet funzioni
- Stai usando OpenAI API versione 1.0+ (installata con le dipendenze)

### Dashboard non mostra gli eventi

Verifica che:
- Hai eseguito `python analyze_all_events.py`
- Il file `index.html` sia stato generato (24KB+)
- I dati siano embedded nell'HTML (non più dipendente da `events_index.json`)

Se vedi l'errore "Impossibile caricare i dati", rigenera la dashboard:
```bash
python generate_dashboard.py
```

## Sviluppi futuri

Possibili miglioramenti da implementare:
- Export dei dati in formato Excel/PDF
- Grafici interattivi con Chart.js o Plotly
- Confronto tra eventi diversi
- Sistema di notifiche per anomalie nei dati
- Dashboard real-time con aggiornamento automatico

## Licenza

Proprietà di Datapizza - Uso interno

