# Guida alla configurazione dei client DatapizzAI

Questa guida ti aiuterà a configurare tutti i tipi di client disponibili nella libreria DatapizzAI per interagire con diversi provider di modelli LLM.
Per due esempi completi di adapter personalizzati consulta anche la guida dedicata [`README_CUSTOM_CLIENT.md`](README_CUSTOM_CLIENT.md).

## Indice

- [Prerequisiti](#prerequisiti)
- [Setup base del codice](#setup-base-del-codice)
- [Metodo 1: Configurazione diretta dei client](#metodo-1-configurazione-diretta-dei-client)
- [Metodo 2: Utilizzo del ClientFactory (raccomandato)](#metodo-2-utilizzo-del-clientfactory-raccomandato)
- [Metodo 3: Client custom (provider esterno o modello locale)](#metodo-3-client-custom-provider-esterno-o-modello-locale)

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

### OpenAI client diretto
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

### Anthropic client diretto
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

### Google client diretto
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

### Mistral client diretto
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

### Azure OpenAI client diretto
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

## Metodo 3: Client custom (provider esterno o modello locale)

Questo metodo segue un percorso unico per tutti i provider non nativi: definisci un adapter base, poi specializzalo verso l'API remota o il modello locale che vuoi utilizzare. In ogni caso l'interfaccia resta `invoke(input_text, memory=None)` come per gli altri client. Come si può vedere nella [sezione di approfondimento](https://github.com/Rkomi98/Datapizza/blob/LastChanges/DatapizzAI/PizzAI/Client/README_CUSTOM_CLIENT.md). Vediamo passo passo come fare.

### Passo 1: Definisci la struttura base dell'adapter

```python
from typing import Optional, Dict, Any

from datapizzai.clients import ClientResponse
from datapizzai.memory import Memory
from datapizzai.type import TextBlock


class CustomProviderClient:
    def __init__(self, api_key: str, model: str, **default_params: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.default_params = default_params  # es. temperature, top_p, ecc.

    def _build_payload(self, prompt: str, memory: Optional[Memory] = None) -> Dict[str, Any]:
        messages = []
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(
                    getattr(block, "content", "") for block in turn.blocks if getattr(block, "content", "")
                )
                if content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})
        return {"model": self.model, "messages": messages, **self.default_params}

    def _execute_request(self, payload: Dict[str, Any]) -> str:
        # Qui va la chiamata HTTP/SDK verso il provider o il runtime locale
        raise NotImplementedError("Sostituisci con la richiesta al tuo provider custom")

    def invoke(self, input_text: str, memory: Optional[Memory] = None) -> ClientResponse:
        payload = self._build_payload(input_text, memory)
        raw_response = self._execute_request(payload).strip()
        return ClientResponse(
            content=[TextBlock(content=raw_response)],
            prompt_tokens_used=0,  # opzionale: sostituisci con metrica reale
            completion_tokens_used=0,
            stop_reason="stop"
        )
```

### Passo 2: Collega un provider esterno (es. IBM WatsonX)

Reimpiega la classe base passando le credenziali del provider e mappando la risposta dell'SDK sul `ClientResponse`. Installa le librerie e imposta le API Keys necessarie.

In questo addendum analalizziamo nello specifico un'implementazione già pronta che estende lo schema visto sopra applicato ad un cliento specifico ([IBM WatsonX](https://github.com/Rkomi98/Datapizza/blob/LastChanges/DatapizzAI/PizzAI/Client/README_CUSTOM_CLIENT.md#esempio-a--provider-esterno-ibm-watsonx)).


### Passo 3: Collega un modello locale (es. Ollama/Gemma)

Se si usa un modello locale, in primis deve essere avviato servizio e successivamente deve essere scaricato ed avviato il modello scelto.

Tra gli esempi specifici è presente una guida ad hoc per configurare [un client locale](https://github.com/Rkomi98/Datapizza/blob/LastChanges/DatapizzAI/PizzAI/Client/README_CUSTOM_CLIENT.md#esempio-b--modello-locale-ollama).

---

Questa guida copre tutti gli aspetti della configurazione dei client. Per funzionalità avanzate, consulta la documentazione completa di DatapizzAI.
