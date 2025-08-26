# Multi Tool Framework - DatapizzAI

Complete guide for creating and using multi-tool clients with the datapizzai framework. Clients can use different tools to complete complex tasks and automate workflows through the OpenAI API.

## Table of contents

1. [Fundamental concepts](#fundamental-concepts)
2. [Basic structure of a Tool](#basic-structure-of-a-tool)
3. [Step-by-step configuration](#step-by-step-configuration)
   - [Step 1: Tool definition](#step-1-tool-definition)
   - [Step 2: OpenAI client creation](#step-2-openai-client-creation)
   - [Step 3: Configuration and execution](#step-3-configuration-and-execution)
   - [Step 4: Advanced multi-tool agent](#step-4-advanced-multi-tool-agent)
   - [Step 5: Conversational memory](#step-5-conversational-memory)
4. [Implemented tool examples](#implemented-tool-examples)
5. [Advanced usage patterns](#advanced-usage-patterns)
6. [Best practices](#best-practices)
7. [Framework extension](#framework-extension)
8. [Complete configuration summary](#complete-configuration-summary)

## Fundamental concepts

### Client with Tools
A client is an AI interface that can use tools to complete tasks. Each client has:
- **Provider**: Connection to the AI model (OpenAI, Google, etc.)
- **Model**: Specific model (gpt-4o, gemini, etc.)
- **System Prompt**: Instructions for client behavior
- **Tools**: List of available tools for invocation

### Tool
A tool is a Python function decorated with `@Tool` that the client can invoke. Each tool has:
- **Name**: Unique identifier
- **Description**: Explanation of what the tool does (from docstring)
- **Parameters**: Defined by function signature
- **Return**: Value returned by the function

## Basic structure of a Tool

```python
from datapizzai.tools import Tool

@Tool
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

Tools are Python functions decorated with `@Tool` that the OpenAI client can invoke:

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.tools import Tool

# Load environment variables
load_dotenv()

@Tool
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
    """Executes tool calls and returns results."""
    tool_results = []
    
    for block in response.content:
        if hasattr(block, 'name') and hasattr(block, 'arguments'):
            tool_name = block.name
            arguments = block.arguments
            
            print(f"🔧 Tool called: {tool_name}")
            print(f"📋 Arguments: {arguments}")
            
            # Execute the tool
            if tool_name == "calculate":
                result = calculate(**arguments)
                tool_results.append(result)
                print(f"✅ Result: {result}")
    
    return tool_results

# 5. Execute tools and show results
tool_results = execute_tool_calls(response, tools)

# 6. Show final response
if response.text.strip():
    print(f"🤖 Assistant: {response.text}")
elif tool_results:
    print(f"🤖 Assistant: {tool_results[0]}")
```

### Step 4: Advanced multi-tool agent

To create an agent with multiple tools, follow these steps:

```python
# 1. Define additional tools
@Tool
def search_information(query: str) -> str:
    """Simulates a web search to find information.
    
    Args:
        query: Search term
    
    Returns:
        Simulated search results
    """
    query_lower = query.lower()
    
    if "python" in query_lower:
        results = [
            "Python is an interpreted programming language",
            "Official documentation: python.org",
            "Tutorials available for beginners"
        ]
    elif "ai" in query_lower:
        results = [
            "Artificial Intelligence: computer science field",
            "Machine Learning is a subset of AI",
            "Applications: NLP, computer vision, robotics"
        ]
    else:
        results = [f"Results for '{query}' not available in demo"]
    
    return f"Results for '{query}':\n" + "\n".join(f"- {r}" for r in results)

@Tool  
def manage_file(command: str, path: str) -> str:
    """Manages files and directories in a simulated system.
    
    Args:
        command: Operation to execute (list, create, delete)
        path: File or directory path
    
    Returns:
        Operation result
    """
    # File system simulation
    files_system = {
        "docs/": ["README.md", "guide.txt"],
        "src/": ["main.py", "utils.py"],
        "data/": ["dataset.csv", "config.json"]
    }
    
    if command == "list":
        if path in files_system:
            files = files_system[path]
            return f"Content of {path}:\n" + "\n".join(f"- {f}" for f in files)
        return f"Directory {path} not found"
    
    elif command == "create":
        return f"File {path} created successfully"
    
    elif command == "delete":
        return f"File {path} deleted successfully"
    
    return f"Command '{command}' not supported"

# 2. Create multi-tool client
def create_multi_tool_client():
    """Creates a client with access to all tools."""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""You are a versatile AI assistant with access to specialized tools:

        - calculate: for mathematical operations
        - search_information: for simulated web searches  
        - manage_file: for file and directory operations

        Analyze each request and choose the most appropriate tool.
        For complex tasks, you can use multiple tools in sequence.
        Always explain what you're doing and why."""
    )
    
    return client

# 3. Configure all tools
tools = [calculate, search_information, manage_file]

# 4. Execute complex workflows
client = create_multi_tool_client()

complex_query = """
Execute this workflow:
1. Search for information on machine learning
2. Calculate how many years have passed from 1990 to 2025
3. Create a file called ml_summary.txt in the docs/ directory
4. List files in the docs/ directory to verify
"""

response = client.invoke(
    input=complex_query,
    tools=tools,
    tool_choice="auto"
)

# The OpenAI model will automatically choose the necessary tools
tool_results = execute_tool_calls(response, tools)
```

Let's review the basic invocation to use the client

```python
# Simple query with tool
response = client.invoke(
    input="Calculate 15 + 27 * 3",
    tools=tools,
    tool_choice="auto"
)

# Tool call handling
def execute_tool_calls(response, available_tools):
    """Executes tool calls present in the response"""
    tool_results = []
    
    for block in response.content:
        if hasattr(block, 'name') and hasattr(block, 'arguments'):
            tool_name = block.name
            arguments = block.arguments
            
            # Map of available tools
            tool_map = {
                "calculate": calculate,
                "search_information": search_information,
                "manage_file": manage_file
            }
            
            if tool_name in tool_map:
                result = tool_map[tool_name](**arguments)
                tool_results.append(result)
                print(f"🔧 {tool_name}: {result}")
    
    return tool_results

# Execute tools
tool_results = execute_tool_calls(response, tools)

# Complex query with multi-step workflow
complex_query = """
    Execute this workflow:
    1. Search for information on Python
    2. Calculate 2^10
    3. Create a file called summary.txt
"""

response = client.invoke(
    input=complex_query,
    tools=tools,
    tool_choice="auto"
)
execute_tool_calls(response, tools)
```

### Step 5: Conversational memory

To maintain context between multiple conversation turns:

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

def create_conversational_agent():
    """Creates an agent with conversational memory."""
    
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
client, memory = create_conversational_agent()
tools = [calculate, search_information, manage_file]

def chat_turn(user_input: str, memory: Memory, client, tools):
    """Handles a single conversation turn."""
    
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
    
    # Add response to memory
    memory.add_turn(response.content, ROLE.ASSISTANT)
    
    # Execute any tool calls
    tool_results = execute_tool_calls(response, tools)
    
    # Show response
    if response.text.strip():
        print(f"🤖 Assistant: {response.text}")
    elif tool_results:
        print(f"🤖 Assistant: {tool_results[0]}")
    
    return response

# 4. Multi-turn conversation example
conversation = [
    "Hello! I'm Mirko, I'm working on an AI project",
    "Search for information on Python frameworks for AI",
    "Calculate the cost if I spend 500€ per month for 2 years",
    "Create a project file called ai_project.txt",
    "Do you remember my name and what I'm doing?"
]

for user_input in conversation:
    chat_turn(user_input, memory, client, tools)
    print()  # Space between turns

# 5. Conversation statistics
print(f"📊 Total turns: {len(memory.memory)}")
print(f"💬 Total blocks: {len(list(memory.iter_blocks()))}")
```

## Implemented tool examples

### Tool: calculate
**Purpose**: Executes safe mathematical calculations
**Input**: Mathematical expression as string
**Output**: Calculation result

```python
# Direct usage example
result = calculate("(15 + 5) * 2")
print(result)  # "Result: 40"

# Example with client
response = client.invoke(
    input="Calculate the area of a square with side 5",
    tools=[calculate],
    tool_choice="auto"
)
```

### Tool: search_information
**Purpose**: Simulates web searches

**Input**: Search query

**Output**: Simulated results

```python
# Direct usage example
result = search_information("Python programming")
print(result)  # Simulated results for Python

# Example with client
response = client.invoke(
    input="Search for information on machine learning",
    tools=[search_information],
    tool_choice="auto"
)
```

### Tool: manage_file
**Purpose**: Manages files and directories (simulated)
**Input**: Command and path
**Output**: Operation result

```python
# Direct usage example
result = manage_file("list", "docs/")
print(result)  # List files in docs/

result = manage_file("create", "docs/new.txt")
print(result)  # Creation confirmation

# Example with client
response = client.invoke(
    input="Create a file called report.txt in the docs/ directory",
    tools=[manage_file],
    tool_choice="auto"
)
```

## Advanced usage patterns

### Sequential workflow
```python
# The client can execute complex workflows
workflow_query = """
    Execute this workflow:
    1. Search for information on machine learning
    2. Calculate how many years have passed from 1990 to 2025
    3. Create a file called ml_summary.txt
    4. Verify the file was created
"""

response = client.invoke(
    input=workflow_query,
    tools=[calculate, search_information, manage_file],
    tool_choice="auto"
)
execute_tool_calls(response, tools)
```

### Intelligent tool selection
```python
# The client automatically chooses the appropriate tool
queries = [
    "Calculate 2 + 2",                    # → calculate
    "Search for information on AI",        # → search_information
    "Create a file called test.txt",       # → manage_file
    "How much does an AI project cost?"    # → search_information + calculate
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
