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
        memory.add_turn([TextBlock(content="Spiega cos'è il machine learning")], ROLE.USER)
        
        # Invoca il client - viene tracciato automaticamente
        response = client.invoke("", memory=memory)
        
        # Aggiungi risposta alla memoria
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        
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
```bash
╭────────────────────────────────────── Trace Summary of chat_conversation ───────────────────────────────────────╮
│ Total Spans: 2                                                                                                  │
│ Duration: 17.97s                                                                                                │
│                          Token Usage                                                                            │
│ ┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓                                                   │
│ ┃ Model ┃ Prompt Tokens ┃ Completion Tokens ┃ Cached Tokens ┃                                                   │
│ ┡━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩                                                   │
│ │ gpt-5 │ 13            │ 912               │ 0             │                                                   │
│ └───────┴───────────────┴───────────────────┴───────────────┘                                                   │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
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
                TextBlock(content="Scrivi una poesia")
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

```bash
╭───────────────────────────────────── Trace Summary of operazione_complessa ─────────────────────────────────────╮
│ Total Spans: 5                                                                                                  │
│ Duration: 11.5s                                                                                                 │
│                          Token Usage                                                                            │
│ ┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓                                                   │
│ ┃ Model ┃ Prompt Tokens ┃ Completion Tokens ┃ Cached Tokens ┃                                                   │
│ ┡━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩                                                   │
│ │ gpt-5 │ 10            │ 748               │ 0             │                                                   │
│ └───────┴───────────────┴───────────────────┴───────────────┘                                                   │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
### Attributi personalizzati

```python
def esempio_attributi_personalizzati():
    """Esempio di attributi personalizzati negli span"""
    
    with tracer.trace("sentiment_analysis_father") as trace:
        with generation_span("sentiment_analysis_child") as span:
            span.set_attribute("model_name", client.model_name)  # es. "gpt-4o"
            
            # Attributi per input
            span.set_attribute("input_type", "text")
            span.set_attribute("language", "italian")
            span.set_attribute("text_length", 250)
            
            # Invoca modello per analisi sentiment
            prompt = "Analizza il sentiment di questo testo: 'Oggi è una giornata fantastica!'"
            response = client.invoke([TextBlock(content=prompt)])
            
            # Attributi per output
            span.set_attribute("sentiment_detected", "positive")
            span.set_attribute("confidence_score", 0.95)
            span.set_attribute("response_tokens", response.completion_tokens_used)
            
    return response
```
```bash
╭────────────────────────────────── Trace Summary of sentiment_analysis_father ───────────────────────────────────╮
│ Total Spans: 3                                                                                                  │
│ Duration: 8.86s                                                                                                 │
│                          Token Usage                                                                            │
│ ┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓                                                   │
│ ┃ Model ┃ Prompt Tokens ┃ Completion Tokens ┃ Cached Tokens ┃                                                   │
│ ┡━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩                                                   │
│ │ gpt-5 │ 23            │ 400               │ 0             │                                                   │
│ └───────┴───────────────┴───────────────────┴───────────────┘                                                   │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
## 4. Adding external exporters

Per integrare il monitoring con sistemi esterni, è possibile configurare esportatori personalizzati.

### 4.1. Create the resource

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

def setup_monitoring_resource():
    """Configura risorsa OpenTelemetry (compatibile con datapizzai)"""
    
    # Ottieni il tracer provider esistente o creane uno nuovo
    tracer_provider = trace.get_tracer_provider()
    
    # Se è un ProxyTracerProvider, configurane uno nuovo
    from opentelemetry.trace import ProxyTracerProvider
    if isinstance(tracer_provider, ProxyTracerProvider):
        resource = Resource.create({
            SERVICE_NAME: "datapizzai-app",
            SERVICE_VERSION: "1.0.0",
            "environment": "production",
            "team": "ai-team"
        })
        
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider
```

### 4.2. Zipkin integration

