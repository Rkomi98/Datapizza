#!/usr/bin/env python3
"""
Esempio completo di monitoring con datapizzai
============================================

Questo esempio dimostra tutte le funzionalità di monitoring disponibili:
- Tracing automatico dei client
- Creazione manuale di span
- Integrazione con esportatori esterni (Zipkin, OTLP)
- Monitoring delle performance
- Attributi personalizzati

Requisiti:
- pip install datapizzai opentelemetry-api opentelemetry-sdk
- pip install opentelemetry-exporter-zipkin opentelemetry-exporter-otlp
- pip install psutil python-dotenv

Uso:
    python monitoring_complete_example.py
"""

import os
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Datapizzai imports
from datapizzai.clients import ClientFactory
from datapizzai.tracing import ContextTracing
from datapizzai.tracing.tracing import generation_span, tool_span, agent_span
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    ZIPKIN_AVAILABLE = True
except ImportError:
    print("⚠️  Zipkin exporter non disponibile. Installare: pip install opentelemetry-exporter-zipkin")
    ZIPKIN_AVAILABLE = False

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    OTLP_AVAILABLE = True
except ImportError:
    print("⚠️  OTLP exporter non disponibile. Installare: pip install opentelemetry-exporter-otlp")
    OTLP_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    print("⚠️  psutil non disponibile. Installare: pip install psutil")
    PSUTIL_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class PerformanceMetrics:
    """Metriche di performance per il monitoring"""
    operation_name: str
    duration_seconds: float
    tokens_used: int
    memory_usage_mb: float
    success: bool
    error_message: Optional[str] = None


