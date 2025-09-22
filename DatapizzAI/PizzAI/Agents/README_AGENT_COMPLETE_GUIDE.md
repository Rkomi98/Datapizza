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
from datapizzai.tools.google import google_search_tool
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

Un sistema multi‑agente maturo richiede un instradamento intelligente basato sulla natura della richiesta. Il pattern `DecisionHub` seguente analizza le query in ingresso e le instrada in modo condizionale verso agenti specializzati:

![multi-agent-svg-animation](https://github.com/user-attachments/assets/a3d6beae-8f9a-4266-92f2-d7fd01d61389)

```python
import os
import re
from textwrap import dedent
from dotenv import load_dotenv

from datapizzai.agents import Agent
from datapizzai.clients import OpenAIClient
from datapizzai.tools import tool

load_dotenv()

openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0.2,
)

@tool
def simulated_web_search(query: str, top_k: int = 3) -> str:
    """Restituisce un elenco numerato di fonti (placeholder in attesa del tool DuckDuckGo)."""
    canonical_results = {
        "fintech": [
            "1. McKinsey 2025 – Investimenti in generative AI nel fintech a 18B€",
            "2. Deloitte Insight – I processi di prestito valgono in media il 22% di 200M$",
            "3. BCE Tech Watch – Rischi chiave: compliance e privacy dei dati costano 70M alle aziende UE",
        ],
        "default": [
            "1. Industry Report – Adozione enterprise AI +30% YoY",
            "2. Vendor Study – ROI dell'automazione documentale in media 180M $",
            "3. Regolatore UE – Linee guida per gestire il 100% dei dati sensibili",
        ],
    }
    bucket = canonical_results["fintech" if "fintech" in query.lower() else "default"]
    return "\n".join(bucket[: max(1, top_k)])

@tool
def extract_numeric_table(raw_text: str) -> str:
    """Estrae valori numerici dal testo e restituisce un'analisi Markdown completa."""
    pattern = re.compile(r"[-+]?\d+[\d,.]*\s?(?:%|€|eur|m|k|b|billion|million|miliardi|milioni)?", re.IGNORECASE)
    rows = []
    for line in raw_text.splitlines():
        matches = pattern.findall(line)
        if matches:
            cleaned = [match.replace(',', '.').strip() for match in matches]
            rows.append((line.strip(), ", ".join(cleaned)))

    if not rows:
        return """## Analisi quantitativa

| Metrica | Valore | Valutazione |
| --- | --- | --- |
| Nessun dato quantificabile trovato | - | Dati insufficienti per l'analisi |

**Implicazioni strategiche**: l'analisi richiede più fonti quantitative."""

    # Crea un'analisi completa
    analysis = ["## Analisi quantitativa", ""]
    analysis.append("| Metrica | Valore | Valutazione |")
    analysis.append("| --- | --- | --- |")

    for entry, values in rows:
        # Analizza i valori nel loro contesto strategico
        assessment = "Monitorare trend"
        if any(char in values.lower() for char in ['%']):
            if any(int(re.findall(r'\d+', val)[0]) > 20 for val in values.split(',') if re.findall(r'\d+', val)):
                assessment = "Indicatore ad alto impatto"
            else:
                assessment = "Segnale di crescita moderata"
        elif any(char in values.lower() for char in ['b', 'billion', 'miliardi']):
            assessment = "Grande opportunità di mercato"
        elif any(char in values.lower() for char in ['€', 'eur']):
            assessment = "KPI finanziario - tracciare il ROI"

        analysis.append(f"| {entry[:50]}... | {values} | {assessment} |")

    return "\n".join(analysis)

# Agenti specializzati
research_agent = Agent(
    name="Research",
    client=openai_client,
    system_prompt=(
        "Ti occupi di market intelligence: chiama simulated_web_search esattamente una volta e "
        "restituisci l'elenco numerato senza commenti aggiuntivi."
    ),
    tools=[simulated_web_search],
    terminate_on_text=True,
    max_steps=2,
)

analysis_agent = Agent(
    name="DataAnalysis",
    client=openai_client,
    system_prompt=(
        "Sei un'analista strategico dei dati. Estrai i numeri più importanti dall'analisi e formattali in una tabella."
    ),
    tools=[extract_numeric_table],
    terminate_on_text=True,
    max_steps=2,
)

# Strumenti di coordinamento del DecisionHub
@tool
def call_research_agent(query: str, top_k: int = 3) -> str:
    """Delega la raccolta di market intelligence allo specialista di ricerca."""
    try:
        prompt = f"Raccogli intelligence su: {query}. Fornisci al massimo {top_k} fonti numerate."
        result = research_agent.run(prompt)
        return result if result is not None else "L'agente di ricerca non ha restituito risultati."
    except Exception as e:
        return f"Errore dell'agente di ricerca: {str(e)}"

@tool
def call_analysis_agent(research_data: str) -> str:
    """Delega l'analisi quantitativa allo specialista di data analysis."""
    try:
        prompt = dedent(f"""
            Fornisci un'analisi di livello executive sui dati di ricerca sottostanti:
            1. Estrai insight quantitativi usando il tuo tool di analisi
            2. Riassumi i risultati chiave
            3. Valuta rischi e opportunità
            4. Fornisci raccomandazioni strategiche

            DATI DI RICERCA:
            {research_data}
        """).strip()
        result = analysis_agent.run(prompt)
        return result if result is not None else "L'agente di analisi non ha restituito risultati."
    except Exception as e:
        return f"Errore dell'agente di analisi: {str(e)}"

# DecisionHub come agente
decision_hub_agent = Agent(
    name="DecisionHub",
    client=openai_client,
    system_prompt=(
        "Sei un agente di coordinamento intelligente che instrada query complesse verso agenti specializzati. "
        "Analizza la richiesta dell'utente e decidi quali agenti coinvolgere: "
        "- Usa call_research_agent per market intelligence, trend, opportunità, scenario competitivo "
        "- Usa call_analysis_agent per analisi quantitativa, KPI, valutazione dei rischi, interpretazione dei dati "
        "Sintetizza sempre i risultati di più agenti in un briefing esecutivo completo."
    ),
    tools=[call_research_agent, call_analysis_agent],
    terminate_on_text=True,
    max_steps=3,
)

# Test del sistema con gestione degli errori
user_query = "Abbiamo bisogno di un aggiornamento sulle opportunità commerciali dell'AI generativa nel fintech. Voglio una tabella con tutti i KPI"

try:
    final_answer = decision_hub_agent.run(user_query)
    if final_answer is None:
        final_answer = "L'agente DecisionHub non ha restituito risposta. Controlla la configurazione."
    print(final_answer)
except Exception as e:
    print(f"Errore di sistema: {str(e)}")
    print("Assicurati che tutti gli agenti siano configurati correttamente con chiavi API e modelli validi.")
```

### Note sulla gestione degli errori

Gli strumenti di coordinamento includono una gestione degli errori pensata per evitare che valori `None` causino problemi di rendering con Rich. Assicurati sempre che:
- Le risposte degli agenti vengano validate prima di passarle ai sistemi di visualizzazione
- Le chiamate agli agenti siano sempre protette da gestione delle eccezioni
- Siano previsti messaggi di fallback quando un agente non risponde

- Quando il tool DuckDuckGo sarà disponibile, sostituisci semplicemente `simulated_web_search` con l'integrazione reale e rimuovi l'avviso sulla simulazione.
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