```python
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_zipkin_exporter():
    """Configura esportatore Zipkin (compatibile con datapizzai)"""
    
    # IMPORTANTE: Inizializza ContextTracing PRIMA di configurare esportatori
    context_tracer = ContextTracing()
    
    # Ottieni il tracer provider configurato da datapizzai
    tracer_provider = trace.get_tracer_provider()
    
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
    return context_tracer

# Esempio di utilizzo con Zipkin
def esempio_zipkin():
    """Esempio con esportazione verso Zipkin"""
    
    # PRIMA: Avvia Zipkin con Docker
    # docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin
    
    tracer = setup_zipkin_exporter()  # Restituisce il ContextTracing configurato
    
    with tracer.trace("zipkin_example") as trace:
        client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
        
        response = client.invoke([
            TextBlock(content="Crea un riassunto di 50 parole")
        ])
        
        print(f"Response inviata a Zipkin: {response.text[:100]}...")
        print("🎯 Controlla Zipkin su http://localhost:9411")

# Esegui l'esempio
esempio_zipkin()
```

<img width="3443" height="1255" alt="immagine" src="https://github.com/user-attachments/assets/99d01347-1069-40dd-a529-feb741ebbd5b" />


### 4.3. OTLP (OpenTelemetry Protocol)

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

def setup_otlp_exporter():
    """Configura esportatore OTLP per Jaeger/Grafana"""
    
    tracer_provider = setup_monitoring_resource()
    
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://localhost:4317"
        # Per Jaeger: endpoint="http://localhost:14250"
        # Per Zipkin: usare ZipkinExporter invece
        # headers={"Authorization": "Bearer <token>"}  # Solo se necessario
    )
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    print("✅ OTLP exporter configurato")
    return tracer_provider

def setup_zipkin_exporter():
    """Configura esportatore Zipkin"""
    
    tracer_provider = setup_monitoring_resource()
    
    zipkin_exporter = ZipkinExporter(
        endpoint="http://localhost:9411/api/v2/spans"
    )
    
    span_processor = BatchSpanProcessor(zipkin_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    print("✅ Zipkin exporter configurato")
    return tracer_provider

# Esempio completo con OTLP
def esempio_otlp_completo():
    """Esempio completo con esportazione OTLP"""
    
    setup_otlp_exporter()
    tracer = ContextTracing()
    
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    memory = Memory()
    
    with tracer.trace("conversazione_otlp") as trace:
        # Primo messaggio
        memory.add_turn([TextBlock(content="Ciao, come stai?")], ROLE.USER)
        response1 = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response1.text)], ROLE.ASSISTANT)
    
        memory.add_turn([TextBlock(content="Parlami di Python")], ROLE.USER)
        response2 = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response2.text)], ROLE.ASSISTANT)

        
        print(f"Conversazione completata. Trace inviato via OTLP.")

# Esempio completo con Zipkin
def esempio_zipkin_completo():
    """Esempio completo con esportazione Zipkin"""
    
    setup_zipkin_exporter()
    tracer = ContextTracing()
    
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    memory = Memory()
    
    with tracer.trace("conversazione_zipkin") as trace:
        # Primo messaggio
        memory.add_turn([TextBlock(content="Ciao, come stai?")], ROLE.USER)
        response1 = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response1.text)], ROLE.ASSISTANT)
    
        memory.add_turn([TextBlock(content="Parlami di Python")], ROLE.USER)
        response2 = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response2.text)], ROLE.ASSISTANT)

        print(f"Conversazione completata. Trace inviato a Zipkin su http://localhost:9411")

# Scegli quale esempio eseguire:
# esempio_otlp_completo()  # Per OTLP/Jaeger
esempio_zipkin_completo()  # Per Zipkin
```

<img width="3443" height="1603" alt="immagine" src="https://github.com/user-attachments/assets/50db17f8-d9bf-4285-bddb-9feaa329064a" />


## 5. Performance considerations

### Monitoring semplice per chatbot con Grafana

```python
import time
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from prometheus_client import start_http_server
from datapizzai import ClientFactory, Memory, TextBlock, ROLE

