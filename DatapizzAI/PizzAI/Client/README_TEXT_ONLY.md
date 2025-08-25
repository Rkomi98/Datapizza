# DatapizzAI text-only

Guida rapida per l'utilizzo delle modalità one-shot e conversational del framework DatapizzAI per prompt testuali.

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

## Comparazione modalità

| Scenario | One-shot | Conversational | Consiglio pratico |
|----------|----------|----------------|-------------------|
| **FAQ semplici** | ✅ Ideale | ✅ Possibile | One-shot (più efficiente) |
| **Traduzioni** | ✅ Ideale | ✅ Possibile | One-shot (più veloce) |
| **Calcoli matematici** | ✅ Ideale | ✅ Possibile | One-shot (più diretto) |
| **Tutoring/Teaching** | ✅ Possibile | ✅ Ideale | Conversational (migliore esperienza) |
| **Consulenza tecnica** | ✅ Possibile | ✅ Ideale | Conversational (contesto persistente) |
| **Brainstorming** | ✅ Possibile | ✅ Ideale | Conversational (sviluppo idee) |
| **Debug assistito** | ✅ Possibile | ✅ Ideale | Conversational (storia errori) |
| **Analisi iterativa** | ✅ Possibile | ✅ Ideale | Conversational (approfondimenti) |

*Nota: Entrambe le modalità supportano tutti gli scenari. I consigli sono basati su efficienza e user experience, non su limitazioni tecniche del framework.*

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

## Documentazione completa

➡️ **[GUIDA_TEXT_ONLY.md](GUIDA_TEXT_ONLY.md)** - Guida tecnica completa con esempi avanzati, best practices, troubleshooting e codice copiabile