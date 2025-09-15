# Multi‑Tool cookbook

In this guide we will show you how to create and use tools with DatapizzAI. Tools let the model perform actions (call Python functions) while reasoning.

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
from datapizzai.memory import Memory
from datapizzai.type import FunctionCallResultBlock, ROLE
import os

load_dotenv()
client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

tools = [calculator, search_info]
memory = Memory()

response = client.invoke(
    input="Calculate (25 * 4) + 10 and search info on Python type hints",
    tools=tools,
    tool_choice="auto",
    memory=memory
)

# Iteratively execute function calls and feed results via Memory
while hasattr(response, "function_calls") and response.function_calls:
    # Add assistant output to memory
    memory.add_turn(response.content, ROLE.ASSISTANT)

    for f_call in response.function_calls:
        tool_name = f_call.name
        args = f_call.arguments or {}
        
        if tool_name == "calculator":
            result = calculator(**args)
        elif tool_name == "search_info":
            result = search_info(**args)
        else:
            result = f"Unknown tool: {tool_name}"

        # Add each tool result as a TOOL turn
        tool_result_block = FunctionCallResultBlock(
            id=f_call.id,
            tool=f_call.tool,
            result=result,
        )
        memory.add_turn([tool_result_block], ROLE.TOOL)

    # Re‑invoke with updated memory
    response = client.invoke(
        input="",
        tools=tools,
        tool_choice="auto",
        memory=memory
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

# 3. Configure multi‑turn conversation
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

    # Handle function calls iteratively using Memory
    while hasattr(response, "function_calls") and response.function_calls:
        # Add assistant output to memory
        memory.add_turn(response.content, ROLE.ASSISTANT)

        for f_call in response.function_calls:
            # Execute chosen tool
            result = {
                "calculator": calculator,
                "search_info": search_info,
            }.get(f_call.name, lambda **_: f"Unknown tool: {f_call.name}")(**(f_call.arguments or {}))

            # Add tool result as TOOL turn
            memory.add_turn([
                FunctionCallResultBlock(id=f_call.id, tool=f_call.tool, result=result)
            ], ROLE.TOOL)

        # Re‑invoke with updated memory
        response = client.invoke(
            input="",
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )

    if response.text:
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {response.text}")
```

## Best practices

### Tool design
- Clear, descriptive name
- Detailed description of purpose
- Clear input schema (types and constraints)
- Robust error handling with informative messages

## Step‑by‑step: custom tool

This shows how to create, expose, and use a custom tool using the Memory‑based pattern.

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
from datapizzai.memory import Memory
import os

load_dotenv()
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)
tools = [extract_emails]
memory = Memory()
```

3) Invoke and handle function calls iteratively
```python
from datapizzai.type import FunctionCallResultBlock, ROLE, TextBlock

prompt = "Find the emails in this text: Contacts: a@example.com, b@test.org"
memory.add_turn([TextBlock(content=prompt)], ROLE.USER)

response = client.invoke(input="", tools=tools, tool_choice="auto", memory=memory)

while hasattr(response, "function_calls") and response.function_calls:
    memory.add_turn(response.content, ROLE.ASSISTANT)
    for f_call in response.function_calls:
        res = extract_emails(**(f_call.arguments or {}))
        memory.add_turn([FunctionCallResultBlock(id=f_call.id, tool=f_call.tool, result=res)], ROLE.TOOL)
    response = client.invoke(input="", tools=tools, tool_choice="auto", memory=memory)

print(response.text)
```

### Complete example with Google Search

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools.google import google_search_tool

load_dotenv()

# Make sure you have GOOGLE_API_KEY in your .env
client = ClientFactory.create(
    provider="google",
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
)

response = client.invoke("When do the Winter Olympics start?", tools=[google_search_tool])

print(response.text)
```

Tips:
- Always define clear docstrings and validate input.
- Avoid `eval` in real systems; use safe libraries or explicit parsing.
- Iterate function calls until they finish, passing results as `FunctionCallResultBlock`.