class SimpleChatbotMonitor:
    """Monitor semplice per chatbot con Grafana/Prometheus"""
    
    def __init__(self, service_name="chatbot"):
        # Configura OpenTelemetry
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0"
        })
        
        # Tracing (per Zipkin)
        tracer_provider = TracerProvider(resource=resource)
        zipkin_exporter = ZipkinExporter(endpoint="http://localhost:9411/api/v2/spans")
        tracer_provider.add_span_processor(BatchSpanProcessor(zipkin_exporter))
        trace.set_tracer_provider(tracer_provider)
        self.tracer = trace.get_tracer(__name__)
        
        # Metriche (per Prometheus/Grafana)
        prometheus_reader = PrometheusMetricReader()
        meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
        metrics.set_meter_provider(meter_provider)
        meter = metrics.get_meter(__name__)
        
        # Definisci metriche
        self.request_counter = meter.create_counter(
            "chatbot_requests_total",
            description="Numero totale di richieste al chatbot"
        )
        self.response_time = meter.create_histogram(
            "chatbot_response_time_seconds",
            description="Tempo di risposta del chatbot in secondi"
        )
        self.token_usage = meter.create_counter(
            "chatbot_tokens_total", 
            description="Numero totale di token utilizzati"
        )
        
        # Avvia server Prometheus
        start_http_server(8000)
        print("✅ Server Prometheus avviato su http://localhost:8000")
    
    def monitor_chat(self, user_message: str, client, memory=None):
        """Monitora una singola interazione di chat"""
        
        with self.tracer.start_as_current_span("chat_interaction") as span:
            start_time = time.time()
            
            try:
                # Aggiungi messaggio utente alla memoria
                if memory:
                    memory.add_turn([TextBlock(content=user_message)], ROLE.USER)
                
                # Chiamata al modello
                response = client.invoke(user_message, memory=memory)
                
                # Calcola durata
                duration = time.time() - start_time
                
                # Aggiungi risposta alla memoria
                if memory:
                    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
                
                # Registra metriche
                self.request_counter.add(1, {"status": "success"})
                self.response_time.record(duration)
                
                # Token usage (se disponibile)
                if hasattr(response, 'prompt_tokens_used'):
                    total_tokens = response.prompt_tokens_used + response.completion_tokens_used
                    self.token_usage.add(total_tokens)
                    span.set_attribute("tokens.prompt", response.prompt_tokens_used)
                    span.set_attribute("tokens.completion", response.completion_tokens_used)
                
                # Attributi span
                span.set_attribute("chat.user_message", user_message[:100])  # Primi 100 char
                span.set_attribute("chat.response_length", len(response.text))
                span.set_attribute("chat.duration_seconds", duration)
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return response
                
            except Exception as e:
                # Errore
                self.request_counter.add(1, {"status": "error"})
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

# Esempio pratico
def esempio_chatbot_con_monitoring():
    """Esempio completo di chatbot con monitoring"""
    
    # Inizializza monitor
    monitor = SimpleChatbotMonitor("mio-chatbot")
    
    # Inizializza client e memoria
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    memory = Memory()
    
    # Simula conversazione
    messaggi = [
        "Ciao, come stai?",
        "Parlami del machine learning",
        "Quali sono i vantaggi dell'AI?",
        "Come funziona un chatbot?",
        "Grazie, arrivederci!"
    ]
    
    print("🤖 Avvio conversazione con monitoring...")
    
    for i, messaggio in enumerate(messaggi, 1):
        print(f"\n👤 Utente: {messaggio}")
        
        try:
            response = monitor.monitor_chat(messaggio, client, memory)
            print(f"🤖 Bot: {response.text[:200]}...")
            
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        time.sleep(1)  # Pausa tra messaggi
    
    print("\n✅ Conversazione completata!")
    print("📊 Metriche disponibili su:")
    print("  - Prometheus: http://localhost:8000")
    print("  - Zipkin: http://localhost:9411")
    print("  - Grafana: http://localhost:3000 (se configurato)")

