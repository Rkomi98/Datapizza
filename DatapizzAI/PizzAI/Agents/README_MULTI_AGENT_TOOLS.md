# Multi Agent-Tool Framework - DatapizzAI

Guida completa per la creazione e utilizzo di agenti multi-tool con il framework datapizzai. Gli agenti possono utilizzare diversi strumenti per completare task complessi e automatizzare workflow.

## Avvio rapido

```bash
# Attiva ambiente virtuale
cd PizzAI && source .venv/bin/activate

# Configura API key nel file .env
echo 'OPENAI_API_KEY=your-key-here' > .env

# Esegui gli esempi
cd Agents && python multi_agent_tools.py
```

## Concetti fondamentali

### Agente (Agent)
Un agente è un'entità AI che può utilizzare strumenti per completare task. Ogni agente ha:
- **Nome**: Identificativo univoco
- **Client**: Connessione al modello AI (OpenAI, Google, etc.)
- **Strumenti**: Lista di tool disponibili
- **System Prompt**: Istruzioni per il comportamento dell'agente

### Strumento (Tool)
Un tool è una funzione specializzata che l'agente può invocare. Ogni tool ha:
- **Nome**: Identificativo univoco
- **Descrizione**: Spiegazione di cosa fa il tool
- **Schema Input**: Definizione del formato di input richiesto
- **Metodo execute**: Logica di esecuzione del tool

### ToolResult
Risultato dell'esecuzione di un tool, contenente:
- **Success**: Boolean che indica se l'operazione è riuscita
- **Result**: Risultato dell'operazione (se success=True)
- **Error**: Messaggio di errore (se success=False)
- **Metadata**: Informazioni aggiuntive sull'operazione

## Struttura base di un Tool

```python
from datapizzai.tools import Tool, ToolResult

class MioTool(Tool):
    """Descrizione del tool"""
    
    def __init__(self):
        super().__init__(
            name="nome_tool",
            description="Cosa fa questo tool",
            input_schema={
                "type": "string",  # o "object", "number", etc.
                "description": "Descrizione dell'input richiesto"
            }
        )
    
    def execute(self, input_data) -> ToolResult:
        """Logica di esecuzione del tool"""
        try:
            # Implementa la logica del tool
            result = self.process_input(input_data)
            
            return ToolResult(
                success=True,
                result=result,
                metadata={"info": "dettagli aggiuntivi"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Errore: {str(e)}"
            )
```

## Creazione di un agente

### Agente con singolo strumento

```python
from datapizzai.clients import ClientFactory
from datapizzai.agents import Agent

# 1. Crea il client
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# 2. Crea lo strumento
calculator_tool = CalculatorTool()

# 3. Crea l'agente
agent = Agent(
    name="MathAgent",
    client=client,
    tools=[calculator_tool],
    system_prompt="""Sei un agente specializzato in calcoli matematici. 
    Usa sempre lo strumento calculator per eseguire calcoli."""
)
```

### Agente con più strumenti

```python
# Crea strumenti multipli
search_tool = WebSearchTool()
file_tool = FileManagerTool()
calc_tool = CalculatorTool()

# Crea agente con tutti gli strumenti
agent = Agent(
    name="MultiToolAgent",
    client=client,
    tools=[search_tool, file_tool, calc_tool],
    system_prompt="""Sei un agente versatile. 
    Analizza la richiesta e scegli lo strumento più appropriato."""
)
```

## Utilizzo dell'agente

### Invocazione base

```python
# Query semplice
response = agent.invoke("Calcola 15 + 27 * 3")
print(response.text)

# Query complessa
response = agent.invoke("""
    Esegui questo workflow:
    1. Cerca informazioni su Python
    2. Calcola 2^10
    3. Crea un file chiamato summary.txt
""")
```

### Invocazione con memoria

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

# Turno 1
memory.add_turn([TextBlock("Ciao, sono Marco")], ROLE.USER)
response = agent.invoke("", memory=memory)
memory.add_turn([TextBlock(response.text)], ROLE.ASSISTANT)

# Turno 2 (l'agente ricorda il contesto)
memory.add_turn([TextBlock("Ricordi il mio nome?")], ROLE.USER)
response = agent.invoke("", memory=memory)
```

## Esempi di strumenti implementati

### CalculatorTool
**Scopo**: Esegue calcoli matematici
**Input**: Espressione matematica come stringa
**Output**: Risultato del calcolo

```python
# Esempio di utilizzo
calc_tool = CalculatorTool()
result = calc_tool.execute("(15 + 5) * 2")
print(result.result)  # "Risultato: 40"
```

### WebSearchTool
**Scopo**: Simula ricerche web
**Input**: Query di ricerca
**Output**: Risultati simulati

```python
# Esempio di utilizzo
search_tool = WebSearchTool()
result = search_tool.execute("Python programming")
print(result.result)  # Risultati simulati per Python
```

### FileManagerTool
**Scopo**: Gestisce file e directory (simulato)
**Input**: Comando e percorso
**Output**: Risultato dell'operazione

```python
# Esempio di utilizzo
file_tool = FileManagerTool()

# Lista file
result = file_tool.execute({"command": "list", "path": "docs/"})

# Crea file
result = file_tool.execute({"command": "create", "path": "docs/new.txt"})

