# Monitoring

## Livelli di osservabilità inclusi

### Eventi applicativi

Persistiti in `storage/monitoring/events.jsonl`.

Campi principali:

- `timestamp`
- `event_type`
- `status`
- `dataset_id`
- `duration_ms`
- `metadata`

Eventi emessi:

- `dashboard_render`
- `dataset_index`
- `rag_query`

### Trace Datapizza

Le query RAG vengono eseguite dentro:

```python
with ContextTracing().trace("rag_<dataset_id>"):
    ...
```

Questo permette di vedere:

- durata complessiva
- numero di span
- utilizzo token per i client Datapizza

## Export esterno

La base è pronta per collegare un exporter OpenTelemetry. Il codice applicativo usa già span manuali via `opentelemetry.trace`.

Per una piattaforma esterna puoi aggiungere, ad esempio:

- OTLP verso Grafana Tempo / Datadog
- Zipkin

## Note operative

- `DATAPIZZA_TRACE_CLIENT_IO` è lasciato a `FALSE` di default per evitare logging eccessivo di prompt e output.
- Se vuoi maggiore dettaglio in sviluppo, puoi impostarlo a `TRUE`.
- Le metriche mostrate nella dashboard derivano dagli eventi JSONL e quindi non richiedono un backend aggiuntivo.

