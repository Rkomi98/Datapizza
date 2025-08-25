# Multi Tool Framework - DatapizzAI

Guida completa per la creazione e utilizzo di client multi-tool con il framework datapizzai. I client possono utilizzare diversi strumenti per completare task complessi e automatizzare workflow attraverso l'API OpenAI.

## Indice

1. [Concetti fondamentali](#concetti-fondamentali)
2. [Struttura base di un Tool](#struttura-base-di-un-tool)
3. [Configurazione passo-passo](#configurazione-passo-passo)
   - [Passo 1: Definizione dei tool](#passo-1-definizione-dei-tool)
   - [Passo 2: Creazione del client OpenAI](#passo-2-creazione-del-client-openai)
   - [Passo 3: Configurazione ed esecuzione](#passo-3-configurazione-ed-esecuzione)
   - [Passo 4: Agente multi-tool avanzato](#passo-4-agente-multi-tool-avanzato)
   - [Passo 5: Memoria conversazionale](#passo-5-memoria-conversazionale)
4. [Esempi di strumenti implementati](#esempi-di-strumenti-implementati)
5. [Pattern di utilizzo avanzati](#pattern-di-utilizzo-avanzati)
6. [Best practices](#best-practices)
7. [Estensione del framework](#estensione-del-framework)
8. [Riepilogo configurazione completa](#riepilogo-configurazione-completa)

## Concetti fondamentali

### Client con Tool
Un client è un'interfaccia AI che può utilizzare strumenti per completare task. Ogni client ha:
- **Provider**: Connessione al modello AI (OpenAI, Google, etc.)
- **Model**: Modello specifico (gpt-4o, gemini, etc.)
- **System Prompt**: Istruzioni per il comportamento del client
- **Tools**: Lista di strumenti disponibili per l'invocazione

### Strumento (Tool)
Un tool è una funzione Python decorata con `@Tool` che il client può invocare. Ogni tool ha:
- **Nome**: Identificativo univoco
- **Descrizione**: Spiegazione di cosa fa il tool (dal docstring)
- **Parametri**: Definiti dalla signature della funzione
- **Return**: Valore restituito dalla funzione

## Struttura base di un Tool

```python
from datapizzai.tools import Tool

@Tool
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

I tool sono funzioni Python decorate con `@Tool` che il client OpenAI può invocare:

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools import Tool

# Carica variabili d'ambiente
load_dotenv()

@Tool
def calcola(espressione: str) -> str:
    """Esegue calcoli matematici sicuri.
    
    Args:
        espressione: Espressione matematica (es: "2 + 3 * 4")
    
    Returns:
        Risultato del calcolo o messaggio di errore
    """
    try:
        # Validazione sicurezza
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in espressione):
            return "Errore: Caratteri non permessi"
        
        result = eval(espressione)
        return f"Risultato: {result}"
    except Exception as e:
        return f"Errore: {str(e)}"
```

### Passo 2: Creazione del client OpenAI

Il client gestisce la connessione all'API OpenAI e la logica di function calling:

```python
def create_calculator_client():
    """Crea un client specializzato in calcoli matematici."""
    
    client = ClientFactory.create(
        provider="openai",                    # Provider AI
        api_key=os.getenv("OPENAI_API_KEY"),  # API key da .env
        model="gpt-4o",                       # Modello OpenAI
        system_prompt="""Sei un assistente matematico esperto.
        Usa sempre lo strumento 'calcola' per eseguire operazioni matematiche.
        Fornisci spiegazioni chiare e dettagliate."""
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
tools = [calcola]

# 3. Esegui query con tool automatico
response = client.invoke(
    input="Calcola l'area di un quadrato con lato 5",
    tools=tools,
    tool_choice="auto"  # OpenAI sceglie automaticamente quando usare i tool
)

# 4. Gestisci i risultati
def execute_tool_calls(response, available_tools):
    """Esegue i tool call e restituisce i risultati."""
    tool_results = []
    
    for block in response.content:
        if hasattr(block, 'name') and hasattr(block, 'arguments'):
            tool_name = block.name
            arguments = block.arguments
            
            print(f"🔧 Tool chiamato: {tool_name}")
            print(f"📋 Argomenti: {arguments}")
            
            # Esegui il tool
            if tool_name == "calcola":
                result = calcola(**arguments)
                tool_results.append(result)
                print(f"✅ Risultato: {result}")
    
    return tool_results

# 5. Esegui i tool e mostra risultati
tool_results = execute_tool_calls(response, tools)

# 6. Mostra risposta finale
if response.text.strip():
    print(f"🤖 Assistente: {response.text}")
elif tool_results:
    print(f"🤖 Assistente: {tool_results[0]}")
```

### Passo 4: Agente multi-tool avanzato

Per creare un agente con più strumenti, segui questi passaggi:

```python
# 1. Definisci strumenti aggiuntivi
@Tool
def cerca_informazioni(query: str) -> str:
    """Simula una ricerca web per trovare informazioni.
    
    Args:
        query: Termine di ricerca
    
    Returns:
        Risultati della ricerca simulata
    """
    query_lower = query.lower()
    
    if "python" in query_lower:
        results = [
            "Python è un linguaggio di programmazione interpretato",
            "Documentazione ufficiale: python.org",
            "Tutorial disponibili per principianti"
        ]
    elif "ai" in query_lower:
        results = [
            "Intelligenza Artificiale: campo dell'informatica",
            "Machine Learning è un sottoinsieme dell'AI",
            "Applicazioni: NLP, computer vision, robotica"
        ]
    else:
        results = [f"Risultati per '{query}' non disponibili in demo"]
    
    return f"Risultati per '{query}':\n" + "\n".join(f"- {r}" for r in results)

@Tool  
def gestisci_file(comando: str, percorso: str) -> str:
    """Gestisce file e directory in un sistema simulato.
    
    Args:
        comando: Operazione da eseguire (list, create, delete)
        percorso: Percorso del file o directory
    
    Returns:
        Risultato dell'operazione
    """
    # Simulazione file system
    files_system = {
        "docs/": ["README.md", "guide.txt"],
        "src/": ["main.py", "utils.py"],
        "data/": ["dataset.csv", "config.json"]
    }
    
    if comando == "list":
        if percorso in files_system:
            files = files_system[percorso]
            return f"Contenuto di {percorso}:\n" + "\n".join(f"- {f}" for f in files)
        return f"Directory {percorso} non trovata"
    
    elif comando == "create":
        return f"File {percorso} creato con successo"
    
    elif comando == "delete":
        return f"File {percorso} eliminato con successo"
    
    return f"Comando '{comando}' non supportato"

# 2. Crea client multi-tool
def create_multi_tool_client():
    """Crea un client con accesso a tutti gli strumenti."""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""Sei un assistente AI versatile con accesso a strumenti specializzati:

        - calcola: per operazioni matematiche
        - cerca_informazioni: per ricerche web simulate  
        - gestisci_file: per operazioni su file e directory

        Analizza ogni richiesta e scegli lo strumento più appropriato.
        Per task complessi, puoi usare più strumenti in sequenza.
        Spiega sempre cosa stai facendo e perché."""
    )
    
    return client

# 3. Configura tutti i tool
tools = [calcola, cerca_informazioni, gestisci_file]

# 4. Esegui workflow complessi
client = create_multi_tool_client()

complex_query = """
Esegui questo workflow:
1. Cerca informazioni su machine learning
2. Calcola quanti anni sono passati dal 1990 al 2025
3. Crea un file chiamato ml_summary.txt nella directory docs/
4. Lista i file nella directory docs/ per verificare
"""

response = client.invoke(
    input=complex_query,
    tools=tools,
    tool_choice="auto"
)

# Il modello OpenAI sceglierà automaticamente i tool necessari
tool_results = execute_tool_calls(response, tools)
```

Ripassiamo l'invocazione base per utilizzare il client

```python
# Query semplice con tool
response = client.invoke(
    input="Calcola 15 + 27 * 3",
    tools=tools,
    tool_choice="auto"
)

# Gestione dei tool call
def execute_tool_calls(response, available_tools):
    """Esegue i tool call presenti nella risposta"""
    tool_results = []
    
    for block in response.content:
        if hasattr(block, 'name') and hasattr(block, 'arguments'):
            tool_name = block.name
            arguments = block.arguments
            
            # Mappa dei tool disponibili
            tool_map = {
                "calcola": calcola,
                "cerca_informazioni": cerca_informazioni,
                "gestisci_file": gestisci_file
            }
            
            if tool_name in tool_map:
                result = tool_map[tool_name](**arguments)
                tool_results.append(result)
                print(f"🔧 {tool_name}: {result}")
    
    return tool_results

# Esegui i tool
tool_results = execute_tool_calls(response, tools)

# Query complessa con workflow multi-step
complex_query = """
    Esegui questo workflow:
    1. Cerca informazioni su Python
    2. Calcola 2^10
    3. Crea un file chiamato summary.txt
"""

response = client.invoke(
    input=complex_query,
    tools=tools,
    tool_choice="auto"
)
execute_tool_calls(response, tools)
```

### Passo 5: Memoria conversazionale

Per mantenere il contesto tra più turni di conversazione:

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

def create_conversational_agent():
    """Crea un agente con memoria conversazionale."""
    
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
client, memory = create_conversational_agent()
tools = [calcola, cerca_informazioni, gestisci_file]

def chat_turn(user_input: str, memory: Memory, client, tools):
    """Gestisce un singolo turno di conversazione."""
    
    print(f"👤 Utente: {user_input}")
    
    # Aggiungi input utente alla memoria
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Invoca il client con memoria e tool
    response = client.invoke(
        input="",  # Input vuoto perché usiamo la memoria
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )
    
    # Aggiungi risposta alla memoria
    memory.add_turn(response.content, ROLE.ASSISTANT)
    
    # Esegui eventuali tool call
    tool_results = execute_tool_calls(response, tools)
    
    # Mostra risposta
    if response.text.strip():
        print(f"🤖 Assistente: {response.text}")
    elif tool_results:
        print(f"🤖 Assistente: {tool_results[0]}")
    
    return response

# 4. Esempio di conversazione multi-turno
conversation = [
    "Ciao! Sono Marco, sto lavorando su un progetto AI",
    "Cerca informazioni sui framework Python per AI",
    "Calcola il costo se spendo 500€ al mese per 2 anni",
    "Crea un file di progetto chiamato ai_project.txt",
    "Ricordi il mio nome e cosa sto facendo?"
]

for user_input in conversation:
    chat_turn(user_input, memory, client, tools)
    print()  # Spazio tra turni

# 5. Statistiche conversazione
print(f"📊 Turni totali: {len(memory.memory)}")
print(f"💬 Blocchi totali: {len(list(memory.iter_blocks()))}")
```

## Esempi di strumenti implementati

### Tool: calcola
**Scopo**: Esegue calcoli matematici sicuri
**Input**: Espressione matematica come stringa
**Output**: Risultato del calcolo

```python
# Esempio di utilizzo diretto
result = calcola("(15 + 5) * 2")
print(result)  # "Risultato: 40"

# Esempio con client
response = client.invoke(
    input="Calcola l'area di un quadrato con lato 5",
    tools=[calcola],
    tool_choice="auto"
)
```

### Tool: cerca_informazioni
**Scopo**: Simula ricerche web

**Input**: Query di ricerca

**Output**: Risultati simulati

```python
# Esempio di utilizzo diretto
result = cerca_informazioni("Python programming")
print(result)  # Risultati simulati per Python

# Esempio con client
response = client.invoke(
    input="Cerca informazioni su machine learning",
    tools=[cerca_informazioni],
    tool_choice="auto"
)
```

### Tool: gestisci_file
**Scopo**: Gestisce file e directory (simulato)
**Input**: Comando e percorso
**Output**: Risultato dell'operazione

```python
# Esempio di utilizzo diretto
result = gestisci_file("list", "docs/")
print(result)  # Lista file in docs/

result = gestisci_file("create", "docs/new.txt")
print(result)  # Conferma creazione

# Esempio con client
response = client.invoke(
    input="Crea un file chiamato report.txt nella directory docs/",
    tools=[gestisci_file],
    tool_choice="auto"
)
```

## Pattern di utilizzo avanzati

### Workflow sequenziale
```python
# Il client può eseguire workflow complessi
workflow_query = """
    Esegui questo workflow:
    1. Cerca informazioni su machine learning
    2. Calcola quanti anni sono passati dal 1990 al 2025
    3. Crea un file chiamato ml_summary.txt
    4. Verifica che il file sia stato creato
"""

response = client.invoke(
    input=workflow_query,
    tools=[calcola, cerca_informazioni, gestisci_file],
    tool_choice="auto"
)
execute_tool_calls(response, tools)
```

### Selezione intelligente dello strumento
```python
# Il client sceglie automaticamente lo strumento appropriato
queries = [
    "Calcola 2 + 2",                    # → calcola
    "Cerca informazioni su AI",          # → cerca_informazioni
    "Crea un file chiamato test.txt",    # → gestisci_file
    "Quanto costa un progetto AI?"       # → cerca_informazioni + calcola
]

for query in queries:
    response = client.invoke(
        input=query,
        tools=tools,
        tool_choice="auto"
    )
    print(f"Query: {query}")
    tool_results = execute_tool_calls(response, tools)
    print(f"Tool utilizzati: {len(tool_results)}")
```

### Gestione errori e fallback
```python
# L'agente gestisce errori e fallback automaticamente
try:
    response = agent.invoke("Calcola qualcosa di complesso")
    
    # Verifica se sono stati usati strumenti
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"Strumento usato: {tool_call.tool_name}")
            print(f"Risultato: {tool_call.result}")
    
except Exception as e:
    print(f"Errore nell'invocazione: {e}")
```

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



## Riepilogo configurazione completa

### Checklist implementazione

✅ **Setup ambiente**
- [ ] Ambiente virtuale attivato
- [ ] Libreria datapizzai installata
- [ ] File `.env` configurato con OPENAI_API_KEY
- [ ] Test connessione OpenAI completato

✅ **Definizione tool**
- [ ] Tool decorati con `@Tool`
- [ ] Docstring complete con Args/Returns
- [ ] Gestione errori implementata
- [ ] Validazione input sicura

✅ **Configurazione client**
- [ ] ClientFactory con provider="openai"
- [ ] System prompt appropriato per il caso d'uso
- [ ] Modello selezionato (gpt-4o raccomandato)
- [ ] Parametri ottimizzazione configurati

✅ **Esecuzione tool**
- [ ] Funzione `execute_tool_calls` implementata
- [ ] Mappa tool configurata correttamente
- [ ] Gestione errori per tool non trovati
- [ ] Log delle operazioni attivo

✅ **Memoria conversazionale** (opzionale)
- [ ] Oggetto Memory inizializzato
- [ ] Turni aggiunti correttamente
- [ ] Gestione dimensione memoria
- [ ] Test conversazioni multi-turno

### Template completo

```python
#!/usr/bin/env python3
"""
Template completo per agente multi-tool con datapizzAI
"""

import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools import Tool
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

# 1. Setup ambiente
load_dotenv()

# 2. Definizione tool
@Tool
def my_tool(param: str) -> str:
    """Descrizione del tool."""
    try:
        # Logica del tool
        result = f"Processato: {param}"
        return result
    except Exception as e:
        return f"Errore: {str(e)}"

# 3. Configurazione client
def create_agent():
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="System prompt personalizzato..."
    )
    return client

# 4. Esecuzione tool
def execute_tool_calls(response, tools):
    tool_results = []
    tool_map = {"my_tool": my_tool}
    
    for block in response.content:
        if hasattr(block, 'name') and hasattr(block, 'arguments'):
            tool_name = block.name
            if tool_name in tool_map:
                result = tool_map[tool_name](**block.arguments)
                tool_results.append(result)
                print(f"🔧 {tool_name}: {result}")
    
    return tool_results

# 5. Main execution
def main():
    client = create_agent()
    tools = [my_tool]
    
    response = client.invoke(
        input="Query utente",
        tools=tools,
        tool_choice="auto"
    )
    
    tool_results = execute_tool_calls(response, tools)
    
    if response.text.strip():
        print(f"🤖 {response.text}")
    elif tool_results:
        print(f"🤖 {tool_results[0]}")

if __name__ == "__main__":
    main()
```

### Esempi demo interattive

Il file `multi_agent_tools.py` include demo complete:

```
MULTI TOOL FRAMEWORK - DatapizzAI
=================================================================

Demo disponibili:

1. Test strumenti individuali → Verifica funzionamento base
2. Client specializzato → Calculator client con strumento matematico
3. Client multi strumento → Research client con search + file
4. Workflow complesso → Client con tutti gli strumenti
5. Client con memoria → Conversazione multi-turno
6. Mostra strumenti → Lista e descrizioni

0. Esci
```



## Documentazione completa

→ **[multi_agent_tools.py](multi_agent_tools.py)** - Script completo con esempi funzionanti

→ **[GUIDA_MULTI_AGENT.md](GUIDA_MULTI_AGENT.md)** - Documentazione tecnica dettagliata (se disponibile)


