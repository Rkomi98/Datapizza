# Monitoring

La panoramica completa e` nel [README principale](../README.md).

## Livelli di osservabilita`

### 1. Eventi applicativi

Persistiti in:

```text
storage/monitoring/events.jsonl
```

Campi principali:

- `timestamp`
- `event_type`
- `status`
- `dataset_id`
- `duration_ms`
- `metadata`

Eventi emessi oggi:

- `dashboard_render`
- `dataset_index`
- `rag_query`

### 2. Tracing

Le query RAG sono eseguite dentro un contesto `ContextTracing`.

Questo consente di vedere:

- numero di span
- durata complessiva
- token usage del client Datapizza, quando disponibile

## Cosa mostra la tab Monitoring

- KPI su numero eventi ed errori
- grafico conteggi per tipo evento
- grafico durate nel tempo
- tabella eventi recenti

## Note operative

- gli eventi applicativi non richiedono backend esterni
- il tracing e` utile soprattutto in sviluppo e debug
- se in futuro vuoi un exporter esterno, il codice usa gia` OpenTelemetry come base
