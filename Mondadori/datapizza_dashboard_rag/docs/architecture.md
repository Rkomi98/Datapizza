# Architettura

La documentazione principale del progetto vive in [README.md](../README.md).

Questo file riassume i punti architetturali piu` importanti.

## Obiettivo

Unire in un solo flusso:

- esplorazione visuale del CSV
- trasformazione analitica locale
- interrogazione conversazionale sul dataset attivo

## Componenti

### 1. Discovery

`dashboard_rag.catalog`

Responsabilita`:

- trovare i CSV disponibili
- inferire il tipo dataset
- costruire un `dataset_id` stabile

### 2. Ingestion

`dashboard_rag.ingestion`

Responsabilita`:

- leggere il CSV
- costruire `raw_df` e `analysis_df`
- scrivere SQLite locale
- generare profilo dataset e manifest
- indicizzare il profilo in Qdrant locale

### 3. Dashboard

`dashboard_rag.charting` + `app.py`

Responsabilita`:

- KPI
- insight
- grafici specifici per `kind`
- rendering Streamlit

### 4. RAG

`dashboard_rag.rag`

Responsabilita`:

- fast path deterministico per richieste frequenti
- memoria di chat per dataset
- entity resolution e period matching
- delta su serie cumulative
- fallback agentico con Datapizza Agent, retrieval e SQL

### 5. Persistence locale

Asset usati:

- SQLite locale
- Qdrant locale su filesystem
- profili markdown
- manifest JSON
- eventi monitoring in JSONL

## Flusso

1. l'utente seleziona un dataset
2. l'app costruisce `raw_df` e `analysis_df`
3. la dashboard mostra i grafici
4. alla prima domanda RAG vengono preparati gli asset locali
5. `rag.py` prova prima il percorso deterministico
6. se non basta, usa l'agente Datapizza con tool, retrieval e SQL
7. la risposta torna con references e memoria aggiornata

## Nota importante

Per i dettagli operativi, setup e flusso UI, usa come riferimento canonico [README.md](../README.md).
