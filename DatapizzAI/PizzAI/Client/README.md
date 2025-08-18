# Guida alla configurazione dei client DatapizzAI

Questa guida ti aiuterà a configurare tutti i tipi di client disponibili nella libreria DatapizzAI per interagire con diversi provider di modelli LLM.

## Prerequisiti

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

Il `ClientFactory` è il modo più semplice per creare client con configurazione automatica.

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
    model="claude-3-5-sonnet-latest",
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

Per configurazioni avanzate, puoi creare i client direttamente.

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

## Esempio completo di utilizzo

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

Una volta configurato il tuo client, puoi esplorare:

1. **Gestione della memoria** per conversazioni multi-turno
2. **Sistema di cache** per ottimizzare le performance
3. **Tools e function calling** per funzionalità avanzate
4. **Risposte strutturate** con modelli Pydantic
5. **Streaming** per risposte in tempo reale

Questa guida copre tutti gli aspetti della configurazione dei client. Per funzionalità avanzate, consulta la documentazione completa di DatapizzAI.
