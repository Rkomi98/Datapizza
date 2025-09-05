#!/usr/bin/env python3
"""
Monitor semplice per chatbot con Grafana/Prometheus/Zipkin
Esempio pratico e pronto all'uso per monitorare un chatbot DatapizzAI
"""

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

try:
    from datapizzai import ClientFactory, Memory, TextBlock, ROLE
except ImportError:
    print("⚠️  datapizzai non installato. Installa con: pip install datapizzai")
    exit(1)

class SimpleChatbotMonitor:
    """Monitor semplice per chatbot con Grafana/Prometheus"""
    
    def __init__(self, service_name="chatbot", prometheus_port=8000, zipkin_url="http://localhost:9411/api/v2/spans"):
        print(f"🔧 Inizializzazione monitor per {service_name}...")
        
        # Configura OpenTelemetry Resource
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
            ResourceAttributes.SERVICE_INSTANCE_ID: f"{service_name}-{int(time.time())}"
        })
        
        # === TRACING (per Zipkin) ===
        try:
            tracer_provider = TracerProvider(resource=resource)
            zipkin_exporter = ZipkinExporter(endpoint=zipkin_url)
            tracer_provider.add_span_processor(BatchSpanProcessor(zipkin_exporter))
            trace.set_tracer_provider(tracer_provider)
            self.tracer = trace.get_tracer(__name__)
            print(f"✅ Zipkin configurato: {zipkin_url}")
        except Exception as e:
            print(f"⚠️  Zipkin non disponibile: {e}")
            self.tracer = None
        
        # === METRICHE (per Prometheus/Grafana) ===
        try:
            prometheus_reader = PrometheusMetricReader()
            meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
            metrics.set_meter_provider(meter_provider)
            meter = metrics.get_meter(__name__)
            
            # Definisci metriche principali
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
            self.error_counter = meter.create_counter(
                "chatbot_errors_total",
                description="Numero totale di errori"
            )
            
            # Avvia server Prometheus
            start_http_server(prometheus_port)
            print(f"✅ Server Prometheus avviato su http://localhost:{prometheus_port}")
            
        except Exception as e:
            print(f"❌ Errore configurazione Prometheus: {e}")
            raise
    
    def monitor_chat(self, user_message: str, client, memory=None):
        """Monitora una singola interazione di chat"""
        
        # Usa span solo se tracer disponibile
        span_context = self.tracer.start_as_current_span("chat_interaction") if self.tracer else None
        
        try:
            with span_context if span_context else nullcontext():
                start_time = time.time()
                
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
                
                # === REGISTRA METRICHE ===
                self.request_counter.add(1, {"status": "success"})
                self.response_time.record(duration)
                
                # Token usage (se disponibile)
                total_tokens = 0
                if hasattr(response, 'prompt_tokens_used') and hasattr(response, 'completion_tokens_used'):
                    total_tokens = response.prompt_tokens_used + response.completion_tokens_used
                    self.token_usage.add(total_tokens)
                
                # === ATTRIBUTI SPAN (se disponibile) ===
                if span_context and self.tracer:
                    span = trace.get_current_span()
                    span.set_attribute("chat.user_message", user_message[:100])  # Primi 100 char
                    span.set_attribute("chat.response_length", len(response.text))
                    span.set_attribute("chat.duration_seconds", duration)
                    span.set_attribute("chat.tokens_total", total_tokens)
                    if hasattr(response, 'prompt_tokens_used'):
                        span.set_attribute("tokens.prompt", response.prompt_tokens_used)
                        span.set_attribute("tokens.completion", response.completion_tokens_used)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                
                return response
                
        except Exception as e:
            # Registra errore
            self.request_counter.add(1, {"status": "error"})
            self.error_counter.add(1, {"error_type": type(e).__name__})
            
            # Span error (se disponibile)
            if span_context and self.tracer:
                span = trace.get_current_span()
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
            
            print(f"❌ Errore durante chat: {e}")
            raise

# Context manager per quando tracer non è disponibile
class nullcontext:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

def esempio_chatbot_interattivo():
    """Esempio interattivo di chatbot con monitoring"""
    
    print("🚀 Avvio chatbot con monitoring completo...\n")
    
    # Verifica API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY non trovata nelle variabili d'ambiente!")
        print("   Esporta la chiave con: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Inizializza monitor
        monitor = SimpleChatbotMonitor("mio-chatbot-interattivo")
        
        # Inizializza client e memoria
        client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
        memory = Memory()
        
        print("\n📊 Monitoring attivo su:")
        print("  - Prometheus metriche: http://localhost:8000")
        print("  - Zipkin traces: http://localhost:9411")
        print("  - Grafana dashboard: http://localhost:3000 (se configurato)")
        print("\n💬 Chatbot pronto! Scrivi 'quit' per uscire.\n")
        
        message_count = 0
        
        while True:
            # Input utente
            user_input = input("👤 Tu: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Arrivederci!")
                break
            
            if not user_input:
                continue
            
            try:
                # Monitora la chiamata
                response = monitor.monitor_chat(user_input, client, memory)
                print(f"🤖 Bot: {response.text}\n")
                
                message_count += 1
                if message_count % 5 == 0:
                    print(f"📈 {message_count} messaggi processati. Controlla le metriche!")
                
            except Exception as e:
                print(f"❌ Errore: {e}\n")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Interruzione utente. Monitoring terminato.")
    
    except Exception as e:
        print(f"❌ Errore fatale: {e}")

def esempio_conversazione_automatica():
    """Esempio con conversazione automatica predefinita"""
    
    print("🤖 Esempio conversazione automatica con monitoring...\n")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY non trovata!")
        return
    
    # Inizializza monitor
    monitor = SimpleChatbotMonitor("chatbot-demo")
    
    # Inizializza client e memoria
    client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
    memory = Memory()
    
    # Messaggi di test
    messaggi = [
        "Ciao! Come stai oggi?",
        "Spiegami cos'è il machine learning in parole semplici",
        "Quali sono i vantaggi dell'intelligenza artificiale?",
        "Come funziona un chatbot come te?",
        "Grazie per le informazioni, arrivederci!"
    ]
    
    print("📊 Metriche disponibili su:")
    print("  - http://localhost:8000 (Prometheus)")
    print("  - http://localhost:9411 (Zipkin)")
    print("  - http://localhost:3000 (Grafana)\n")
    
    for i, messaggio in enumerate(messaggi, 1):
        print(f"👤 Utente: {messaggio}")
        
        try:
            response = monitor.monitor_chat(messaggio, client, memory)
            print(f"🤖 Bot: {response.text[:200]}{'...' if len(response.text) > 200 else ''}\n")
            
            time.sleep(2)  # Pausa tra messaggi
            
        except Exception as e:
            print(f"❌ Errore: {e}\n")
    
    print("✅ Conversazione completata! Controlla le metriche sui link sopra.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        esempio_conversazione_automatica()
    else:
        esempio_chatbot_interattivo()
