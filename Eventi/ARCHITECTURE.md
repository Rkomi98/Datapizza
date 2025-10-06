# Architettura del sistema

## Panoramica

Il sistema è composto da tre componenti principali:
1. **Analisi automatica** - Script Python per analizzare CSV e generare KPI
2. **Dashboard web** - Interfaccia HTML/JavaScript per visualizzare i dati
3. **Report evento** - Pagine HTML statiche per ogni evento

## Flusso di lavoro

```
┌─────────────────────────────────────────────────────────────┐
│                     NUOVO EVENTO                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Crea cartella con CSV        │
        │  - responses.csv              │
        │  - responses(1).csv           │
        └───────────┬───────────────────┘
                    │
                    ▼
        ┌───────────────────────────────┐
        │  python analyze_all_events.py │
        └───────────┬───────────────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    ┌─────┐   ┌─────────┐   ┌─────┐
    │ CSV │──▶│ Analyzer│──▶│ GPT │ (opzionale)
    └─────┘   └────┬────┘   └─────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  analysis.json       │
        │  (per ogni evento)   │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  events_index.json   │
        │  (indice globale)    │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  index.html          │
        │  (dashboard)         │
        └──────────────────────┘
```

## Componenti Python

### 1. `analyze_event.py`

**Responsabilità:** analisi di un singolo evento

**Classi principali:**
- `EventAnalyzer` - Coordina l'analisi completa

**Metodi chiave:**
- `find_csv_files()` - Identifica file profilazione/feedback
- `analyze_profiling_data()` - Estrae KPI dai dati profilazione
- `analyze_feedback_data()` - Estrae KPI dai feedback
- `analyze_suggestions_with_gpt()` - Analisi qualitativa con GPT
- `_calculate_kpis()` - Calcola KPI aggregati

**Output:**
- `<evento>/analysis.json` - Dati completi analizzati

### 2. `analyze_all_events.py`

**Responsabilità:** coordinamento analisi multipli eventi

**Funzioni principali:**
- `find_event_folders()` - Cerca cartelle con CSV
- `analyze_all_events()` - Esegue analisi batch

**Output:**
- `events_index.json` - Indice globale per dashboard

### 3. `extract_kpi_from_html.py`

**Responsabilità:** estrazione KPI da HTML esistenti

**Classi principali:**
- `HTMLKPIExtractor` - Parse HTML e estrae dati

**Metodi chiave:**
- `extract_metric_cards()` - Estrae metriche numeriche
- `extract_companies()` - Estrae lista aziende
- `extract_insights()` - Estrae insight testuali

**Use case:** eventi legacy con solo report HTML

## Componente web

### 1. `index.html` (Dashboard)

**Tecnologie:**
- HTML5
- CSS3 (Grid, Flexbox, Animations)
- Vanilla JavaScript (ES6+)

**Funzionalità:**
- Carica `events_index.json` via fetch
- Calcola statistiche aggregate
- Renderizza card dinamiche per ogni evento
- Navigazione verso report specifici

**Struttura dati attesa:**
```javascript
{
  "events": [
    {
      "event_name": "string",
      "kpis": {...},
      "profiling_data": {...},
      "feedback_data": {...}
    }
  ]
}
```

### 2. `<evento>/index.html` (Report)

**Tipo:** statico o dinamico

**Opzioni:**
- **Statico:** HTML manuale con dati hard-coded (come AperipizzaAI0925)
- **Dinamico:** HTML che carica `analysis.json` e renderizza dati

## Struttura dati

### `analysis.json`

```json
{
  "event_name": "string",
  "event_folder": "string",
  "analysis_date": "ISO-8601",
  "profiling_data": {
    "total_responses": int,
    "age_distribution": {...},
    "students_vs_professionals": {...},
    "experience_levels": {...},
    "job_categories": {...},
    "companies": {
      "total_unique": int,
      "list": ["string"]
    },
    "motivations": {...},
    "future_participation": {...},
    "topics_of_interest": ["string"]
  },
  "feedback_data": {
    "total_responses": int,
    "overall_rating": {
      "average": float,
      "distribution": {...}
    },
    "networking_rating": {...},
    "suggestions": ["string"],
    "future_interest": {...},
    "gpt_analysis": {
      "summary": "string",
      "categories": {...},
      "key_improvements": ["string"]
    }
  },
  "kpis": {
    "profiling_responses": int,
    "feedback_responses": int,
    "feedback_rate": float,
    "overall_satisfaction": float,
    "satisfaction_5_stars_percentage": float,
    "future_participation_rate": float,
    "unique_companies": int
  }
}
```

## Estensibilità

### Aggiungere nuovi KPI

1. Modifica `_calculate_kpis()` in `analyze_event.py`
2. Aggiungi calcolo del nuovo KPI
3. Il dashboard si aggiornerà automaticamente

### Aggiungere nuove categorie professionali

1. Modifica `_categorize_jobs()` in `analyze_event.py`
2. Aggiungi nuova categoria con keywords
3. Rianalizza eventi con `analyze_all_events.py`

### Personalizzare analisi GPT

1. Modifica il prompt in `analyze_suggestions_with_gpt()`
2. Cambia modello o temperatura
3. Modifica struttura output JSON se necessario

### Aggiungere grafici

1. Includi libreria charting (Chart.js, Plotly)
2. Modifica `index.html` per renderizzare grafici
3. Usa dati da `events_index.json`

## Sicurezza

- **API Keys:** mai committare `.env` (è in `.gitignore`)
- **Dati sensibili:** i CSV potrebbero contenere email - gestire secondo GDPR
- **HTML output:** sanitizzare input utente se si genera HTML dinamico

## Performance

- **Analisi batch:** ~1-2 secondi per evento (senza GPT)
- **Analisi GPT:** +3-5 secondi per evento
- **Dashboard:** carica istantaneamente (< 100ms per < 50 eventi)
- **Dimensioni file:** ~50-100KB per `analysis.json`

## Limitazioni note

- **Riconoscimento campi CSV:** basato su keywords, potrebbe fallire con nomi molto diversi
- **Encoding CSV:** supporta UTF-8, Latin-1, CP1252 - altri encoding potrebbero fallire
- **GPT rate limits:** rispetta limiti API OpenAI
- **Browser compatibility:** richiede ES6+ (Chrome 60+, Firefox 55+, Safari 11+)

## Roadmap futura

1. **Export PDF/Excel** dei report
2. **Grafici interattivi** con Chart.js
3. **Comparazione** tra eventi
4. **Dashboard real-time** con auto-refresh
5. **Template HTML dinamici** per report evento
6. **CLI interattivo** con menu
7. **Web server** locale per sviluppo
8. **Test suite** automatizzati

