#!/usr/bin/env python3
"""
Monitor semplice per chatbot con Grafana/Prometheus/Zipkin
Esempio pratico e pronto all'uso per monitorare un chatbot DatapizzaAI
Usa solo le librerie già disponibili in datapizza
"""

import time
import os
from prometheus_client import Counter, Histogram, start_http_server
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry import trace
from opentelemetry.trace import ProxyTracerProvider

try:
    from datapizza.clients import ClientFactory
    from datapizza.memory import Memory
    from datapizza.type import TextBlock, ROLE
    from datapizza.tracing import ContextTracing
except ImportError as e:
    print(f"⚠️  Errore importazione datapizza: {e}")
    print("   Verifica che datapizza sia installato correttamente")
    exit(1)

# Sentinel globali per esecuzioni ripetute (es. notebook)
_TRACER_PROVIDER_SET = False
_ZIPKIN_SP_ATTACHED = False
_METRICS_PROVIDER_SET = False
_PROM_SERVER_STARTED = False


class SimpleChatbotMonitor:
    """Monitor semplice per chatbot con Grafana/Prometheus usando le librerie disponibili"""
    
    def __init__(self, service_name="chatbot", prometheus_port=8000, zipkin_url="http://localhost:9411/api/v2/spans"):
        print(f"🔧 Inizializzazione monitor per {service_name}...")
        
        # === TRACING (usando ContextTracing di datapizza) ===
        try:
            self.context_tracer = ContextTracing()
            print("✅ ContextTracing di datapizza configurato")
        except Exception as e:
            print(f"⚠️  ContextTracing non disponibile: {e}")
            self.context_tracer = None
        
        # === TRACING ZIPKIN (opzionale) ===
        try:
            # Prima verifica se Zipkin è raggiungibile
            import requests
            try:
                response = requests.get("http://localhost:9411/api/v2/services", timeout=2)
                zipkin_available = response.status_code == 200
            except:
                zipkin_available = False

            if zipkin_available:
                global _TRACER_PROVIDER_SET, _ZIPKIN_SP_ATTACHED

                current_tp = trace.get_tracer_provider()
                if not _TRACER_PROVIDER_SET:
                    # Sostituisci solo se è ancora il proxy di default
                    if isinstance(current_tp, ProxyTracerProvider):
                        tracer_provider = TracerProvider()
                        trace.set_tracer_provider(tracer_provider)
                    else:
                        tracer_provider = current_tp
                    _TRACER_PROVIDER_SET = True
                else:
                    tracer_provider = current_tp

                # Collega lo Zipkin exporter una sola volta
                if not _ZIPKIN_SP_ATTACHED:
                    zipkin_exporter = ZipkinExporter(endpoint=zipkin_url)
                    tracer_provider.add_span_processor(BatchSpanProcessor(zipkin_exporter))
                    _ZIPKIN_SP_ATTACHED = True
                    print(f"✅ Zipkin configurato: {zipkin_url}")

                self.zipkin_tracer = trace.get_tracer(__name__)
            else:
                print("⚠️  Zipkin non raggiungibile su localhost:9411. Tracciamento Zipkin disabilitato.")
                self.zipkin_tracer = None
        except Exception as e:
            print(f"⚠️  Zipkin non disponibile: {e}")
            self.zipkin_tracer = None
        
        # === METRICHE PROMETHEUS (usando prometheus_client direttamente) ===
        try:
            # Definisci metriche principali
            self.request_counter = Counter(
                'chatbot_requests_total',
                'Numero totale di richieste al chatbot',
                ['status']
            )
            self.response_time = Histogram(
                'chatbot_response_time_seconds',
                'Tempo di risposta del chatbot in secondi'
            )
            self.token_counter = Counter(
                'chatbot_tokens_total', 
                'Numero totale di token utilizzati',
                ['type']
            )
            self.error_counter = Counter(
                'chatbot_errors_total',
                'Numero totale di errori',
                ['error_type']
            )
            
            # Avvia server Prometheus solo se non già avviato
            global _PROM_SERVER_STARTED
            if not _PROM_SERVER_STARTED:
                try:
                    start_http_server(prometheus_port)
                    _PROM_SERVER_STARTED = True
                    print(f"✅ Server Prometheus avviato su http://localhost:{prometheus_port}")
                except OSError as e:
                    # Porta occupata: presumiamo che il server sia già attivo
                    print("⚠️  Prometheus già in esecuzione (porta in uso). Uso server esistente.")
            
        except Exception as e:
            print(f"❌ Errore configurazione Prometheus: {e}")
            raise
    
    def monitor_chat(self, user_message: str, client, memory=None):
        """Monitora una singola interazione di chat"""
        
        start_time = time.time()
        
        # Usa ContextTracing di datapizza se disponibile
        if self.context_tracer:
            with self.context_tracer.trace("chat_interaction") as trace_context:
                return self._execute_chat_with_monitoring(user_message, client, memory, start_time, trace_context)
        else:
            return self._execute_chat_with_monitoring(user_message, client, memory, start_time, None)
    
    def _execute_chat_with_monitoring(self, user_message: str, client, memory, start_time, trace_context):
        """Esegue la chat con monitoring completo"""
        
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
            
            # === REGISTRA METRICHE PROMETHEUS ===
            self.request_counter.labels(status="success").inc()
            self.response_time.observe(duration)
            
            # Token usage (se disponibile)
            if hasattr(response, 'prompt_tokens_used') and hasattr(response, 'completion_tokens_used'):
                self.token_counter.labels(type="prompt").inc(response.prompt_tokens_used)
                self.token_counter.labels(type="completion").inc(response.completion_tokens_used)
            
            # === ZIPKIN SPAN (opzionale) ===
            if self.zipkin_tracer:
                with self.zipkin_tracer.start_as_current_span("chat_zipkin") as span:
                    span.set_attribute("chat.user_message", user_message[:100])
                    span.set_attribute("chat.response_length", len(response.text))
                    span.set_attribute("chat.duration_seconds", duration)
                    if hasattr(response, 'prompt_tokens_used'):
                        span.set_attribute("tokens.prompt", response.prompt_tokens_used)
                        span.set_attribute("tokens.completion", response.completion_tokens_used)
            
            return response
            
        except Exception as e:
            # Registra errore
            self.request_counter.labels(status="error").inc()
            self.error_counter.labels(error_type=type(e).__name__).inc()
            
            print(f"❌ Errore durante chat: {e}")
            raise

def esempio_chatbot_interattivo():
    """Esempio interattivo di chatbot con monitoring"""
    
    print("🚀 Avvio chatbot con monitoring completo...\n")
    
    # Verifica API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY non trovata nelle variabili d'ambiente!")
        print("   Esporta la chiave con: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Suggerimento per Zipkin se non disponibile
    print("💡 Per abilitare il tracciamento Zipkin, avvia:")
    print("   docker run -d -p 9411:9411 --name zipkin openzipkin/zipkin")
    print("   Altrimenti il monitoring funzionerà solo con Prometheus.\n")
    
    try:
        # Inizializza monitor
        monitor = SimpleChatbotMonitor("mio-chatbot-interattivo")
        
        # Inizializza client e memoria
        client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
        memory = Memory()
        
        print("\n📊 Monitoring attivo su:")
        print("  - Prometheus metriche: http://localhost:8000")
        print("  - Zipkin traces: http://localhost:9411 (se configurato)")
        print("  - Grafana dashboard: http://localhost:3000 (se configurato)")
        print("  - ContextTracing: integrato in datapizza")
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
