# Complete Guide: Building AI Agents with datapizzai

## Overview

This guide demonstrates how to build and orchestrate AI agents using the `datapizzai` library (>= 3.0.8). You'll gain a thorough, hands-on understanding of how agents operate and collaborate in complex systems through concise, practical examples.

## Table of contents

- [1. Create an agent](#1-create-an-agent)
- [2. Run an agent](#2-run-an-agent)
- [3. Multi‑agent system](#3-multi-agent-system)
- [4. Planning interval](#4-planning-interval)

## 1. Create an agent

An agent is an autonomous entity that leverages an LLM to reason, operate tools, and solve problems. Creating one involves configuring the parameters that define its behavior and capabilities.

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

Each agent parameter serves a specific purpose:

- `name` (`str`): An identifier useful for logging and debugging multi-agent systems.
- `client` (`Client`): The LLM client instance (e.g., `OpenAIClient`, `GoogleClient`) that powers the agent's reasoning. Created via `ClientFactory`.
- `system_prompt` (`str`): Core instructions defining the agent's personality, role, and behavior patterns. This is the most critical element for directing agent actions.
- `tools` (`List[Tool]`): Python functions decorated with `@tool` that the agent can invoke to perform actions (calculations, file operations, API calls, etc.).
- `max_steps` (`int`): Maximum reasoning cycles (thought → action) before termination. Prevents infinite loops.
- `memory` (`Memory`): Maintains conversation context across interactions. Without this, the agent is stateless.
- `stateless` (`bool`): When `True`, memory isn't automatically updated between `.run()` calls. Defaults to `False` when memory is provided.
- `terminate_on_text` (`bool`): When `True`, stops execution immediately after generating a text response, bypassing further tool use.
- `planning_interval` (`int`): When `> 0`, pauses every N steps to reassess strategy. Improves performance on complex, multi-step tasks. Set to `0` to disable.

## 2. Run an agent

Once configured, you can execute the agent in several modes:

- **Synchronous**: Blocking execution that waits for complete response.
  ```python
  response = agent.run("Calculate 25 * 4 + 100")
  ```
- **Asynchronous**: Non-blocking I/O operations, perfect for web applications.
  ```python
  response = await agent.a_run("Explain what AI is")
  ```
- **Streaming**: Real-time response chunks, revealing both intermediate reasoning steps and final output.
  ```python
  for chunk in agent.stream_invoke("Tell me a joke"):
      if isinstance(chunk, str):
          print("Final text:", chunk)
      else:
          print("Intermediate step:", type(chunk).__name__)
  ```

## 3. Multi‑agent system

A sophisticated multi-agent system requires intelligent routing based on the nature of the request. The `DecisionHub` pattern below analyzes incoming queries and conditionally routes them to specialized agents:

```mermaid
graph TD
    U["User request"] --> H{"DecisionHub"}
    H -->|If scouting needed| R{"Research Agent"}
    H -->|If KPIs/risks needed| D{"DataAnalysis Agent"}
    R --> H
    D --> H
    H --> F["Final response"]
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
    """Returns a numbered list of sources (placeholder until the DuckDuckGo tool is available)."""
    canonical_results = {
        "fintech": [
            "1. McKinsey 2025 – Generative AI investments in fintech at €18B",
            "2. Deloitte Insight – Lending processes average 22% cost reduction",
            "3. ECB Tech Watch – Key risks: compliance and data privacy",
        ],
        "default": [
            "1. Industry Report – Enterprise AI adoption +30% YoY",
            "2. Vendor Study – Document automation ROI averages 180%",
            "3. EU Regulator – Guidelines for handling sensitive data",
        ],
    }
    bucket = canonical_results["fintech" if "fintech" in query.lower() else "default"]
    return "\n".join(bucket[: max(1, top_k)])

@tool
def extract_numeric_table(raw_text: str) -> str:
    """Extracts numeric values from text and outputs a compact Markdown table."""
    pattern = re.compile(r"[-+]?\d+[\d,.]*\s?(?:%|€|eur|m|k)?", re.IGNORECASE)
    rows = []
    for line in raw_text.splitlines():
        matches = pattern.findall(line)
        if matches:
            cleaned = [match.replace(',', '.').strip() for match in matches]
            rows.append((line.strip(), ", ".join(cleaned)))
    if not rows:
        return """| Item | Value |
| --- | --- |
| No numbers found | - |"""
    table = ["| Item | Value |", "| --- | --- |"]
    table += [f"| {entry} | {value} |" for entry, value in rows]
    return "\n".join(table)

# Specialized agents
research_agent = Agent(
    name="Research",
    client=openai_client,
    system_prompt=(
        "You handle market intelligence: call simulated_web_search exactly once and return "
        "the numbered list without additional commentary."
    ),
    tools=[simulated_web_search],
    terminate_on_text=True,
    max_steps=2,
)

analysis_agent = Agent(
    name="DataAnalysis",
    client=openai_client,
    system_prompt=(
        "You extract and analyze quantitative data. Invoke extract_numeric_table once, "
        "then provide strategic insights and include the Markdown table in your response."
    ),
    tools=[extract_numeric_table],
    terminate_on_text=True,
    max_steps=3,
)

class DecisionHub:
    """Intelligent routing hub that analyzes queries and delegates to appropriate agents."""
    
    def __init__(self, research_agent, analysis_agent):
        self.research_agent = research_agent
        self.analysis_agent = analysis_agent
    
    def needs_research(self, query: str) -> bool:
        """Determine if query requires market intelligence gathering."""
        research_keywords = ["update", "trends", "market", "opportunities", "landscape", "competition"]
        return any(keyword in query.lower() for keyword in research_keywords)
    
    def needs_analysis(self, query: str) -> bool:
        """Determine if query requires quantitative analysis."""
        analysis_keywords = ["kpi", "metrics", "numbers", "data", "analysis", "risk", "performance"]
        return any(keyword in query.lower() for keyword in analysis_keywords)
    
    def process_query(self, user_query: str, top_k: int = 3) -> str:
        """Route query to appropriate agents based on content analysis."""
        results = {}
        
        if self.needs_research(user_query):
            research_prompt = f"Gather intelligence on: {user_query}. Provide up to {top_k} numbered sources."
            results["research"] = self.research_agent.run(research_prompt)
        
        if self.needs_analysis(user_query) and "research" in results:
            analysis_prompt = dedent(f"""
                Analyze the research data below for key metrics and risks.
                1. Extract numeric values using your tool
                2. Provide strategic assessment
                3. Include the data table
                
                RESEARCH DATA:
                {results["research"]}
            """).strip()
            results["analysis"] = self.analysis_agent.run(analysis_prompt)
        
        # Synthesize final response
        if "analysis" in results:
            return f"### Intelligence Brief: {user_query}\n\n{results['analysis']}\n\n---\n*Sources simulated (awaiting official DuckDuckGo tool)*"
        elif "research" in results:
            return f"### Market Intelligence: {user_query}\n\n{results['research']}\n\n---\n*Sources simulated (awaiting official DuckDuckGo tool)*"
        else:
            return f"Query '{user_query}' doesn't match available agent capabilities."

# Initialize DecisionHub
hub = DecisionHub(research_agent, analysis_agent)

# Test the system
user_query = "We need an update on generative AI commercial opportunities in fintech and a risk assessment."
final_answer = hub.process_query(user_query)
print(final_answer)
```

- Once the DuckDuckGo tool becomes available, simply replace `simulated_web_search` with the real integration and remove the simulation disclaimer.
## 4. Planning interval

Setting `planning_interval=N` forces the agent to reassess its strategy every N steps. This is particularly valuable for complex, multi-phase tasks.

```python
from datapizzai.agents import Agent

agent = Agent(
    client=client,
    planning_interval=3,  # plan every 3 steps
)

response = agent.run("Write a migration plan from monolith to microservices and estimate the effort")
print(response)
```

Conceptual execution flow (reassessing strategy every 3 steps):

```mermaid
flowchart LR
    A[Start] --> S1[Step 1]
    S1 --> S2[Step 2]
    S2 --> S3[Step 3]
    S3 --> P[Strategy Review]
    P --> S4[Step 4]
    S4 --> S5[Step 5]
    S5 --> S6[Step 6]
    S6 --> P2[Strategy Review]
    P2 --> E[End]
```
<!--
## Additional information

- The `agent_complete.py` file contains complete implementations and advanced scenarios.
-->
