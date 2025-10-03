#!/usr/bin/env python3
"""
Esempio di monitoring datapizza - VERSIONE CORRETTA
==================================================

Questo esempio risolve il problema "Overriding of current TracerProvider is not allowed"
e mostra come integrare correttamente datapizza con esportatori esterni.

PRIMA DI ESEGUIRE:
1. Avvia i servizi Docker:
   cd Monitoring/
   docker-compose up -d

2. Verifica che siano attivi:
   curl http://localhost:9411/health
   curl http://localhost:3000/health

3. Configura le API keys nel file .env
"""

import os
import time
from dotenv import load_dotenv

# Import OpenTelemetry PRIMA di datapizza (importante!)
from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Import datapizza DOPO OpenTelemetry
from datapizza.clients import ClientFactory
from datapizza.tracing import ContextTracing
from datapizza.type import TextBlock, ROLE

load_dotenv()


class DatapizzaAiMonitoringManager:
    """Manager per configurare monitoring con datapizza senza conflitti"""
    
    def __init__(self):
        self.context_tracer = None
        self.tracer_provider = None
        self.exporters_configured = False
    
    def setup_monitoring(self, enable_zipkin=True, enable_otlp=True):
        """
        Configura il monitoring in modo compatibile con datapizza
        
        IMPORTANTE: L'ordine delle operazioni è critico!
        """
        print("🔧 Configurazione monitoring datapizza...")
        
        # STEP 1: Inizializza ContextTracing (questo configura il TracerProvider)
        print("  1. Inizializzazione ContextTracing...")
        self.context_tracer = ContextTracing()
        
        # STEP 2: Ottieni il TracerProvider configurato da datapizza
        print("  2. Recupero TracerProvider...")
        self.tracer_provider = trace.get_tracer_provider()
        
        # STEP 3: Configura esportatori DOPO l'inizializzazione
        if enable_zipkin:
            self._setup_zipkin()
        
        if enable_otlp:
            self._setup_otlp()
        
        self.exporters_configured = True
        print("✅ Monitoring configurato correttamente!")
        return self.context_tracer
    
    def _setup_zipkin(self):
        """Configura esportatore Zipkin"""
        try:
            zipkin_exporter = ZipkinExporter(
                endpoint="http://localhost:9411/api/v2/spans",
                local_node_ipv4="127.0.0.1",
                local_node_ipv6="::1",
                local_node_port=5000,
            )
            
            zipkin_processor = BatchSpanProcessor(zipkin_exporter)
            self.tracer_provider.add_span_processor(zipkin_processor)
            print("  ✅ Zipkin exporter configurato")
            
        except Exception as e:
            print(f"  ⚠️ Zipkin non disponibile: {e}")
    
    def _setup_otlp(self):
        """Configura esportatore OTLP per Grafana/Tempo"""
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint="http://localhost:4317",
                insecure=True
            )
            
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(otlp_processor)
            print("  ✅ OTLP exporter configurato")
            
        except Exception as e:
            print(f"  ⚠️ OTLP non disponibile: {e}")


def test_basic_monitoring():
    """Test base del monitoring"""
    print("\n🧪 Test 1: Monitoring base")
    
    # Setup monitoring
    manager = DatapizzaAiMonitoringManager()
    tracer = manager.setup_monitoring()
    
    # Setup client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY non trovata. Usando mock per demo.")
        client = create_mock_client()
    else:
        client = ClientFactory.create("openai", api_key, "gpt-4o")
    
    # Test con trace
    with tracer.trace("basic_monitoring_test") as trace:
        response = client.invoke([
            TextBlock(content="Spiega cos'è il monitoring in una frase")
        ])
        
        print(f"🤖 Risposta: {response.text}")
        if hasattr(response, 'prompt_tokens_used'):
            print(f"📊 Token: {response.prompt_tokens_used + response.completion_tokens_used}")
    
    print("✅ Test completato!")


def test_conversation_monitoring():
    """Test monitoring con conversazione"""
    print("\n🧪 Test 2: Monitoring conversazione")
    
    # Setup
    manager = DatapizzaAiMonitoringManager()
    tracer = manager.setup_monitoring()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        client = create_mock_client()
    else:
        client = ClientFactory.create("openai", api_key, "gpt-4o")
    
    from datapizza.memory import Memory
    memory = Memory()
    
    # Simulazione conversazione
    conversation = [
        "Ciao, sono un developer Python",
        "Voglio imparare il monitoring delle applicazioni",
        "Quali strumenti mi consigli?"
    ]
    
    with tracer.trace("conversation_monitoring_test") as trace:
        for i, user_input in enumerate(conversation, 1):
            print(f"👤 Turno {i}: {user_input}")
            
            # Aggiungi input alla memoria
            memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
            
            # Genera risposta
            response = client.invoke(user_input, memory=memory)
            
            # Aggiungi risposta alla memoria
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Risposta {i}: {response.text[:100]}...")
            
            time.sleep(0.5)  # Pausa per simulare interazione reale
    
    print("✅ Test conversazione completato!")


