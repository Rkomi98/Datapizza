# Guida alla configurazione dei client DatapizzAI

Questa guida ti aiuterà a configurare tutti i tipi di client disponibili nella libreria DatapizzAI per interagire con diversi provider di modelli LLM.

## Indice

- [Prerequisiti](#prerequisiti)
- [Setup base del codice](#setup-base-del-codice)
- [Metodo 1: Utilizzo del ClientFactory (raccomandato)](#metodo-1-utilizzo-del-clientfactory-raccomandato)
- [Metodo 2: Configurazione diretta dei client](#metodo-2-configurazione-diretta-dei-client)
- [Metodo 3: Provider personalizzato via API (es. DeepSeek)](#metodo-3-provider-personalizzato-via-api-es-deepseek)
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
# File .env - aggiungi solo le chiavi che ti servono
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

# Carica le variabili d'ambiente
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

## Metodo 1: Utilizzo del ClientFactory (raccomandato)

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

# Modelli disponibili: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
```

### Anthropic client (Claude)
```python
# Configurazione base
anthropic_client = ClientFactory.create(
    provider=Provider.ANTHROPIC,  # o "anthropic"
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-4-sonnet-latest",
    system_prompt="Sei Claude, un assistente AI di Anthropic.",
    temperature=0.5
)

# Modelli disponibili: claude-3-5-sonnet-latest, claude-3-5-haiku-latest, claude-3-opus-latest
```

### Google client (Gemini)
```python
# Configurazione base
google_client = ClientFactory.create(
    provider=Provider.GOOGLE,  # o "google"
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
    system_prompt="Sei Gemini, l'assistente AI di Google.",
    temperature=0.6
)

# Modelli disponibili: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash
```

### Mistral client
```python
# Configurazione base
mistral_client = ClientFactory.create(
    provider=Provider.MISTRAL,  # o "mistral"
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-large-latest",
    system_prompt="Sei un assistente AI basato su Mistral.",
    temperature=0.7
)

# Modelli disponibili: mistral-large-latest, mistral-medium-latest, mistral-small-latest
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

## Metodo 2: Configurazione diretta dei client

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
    model="claude-3-5-sonnet-latest",
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
    model="gemini-2.0-flash",
    system_prompt="Sei un tutor di matematica paziente.",
    temperature=0.4
)

# Configurazione per Vertex AI (deployment enterprise)
google_vertex_client = GoogleClient(
    model="gemini-1.5-pro",
    system_prompt="Sei un assistente aziendale.",
    temperature=0.5,
    # Parametri per Vertex AI
    project_id="your-gcp-project-id",
    location="us-central1",
    credentials_path="/path/to/service-account.json",
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

## Metodo 3: Provider personalizzato via API (es. DeepSeek)

#TODO (con AI eng):
- Definire design dell'adapter REST per provider custom (schema richieste/risposte, headers, retry, timeouts).
- Standardizzare il payload e la risposta per allinearsi a `invoke(input, memory)` del framework.
- Gestire errori/transitori (HTTP, rate limit, parsing) e metriche (`usage`).
- Scrivere esempi minimi e test end‑to‑end con provider reale.

Nota: per ora, si consiglia l’uso di `ClientFactory` o client nativi già inclusi. L’implementazione dell’adapter custom sarà aggiunta insieme al team AI Engineering.

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

Adapter Python minimale (stesso schema del provider personalizzato):

```python
import requests
from typing import Optional, Union, List
from pydantic import BaseModel

from datapizzai.type import TextBlock
from datapizzai.memory import Memory


class SimpleResponse(BaseModel):
    text: str
    prompt_tokens_used: int = 0
    completion_tokens_used: int = 0
    stop_reason: str = "stop"


class OllamaClient:
    def __init__(self, model: str = "gemma3n:e2b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _build_messages(self, input=None, memory: Optional[Memory] = None):
        msgs = []
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(getattr(b, "content", "") for b in turn.blocks)
                if content:
                    msgs.append({"role": role, "content": content})
        if isinstance(input, str) and input:
            msgs.append({"role": "user", "content": input})
        return msgs

    def invoke(self, input=None, memory: Optional[Memory] = None) -> SimpleResponse:
        payload = {"model": self.model, "messages": self._build_messages(input, memory), "stream": False}
        try:
            r = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            text = data.get("message", {}).get("content") or str(data)
        except Exception as e:
            text = f"Errore Ollama: {e}"
        return SimpleResponse(text=text)


if __name__ == "__main__":
    client = OllamaClient()
    print(client.invoke("Ciao! Riassumi in una frase il teorema di Pitagora.").text)
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

Suggerimenti di personalizzazione ad alto impatto:
- Pre‑processing del prompt: normalizzazione, iniezione di contesto, safety filters
- Policy di memoria: riassunti periodici (es. ogni 5 turni), pin di messaggi chiave
- Cache: passare da `MemoryCache` a `RedisCache` per ambienti multi‑istanza
- Error handling: retry con backoff, fallback cross‑provider
- Logging/metrics: hook post‑invoke per telemetria e valutazioni

Questa guida copre tutti gli aspetti della configurazione dei client. Per funzionalità avanzate, consulta la documentazione completa di DatapizzAI.
