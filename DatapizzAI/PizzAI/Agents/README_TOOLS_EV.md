# Multi‑Tool Framework - DatapizzAI

Concise guide to creating and using tools with DatapizzAI. Tools let the model perform actions (call Python functions) while reasoning.

## Table of Contents

1. [Basic tool structure](#basic-tool-structure)
2. [Minimal invoke](#minimal-invoke)
3. [Multi‑tool client](#multi-tool-client)
4. [Conversation with memory](#conversation-with-memory)
5. [Best practices](#best-practices)
6. [Step‑by‑step: custom tool](#step-by-step-custom-tool)

## Basic tool structure

```python
from datapizzai.tools import tool

@tool
def timer_tool(duration: str) -> str:
    """Set a timer (e.g., "5 minutes")."""
    # DO something (stub)
    return f"Timer set for {duration}"
```

## Minimal invoke

```python
from datapizzai.clients import ClientFactory
from dotenv import load_dotenv
import os

load_dotenv()
client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-5")

response = client.invoke(
    "Set a timer for 5 minutes",
    tools=[timer_tool],
    tool_choice="auto"
)

print(response.text)  # Any text response
for f_call in response.function_calls or []:
    # Execute the local tool with model-suggested arguments
    result = timer_tool(**(f_call.arguments or {}))
    print("tool result:", result)
```

## Multi‑tool client

Example with two tools: a calculator and an information retriever.

```python
from datapizzai.tools import tool

@tool
def calculator(expr: str) -> str:
    """Performs simple calculations (demo)."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(expr) <= allowed:
            return "Error: invalid characters"
        return str(eval(expr))
    except Exception as e:
        return f"Error: {e}"

@tool
def search_info(query: str) -> str:
    """Dummy search (example)."""
    return f"(synthetic results for: {query})"

from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
import os

load_dotenv()
client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

tools = [calculator, search_info]

from datapizzai.type import FunctionCallResultBlock

response = client.invoke(
    input="Calculate (25 * 4) + 10 and search info on Python type hints",
    tools=tools,
    tool_choice="auto"
)

while getattr(response, "function_calls", []):
    for f_call in response.function_calls:
        tool_name = f_call.name
        args = f_call.arguments or {}
        if tool_name == "calculator":
            result = calculator(**args)
        elif tool_name == "search_info":
            result = search_info(**args)
        else:
            result = f"Unknown tool: {tool_name}"

        response = client.invoke(
            input="",
            tools=tools,
            tool_choice="auto",
            tool_results=[FunctionCallResultBlock(id=f_call.id, tool=tool_name, result=result)]
        )

print(response.text)
```

## Conversation with memory

Combine everything in a minimal, realistic conversational loop.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE, FunctionCallResultBlock
from datapizzai.clients import ClientFactory
import os

def create_conversational_client():
    memory = Memory()
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
    )
    return client, memory

client, memory = create_conversational_client()
tools = [calculator, search_info]

def chat_turn(user_input: str, memory: Memory, client, tools):
    print(f"👤 User: {user_input}")
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)

    response = client.invoke(
        input="",
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )

    # Iterate function calls until completion
    while getattr(response, "function_calls", []):
        for f_call in response.function_calls:
            fn = {
                "calculator": calculator,
                "search_info": search_info,
            }.get(f_call.name, lambda **_: f"Unknown tool: {f_call.name}")
            res = fn(**(f_call.arguments or {}))
            response = client.invoke(
                input="",
                memory=memory,
                tools=tools,
                tool_choice="auto",
                tool_results=[FunctionCallResultBlock(id=f_call.id, tool=f_call.name, result=res)]
            )

    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    print(f"🤖 Assistant: {response.text}")
```

## Best practices

### Tool design
- Clear name and description
- Validate inputs and handle errors
- Keep output concise and consistent

### Memory management
- Use memory for multi‑turn conversations
- Manage memory size for long chats
- Keep user vs assistant roles clear

## Step‑by‑step: custom tool

This shows how to create, expose, and use a custom tool.

1) Define the tool
```python
from datapizzai.tools import tool

@tool
def extract_emails(text: str, domain: str | None = None) -> list[str]:
    """Extract emails from text; optionally filter by domain."""
    import re
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    emails = re.findall(pattern, text)
    if domain:
        emails = [e for e in emails if e.endswith(domain)]
    return emails
```

2) Create the client
```python
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
import os

load_dotenv()
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)
tools = [extract_emails]
```

3) Invoke and handle function calls iteratively
```python
response = client.invoke(
    input="Find the emails in this text: Contacts: a@example.com, b@test.org",
    tools=tools,
    tool_choice="auto"
)

from datapizzai.type import FunctionCallResultBlock
while getattr(response, "function_calls", []):
    for f_call in response.function_calls:
        res = extract_emails(**(f_call.arguments or {}))
        response = client.invoke(
            input="",
            tools=tools,
            tool_choice="auto",
            tool_results=[FunctionCallResultBlock(id=f_call.id, tool=f_call.name, result=res)]
        )
print(response.text)
```

### Complete example with Google Search

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools.google import google_search_tool
from datapizzai.type import FunctionCallResultBlock

load_dotenv()

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)

response = client.invoke(
    "Who won Wimbledon 2024?",
    tools=[google_search_tool],
    tool_choice="auto"
)

while getattr(response, "function_calls", []):
    for f_call in response.function_calls:
        res = google_search_tool(**(f_call.arguments or {}))
        response = client.invoke(
            input="",
            tools=[google_search_tool],
            tool_choice="auto",
            tool_results=[FunctionCallResultBlock(id=f_call.id, tool=f_call.name, result=res)]
        )
print(response.text)
```

Tips:
- Always define clear docstrings and validate input.
- Avoid `eval` in real systems; use safe libraries or explicit parsing.
- Iterate function calls until they finish, passing results as `FunctionCallResultBlock`.

