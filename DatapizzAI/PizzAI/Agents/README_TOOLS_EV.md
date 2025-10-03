# Multi‑Tool Framework - Datapizza-AI

Guide for creating and using tools with Datapizza-AI. 

## Table of Contents

1. [Tool basic structure](#tool-basic-structure)
2. [Minimal execution with invoke](#minimal-execution-with-invoke)
3. [Multi‑tool client](#multi-tool-client)
4. [Conversation with memory](#conversation-with-memory)
5. [Complete example with Google Search](#complete-example-with-google-search)
6. [Why step in on tool calls](#why-step-in-on-tool-calls)

## Tool basic structure

```python
from datapizza.tools import tool


@tool
def timer_tool(duration: str) -> str:
    """Sets a timer (e.g. "5 minutes")."""
    # DO something (stub)
    return f"Timer set for {duration}"
```

## Minimal execution with invoke

The simplest way to use a tool is to pass it directly to the `invoke` method. The model will then decide if and how to use it based on the prompt.

```python
from dotenv import load_dotenv
import os

load_dotenv()

from datapizza.clients.openai import OpenAIClient
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"), 
    model="gpt-5",
    temperature=1
)

response = client.invoke(
    "Set a timer for 5 minutes",
    tools=[timer_tool],
    tool_choice="auto"
)

print(response.text)
for f_call in response.function_calls or []:
    result = timer_tool(**(f_call.arguments or {}))
    print("tool result:", result)
```

## Multi‑tool client

Example with two tools: a calculator and an information search.

```python
from datapizza.tools import tool


@tool
def calculator(expr: str) -> str:
    """Performs simple calculations safely (demo)."""
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
```

### Execution

```python
from dotenv import load_dotenv
import os

load_dotenv()

from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE
client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

tools = [calculator, search_info]
memory = Memory()

response = client.invoke(
    input="Calculate (25 * 4) + 10 and search information about Python type hints",
    tools=tools,
    tool_choice="auto",
    memory=memory
)

while hasattr(response, "function_calls") and response.function_calls:
    # Add assistant response to memory
    memory.add_turn(response.content, ROLE.ASSISTANT)
    
    # Create tool results and add them one by one to memory
    for f_call in response.function_calls:
        tool_name = f_call.name
        args = f_call.arguments or {}
        
        if tool_name == "calculator":
            result = calculator(**args)
        elif tool_name == "search_info":
            result = search_info(**args)
        else:
            result = f"Unknown tool: {tool_name}"

        tool_result_block = FunctionCallResultBlock(
            id=f_call.id,
            tool=f_call.tool,
            result=result,
        )
        
        # Add each tool result as separate turn with TOOL role
        memory.add_turn([tool_result_block], ROLE.TOOL)

    # Re-invoke with updated memory
    response = client.invoke(
        input=response,
        tools=tools,
        tool_choice="auto",
        memory=memory
    )

print(response.text)
```

## Conversation with memory

For a more realistic experience, let's combine the concepts we've seen so far into an interactive chatbot. The script handles a continuous conversation loop, accepts user input, and uses tools when needed, maintaining context with memory. The loop only ends when the user types "end".

```python
import os
from dotenv import load_dotenv

load_dotenv()

from datapizza.clients.google import GoogleClient
from datapizza.memory import Memory
from datapizza.tools import tool
from datapizza.type import ROLE, TextBlock

# Simple calculator
@tool
def calculator(expr: str) -> str:
    """Performs simple mathematical calculations safely."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(expr) <= allowed:
            return "Error: invalid characters in calculation"
        result = eval(expr)
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {e}"

# Gemini client with tools
client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
)

tools = [calculator, google_search_tool]
memory = Memory()

print("🤖 Chatbot with tools started! Type 'end' to exit.")
print("I can do calculations and search the web for information.")

while True:
    # User input
    user_input = input("\n👤 You: ").strip()
    
    # Check exit conditions
    if user_input.lower() in ["end", "exit", "quit", "stop"]:
        print("👋 Goodbye!")
        break
    
    if not user_input:
        continue
        
    # Add user input to memory
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    try:
        # Invoke model with tools
        response = client.invoke(
            input="",
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )
        
        # Handle function calls if present
        while hasattr(response, "function_calls") and response.function_calls:
            # Add assistant response to memory
            memory.add_turn(response.content, ROLE.ASSISTANT)
            
            # Execute each function call
            for f_call in response.function_calls:
                tool_name = f_call.name
                args = f_call.arguments or {}
                
                print(f"🔧 Using tool: {tool_name}")
                
                # Execute the appropriate tool
                if tool_name == "calculator":
                    result = calculator(**args)
                elif tool_name == "google_search_tool":
                    result = google_search_tool(**args)
                else:
                    result = f"Unknown tool: {tool_name}"

                # Normalise to text (some tools yield ClientResponse objects)
                if hasattr(result, "text"):
                    result_payload = result.text
                else:
                    result_payload = str(result)

                # Add result to memory
                tool_result_block = FunctionCallResultBlock(
                    id=f_call.id,
                    tool=f_call.tool,
                    result=result_payload,
                )
                memory.add_turn([tool_result_block], ROLE.TOOL)
            
            # Call model again with tool results
            response = client.invoke(
                input="",
                memory=memory,
                tools=tools,
                tool_choice="auto"
            )
        
        # Show final response
        if response.text:
            print(f"🤖 Assistant: {response.text}")
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please try with a different question.")
```

## Complete example with Google Search

```python
import os
from dotenv import load_dotenv

load_dotenv()

from datapizza.clients.google import GoogleClient

client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
)

response = client.invoke("When do the Winter Olympics start?", tools=[google_search_tool])

print(response.text)
```

## Why step in on tool calls

Tools keep a human in the loop: whenever the model proposes a `function_call` you can decide whether to run it, tweak it, or block it.

### When stepping in helps
- **Irreversible or sensitive operations**: deletions, filesystem writes, transactions
- **Uncertain parameters**: the model may hallucinate paths, IDs, or queries; validate first
- **External constraints**: rate limits, per-user permissions, company policies
- **Cost and performance**: expensive calls (paid APIs, long jobs) should run only when needed
- **User experience**: confirm or rephrase the action before continuing

For low-risk, idempotent tasks (e.g. lightweight string transformations) you can let the execution stay fully automatic.

### Recommended handling flow
1. Inspect `response.function_calls` and identify the requested tool
2. Validate that parameters are complete, coherent, and authorized
3. Execute the tool or block the operation and explain the reason to the model
4. Return the result (or error) via `FunctionCallResultBlock`

### Example of custom gating
```python
# Helper functions you define locally
tools_map = {
    "web_search": web_search,
    "file_delete": file_delete,
}

for f_call in response.function_calls or []:
    tool_name = f_call.name
    args = f_call.arguments or {}

    if tool_name == "file_delete":
        result = "Operation blocked: explicit approval required"
    elif not params_are_valid(args):
        result = "Parameters are missing or invalid"
    else:
        result_obj = tools_map[tool_name](**args)
        result = result_obj.text if hasattr(result_obj, "text") else str(result_obj)

    tool_result = FunctionCallResultBlock(
        id=f_call.id,
        tool=f_call.tool,
        result=result,
    )
    memory.add_turn([tool_result], ROLE.TOOL)
```

So, when does it really pay off to step in?
- **Governance**: apply different policies depending on who is using the assistant
- **Observability**: controlled logging of when and why a tool is approved or denied
- **Recovery**: send targeted guidance so the model retries with better parameters
- **System protection**: prevent side effects on critical resources or sensitive data