class MonitoringExampleApp:
    """Applicazione di esempio per il monitoring con datapizzai"""
    
    def __init__(self):
        self.tracer = ContextTracing()
        self.metrics: List[PerformanceMetrics] = []
        self.client = None
        self.memory = Memory()
        
        # Setup client
        self._setup_client()
        
        # Setup external exporters (opzionale)
        self._setup_external_exporters()
    
    def _setup_client(self):
        """Configura il client AI"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY non trovata. Usando mock client per demo.")
                self.client = self._create_mock_client()
            else:
                self.client = ClientFactory.create("openai", api_key, "gpt-3.5-turbo")
                logger.info("✅ Client OpenAI configurato")
        except Exception as e:
            logger.error(f"Errore configurazione client: {e}")
            self.client = self._create_mock_client()
    
    def _create_mock_client(self):
        """Crea un mock client per testing senza API key"""
        class MockResponse:
            def __init__(self, text: str):
                self.text = text
                self.prompt_tokens_used = 10
                self.completion_tokens_used = 20
                self.cached_tokens_used = 0
        
        class MockClient:
            def invoke(self, messages):
                time.sleep(0.1)  # Simula latenza
                return MockResponse("Questa è una risposta mock per il testing del monitoring.")
        
        return MockClient()
    
    def _setup_external_exporters(self):
        """Configura esportatori esterni (Zipkin, OTLP)"""
        try:
            # Setup risorsa OpenTelemetry
            resource = Resource.create({
                SERVICE_NAME: "datapizzai-monitoring-example",
                SERVICE_VERSION: "1.0.0",
                "environment": "development",
                "example": "monitoring"
            })
            
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)
            
            # Setup Zipkin (se disponibile e configurato)
            if ZIPKIN_AVAILABLE and os.getenv("ZIPKIN_ENDPOINT"):
                zipkin_exporter = ZipkinExporter(
                    endpoint=os.getenv("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans")
                )
                zipkin_processor = BatchSpanProcessor(zipkin_exporter)
                tracer_provider.add_span_processor(zipkin_processor)
                logger.info("✅ Zipkin exporter configurato")
            
            # Setup OTLP (se disponibile e configurato)
            if OTLP_AVAILABLE and os.getenv("OTLP_ENDPOINT"):
                otlp_exporter = OTLPSpanExporter(
                    endpoint=os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
                )
                otlp_processor = BatchSpanProcessor(otlp_exporter)
                tracer_provider.add_span_processor(otlp_processor)
                logger.info("✅ OTLP exporter configurato")
                
        except Exception as e:
            logger.warning(f"Errore configurazione esportatori: {e}")
    
    def _record_performance(self, operation_name: str, duration: float, 
                          tokens_used: int, success: bool, error_message: str = None):
        """Registra metriche di performance"""
        memory_usage = 0.0
        if PSUTIL_AVAILABLE:
            try:
                memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
            except:
                pass
        
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            duration_seconds=duration,
            tokens_used=tokens_used,
            memory_usage_mb=memory_usage,
            success=success,
            error_message=error_message
        )
        self.metrics.append(metrics)
    
    def basic_tracing_example(self):
        """Esempio 1: Tracing automatico base"""
        print("\n🔍 Esempio 1: Tracing automatico base")
        
        start_time = time.time()
        success = True
        tokens_used = 0
        error_message = None
        
        try:
            with self.tracer.trace("basic_conversation") as trace:
                # Aggiungi messaggio utente
                self.memory.add(TextBlock(
                    text="Ciao! Puoi spiegarmi in breve cos'è il monitoring?", 
                    role=ROLE.USER
                ))
                
                # Invoca client (tracciato automaticamente)
                response = self.client.invoke(self.memory.get_memory())
                
                # Aggiungi risposta
                self.memory.add(TextBlock(text=response.text, role=ROLE.ASSISTANT))
                
                tokens_used = response.prompt_tokens_used + response.completion_tokens_used
                
                print(f"  💬 Risposta: {response.text[:100]}...")
                print(f"  📊 Token utilizzati: {tokens_used}")
                
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Errore in basic_tracing_example: {e}")
        
        finally:
            duration = time.time() - start_time
            self._record_performance("basic_conversation", duration, tokens_used, success, error_message)
    
    def manual_spans_example(self):
        """Esempio 2: Creazione manuale di span"""
        print("\n🛠️  Esempio 2: Span manuali con attributi personalizzati")
        
        start_time = time.time()
        success = True
        total_tokens = 0
        error_message = None
        
        try:
            with self.tracer.trace("complex_operation_with_spans") as trace:
                
                # Span per preprocessing
                with tool_span("preprocessing") as span:
                    span.set_attribute("operation_type", "data_preprocessing")
                    span.set_attribute("input_size", 150)
                    
                    # Simula preprocessing
                    time.sleep(0.2)
                    
                    processed_data = {"clean": True, "tokens": 120}
                    span.set_attribute("output_tokens", processed_data["tokens"])
                    span.set_attribute("preprocessing_success", True)
                    
                    print("  🔧 Preprocessing completato")
                
                # Span per generazione AI
                with generation_span("ai_generation") as span:
                    span.set_attribute("model_type", "language_model")
                    span.set_attribute("temperature", 0.7)
                    span.set_attribute("max_tokens", 150)
                    
                    self.memory.add(TextBlock(
                        text="Basandoti sulla conversazione precedente, dammi un esempio pratico di monitoring",
                        role=ROLE.USER
                    ))
                    
                    response = self.client.invoke(self.memory.get_memory())
                    self.memory.add(TextBlock(text=response.text, role=ROLE.ASSISTANT))
                    
                    tokens_used = response.prompt_tokens_used + response.completion_tokens_used
                    total_tokens += tokens_used
                    
                    span.set_attribute("tokens_generated", response.completion_tokens_used)
                    span.set_attribute("tokens_input", response.prompt_tokens_used)
                    span.set_attribute("response_length", len(response.text))
                    
                    print(f"  🤖 AI Generation completato - {tokens_used} tokens")
                
                # Span per post-processing
                with agent_span("decision_agent") as span:
                    span.set_attribute("agent_type", "quality_checker")
                    
                    # Simula decisione basata sulla risposta
                    quality_score = 0.95 if len(response.text) > 50 else 0.3
                    decision = "approved" if quality_score > 0.8 else "needs_revision"
                    
                    span.set_attribute("quality_score", quality_score)
                    span.set_attribute("decision", decision)
                    span.set_attribute("response_approved", decision == "approved")
                    
                    print(f"  ✅ Quality Check: {decision} (score: {quality_score})")
                
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Errore in manual_spans_example: {e}")
        
        finally:
            duration = time.time() - start_time
            self._record_performance("complex_operation", duration, total_tokens, success, error_message)
    
    def performance_monitoring_example(self):
        """Esempio 3: Monitoring delle performance"""
        print("\n📈 Esempio 3: Performance monitoring")
        
        operations = ["quick_question", "detailed_analysis", "creative_task"]
        
        for i, operation in enumerate(operations):
            start_time = time.time()
            success = True
            tokens_used = 0
            error_message = None
            
            try:
                with self.tracer.trace(f"performance_test_{operation}") as trace:
                    with generation_span(f"perf_{operation}") as span:
                        span.set_attribute("test_iteration", i + 1)
                        span.set_attribute("operation_category", operation)
                        
                        # Varia la complessità delle richieste
                        if operation == "quick_question":
                            prompt = "Cosa significa AI?"
                            expected_tokens = 30
                        elif operation == "detailed_analysis":
                            prompt = "Analizza i pro e contro dell'intelligenza artificiale in 200 parole"
                            expected_tokens = 250
                        else:  # creative_task
                            prompt = "Scrivi una breve storia di fantascienza"
                            expected_tokens = 200
                        
                        span.set_attribute("expected_tokens", expected_tokens)
                        span.set_attribute("prompt_complexity", operation)
                        
                        self.memory.add(TextBlock(text=prompt, role=ROLE.USER))
                        response = self.client.invoke(self.memory.get_memory())
                        
                        tokens_used = response.prompt_tokens_used + response.completion_tokens_used
                        
                        span.set_attribute("actual_tokens", tokens_used)
                        span.set_attribute("token_efficiency", tokens_used / expected_tokens)
                        
                        print(f"  📝 {operation}: {tokens_used} tokens in {time.time() - start_time:.2f}s")
                        
            except Exception as e:
                success = False
                error_message = str(e)
                logger.error(f"Errore in performance test {operation}: {e}")
            
            finally:
                duration = time.time() - start_time
                self._record_performance(f"perf_{operation}", duration, tokens_used, success, error_message)
    
    def get_performance_report(self) -> Dict:
        """Genera report delle performance"""
        if not self.metrics:
            return {"error": "Nessuna metrica disponibile"}
        
        successful_ops = [m for m in self.metrics if m.success]
        failed_ops = [m for m in self.metrics if not m.success]
        
        if not successful_ops:
            return {"error": "Nessuna operazione completata con successo"}
        
        total_operations = len(self.metrics)
        success_rate = len(successful_ops) / total_operations
        avg_duration = sum(m.duration_seconds for m in successful_ops) / len(successful_ops)
        total_tokens = sum(m.tokens_used for m in successful_ops)
        avg_memory = sum(m.memory_usage_mb for m in successful_ops) / len(successful_ops)
        
        # Raggruppa per tipo di operazione
        operations_by_type = {}
        for metric in successful_ops:
            op_type = metric.operation_name
            if op_type not in operations_by_type:
                operations_by_type[op_type] = []
            operations_by_type[op_type].append(metric)
        
        # Calcola statistiche per tipo
        type_stats = {}
        for op_type, ops in operations_by_type.items():
            type_stats[op_type] = {
                "count": len(ops),
                "avg_duration": sum(op.duration_seconds for op in ops) / len(ops),
                "total_tokens": sum(op.tokens_used for op in ops),
                "avg_tokens": sum(op.tokens_used for op in ops) / len(ops) if ops else 0
            }
        
        return {
            "summary": {
                "total_operations": total_operations,
                "successful_operations": len(successful_ops),
                "failed_operations": len(failed_ops),
                "success_rate": round(success_rate * 100, 2),
                "avg_duration_seconds": round(avg_duration, 3),
                "total_tokens_used": total_tokens,
                "avg_memory_usage_mb": round(avg_memory, 2),
                "operations_per_second": round(1 / avg_duration, 2) if avg_duration > 0 else 0
            },
            "by_operation_type": type_stats,
            "errors": [{"operation": m.operation_name, "error": m.error_message} 
                      for m in failed_ops] if failed_ops else []
        }
    
    def run_complete_example(self):
        """Esegue l'esempio completo di monitoring"""
        print("🚀 Avvio esempio completo di monitoring con datapizzai")
        print("=" * 60)
        
        # Esempio 1: Tracing base
        self.basic_tracing_example()
        
        # Esempio 2: Span manuali
        self.manual_spans_example()
        
        # Esempio 3: Performance monitoring
        self.performance_monitoring_example()
        
        # Report finale
        print("\n📊 REPORT FINALE DELLE PERFORMANCE")
        print("=" * 60)
        
        report = self.get_performance_report()
        
        if "error" in report:
            print(f"❌ {report['error']}")
            return
        
        # Summary
        summary = report["summary"]
        print(f"📈 Operazioni totali: {summary['total_operations']}")
        print(f"✅ Operazioni riuscite: {summary['successful_operations']}")
        print(f"❌ Operazioni fallite: {summary['failed_operations']}")
        print(f"📊 Tasso di successo: {summary['success_rate']}%")
        print(f"⏱️  Durata media: {summary['avg_duration_seconds']}s")
        print(f"🎯 Token totali: {summary['total_tokens_used']}")
        print(f"💾 Memoria media: {summary['avg_memory_usage_mb']} MB")
        print(f"🚀 Ops/sec: {summary['operations_per_second']}")
        
        # Dettagli per tipo di operazione
        print(f"\n📋 DETTAGLI PER TIPO DI OPERAZIONE")
        print("-" * 40)
        for op_type, stats in report["by_operation_type"].items():
            print(f"🔸 {op_type}:")
            print(f"   Esecuzioni: {stats['count']}")
            print(f"   Durata media: {stats['avg_duration']:.3f}s")
            print(f"   Token medi: {stats['avg_tokens']:.0f}")
            print(f"   Token totali: {stats['total_tokens']}")
        
        # Errori (se presenti)
        if report["errors"]:
            print(f"\n❌ ERRORI RILEVATI")
            print("-" * 40)
            for error in report["errors"]:
                print(f"🔸 {error['operation']}: {error['error']}")
        
        print(f"\n✨ Esempio completato! Controlla i trace sopra per i dettagli.")
        print(f"💡 Suggerimento: Configura ZIPKIN_ENDPOINT o OTLP_ENDPOINT per esportazione esterna")


def main():
    """Funzione principale"""
    app = MonitoringExampleApp()
    app.run_complete_example()


if __name__ == "__main__":
    main()
