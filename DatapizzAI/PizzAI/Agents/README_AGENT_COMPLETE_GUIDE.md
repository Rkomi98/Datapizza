# Guida completa: creare agenti AI con datapizzai

## Panoramica

Questa guida illustra come costruire e orchestrare agenti AI utilizzando la libreria `datapizzai` (>= 3.0.8). L'obiettivo è una comprensione chiara del funzionamento degli agenti e della loro interazione in sistemi complessi, con esempi minimali e pratici.

## Indice

- [1. Creare un agente](#1-creare-un-agente)
- [2. Eseguire un agente](#2-eseguire-un-agente)
- [3. Sistema multi‑agente](#3-sistema-multiagente)
- [4. Planning interval](#4-planning-interval)

## 1. Creare un agente

Un agente è un'entità autonoma che utilizza un LLM per ragionare, usare strumenti (`tools`) e risolvere problemi. La sua creazione richiede la configurazione di diversi parametri che ne definiscono il comportamento.

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import OpenAIClient
from datapizzai.tools import tool
from datapizzai.agents import Agent  # in alternativa: from datapizzai.agents import Agent, ClientManager

load_dotenv()

# Client OpenAI
openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="Sei un assistente AI utile.",
    temperature=0.7,
)

# Tool
@tool
def get_weather(location: str, when: str) -> str:
    """Retrieves weather information for a specified location and time."""
    return "25 °C"

# Agent collegato al client
agent = Agent(
    name="WeatherAgent",
    client=openai_client,
    system_prompt="Sei un assistente meteo. Usa i tool quando servono e rispondi in italiano.",
    tools=[get_weather],
    terminate_on_text=True,
)
response = agent.run("Che tempo ci sarà lunedì prossimo a Milano?")
print(response)
```

## 2. Eseguire un agente

Una volta configurato, l'agente può essere eseguito in diverse modalità:

- **Sincrona**: Esecuzione bloccante che attende la risposta finale.
  ```python
  response = agent.run("Calcola 25 * 4 + 100")
  ```
- **Asincrona**: Per operazioni I/O non bloccanti, ideale in applicazioni web.
  ```python
  response = await agent.a_run("Spiega cos'è l'AI")
  ```
- **Streaming**: Riceve la risposta un pezzo alla volta (chunk), mostrando sia i passaggi intermedi sia il testo finale.
  ```python
  for chunk in agent.stream_invoke("Racconta una barzelletta"):
      if isinstance(chunk, str):
          print("Testo finale:", chunk)
      else:
          print("Step intermedio:", type(chunk).__name__)
  ```

## 3. Sistema multi‑agente

Per gestire richieste eterogenee può bastare un orchestratore applicativo che decide quando raccogliere informazioni dal modello e quando sintetizzarle in un'unica risposta finale. Nell'esempio seguente l'orchestratore `decision_hub_pipeline` richiama due agenti specializzati: `Ricerche` (per ottenere un elenco numerato di fonti) e `DataAnalysis` (per trasformare tali note in scenario e prossimi passi).

```mermaid
graph TD
    U["Input utente"] --> P["Funzione DecisionHub"]
    P -->|Prompt ricerca| R{"Agente Ricerche"}
    R -->|Note numerate| P
    P -->|Prompt analisi| D{"Agente DataAnalysis"}
    D -->|Sintesi finale| P
    P --> F["Risposta finale"]
```

```python
import os
from dotenv import load_dotenv

from datapizzai.agents import Agent
from datapizzai.clients import ClientFactory
from datapizzai.tools import tool

load_dotenv()

base_client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0.4,
)

@tool
def web_digest(topic: str, top_k: int = 3) -> str:
    """Restituisce un elenco sintetico di top_k trend o fonti rilevanti."""
    return (
        "1. Report Gartner 2025 su trend AI\n"
        "2. Studio interno DatapizzAI sul ROI dei modelli small\n"
        "3. Nota di regolamentazione UE sugli AI Act sandbox"
    )

@tool
def synthesize_insights(research_notes: str) -> str:
    """Condensa le note di ricerca in scenario e prossimi passi."""
    bullets = [line.strip() for line in research_notes.splitlines() if line.strip()]
    summary = \"; \".join(bullets[:3])
    return (
        f"Scenario: {summary}\n\n"
        "Prossimi passi:\n"
        "- Validare gli impatti regolatori con il team legale\n"
        "- Prioritizzare i use case a ROI più alto"
    )

research_agent = Agent(
    name="Ricerche",
    client=base_client,
    system_prompt=(
        "Sei lo specialista di scouting. Usa il tool web_digest UNA sola volta"
        " e restituisci sempre un elenco numerato (1., 2., 3.)."
    ),
    tools=[web_digest],
    terminate_on_text=True,
    max_steps=2,
)

analysis_agent = Agent(
    name="DataAnalysis",
    client=base_client,
    system_prompt=(
        "Ricevi le note di ricerca e devi sintetizzarle."
        " Usa il tool synthesize_insights UNA sola volta e restituisci la risposta così com'è."
    ),
    tools=[synthesize_insights],
    terminate_on_text=True,
    max_steps=2,
)

def decision_hub_pipeline(user_query: str, top_k: int = 3) -> str:
    research_prompt = (
        f"Fornisci al massimo {top_k} trend numerati (1., 2., 3.) su: {user_query}. "
        "Non aggiungere altro testo."
    )
    research_notes = research_agent.run(research_prompt)

    analysis_prompt = (
        "Trasforma le seguenti note in scenario e prossimi passi usando il tool synthesize_insights."
    )
    analysis_input = f"{analysis_prompt}\n\nNOTE DI RICERCA:\n{research_notes}"

    insights = analysis_agent.run(analysis_input)
    return f"Scenario multi-agente per '{user_query}'\n\n{insights}"

user_query = "Serve un aggiornamento sulle opportunità commerciali dell'AI generativa in fintech e un check dei rischi."
final_answer = decision_hub_pipeline(user_query)
print(final_answer)
```

- L'orchestratore può essere arricchito con logiche di routing più sofisticate (classificazione, regole, feedback utenti) prima di decidere quali agenti coinvolgere.

## 4. Planning interval

Con `planning_interval=N` l’agente rivede il piano ogni N passi. È utile per task lunghi/ramificati.

```python
from datapizzai.agents import Agent

agent = Agent(
    client=client,
    planning_interval=3,  # pianifica ogni 3 step
)

response = agent.run("Scrivi un piano per migrare un monolite a microservizi e stimane l'effort")
print(response)
```

Esecuzione concettuale (planning ogni 3 step):

```mermaid
flowchart LR
    A[Start] --> S1[Step 1]
    S1 --> S2[Step 2]
    S2 --> S3[Step 3]
    S3 --> P[Revisione Piano]
    P --> S4[Step 4]
    S4 --> S5[Step 5]
    S5 --> S6[Step 6]
    S6 --> P2[Revisione Piano]
    P2 --> E[End]
```
