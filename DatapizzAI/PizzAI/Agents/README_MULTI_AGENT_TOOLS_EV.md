# Multi Tool Framework - DatapizzAI

Complete guide for creating and using multi-tool clients with the datapizzai framework. Clients can use different tools to complete complex tasks and automate workflows through the OpenAI API.

## Table of contents

1. [Fundamental concepts](#fundamental-concepts)
2. [Basic structure of a tool](#basic-structure-of-a-tool)
3. [Step-by-step configuration](#step-by-step-configuration)
   - [Step 1: Tool definition](#step-1-tool-definition)
   - [Step 2: OpenAI client creation](#step-2-openai-client-creation)
   - [Step 3: Configuration and execution](#step-3-configuration-and-execution)
   - [Step 4: Advanced multi-tool client](#step-4-advanced-multi-tool-client)
   - [Step 5: Conversational memory](#step-5-conversational-memory)
4. [Best practices](#best-practices)
5. [Framework extension](#framework-extension)
6. [Step-by-step guide: custom tool](#step-by-step-guide-custom-tool)

## Fundamental concepts

### Client with Tools
A client is an AI interface that can use tools to complete tasks. Each client has:
- **Provider**: Connection to the AI model (OpenAI, Google, etc.)
- **Model**: Specific model (gpt-4o, gemini, etc.)
- **System Prompt**: Instructions for client behavior
- **Tools**: List of available tools for invocation

### Tool
A tool is a Python function decorated with `@tool` that the client can invoke. Each tool has:
- **Name**: Unique identifier
- **Description**: Explanation of what the tool does (from docstring)
- **Parameters**: Defined by function signature
- **Return**: Value returned by the function

### Function calling at a glance

Function calling lets the model "call" Python functions that you expose as tools. In practice:
- You define Python functions and decorate them with `@tool` (name, description, argument schema).
- Guided by the system prompt and context, the model can return a structured request to invoke a tool with specific arguments.
- Your runtime executes the Python function with those arguments and returns the output to the model or the user.
- With `tool_choice="auto"`, the model decides when to use tools; alternatively, you can force a specific tool.

## Basic structure of a tool

```python
from datapizzai.tools import tool

@tool
def my_tool(parameter: str) -> str:
    """Description of what this tool does.
    
    Args:
        parameter: Parameter description
        
    Returns:
        Result of the operation
    """
    try:
        # Implement tool logic
        result = process_input(parameter)
        return f"Result: {result}"
        
    except Exception as e:
        return f"Error: {str(e)}"
```

## Step-by-step configuration

### Step 1: Tool definition

Tools are Python functions decorated with `@tool` that the client can invoke:

```python
import os
import re
import ast
import math
import numpy as np
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools import tool

# Load environment variables
load_dotenv()

# Safe evaluation setup
ALLOWED_FUNCS = {
    # base & powers/logs
    "sqrt": np.sqrt, "log": np.log, "log10": np.log10, "exp": np.exp,
    "abs": abs, "round": round, "min": np.minimum, "max": np.maximum,
    # trig
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
}
ALLOWED_CONSTS = {"pi": math.pi, "e": math.e}
ALLOWED_BINOPS = {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow}
ALLOWED_UNARYOPS = {ast.UAdd, ast.USub}
MAX_EXPR_LEN, MAX_NODES = 2000, 800

def _normalize(s: str) -> str:
    s = s.strip()
    if len(s) > MAX_EXPR_LEN: raise ValueError("Expression is too long")
    s = s.replace("^", "**")                # power
    s = re.sub(r"√\s*\(", "sqrt(", s)       # root symbol → sqrt(
    s = re.sub(r"(\d)\s*π", r"\1*pi", s)    # 2π → 2*pi
    return s

def _safe_eval(node):
    if isinstance(node, ast.Expression): return _safe_eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)): return node.value
        raise ValueError("Non-numeric constant")
    if isinstance(node, ast.Name):
        if node.id in ALLOWED_CONSTS: return ALLOWED_CONSTS[node.id]
        raise ValueError(f"Identifier not allowed: {node.id}")
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARYOPS:
        v = _safe_eval(node.operand); return +v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINOPS:
        a, b = _safe_eval(node.left), _safe_eval(node.right)
        if   isinstance(node.op, ast.Add): return a + b
        elif isinstance(node.op, ast.Sub): return a - b
        elif isinstance(node.op, ast.Mult): return a * b
        elif isinstance(node.op, ast.Div): return a / b
        elif isinstance(node.op, ast.FloorDiv): return a // b
        elif isinstance(node.op, ast.Mod): return a % b
        elif isinstance(node.op, ast.Pow):
            if isinstance(b, int) and abs(b) > 1000: raise ValueError("Exponent is too large")
            return a ** b
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and not node.keywords:
            fn = ALLOWED_FUNCS.get(node.func.id)
            if not fn: raise ValueError("Function not allowed")
            args = [_safe_eval(a) for a in node.args]
            if len(args) > 8: raise ValueError("Too many arguments")
            return fn(*args)
    raise ValueError("Syntax not allowed")

@tool
def calculate(expression: str) -> str:
    """
    Safely evaluates a mathematical expression using an Abstract Syntax Tree (AST).
    Supports basic arithmetic, powers, roots, logarithms, and trigonometric functions.
    """
    try:
        src = _normalize(expression)
        tree = ast.parse(src, mode="eval")
        # You could add a complexity check here by walking the tree
        val = _safe_eval(tree)
        if isinstance(val, float) and val.is_integer(): val = int(val) # clean output
        return f"Result: {val}"
    except Exception as e:
        return f"Error: {e}"
```

### Step 2: OpenAI client creation

The client manages the connection to the OpenAI API and function calling logic:

```python
def create_calculator_client():
    """Creates a client specialized in mathematical calculations."""
    
    client = ClientFactory.create(
        provider="openai",                    # AI provider
        api_key=os.getenv("OPENAI_API_KEY"),  # API key from .env
        model="gpt-4o",                       # OpenAI model
        system_prompt="""You are an expert mathematical assistant.
        Always use the 'calculate' tool to perform mathematical operations.
        Provide clear and detailed explanations.""",
        temperature=1,
    )
    
    if not client:
        raise ValueError("❌ Unable to create OpenAI client")
    
    return client
```

### Step 3: Configuration and execution

```python
# 1. Create the client
client = create_calculator_client()

# 2. Define available tools
tools = [calculate]

# 3. Execute query with automatic tool selection
response = client.invoke(
    input="Let $k = \\lceil{\\sqrt{m + n}}\\rceil$, where $n$ and $m$ are two distinct natural numbers less than $100$. Find the maximum value of $k$.",
    tools=tools,
    tool_choice="auto"  # OpenAI automatically chooses when to use tools
)

# 4. Handle results
def execute_tool_calls(response, available_tools):
    """Executes function calls using the provided tools (not textual content)."""
    tool_results = []
    tool_map = {t.name: t for t in available_tools}

    for call in getattr(response, "function_calls", []) or []:
        tool_name = getattr(call, "name", None)
        arguments = getattr(call, "arguments", {}) or {}

        print(f"🔧 Tool called: {tool_name}")
        print(f"📋 Arguments: {arguments}")

        if tool_name in tool_map:
            result = tool_map[tool_name](**arguments)
            tool_results.append(result)
            print(f"✅ Result: {result}")
        else:
            print(f"⚠️ Unknown tool: {tool_name}")
    
    return tool_results

# 5. Execute tools and show results
tool_results = execute_tool_calls(response, tools)

# 6. Show final response
if response.text.strip():
    print(f"🤖 Assistant: {response.text}")
elif tool_results:
    print(f"🤖 Assistant: {tool_results[0]}")
```

### Step 4: Advanced multi-tool client

To create a client with multiple tools, follow these steps:

```python
# 1. Use the built-in Google search tool
from datapizzai.tools.google import google_search_tool

# The google_search_tool is ready to use with datapizzai 3.0.8
# Requires GOOGLE_API_KEY in .env file for Google Custom Search API

# Direct usage example:
# response = client.invoke("Who won Wimbledon 2024?", tools=[google_search_tool])


# 2. Create multi-tool client
def create_multi_tool_client():
    """Creates a client with access to all tools."""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""You are a versatile AI assistant with access to specialized tools:

        - calculate: for mathematical operations
        - google_search_tool: for real web searches via Google

        Analyze each request and choose the most appropriate tool.
        For complex tasks, you can use multiple tools in sequence.
        Always explain what you're doing and why."""
    )
    
    return client

# 3. Configure all tools
tools = [calculate, google_search_tool]

# 4. Execute complex workflows
client = create_multi_tool_client()

complex_query = """
Execute this workflow:
1. Calculate how many years have passed from 1990 to 2025
2. Search for information on "machine learning trends 2025"
"""

response = client.invoke(
    input=complex_query,
    tools=tools,
    tool_choice="auto"
)

# The OpenAI model will automatically choose the necessary tools
tool_results = execute_tool_calls(response, tools)
```

### Step 5: Conversational memory

Combine everything into a minimal, realistic conversational loop.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

def create_conversational_client():
    """Creates a conversational client with memory."""
    
    # 1. Initialize memory
    memory = Memory()
    
    # 2. Create client with system prompt for conversations
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""You are a friendly AI assistant with conversational memory.
        Remember details from previous conversations and refer to them when appropriate.
        Use available tools to help users with specific tasks."""
    )
    
    return client, memory

# 3. Configure multi-turn conversation
client, memory = create_conversational_client()
tools = [calculate, google_search_tool]

def chat_turn(user_input: str, memory: Memory, client, tools):
    """Handles a turn: updates memory, invokes client, executes function calls."""
    
    print(f"👤 User: {user_input}")
    
    # Add user input to memory
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Invoke client with memory and tools
    response = client.invoke(
        input="",
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )
    
    # NEVER add response.content to memory if it contains function_calls
    tool_calls = getattr(response, "function_calls", []) or []
    
    if tool_calls:
        # Execute tools (reuse your function)
        tool_results = execute_tool_calls(response, tools)
    
        # Re-invoke, passing the results as text (no tool_calls in memory)
        followup = client.invoke(
            input="Use these tool results to complete the answer:\n" + "\n".join(map(str, tool_results)),
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )
    
        # Add only the final text to memory
        memory.add_turn([TextBlock(content=followup.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {followup.text}")
    
    else:
        # No tools: save normally
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {response.text}")

# 4. Multi-turn conversation example
conversation = [
    "Hello! I'm Mike, working on an AI project.",
    "Search for information on Python frameworks for AI.",
    "Calculate the cost if I spend $500 per month for 2 years.",
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
- **Clear input schema**: Precisely define input format
- **Error handling**: Always handle exceptions and return appropriate ToolResult

### Agent system prompt
- **Clear instructions**: Explain when and how to use each tool
- **Fallback**: Define what to do if no tool is appropriate
- **Output format**: Specify desired response format

### Memory management
- **Persistent context**: Use memory for multi-turn conversations
- **Memory cleanup**: Manage memory size for long conversations
- **Role separation**: Maintain clear distinction between user and assistant

## Framework extension

### Creating new tools
```python
from datapizzai.tools import Tool
from typing import Dict

class DatabaseTool(Tool):
    """Tool for database operations"""
    
    def __init__(self, connection_string: str):
        super().__init__(
            name="database",
            description="Executes database queries",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "operation": {"type": "string", "enum": ["select", "insert", "update", "delete"]}
                }
            }
        )
        self.connection_string = connection_string
    
    def execute(self, input_data: Dict[str, str]):
        # Implement database logic
        pass
```

### Tools with configuration parameters
```python
class APITool(Tool):
    """Tool for external API calls"""
    
    def __init__(self, base_url: str, api_key: str):
        super().__init__(
            name="api_client",
            description="Executes API calls",
            input_schema={"type": "string"}
        )
        self.base_url = base_url
        self.api_key = api_key
    
    def execute(self, endpoint: str):
        # Implement API call
        pass
```

## Step-by-step guide: custom tool

This guide shows how to create, expose, and use a custom tool with the datapizzai library.

1. Define the tool with `@tool`
   ```python
   from datapizzai.tools import tool

   @tool
   def extract_emails(text: str, domain: str | None = None) -> list[str]:
       """Extracts emails from text; optionally filters by domain.

       Args:
           text: Input text
           domain: If set, returns only emails ending with that domain

       Returns:
           A list of found emails
       """
       import re
       pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
       emails = re.findall(pattern, text)
       if domain:
           emails = [e for e in emails if e.endswith(domain)]
       return emails
   ```

2. Create the client
   ```python
   import os
   from dotenv import load_dotenv
   from datapizzai.clients import ClientFactory

   load_dotenv()
   client = ClientFactory.create(
       provider="openai",
       api_key=os.getenv("OPENAI_API_KEY"),
       model="gpt-4o",
       system_prompt=(
           "You are an assistant that can use tools. If the user asks for email extraction, "
           "always use the 'extract_emails' tool."
       ),
   )
   tools = [extract_emails]
   ```

3. Invoke and handle function calls
   ```python
   response = client.invoke(
       input="Find the emails in this text: Contacts: a@example.com, b@test.org",
       tools=tools,
       tool_choice="auto"
   )

   def execute_tool_calls(response, available_tools):
       tool_map = {t.name: t for t in available_tools}
       results = []
       for call in getattr(response, "function_calls", []) or []:
           name = getattr(call, "name", "")
           args = getattr(call, "arguments", {}) or {}
           res = tool_map[name](**args) if name in tool_map else f"Unknown tool: {name}"
           results.append(f"{name}: {res}")
       return results

   tool_results = execute_tool_calls(response, tools)

   # If tools were executed, re-invoke passing the results as text
   if tool_results:
       followup = client.invoke(
           input="Use these tool results to complete the answer:\n" + "\n".join(tool_results),
           tools=tools,
           tool_choice="auto"
       )
       print(followup.text)
   else:
       print(response.text)
   ```

### Complete example with Google Search

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools.google import google_search_tool

load_dotenv()

# Make sure you have GOOGLE_API_KEY in your .env file
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are an assistant that can search for information on Google."
)

# Direct usage
response = client.invoke(
    "Who won Wimbledon 2024?", 
    tools=[google_search_tool],
    tool_choice="auto"
)
    
# Handle results as in previous examples
tool_results = execute_tool_calls(response, [google_search_tool])
if tool_results:
    followup = client.invoke(
        f"Use these results to answer: {tool_results[0]}",
        tools=[google_search_tool]
    )
    print(followup.text)
```

Tips:
- Always define clear docstrings (Args/Returns) and validate input.
- Avoid `eval` in real-world cases; prefer safe libraries or explicit parsing.
- If using conversational memory, do not add an assistant message containing tool_calls to memory without first providing the corresponding tool messages; without native support for "tool" messages, re-send the results as text (as in the example above).
