# Multi‑Tool Framework - DatapizzAI

Guida per creare e usare strumenti (tools) con DatapizzAI. 

## Indice

1. [Struttura base di un tool](#struttura-base-di-un-tool)
2. [Esecuzione minimale con invoke](#esecuzione-minimale-con-invoke)
3. [Client multi‑tool](#client-multi-tool)
4. [Conversazione con memoria](#conversazione-con-memoria)
5. [Esempio con Google Search](#esempio-completo-con-google-search)
6. [Perché intervenire manualmente sui tool](#perche-intervenire-manualmente-sui-tool)

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
from datapizzai.clients import OpenAIClient
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"), 
    model="gpt-5",
    temperature=1
)

response = client.invoke(
    "Set a timer for 5 minutes",
    tools=[timer_tool],
    tool_choice="auto"
)

print(response.text)
for f_call in response.function_calls or []:
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
from datapizzai.clients import OpenAIClient
from datapizzai.memory import Memory
from datapizzai.type import FunctionCallResultBlock, ROLE
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAIClient(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

tools = [calcolatrice, cerca_informazioni]
memory = Memory()

response = client.invoke(
    input="Calcola (25 * 4) + 10 e cerca informazioni su Python type hints",
    tools=tools,
    tool_choice="auto",
    memory=memory
)
while hasattr(response, "function_calls") and response.function_calls:
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

## Esempio completo con Google Search

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import GoogleClient
from datapizzai.tools.google import google_search_tool

load_dotenv()

client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)

response = client.invoke("Quando iniziano le olimpiadi invernali?", tools=[google_search_tool])

print(response.text)
```

## Conversazione con memoria

Chatbot interattivo con tools che continua fino a quando l'utente digita "fine":

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import GoogleClient
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE, FunctionCallResultBlock
from datapizzai.tools import tool
from datapizzai.tools.google import google_search_tool

load_dotenv()

# Calcolatrice semplice
@tool
def calcolatrice(expr: str) -> str:
    """Esegue calcoli matematici semplici in modo sicuro."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(expr) <= allowed:
            return "Errore: caratteri non validi nel calcolo"
        result = eval(expr)
        return f"Risultato: {result}"
    except Exception as e:
        return f"Errore nel calcolo: {e}"

# Client Gemini con tools
client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
)

tools = [calcolatrice, google_search_tool]
memory = Memory()

print("🤖 Chatbot con tools avviato! Scrivi 'fine' per uscire.")
print("Posso fare calcoli e cercare informazioni sul web.")

while True:
    # Input utente
    user_input = input("\n👤 Tu: ").strip()
    
    # Controlla condizioni di uscita
    if user_input.lower() in ["fine", "end", "exit", "quit", "esci"]:
        print("👋 Arrivederci!")
        break
    
    if not user_input:
        continue
        
    # Aggiungi input utente alla memoria
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    try:
        # Invoca il modello con tools
        response = client.invoke(
            input="",
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )
        
        # Gestisci function calls se presenti
        while hasattr(response, "function_calls") and response.function_calls:
            # Aggiungi risposta assistant alla memoria
            memory.add_turn(response.content, ROLE.ASSISTANT)
            
            # Esegui ogni function call
            for f_call in response.function_calls:
                tool_name = f_call.name
                args = f_call.arguments or {}
                
                print(f"🔧 Uso tool: {tool_name}")
                
                # Esegui il tool appropriato
                if tool_name == "calcolatrice":
                    result = calcolatrice(**args)
                elif tool_name == "google_search_tool":
                    result = google_search_tool(**args)
                else:
                    result = f"Tool sconosciuto: {tool_name}"
                
                # Aggiungi risultato alla memoria
                tool_result_block = FunctionCallResultBlock(
                    id=f_call.id,
                    tool=f_call.tool,
                    result=result,
                )
                memory.add_turn([tool_result_block], ROLE.TOOL)
            
            # Richiama il modello con i risultati dei tools
            response = client.invoke(
                input="",
                memory=memory,
                tools=tools,
                tool_choice="auto"
            )
        
        # Mostra risposta finale
        if response.text:
            print(f"🤖 Assistant: {response.text}")
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        print("Riprova con una domanda diversa.")
```


## Perché intervenire manualmente sui tool

I tool mantengono l'umano nel loop: ogni volta che il modello propone una `function_call` puoi decidere se eseguirla, modificarla o bloccarla.

### Quando conviene intervenire
- **Operazioni irreversibili o sensibili**: cancellazioni, scritture su filesystem, transazioni
- **Parametri incerti**: il modello potrebbe allucinare percorsi, ID o query; serve validazione
- **Vincoli esterni**: rate limiting, permessi per utente/ruolo, policy aziendali
- **Costi e performance**: chiamate costose (es. API a pagamento) da eseguire solo se davvero necessarie
- **Esperienza utente**: vuoi confermare o riformulare l'azione prima di procedere

Per task idempotenti e a basso rischio (es. piccole trasformazioni di stringhe) puoi invece lasciare l'esecuzione completamente automatica.

### Flusso di gestione consigliato
1. Ispeziona `response.function_calls` e identifica lo strumento richiesto
2. Valida che i parametri siano completi, coerenti e autorizzati
3. Esegui il tool o nega l'operazione motivandolo al modello
4. Restituisci il risultato (o l'errore) al modello tramite `FunctionCallResultBlock`

### Esempio di gating personalizzato
```python
# Funzioni helper definite da te
tools_map = {
    "web_search": web_search,
    "file_delete": file_delete,
}

for f_call in response.function_calls or []:
    tool_name = f_call.name
    args = f_call.arguments or {}

    if tool_name == "file_delete":
        result = "Operazione bloccata: richiede approvazione esplicita"
    elif not params_are_valid(args):
        result = "Parametri non validi o incompleti"
    else:
        result = tools_map[tool_name](**args)

    tool_result = FunctionCallResultBlock(
        id=f_call.id,
        tool=f_call.tool,
        result=result,
    )
    memory.add_turn([tool_result], ROLE.TOOL)
```
Quindi, in conclusione, quando e perché conviene usarlo?
- **Governance**: puoi applicare policy diverse in base a chi sta usando l'assistente
- **Osservabilità**: log controllato su quando e perché un tool viene autorizzato o negato
- **Recupero rapido**: fornisci al modello messaggi mirati per riprovare con parametri corretti
- **Tutela dei sistemi**: eviti effetti collaterali su risorse critiche o dati sensibili
