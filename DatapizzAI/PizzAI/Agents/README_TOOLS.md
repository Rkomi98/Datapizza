# Multi‑Tool Framework - Datapizza-AI

Guida per creare e usare strumenti (tools) con Datapizza-AI. 

## Indice

1. [Struttura base di un tool](#struttura-base-di-un-tool)
2. [Esecuzione minimale con invoke](#esecuzione-minimale-con-invoke)
3. [Client multi‑tool](#client-multi-tool)
4. [Conversazione con memoria](#conversazione-con-memoria)
5. [Esempio con Google Search](#esempio-completo-con-google-search)
6. [Perché intervenire manualmente sui tool](#perche-intervenire-manualmente-sui-tool)

## Struttura base di un tool

```python
from datapizza.tools import tool


@tool
def timer_tool(duration: str) -> str:
    """Imposta un timer (es. "5 minutes")."""
    # DO something (stub)
    return f"Timer impostato per {duration}"
```

## Esecuzione minimale con invoke

Il modo più semplice per usare un tool è passarlo direttamente al metodo `invoke`. Il modello deciderà se e come usarlo in base al prompt.

```python
from dotenv import load_dotenv
import os

load_dotenv()

from datapizza.clients.openai import OpenAIClient
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

Esempio con due strumenti: una calcolatrice e una ricerca informazioni molto semplice.

```python
from datapizza.tools import tool


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

Che poi si integrano così:

```python
from dotenv import load_dotenv
import os

load_dotenv()

from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE
client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

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
In `datapizza-ai` è implementato il tool di ricerca `Google_search_tool`, che funziona solo con `GoogleClient`.

```python
import os
from dotenv import load_dotenv

load_dotenv()

from datapizza.clients.google import GoogleClient

client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)

response = client.invoke("Quando iniziano le olimpiadi invernali?", tools=[google_search_tool])

print(response.text)
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
        result_obj = tools_map[tool_name](**args)
        result = result_obj.text if hasattr(result_obj, "text") else str(result_obj)

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
