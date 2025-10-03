# Guida al monitoraggio con datapizza-ai

## Panoramica

Questa guida illustra come implementare un sistema di monitoraggio completo utilizzando la libreria `datapizza-ai`. Il monitoraggio permette di tracciare le prestazioni, i token utilizzati e il comportamento dei client AI in tempo reale.

## Indice

- [1. Configurazione di base](#1-configurazione-di-base)
- [2. Tracciamento del client: input, output e memoria](#2-tracciamento-del-client-input-output-e-memoria)
- [3. Creazione manuale di span](#3-creazione-manuale-di-span)
- [4. Aggiungere esportatori esterni](#4-aggiungere-esportatori-esterni)
- [5. Configurazione del monitoraggio con Grafana](#5-configurazione-del-monitoraggio-con-grafana)

## 1. Configurazione di base

Per iniziare con il monitoraggio in datapizza-ai, è necessario configurare il sistema di tracciamento OpenTelemetry integrato.

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
Arrivati a questo punto può sembrare banale, ma come sembre iniziamo dalla configurazione del client.

```python
import os
from dotenv import load_dotenv
from opentelemetry import trace

load_dotenv()

from datapizza.clients.openai import OpenAIClient

# Inizializza il sistema di tracciamento
tracer = ContextTracing()

# Configura il client
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1
)
```

## 2. Tracciamento del client: input, output e memoria

Il tracciamento automatico dei client permette di monitorare tutte le interazioni con il modello scelto.

### Esempio base con tracciamento

```python
from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock


# Inizializza i componenti
tracer = ContextTracing()

client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
memory = Memory()

def esempio_tracciamento_base():
    """Esempio di tracciamento automatico di input e output"""
    
    with tracer.trace("chat_conversation") as trace:
        # Aggiunge il messaggio utente alla memoria
        memory.add_turn([TextBlock(content="Spiega cos'è il machine learning")], ROLE.USER)
        
        # Invoca il client: l'operazione viene tracciata automaticamente
        response = client.invoke("Spiega cos'è il machine learning", memory=memory)
        
        # Aggiunge la risposta alla memoria
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        
        print(f"Risposta: {response.text}")
        print(f"Token utilizzati: {response.prompt_tokens_used + response.completion_tokens_used}")        
        return response

# Esegue l'esempio
response = esempio_tracciamento_base()
```
```bash
╭───────────────────────────── Riepilogo traccia di chat_conversation ──────────────────────────────╮
│ Span totali: 2                                                                                    │
│ Durata: 17.97s                                                                                    │
│ Utilizzo token:                                                                                   │
│                ┏━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓             │
│                ┃ Modello ┃ Token prompt   ┃ Token completamento ┃ Token in cache    ┃             │
│                ┡━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩             │
│                │ gpt-5   │ 13             │ 912                 │ 0                 │             │
│                └─────────┴────────────────┴─────────────────────┴───────────────────┘             │
╰───────────────────────────────────────────────────────────────────────────────────────────────────╯
```
Come puoi vedere, la traccia mostra automaticamente:
    
 - Token utilizzati (prompt, completion, cached)
 - Durata dell'operazione
 - Numero di span generati

### Parametri della traccia

Più in dettaglio, il sistema di tracciamento cattura automaticamente:

- **prompt_tokens_used**: Token del prompt inviato
- **completion_tokens_used**: Token generati dal modello  
- **cached_tokens_used**: Token forniti dalla cache
- **model_name**: Nome del modello utilizzato
- **duration**: Durata dell'operazione in secondi

## 3. Creazione manuale di span

Per un controllo più granulare, è possibile creare span manuali per tracciare operazioni specifiche.

Vediamo ora con un esempio come definire varie tipologie di span e qual è il loro output.

```python

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
            span.set_attribute("model_name", "gpt-5")
        
        # Span per operazioni di strumenti
        with tool_span("elaborazione_dati") as span:
            span.set_attribute("operazione", "data_processing")
            
            # Simula l'elaborazione dei dati
            import time

from datapizza.type import TextBlock
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
╭──────────────────────────── Riepilogo traccia di operazione_complessa ────────────────────────────╮
│ Span totali: 5                                                                                    │
│ Durata: 11.5s                                                                                     │
│ Utilizzo token                                                                                    │
│                ┏━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓             │
│                ┃ Modello ┃ Token prompt   ┃ Token completamento ┃ Token in cache    ┃             │
│                ┡━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩             │
│                │ gpt-5   │ 10             │ 748                 │ 0                 │             │
│                └─────────┴────────────────┴─────────────────────┴───────────────────┘             │
╰───────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 4. Aggiungere esportatori esterni

Per integrare il monitoraggio con sistemi esterni, è possibile configurare delle funzioni personalizzate.

### 4.1. Creazione della risorsa
Per fare questo non serve usare la libreria datapizza-ai, ma basta il modo standard che probabilmente hai già visto in passato.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

def setup_risorsa_monitoraggio():
    """Configura la risorsa OpenTelemetry (compatibile con datapizza-ai)"""
    
    # Ottiene il tracer provider esistente o ne crea uno nuovo
    tracer_provider = trace.get_tracer_provider()
    
    # Se è un ProxyTracerProvider, ne configura uno nuovo
    from opentelemetry.trace import ProxyTracerProvider
    if isinstance(tracer_provider, ProxyTracerProvider):
        resource = Resource.create({
            SERVICE_NAME: "datapizza-ai-app",
            SERVICE_VERSION: "1.0.0",
            "ambiente": "produzione",
            "team": "ai-team"
        })
        
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
    
    return tracer_provider
```

### 4.2. Integrazione con Zipkin

Il setup di Zipkin si integra facilmente con `ContextTracing`. L'esportatore viene aggiunto al provider di tracce esistente.

```python
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from datapizza.clients.openai import OpenAIClient

from datapizza.type import TextBlock

def setup_esportatore_zipkin():
    """Configura l'esportatore Zipkin (compatibile con datapizza-ai)"""
    
    # IMPORTANTE: Inizializza ContextTracing PRIMA di configurare gli esportatori
    context_tracer = ContextTracing()
    
    # Ottiene il tracer provider configurato da datapizza-ai
    tracer_provider = trace.get_tracer_provider()
    
    # Configura l'esportatore Zipkin
    zipkin_exporter = ZipkinExporter(
        endpoint="http://localhost:9411/api/v2/spans",
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
        client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
        
        response = client.invoke([
            TextBlock(content="Crea un riassunto di 50 parole")
        ])
        
        print(f"Risposta inviata a Zipkin: {response.text[:100]}...")
        print("🎯 Controlla Zipkin su http://localhost:9411")

# Esegue l'esempio
# esempio_zipkin()
```

<img width="3443" height="1255" alt="immagine" src="https://github.com/user-attachments/assets/99d01347-1069-40dd-a529-feb741ebbd5b" />

## 5. Configurazione del monitoraggio con Grafana

> **💡 Nota per notebook Jupyter**: Se hai usato il codice finora in jupyter notebook, dovrai riavviare il kernel ogni volta che fai il setup di prometheus in questa cella. 

```python
import os
from dotenv import load_dotenv
load_dotenv()

from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock

# Oppure, se preferisci il codice inline, ecco la versione semplificata:
import time
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.trace import ProxyTracerProvider
from prometheus_client import Counter, Histogram, start_http_server

_ZIPKIN_ATTACHED = False  # evita duplicazioni in notebook


class SimpleChatbotMonitor:
    """Monitoraggio semplice per chatbot con Grafana/Prometheus"""
    
    def __init__(self, service_name="chatbot"):
        # Tracciamento (Zipkin) senza sovrascrivere provider già impostati
        current_tp = trace.get_tracer_provider()
        if isinstance(current_tp, ProxyTracerProvider):
            trace.set_tracer_provider(TracerProvider())
            current_tp = trace.get_tracer_provider()

        # Verifica se Zipkin è disponibile prima di configurarlo
        zipkin_available = False
        try:
            import requests
            response = requests.get("http://localhost:9411/api/v2/services", timeout=2)
            zipkin_available = response.status_code == 200
        except:
            print("⚠️  Zipkin non raggiungibile. Avvia con: docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin")

        global _ZIPKIN_ATTACHED
        if zipkin_available and not _ZIPKIN_ATTACHED:
            zipkin_exporter = ZipkinExporter(endpoint="http://localhost:9411/api/v2/spans")
            current_tp.add_span_processor(BatchSpanProcessor(zipkin_exporter))
            _ZIPKIN_ATTACHED = True
            print("✅ Zipkin configurato")
        
        self.tracer = trace.get_tracer(__name__)

        # Metriche (Prometheus client diretto: nessun MeterProvider da impostare)
        self.request_counter = Counter(
            "chatbot_requests_total",
            "Numero totale di richieste al chatbot",
            ["status"],
        )
        self.response_time = Histogram(
            "chatbot_response_time_seconds",
            "Tempo di risposta del chatbot in secondi",
        )
        self.token_usage = Counter(
            "chatbot_tokens_total",
            "Numero totale di token utilizzati",
            ["type"],
        )

        # Avvia server Prometheus (idempotente)
        try:
            start_http_server(8000)
            print("✅ Server Prometheus avviato su http://localhost:8000")
        except OSError:
            print("⚠️  Porta 8000 già in uso: uso il server Prometheus esistente")
    
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
                self.request_counter.labels(status="success").inc()
                self.response_time.observe(duration)
                
                # Utilizzo token (se disponibile)
                if hasattr(response, 'prompt_tokens_used'):
                    self.token_usage.labels(type="prompt").inc(response.prompt_tokens_used)
                    self.token_usage.labels(type="completion").inc(response.completion_tokens_used)
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
                self.request_counter.labels(status="error").inc()
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

# Esempio pratico
def esempio_chatbot_con_monitoraggio():
    """Esempio completo di chatbot con monitoraggio"""
    
    # Inizializza il monitor
    monitor = SimpleChatbotMonitor("mio-chatbot")
    
    # Inizializza client e memoria
    client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
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

**💡 Note per l'uso in notebook Jupyter:**
1. **Zipkin opzionale**: Se non è in esecuzione, il monitoring continua solo con Prometheus 
2. **Per avviare Zipkin**: `docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin`
3. **Usa il file ottimizzato**: `from simple_chatbot_monitor import SimpleChatbotMonitor` (consigliato)

### Configurazione rapida di Prometheus e Grafana

Vediamo come avviare il docker di Prometheus e Grafana. Anche questo è stato fatto in modo standard.

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

1.  **Aggiungi Data Source**: Prometheus → http://172.17.0.1:9090/
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

Sono disponibili le seguenti metriche, visualizzabili su Grafana

- `chatbot_requests_total` - Richieste totali (successo/errore)
- `chatbot_response_time_seconds` - Tempo di risposta
- `chatbot_tokens_total` - Token utilizzati
- `chatbot_errors_total` - Errori per tipo

<img width="1862" height="800" alt="immagine" src="https://github.com/user-attachments/assets/544c5c3f-273b-4379-abda-a66097a07012" />

## Conclusioni

In questa guida abbiamo visto come usare il monitoraggio con la libreria datapizza-ai. Più in dettaglio abbiamo visto:

- **Tracciamento automatico** di tutte le interazioni con i modelli
- **Span personalizzati** per operazioni specifiche  
- **Integrazione con OpenTelemetry** e sistemi esterni
- **Monitoraggio delle prestazioni** in tempo reale
- **Dashboard Grafana** per una visualizzazione avanzata

Il monitoraggio è essenziale per:
- Ottimizzare l'utilizzo dei token
- Identificare colli di bottiglia
- Monitorare i costi operativi
