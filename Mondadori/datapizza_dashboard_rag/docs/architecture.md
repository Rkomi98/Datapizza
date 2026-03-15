# Architettura

## Obiettivo

Unire esplorazione visuale dei CSV e interrogazione in linguaggio naturale in un unico flusso, usando `datapizza-ai` come strato di orchestrazione LLM/RAG.

## Componenti

### 1. Discovery

`dashboard_rag.catalog` cerca CSV in:

- root della repo
- `datapizza_dashboard_rag/datasets/`

Ogni dataset viene classificato in una delle famiglie:

- `sankey`
- `scatter`
- `bar_chart_race`
- `slope`
- `generic`

### 2. Dashboard

`dashboard_rag.charting` costruisce:

- KPI
- grafici Plotly coerenti con il tipo dataset
- insight sintetici da mostrare sopra ai grafici

### 3. Ingestion

`dashboard_rag.ingestion` crea due rappresentazioni:

- `raw_<dataset_id>`: copia fedele del CSV
- `analysis_<dataset_id>`: forma normalizzata utile per SQL e analytics

Output persistiti:

- SQLite locale
- profilo markdown del dataset
- manifest JSON
- collection Qdrant locale

### 4. RAG

`dashboard_rag.rag` usa:

- `OpenAIClient` per generazione
- `OpenAIEmbedder` per embedding
- `QdrantVectorstore` per retrieval
- `SQLDatabase` per interrogare SQLite
- `Agent` Datapizza per orchestrare i tool

L'approccio è ibrido:

- retrieval per contesto, glossario e insight
- SQL per risposte numeriche verificabili

### 5. Monitoring

`dashboard_rag.monitoring` scrive eventi JSONL applicativi.

In parallelo il codice RAG avvolge le operazioni in `ContextTracing`, così è possibile collegare un exporter OpenTelemetry se servirà un backend esterno.

## Flusso end-to-end

1. L'utente seleziona un CSV.
2. La dashboard lo carica e produce grafici.
3. Alla prima domanda RAG il dataset viene indicizzato.
4. L'agente usa retrieval + SQL sui dati del dataset attivo.
5. Gli eventi vengono registrati e visualizzati nella tab Monitoring.

