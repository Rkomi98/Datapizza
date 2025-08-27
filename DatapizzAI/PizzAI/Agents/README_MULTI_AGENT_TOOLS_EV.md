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
   - [Step 5: Conversational flow with memory (throughline)](#step-5-conversational-flow-with-memory-throughline)
4. [Advanced usage patterns](#advanced-usage-patterns)
5. [Best practices](#best-practices)
6. [Framework extension](#framework-extension)
7. [Step-by-step guide: custom tool](#step-by-step-guide-custom-tool)

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
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools import tool

# Load environment variables
load_dotenv()

# To use google_search_tool, add to your .env file:
# GOOGLE_API_KEY=your-google-api-key-here
# GOOGLE_CSE_ID=your-custom-search-engine-id  # Optional

@tool
def calculate(expression: str) -> str:
    """Executes safe mathematical calculations.
    
    Args:
        expression: Mathematical expression (e.g., "2 + 3 * 4")
    
    Returns:
        Calculation result or error message
    """
    try:
        # Security validation
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Characters not allowed"
        
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
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
        Provide clear and detailed explanations."""
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
    input="Calculate the area of a square with side 5",
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
1. Search for information on "machine learning trends 2025"
2. Calculate how many years have passed from 1990 to 2025
"""

response = client.invoke(
    input=complex_query,
    tools=tools,
    tool_choice="auto"
)

# The OpenAI model will automatically choose the necessary tools
tool_results = execute_tool_calls(response, tools)
```

<!-- Removed duplicated base invocation section to avoid redundancy -->

### Step 5: Conversational flow with memory (throughline)

Combine everything into a concise, usable conversational loop.

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
        input="",  # Empty input because we use memory
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )
    
    # IMPORTANT: do not store assistant messages with tool_calls into memory.
    tool_calls = getattr(response, "function_calls", []) or []
    if tool_calls:
        tool_results = execute_tool_calls(response, tools)
        followup = client.invoke(
            input=(
                "Use these tool results to complete the answer:\n" + "\n".join(map(str, tool_results))
            ),
            memory=memory,
            tools=tools,
            tool_choice="auto"
        )
        memory.add_turn([TextBlock(content=followup.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {followup.text}")
    else:
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        print(f"🤖 Assistant: {response.text}")

# 4. Multi-turn conversation example
conversation = [
    "Hello! I'm Mirko, I'm working on an AI project",
    "Search for information on Python frameworks for AI",
    "Calculate the cost if I spend 500€ per month for 2 years",
    "Who won Wimbledon 2024?",
    "Do you remember my name and what I'm doing?"
]

for user_input in conversation:
    chat_turn(user_input, memory, client, tools)
    print()  # Space between turns

# 5. Conversation statistics
print(f"📊 Total turns: {len(memory.memory)}")
print(f"💬 Total blocks: {len(list(memory.iter_blocks()))}")
```

<!-- Removed repetitive implemented tools section to keep the guide concise -->

## Advanced usage patterns

### Sequential workflow
```python
# The client can execute complex workflows
workflow_query = """
    Execute this workflow:
    1. Search for information on machine learning
    2. Calculate how many years have passed from 1990 to 2025
"""

response = client.invoke(
    input=workflow_query,
    tools=[calculate, google_search_tool],
    tool_choice="auto"
)
execute_tool_calls(response, tools)
```

### Intelligent tool selection
```python
# The client automatically chooses the appropriate tool
queries = [
    "Calculate 2 + 2",                    # → calculate
    "Search for information on AI",        # → google_search_tool
    "How much does an AI project cost?"    # → google_search_tool + calculate
]

for query in queries:
    response = client.invoke(
        input=query,
        tools=tools,
        tool_choice="auto"
    )
    print(f"Query: {query}")
    tool_results = execute_tool_calls(response, tools)
    print(f"Tools used: {len(tool_results)}")
```

### Error handling and fallback
```python
# The agent handles errors and fallback automatically
try:
    response = agent.invoke("Calculate something complex")
    
    # Check if tools were used
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"Tool used: {tool_call.tool_name}")
            print(f"Result: {tool_call.result}")
    
except Exception as e:
    print(f"Error in invocation: {e}")
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
    
    def execute(self, input_data: Dict[str, str]) -> ToolResult:
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
    
    def execute(self, endpoint: str) -> ToolResult:
        # Implement API call
        pass
```



## Complete configuration summary

### Implementation checklist

✅ **Environment setup**
- [ ] Virtual environment activated
- [ ] datapizzai library installed
- [ ] `.env` file configured with OPENAI_API_KEY
- [ ] OpenAI connection test completed

✅ **Tool definition**
- [ ] Tools decorated with `@Tool`
- [ ] Complete docstrings with Args/Returns
- [ ] Error handling implemented
- [ ] Safe input validation

✅ **Client configuration**
- [ ] ClientFactory with provider="openai"
- [ ] Appropriate system prompt for use case
- [ ] Model selected (gpt-4o recommended)
- [ ] Optimization parameters configured

✅ **Tool execution**
- [ ] `execute_tool_calls` function implemented
- [ ] Tool map correctly configured
- [ ] Error handling for tools not found
- [ ] Operation logging active

✅ **Conversational memory** (optional)
- [ ] Memory object initialized
- [ ] Turns added correctly
- [ ] Memory size management
- [ ] Multi-turn conversation testing

### Complete template

```python
#!/usr/bin/env python3
"""
Complete template for multi-tool agent with datapizzAI
"""

import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools import Tool
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

# 1. Environment setup
load_dotenv()

# 2. Tool definition
@Tool
def my_tool(param: str) -> str:
    """Tool description."""
    try:
        # Tool logic
        result = f"Processed: {param}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# 3. Client configuration
def create_agent():
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Custom system prompt..."
    )
    return client

# 4. Tool execution
def execute_tool_calls(response, tools):
    tool_results = []
    tool_map = {"my_tool": my_tool}
    
    for block in response.content:
        if hasattr(block, 'name') and hasattr(block, 'arguments'):
            tool_name = block.name
            if tool_name in tool_map:
                result = tool_map[tool_name](**block.arguments)
                tool_results.append(result)
                print(f"🔧 {tool_name}: {result}")
    
    return tool_results

# 5. Main execution
def main():
    client = create_agent()
    tools = [my_tool]
    
    response = client.invoke(
        input="User query",
        tools=tools,
        tool_choice="auto"
    )
    
    tool_results = execute_tool_calls(response, tools)
    
    if response.text.strip():
        print(f"🤖 {response.text}")
    elif tool_results:
        print(f"🤖 {tool_results[0]}")

if __name__ == "__main__":
    main()
```
