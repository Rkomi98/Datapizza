# Guida completa: tool, agenti e RAG agentico

Questa guida approfondisce i concetti di tool, agenti e RAG agentico con esempi pratici e codice funzionante.

## Indice

1. [Tool: estendere le capacità degli LLM](#1-tool-estendere-le-capacità-degli-llm)
2. [Agenti: sistemi autonomi di ragionamento](#2-agenti-sistemi-autonomi-di-ragionamento)
3. [RAG agentico: retrieval intelligente](#3-rag-agentico-retrieval-intelligente)
4. [Implementazione pratica](#4-implementazione-pratica)
5. [Best practice e pattern comuni](#5-best-practice-e-pattern-comuni)

---

## 1. Tool: estendere le capacità degli LLM

### 1.1 Definizione

Un **tool** (o funzione) è un componente software che un LLM può invocare per eseguire operazioni che non può fare autonomamente. I tool permettono agli LLM di:

- Accedere a dati esterni (API, database, file)
- Eseguire calcoli complessi
- Interagire con sistemi esterni
- Recuperare informazioni in tempo reale

### 1.2 Anatomia di un tool

Un tool è composto da due elementi:

**1. Schema JSON** - Descrive il tool all'LLM:

```python
tool_schema = {
    "type": "function",
    "function": {
        "name": "nome_funzione",           # Identificatore univoco
        "description": "Descrizione...",   # L'LLM usa questo per decidere quando usare il tool
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Descrizione del parametro"
                },
                "param2": {
                    "type": "integer",
                    "description": "Altro parametro"
                }
            },
            "required": ["param1"]  # Parametri obbligatori
        }
    }
}
```

**2. Implementazione Python** - La funzione che esegue l'operazione:

```python
def nome_funzione(param1: str, param2: int = 10) -> dict:
    """
    Esegue l'operazione descritta nello schema.
    
    Args:
        param1: Descrizione del parametro
        param2: Altro parametro (default: 10)
    
    Returns:
        Dizionario con il risultato
    """
    # Logica della funzione
    result = do_something(param1, param2)
    return {"result": result}
```

### 1.3 Come funziona il function calling

Il flusso di esecuzione è:

```
1. UTENTE: "Che tempo fa a Milano?"

2. LLM: Analizza la richiesta e i tool disponibili
   → Decide di usare get_weather
   → Genera: {"name": "get_weather", "arguments": {"city": "Milano"}}

3. SISTEMA: Esegue get_weather("Milano")
   → Ottiene: {"temperature": 18, "condition": "nuvoloso"}

4. LLM: Riceve il risultato e genera la risposta finale
   → "A Milano ci sono 18 gradi e il cielo è nuvoloso."
```

### 1.4 Tipi di tool comuni

| Tipo | Descrizione | Esempio |
|------|-------------|---------|
| **Retrieval** | Recupera informazioni | Ricerca documenti, query database |
| **Computation** | Esegue calcoli | Calcolatrice, analisi dati |
| **API** | Chiama servizi esterni | Meteo, traduzione, email |
| **Action** | Esegue azioni | Crea file, invia notifiche |

### 1.5 Esempio completo: tool meteo

```python
import json
from openai import OpenAI

# 1. Implementazione
def get_weather(city: str, unit: str = "celsius") -> dict:
    """Restituisce il meteo di una città."""
    # Simulazione - in produzione si userebbe un'API reale
    weather_data = {
        "bologna": {"temp": 22, "condition": "soleggiato"},
        "milano": {"temp": 18, "condition": "nuvoloso"},
        "roma": {"temp": 25, "condition": "sereno"},
    }
    
    city_lower = city.lower()
    if city_lower not in weather_data:
        return {"error": f"Città {city} non trovata"}
    
    data = weather_data[city_lower]
    temp = data["temp"]
    
    if unit == "fahrenheit":
        temp = temp * 9/5 + 32
    
    return {
        "city": city,
        "temperature": temp,
        "unit": unit,
        "condition": data["condition"]
    }

# 2. Schema
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Restituisce le condizioni meteo attuali di una città",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Nome della città"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Unità di temperatura"
                }
            },
            "required": ["city"]
        }
    }
}

# 3. Utilizzo con OpenAI
client = OpenAI()

def call_with_weather_tool(user_message: str) -> str:
    """Chiama l'LLM con il tool meteo disponibile."""
    messages = [{"role": "user", "content": user_message}]
    
    # Prima chiamata - l'LLM decide se usare il tool
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=[weather_tool],
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message
    
    # Se l'LLM non vuole usare tool
    if not response_message.tool_calls:
        return response_message.content
    
    # Esegui i tool richiesti
    messages.append(response_message)
    
    for tool_call in response_message.tool_calls:
        function_args = json.loads(tool_call.function.arguments)
        result = get_weather(**function_args)
        
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })
    
    # Seconda chiamata - genera risposta finale
    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    return final_response.choices[0].message.content

# Test
print(call_with_weather_tool("Che tempo fa a Bologna?"))
```

---

## 2. Agenti: sistemi autonomi di ragionamento

### 2.1 Definizione

Un **agente** è un sistema che usa un LLM come "motore di ragionamento" per:

1. Analizzare un problema
2. Pianificare i passi necessari
3. Usare tool per eseguire azioni
4. Osservare i risultati
5. Iterare fino a raggiungere l'obiettivo

### 2.2 Differenza tra LLM con tool e agente

| Aspetto | LLM con tool | Agente |
|---------|--------------|--------|
| Esecuzione | Singola chiamata | Loop di ragionamento |
| Tool | Una chiamata per risposta | Multiple chiamate in sequenza |
| Stato | Stateless | Mantiene contesto |
| Obiettivo | Rispondere alla domanda | Raggiungere un goal |
| Autonomia | Limitata | Alta |

### 2.3 Architettura ReAct

L'architettura più usata per gli agenti è **ReAct** (Reasoning + Acting):

```
while not done:
    THOUGHT  → L'agente ragiona sul problema
    ACTION   → Decide quale tool usare (o se rispondere)
    OBSERVATION → Riceve il risultato del tool
    
    if can_answer:
        ANSWER → Genera la risposta finale
        done = True
```

### 2.4 Implementazione di un agente

```python
import os
import json
from openai import OpenAI

class Agent:
    """
    Agente che usa tool per rispondere a domande.
    """
    
    def __init__(self, tools: list, functions: dict, model: str = "gpt-4o-mini"):
        """
        Args:
            tools: Lista degli schemi JSON dei tool
            functions: Dizionario {nome_funzione: funzione}
            model: Modello OpenAI da usare
        """
        self.tools = tools
        self.functions = functions
        self.model = model
        self.client = OpenAI()
        self.max_iterations = 5
        
    def run(self, user_query: str, system_prompt: str = None, verbose: bool = True) -> str:
        """
        Esegue l'agente su una query.
        
        Args:
            user_query: Domanda dell'utente
            system_prompt: Prompt di sistema (opzionale)
            verbose: Se True, stampa i passi intermedi
        
        Returns:
            Risposta finale dell'agente
        """
        # Costruisci messaggi iniziali
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": user_query})
        
        # Loop di ragionamento
        for iteration in range(self.max_iterations):
            if verbose:
                print(f"\n--- Iterazione {iteration + 1} ---")
            
            # Chiamata all'LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None
            )
            
            response_message = response.choices[0].message
            
            # Se non ci sono tool call, abbiamo la risposta
            if not response_message.tool_calls:
                if verbose:
                    print("Risposta finale generata")
                return response_message.content
            
            # Aggiungi la risposta ai messaggi
            messages.append(response_message)
            
            # Esegui ogni tool richiesto
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if verbose:
                    print(f"ACTION: {function_name}({function_args})")
                
                # Esegui la funzione
                if function_name in self.functions:
                    result = self.functions[function_name](**function_args)
                else:
                    result = {"error": f"Funzione {function_name} non trovata"}
                
                if verbose:
                    print(f"OBSERVATION: {result}")
                
                # Aggiungi il risultato ai messaggi
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
        
        return "Limite iterazioni raggiunto."
```

### 2.5 Esempio: agente multi-tool

```python
import math

# Tool 1: Meteo
def get_weather(city: str) -> dict:
    weather_data = {
        "bologna": {"temp": 22, "condition": "soleggiato"},
        "milano": {"temp": 18, "condition": "nuvoloso"},
    }
    return weather_data.get(city.lower(), {"error": "Città non trovata"})

weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Ottiene il meteo di una città",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "Nome della città"}
            },
            "required": ["city"]
        }
    }
}

# Tool 2: Calcolatrice
def calculate(expression: str) -> dict:
    allowed = {"sqrt": math.sqrt, "pow": pow, "pi": math.pi}
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Esegue calcoli matematici",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Espressione matematica"}
            },
            "required": ["expression"]
        }
    }
}

# Crea l'agente
agent = Agent(
    tools=[weather_tool, calculator_tool],
    functions={
        "get_weather": get_weather,
        "calculate": calculate
    }
)

# Test
response = agent.run("Se a Bologna ci sono 22 gradi, quanto fa il quadrato della temperatura?")
print(response)
```

---

## 3. RAG agentico: retrieval intelligente

### 3.1 Definizione

Un **RAG agentico** è un sistema dove un agente decide autonomamente:

- **Se** cercare informazioni
- **Cosa** cercare (può riformulare la query)
- **Quante volte** cercare
- **Come** combinare i risultati

### 3.2 Confronto: RAG classico vs RAG agentico

| Aspetto | RAG classico | RAG agentico |
|---------|--------------|--------------|
| Ricerca | Sempre | Solo se necessario |
| Query | Diretta dall'utente | Può essere riformulata |
| Iterazioni | Una sola | Multiple se serve |
| Flusso | Fisso | Dinamico |
| Altri tool | No | Sì |

### 3.3 Architettura

**RAG classico:**
```
Query → Embedding → Vector Search → Chunks → LLM → Risposta
```

**RAG agentico:**
```
Query → Agente → [Analizza se serve ricerca]
              ↓
        [Sì: Tool search_documents]
              ↓
        [Analizza risultati]
              ↓
        [Serve altra ricerca?]
              ↓
        [Genera risposta]
```

### 3.4 Vantaggi del RAG agentico

1. **Efficienza**: non esegue ricerche inutili (es: per "Ciao")
2. **Precisione**: può riformulare query ambigue
3. **Completezza**: ricerche multiple per domande complesse
4. **Flessibilità**: combina ricerca con altri tool (calcoli, API)
5. **Contestualità**: ricorda la conversazione precedente

### 3.5 Implementazione del tool di ricerca

```python
from datapizza.vectorstores.qdrant import QdrantVectorstore
from datapizza.embedders.openai import OpenAIEmbedder

# Setup
vectorstore = QdrantVectorstore(location=None, path="./qdrant_data")
embedder = OpenAIEmbedder(api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-small")

def search_documents(query: str, num_results: int = 3) -> dict:
    """
    Cerca informazioni nei documenti indicizzati.
    
    Args:
        query: Testo da cercare
        num_results: Numero di risultati (default: 3)
    
    Returns:
        Dizionario con i chunk trovati
    """
    try:
        query_embedding = embedder.embed(query)
        
        results = vectorstore.search(
            query_vector=query_embedding,
            collection_name="docs",
            k=num_results
        )
        
        if not results:
            return {"found": False, "message": "Nessun documento trovato"}
        
        chunks = []
        for i, chunk in enumerate(results):
            chunks.append({
                "index": i + 1,
                "text": chunk.text[:500] + "..." if len(chunk.text) > 500 else chunk.text
            })
        
        return {"found": True, "num_results": len(chunks), "chunks": chunks}
        
    except Exception as e:
        return {"found": False, "error": str(e)}

# Schema del tool
search_tool = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": "Cerca informazioni nei documenti aziendali. Usa per domande su contenuti specifici.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Testo da cercare"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Numero di risultati (default: 3)"
                }
            },
            "required": ["query"]
        }
    }
}
```

### 3.6 Implementazione dell'agente RAG

```python
class RAGAgent:
    """
    Agente RAG che decide autonomamente quando cercare.
    """
    
    SYSTEM_PROMPT = """Sei un assistente esperto dei documenti aziendali.

Hai accesso al tool search_documents per cercare nei documenti.

Regole:
1. Usa search_documents SOLO per domande sui contenuti aziendali
2. Per domande generiche (saluti, ecc.) rispondi direttamente
3. Se la ricerca non trova risultati, prova a riformulare
4. Basa le risposte ESCLUSIVAMENTE sui documenti trovati
5. Se non trovi info, dillo chiaramente

Rispondi sempre in italiano."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI()
        self.tools = [search_tool]
        self.functions = {"search_documents": search_documents}
        self.max_iterations = 3
        self.history = []
    
    def reset(self):
        """Resetta la cronologia."""
        self.history = []
    
    def chat(self, message: str, verbose: bool = True) -> str:
        """
        Invia un messaggio e ottieni risposta.
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ] + self.history + [
            {"role": "user", "content": message}
        ]
        
        for _ in range(self.max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Risposta finale
            if not response_message.tool_calls:
                final = response_message.content
                self.history.append({"role": "user", "content": message})
                self.history.append({"role": "assistant", "content": final})
                return final
            
            # Esegui tool
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                
                if verbose:
                    print(f"Ricerca: \"{args.get('query', '')}\"")
                
                result = self.functions[tool_call.function.name](**args)
                
                if verbose:
                    found = result.get("found", False)
                    print(f"   Trovati: {result.get('num_results', 0)} risultati" if found else "   Nessun risultato")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })
        
        return "Non sono riuscito a trovare una risposta."

# Uso
agent = RAGAgent()

# Domanda sui documenti → usa il tool
print(agent.chat("Quanti dipendenti IT ci sono?"))

# Saluto → risponde direttamente
agent.reset()
print(agent.chat("Ciao!"))
```

---

## 4. Implementazione pratica

### 4.1 Setup del progetto

```bash
# Installa dipendenze
uv add openai python-dotenv datapizza-ai qdrant-client

# Crea .env
echo "OPENAI_API_KEY=sk-..." > .env
```

### 4.2 Struttura consigliata

```
progetto/
├── agents/
│   ├── __init__.py
│   ├── base.py          # Classe Agent base
│   └── rag_agent.py     # RAGAgent
├── tools/
│   ├── __init__.py
│   ├── search.py        # Tool di ricerca
│   ├── calculator.py    # Tool calcolatrice
│   └── schemas.py       # Schemi JSON dei tool
├── vectorstore/
│   ├── __init__.py
│   └── setup.py         # Setup Qdrant
├── main.py
└── .env
```

### 4.3 Tool riutilizzabili

```python
# tools/schemas.py
from typing import Callable, TypedDict

class Tool(TypedDict):
    schema: dict
    function: Callable

def create_tool(name: str, description: str, parameters: dict, function: Callable) -> Tool:
    """Factory per creare tool."""
    return {
        "schema": {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        },
        "function": function
    }
```

### 4.4 Agent configurabile

```python
# agents/base.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class AgentConfig:
    model: str = "gpt-4o-mini"
    max_iterations: int = 5
    temperature: float = 0.7
    system_prompt: Optional[str] = None

class ConfigurableAgent:
    def __init__(self, tools: list, functions: dict, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.tools = tools
        self.functions = functions
        self.client = OpenAI()
        self.history = []
    
    # ... implementazione
```

---

## 5. Best practice e pattern comuni

### 5.1 Design dei tool

- **Descrizioni chiare**: l'LLM usa la descrizione per decidere quando usare il tool
- **Parametri tipizzati**: usa `enum` per valori finiti, `integer` per numeri
- **Gestione errori**: restituisci sempre un dizionario con campo `error` se fallisce
- **Risultati strutturati**: usa un formato consistente per i risultati

```python
# Buon esempio
def search_documents(query: str, limit: int = 5) -> dict:
    try:
        results = do_search(query, limit)
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### 5.2 Prompt engineering per agenti

```python
AGENT_PROMPT = """Sei un assistente AI con accesso a tool.

## Comportamento
- Ragiona passo passo prima di agire
- Usa i tool solo quando necessario
- Se non trovi informazioni, dillo chiaramente

## Tool disponibili
- search_documents: cerca nei documenti aziendali
- calculate: esegue calcoli matematici

## Regole
1. Per saluti e domande generiche, rispondi direttamente
2. Per domande sui documenti, usa search_documents
3. Per calcoli, usa calculate
4. Non inventare informazioni"""
```

### 5.3 Gestione della memoria

```python
class AgentWithMemory:
    def __init__(self):
        self.short_term = []  # Conversazione corrente
        self.long_term = {}   # Fatti importanti
    
    def remember(self, key: str, value: str):
        """Salva un fatto nella memoria a lungo termine."""
        self.long_term[key] = value
    
    def get_context(self) -> str:
        """Genera contesto dalla memoria."""
        facts = "\n".join([f"- {k}: {v}" for k, v in self.long_term.items()])
        return f"Fatti noti:\n{facts}" if facts else ""
```

### 5.4 Pattern multi-agente

Per task complessi, usa agenti specializzati:

```python
class OrchestratorAgent:
    """Agente che coordina altri agenti specializzati."""
    
    def __init__(self):
        self.researcher = RAGAgent()     # Cerca informazioni
        self.calculator = MathAgent()    # Fa calcoli
        self.writer = WriterAgent()      # Genera testo
    
    def solve(self, task: str) -> str:
        # 1. Analizza il task
        analysis = self.analyze(task)
        
        # 2. Delega agli agenti specializzati
        if analysis.needs_research:
            info = self.researcher.chat(analysis.research_query)
        
        if analysis.needs_calculation:
            calc = self.calculator.calculate(analysis.expression)
        
        # 3. Genera risposta finale
        return self.writer.compose(info, calc, task)
```

### 5.5 Logging e debugging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

class DebugAgent(Agent):
    def run(self, query: str) -> str:
        logger.info(f"Query: {query}")
        
        for i, step in enumerate(self.execute_steps(query)):
            logger.info(f"Step {i+1}: {step.action}")
            logger.debug(f"Tool args: {step.args}")
            logger.debug(f"Result: {step.result}")
        
        logger.info(f"Final response generated")
        return self.response
```

---

## Riferimenti

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Documentazione datapizza-ai](https://docs.datapizza.ai)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)

