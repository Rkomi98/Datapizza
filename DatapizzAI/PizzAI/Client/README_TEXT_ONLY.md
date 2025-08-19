# DatapizzAI text-only

Guida rapida per l'utilizzo delle modalità one-shot e conversational del framework DatapizzAI per prompt testuali.

## Avvio rapido

```bash
# Attiva ambiente virtuale
source .venv/bin/activate

# Configura API keys nel file .env
echo 'OPENAI_API_KEY=your-key-here' > PizzAI/.env

# Esegui l'esempio interattivo
python Client/text_only_examples.py
```

## Modalità disponibili

### One-shot (Query singola → Risposta)
**Quando usare**: Domande isolate, traduzioni, calcoli, analisi indipendenti

```python
from datapizzai.clients import ClientFactory
import os

# Creazione client
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Query semplice
response = client.invoke("Spiega il machine learning in 2 frasi")
print(response.text)
```

### Conversational (Multi-turno con memoria)
**Quando usare**: Tutoring, consulenza, sviluppo iterativo di idee, supporto tecnico

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

# Setup memoria
memory = Memory()

# Conversazione
def chat_turn(user_input: str):
    # Aggiungi input utente
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Genera risposta con contesto
    response = client.invoke("", memory=memory)
    
    # Aggiungi risposta alla memoria
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    return response.text

# Utilizzo
print(chat_turn("Ciao, sono Marco, sviluppatore Python"))
print(chat_turn("Quali sono le best practices per Django?"))
print(chat_turn("E per il mio caso specifico?"))  # Usa il contesto precedente
```

## Configurazione

### File .env richiesto
```bash
# Directory: PizzAI/.env
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here  
GOOGLE_API_KEY=your-google-key-here
MISTRAL_API_KEY=your-mistral-key-here
```

### Provider supportati

| Provider | Modello | One-shot | Conversational | Cache |
|----------|---------|----------|----------------|-------|
| **OpenAI** | gpt-4o | ✅ | ✅ | ✅ |
| **Anthropic** | claude-3-5-sonnet | ✅ | ✅ | ❌ |
| **Google** | gemini-2.5-flash | ✅ | ✅ | ❌ |
| **Mistral** | mistral-large-latest | ✅ | ✅ | ❌ |

## Menu interattivo

```
MODALITÀ ONE-SHOT:
1. Esempi base one-shot
2. Esempi avanzati one-shot  
3. Confronto tra provider

MODALITÀ CONVERSATIONAL:
4. Conversazione base con memoria
5. Scenari conversazionali avanzati
6. Gestione avanzata della memoria
```

## Comparazione modalità

| Scenario | One-shot | Conversational | Consiglio |
|----------|----------|----------------|-----------|
| **FAQ semplici** | ✅ Ideale | ❌ Overhead | One-shot |
| **Traduzioni** | ✅ Ideale | ❌ Non necessario | One-shot |
| **Calcoli matematici** | ✅ Ideale | ❌ Overhead | One-shot |
| **Tutoring/Teaching** | ❌ Limitato | ✅ Necessario | Conversational |
| **Consulenza tecnica** | ❌ Limitato | ✅ Necessario | Conversational |
| **Brainstorming** | ❌ Limitato | ✅ Necessario | Conversational |
| **Debug assistito** | ❌ Limitato | ✅ Necessario | Conversational |
| **Analisi iterativa** | ❌ Limitato | ✅ Necessario | Conversational |

## Gestione memoria avanzata

### Strategia sliding window
```python
def sliding_window_chat(memory: Memory, user_input: str, window_size: int = 6):
    """Mantiene solo gli ultimi N turni per ottimizzare token usage"""
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Limita memoria se necessario
    if len(memory.memory) > window_size:
        memory.memory = memory.memory[-window_size:]
    
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    return response
```

### Cache per performance
```python
from datapizzai.cache import MemoryCache

# Solo OpenAI supporta cache nel costruttore
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=MemoryCache()  # Riduce costi per query ripetute
)
```

## Esempi pratici

### Consulenza tecnica progressiva
```python
memory = Memory()

def technical_consultation():
    responses = []
    
    # Definizione problema
    responses.append(chat_turn("Devo architettare un sistema e-commerce per 100k utenti"))
    
    # Approfondimento vincoli
    responses.append(chat_turn("Budget 50k€, team 6 sviluppatori, lancio in 6 mesi"))
    
    # Scelta tecnologica basata su contesto
    responses.append(chat_turn("Il team conosce Java Spring. Microservizi o monolite?"))
    
    # Cambio focus mantenendo contesto
    responses.append(chat_turn("Parliamo di sicurezza per il sistema che abbiamo discusso"))
    
    return responses
```

### Analisi multi-provider
```python
def compare_providers_response(prompt: str):
    """Confronta risposta di diversi provider sullo stesso prompt"""
    
    providers = ["openai", "anthropic", "google"]
    results = {}
    
    for provider in providers:
        client = ClientFactory.create(provider=provider, ...)
        response = client.invoke(prompt)
        results[provider] = {
            "text": response.text,
            "tokens": response.prompt_tokens_used + response.completion_tokens_used,
            "time": "..." # misurato con time.time()
        }
    
    return results
```

## Troubleshooting comune

### Error: "API key not found"
```bash
# Verifica file .env
ls -la PizzAI/.env

# Crea se mancante
echo 'OPENAI_API_KEY=your-key' > PizzAI/.env
```

### Error: "Cache not supported"
```python
# Solo OpenAI supporta cache nel costruttore
def create_safe_client(provider: str):
    kwargs = {"provider": provider, "api_key": "...", "model": "..."}
    
    if provider == "openai":
        kwargs["cache"] = MemoryCache()  # OK
    # Altri provider: cache non supportata nel costruttore
    
    return ClientFactory.create(**kwargs)
```

### Memoria troppo grande
```python
# Strategia di pulizia memoria
if len(memory.memory) > 10:  # Soglia personalizzabile
    # Mantieni solo ultimi 6 turni
    memory.memory = memory.memory[-6:]
    print("Memoria ottimizzata")
```

## Metriche di performance

### Token usage tipico
- **One-shot**: 50-200 token per query
- **Conversational**: Token crescenti con memoria
- **Cache hit**: ~50% riduzione costi query ripetute

### Latenza tipica
- **OpenAI**: 1-3 secondi
- **Anthropic**: 2-4 secondi  
- **Google**: 1-2 secondi

### Gestione costi
- One-shot: Costi prevedibili per query
- Conversational: Monitorare crescita memoria
- Cache: Significativo risparmio per pattern ripetuti

## Documentazione completa

➡️ **[GUIDA_TEXT_ONLY.md](GUIDA_TEXT_ONLY.md)** - Guida tecnica completa con esempi avanzati, best practices, troubleshooting e codice copiabile

## Pattern di implementazione consigliati

### Per applicazioni FAQ/Support
```python
# Pattern one-shot ottimizzato
def handle_faq(question: str):
    client = create_client("openai")
    return client.invoke(f"FAQ: {question}")
```

### Per applicazioni tutoring/consulenza
```python
# Pattern conversational con memoria gestita
class TutoringSession:
    def __init__(self):
        self.memory = Memory()
        self.client = create_client("openai")
    
    def ask(self, question: str):
        self.memory.add_turn([TextBlock(content=question)], ROLE.USER)
        response = self.client.invoke("", memory=self.memory)
        self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        return response.text
```

---

**DatapizzAI text-only**: un'interfaccia unificata per gestire sia query singole che conversazioni complesse con la massima semplicità e flessibilità.
