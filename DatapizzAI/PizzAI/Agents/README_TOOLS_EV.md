# Multi‑Tool Framework - DatapizzAI

Concise guide for creating and using tools with DatapizzAI. Tools allow the model to perform actions (Python function execution) during reasoning.

## Table of Contents

1. [Tool basic structure](#tool-basic-structure)
2. [Minimal execution with invoke](#minimal-execution-with-invoke)
3. [Multi‑tool client](#multi-tool-client)
4. [Conversation with memory](#conversation-with-memory)
5. [Best practices](#best-practices)
6. [Why step in on tool calls](#why-step-in-on-tool-calls)

## Tool basic structure

```python
from datapizzai.tools import tool

@tool
def timer_tool(duration: str) -> str:
    """Sets a timer (e.g. "5 minutes")."""
    # DO something (stub)
    return f"Timer set for {duration}"
```

## Minimal execution with invoke

```python
from datapizzai.clients import OpenAIClient
from dotenv import load_dotenv
import os

load_dotenv()
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

print(response.text)  # Any text response
for f_call in response.function_calls or []:
    # Execute the local tool with suggested arguments
    result = timer_tool(**(f_call.arguments or {}))
    print("tool result:", result)
```

## Multi‑tool client

Example with two tools: a calculator and an information search.

```python
from datapizzai.tools import tool

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
# Client and Memory  
from datapizzai.clients import OpenAIClient
from datapizzai.memory import Memory
from datapizzai.type import FunctionCallResultBlock, ROLE
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAIClient(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

tools = [calculator, search_info]
memory = Memory()

response = client.invoke(
    input="Calculate (25 * 4) + 10 and search information about Python type hints",
    tools=tools,
    tool_choice="auto",
    memory=memory
)

# Iterative function call execution
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
        input="",
        tools=tools,
        tool_choice="auto",
        memory=memory
    )

print(response.text)
```

## Conversation with memory

Now let's bring everything together in a minimal and realistic conversational cycle.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

def create_conversational_client():
    memory = Memory()
    client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
    )
    return client, memory

# 3. Configure multi‑turn conversation
client, memory = create_conversational_client()
tools = [calculator, search_info]

def chat_turn(user_input, memory, client, tools):
    """Handles a single conversation turn with tools"""
    print(f"👤 User: {user_input}")
    
    # Add user input to memory
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # First model call
    response = client.invoke(
        input="",  # Empty input because we use memory
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )
    
    # Iterative function call handling
    while hasattr(response, "function_calls") and response.function_calls:
        print("🔧 Executing tool calls...")
        
        # Add assistant response to memory
        memory.add_turn(response.content, ROLE.ASSISTANT)
        
        # Execute each function call
        for f_call in response.function_calls:
            print(f"   📞 {f_call.name}({f_call.arguments})")
            
            # Execute the tool (your existing code works fine)
            result = {
                "calculator": calculator,
                "search_info": search_info,
            }.get(f_call.name, lambda **_: f"Unknown tool: {f_call.name}")(**(f_call.arguments or {}))
            
            print(f"   ✅ {result}")
            
            # Create result block
            tool_result_block = FunctionCallResultBlock(
                id=f_call.id, 
                tool=f_call.tool, 
                result=result
            )
            memory.add_turn([tool_result_block], ROLE.TOOL)
        response = client.invoke(
            input="",
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )
    
    # Add final response to memory
    if response.text:
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {response.text}")

# 4. Multi-turn conversation example
conversation = [
    "Hello! I'm Mike, I'm working on an AI project",
    "Search for information about Python AI frameworks", 
    "Calculate the cost if I spend 500€ per month for 2 years",
    "Do you remember my name and what I'm doing?"
]

for user_input in conversation:
    chat_turn(user_input, memory, client, tools)
    print()  # Space between turns

# 5. Conversation statistics
print(f"📊 Total turns: {len(memory.memory)}")
print(f"💬 Total blocks: {len(list(memory.iter_blocks()))}")
```

## Best practices

### Tool design
- **Descriptive name**: Use clear and specific names
- **Detailed description**: Explain exactly what the tool does
- **Clear input schema**: Define precisely the input format
- **Error handling**: Always handle exceptions and return appropriate ToolResult

### Complete example with Google Search

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import GoogleClient
from datapizzai.tools.google import google_search_tool

load_dotenv()

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
        result = tools_map[tool_name](**args)

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
