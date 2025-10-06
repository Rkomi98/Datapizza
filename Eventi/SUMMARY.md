# Riepilogo sistema eventi Datapizza

## Sistema completato ✅

Ho creato un sistema completo e automatizzato per la gestione e analisi degli eventi Datapizza.

## File creati

### Script Python

1. **`analyze_event.py`** (20KB)
   - Analizza un singolo evento
   - Estrae KPI da CSV di profilazione e feedback
   - Integra GPT-4 per analisi qualitativa dei suggerimenti
   - Gestisce automaticamente encoding e formati diversi dei CSV

2. **`analyze_all_events.py`** (3KB)
   - Analizza tutti gli eventi in batch
   - Genera l'indice globale per la dashboard
   - Genera automaticamente la dashboard HTML
   - Mostra progress e gestisce errori

3. **`generate_dashboard.py`** (8KB)
   - Genera `index.html` con dati embedded
   - Risolve problemi CORS del filesystem
   - Può essere eseguito standalone per rigenerare solo la dashboard

4. **`extract_kpi_from_html.py`** (5KB)
   - Estrae KPI da report HTML esistenti
   - Utile per eventi legacy senza CSV originali

### Web Dashboard

5. **`index.html`** (24KB - generato automaticamente)
   - Dashboard principale interattiva
   - Dati embedded direttamente nell'HTML (no CORS issues)
   - Mostra statistiche aggregate di tutti gli eventi
   - Card dinamiche per ogni evento con KPI principali
   - Design responsive e moderno

### Configurazione

6. **`requirements.txt`** - Dipendenze Python
7. **`pyproject.toml`** - Configurazione progetto (con index Datapizza)
8. **`.env.example`** - Template per API key OpenAI
9. **`.gitignore`** - Esclude file sensibili e generati

### Documentazione

10. **`README.md`** (7KB) - Documentazione completa
11. **`QUICK_START.md`** (2KB) - Setup rapido 5 minuti
12. **`ARCHITECTURE.md`** (8KB) - Architettura tecnica del sistema
13. **`SUMMARY.md`** - Questo documento

### File generati automaticamente

- **`events_index.json`** - Indice globale eventi
- **`AperipizzaAI0925/analysis.json`** - Dati analizzati primo evento

## Caratteristiche principali

### 1. Analisi automatica CSV

- Riconoscimento automatico dei campi (nomi colonne flessibili)
- Supporto multipli encoding (UTF-8, Latin-1, CP1252)
- Gestione strutture CSV variabili
- Calcolo automatico di 20+ KPI

### 2. Integrazione GPT

- Analisi qualitativa dei feedback testuali
- Categorizzazione automatica suggerimenti
- Identificazione punti di miglioramento ricorrenti
- Opzionale (funziona anche senza API key)

### 3. KPI calcolati

**Profilazione:**
- Numero partecipanti
- Distribuzione età
- Studenti vs professionisti
- Livelli esperienza
- Categorie professionali (Data & AI, Management, Software, Marketing)
- Numero aziende uniche
- Motivazioni partecipazione
- Topic di interesse

**Feedback:**
- Valutazione media complessiva
- Valutazione networking
- Distribuzione ratings
- Tasso di retention (interesse eventi futuri)
- Analisi qualitativa suggerimenti

**Aggregati:**
- Feedback rate
- Percentuale soddisfazione 5 stelle
- Tasso partecipazione futura
- Diversità aziendale

### 4. Dashboard dinamica

- Statistiche aggregate multi-evento
- Card interattive per ogni evento
- Design moderno e responsive
- Aggiornamento automatico

### 5. Flessibilità

- Struttura CSV adattabile
- Campi opzionali gestiti automaticamente
- Nomi colonne flessibili (riconoscimento keyword)
- Categorizzazione personalizzabile

## Come usare

### Setup iniziale (2 minuti)

```bash
# Installa dipendenze
pip install -r requirements.txt

# (Opzionale) Configura OpenAI
cp .env.example .env
# Modifica .env con la tua API key
```

### Workflow evento

```bash
# 1. Aggiungi nuova cartella evento con CSV
mkdir NuovoEvento
cp dati.csv NuovoEvento/

# 2. Analizza tutti gli eventi
python analyze_all_events.py

# 3. Apri dashboard
xdg-open index.html
```

### Output esempio

