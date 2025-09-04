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
from datapizzai.clients import ClientFactory
from datapizzai.tracing import ContextTracing

load_dotenv()

# Inizializza il sistema di tracing
tracer = ContextTracing()

# Configura client
client = ClientFactory.create(
    "openai", 
    os.getenv("OPENAI_API_KEY"), 
    "gpt-4"
)
```

**Spazio per screenshot: Configurazione iniziale del progetto**

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

**Spazio per screenshot: Output del tracing con token usage**

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

Questo esempio pratico combina il tracer contestuale di `datapizzai` con span manuali creati tramite OpenTelemetry per monitorare un flusso di lavoro completo. Lo script è stato progettato per essere il più chiaro possibile, con commenti dettagliati che spiegano ogni passaggio.

```python
#!/usr/bin/env python3
"""
Esempio pratico di monitoring con datapizzai.

Obiettivo:
Illustrare come combinare il tracing contestuale di `datapizzai` con 
la creazione di span manuali tramite OpenTelemetry per monitorare un 
flusso di lavoro realistico.

Cosa fa questo script:
1.  **Inizializza il tracing**: Configura sia `ContextTracing` di datapizzai per il monitoraggio generale, sia un tracer OpenTelemetry standard per span personalizzati.
2.  **Configura un client AI**: Usa `ClientFactory` per creare un client OpenAI. Se la API key non è disponibile, utilizza un client "mock" per permettere l'esecuzione.
3.  **Simula un flusso di lavoro**:
    - Recupera dati da un "database".
    - Valida i dati.
    - Esegue una logica di business che include una chiamata al client AI.
4.  **Crea Span Dettagliati**: Ogni passaggio del flusso (lettura DB, validazione, business logic) viene racchiuso in uno span manuale per un'analisi dettagliata delle performance e del flusso.
5.  **Stampa un output chiaro**: Mostra a console i passaggi eseguiti e il risultato finale. Alla fine, il trace di `ContextTracing` riassume le metriche chiave (token, durata).
"""

import os
import time
import logging
from dotenv import load_dotenv

# Import da OpenTelemetry per creare span manuali
from opentelemetry import trace

# Import da datapizzai per il client e il tracing contestuale
from datapizzai.clients import ClientFactory
from datapizzai.tracing import ContextTracing
from datapizzai.type import TextBlock, ROLE

# --- Configurazione Iniziale ---

# Abilita un logging chiaro per seguire l'esecuzione dello script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
logger = logging.getLogger(__name__)

# Carica le variabili d'ambiente da un file .env
load_dotenv()


# --- Funzioni Ausiliarie che simulano un'applicazione reale ---

def fetch_from_database():
    """Simula una chiamata a un database per recuperare dati."""
    logger.info("Tentativo di recupero dati...")
    time.sleep(0.3)  # Simula latenza di rete/DB
    logger.info("Dati recuperati.")
    return {"user_id": "USR-007", "request_text": "Spiegami i vantaggi del monitoring in un'applicazione AI."}

def validate_data(data: dict):
    """Simula la validazione dei dati ricevuti."""
    logger.info("Validazione dei dati in corso...")
    time.sleep(0.1)  # Simula tempo di elaborazione
    if data and "user_id" in data and len(data.get("request_text", "")) > 10:
        logger.info("Dati validi.")
        return True
    logger.error("Dati non validi o incompleti.")
    return False

def process_with_ai(data: dict, client):
    """
    Esegue la logica di business principale, che include una chiamata a un LLM.
    L'interazione con `client.invoke` viene tracciata automaticamente da `ContextTracing`.
    """
    logger.info("Elaborazione della richiesta con il client AI...")
    
    prompt = f"L'utente {data['user_id']} chiede: '{data['request_text']}'. Formula una risposta chiara e sintetica."
    
    # Questa chiamata viene tracciata automaticamente, inclusi i token usati
    response = client.invoke([TextBlock(text=prompt, role=ROLE.USER)])
    
    logger.info("Risposta AI generata.")
    return {"final_summary": response.text, "tokens_used": response.completion_tokens_used}

def get_ai_client():
    """
    Crea e restituisce un client AI. Se la chiave API non è configurata,
    restituisce un client fittizio (mock) per consentire l'esecuzione.
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY non trovata nel file .env")
            
        client = ClientFactory.create(
            provider="openai",
            api_key=api_key,
            model="gpt-4",
            temperature=0.7
        )
        logger.info("Client OpenAI configurato correttamente.")
        return client
    except Exception as e:
        logger.warning(f"{e}. Verrà utilizzato un client fittizio (mock).")
        
        # --- Definizione di un client Mock per l'esecuzione offline ---
        class MockResponse:
            text = "Il monitoring è fondamentale per tracciare performance, costi e affidabilità. (Risposta Mock)"
            prompt_tokens_used = 30
            completion_tokens_used = 45
            cached_tokens_used = 0
            
        class MockClient:
            def invoke(self, messages):
                time.sleep(0.5) # Simula latenza LLM
                return MockResponse()
                
        return MockClient()


# --- Flusso Principale ---

def run_monitored_workflow():
    """
    Esegue un flusso di lavoro completo, monitorandolo con `ContextTracing`
    e arricchendolo con span manuali OpenTelemetry.
    """
    
    # 1. Inizializza il tracer contestuale di datapizzai.
    #    Questo wrapper catturerà automaticamente le chiamate ai client datapizzai
    #    e fornirà un riepilogo finale.
    datapizzai_tracer = ContextTracing()

    # 2. Ottieni il tracer standard di OpenTelemetry.
    #    Questo serve per creare span manuali e avere un controllo granulare
    #    sul monitoraggio di parti specifiche del codice.
    otel_tracer = trace.get_tracer(__name__)

    # 3. Prepara il client AI
    ai_client = get_ai_client()

    # 4. Avvia il trace principale.
    #    Tutto ciò che accade all'interno di questo blocco `with` sarà parte
    #    di un unico trace, rendendo facile analizzare l'intera operazione.
    with datapizzai_tracer.trace("elaborazione_richiesta_completa") as main_trace:
        logger.info(">>> Inizio del workflow monitorato <<<")

        # Span 1: Recupero dati dal Database
        with otel_tracer.start_as_current_span("1. recupero_dati_db") as db_span:
            retrieved_data = fetch_from_database()
            db_span.set_attribute("user.id", retrieved_data.get("user_id"))
            db_span.set_attribute("db.system", "postgresql_simulation")

        # Span 2: Validazione Dati
        with otel_tracer.start_as_current_span("2. validazione_input") as validation_span:
            is_valid = validate_data(retrieved_data)
            validation_span.set_attribute("validation.success", is_valid)
            if not is_valid:
                logger.error("Workflow interrotto a causa di dati non validi.")
                return

        # Span 3: Logica di Business con AI
        # Questo span manuale serve a contestualizzare la chiamata AI.
        # La chiamata `client.invoke` al suo interno creerà a sua volta uno span
        # figlio automatico, grazie a `ContextTracing`.
        with otel_tracer.start_as_current_span("3. elaborazione_business_logic") as business_span:
            result = process_with_ai(retrieved_data, ai_client)
            business_span.set_attribute("ai.tokens_used", result.get("tokens_used"))
            business_span.set_attribute("result.summary_length", len(result.get("final_summary", "")))

        logger.info(f"\n--- RISULTATO FINALE ---\n{result['final_summary']}\n----------------------")
        logger.info(">>> Workflow monitorato completato con successo <<<")


if __name__ == "__main__":
    run_monitored_workflow()
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
