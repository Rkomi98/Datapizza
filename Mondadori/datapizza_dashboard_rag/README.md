# Datapizza Dashboard RAG

Dashboard Streamlit per esplorare i CSV Mondadori e interrogarli con un RAG agentico basato su `datapizza-ai`, SQLite locale, Qdrant locale e OpenAI.

## Obiettivo

L'app unisce tre livelli in un unico flusso:

- esplorazione visuale dei dataset CSV
- indicizzazione locale per retrieval e query strutturate
- agente conversazionale capace di usare tool, memoria di chat e matching flessibile delle testate

L'obiettivo non e` solo "fare una chat sul CSV", ma costruire un assistente che:

- capisca il dataset attivo
- recuperi contesto semantico
- faccia query strutturate sui dati trasformati
- gestisca follow-up come `e per Focus?` o `solo per lei`
- mostri la fonte da cui ha tratto la risposta

## Stack

- UI: Streamlit
- Data prep: pandas
- Charting: Plotly
- Structured query layer: SQLite locale
- Retrieval layer: Qdrant locale su filesystem
- LLM orchestration: Datapizza Agent
- LLM/embeddings: OpenAI
- Monitoring: JSONL locale + tracing Datapizza

## Setup

1. Crea un ambiente Python 3.11+:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

2. Installa le dipendenze:

```bash
pip install -r datapizza_dashboard_rag/requirements.txt
```

3. Crea `datapizza_dashboard_rag/.env` oppure `.env` in root con almeno:

```env
Openai=...
DATAPIZZA_CHAT_MODEL=gpt-4o-mini
DATAPIZZA_EMBEDDING_MODEL=text-embedding-3-small
```

4. Avvia l'app dalla root repo:

```bash
streamlit run datapizza_dashboard_rag/app.py
```

## Architettura

### 1. Catalogazione dataset

Il modulo [`dashboard_rag/catalog.py`](./dashboard_rag/catalog.py) scansiona:

- tutti i CSV nella root del repository
- tutti i CSV in `datapizza_dashboard_rag/datasets/`

Per ogni file costruisce:

- `dataset_id` stabile
- `kind` inferito dallo schema
- descrizione sintetica del dataset

I tipi riconosciuti oggi sono:

- `bar_chart_race`
- `scatter`
- `sankey`
- `slope`
- `generic`

### 2. Trasformazione analitica

Il modulo [`dashboard_rag/ingestion.py`](./dashboard_rag/ingestion.py) produce due livelli:

- `raw_df`: CSV originale letto dal file
- `analysis_df`: tabella trasformata e normalizzata per analytics e RAG

Esempi:

- `bar_chart_race`: wide table mensile -> long table con `testata`, `mese`, `mese_dt`, `revenue_cumulativa_eur`
- `scatter`: normalizzazione numerica di KPI e revenue
- `slope`: trasformazione wide -> long con delta tra periodi

Il risultato viene persistito in SQLite con due tabelle:

- `raw_<dataset_id>`
- `analysis_<dataset_id>`

### 3. Profilazione del dataset

Sempre in [`dashboard_rag/ingestion.py`](./dashboard_rag/ingestion.py), l'app costruisce un profilo testuale del dataset che contiene:

- metadati
- colonne
- sommario numerico
- top business facts
- sample rows

Questo profilo viene salvato in:

- `storage/profiles/<dataset_id>.md`

ed e` la base del retrieval semantico.

### 4. Embedding e vector store

Il profilo viene spezzato in chunk e passato a OpenAI embeddings.

I vettori vengono poi salvati in Qdrant locale. L'implementazione usa [`dashboard_rag/local_qdrant.py`](./dashboard_rag/local_qdrant.py), un adapter locale introdotto per evitare un comportamento ambiguo del wrapper Datapizza standard con `location/path`.

Questa parte genera:

- collection Qdrant locale per dataset
- manifest locale in `storage/manifests/<dataset_id>.json`

### 5. Agente RAG

Il cuore della chat e` in [`dashboard_rag/rag.py`](./dashboard_rag/rag.py).

L'agente usa contemporaneamente:

- `retrieve_dataset_context` per il retrieval semantico da Qdrant
- `SQLDatabase` per query SQL sul dataset attivo
- tool deterministici per matching entita` e metriche business

Il comportamento e` volutamente agentico:

