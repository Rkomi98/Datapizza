# Guida monitoring con datapizzai

## Panoramica

Questa guida illustra come implementare un sistema di monitoring completo utilizzando la libreria `datapizzai`. Il monitoring permette di tracciare le performance, i token utilizzati e il comportamento dei client AI in tempo reale.

## Indice

- [1. Configurazione base](#1-configurazione-base)
- [2. Client trace input/output/memory](#2-client-trace-inputoutputmemory)
- [3. Manual span creation](#3-manual-span-creation)
- [4. Adding external exporters](#4-adding-external-exporters)
- [5. Performance considerations](#5-performance-considerations)
- [6. Configurazione monitoring con Grafana](#6-configurazione-monitoring-con-grafana)

## 1. Configurazione base

Per iniziare con il monitoring in datapizzai, è necessario configurare il sistema di tracing OpenTelemetry integrato.

### Installazione dipendenze

```bash
pip install datapizzai opentelemetry-api opentelemetry-sdk opentelemetry-exporter-zipkin opentelemetry-exporter-otlp
```

### Setup iniziale

```python
import os
from dotenv import load_dotenv
from opentelemetry import trace
from datapizzai.clients import ClientFactory
from datapizzai.tracing import ContextTracing

load_dotenv()

# Inizializza il sistema di tracing
tracer = ContextTracing()

# Configura client
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1
)
```

## 2. Client trace input/output/memory

Il tracing automatico dei client permette di monitorare tutte le interazioni con i modelli AI.

### Esempio base con tracing

```python
from datapizzai.tracing import ContextTracing
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

# Inizializza componenti
tracer = ContextTracing()
client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4")
memory = Memory()

def esempio_tracing_base():
    """Esempio di tracing automatico di input/output"""
    
    with tracer.trace("chat_conversation") as trace:
        # Aggiungi messaggio utente alla memoria
        memory.add(TextBlock(text="Spiega cos'è il machine learning", role=ROLE.USER))
        
        # Invoca il client - viene tracciato automaticamente
        response = client.invoke(memory.get_memory())
        
        # Aggiungi risposta alla memoria
        memory.add(TextBlock(text=response.text, role=ROLE.ASSISTANT))
        
        print(f"Response: {response.text}")
        print(f"Tokens used: {response.prompt_tokens_used + response.completion_tokens_used}")
        
        # Il trace mostra automaticamente:
        # - Token utilizzati (prompt, completion, cached)
        # - Durata dell'operazione
        # - Numero di span generati
        
        return response

# Esegui l'esempio
response = esempio_tracing_base()
```

### Parametri del trace

Il sistema di tracing cattura automaticamente:

- **prompt_tokens_used**: Token del prompt inviato
- **completion_tokens_used**: Token generati dal modello  
- **cached_tokens_used**: Token serviti dalla cache
- **model_name**: Nome del modello utilizzato
- **duration**: Durata dell'operazione in secondi

## 3. Manual span creation

Per un controllo più granulare, è possibile creare span manuali per tracciare operazioni specifiche.

### Tipi di span disponibili

```python
from datapizzai.tracing.tracing import generation_span, agent_span, tool_span

def esempio_span_manuali():
    """Esempio di creazione manuale di span"""
    
    with tracer.trace("operazione_complessa") as trace:
        
        # Span per generazione di contenuto
        with generation_span("generazione_testo") as span:
            span.set_attribute("custom_param", "valore")
            span.set_attribute("input_length", 150)
            
            response = client.invoke([
                TextBlock(text="Scrivi una poesia", role=ROLE.USER)
            ])
            
            span.set_attribute("output_length", len(response.text))
            span.set_attribute("model_name", "gpt-4")
        
        # Span per operazioni di tool
        with tool_span("elaborazione_dati") as span:
            span.set_attribute("operation", "data_processing")
            
            # Simula elaborazione dati
            import time
            time.sleep(0.5)
            
            processed_data = {"status": "completed", "records": 100}
            span.set_attribute("records_processed", processed_data["records"])
        
        # Span per agenti
        with agent_span("agent_decisione") as span:
            span.set_attribute("agent_type", "decision_maker")
            
            decision = "continue" if len(response.text) > 50 else "stop"
            span.set_attribute("decision", decision)
    
    return response

# Esegui l'esempio
result = esempio_span_manuali()
```

**Spazio per screenshot: Dettagli degli span manuali nel trace**

### Attributi personalizzati

```python
def esempio_attributi_personalizzati():
    """Esempio di attributi personalizzati negli span"""
    
    with tracer.trace("analisi_sentimento") as trace:
        with generation_span("sentiment_analysis") as span:
            # Attributi per input
            span.set_attribute("input_type", "text")
            span.set_attribute("language", "italian")
            span.set_attribute("text_length", 250)
            
            # Invoca modello per analisi sentiment
            prompt = "Analizza il sentiment di questo testo: 'Oggi è una giornata fantastica!'"
            response = client.invoke([TextBlock(text=prompt, role=ROLE.USER)])
            
            # Attributi per output
            span.set_attribute("sentiment_detected", "positive")
            span.set_attribute("confidence_score", 0.95)
            span.set_attribute("response_tokens", response.completion_tokens_used)
            
    return response
```

## 4. Adding external exporters

Per integrare il monitoring con sistemi esterni, è possibile configurare esportatori personalizzati.

### 4.1. Create the resource

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

def setup_monitoring_resource():
    """Configura risorsa OpenTelemetry"""
    
    resource = Resource.create({
        SERVICE_NAME: "datapizzai-app",
        SERVICE_VERSION: "1.0.0",
        "environment": "production",
        "team": "ai-team"
    })
    
    # Configura tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider
```

### 4.2. Zipkin integration

```python
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_zipkin_exporter():
    """Configura esportatore Zipkin"""
    
    tracer_provider = setup_monitoring_resource()
    
    # Configura Zipkin exporter
    zipkin_exporter = ZipkinExporter(
        endpoint="http://localhost:9411/api/v2/spans",
        local_node_ipv4="127.0.0.1",
        local_node_ipv6="::1",
        local_node_port=5000,
    )
    
    # Aggiungi span processor
    span_processor = BatchSpanProcessor(zipkin_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    print("✅ Zipkin exporter configurato")
    return tracer_provider

# Esempio di utilizzo con Zipkin
def esempio_zipkin():
    """Esempio con esportazione verso Zipkin"""
    
    setup_zipkin_exporter()
    tracer = ContextTracing()
    
    with tracer.trace("zipkin_example") as trace:
        client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-3.5-turbo")
        
        response = client.invoke([
            TextBlock(text="Crea un riassunto di 50 parole", role=ROLE.USER)
        ])
        
        print(f"Response inviata a Zipkin: {response.text[:100]}...")
```

**Spazio per screenshot: Dashboard Zipkin con trace datapizzai**

### 4.3. OTLP (OpenTelemetry Protocol)

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_otlp_exporter():
    """Configura esportatore OTLP per Jaeger/Grafana"""
    
    tracer_provider = setup_monitoring_resource()
    
    # Configura OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317",  # Jaeger OTLP endpoint
        headers={
            "Authorization": "Bearer your-token-here"
        }
    )
    
    # Aggiungi span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    print("✅ OTLP exporter configurato")
    return tracer_provider

# Esempio completo con OTLP
def esempio_otlp_completo():
    """Esempio completo con esportazione OTLP"""
    
    setup_otlp_exporter()
    tracer = ContextTracing()
    
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4")
    memory = Memory()
    
    with tracer.trace("conversazione_otlp") as trace:
        # Primo messaggio
        memory.add(TextBlock(text="Ciao, come stai?", role=ROLE.USER))
        response1 = client.invoke(memory.get_memory())
        memory.add(TextBlock(text=response1.text, role=ROLE.ASSISTANT))
        
        # Secondo messaggio  
        memory.add(TextBlock(text="Parlami di Python", role=ROLE.USER))
        response2 = client.invoke(memory.get_memory())
        memory.add(TextBlock(text=response2.text, role=ROLE.ASSISTANT))
        
        print(f"Conversazione completata. Trace inviato via OTLP.")
```

**Spazio per screenshot: Jaeger UI con trace OTLP**

## 5. Performance considerations

### Monitoring delle performance

```python
import time
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PerformanceMetrics:
    """Metriche di performance"""
    operation_name: str
    duration_seconds: float
    tokens_used: int
    memory_usage_mb: float
    cache_hit_rate: float

class PerformanceMonitor:
    """Monitor delle performance per datapizzai"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.tracer = ContextTracing()
    
    def monitor_operation(self, operation_name: str):
        """Decorator per monitorare operazioni"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                with self.tracer.trace(f"perf_{operation_name}") as trace:
                    result = func(*args, **kwargs)
                    
                    duration = time.time() - start_time
                    
                    # Calcola metriche
                    tokens_used = 0
                    if hasattr(result, 'prompt_tokens_used'):
                        tokens_used = result.prompt_tokens_used + result.completion_tokens_used
                    
                    # Simula calcolo memoria
                    import psutil
                    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
                    
                    # Salva metriche
                    metrics = PerformanceMetrics(
                        operation_name=operation_name,
                        duration_seconds=duration,
                        tokens_used=tokens_used,
                        memory_usage_mb=memory_usage,
                        cache_hit_rate=0.0  # Da implementare con cache
                    )
                    self.metrics.append(metrics)
                    
                    return result
            return wrapper
        return decorator
    
    def get_performance_report(self) -> Dict:
        """Genera report delle performance"""
        if not self.metrics:
            return {"error": "Nessuna metrica disponibile"}
        
        total_operations = len(self.metrics)
        avg_duration = sum(m.duration_seconds for m in self.metrics) / total_operations
        total_tokens = sum(m.tokens_used for m in self.metrics)
        avg_memory = sum(m.memory_usage_mb for m in self.metrics) / total_operations
        
        return {
            "total_operations": total_operations,
            "avg_duration_seconds": round(avg_duration, 3),
            "total_tokens_used": total_tokens,
            "avg_memory_usage_mb": round(avg_memory, 2),
            "operations_per_second": round(1 / avg_duration, 2) if avg_duration > 0 else 0
        }

# Esempio di utilizzo
monitor = PerformanceMonitor()

@monitor.monitor_operation("chat_response")
def chat_with_monitoring():
    """Funzione di chat con monitoring"""
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-3.5-turbo")
    
    response = client.invoke([
        TextBlock(text="Spiega il concetto di monitoring in 100 parole", role=ROLE.USER)
    ])
    
    return response

# Esegui e ottieni report
for i in range(3):
    response = chat_with_monitoring()
    print(f"Operazione {i+1} completata")

print("\n📊 Performance Report:")
report = monitor.get_performance_report()
for key, value in report.items():
    print(f"  {key}: {value}")
```

**Spazio per screenshot: Report delle performance**

### Ottimizzazioni

```python
def configurazione_ottimizzata():
    """Configurazione ottimizzata per production"""
    
    # Batch processing per ridurre overhead
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    
    tracer_provider = setup_monitoring_resource()
    
    # Configura batch processor ottimizzato
    batch_processor = BatchSpanProcessor(
        span_exporter=otlp_exporter,
        max_queue_size=2048,        # Coda più grande
        export_timeout_millis=30000, # Timeout più lungo
        schedule_delay_millis=5000,  # Ritardo ottimizzato
        max_export_batch_size=512    # Batch size ottimizzato
    )
    
    tracer_provider.add_span_processor(batch_processor)
    
    print("✅ Configurazione ottimizzata applicata")
```

## 6. Configurazione monitoring con Grafana

### Setup Grafana + Tempo

```yaml
# docker-compose.yml per Grafana stack
version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning

  tempo:
    image: grafana/tempo:latest
    command: [ "-config.file=/etc/tempo.yaml" ]
    volumes:
      - ./tempo/tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo
    ports:
      - "3200:3200"   # Tempo
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP

volumes:
  grafana-data:
  tempo-data:
```

### Configurazione Tempo

```yaml
# tempo/tempo.yaml
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
```

### Dashboard Grafana per datapizzai

```python
def setup_grafana_dashboard():
    """Configura dashboard Grafana per datapizzai"""
    
    dashboard_config = {
        "dashboard": {
            "title": "DatapizzAI Monitoring",
            "panels": [
                {
                    "title": "Token Usage Over Time",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "rate(datapizzai_tokens_total[5m])",
                            "legendFormat": "{{model_name}}"
                        }
                    ]
                },
                {
                    "title": "Response Time Distribution", 
                    "type": "histogram",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, datapizzai_duration_seconds)",
                            "legendFormat": "95th percentile"
                        }
                    ]
                },
                {
                    "title": "Cache Hit Rate",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "datapizzai_cache_hits / datapizzai_total_requests",
                            "legendFormat": "Cache Hit Rate"
                        }
                    ]
                }
            ]
        }
    }
    
    print("📊 Dashboard Grafana configurata")
    return dashboard_config

# Integrazione con Grafana
def esempio_completo_grafana():
    """Esempio completo con Grafana monitoring"""
    
    # Setup OTLP per Tempo
    setup_otlp_exporter()
    
    # Setup dashboard
    setup_grafana_dashboard()
    
    tracer = ContextTracing()
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4")
    
    # Simula traffico per dashboard
    for i in range(10):
        with tracer.trace(f"grafana_example_{i}") as trace:
            response = client.invoke([
                TextBlock(text=f"Messaggio numero {i+1}", role=ROLE.USER)
            ])
            
            print(f"✅ Richiesta {i+1} tracciata in Grafana")
            time.sleep(1)
    
    print("🎯 Controlla Grafana su http://localhost:3000")
    print("   Username: admin, Password: admin")
```

**Spazio per screenshot: Dashboard Grafana con metriche datapizzai**

## Esempio completo

```python
#!/usr/bin/env python3
"""
Esempio completo di monitoring con datapizzai
Dimostra l'integrazione tra ContextTracing e span manuali OpenTelemetry
"""

import os
import time
from dotenv import load_dotenv
from opentelemetry import trace
from datapizzai.clients import ClientFactory
from datapizzai.tracing import ContextTracing
from datapizzai.type import TextBlock, ROLE

load_dotenv()

# Inizializza il sistema di tracing
context_tracer = ContextTracing()

# Configura client
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4",
    temperature=0.7
)

# Tracer OpenTelemetry per span manuali
tracer = trace.get_tracer(__name__)

def fetch_from_database():
    """Simula recupero dati dal database"""
    print("📊 Recupero dati dal database...")
    time.sleep(0.3)  # Simula latenza database
    
    # Dati di esempio per una richiesta di analisi
    data = {
        "user_id": "USR-001",
        "request_type": "analysis",
        "content": "Analizza le performance del nostro sistema di monitoring",
        "priority": "high",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    print(f"✅ Dati recuperati: {data['request_type']} per utente {data['user_id']}")
    return data

def validate_data(data):
    """Valida i dati recuperati"""
    print("🔍 Validazione dati in corso...")
    time.sleep(0.1)  # Simula tempo di validazione
    
    # Controlli di validazione
    if not data:
        raise ValueError("Dati vuoti")
    
    required_fields = ["user_id", "request_type", "content"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValueError(f"Campi mancanti: {missing_fields}")
    
    if len(data.get("content", "")) < 10:
        raise ValueError("Contenuto troppo breve")
    
    print("✅ Validazione completata con successo")
    return True

def process_business_rules(data):
    """Elabora la logica di business con chiamata AI"""
    print("🤖 Elaborazione logica di business...")
    
    # Costruisce il prompt basato sui dati
    prompt = f"""
    Analizza la seguente richiesta di {data['user_id']}:
    Tipo: {data['request_type']}
    Contenuto: {data['content']}
    Priorità: {data['priority']}
    
    Fornisci un'analisi dettagliata e raccomandazioni pratiche.
    """
    
    # Chiamata al client AI (tracciata automaticamente da ContextTracing)
    response = client.invoke([TextBlock(text=prompt, role=ROLE.USER)])
    
    # Elabora il risultato
    result = {
        "user_id": data["user_id"],
        "analysis": response.text,
        "tokens_used": response.completion_tokens_used,
        "processing_time": time.time(),
        "status": "completed"
    }
    
    print(f"✅ Elaborazione completata - {result['tokens_used']} token utilizzati")
    return result

def main():
    """Esempio completo con ContextTracing e span manuali"""
    print("🚀 Avvio esempio monitoring completo")
    
    with context_tracer.trace("business_workflow_complete") as trace:
        
        # Span manuale per operazione database
        with tracer.start_as_current_span("database_query") as db_span:
            # Attributi per il database span
            db_span.set_attribute("db.system", "postgresql")
            db_span.set_attribute("db.operation", "select")
            
            # Database operation
            data = fetch_from_database()
            
            db_span.set_attribute("db.records_fetched", 1)
            db_span.set_attribute("user.id", data["user_id"])

        # Span manuale per validazione
        with tracer.start_as_current_span("data_validation") as validation_span:
            validation_span.set_attribute("validation.type", "business_rules")
            
            # Validation logic
            try:
                validate_data(data)
                validation_span.set_attribute("validation.success", True)
            except ValueError as e:
                validation_span.set_attribute("validation.success", False)
                validation_span.set_attribute("validation.error", str(e))
                raise

        # Span manuale per logica di business
        with tracer.start_as_current_span("business_logic") as business_span:
            business_span.set_attribute("business.operation", "ai_analysis")
            business_span.set_attribute("business.priority", data["priority"])
            
            # Core business logic (include chiamata AI tracciata automaticamente)
            result = process_business_rules(data)
            
            business_span.set_attribute("business.tokens_consumed", result["tokens_used"])
            business_span.set_attribute("business.status", result["status"])
    
    print("\n🎯 Workflow completato!")
    print("📊 Il trace mostra:")
    print("  - Span manuali per database, validazione e business logic")
    print("  - Span automatici per le chiamate AI")
    print("  - Attributi personalizzati per ogni operazione")
    print("  - Token usage e performance metrics")

if __name__ == "__main__":
    main()
```

**Spazio per screenshot: Output finale del trace completo**

## Conclusioni

Il sistema di monitoring di datapizzai offre:

- **Tracing automatico** di tutte le interazioni con i modelli
- **Span personalizzati** per operazioni specifiche  
- **Integrazione OpenTelemetry** con sistemi esterni
- **Performance monitoring** in tempo reale
- **Dashboard Grafana** per visualizzazione avanzata

Il monitoring è essenziale per:
- Ottimizzare l'utilizzo dei token
- Identificare colli di bottiglia
- Monitorare costi operativi
- Garantire performance stabili in produzione
