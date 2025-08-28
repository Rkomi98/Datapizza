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
client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-5")

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
# Client
from datapizzai.clients import ClientFactory
from dotenv import load_dotenv
import os

load_dotenv()
client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

tools = [calcolatrice, cerca_informazioni]

response = client.invoke(
    input="Calcola (25 * 4) + 10 e cerca informazioni su Python type hints",
    tools=tools,
    tool_choice="auto"
)

# Esecuzione iterativa dei function call
from datapizzai.type import FunctionCallResultBlock

while getattr(response, "function_calls", []):
    for f_call in response.function_calls:
        tool_name = f_call.name
        args = f_call.arguments or {}
        if tool_name == "calcolatrice":
            result = calcolatrice(**args)
        elif tool_name == "cerca_informazioni":
            result = cerca_informazioni(**args)
        else:
            result = f"Tool sconosciuto: {tool_name}"

        block = FunctionCallResultBlock(
            id=f_call.id,
            tool=tool_name,
            result=result,
        )

        # Re‑invoca con i risultati dei tool
        response = client.invoke(
            input="",
            tools=tools,
            tool_choice="auto",
            tool_results=[block]
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

def chat_turn(user_input: str, memory: Memory, client, tools):
    """Gestisce un turno: aggiorna memoria, invoca il client, esegue function calls."""
    
    print(f"👤 Utente: {user_input}")
    
    # Aggiungi input utente alla memoria
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Invoca il client con memoria e tool
    response = client.invoke(
        input="",
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )
    
    # Esecuzione tool iterativa finché necessario
    while getattr(response, "function_calls", []):
        for f_call in response.function_calls:
            result = {
                "calcolatrice": calcolatrice,
                "cerca_informazioni": cerca_informazioni,
            }.get(f_call.name, lambda **_: f"Tool sconosciuto: {f_call.name}")(**(f_call.arguments or {}))

            block = FunctionCallResultBlock(id=f_call.id, tool=f_call.name, result=result)

            response = client.invoke(
                input="",
                memory=memory,
                tools=tools,
                tool_choice="auto",
                tool_results=[block]
            )

    # Nessun tool: salva normalmente
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    print(f"🤖 Assistente: {response.text}")

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

### Gestione della memoria
- **Contesto persistente**: Usa la memoria per conversazioni multi-turno
- **Pulizia memoria**: Gestisci la dimensione della memoria per conversazioni lunghe
- **Separazione ruoli**: Mantieni chiara la distinzione tra utente e assistente



 
## Guida passo‑passo: tool custom

Questa guida mostra come creare, esporre e usare un tool personalizzato con la libreria datapizzai.

1. Definisci il tool con `@tool`
   ```python
   from datapizzai.tools import tool

   @tool
   def estrai_email(testo: str, dominio: str | None = None) -> list[str]:
       """Estrae email da un testo; opzionalmente filtra per dominio.

       Args:
           testo: Testo di input
           dominio: Se impostato, restituisce solo email che terminano con quel dominio

       Returns:
           Lista di email trovate
       """
       import re
       pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
       emails = re.findall(pattern, testo)
       if dominio:
           emails = [e for e in emails if e.endswith(dominio)]
       return emails
   ```

2. Crea il client
   ```python
   import os
   from dotenv import load_dotenv
   from datapizzai.clients import ClientFactory

   load_dotenv()
   client = ClientFactory.create(
       provider="openai",
       api_key=os.getenv("OPENAI_API_KEY"),
       model="gpt-4o",
   )
   tools = [estrai_email]
   ```

3. Invoca e gestisci i function call
   ```python
   response = client.invoke(
       input="Trova le email in questo testo: Contatti: a@example.com, b@test.org",
       tools=tools,
       tool_choice="auto"
   )

   from datapizzai.type import FunctionCallResultBlock
   while getattr(response, "function_calls", []):
       for f_call in response.function_calls:
           res = estrai_email(**(f_call.arguments or {}))
           response = client.invoke(
               input="",
               tools=tools,
               tool_choice="auto",
               tool_results=[FunctionCallResultBlock(id=f_call.id, tool=f_call.name, result=res)]
           )
   print(response.text)
   ```

### Esempio completo con Google Search

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools.google import google_search_tool

load_dotenv()

# Assicurati di avere GOOGLE_API_KEY nel file .env
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)

# Utilizzo diretto
response = client.invoke(
    "Chi ha vinto Wimbledon 2024?", 
    tools=[google_search_tool],
    tool_choice="auto"
)

from datapizzai.type import FunctionCallResultBlock
while getattr(response, "function_calls", []):
    for f_call in response.function_calls:
        res = google_search_tool(**(f_call.arguments or {}))
        response = client.invoke(
            input="",
            tools=[google_search_tool],
            tool_choice="auto",
            tool_results=[FunctionCallResultBlock(id=f_call.id, tool=f_call.name, result=res)]
        )
print(response.text)
```

Suggerimenti:
- Definisci sempre docstring chiare (Args/Returns) e valida l'input.
- Evita `eval` per casi reali; preferisci librerie sicure o parsing esplicito.
- Esegui iterativamente i function call finché non terminano, passando i risultati come blocchi `FunctionCallResultBlock`.
