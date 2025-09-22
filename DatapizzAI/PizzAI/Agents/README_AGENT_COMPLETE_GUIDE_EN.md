# Complete Guide: Building AI Agents with datapizzai

## Overview

This guide shows how to build and orchestrate AI agents using the `datapizzai` library (>= 3.0.8). The goal is a clear, hands‑on understanding of how agents work and interact in complex systems, with minimal, practical examples.

## Table of contents

- [1. Create an agent](#1-create-an-agent)
- [2. Run an agent](#2-run-an-agent)
- [3. Multi‑agent system](#3-multi-agent-system)
- [4. Planning interval](#4-planning-interval)

## 1. Create an agent

An agent is an autonomous entity that uses a LLM to reason, operate tools, and solve problems. Creating one means configuring the parameters that shape its behaviour.

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import OpenAIClient
from datapizzai.tools import tool
from datapizzai.tools.google import google_search_tool
from datapizzai.agents import Agent  # alternatively: from datapizzai.agents import Agent, ClientManager

load_dotenv()

# OpenAI client
openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3,
)

# Tool
@tool
def get_weather(location: str, when: str) -> str:
    """Retrieves weather information for a specified location and time."""
    return "25 °C"

# Agent wired to the client
agent = Agent(
    name="WeatherAgent",
    client=openai_client,
    system_prompt="You are a weather assistant. Use tools when needed and reply in English.",
    tools=[get_weather],
    terminate_on_text=True,
)
response = agent.run("What will the weather be next Monday in Milan?")
print(response)
```

### Input parameters

Each agent parameter has a specific role:

- `name` (`str`): An identifying name, useful for logging and in multi-agent systems.
- `client` (`Client`): The instance of the LLM client (e.g., `OpenAIClient`, `GoogleClient`) that the agent will use to "think". It is created via `ClientFactory`.
- `system_prompt` (`str`): The basic instructions that define the agent's personality, role, and directives. It is the most important element for guiding its behavior.
- `tools` (`List[Tool]`): A list of tools (Python functions decorated with `@tool`) that the agent can decide to use to perform actions (e.g., calculations, file searches, external APIs).
- `max_steps` (`int`): The maximum number of reasoning steps (thought -> action) the agent can take before stopping. Useful for preventing infinite loops.
- `memory` (`Memory`): A `Memory` instance to maintain the context of past conversations. If not provided, the agent operates without a memory of previous interactions.
- `stateless` (`bool`): If `True`, the memory is not automatically updated between `.run()` calls. It defaults to `False` when a memory is provided.
- `terminate_on_text` (`bool`): If `True`, the agent stops as soon as it produces a final text response, without attempting to use other tools.
- `planning_interval` (`int`): If set to a value `> 0`, the agent stops every `N` steps to review its action plan, improving effectiveness on complex tasks. `0` disables explicit planning.

## 2. Run an agent

Once configured, the agent can be run in different modes:

- **Synchronous**: A blocking execution that waits for the final response.
  ```python
  response = agent.run("Calculate 25 * 4 + 100")
  ```
- **Asynchronous**: For non-blocking I/O operations, ideal for web applications.
  ```python
  response = await agent.a_run("Explain what AI is")
  ```
- **Streaming**: Receives the response one piece at a time (chunk), showing both intermediate steps and the final text.
  ```python
  for chunk in agent.stream_invoke("Tell me a joke"):
      if isinstance(chunk, str):
          print("Final text:", chunk)
      else:
          print("Intermediate step:", type(chunk).__name__)
  ```

## 3. Multi‑agent system

Sometimes you need to orchestrate specialised agents without adding heavy multi-step plans. The `decision_hub_pipeline` function below:
1. Uses the `Research` agent to simulate (until DuckDuckGo is available) a search and return a numbered list of sources.
2. Sends the list to the `DataAnalysis` agent, which extracts the key figures via a dedicated tool and renders a Markdown table.
3. Produces a ready-to-display final answer.

```mermaid
graph TD
    U["User request"] --> P["DecisionHub function"]
    P -->|Simulated search| R{"Research Agent"}
    R -->|Numbered notes| P
    P -->|Numeric extraction| D{"DataAnalysis Agent"}
    D -->|Summary + table| P
    P --> F["Final Markdown response"]
```

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
    """Returns a numbered list of sources while we wait for the DuckDuckGo tool."""
    canonical_results = {
        "fintech": [
            "1. McKinsey 2025 – Generative AI investments hit €18B in fintech",
            "2. Deloitte Insight – Lending automation cuts costs by 22% on average",
            "3. ECB Tech Brief – Key risks: compliance and data privacy",
        ],
        "default": [
            "1. Industry Report – Enterprise AI adoption up 30% YoY",
            "2. Vendor Study – Document automation ROI reaches 180%",
            "3. EU Regulator – Guidance on handling sensitive data",
        ],
    }
    bucket = canonical_results["fintech" if "fintech" in query.lower() else "default"]
    return "
".join(bucket[: max(1, top_k)])

@tool
def extract_numeric_table(raw_text: str) -> str:
    """Extracts numeric values from text and returns a compact Markdown table."""
    pattern = re.compile(r"[-+]?\d+[\d,.]*\s?(?:%|€|eur|m|k)?", re.IGNORECASE)
    rows = []
    for line in raw_text.splitlines():
        matches = pattern.findall(line)
        if matches:
            cleaned = [match.replace(',', '.').strip() for match in matches]
            rows.append((line.strip(), ", ".join(cleaned)))
    if not rows:
        return "| Item | Value |
| --- | --- |
| No numeric data found | - |"
    table = ["| Item | Value |", "| --- | --- |"]
    table += [f"| {item} | {value} |" for item, value in rows]
    return "
".join(table)

research_agent = Agent(
    name="Research",
    client=openai_client,
    system_prompt=(
        "You are the research specialist: call simulated_web_search exactly once and "
        "return the numbered list verbatim."
    ),
    tools=[simulated_web_search],
    terminate_on_text=True,
    max_steps=2,
)

analysis_agent = Agent(
    name="DataAnalysis",
    client=openai_client,
    system_prompt=(
        "You receive a bullet list and must extract relevant figures. "
        "Call extract_numeric_table once, then provide a two-sentence overview and paste the Markdown table."
    ),
    tools=[extract_numeric_table],
    terminate_on_text=True,
    max_steps=3,
)

def decision_hub_pipeline(user_query: str, top_k: int = 3) -> str:
    research_prompt = (
        f"Collect up to {top_k} numbered bullet points (1., 2., 3.) using the available tool about {user_query}."
    )
    research_notes = research_agent.run(research_prompt)

    analysis_prompt = dedent(
        """
        Summarise the numbered list below.
        1. Invoke extract_numeric_table to produce a value table.
        2. Provide a two-sentence strategic overview.
        3. Include the table in the final output.
        """
    ).strip()
    analysis_input = f"{analysis_prompt}

RESEARCH NOTES:
{research_notes}"
    structured_output = analysis_agent.run(analysis_input)

    return (
        f"### Update on '{user_query}'

"
        f"{structured_output}

"
        "---
"
        "Sources simulated (awaiting the official DuckDuckGo tool)."
    )

user_query = "Share a commercial outlook for generative AI in fintech and highlight potential risks."
final_answer = decision_hub_pipeline(user_query)
print(final_answer)
```

- Once the DuckDuckGo tool ships, replace `simulated_web_search` with the real integration and drop the simulation notice.
## 4. Planning interval

With `planning_interval=N` the agent reviews its plan every N steps. Useful for long/branched tasks.

```python
from datapizzai.agents import Agent

agent = Agent(
    client=client,
    planning_interval=3,  # plan every 3 steps
)

response = agent.run("Write a plan to migrate a monolith to microservices and estimate the effort")
print(response)
```

Conceptual execution (planning every 3 steps):

```mermaid
flowchart LR
    A[Start] --> S1[Step 1]
    S1 --> S2[Step 2]
    S2 --> S3[Step 3]
    S3 --> P[Plan Review]
    P --> S4[Step 4]
    S4 --> S5[Step 5]
    S5 --> S6[Step 6]
    S6 --> P2[Plan Review]
    P2 --> E[End]
```
<!--
## Additional information

- The `agent_complete.py` file contains complete implementations and advanced scenarios.
-->
