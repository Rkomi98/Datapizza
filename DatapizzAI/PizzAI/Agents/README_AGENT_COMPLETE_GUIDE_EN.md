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

To handle diverse requests you can add a routing layer that decides which specialists to involve, plus an aggregator that merges their outputs. In the flow below the input hits a "Router" agent that chooses which specialists to activate; their results are then handed to an "Aggregator" agent that crafts the final answer.

```mermaid
graph TD
    U["User request"] --> T{"Router"}
    T -->|Trigger research| R{"Research Agent"}
    T -->|Trigger analysis| D{"DataAnalysis Agent"}
    R --> T
    D --> T
    T --> G{"Aggregator Agent"}
    G --> F["Final response"]
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
    model="gpt-5",
    temperature=1,
)

@tool
def web_digest(topic: str, top_k: int = 3) -> str:
    """Returns a concise list of top_k relevant trends or sources."""
    return (
        "1. Gartner 2025 report on AI adoption\n"
        "2. DatapizzAI internal study on small-model ROI\n"
        "3. EU AI Act sandbox note on compliance"
    )

@tool
def compute_metrics(raw_numbers: str) -> str:
    """Computes core KPIs from raw textual numbers (e.g., revenue, costs, margins)."""
    return "KPIs: revenue €4.2M, margin 28%, growth +12% QoQ"

@tool
def risk_matrix(context: str) -> str:
    """Lists main risks with impact level."""
    return "Risks: compliance medium, security high, reputation medium"

research_agent = Agent(
    name="Research",
    client=base_client,
    system_prompt=(
        "You scout for external signals. Use web_digest to fetch no more than top_k bullet points\n"
        "and always return a numbered list with a one-line justification."
    ),
    tools=[web_digest],
    terminate_on_text=True,
)

analysis_agent = Agent(
    name="DataAnalysis",
    client=base_client,
    system_prompt=(
        "You enrich quantitative or qualitative notes coming from the router."
        " For numbers call compute_metrics; for qualitative aspects complement with risk_matrix."
    ),
    tools=[compute_metrics, risk_matrix],
    terminate_on_text=True,
)

router_agent = Agent(
    name="Router",
    client=base_client,
    system_prompt=(
        "Assess each incoming request and decide whether Research, DataAnalysis or both are required."
        " Whenever you call a specialist, summarise the outcome in JSON under the 'outputs' key."
    ),
    terminate_on_text=True,
)
router_agent.can_call([research_agent, analysis_agent])

aggregator_agent = Agent(
    name="Aggregator",
    client=base_client,
    system_prompt=(
        "You are the final coordinator."
        " 1) Ask Router to orchestrate the needed specialists."
        " 2) Combine the collected material into sections 'Overview' and 'Next steps'."
    ),
    terminate_on_text=True,
)
aggregator_agent.can_call(router_agent)

user_query = (
    "Share a commercial outlook for generative AI in fintech and highlight potential risks."
)
final_answer = aggregator_agent.run(user_query)
print(final_answer)
```

- `can_call` (`List[Agent]`): lets an agent invoke other agents as if they were tools, delegating the appropriate subtask on demand.

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
