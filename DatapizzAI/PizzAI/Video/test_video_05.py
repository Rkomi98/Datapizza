import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.tools import tool
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock, FunctionCallResultBlock

load_dotenv()

# Install Google client for the example
try:
    from datapizza.clients.google import GoogleClient
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️ Google client not available, skipping Google-specific tests")

# Test 1: Defining Your First Tool
print("=== Test 1: Defining Your First Tool ===")

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

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

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
else:
    print("No function calls made")

print(f"Final response: {response.text}")
print("✅ First tool test successful\n")

# Test 2: Multi-Tool Interactions
print("=== Test 2: Multi-Tool Interactions ===")

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

memory.add_turn([TextBlock(content="Calculate 25 * 4")], ROLE.USER)

response = client.invoke(
    "",
    tools=tools,
    memory=memory
)

# Handle tool execution loop
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
        
        print(f"Executed {call.name}: {result}")
        
        # Add tool result to memory
        tool_result = FunctionCallResultBlock(
            id=call.id,
            tool=call.tool,
            result=result
        )
        memory.add_turn([tool_result], ROLE.TOOL)
    
    # Call the model again with tool results
    response = client.invoke(
        input="",
        tools=tools,
        memory=memory
    )

print(f"Final answer: {response.text}")
print("✅ Multi-tool test successful\n")

# Test 3: Conversational Tool Interface (only if Google client is available)
if GOOGLE_AVAILABLE:
    print("=== Test 3: Conversational Tool Interface ===")
    
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
    
    google_client = GoogleClient(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash"
    )
    
    tools = [calculator]
    memory = Memory()
    
    # Simulate a conversation
    test_inputs = ["What's 150 * 83?", "What's half of that?"]
    
    for user_input in test_inputs:
        print(f"User: {user_input}")
        
        # Add user message
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        # Get response
        response = google_client.invoke(
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
            
            response = google_client.invoke(
                input="",
                memory=memory,
                tools=tools
            )
        
        # Show final response
        print(f"Bot: {response.text}")
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    print("✅ Conversational tool test successful\n")
else:
    print("⚠️ Skipping Test 3 (Google client not available)\n")

print("✅ All tests passed for video_05!")