```
======================================================================
🎯 ANALISI COMPLETA EVENTI DATAPIZZA
======================================================================

📁 Trovate 1 cartelle evento:
   - AperipizzaAI0925

[1/1] Analisi evento: AperipizzaAI0925
----------------------------------------------------------------------
✓ Trovato file profilazione: responses(1).csv
  → 73 risposte analizzate
✓ Trovato file feedback: responses.csv
  → 30 feedback analizzati
🤖 Analisi qualitativa con GPT in corso...
  → Analisi completata

✅ Analisi completata!
💾 Dati salvati in: AperipizzaAI0925/analysis.json

======================================================================
✅ ANALISI COMPLETATA!
📊 1 eventi analizzati con successo
💾 Indice salvato in: events_index.json

🌐 Apri index.html nel browser per visualizzare la dashboard
======================================================================
```

## Estensibilità

Il sistema è progettato per essere facilmente estendibile:

- **Nuovi KPI:** modifica `_calculate_kpis()` in `analyze_event.py`
- **Nuove categorie:** modifica `_categorize_jobs()` 
- **Personalizza GPT:** modifica prompt in `analyze_suggestions_with_gpt()`
- **Grafici:** aggiungi Chart.js/Plotly a `index.html`
- **Export:** aggiungi funzioni per PDF/Excel

## Tecnologie usate

- **Backend:** Python 3.8+
- **Analisi dati:** pandas-like manual parsing (no dipendenze pesanti)
- **AI:** OpenAI GPT-4o-mini
- **Frontend:** HTML5, CSS3, Vanilla JavaScript ES6+
- **Design:** Gradient UI, responsive, animations

## Note tecniche

### Pro del sistema

✅ Zero dipendenze pesanti (no pandas, no numpy)  
✅ Veloce (~1-2 sec per evento senza GPT)  
✅ Flessibile con formati CSV variabili  
✅ Gestione automatica errori e encoding  
✅ Design moderno e professionale  
✅ Documentazione completa  

### Limitazioni

⚠️ Riconoscimento campi basato su keyword (nomi colonne molto diversi potrebbero non funzionare)  
⚠️ GPT ha costi e rate limits API  
⚠️ Dashboard richiede browser moderno (ES6+)  

### Sicurezza

🔒 API keys mai committate (`.env` in `.gitignore`)  
🔒 Dati sensibili nei CSV - gestire secondo GDPR  
🔒 Output HTML sanitizzato  

## Problemi risolti

### Issue CORS
**Problema:** La dashboard non caricava i dati quando aperta direttamente dal filesystem (`file://`)

**Soluzione:** Creato `generate_dashboard.py` che genera `index.html` con dati embedded, eliminando la necessità di `fetch()` e quindi i problemi CORS.

### Issue OpenAI API
**Problema:** Errore con OpenAI API 1.0+ (sintassi vecchia)

**Soluzione:** Aggiornato il codice per usare la nuova sintassi `OpenAI(api_key)` e `client.chat.completions.create()`.

## Prossimi passi

1. **Testa con un nuovo evento:**
   - Crea cartella con nuovi CSV
   - Esegui `python analyze_all_events.py`
   - Verifica risultati in dashboard

2. **Configura OpenAI (opzionale):**
   - Aggiungi API key in `.env`
   - Ri-esegui analisi per ottenere insights GPT

3. **Personalizza:**
   - Modifica categorie professionali se necessario
   - Adatta prompt GPT al tuo caso d'uso
   - Personalizza stili dashboard

## File CSV attesi

### Profilazione (es: responses(1).csv)

Campi riconosciuti automaticamente:
- Anno nascita / età
- Status (studente/lavoratore)
- Job title / ruolo
- Anni esperienza
- Azienda
- Motivazione partecipazione
- Interesse eventi futuri
- Topic interesse

### Feedback (es: responses.csv)

Campi riconosciuti automaticamente:
- Valutazione complessiva (stelle)
- Valutazione networking (stelle)
- Suggerimenti miglioramento (testo)
- Interesse futuro (Sì/No/Forse)

**Note:** tutti i campi sono opzionali. Il sistema funziona anche con dati parziali.

## Supporto

Per problemi o domande:

1. Leggi `QUICK_START.md` per setup rapido
2. Consulta `README.md` per troubleshooting
3. Verifica `ARCHITECTURE.md` per dettagli tecnici

## Versione

Sistema Datapizza Eventi v1.0.0  
Data creazione: 6 Ottobre 2025  
Python: 3.8+  
Licenza: Uso interno Datapizza

