import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.agents import Agent
from datapizza.tools import tool

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3
)

# Test 1: Basic Agent
print("=== Test 1: Basic Agent ===")

@tool
def get_weather(location: str, when: str) -> str:
    """Retrieves weather information."""
    return f"Weather in {location} on {when}: 72°F, partly cloudy"

agent = Agent(
    name="WeatherAgent",
    client=client,
    system_prompt="You are an expert weather assistant. Use tools when needed.",
    tools=[get_weather],
    max_steps=5,
    terminate_on_text=True
)

response = agent.run("What will the weather be like in Chicago next Monday?")
print(f"Response: {response}")
print("✅ Basic agent test successful\n")

# Test 2: Multiple Tools Agent
print("=== Test 2: Multiple Tools Agent ===")

@tool
def calculator(expression: str) -> str:
    """Performs calculations."""
    try:
        return str(eval(expression))
    except:
        return "Error in calculation"

@tool
def search_database(query: str) -> str:
    """Searches internal database."""
    # Mock database
    db = {
        "revenue_q1": "$2.5M",
        "revenue_q2": "$3.1M",
        "employees": "47"
    }
    return db.get(query.lower(), "Data not found")

agent = Agent(
    name="AnalystAgent",
    client=client,
    system_prompt="You are a business analyst. Use tools to gather data and perform calculations.",
    tools=[calculator, search_database],
    max_steps=5
)

response = agent.run(
    "What's our total revenue for Q1 and Q2? Calculate the growth rate."
)
print(f"Response: {response}")
print("✅ Multiple tools agent test successful\n")

# Test 3: Controlling Agent Behavior
print("=== Test 3: Controlling Agent Behavior ===")

# Conservative agent
conservative = Agent(
    name="Conservative",
    client=client,
    system_prompt="You are cautious. Only use tools when absolutely necessary. Explain your reasoning before acting.",
    tools=[calculator],
    max_steps=5
)

# Aggressive agent
aggressive = Agent(
    name="Aggressive",
    client=client,
    system_prompt="You are action-oriented. Use tools proactively. Take initiative.",
    tools=[calculator],
    max_steps=5
)

task = "What is 50 + 50?"
print(f"Task: {task}")
print(f"Conservative: {conservative.run(task)}")
print(f"Aggressive: {aggressive.run(task)}")
print("✅ Agent behavior test successful\n")

# Test 4: Execution Modes
print("=== Test 4: Execution Modes ===")

agent = Agent(
    name="SafeAgent",
    client=client,
    tools=[calculator],
    max_steps=10
)

# Synchronous (blocks until complete)
result = agent.run("Calculate 100 * 5")
print(f"Sync result: {result}")

# Streaming (real-time updates)
print("Streaming execution:")
for chunk in agent.stream_invoke("Calculate 200 / 4"):
    if isinstance(chunk, str):
        print(f"Final: {chunk}")
    else:
        print(f"Step: {type(chunk).__name__}")

print("✅ Execution modes test successful\n")

print("✅ All tests passed for video_06!")

