# Guide: Structured Responses (JSON and structured_response)

This guide shows two practical ways to get structured outputs with DatapizzAI:
- Classic prompting for raw JSON + client-side parsing
- Typed output via `structured_response` with Pydantic models

## 1) JSON via prompting + parsing

```python
import os, json
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory

load_dotenv()
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1,
)

prompt = (
    "Return a valid JSON object only, with no extra text.\n"
    "Schema: {\n"
    "  \"title\": string,\n"
    "  \"status\": one of [planned, in_progress, done],\n"
    "  \"tasks\": array of {\n"
    "    \"name\": string, \"owner\": string, \"eta_days\": integer\n"
    "  }\n"
    "}"
)

resp = client.invoke(prompt)
raw = resp.text

# Client-side parsing
data = json.loads(raw)
print("Title:", data["title"])  # e.g., "Microservices migration"
```

Tips:
- Validate with Pydantic/JSON Schema for robustness
- Explicitly request “valid JSON only, no extra text” to reduce pre/post text

## 2) Typed output with structured_response

When supported by the provider, define Pydantic classes and get a validated, typed result directly.

```python
import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory

# Pydantic data models
class Task(BaseModel):
    name: str
    owner: str
    eta_days: int

class ProjectSummary(BaseModel):
    title: str
    status: str  # planned, in_progress, done
    tasks: List[Task]

load_dotenv()
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)

# Ask for a typed, validated output
response = client.structured_response(
    input="Summarize the project plan for the new e-commerce portal",
    output_cls=ProjectSummary,
)

# Access the first structured object
structured = response.structured_data[0]
print("Title:", structured.title)
print("Status:", structured.status)
print("Tasks:")
for task in structured.tasks:
    print(f"  - {task.name} (owner: {task.owner}, ETA: {task.eta_days} days)")
```

Practical notes:
- Prefer Pydantic models to define shape and validate outputs
- Typed models provide validation and type hints with minimal boilerplate
- Data is available under `response.structured_data[0]`
