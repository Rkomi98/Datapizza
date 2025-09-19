# Guida alla configurazione dei client DatapizzAI

Questa guida ti aiuterà a configurare tutti i tipi di client disponibili nella libreria DatapizzAI per interagire con diversi provider di modelli LLM.
Per due esempi completi di adapter personalizzati consulta anche la guida dedicata [`README_CUSTOM_CLIENT.md`](README_CUSTOM_CLIENT.md).

## Indice

- [Prerequisiti](#prerequisiti)
- [Setup base del codice](#setup-base-del-codice)
- [Metodo 1: Configurazione diretta dei client](#metodo-1-configurazione-diretta-dei-client)
- [Metodo 2: Utilizzo del ClientFactory (raccomandato)](#metodo-2-utilizzo-del-clientfactory-raccomandato)
- [Metodo 3: Provider personalizzato via API (es. IBM WatsonX)](#metodo-3-provider-personalizzato-via-api-es-ibm-watsonX)
- [Metodo 4: Modello locale (Ollama/Gemma)](#metodo-4-modello-locale-ollamagemma)
- [Esempio completo di utilizzo](#esempio-completo-di-utilizzo)
- [Prossimi passi](#prossimi-passi)

## Prerequisiti

Questo passaggio prepara l'ambiente, installando le dipendenze e configurando le chiavi API per evitare errori di esecuzione.

### Installazione delle dipendenze
```bash
pip install python-dotenv
```

### Configurazione delle variabili d'ambiente
Crea un file `.env` nella root del tuo progetto con almeno una chiave API:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
MISTRAL_API_KEY=your-mistral-api-key-here
AZURE_OPENAI_API_KEY=your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### Setup base del codice
Questo blocco di codice definisce l'inizializzazione minima, caricando le variabili d'ambiente e importando i client necessari per tutti gli esempi.
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Importazioni necessarie
from datapizzai.clients import (
    ClientFactory, 
    OpenAIClient,
    AnthropicClient, 
    GoogleClient,
    MistralClient,
    AzureOpenAIClient
)
from datapizzai.clients.factory import Provider
```

---

## Metodo 1: Configurazione diretta dei client

La configurazione diretta offre un controllo granulare sui parametri specifici di ciascun provider, come opzioni di caching o endpoint personalizzati.

### OpenAI client avanzato
```python
from datapizzai.cache import MemoryCache

# Configurazione con cache
cache = MemoryCache()

openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="Sei un esperto di programmazione Python.",
    temperature=0.3,  # Più deterministico per il codice
    cache=cache  # Cache opzionale per ottimizzare le performance
)

# Test del client
response = openai_client.invoke("Ciao! Come stai?")
print(f"Risposta: {response.text}")
```

### Anthropic client avanzato
```python
anthropic_client = AnthropicClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-20250514",
    system_prompt="Sei un assistente per la scrittura creativa.",
    temperature=0.8  # Più creativo per la scrittura
)

# Test del client
response = anthropic_client.invoke("Scrivi una breve poesia sulla tecnologia")
print(f"Risposta: {response.text}")
```

### Google client avanzato
```python
# Configurazione standard (GenAI API)
google_client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
    system_prompt="Sei un tutor di matematica paziente.",
    temperature=0.4
)

# Configurazione per Vertex AI (deployment enterprise)
google_vertex_client = GoogleClient(
    model="gemini-2.5-pro",
    system_prompt="Sei un assistente aziendale.",
    temperature=0.5,
    # Parametri per Vertex AI
    project_id=os.getenv("VERTEX_PROJECT_ID"),
    location="us-central1",
    credentials_path="service-account.json",
    use_vertexai=True
)

# Test del client
response = google_client.invoke("Spiegami il teorema di Pitagora")
print(f"Risposta: {response.text}")
```

### Mistral client avanzato
```python
mistral_client = MistralClient(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-large-latest",
    system_prompt="Sei un assistente multilingue specializzato in traduzioni.",
    temperature=0.6
)

# Test del client
response = mistral_client.invoke("Traduci 'Hello world' in italiano e francese")
print(f"Risposta: {response.text}")
```

### Azure OpenAI client avanzato
```python
azure_client = AzureOpenAIClient(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="Sei un assistente aziendale per Microsoft Azure.",
    temperature=0.5,
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version="2024-02-15-preview"
)

# Test del client
response = azure_client.invoke("Spiegami i servizi Azure AI")
print(f"Risposta: {response.text}")
```

---

## Metodo 2: Utilizzo del ClientFactory (raccomandato)

Il `ClientFactory` astrae i dettagli specifici del provider, permettendo di creare rapidamente un client coerente e riducendo il rischio di errori.

### OpenAI client
```python
# Configurazione base
openai_client = ClientFactory.create(
    provider=Provider.OPENAI,  # o semplicemente "openai"
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="Sei un assistente AI utile.",
    temperature=0.7
)
```

### Anthropic client (Claude)
```python
# Configurazione base
anthropic_client = ClientFactory.create(
    provider=Provider.ANTHROPIC,  # o "anthropic"
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-20250514",
    system_prompt="Sei Claude, un assistente AI di Anthropic.",
    temperature=0.5
)
```

### Google client (Gemini)
```python
# Configurazione base
google_client = ClientFactory.create(
    provider=Provider.GOOGLE,  # o "google"
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
    system_prompt="Sei Gemini, l'assistente AI di Google.",
    temperature=0.6
)
```

### Mistral client
```python
# Configurazione base
mistral_client = ClientFactory.create(
    provider=Provider.MISTRAL,  # o "mistral"
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-small-latest",
    system_prompt="Sei un assistente AI basato su Mistral.",
    temperature=0.7
)
```

### Azure OpenAI client
```python
# Configurazione base
azure_client = ClientFactory.create(
    provider=Provider.AZURE_OPENAI,  # o "azure_openai"
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="Sei un assistente aziendale professionale.",
    temperature=0.5,
    # Parametri specifici per Azure
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version="2024-02-15-preview"
)
```

---

## Metodo 3: Provider personalizzato via API (es. IBM WatsonX)

Per integrare provider personalizzati come IBM Watson, puoi creare un adapter che rispetti l'interfaccia standard `invoke(input, memory)`.

### Configurazione IBM Watson

Prerequisiti:
```bash
pip install ibm-watsonx-ai
```

Variabili d'ambiente:
```bash
IBM_WATSONX_API_KEY=your-ibm-watsonx-api-key
IBM_WATSONX_PROJECT_ID=your-project-id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Implementazione dell'adapter:

L'implementazione completa e commentata è ora disponibile nel file [`Client/custom_client_external.py`](Client/custom_client_external.py). Il modulo mostra come mappare un provider esterno sull'interfaccia `invoke` standard di DatapizzAI.

Esempio rapido di utilizzo:

```python
from dotenv import load_dotenv
from custom_client_external import IBMWatsonXClient

load_dotenv()

client = IBMWatsonXClient(
    model_id="ibm/granite-3-2-8b-instruct",
    temperature=0.7,
)
response = client.invoke("Ciao! Presentati brevemente.")
print(response.text)
```

## Metodo 4: Modello locale (Ollama/Gemma)

L'esecuzione di modelli in locale garantisce privacy, controllo dei costi e bassa latenza, senza dipendere da servizi esterni. Con [Ollama](https://ollama.com) puoi eseguire Gemma (o altri modelli) in locale e integrarlo con la stessa interfaccia `invoke`.

Prerequisiti (Linux/macOS):

```bash
# Installa Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Avvia il servizio (in un terminale separato)
ollama serve | cat

# Scarica il modello Gemma (sostituisci il tag se usi una variante diversa)
ollama pull gemma3n:e2b
```

Test rapido da CLI:

```bash
ollama run gemma3n:e2b "Ciao! Presentati brevemente."
```

Ora vediamo l'adapter Python con DatapizzAI:

Implementazione dell'adapter Python:

Trovi l'implementazione completa e commentata nel file [`Client/custom_client_ollama.py`](Client/custom_client_ollama.py). Usa la stessa interfaccia `invoke` e semplifica l'integrazione con DatapizzAI una volta che il demone Ollama è attivo (`ollama serve`).

Esempio rapido di utilizzo:

```python
from custom_client_ollama import OllamaClient

client = OllamaClient()
response = client.invoke("Ciao! Riassumi in una frase il teorema di Pitagora.")
print(response.text)
```


---

## Esempio completo di utilizzo

Questo script completo permette di verificare che il setup e la configurazione del client scelto funzionino correttamente end‑to‑end.

```python
#!/usr/bin/env python3
"""
Esempio completo di utilizzo client DatapizzAI
"""

import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.clients.factory import Provider

# Setup
load_dotenv()

def main():
    # Scegli il tuo provider preferito
    client = ClientFactory.create(
        provider=Provider.OPENAI,  # Cambia qui per testare altri provider
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Sei un assistente AI utile e professionale.",
        temperature=0.7
    )
    
    # Test del client
    print("Test del client DatapizzAI")
    print("-" * 30)
    
    response = client.invoke("Ciao! Presentati brevemente.")
    print(f"Risposta: {response.text}")
    print(f"Token usati: {response.prompt_tokens_used + response.completion_tokens_used}")
    print(f"Stop reason: {response.stop_reason}")

if __name__ == "__main__":
    main()
```

---

## Prossimi passi

Una volta validata la configurazione di base, è possibile esplorare le funzionalità avanzate della libreria.

1. **Gestione della memoria** per conversazioni multi‑turno
2. **Cache lato libreria** (`MemoryCache`, `RedisCache`) per ottimizzare costi/latency
3. **Tools e function calling** per funzionalità avanzate
4. **Risposte strutturate** con modelli Pydantic
5. **Streaming** per risposte in tempo reale

Per una spiegazione passo-passo degli adapter personalizzati visita la guida [`README_CUSTOM_CLIENT.md`](README_CUSTOM_CLIENT.md).

Suggerimenti di personalizzazione ad alto impatto:
- Pre‑processing del prompt: normalizzazione, iniezione di contesto, safety filters
- Policy di memoria: riassunti periodici (es. ogni 5 turni), pin di messaggi chiave
- Cache: passare da `MemoryCache` a `RedisCache` per ambienti multi‑istanza
- Error handling: retry con backoff, fallback cross‑provider
- Logging/metrics: hook post‑invoke per telemetria e valutazioni

Questa guida copre tutti gli aspetti della configurazione dei client. Per funzionalità avanzate, consulta la documentazione completa di DatapizzAI.
