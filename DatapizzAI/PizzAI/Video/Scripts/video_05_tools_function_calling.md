# Video 5: Tools and Function Calling

## Introduction (1.5 min)

Welcome back! Up until now, our LLMs could only generate text. They could explain things, answer questions, write code—but they couldn't actually do anything.

That changes today with tools and function calling.

[Visual: Show chatbot connected to various tools - calculator, search, database]

Function calling lets LLMs take actions. Need to fetch data from an API? Search the web? Run calculations? The model can decide to use tools and execute them.

This is how you build agents, not just chatbots. This is how you connect LLMs to the real world.

By the end of this video, you'll know how to define tools, control when they're used, and build interactive applications that combine reasoning with action.

Let's get into it.

[Transition: "What Are Tools?"]

## Content Main (7.5 min)

### Defining Your First Tool (2 min)

A tool is just a Python function with a decorator. That's it. Let me show you:

[Show code]

```python
from datapizza.tools import tool

@tool
def calculator(expression: str) -> str:
    """Performs simple calculations safely."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            return "Error: invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"
```

The `@tool` decorator tells Datapizza-AI this function can be called by the model. The docstring is important—it tells the model what the tool does.

[Highlight the docstring]

The model reads that docstring and decides whether to use this tool based on the user's request. Clear documentation means better tool selection.

Now let's use it:

```python
response = client.invoke(
    "Calculate 25 * 4 + 100",
    tools=[calculator],
    tool_choice="auto"
)

# Check if the model called the function
if response.function_calls:
    for call in response.function_calls:
        result = calculator(**(call.arguments or {}))
        print(f"Tool result: {result}")

print(response.text)
```

[Run and show output]

The model sees the question, realizes it needs calculation, and returns a function call instead of text. We execute the tool and get the result.

This is the basic pattern: define tool, pass to invoke, check for function calls, execute them.

### Multi-Tool Interactions (2.5 min)

Real applications use multiple tools. Let me show you a practical example with a calculator and search function.

[Show code]

```python
@tool
def calculator(expr: str) -> str:
    """Performs calculations."""
    try:
        return str(eval(expr))
    except Exception as e:
        return f"Error: {e}"

@tool
def search_info(query: str) -> str:
    """Searches for information."""
    # In production, this would hit a real search API
    return f"Results for: {query}"

tools = [calculator, search_info]
memory = Memory()

response = client.invoke(
    "Calculate 25 * 4, then search for Python tutorials",
    tools=tools,
    memory=memory
)
```

[Show the interaction]

Here's where it gets interesting. The model might need multiple tool calls to answer one question. You need a loop to handle this:

```python
from datapizza.type import FunctionCallResultBlock

while response.function_calls:
    # Add the model's response to memory
    memory.add_turn(response.content, ROLE.ASSISTANT)
    
    # Execute each tool call
    for call in response.function_calls:
        if call.name == "calculator":
            result = calculator(**(call.arguments or {}))
        elif call.name == "search_info":
            result = search_info(**(call.arguments or {}))
        else:
            result = f"Unknown tool: {call.name}"
        
        # Add tool result to memory
        tool_result = FunctionCallResultBlock(
            id=call.id,
            tool=call.tool,
            result=result
        )
        memory.add_turn([tool_result], ROLE.TOOL)
    
    # Call the model again with tool results
    response = client.invoke(
        input=response,
        tools=tools,
        memory=memory
    )
```

[Walk through this carefully]

This loop handles the full tool execution cycle: the model calls tools, we execute them, add results to memory, and invoke again. The model sees those results and either calls more tools or generates a final text response.

[Visual: Show flowchart of the tool execution loop]

This is how agents work under the hood. It's a loop of reasoning and action.

### Building a Conversational Tool Interface (3 min)

Now let's combine everything into a practical chatbot with tools.

[Show complete code]

```python
from datapizza.tools import tool
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock, FunctionCallResultBlock

@tool
def calculator(expr: str) -> str:
    """Performs mathematical calculations."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(expr) <= allowed:
            return "Error: invalid characters"
        return f"Result: {eval(expr)}"
    except Exception as e:
        return f"Error: {e}"

client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash"
)

tools = [calculator]
memory = Memory()

print("Chatbot with tools ready! Type 'exit' to quit.")

while True:
    user_input = input("\nYou: ").strip()
    
    if user_input.lower() in ["exit", "quit"]:
        break
    
    if not user_input:
        continue
    
    # Add user message
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Get response
    response = client.invoke(
        input="",
        memory=memory,
        tools=tools,
        tool_choice="auto"
    )
    
    # Handle tool calls
    while response.function_calls:
        memory.add_turn(response.content, ROLE.ASSISTANT)
        
        for call in response.function_calls:
            print(f"[Using tool: {call.name}]")
            
            result = calculator(**(call.arguments or {}))
            
            tool_result = FunctionCallResultBlock(
                id=call.id,
                tool=call.tool,
                result=result
            )
            memory.add_turn([tool_result], ROLE.TOOL)
        
        response = client.invoke(
            input="",
            memory=memory,
            tools=tools
        )
    
    # Show final response
    print(f"Bot: {response.text}")
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

[Run the chatbot, show conversation]

Try asking: "What's 150 * 83? And what's half of that?"

[Demonstrate the tool being called multiple times]

The model uses the calculator when needed, but answers conversational questions normally. It knows when to use tools and when to just respond.

This is the foundation of agentic behavior—combining reasoning with the ability to take actions.

## Conclusion (1 min)

Let's recap: We defined tools using simple Python functions with the @tool decorator. We handled multi-tool scenarios with execution loops. And we built a conversational chatbot that decides when to use tools autonomously.

[Visual: Show the tool execution cycle diagram]

This is crucial for what's coming next. In the following video, we're building full AI agents—systems that plan, reason, and use tools to accomplish complex tasks.

Before that, try adding your own tools. Maybe a weather API, a database query, or a file system operation. The pattern is the same—define the function, add the decorator, and let the model decide when to use it.

See you next time when we build our first agent!

[Note for narrator: Build excitement—tools are the gateway to agents]
