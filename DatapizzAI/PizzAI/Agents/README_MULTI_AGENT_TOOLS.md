# Multi Tool Framework - DatapizzAI

Guida completa per la creazione e utilizzo di client multi-tool con il framework datapizzai. I client possono utilizzare diversi strumenti per completare task complessi e automatizzare workflow attraverso l'API OpenAI.

## Indice

1. [Concetti fondamentali](#concetti-fondamentali)
2. [Struttura base di un tool](#struttura-base-di-un-tool)
3. [Configurazione passo-passo](#configurazione-passo-passo)
   - [Passo 1: Definizione dei tool](#passo-1-definizione-dei-tool)
   - [Passo 2: Creazione del client OpenAI](#passo-2-creazione-del-client-openai)
   - [Passo 3: Configurazione ed esecuzione](#passo-3-configurazione-ed-esecuzione)
   - [Passo 4: Client multi-tool avanzato](#passo-4-client-multi-tool-avanzato)
   - [Passo 5: Conversazione con memoria](#passo-5-conversazione-con-memoria)
4. [Best practices](#best-practices)
5. [Estensione del framework](#estensione-del-framework)
6. [Guida passo-passo: tool custom](#guida-passo-passo-tool-custom)

## Concetti fondamentali

### Client con Tool
Un client è un'interfaccia AI che può utilizzare strumenti per completare task. Ogni client ha:
- **Provider**: Connessione al modello AI (OpenAI, Google, etc.)
- **Model**: Modello specifico (gpt-5, gemini 2.5 pro, etc.)
- **System Prompt**: Istruzioni per il comportamento del client
- **Tools**: Lista di strumenti disponibili per l'invocazione

### Strumento (tool)
Un tool è una funzione Python decorata con `@tool` che il client può invocare. Ogni tool ha:
- **Nome**: Identificativo univoco
- **Descrizione**: Spiegazione di cosa fa il tool (dal docstring)
- **Parametri**: Definiti dalla signature della funzione
- **Return**: Valore restituito dalla funzione

### Function calling in breve

Il function calling permette al modello di "chiamare" funzioni Python dichiarate come tool. In pratica:
- Definisci funzioni Python e le annoti con `@tool` (nome, descrizione, schema argomenti).
- Il modello, guidato dal system prompt e dal contesto, può restituire una richiesta strutturata a invocare un tool con specifici argomenti.
- Il runtime esegue davvero la funzione Python con quegli argomenti e restituisce l'output al modello o all'utente.
- Con `tool_choice="auto"` il modello decide quando usare i tool; in alternativa puoi forzare un tool specifico.

## Struttura base di un tool

```python
from datapizzai.tools import tool

@tool
def mio_tool(parametro: str) -> str:
    """Descrizione di cosa fa questo tool.
    
    Args:
        parametro: Descrizione del parametro
        
    Returns:
        Risultato dell'operazione
    """
    try:
        # Implementa la logica del tool
        result = process_input(parametro)
        return f"Risultato: {result}"
        
    except Exception as e:
        return f"Errore: {str(e)}"
```

## Configurazione passo-passo

### Passo 1: Definizione dei tool

I tool sono funzioni Python decorate con `@tool` che il client può invocare:

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools import tool
import re

# Carica variabili d'ambiente
load_dotenv()
ALLOWED_FUNCS = {
    # base & potenze/log
    "sqrt": np.sqrt, "log": np.log, "log10": np.log10, "exp": np.exp,
    "abs": abs, "round": round, "min": np.minimum, "max": np.maximum,
    # trig
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
}
ALLOWED_CONSTS = {"pi": math.pi, "e": math.e}
ALLOWED_BINOPS = {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow}
ALLOWED_UNARYOPS = {ast.UAdd, ast.USub}
MAX_EXPR_LEN, MAX_NODES = 2000, 800

def _normalize(s: str) -> str:
    s = s.strip()
    if len(s) > MAX_EXPR_LEN: raise ValueError("Espressione troppo lunga")
    s = s.replace("^", "**")                # potenza
    s = re.sub(r"√\s*\(", "sqrt(", s)       # radice simbolo → sqrt(
    s = re.sub(r"(\d)\s*π", r"\1*pi", s)    # 2π → 2*pi
    return s

def _safe_eval(node):
    if isinstance(node, ast.Expression): return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)): return node.value
        raise ValueError("Costante non numerica")
    if isinstance(node, ast.Name):
        if node.id in ALLOWED_CONSTS: return ALLOWED_CONSTS[node.id]
        raise ValueError(f"Identificatore non permesso: {node.id}")
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARYOPS:
        v = _safe_eval(node.operand); return +v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINOPS:
        a, b = _safe_eval(node.left), _safe_eval(node.right)
        if   isinstance(node.op, ast.Add): return a + b
        elif isinstance(node.op, ast.Sub): return a - b
        elif isinstance(node.op, ast.Mult): return a * b
        elif isinstance(node.op, ast.Div): return a / b
        elif isinstance(node.op, ast.FloorDiv): return a // b
        elif isinstance(node.op, ast.Mod): return a % b
        elif isinstance(node.op, ast.Pow):
            if isinstance(b, int) and abs(b) > 1000: raise ValueError("Esponente troppo grande")
            return a ** b
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and not node.keywords:
            fn = ALLOWED_FUNCS.get(node.func.id)
            if not fn: raise ValueError("Funzione non permessa")
            args = [_safe_eval(a) for a in node.args]
            if len(args) > 8: raise ValueError("Troppe argomentazioni")
            return fn(*args)
    raise ValueError("Sintassi non permessa")

@tool
def calcolatrice(espressione: str) -> str:
    try:
        src = _normalize(espressione)
        tree = ast.parse(src, mode="eval")             # guard complessità
        val = _safe_eval(tree)
        if isinstance(val, float) and val.is_integer(): val = int(val)  # output pulito
        print(val)
        return f"Risultato: {val}"
    except Exception as e:
        return f"Errore: {e}"
```

### Passo 2: Creazione del client OpenAI

Il client gestisce la connessione all'API OpenAI e la logica di function calling:

```python
def create_calculator_client():
    """Crea un client specializzato in calcoli matematici."""
    
    client = ClientFactory.create(
        provider="openai",                    # Provider AI
        api_key=os.getenv("OPENAI_API_KEY"),  # API key da .env
        model="gpt-5",                        # Modello OpenAI
        system_prompt="""Sei un assistente matematico esperto.
        Usa sempre lo strumento 'calcolatrice' per eseguire operazioni matematiche.
        Fornisci spiegazioni chiare e dettagliate.""",
        temperature=1,
    )
    
    if not client:
        raise ValueError("❌ Impossibile creare client OpenAI")
    
    return client
```

### Passo 3: Configurazione ed esecuzione

```python
# 1. Crea il client
client = create_calculator_client()

# 2. Definisci i tool disponibili
tools = [calcolatrice]

# 3. Esegui query con tool automatico
response = client.invoke(
    input="Sia $k = \lceil{\sqrt{m + n}}\rceil$, dove $n$ e $m$ sono due numeri distinti naturali minori di $100$. Trova il massimo valore di $k$",
    tools=tools,
    tool_choice="auto"  # OpenAI sceglie automaticamente quando usare i tool
)

# 4. Gestisci i risultati
def execute_tool_calls(response, available_tools):
    """Esegue i function call usando i tool passati (non il contenuto testuale)."""
    tool_results = []
    tool_map = {t.name: t for t in available_tools}

    for call in getattr(response, "function_calls", []) or []:
        tool_name = getattr(call, "name", None)
        arguments = getattr(call, "arguments", {}) or {}

        print(f"🔧 Tool chiamato: {tool_name}")
        print(f"📋 Argomenti: {arguments}")

        if tool_name in tool_map:
            result = tool_map[tool_name](**arguments)
            tool_results.append(result)
            print(f"✅ Risultato: {result}")
        else:
            print(f"⚠️ Tool sconosciuto: {tool_name}")
    
    return tool_results

# 5. Esegui i tool e mostra risultati
tool_results = execute_tool_calls(response, tools)

# 6. Mostra risposta finale
if response.text.strip():
    print(f"🤖 Assistente: {response.text}")
elif tool_results:
    print(f"🤖 Assistente: {tool_results[0]}")
```

### Passo 4: Client multi-tool avanzato

Per creare un client con più strumenti, segui questi passaggi:

```python
# 1. Utilizza il tool di ricerca Google integrato
from datapizzai.tools.google import google_search_tool

# Il google_search_tool è già pronto all'uso con datapizzai 3.0.8
# Richiede GOOGLE_API_KEY nel file .env per Google Custom Search API

# Esempio di utilizzo diretto:
# response = client.invoke("Chi ha vinto Wimbledon 2024?", tools=[google_search_tool])


# 2. Crea client multi-tool
def create_multi_tool_client():
    """Crea un client con accesso a tutti gli strumenti."""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""Sei un assistente AI versatile con accesso a strumenti specializzati:

        - calcolatrice: per operazioni matematiche
        - google_search_tool: per ricerche web reali tramite Google

        Analizza ogni richiesta e scegli lo strumento più appropriato.
        Per task complessi, puoi usare più strumenti in sequenza.
        Spiega sempre cosa stai facendo e perché."""
    )
    
    return client

# 3. Configura tutti i tool
tools = [calcolatrice, google_search_tool]

# 4. Esegui workflow complessi
client = create_multi_tool_client()

complex_query = """
Esegui questo workflow:
1. Calcola quanti anni sono passati dal 1990 al 2025
2. Cerca informazioni su "machine learning trends 2025"
"""

response = client.invoke(
    input=complex_query,
    tools=tools,
    tool_choice="auto"
)

# Il modello OpenAI sceglierà automaticamente i tool necessari
tool_results = execute_tool_calls(response, tools)
```

<!-- Sezione duplicata rimossa: l'invocazione base è già coperta nei passi precedenti -->

### Passo 5: Conversazione con memoria

Ora uniamo tutto in un ciclo conversazionale minimal e verosimile.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

def create_conversational_client():
    """Crea un client conversazionale con memoria."""
    
    # 1. Inizializza la memoria
    memory = Memory()
    
    # 2. Crea client con system prompt per conversazioni
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""Sei un assistente AI amichevole con memoria conversazionale.
        Ricorda i dettagli delle conversazioni precedenti e fai riferimento ad essi quando appropriato.
        Usa gli strumenti disponibili per aiutare l'utente con task specifici."""
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
    
    # NON aggiungere mai response.content alla memoria se ci sono function_calls
    tool_calls = getattr(response, "function_calls", []) or []
    
    if tool_calls:
        # Esegui i tool (riusa la tua funzione)
        tool_results = execute_tool_calls(response, tools)
    
        # Re-invoca passando i risultati come testo (niente tool_calls in memoria)
        followup = client.invoke(
            input="Usa questi risultati degli strumenti per completare la risposta:\n" + "\n".join(map(str, tool_results)),
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )
    
        # Aggiungi solo testo finale alla memoria
        memory.add_turn([TextBlock(content=followup.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistente: {followup.text}")
    
    else:
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

### System prompt dell'agente
- **Istruzioni chiare**: Spiega quando e come usare ogni strumento
- **Fallback**: Definisci cosa fare se nessuno strumento è appropriato
- **Output format**: Specifica il formato delle risposte desiderato

### Gestione della memoria
- **Contesto persistente**: Usa la memoria per conversazioni multi-turno
- **Pulizia memoria**: Gestisci la dimensione della memoria per conversazioni lunghe
- **Separazione ruoli**: Mantieni chiara la distinzione tra utente e assistente



## Estensione del framework

### Creazione di nuovi tool
```python
class DatabaseTool(Tool):
    """Tool per operazioni su database"""
    
    def __init__(self, connection_string: str):
        super().__init__(
            name="database",
            description="Esegue query su database",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "operation": {"type": "string", "enum": ["select", "insert", "update", "delete"]}
                }
            }
        )
        self.connection_string = connection_string
    
    def execute(self, input_data: Dict[str, str]) -> ToolResult:
        # Implementa logica database
        pass
```

### Tool con parametri di configurazione
```python
class APITool(Tool):
    """Tool per chiamate API esterne"""
    
    def __init__(self, base_url: str, api_key: str):
        super().__init__(
            name="api_client",
            description="Esegue chiamate API",
            input_schema={"type": "string"}
        )
        self.base_url = base_url
        self.api_key = api_key
    
    def execute(self, endpoint: str) -> ToolResult:
        # Implementa chiamata API
        pass
```



## Guida passo-passo: tool custom

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
       system_prompt=(
           "Sei un assistente che può usare strumenti. Se l'utente chiede estrazione di email, "
           "usa sempre lo strumento 'estrai_email'."
       ),
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

   def execute_tool_calls(response, available_tools):
       tool_map = {t.name: t for t in available_tools}
       results = []
       for call in getattr(response, "function_calls", []) or []:
           name = getattr(call, "name", "")
           args = getattr(call, "arguments", {}) or {}
           res = tool_map[name](**args) if name in tool_map else f"Tool sconosciuto: {name}"
           results.append(f"{name}: {res}")
       return results

   tool_results = execute_tool_calls(response, tools)

   # Se sono stati eseguiti tool, re-invoca passando i risultati come testo
   if tool_results:
       followup = client.invoke(
           input="Usa questi risultati degli strumenti per completare la risposta:\n" + "\n".join(tool_results),
           tools=tools,
           tool_choice="auto"
       )
       print(followup.text)
   else:
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
    system_prompt="Sei un assistente che può cercare informazioni su Google."
)

# Utilizzo diretto
response = client.invoke(
    "Chi ha vinto Wimbledon 2024?", 
    tools=[google_search_tool],
    tool_choice="auto"
)

# Gestisci i risultati come negli esempi precedenti
tool_results = execute_tool_calls(response, [google_search_tool])
if tool_results:
    followup = client.invoke(
        f"Usa questi risultati per rispondere: {tool_results[0]}",
        tools=[google_search_tool]
    )
    print(followup.text)
```

Suggerimenti:
- Definisci sempre docstring chiare (Args/Returns) e valida l'input.
- Evita `eval` per casi reali; preferisci librerie sicure o parsing esplicito.
- Se usi memoria conversazionale, non aggiungere alla memoria un messaggio assistant contenente tool_calls senza fornire prima i relativi messaggi di tool; in mancanza del supporto nativo ai messaggi "tool", reinvia i risultati come testo (come nell'esempio sopra).