def test_manual_spans():
    """Test con span manuali"""
    print("\n🧪 Test 3: Span manuali")
    
    # Setup
    manager = DatapizzaAiMonitoringManager()
    tracer = manager.setup_monitoring()
    
    # Ottieni tracer OpenTelemetry per span manuali
    otel_tracer = trace.get_tracer(__name__)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        client = create_mock_client()
    else:
        client = ClientFactory.create("openai", api_key, "gpt-4o")
    
    with tracer.trace("manual_spans_test") as trace:
        
        # Span manuale per preprocessing
        with otel_tracer.start_as_current_span("data_preprocessing") as span:
            span.set_attribute("operation", "data_preparation")
            span.set_attribute("input_size", 150)
            
            # Simula preprocessing
            time.sleep(0.2)
            processed_data = {"status": "ready", "tokens_estimated": 50}
            span.set_attribute("output_status", processed_data["status"])
            print("  🔧 Preprocessing completato")
        
        # Span manuale per AI generation
        with otel_tracer.start_as_current_span("ai_generation") as span:
            span.set_attribute("model_type", "language_model")
            span.set_attribute("provider", "openai")
            
            response = client.invoke([
                TextBlock(content="Scrivi una breve introduzione al monitoring")
            ])
            
            if hasattr(response, 'completion_tokens_used'):
                span.set_attribute("tokens_generated", response.completion_tokens_used)
                span.set_attribute("tokens_input", response.prompt_tokens_used)
            
            span.set_attribute("response_length", len(response.text))
            print(f"  🤖 AI Generation: {response.text[:80]}...")
        
        # Span manuale per post-processing
        with otel_tracer.start_as_current_span("post_processing") as span:
            span.set_attribute("operation", "result_validation")
            
            # Simula validazione
            quality_score = 0.95 if len(response.text) > 50 else 0.6
            span.set_attribute("quality_score", quality_score)
            span.set_attribute("validation_passed", quality_score > 0.8)
            
            print(f"  ✅ Post-processing: quality score {quality_score}")
    
    print("✅ Test span manuali completato!")


def create_mock_client():
    """Crea un client mock per testing senza API key"""
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.prompt_tokens_used = 15
            self.completion_tokens_used = 45
            self.cached_tokens_used = 0
    
    class MockClient:
        def invoke(self, input_data, memory=None):
            time.sleep(0.3)  # Simula latenza
            if isinstance(input_data, list):
                return MockResponse("Questa è una risposta mock per il testing del monitoring. Il monitoring è essenziale per osservare le performance delle applicazioni.")
            else:
                return MockResponse("Risposta mock per input stringa.")
    
    return MockClient()


def main():
    """Funzione principale con tutti i test"""
    print("🚀 DATAPIZZA MONITORING - Test Completo")
    print("=" * 50)
    
    # Verifica prerequisiti
    print("🔍 Verifica prerequisiti...")
    
    # Controlla Docker services
    docker_services = {
        "Zipkin": "http://localhost:9411/health",
        "Grafana": "http://localhost:3000/api/health",
        "Tempo": "http://localhost:3200/ready"
    }
    
    import requests
    available_services = []
    for service, url in docker_services.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                available_services.append(service)
                print(f"  ✅ {service} attivo")
            else:
                print(f"  ⚠️ {service} non risponde correttamente")
        except:
            print(f"  ❌ {service} non disponibile")
    
    if not available_services:
        print("\n⚠️ Nessun servizio di monitoring attivo.")
        print("💡 Avvia i servizi con: cd Monitoring/ && docker-compose up -d")
        print("   I trace saranno comunque visibili nella console.\n")
    else:
        print(f"\n✅ Servizi disponibili: {', '.join(available_services)}\n")
    
    # Esegui i test
    try:
        test_basic_monitoring()
        test_conversation_monitoring()
        test_manual_spans()
        
        print("\n🎉 TUTTI I TEST COMPLETATI!")
        print("🎯 Controlla i trace su:")
        if "Zipkin" in available_services:
            print("  - Zipkin: http://localhost:9411")
        if "Grafana" in available_services:
            print("  - Grafana: http://localhost:3000 (admin/admin)")
        
        print("\n💡 I trace sono visibili anche nella console grazie a ContextTracing!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotti dall'utente")
    except Exception as e:
        print(f"\n❌ Errore durante i test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
