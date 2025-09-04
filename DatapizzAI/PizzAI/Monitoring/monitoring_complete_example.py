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
