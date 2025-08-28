# Guida completa agenti datapizzai

## Panoramica

Questa guida descrive gli elementi essenziali per creare agenti AI usando la libreria `datapizzai` (>= 3.0.8), con esempi copiabili dal file `Agents/agent_complete.py`.

## Moduli principali

- `agents`: classe `Agent` e `ClientManager`
- `clients`: `ClientFactory`, `Provider`, `MockClient`
- `tools`: decoratore `@tool` e classe `Tool`
- `memory`: classe `Memory`
- `type`: `ROLE`, `TextBlock`
- `pipeline`, `vectorstores`: funzionalità avanzate (ingestion, ricerca)

## Provider supportati

- OpenAI (es. `gpt-4o`)
- Google (es. `gemini-2.0-flash`)
- Anthropic (es. `claude-3.5-sonnet`)
- Mistral (es. `mistral-large`)
- Azure OpenAI (es. `gpt-35-turbo`)

## 1. Configurazione client

```python
from datapizzai.clients import ClientFactory
from datapizzai.clients.factory import Provider
import os

# OpenAI
openai_client = ClientFactory.create(
    provider=Provider.OPENAI,  # o "openai"
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="Sei un assistente AI utile.",
    temperature=0.7,
)

# Google
google_client = ClientFactory.create(
    provider=Provider.GOOGLE,  # o "google"
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
    system_prompt="Sei Gemini, l'assistente AI di Google.",
    temperature=0.6,
)
```

Nel file `agent_complete.py` è presente un metodo `setup_client` che accetta sia `Provider` sia stringhe e imposta automaticamente modello, `system_prompt` e `temperature`. Se la chiave API non è disponibile, viene utilizzato `MockClient` per test locali.

## 2. Tools personalizzati

```python
from datapizzai.tools import tool

@tool(name="calculator", description="Esegue calcoli matematici")
def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Errore: caratteri non consentiti"
    return f"Risultato: {eval(expression)}"
```

- **definizione**: con `@tool`
- **metadata**: `name`, `description`
- **tipi**: usare type hints per validazione

## 3. Memoria conversazionale

```python
from datapizzai.memory import Memory
from datapizzai.type import ROLE, TextBlock

memory = Memory()
memory.add_turn(TextBlock(content="Preferisco risposte concise."), role=ROLE.SYSTEM)
```

- Mantiene il contesto tra chiamate
- API principali: `add_turn`, `new_turn`, `iter_blocks`

## 4. Creazione agente

```python
from datapizzai.agents import Agent

agent = Agent(
    name="DatapizzAI_Agent_Basic",
    client=openai_client,  # o qualunque client creato
    system_prompt="Sei un assistente AI utile.",
    tools=[calculator],
    max_steps=5,
    terminate_on_text=True,
    stateless=False,
    memory=memory,
)
```

- `max_steps`: limite step di ragionamento
- `terminate_on_text`: termina su risposta testuale
- `planning_interval`: attiva planning periodico (0 = disattivato)

## 5. Esecuzione

- **sincrona**:

```python
response = agent.run("Calcola 25 * 4 + 100")
```

- **asincrona**:

```python
response = await agent.a_run("Spiega cos'è l'AI")
```

- **streaming**:

```python
for chunk in agent.stream_invoke("Racconta una frase"):
    if isinstance(chunk, str):
        print("Finale:", chunk)
    else:
        print("Step:", type(chunk).__name__)
```

## 6. Multi‑agent

```python
analyst = Agent(name="Analyst", client=openai_client, tools=[calculator])
coordinator = Agent(name="Coordinator", client=openai_client, can_call=[analyst])
response = coordinator.run("Analizza 'AI revolution' e calcola 2^8")
```

- `can_call`: consente a un agente di delegare ad altri agenti

## 7. Esempio rapido (dal file)

```python
from Agents.agent_complete import DatapizzAIAgentDemo

demo = DatapizzAIAgentDemo()
demo.setup_client()                 # usa Provider e fallback MockClient
tools = demo.create_custom_tools()
demo.setup_agent_basic(tools)
print(demo.agent.run("Calcola 10 + 20"))
```

## 8. Variabili ambiente

```bash
export OPENAI_API_KEY="..."
export GOOGLE_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export MISTRAL_API_KEY="..."
export AZURE_OPENAI_API_KEY="..."
```

## 9. Best practice

- **sicurezza**: gestire API key via variabili d'ambiente
- **affidabilità**: usare `MockClient` per test locali senza credenziali
- **performance**: preferire metodi asincroni e planning per task complessi
- **manutenibilità**: definire tools piccoli e riusabili, con type hints

## 10. Troubleshooting

- API key mancante: verrà usato `MockClient`
- Modello non supportato: verificare il nome del modello per il provider
- Errori tools: validare input (es. caratteri consentiti nel `calculator`)


