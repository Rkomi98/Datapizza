# Setup Docker per monitoring datapizza-ai

## Quick start

```bash
# 1. Avvia tutti i servizi
docker-compose up -d

# 2. Verifica che siano attivi
docker ps

# 3. Testa gli endpoint
curl http://localhost:9411/health      # Zipkin
curl http://localhost:3000/health      # Grafana
curl http://localhost:4317             # OTLP (dovrebbe dare errore ma conferma che è attivo)
```

## Servizi disponibili

- **Zipkin**: http://localhost:9411 (tracing UI)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Tempo**: http://localhost:3200 (backend tracing)
- **OTLP**: localhost:4317 (gRPC) e localhost:4318 (HTTP)

## 1. Setup Zipkin (semplice)

```bash
# Avvia solo Zipkin
docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin

# Verifica
curl http://localhost:9411/health
```

## 2. Setup completo (Grafana + Tempo + Zipkin)

Crea il file `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # Zipkin per tracing semplice
  zipkin:
    image: openzipkin/zipkin
    container_name: zipkin
    ports:
      - "9411:9411"
    environment:
      - STORAGE_TYPE=mem

  # Grafana per visualizzazione avanzata
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - tempo

  # Tempo per backend tracing
  tempo:
    image: grafana/tempo:latest
    container_name: tempo
    command: [ "-config.file=/etc/tempo.yaml" ]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo
    ports:
      - "3200:3200"   # Tempo API
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP

volumes:
  grafana-data:
  tempo-data:
```

## 3. Configurazione Tempo

Crea il file `tempo.yaml`:

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

ingester:
  trace_idle_period: 10s
  max_block_bytes: 1_000_000
  max_block_duration: 5m

compactor:
  compaction:
    compaction_window: 1h
    max_block_bytes: 100_000_000
    block_retention: 1h
    compacted_block_retention: 10m

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces

query_frontend:
  search:
    duration_slo: 5s
    throughput_bytes_slo: 1.073741824e+09
  trace_by_id:
    duration_slo: 5s
```

## 4. Configurazione Grafana

Crea la cartella `grafana/provisioning/datasources/` e il file `tempo.yaml`:

```yaml
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    orgId: 1
    url: http://tempo:3200
    basicAuth: false
    isDefault: true
    version: 1
    editable: false
    apiVersion: 1
    uid: tempo
```

## 5. Comandi utili

### Avvio servizi
```bash
# Avvia tutto
docker-compose up -d

# Solo Zipkin (minimo)
docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin

# Solo Grafana + Tempo
docker-compose up -d grafana tempo
```

### Verifica stato
```bash
# Controlla container attivi
docker ps

# Log dei servizi
docker-compose logs zipkin
docker-compose logs grafana
docker-compose logs tempo

# Health check
curl http://localhost:9411/health
curl http://localhost:3000/api/health
```

### Cleanup
```bash
# Ferma tutto
docker-compose down

# Rimuovi volumi (ATTENZIONE: cancella i dati)
docker-compose down -v

# Rimuovi solo Zipkin standalone
docker stop zipkin && docker rm zipkin
```

## 6. Test di integrazione

Una volta avviati i servizi, testa con questo codice Python:

```python
import os
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from datapizza.clients import ClientFactory
from datapizza.tracing import ContextTracing
from datapizza.type import TextBlock

load_dotenv()

def test_monitoring_stack():
    """Testa l'intero stack di monitoring"""
    
    # Inizializza datapizza-ai tracing
    context_tracer = ContextTracing()
    tracer_provider = trace.get_tracer_provider()
    
    # Configura Zipkin
    zipkin_exporter = ZipkinExporter(endpoint="http://localhost:9411/api/v2/spans")
    zipkin_processor = BatchSpanProcessor(zipkin_exporter)
    tracer_provider.add_span_processor(zipkin_processor)
    
    # Configura OTLP (per Grafana/Tempo)
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
    otlp_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(otlp_processor)
    
    print("✅ Monitoring stack configurato")
    
    # Test con datapizza-ai
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    
    with context_tracer.trace("monitoring_stack_test") as trace:
        response = client.invoke([
            TextBlock(content="Scrivi una frase sul monitoring")
        ])
        
        print(f"🤖 Risposta: {response.text}")
        print(f"📊 Token: {response.prompt_tokens_used + response.completion_tokens_used}")
    
    print("🎯 Controlla i trace su:")
    print("  - Zipkin: http://localhost:9411")
    print("  - Grafana: http://localhost:3000 (admin/admin)")

if __name__ == "__main__":
    test_monitoring_stack()
```

## Troubleshooting

### Errore "Overriding of current TracerProvider is not allowed"
- **Causa**: datapizza-ai ha già inizializzato OpenTelemetry
- **Soluzione**: Inizializza `ContextTracing()` PRIMA di configurare gli esportatori

### Zipkin non riceve trace
- Verifica che Zipkin sia attivo: `curl http://localhost:9411/health`
- Controlla i log: `docker logs zipkin`
- Verifica l'endpoint nell'esportatore: `http://localhost:9411/api/v2/spans`

### OTLP connection refused
- Verifica che Tempo sia attivo: `docker ps | grep tempo`
- Controlla la porta: `netstat -tlnp | grep 4317`
- Verifica la configurazione in `tempo.yaml`

### Grafana non mostra trace
- Verifica che il datasource Tempo sia configurato
- Controlla la connettività: Grafana → Tempo
- Verifica che i trace arrivino a Tempo: `curl http://localhost:3200/api/echo`