# Elimina file
result = file_tool.execute({"command": "delete", "path": "docs/old.txt"})
```

## Pattern di utilizzo avanzati

### Workflow sequenziale
```python
# L'agente può eseguire workflow complessi
workflow_query = """
    Esegui questo workflow:
    1. Cerca informazioni su machine learning
    2. Calcola quanti anni sono passati dal 1990 al 2025
    3. Crea un file chiamato ml_summary.txt
    4. Verifica che il file sia stato creato
"""

response = agent.invoke(workflow_query)
```

### Selezione intelligente dello strumento
```python
# L'agente sceglie automaticamente lo strumento appropriato
queries = [
    "Calcola 2 + 2",                    # → CalculatorTool
    "Cerca informazioni su AI",          # → WebSearchTool
    "Crea un file chiamato test.txt",    # → FileManagerTool
    "Quanto costa un progetto AI?"       # → WebSearchTool + CalculatorTool
]

for query in queries:
    response = agent.invoke(query)
    print(f"Query: {query}")
    print(f"Risposta: {response.text}")
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

## Debugging e testing

### Test individuale dei tool
```python
# Testa ogni tool individualmente
def test_tool(tool, test_cases):
    for test_case in test_cases:
        result = tool.execute(test_case)
        print(f"Input: {test_case}")
        print(f"Success: {result.success}")
        if result.success:
            print(f"Result: {result.result}")
        else:
            print(f"Error: {result.error}")
        print()

# Test CalculatorTool
calc_tool = CalculatorTool()
test_cases = ["2 + 2", "10 * 5", "(15 + 5) / 4"]
test_tool(calc_tool, test_cases)
```

### Verifica uso strumenti
```python
# Verifica quali strumenti sono stati utilizzati
response = agent.invoke("Calcola e cerca informazioni")

if hasattr(response, 'tool_calls') and response.tool_calls:
    print("Strumenti utilizzati:")
    for tool_call in response.tool_calls:
        print(f"- {tool_call.tool_name}: {tool_call.result}")
else:
    print("Nessuno strumento utilizzato")
```

### Logging e monitoraggio
```python
# Abilita logging per debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitora l'uso dei tool
def monitor_tool_usage(agent, query):
    print(f"Query: {query}")
    response = agent.invoke(query)
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"Tool utilizzati: {len(response.tool_calls)}")
        for tool_call in response.tool_calls:
            print(f"  {tool_call.tool_name}: {tool_call.result}")
    
    return response
```

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

## Configurazione e ambiente

### File .env richiesto
```bash
# Directory: PizzAI/.env
OPENAI_API_KEY=sk-your-openai-key-here
```

### Dipendenze Python
```bash
pip install datapizzai python-dotenv
```

### Variabili d'ambiente opzionali
```bash
# Modello personalizzato
OPENAI_MODEL=gpt-4o

# Configurazioni tool specifiche
DATABASE_URL=postgresql://user:pass@localhost/db
API_BASE_URL=https://api.example.com
```

## Menu interattivo

```
MULTI AGENT-TOOL FRAMEWORK
=================================================================

Demo disponibili:

1. Test strumenti individuali → Verifica funzionamento base
2. Agente singolo strumento → MathAgent con calculator
3. Agente multi strumento → ResearchAgent con search + file
4. Workflow complesso → MultiToolAgent con tutti gli strumenti
5. Agente con memoria → Conversazione multi-turno
6. Mostra strumenti → Lista e descrizioni

0. Esci
```

## Risoluzione problemi comuni

### Error: "Client OpenAI non disponibile"
```bash
# Verifica file .env
ls -la PizzAI/.env

# Crea se mancante
echo 'OPENAI_API_KEY=your-key' > PizzAI/.env
```

### Error: "Tool not found"
```python
# Verifica che il tool sia nella lista dell'agente
print(f"Tool disponibili: {[t.name for t in agent.tools]}")

# Assicurati di passare la lista corretta
agent = Agent(
    name="TestAgent",
    client=client,
    tools=[calculator_tool, search_tool],  # Lista non vuota
    system_prompt="..."
)
```

### Error: "Invalid input schema"
```python
# Verifica lo schema del tool
print(f"Schema input: {tool.input_schema}")

# Assicurati che l'input corrisponda allo schema
# Per schema "string": tool.execute("testo")
# Per schema "object": tool.execute({"key": "value"})
```

## Documentazione completa

→ **[multi_agent_tools.py](multi_agent_tools.py)** - Script completo con esempi funzionanti

→ **[GUIDA_MULTI_AGENT.md](GUIDA_MULTI_AGENT.md)** - Documentazione tecnica dettagliata (se disponibile)

## Requisiti tecnici

- Python 3.8+
- Ambiente virtuale attivato
- OPENAI_API_KEY configurata
- Modulo datapizzai installato
- Connessione internet per API calls

## Note sui costi

- **OpenAI GPT-4o**: ~$0.01 per 1K token input, ~$0.03 per 1K token output
- **Tool execution**: Gratuito (eseguiti localmente)
- **Memoria**: Aggiunge token al contesto, aumentando i costi per conversazioni lunghe

Consultare la documentazione ufficiale OpenAI per tariffe aggiornate.