# Esegui esempio
esempio_chatbot_con_monitoring()
```

### Setup rapido per Grafana

#### 1. Avvia Prometheus e Grafana con Docker

```bash
# Crea directory per i dati
mkdir -p grafana-data prometheus-data

# Avvia Prometheus
docker run -d -p 9090:9090 \
  --name prometheus \
  -v $(pwd)/prometheus-data:/prometheus \
  prom/prometheus --config.file=/etc/prometheus/prometheus.yml

# Avvia Grafana
docker run -d -p 3000:3000 \
  --name grafana \
  -v $(pwd)/grafana-data:/var/lib/grafana \
  grafana/grafana
```

#### 2. Configura Prometheus per leggere le metriche

Crea file `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'chatbot-metrics'
    static_configs:
      - targets: ['host.docker.internal:8000']  # Per Docker Desktop
        # - targets: ['172.17.0.1:8000']        # Per Linux
```

#### 3. Dashboard Grafana per il chatbot

Una volta avviato Grafana (http://localhost:3000, user/pass: admin/admin):

1. **Aggiungi Data Source**: Prometheus → http://prometheus:9090
2. **Crea Dashboard** con questi pannelli:

```json
{
  "dashboard": {
    "title": "Chatbot Monitoring",
    "panels": [
      {
        "title": "Richieste Totali",
        "type": "stat",
        "targets": [{"expr": "chatbot_requests_total"}]
      },
      {
        "title": "Tempo di Risposta",
        "type": "graph", 
        "targets": [{"expr": "rate(chatbot_response_time_seconds_sum[5m]) / rate(chatbot_response_time_seconds_count[5m])"}]
      },
      {
        "title": "Token Utilizzati",
        "type": "graph",
        "targets": [{"expr": "rate(chatbot_tokens_total[5m])"}]
      }
    ]
  }
}
```

#### 4. Esecuzione completa

```bash
# 1. Avvia i servizi
docker run -d -p 9411:9411 openzipkin/zipkin        # Zipkin
docker run -d -p 9090:9090 prom/prometheus          # Prometheus  
docker run -d -p 3000:3000 grafana/grafana          # Grafana

# 2. Esegui il tuo chatbot con monitoring
python tuo_chatbot.py

# 3. Visualizza metriche
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Zipkin: http://localhost:9411
```

### Utilizzo pratico

#### File pronti all'uso:

1. **`simple_chatbot_monitor.py`** - Monitor completo per chatbot
2. **`prometheus.yml`** - Configurazione Prometheus  
3. **`start_monitoring.sh`** - Avvia tutto l'stack
4. **`stop_monitoring.sh`** - Ferma tutto l'stack

#### Avvio rapido:

```bash
# 1. Vai nella directory Monitoring
cd Monitoring/

# 2. Avvia lo stack di monitoring
./start_monitoring.sh

# 3. Configura API key
export OPENAI_API_KEY='your-key-here'

# 4. Avvia chatbot con monitoring
python simple_chatbot_monitor.py

# Oppure modalità automatica:
python simple_chatbot_monitor.py --auto
```

#### Accesso ai servizi:

- **Zipkin** (traces): http://localhost:9411
- **Prometheus** (metriche): http://localhost:9090  
- **Grafana** (dashboard): http://localhost:3000 (admin/admin)
- **Metriche chatbot**: http://localhost:8000

#### Metriche disponibili:

- `chatbot_requests_total` - Richieste totali (successo/errore)
- `chatbot_response_time_seconds` - Tempo di risposta
- `chatbot_tokens_total` - Token utilizzati
- `chatbot_errors_total` - Errori per tipo

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
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    
    # Simula traffico per dashboard
    for i in range(10):
        with tracer.trace(f"grafana_example_{i}") as trace:
            response = client.invoke([
                TextBlock(content=f"Messaggio numero {i+1}")
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
    model="gpt-4o",
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
    response = client.invoke([TextBlock(content=prompt)])
    
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
