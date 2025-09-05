# Guida al monitoraggio con datapizzai

## Panoramica

Questa guida illustra come implementare un sistema di monitoraggio completo utilizzando la libreria `datapizzai`. Il monitoraggio permette di tracciare le prestazioni, i token utilizzati e il comportamento dei client AI in tempo reale.

## Indice

- [1. Configurazione di base](#1-configurazione-di-base)
- [2. Tracciamento del client: input, output e memoria](#2-tracciamento-del-client-input-output-e-memoria)
- [3. Creazione manuale di span](#3-creazione-manuale-di-span)
- [4. Aggiungere esportatori esterni](#4-aggiungere-esportatori-esterni)
- [5. Considerazioni sulle prestazioni](#5-considerazioni-sulle-prestazioni)
- [6. Configurazione del monitoraggio con Grafana](#6-configurazione-del-monitoraggio-con-grafana)

## 1. Configurazione di base

Per iniziare con il monitoraggio in datapizzai, è necessario configurare il sistema di tracciamento OpenTelemetry integrato.

### Installazione delle dipendenze

```bash
# Pacchetti richiesti
pip install opentelemetry-api opentelemetry-sdk \
  opentelemetry-exporter-zipkin opentelemetry-exporter-otlp \
  opentelemetry-exporter-prometheus prometheus-client

# Se il registry privato non contiene alcuni pacchetti, installa da PyPI:
python -m pip install --index-url https://pypi.org/simple/ opentelemetry-exporter-prometheus prometheus-client
```

### Configurazione iniziale

```python
import os
from dotenv import load_dotenv
from opentelemetry import trace
from datapizzai.clients import ClientFactory
from datapizzai.tracing import ContextTracing

load_dotenv()

# Inizializza il sistema di tracciamento
tracer = ContextTracing()

# Configura il client
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1
)
```

## 2. Tracciamento del client: input, output e memoria

Il tracciamento automatico dei client permette di monitorare tutte le interazioni con i modelli di intelligenza artificiale.

### Esempio base con tracciamento

```python
from datapizzai.tracing import ContextTracing
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

# Inizializza i componenti
tracer = ContextTracing()
client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4")
memory = Memory()

def esempio_tracciamento_base():
    """Esempio di tracciamento automatico di input e output"""
    
    with tracer.trace("chat_conversation") as trace:
        # Aggiunge il messaggio utente alla memoria
        memory.add_turn([TextBlock(content="Spiega cos'è il machine learning")], ROLE.USER)
        
        # Invoca il client: l'operazione viene tracciata automaticamente
        response = client.invoke("", memory=memory)
        
        # Aggiunge la risposta alla memoria
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        
        print(f"Risposta: {response.text}")
        print(f"Token utilizzati: {response.prompt_tokens_used + response.completion_tokens_used}")
        
        # La traccia mostra automaticamente:
        # - Token utilizzati (prompt, completion, cached)
        # - Durata dell'operazione
        # - Numero di span generati
        
        return response

# Esegue l'esempio
response = esempio_tracciamento_base()
```
```bash
╭────────────────────────────────────── Riepilogo traccia di chat_conversation ───────────────────────────────────────╮
│ Span totali: 2                                                                                                      │
│ Durata: 17.97s                                                                                                      │
│                          Utilizzo token                                                                               │
│ ┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓                                                       │
│ ┃ Modello ┃ Token prompt ┃ Token completamento ┃ Token in cache ┃                                                  │
│ ┡━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩                                                       │
│ │ gpt-5 │ 13            │ 912               │ 0             │                                                       │
│ └───────┴───────────────┴───────────────────┴───────────────┘                                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Parametri della traccia

Il sistema di tracciamento cattura automaticamente:

- **prompt_tokens_used**: Token del prompt inviato
- **completion_tokens_used**: Token generati dal modello  
- **cached_tokens_used**: Token forniti dalla cache
- **model_name**: Nome del modello utilizzato
- **duration**: Durata dell'operazione in secondi

## 3. Creazione manuale di span

Per un controllo più granulare, è possibile creare span manuali per tracciare operazioni specifiche.

### Tipi di span disponibili

```python
from datapizzai.tracing.tracing import generation_span, agent_span, tool_span

def esempio_span_manuali():
    """Esempio di creazione manuale di span"""
    
    with tracer.trace("operazione_complessa") as trace:
        
        # Span per la generazione di contenuto
        with generation_span("generazione_testo") as span:
            span.set_attribute("parametro_custom", "valore")
            span.set_attribute("lunghezza_input", 150)
            
            response = client.invoke([
                TextBlock(content="Scrivi una poesia")
            ])
            
            span.set_attribute("lunghezza_output", len(response.text))
            span.set_attribute("model_name", "gpt-4")
        
        # Span per operazioni di strumenti
        with tool_span("elaborazione_dati") as span:
            span.set_attribute("operazione", "data_processing")
            
            # Simula l'elaborazione dei dati
            import time
            time.sleep(0.5)
            
            processed_data = {"stato": "completato", "record": 100}
            span.set_attribute("record_processati", processed_data["record"])
        
        # Span per agenti
        with agent_span("agente_decisionale") as span:
            span.set_attribute("tipo_agente", "decision_maker")
            
            decisione = "continua" if len(response.text) > 50 else "ferma"
            span.set_attribute("decisione", decisione)
    
    return response

# Esegue l'esempio
result = esempio_span_manuali()
```

```bash
╭───────────────────────────────────── Riepilogo traccia di operazione_complessa ─────────────────────────────────────╮
│ Span totali: 5                                                                                                      │
│ Durata: 11.5s                                                                                                       │
│                          Utilizzo token                                                                               │
│ ┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓                                                      │
│ ┃ Modello ┃ Token prompt ┃ Token completamento ┃ Token in cache ┃                                                     │
│ ┡━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩                                                     │
│ │ gpt-5 │ 10            │ 748               │ 0             │                                                      │
│ └───────┴───────────────┴───────────────────┴───────────────┘                                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
### Attributi personalizzati

```python
def esempio_attributi_personalizzati():
    """Esempio di attributi personalizzati negli span"""
    
    with tracer.trace("analisi_sentiment_padre") as trace:
        with generation_span("analisi_sentiment_figlio") as span:
            span.set_attribute("model_name", client.model_name)  # es. "gpt-4o"
            
            # Attributi per l'input
            span.set_attribute("tipo_input", "testo")
            span.set_attribute("lingua", "italiano")
            span.set_attribute("lunghezza_testo", 250)
            
            # Invoca il modello per l'analisi del sentiment
            prompt = "Analizza il sentiment di questo testo: 'Oggi è una giornata fantastica!'"
            response = client.invoke([TextBlock(content=prompt)])
            
            # Attributi per l'output
            span.set_attribute("sentiment_rilevato", "positivo")
            span.set_attribute("punteggio_confidenza", 0.95)
            span.set_attribute("token_risposta", response.completion_tokens_used)
            
    return response
```
```bash
╭────────────────────────────────── Riepilogo traccia di analisi_sentiment_padre ───────────────────────────────────╮
│ Span totali: 3                                                                                                      │
│ Durata: 8.86s                                                                                                       │
│                          Utilizzo token                                                                               │
│ ┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓                                                      │
│ ┃ Modello ┃ Token prompt ┃ Token completamento ┃ Token in cache ┃                                                     │
│ ┡━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩                                                     │
│ │ gpt-5 │ 23            │ 400               │ 0             │                                                      │
│ └───────┴───────────────┴───────────────────┴───────────────┘                                                      │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
## 4. Aggiungere esportatori esterni

Per integrare il monitoraggio con sistemi esterni, è possibile configurare esportatori personalizzati.

### 4.1. Creazione della risorsa

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

def setup_risorsa_monitoraggio():
    """Configura la risorsa OpenTelemetry (compatibile con datapizzai)"""
    
    # Ottiene il tracer provider esistente o ne crea uno nuovo
    tracer_provider = trace.get_tracer_provider()
    
    # Se è un ProxyTracerProvider, ne configura uno nuovo
    from opentelemetry.trace import ProxyTracerProvider
    if isinstance(tracer_provider, ProxyTracerProvider):
        resource = Resource.create({
            SERVICE_NAME: "datapizzai-app",
            SERVICE_VERSION: "1.0.0",
            "ambiente": "produzione",
            "team": "ai-team"
        })
        
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider
```

### 4.2. Integrazione con Zipkin

```python
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_esportatore_zipkin():
    """Configura l'esportatore Zipkin (compatibile con datapizzai)"""
    
    # IMPORTANTE: Inizializza ContextTracing PRIMA di configurare gli esportatori
    context_tracer = ContextTracing()
    
    # Ottiene il tracer provider configurato da datapizzai
    tracer_provider = trace.get_tracer_provider()
    
    # Configura l'esportatore Zipkin
    zipkin_exporter = ZipkinExporter(
        endpoint="http://localhost:9411/api/v2/spans",
        local_node_ipv4="127.0.0.1",
        local_node_ipv6="::1",
        local_node_port=5000,
    )
    
    # Aggiunge il processore di span
    span_processor = BatchSpanProcessor(zipkin_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    print("✅ Esportatore Zipkin configurato")
    return context_tracer

# Esempio di utilizzo con Zipkin
def esempio_zipkin():
    """Esempio con esportazione verso Zipkin"""
    
    # PRIMA: Avvia Zipkin con Docker
    # docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin
    
    tracer = setup_esportatore_zipkin()  # Restituisce il ContextTracing configurato
    
    with tracer.trace("zipkin_example") as trace:
        client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
        
        response = client.invoke([
            TextBlock(content="Crea un riassunto di 50 parole")
        ])
        
        print(f"Risposta inviata a Zipkin: {response.text[:100]}...")
        print("🎯 Controlla Zipkin su http://localhost:9411")

# Esegue l'esempio
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

def setup_esportatore_otlp():
    """Configura l'esportatore OTLP (gRPC) per Jaeger/Collector"""
    
    tracer_provider = setup_risorsa_monitoraggio()
    
    # NOTE importanti per gRPC OTLP:
    # - NIENTE prefisso http:// nell'endpoint (usa host:porta)
    # - Usa insecure=True se il backend non ha TLS
    # - Le chiavi degli header devono essere lowercase (es. "authorization")
    otlp_exporter = OTLPSpanExporter(
        endpoint="localhost:4317",
        insecure=True,
        # headers=(("authorization", f"Bearer {os.getenv('OTLP_TOKEN','')}"),),  # opzionale
    )
    
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    print("✅ Esportatore OTLP configurato (gRPC → localhost:4317)")
    return tracer_provider
```
### Backend OTLP consigliato (Jaeger all-in-one)

Avvia Jaeger con supporto OTLP gRPC e interfaccia web:

```bash
docker run -d --name jaeger \
  -p 4317:4317 -p 16686:16686 \
  jaegertracing/all-in-one:1.57
```

- Tracce via OTLP gRPC: `localhost:4317`
- UI Jaeger: http://localhost:16686

Nota: Zipkin non riceve OTLP gRPC su 4317. Per Zipkin, usa lo `ZipkinExporter` oppure un OpenTelemetry Collector come bridge (OTLP → Zipkin).
"""

def setup_esportatore_zipkin():
    """Configura l'esportatore Zipkin"""
    
    tracer_provider = setup_risorsa_monitoraggio()
    
    zipkin_exporter = ZipkinExporter(
        endpoint="http://localhost:9411/api/v2/spans"
    )
    
    span_processor = BatchSpanProcessor(zipkin_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    print("✅ Esportatore Zipkin configurato")
    return tracer_provider

### Esempio completo con OTLP
def esempio_otlp_completo():
    """Esempio completo con esportazione OTLP"""
    
    setup_esportatore_otlp()
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

        
        print(f"Conversazione completata. Traccia inviata via OTLP.")

### Esempio completo con Zipkin
def esempio_zipkin_completo():
    """Esempio completo con esportazione Zipkin"""
    
    setup_esportatore_zipkin()
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

        print(f"Conversazione completata. Traccia inviata a Zipkin su http://localhost:9411")

# Scegli quale esempio eseguire:
# esempio_otlp_completo()  # Per OTLP → Jaeger (porta 4317)
esempio_zipkin_completo()  # Per Zipkin
```

<img width="3443" height="1603" alt="immagine" src="https://github.com/user-attachments/assets/50db17f8-d9bf-4285-bddb-9feaa329064a" />


## 5. Considerazioni sulle prestazioni

### Monitoraggio semplice per chatbot con Grafana

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
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE
from datapizzai.tracing import ContextTracing

class SimpleChatbotMonitor:
    """Monitoraggio semplice per chatbot con Grafana/Prometheus"""
    
    def __init__(self, service_name="chatbot"):
        # Configura OpenTelemetry
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0"
        })
        
        # Tracciamento (per Zipkin)
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
                # Aggiunge il messaggio utente alla memoria
                if memory:
                    memory.add_turn([TextBlock(content=user_message)], ROLE.USER)
                
                # Chiamata al modello
                response = client.invoke(user_message, memory=memory)
                
                # Calcola la durata
                duration = time.time() - start_time
                
                # Aggiunge la risposta alla memoria
                if memory:
                    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
                
                # Registra le metriche
                self.request_counter.add(1, {"status": "success"})
                self.response_time.record(duration)
                
                # Utilizzo token (se disponibile)
                if hasattr(response, 'prompt_tokens_used'):
                    total_tokens = response.prompt_tokens_used + response.completion_tokens_used
                    self.token_usage.add(total_tokens)
                    span.set_attribute("tokens.prompt", response.prompt_tokens_used)
                    span.set_attribute("tokens.completion", response.completion_tokens_used)
                
                # Attributi dello span
                span.set_attribute("chat.user_message", user_message[:100])  # Primi 100 caratteri
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
def esempio_chatbot_con_monitoraggio():
    """Esempio completo di chatbot con monitoraggio"""
    
    # Inizializza il monitor
    monitor = SimpleChatbotMonitor("mio-chatbot")
    
    # Inizializza client e memoria
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    memory = Memory()
    
    # Simula una conversazione
    messaggi = [
        "Ciao, come stai?",
        "Parlami del machine learning",
        "Quali sono i vantaggi dell'AI?",
        "Come funziona un chatbot?",
        "Grazie, arrivederci!"
    ]
    
    print("🤖 Avvio conversazione con monitoraggio...")
    
    for i, messaggio in enumerate(messaggi, 1):
        print(f"\n👤 Utente: {messaggio}")
        
        try:
            response = monitor.monitor_chat(messaggio, client, memory)
            print(f"🤖 Bot: {response.text[:200]}...")
            
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        time.sleep(1)  # Pausa tra i messaggi
    
    print("\n✅ Conversazione completata!")
    print("📊 Metriche disponibili su:")
    print("  - Prometheus: http://localhost:8000")
    print("  - Zipkin: http://localhost:9411")
    print("  - Grafana: http://localhost:3000 (se configurato)")

# Esegui l'esempio
esempio_chatbot_con_monitoraggio()
```

### Configurazione rapida per Grafana

#### 1. Avvia Prometheus e Grafana con Docker

```bash
# Crea le directory per i dati
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

Crea il file `prometheus.yml`:

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

1.  **Aggiungi Data Source**: Prometheus → http://prometheus:9090
2.  **Crea una Dashboard** con questi pannelli:

```json
{
  "dashboard": {
    "title": "Monitoraggio Chatbot",
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

# 2. Esegui il tuo chatbot con monitoraggio
python tuo_chatbot.py

# 3. Visualizza le metriche
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
# - Zipkin: http://localhost:9411
```

### Utilizzo pratico

#### File pronti all'uso:

1.  **`simple_chatbot_monitor.py`** - Monitor completo per chatbot
2.  **`prometheus.yml`** - Configurazione Prometheus  
3.  **`start_monitoring.sh`** - Avvia tutto lo stack
4.  **`stop_monitoring.sh`** - Ferma tutto lo stack

#### Avvio rapido:

```bash
# 1. Vai nella directory Monitoring
cd Monitoring/

# 2. Avvia lo stack di monitoraggio
./start_monitoring.sh

# 3. Configura la chiave API
export OPENAI_API_KEY='your-key-here'

# 4. Avvia il chatbot con monitoraggio
python simple_chatbot_monitor.py

# Oppure in modalità automatica:
python simple_chatbot_monitor.py --auto
```

#### Accesso ai servizi:

- **Zipkin** (tracce): http://localhost:9411
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
    """Configurazione ottimizzata per produzione"""
    
    # Elaborazione in batch per ridurre l'overhead
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    
    tracer_provider = setup_risorsa_monitoraggio()
    
    # Configura il processore batch ottimizzato
    batch_processor = BatchSpanProcessor(
        span_exporter=otlp_exporter,
        max_queue_size=2048,        # Coda più grande
        export_timeout_millis=30000, # Timeout più lungo
        schedule_delay_millis=5000,  # Ritardo ottimizzato
        max_export_batch_size=512    # Dimensione batch ottimizzata
    )
    
    tracer_provider.add_span_processor(batch_processor)
    
    print("✅ Configurazione ottimizzata applicata")
```

## 6. Configurazione del monitoraggio con Grafana

### 6.1 Datasource Prometheus (fix errore porta 8000)

Se in Grafana vedi l'errore:

Post "http://localhost:8000/api/v1/query": connect: connection refused

significa che la datasource punta all'endpoint di metriche dell'applicazione (porta 8000) invece che all'API di Prometheus (porta 9090). Correggi così:

- URL corretta della datasource Prometheus:
  - Host locale: `http://localhost:9090`
  - Stesso network Docker: `http://prometheus:9090`
  - Grafana in container, Prometheus su host:
    - Mac/Windows: `http://host.docker.internal:9090`
    - Linux: `http://172.17.0.1:9090`

Esempio provisioning Grafana per Prometheus (`grafana/provisioning/datasources/prometheus.yml`):

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

Esegui Prometheus con una config minima che scrapi la tua app su `:8000`:

```yaml
# Monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'datapizzai-app'
    static_configs:
      # Scegli UN solo target a seconda dello scenario:
      # - Se Prometheus gira sullo stesso host dell'app:
      # - targets: ['localhost:8000']
      # - Se Prometheus è in Docker e l'app è sull'host (Linux):
      # - targets: ['172.17.0.1:8000']
      # - Se Prometheus è in Docker e l'app è sull'host (Mac/Win):
      # - targets: ['host.docker.internal:8000']
      # - Se sia Prometheus che l'app sono nello stesso network Docker (nome servizio "app"):
      # - targets: ['app:8000']
      targets: ['localhost:8000']
```

Esegui Prometheus (host o Docker):

```bash
docker run -d --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/Monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest

# Verifica
curl -s http://localhost:9090/-/ready  # atteso: OK
```

Poi in Grafana imposta/aggiorna la datasource Prometheus con la URL corretta (vedi sopra).

### 6.2 Impostazione di Grafana + Tempo

```yaml
# docker-compose.yml per lo stack Grafana
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

### Configurazione di Tempo

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
def setup_dashboard_grafana():
    """Configura la dashboard Grafana per datapizzai"""
    
    dashboard_config = {
        "dashboard": {
            "title": "Monitoraggio DatapizzAI",
            "panels": [
                {
                    "title": "Utilizzo Token nel Tempo",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "rate(datapizzai_tokens_total[5m])",
                            "legendFormat": "{{model_name}}"
                        }
                    ]
                },
                {
                    "title": "Distribuzione Tempo di Risposta", 
                    "type": "histogram",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, datapizzai_duration_seconds)",
                            "legendFormat": "95 percentile"
                        }
                    ]
                },
                {
                    "title": "Tasso di Riscontri in Cache",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "datapizzai_cache_hits / datapizzai_total_requests",
                            "legendFormat": "Tasso di Riscontri in Cache"
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
    """Esempio completo con monitoraggio Grafana"""
    
    # Configura OTLP per Tempo
    setup_esportatore_otlp()
    
    # Configura la dashboard
    setup_dashboard_grafana()
    
    tracer = ContextTracing()
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    
    # Simula traffico per la dashboard
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
Esempio completo di monitoraggio con datapizzai.
Dimostra l'integrazione tra ContextTracing e span manuali di OpenTelemetry.
"""

import os
import time
from dotenv import load_dotenv
from opentelemetry import trace
from datapizzai.clients import ClientFactory
from datapizzai.tracing import ContextTracing
from datapizzai.type import TextBlock, ROLE

load_dotenv()

# Inizializza il sistema di tracciamento
context_tracer = ContextTracing()

# Configura il client
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7
)

# Tracer OpenTelemetry per span manuali
tracer = trace.get_tracer(__name__)

def recupera_da_database():
    """Simula il recupero di dati dal database"""
    print("📊 Recupero dati dal database...")
    time.sleep(0.3)  # Simula latenza del database
    
    # Dati di esempio per una richiesta di analisi
    data = {
        "user_id": "USR-001",
        "tipo_richiesta": "analisi",
        "contenuto": "Analizza le prestazioni del nostro sistema di monitoraggio",
        "priorita": "alta",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    
    print(f"✅ Dati recuperati: {data['tipo_richiesta']} per utente {data['user_id']}")
    return data

def valida_dati(data):
    """Valida i dati recuperati"""
    print("🔍 Validazione dati in corso...")
    time.sleep(0.1)  # Simula tempo di validazione
    
    # Controlli di validazione
    if not data:
        raise ValueError("Dati vuoti")
    
    campi_richiesti = ["user_id", "tipo_richiesta", "contenuto"]
    campi_mancanti = [field for field in campi_richiesti if field not in data]
    
    if campi_mancanti:
        raise ValueError(f"Campi mancanti: {campi_mancanti}")
    
    if len(data.get("contenuto", "")) < 10:
        raise ValueError("Contenuto troppo breve")
    
    print("✅ Validazione completata con successo")
    return True

def elabora_regole_di_business(data):
    """Elabora la logica di business con chiamata AI"""
    print("🤖 Elaborazione logica di business...")
    
    # Costruisce il prompt basato sui dati
    prompt = f"""
    Analizza la seguente richiesta di {data['user_id']}:
    Tipo: {data['tipo_richiesta']}
    Contenuto: {data['contenuto']}
    Priorità: {data['priorita']}
    
    Fornisci un'analisi dettagliata e raccomandazioni pratiche.
    """
    
    # Chiamata al client AI (tracciata automaticamente da ContextTracing)
    response = client.invoke([TextBlock(content=prompt)])
    
    # Elabora il risultato
    result = {
        "user_id": data["user_id"],
        "analisi": response.text,
        "token_utilizzati": response.completion_tokens_used,
        "tempo_elaborazione": time.time(),
        "stato": "completato"
    }
    
    print(f"✅ Elaborazione completata - {result['token_utilizzati']} token utilizzati")
    return result

def main():
    """Esempio completo con ContextTracing e span manuali"""
    print("🚀 Avvio esempio di monitoraggio completo")
    
    with context_tracer.trace("flusso_di_lavoro_business_completo") as trace:
        
        # Span manuale per operazione su database
        with tracer.start_as_current_span("query_database") as db_span:
            # Attributi per lo span del database
            db_span.set_attribute("db.system", "postgresql")
            db_span.set_attribute("db.operation", "select")
            
            # Operazione su database
            data = recupera_da_database()
            
            db_span.set_attribute("db.record_recuperati", 1)
            db_span.set_attribute("user.id", data["user_id"])

        # Span manuale per validazione
        with tracer.start_as_current_span("validazione_dati") as validation_span:
            validation_span.set_attribute("validation.type", "regole_di_business")
            
            # Logica di validazione
            try:
                valida_dati(data)
                validation_span.set_attribute("validation.success", True)
            except ValueError as e:
                validation_span.set_attribute("validation.success", False)
                validation_span.set_attribute("validation.error", str(e))
                raise

        # Span manuale per logica di business
        with tracer.start_as_current_span("logica_di_business") as business_span:
            business_span.set_attribute("business.operation", "analisi_ai")
            business_span.set_attribute("business.priority", data["priorita"])
            
            # Logica di business principale (include chiamata AI tracciata automaticamente)
            result = elabora_regole_di_business(data)
            
            business_span.set_attribute("business.token_consumati", result["token_utilizzati"])
            business_span.set_attribute("business.status", result["stato"])
    
    print("\n🎯 Flusso di lavoro completato!")
    print("📊 La traccia mostra:")
    print("  - Span manuali per database, validazione e logica di business")
    print("  - Span automatici per le chiamate AI")
    print("  - Attributi personalizzati per ogni operazione")
    print("  - Utilizzo di token e metriche di prestazione")

if __name__ == "__main__":
    main()
```

**Spazio per screenshot: Output finale del tracciamento completo**

## Conclusioni

Il sistema di monitoraggio di datapizzai offre:

- **Tracciamento automatico** di tutte le interazioni con i modelli
- **Span personalizzati** per operazioni specifiche  
- **Integrazione con OpenTelemetry** e sistemi esterni
- **Monitoraggio delle prestazioni** in tempo reale
- **Dashboard Grafana** per una visualizzazione avanzata

Il monitoraggio è essenziale per:
- Ottimizzare l'utilizzo dei token
- Identificare colli di bottiglia
- Monitorare i costi operativi
- Garantire prestazioni stabili in produzione
