# Complete Guide: Building AI Agents with datapizzai

## Overview

This guide shows how to build and orchestrate AI agents using the `datapizzai` library (>= 3.0.8). The goal is a clear, hands‑on understanding of how agents work and interact in complex systems, with minimal, practical examples.

## Table of contents

- [1. Create an agent](#1-create-an-agent)
- [2. Run an agent](#2-run-an-agent)
- [3. Multi‑agent system](#3-multi-agent-system)
- [4. Planning interval](#4-planning-interval)

## 1. Create an agent

An agent is an autonomous entity that uses a language model (LLM) to reason, use tools, and maintain conversational memory to solve problems.

```mermaid
graph TD;
    subgraph Single Agent Architecture;
        A["User Query"] --> B{"Agent (Brain)"};
        B --> C["LLM Client (Reasoning)"];
        B --> D["Tools (Actions)"];
        B --> E["Memory (Context)"];
        C --> B;
        D --> B;
        E --> B;
        B --> F["Final Response"];
    end;
```

Its creation requires configuring several parameters that define its behavior.

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import OpenAIClient
from datapizzai.cache import MemoryCache
from datapizzai.tools import tool
from datapizzai.agents import Agent  # alternatively: from datapizzai.agents import Agent, ClientManager

load_dotenv()

# In‑process cache
cache = MemoryCache()

# OpenAI client with cache
openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3,
    cache=cache,
)

# Quick client test (second call is a cache hit)
r1 = openai_client.invoke("Hello!")
print("Response 1:", r1.text)
r2 = openai_client.invoke("Hello!")
print("Response 2 (cache hit):", r2.text)

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

For complex problems, it is effective to combine multiple specialized agents. A "coordinator" agent receives the request, breaks it down, and delegates the sub-tasks to the most suitable agents.

This is achieved through the `can_call` parameter.

```mermaid
graph TD
    subgraph Multi-Agent System
        A["Complex User Query"] --> B{"Coordinator Agent"}
        B -- Plan --> P((Plan))
        B -- Task 1 --> C["text_analysis_tool"]:::tool
        B -- Task 2 --> D["calculator_tool"]:::tool
        C -- Result --> B
        D -- Result --> B
        B -- Synthesize --> E["Final Response"]
    end

classDef tool fill:#E6F7FF,stroke:#1890FF,color:#003A8C
classDef agent fill:#FFF7E6,stroke:#FA8C16,color:#613400
class B agent
```

```python
analyst_agent = Agent(name="Analyst_Agent", tools=[text_analysis_tool])
calculator_agent = Agent(name="Calculator_Agent", tools=[calculator_tool])

coordinator = Agent(name="Coordinator_Agent", can_call=[analyst_agent, calculator_agent])
response = coordinator.run("Analyze the text 'AI is powerful' and calculate 1024 / 256")
```

- `can_call` (`List[Agent]`): Makes the agents in the list available as "tools" for the coordinator, who can then invoke them by passing a specific task.

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