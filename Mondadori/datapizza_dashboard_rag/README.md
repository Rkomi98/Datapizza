# Datapizza Dashboard RAG

Dashboard Streamlit per scegliere uno dei CSV già presenti nella repo, visualizzarlo con grafici semplici e interrogarlo in linguaggio naturale con `datapizza-ai` usando solo OpenAI.

## Cosa fa

- Scansiona automaticamente i CSV presenti nella root della repo e in `datapizza_dashboard_rag/datasets/`.
- Riconosce i quattro dataset già disponibili:
  - `bar_chart_race_ready.csv`
  - `scatter_ready.csv`
  - `sankey_ready.csv`
  - `slope_ready.csv`
- Mostra KPI, preview tabellare e grafici dedicati per ciascun formato.
- Indicizza il dataset attivo in:
  - SQLite locale per query strutturate
  - Qdrant locale per retrieval semantico
- Espone una chat RAG/agent basata su `datapizza-ai` con:
  - `OpenAIClient`
  - `OpenAIEmbedder`
  - `QdrantVectorstore`
  - `SQLDatabase`
- Registra eventi applicativi in JSONL e usa `ContextTracing` di Datapizza per il tracing.

## Vincoli runtime

- `datapizza-ai` richiede Python `>=3.10,<3.13`.
- In questa macchina il comando `python3` attuale risulta `3.9.6`, quindi per eseguire davvero l'app serve un interprete Python 3.10+.
- La chiave usata dall'app viene letta da `.env` con il nome esatto `Openai`.

## Setup

1. Crea e attiva un ambiente Python 3.10+.
2. Installa le dipendenze:

```bash
pip install -r datapizza_dashboard_rag/requirements.txt
```

3. Verifica che nel `.env` della repo esista:

```env
Openai=...
```

4. Avvia la dashboard dalla root del repository:

```bash
streamlit run datapizza_dashboard_rag/app.py
```

## Struttura

```text
datapizza_dashboard_rag/
├── app.py
├── dashboard_rag/
│   ├── catalog.py
│   ├── charting.py
│   ├── config.py
│   ├── ingestion.py
│   ├── monitoring.py
│   └── rag.py
├── datasets/
├── docs/
│   ├── architecture.md
│   └── monitoring.md
└── storage/
```

## Come funziona

### Dashboard

- Selezioni un CSV dal pannello laterale.
- L'app riconosce il tipo di dataset dal suo schema.
- Genera KPI e 2 grafici semplici coerenti con il formato.

### RAG

- Alla prima domanda il dataset selezionato viene indicizzato.
- L'indicizzazione produce:
  - un profilo testuale del dataset
  - chunk embeddati con OpenAI
  - una collection locale Qdrant
  - tabelle SQLite raw e analitiche
- L'agente Datapizza usa sia retrieval che SQL per rispondere.

### Monitoring

- Ogni ingestione, render dashboard e query RAG produce un evento JSONL in `storage/monitoring/events.jsonl`.
- Le query RAG vengono anche tracciate con `ContextTracing`.
- La tab "Monitoring" mostra volume eventi, latenza media ed errori recenti.

## Aggiungere nuovi CSV

- Puoi salvare nuovi file in `datapizza_dashboard_rag/datasets/`.
- In alternativa, l'app continua a leggere anche i CSV presenti nella root del repository.
- I dataset non riconosciuti vengono comunque mostrati con grafici generici.

## Note sull'uso di OpenAI

- L'app usa solo la variabile `Openai`.
- Le altre chiavi eventualmente presenti nel `.env` non vengono lette dalla configurazione applicativa.

## Riferimenti Datapizza

- Docs: https://docs.datapizza.ai/0.0.2/
- Agent: https://docs.datapizza.ai/0.0.2/Guides/agent/
- Tracing: https://docs.datapizza.ai/0.0.2/Guides/Monitoring/tracing/
- QdrantVectorstore: https://docs.datapizza.ai/0.0.2/API%20Reference/Vectorstore/qdrant_vectorstore/
- SQLDatabase: https://docs.datapizza.ai/0.0.9/API%20Reference/Tools/SQLDatabase/