- il modello decide quali tool usare
- puo` combinare retrieval e SQL
- mantiene memoria tra i turni della chat
- riceve istruzioni esplicite per non sommare erroneamente valori cumulativi

### 6. Tool business-aware

Per correggere i problemi tipici del "solo SQL", il layer RAG include tool specifici:

- `resolve_entity_reference`
  Cerca match flessibili su colonne testuali come `testata`, `source`, `target`
- `get_entity_business_summary`
  Calcola metriche robuste per una singola entita`

Questi tool risolvono casi come:

- `FOCUS` vs `Focus`
- follow-up ellittici tipo `solo per focus`
- revenue cumulative interpretate male

Regola importante:

- se il dataset ha `revenue_cumulativa_eur`, la revenue totale della testata e` l'ultimo valore cumulativo disponibile, non la somma delle righe

Questo evita errori come sommare mese per mese una serie gia` cumulativa.

### 7. Memoria conversazionale

La memoria e` di sessione chat per dataset e vive in `st.session_state`.

In pratica:

- ogni dataset ha una propria `Memory`
- dopo ogni risposta la memoria aggiornata viene salvata
- il turno successivo riusa la stessa memoria

Questo permette follow-up naturali come:

- `e per Focus?`
- `solo per lei`
- `ok ma allora la revenue?`

senza perdere il contesto conversazionale.

### 8. References e anteprima fonte

Ogni risposta assistant puo` includere una reference visuale in UI.

Il pattern e`:

- la risposta mostra un marker `[*]`
- sotto compare un box `* Fonte e anteprima CSV`
- l'utente puo` aprirlo e vedere:
  - path del CSV sorgente
  - tabella raw
  - tabella analysis
  - preview filtrata sulla testata o entita` usata, quando disponibile

Questo rende piu` trasparente il legame tra risposta e dato sorgente.

### 9. Monitoring

Il modulo [`dashboard_rag/monitoring.py`](./dashboard_rag/monitoring.py) salva eventi applicativi in JSONL:

- render dashboard
- indicizzazione dataset
- query RAG
- errori

La tab Monitoring mostra:

- volumi per tipo evento
- latenza media
- errori recenti

## Flusso end-to-end

1. L'utente seleziona un CSV.
2. L'app riconosce il tipo dataset.
3. Vengono costruiti `raw_df` e `analysis_df`.
4. Alla prima domanda, il dataset viene indicizzato:
   - SQLite locale
   - profilo markdown
   - chunk embeddings
   - collection Qdrant locale
5. L'agente riceve la domanda e la memoria di chat.
6. L'agente decide se usare:
   - retrieval semantico
   - tool di entity resolution
   - tool business-aware
   - SQL
7. La risposta viene renderizzata con reference e anteprima fonte.
8. La memoria aggiornata viene salvata per i messaggi successivi.

## Struttura progetto

```text
datapizza_dashboard_rag/
├── app.py
├── README.md
├── dashboard_rag/
│   ├── catalog.py
│   ├── charting.py
│   ├── config.py
│   ├── ingestion.py
│   ├── local_qdrant.py
│   ├── monitoring.py
│   └── rag.py
├── datasets/
├── docs/
│   ├── architecture.md
│   └── monitoring.md
└── storage/
```

## File chiave

- [`app.py`](./app.py): UI, session state, chat, rendering references
- [`dashboard_rag/config.py`](./dashboard_rag/config.py): env, path locali, modelli OpenAI
- [`dashboard_rag/ingestion.py`](./dashboard_rag/ingestion.py): trasformazioni dataset, SQLite, profilo, embeddings
- [`dashboard_rag/local_qdrant.py`](./dashboard_rag/local_qdrant.py): adapter Qdrant locale
- [`dashboard_rag/rag.py`](./dashboard_rag/rag.py): agente, tool, memoria, retrieval e business logic
- [`dashboard_rag/monitoring.py`](./dashboard_rag/monitoring.py): eventi e telemetria locale

## Limiti attuali

- le answer dipendono comunque dall'LLM per il wording finale
- la precisione massima richiede che il dataset attivo sia quello giusto
- la memoria e` per sessione Streamlit, non ancora persistita su disco
- il retrieval semantico e` costruito sul profilo del dataset, non su ogni singola riga raw

## Evoluzioni utili

- persistenza su disco della memoria conversazionale
- citazioni ancora piu` granulari a livello riga/periodo
- tool business specifici per ogni tipo dataset
- verifica automatica post-risposta su query numeriche ad alto rischio

## Riferimenti

- Datapizza docs: https://docs.datapizza.ai/
- Streamlit: https://streamlit.io/
- Qdrant: https://qdrant.tech/
