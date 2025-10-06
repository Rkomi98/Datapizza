# Changelog

## [1.1.0] - 2025-10-06

### Fixed
- **CORS issue risolto:** La dashboard ora funziona quando aperta direttamente dal filesystem
  - Creato `generate_dashboard.py` che genera HTML con dati embedded
  - Non più dipendente da `fetch()` di `events_index.json`
  
- **OpenAI API aggiornata:** Compatibilità con OpenAI API 1.0+
  - Aggiornata sintassi da `openai.ChatCompletion.create()` a `client.chat.completions.create()`
  - Inizializzazione client con `OpenAI(api_key=...)`

### Added
- Script `generate_dashboard.py` per generare la dashboard standalone
- Integrazione automatica in `analyze_all_events.py`
- Documentazione aggiornata in tutti i file README

### Changed
- `index.html` ora generato automaticamente (non più statico)
- Dimensione file `index.html`: da 16KB a 24KB (con dati embedded)
- Workflow semplificato: un solo comando per tutto (`analyze_all_events.py`)

## [1.0.0] - 2025-10-06

### Added
- Sistema completo di analisi eventi
- Script `analyze_event.py` per singolo evento
- Script `analyze_all_events.py` per batch
- Script `extract_kpi_from_html.py` per HTML legacy
- Dashboard HTML interattiva
- Integrazione GPT-4 per analisi qualitativa
- Calcolo automatico 20+ KPI
- Documentazione completa (README, QUICK_START, ARCHITECTURE, SUMMARY)
- Configurazione con `.env` per API keys
- File di dipendenze (`requirements.txt`, `pyproject.toml`)

### Features
- Riconoscimento automatico campi CSV
- Supporto multipli encoding
- Categorizzazione professionale automatica
- Analisi età, esperienza, aziende
- Valutazioni e feedback rate
- Design moderno e responsive

