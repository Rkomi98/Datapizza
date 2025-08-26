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
    # Aggiungi input utente
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Limita memoria se necessario - mantieni solo gli ultimi N turni
    if len(memory.memory) > window_size:
        memory.memory = memory.memory[-window_size:]
    
    # Genera risposta con memoria ottimizzata
    response = client.invoke("", memory=memory)
    
    # Aggiungi risposta alla memoria
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    return response

# Utilizzo pratico
memory = Memory()
conversation = [
    "Ciao! Sono un sviluppatore Python alle prime armi.",
    "Vorrei imparare a creare un chatbot con Python.",
    "Quali librerie mi consigli per iniziare?",
    "E come gestisco la memoria delle conversazioni?",
    "Puoi mostrarmi un esempio di codice?",
    "Come gestisco gli errori e le eccezioni?",
    "E per il deployment su un server web?",
    "Quali sono le best practices per la sicurezza?"
]

for user_input in conversation:
    response = sliding_window_chat(memory, user_input, window_size=4)
    print(f"Utente: {user_input}")
    print(f"Assistente: {response.text}")
    print(f"Memoria attiva: {len(memory.memory)} turni\n")
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

## Esempi complessi

### Creazione di un chatbot completo
```python
def develop_chatbot_with_ai():
    """Sviluppa un chatbot completo con assistenza AI"""
    memory = Memory()
    
    # Fase 1: Analisi requisiti
    requirements = [
        "Voglio creare un chatbot per un e-commerce di abbigliamento.",
        "Il chatbot deve gestire: assistenza clienti, ricerca prodotti, gestione ordini.",
        "Avremo circa 1000 clienti al giorno e dobbiamo gestire 5 lingue diverse.",
        "Quali sono i requisiti tecnici principali?"
    ]
    
    for req in requirements:
        memory.add_turn([TextBlock(content=req)], ROLE.USER)
        response = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    # Fase 2: Progettazione tecnica
    technical_questions = [
        "Come strutturerei l'architettura del sistema?",
        "Quali tecnologie mi consigli per backend e frontend?",
        "Come gestisco la scalabilità e la disponibilità?"
    ]
    
    for question in technical_questions:
        memory.add_turn([TextBlock(content=question)], ROLE.USER)
        response = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    # Fase 3: Riassunto e piano d'azione
    summary_response = client.invoke(
        "Riassumi il progetto e fornisci un piano d'azione con i prossimi 5 passi",
        memory=memory
    )
    
    return summary_response.text

# Utilizzo
chatbot_plan = develop_chatbot_with_ai()
print(chatbot_plan)
```

### Gestione memoria intelligente
```python
class SmartMemory:
    """Gestisce la memoria con strategie avanzate"""
    
    def __init__(self, max_turns: int = 10, importance_threshold: float = 0.7):
        self.memory = Memory()
        self.max_turns = max_turns
        self.importance_threshold = importance_threshold
    
    def add_turn(self, content: str, role: ROLE, importance: float = 0.5):
        """Aggiunge un turno con valutazione dell'importanza"""
        # Aggiungi turno
        self.memory.add_turn([TextBlock(content=content)], role)
        
        # Gestisci dimensione memoria
        if len(self.memory.memory) > self.max_turns:
            # Mantieni turni importanti e ultimi turni
            important_turns = [t for t in self.memory.memory if hasattr(t, 'importance') and t.importance > self.importance_threshold]
            recent_turns = self.memory.memory[-self.max_turns//2:]
            
            # Combina e limita
            combined = list(set(important_turns + recent_turns))
            self.memory.memory = combined[-self.max_turns:]
    
    def get_context_summary(self, client):
        """Genera un riassunto del contesto per ottimizzare i token"""
        if len(self.memory.memory) > 5:
            summary_response = client.invoke(
                "Riassumi brevemente i punti principali della conversazione",
                memory=self.memory
            )
            return summary_response.text
        return None

# Utilizzo
smart_memory = SmartMemory(max_turns=8)
# ... conversazione con gestione automatica della memoria
```

## Documentazione completa

➡️ **[GUIDA_TEXT_ONLY.md](GUIDA_TEXT_ONLY.md)** - Guida tecnica completa con esempi avanzati, best practices, troubleshooting e codice copiabile

➡️ **[text_only_examples.py](text_only_examples.py)** - Script completo con tutte le demo e esempi pratici