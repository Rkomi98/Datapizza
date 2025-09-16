# Multi‑Tool Framework - DatapizzAI

Guida concisa per creare e usare strumenti (tools) con DatapizzAI. I tools consentono al modello di compiere azioni (esecuzione di funzioni Python) durante il ragionamento.

## Indice

1. [Struttura base di un tool](#struttura-base-di-un-tool)
2. [Esecuzione minimale con invoke](#esecuzione-minimale-con-invoke)
3. [Client multi‑tool](#client-multi-tool)
4. [Conversazione con memoria](#conversazione-con-memoria)
5. [Best practices](#best-practices)
6. [Guida passo‑passo: tool custom](#guida-passo-passo-tool-custom)
## Struttura base di un tool

```python
from datapizzai.tools import tool

@tool
def timer_tool(duration: str) -> str:
    """Imposta un timer (es. "5 minutes")."""
    # DO something (stub)
    return f"Timer impostato per {duration}"
```

## Esecuzione minimale con invoke

```python
from datapizzai.clients import ClientFactory
from dotenv import load_dotenv
import os

load_dotenv()
client = ClientFactory.create(
    provider="openai", 
    api_key=os.getenv("OPENAI_API_KEY"), 
    model="gpt-5",
    temperature=1
    )

response = client.invoke(
    "Set a timer for 5 minutes",
    tools=[timer_tool],
    tool_choice="auto"
)

print(response.text)  # Qualsiasi risposta testuale
for f_call in response.function_calls or []:
    # Esegui il tool locale con gli argomenti suggeriti
    result = timer_tool(**(f_call.arguments or {}))
    print("tool result:", result)
```

## Client multi‑tool

Esempio con due strumenti: una calcolatrice e una ricerca informazioni.

```python
from datapizzai.tools import tool

@tool
def calcolatrice(expr: str) -> str:
    """Esegue calcoli semplici in modo sicuro (demo)."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(expr) <= allowed:
            return "Errore: caratteri non validi"
        return str(eval(expr))
    except Exception as e:
        return f"Errore: {e}"

@tool
def cerca_informazioni(query: str) -> str:
    """Dummy search (esempio)."""
    return f"(risultati sintetici per: {query})"
```

### Esecuzione

```python
# Client e Memory  
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import FunctionCallResultBlock, ROLE
from dotenv import load_dotenv
import os

load_dotenv()
client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

tools = [calcolatrice, cerca_informazioni]
memory = Memory()

response = client.invoke(
    input="Calcola (25 * 4) + 10 e cerca informazioni su Python type hints",
    tools=tools,
    tool_choice="auto",
    memory=memory
)

# Esecuzione iterativa dei function call
while hasattr(response, "function_calls") and response.function_calls:
    # Aggiungi la risposta dell'assistant alla memoria
    memory.add_turn(response.content, ROLE.ASSISTANT)
    
    # Crea i risultati dei tool e aggiungili uno per volta alla memoria
    for f_call in response.function_calls:
        tool_name = f_call.name
        args = f_call.arguments or {}
        
        if tool_name == "calcolatrice":
            result = calcolatrice(**args)
        elif tool_name == "cerca_informazioni":
            result = cerca_informazioni(**args)
        else:
            result = f"Tool sconosciuto: {tool_name}"

        tool_result_block = FunctionCallResultBlock(
            id=f_call.id,
            tool=f_call.tool,
            result=result,
        )
        
        # Aggiungi ogni tool result come turn separato con ruolo TOOL
        memory.add_turn([tool_result_block], ROLE.TOOL)

    # Re-invoca con la memoria aggiornata
    response = client.invoke(
        input="",
        tools=tools,
        tool_choice="auto",
        memory=memory
    )

print(response.text)
```

## Conversazione con memoria

Ora uniamo tutto in un ciclo conversazionale minimal e verosimile.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

def create_conversational_client():
    memory = Memory()
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
    )
    return client, memory

# 3. Configura conversazione multi-turno
client, memory = create_conversational_client()
tools = [calcolatrice, cerca_informazioni]

def chat_turn(user_input, memory, client, tools):
    """Gestisce un singolo turno di conversazione con tools"""
    print(f"👤 Utente: {user_input}")
    
    # Aggiungi input utente alla memoria
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Prima chiamata al modello
    response = client.invoke(
        input="",  # Input vuoto perché usiamo la memory
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )
    
    # Gestione iterativa dei function calls
    while hasattr(response, "function_calls") and response.function_calls:
        print("🔧 Esecuzione tool calls...")
        
        # Aggiungi la risposta dell'assistant alla memoria
        memory.add_turn(response.content, ROLE.ASSISTANT)
        
        # Esegui ogni function call
        for f_call in response.function_calls:
            print(f"   📞 {f_call.name}({f_call.arguments})")
            
            # Esegui il tool (il tuo codice esistente va bene)
            result = {
                "calcolatrice": calcolatrice,
                "cerca_informazioni": cerca_informazioni,
            }.get(f_call.name, lambda **_: f"Tool sconosciuto: {f_call.name}")(**(f_call.arguments or {}))
            
            print(f"   ✅ {result}")
            
            # Crea il blocco risultato
            tool_result_block = FunctionCallResultBlock(
                id=f_call.id, 
                tool=f_call.tool, 
                result=result
            )
            memory.add_turn([tool_result_block], ROLE.TOOL)
        response = client.invoke(
            input="",
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )
    
    # Aggiungi la risposta finale alla memoria
    if response.text:
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {response.text}")

# 4. Esempio di conversazione multi-turno
conversation = [
    "Ciao! Sono Mirko, sto lavorando su un progetto AI",
    "Cerca informazioni sui framework Python per AI",
    "Calcola il costo se spendo 500€ al mese per 2 anni",
    "Ricordi il mio nome e cosa sto facendo?"
]

for user_input in conversation:
    chat_turn(user_input, memory, client, tools)
    print()  # Spazio tra turni

# 5. Statistiche conversazione
print(f"📊 Turni totali: {len(memory.memory)}")
print(f"💬 Blocchi totali: {len(list(memory.iter_blocks()))}")
```

<!-- Sezione esempi ripetitivi rimossa per evitare ridondanza -->


## Best practices

### Design dei tool
- **Nome descrittivo**: Usa nomi chiari e specifici
- **Descrizione dettagliata**: Spiega esattamente cosa fa il tool
- **Schema input chiaro**: Definisci precisamente il formato di input
- **Gestione errori**: Gestisci sempre le eccezioni e restituisci ToolResult appropriati

### Esempio completo con Google Search

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools.google import google_search_tool

load_dotenv()

client = ClientFactory.create(
    provider="google",
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
)

response = client.invoke("Quando iniziano le olimpiadi invernali?", tools=[google_search_tool])

print(response.text)
```
