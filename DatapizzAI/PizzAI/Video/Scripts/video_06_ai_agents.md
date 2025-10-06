# Video 6: Building AI Agents

## Introduction (1.5 min)

Hey, welcome back! So we've covered clients, memory, tools—all the building blocks. Now we're putting them together into something way more powerful: autonomous AI agents.

[Visual: Show evolution from chatbot to agent]

Here's the key difference—an agent isn't just a chatbot with tools. It's a system that can reason, plan, and take multiple actions to solve problems. It operates independently within the boundaries you set for it.

Today we're building your first agent from scratch. You'll learn how agents think, how to configure their behavior, and how to control their execution so they don't go rogue on you.

After this, you'll have a working agent that can solve multi-step problems autonomously. Pretty cool.

Alright, so what is an agent exactly?

## Content Main (7.5 min)

### Agent Architecture (2 min)

Okay, so an agent is fundamentally different from a chatbot. A chatbot responds to messages. An agent pursues goals. Big difference.

[Visual: Show agent reasoning loop diagram]

Here's how an agent works:
1. Receives a task
2. Reasons about what to do
3. Selects and executes tools
4. Evaluates results
5. Repeats until the task is complete

This is the thought-action-observation loop. The agent thinks, acts, observes the result, and decides what to do next.

[Show the Agent creation code]

```python
from datapizza.agents import Agent
from datapizza.clients.openai import OpenAIClient
from datapizza.tools import tool

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3
)

@tool
def get_weather(location: str, when: str) -> str:
    """Retrieves weather information."""
    return f"Weather in {location} on {when}: 72°F, partly cloudy"

agent = Agent(
    name="WeatherAgent",
    client=client,
    system_prompt="You are a weather assistant. Use tools when needed.",
    tools=[get_weather],
    max_steps=5,
    terminate_on_text=True
)
```

[Walk through each parameter]

The `name` is for logging. The `client` powers the reasoning. The `system_prompt` defines personality and behavior. Tools are what the agent can do.

`max_steps` prevents infinite loops—the agent stops after 5 reasoning cycles. `terminate_on_text` makes it stop immediately after generating a text response, preventing unnecessary tool calls.

### Running Your First Agent (2 min)

Let's see it in action:

```python
response = agent.run("What will the weather be like in Chicago next Monday?")
print(response)
```

[Run and show output]

Watch what happens: The agent reads the task, realizes it needs the weather tool, calls it with the right parameters, gets the result, and formulates an answer.

[Show the step-by-step execution if possible]

You didn't tell it to use the tool. You didn't write the logic. The agent figured it out.

This is the power of agentic systems. You define capabilities and constraints, then let the agent solve problems.

Let's make it more interesting with multiple tools:

```python
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
    max_steps=10
)

response = agent.run(
    "What's our total revenue for Q1 and Q2? Calculate the growth rate."
)
print(response)
```

[Run and show the agent using multiple tools]

The agent searches the database twice, performs a calculation, and synthesizes a report. It chains multiple actions together to complete the task.

### Controlling Agent Behavior (3.5 min)

The system prompt is your control interface. Let me show you how different prompts create different behaviors.

[Show comparison]

```python
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
```

[Show same task with both agents]

Same tools, same task, completely different execution patterns. The system prompt shapes personality and decision-making.

Now let's talk about execution modes. You have three options:

```python
# Synchronous (blocks until complete)
result = agent.run("Task here")

# Asynchronous (non-blocking)
result = await agent.a_run("Task here")

# Streaming (real-time updates)
for chunk in agent.stream_invoke("Task here"):
    if isinstance(chunk, str):
        print("Final:", chunk)
    else:
        print("Step:", type(chunk).__name__)
```

[Demonstrate streaming]

Streaming is powerful for long-running tasks. You can show progress in real-time, log intermediate steps, or even interrupt execution if something goes wrong.

The `max_steps` parameter is crucial for production. Without it, agents can get stuck in loops:

```python
agent = Agent(
    name="SafeAgent",
    client=client,
    tools=tools,
    max_steps=10  # Safety limit
)
```

If the agent hits 10 steps, it stops regardless of task completion. This prevents runaway API costs.

Finally, there's `terminate_on_text`. This controls whether the agent stops after generating text or continues looking for more actions:

```python
# Stops after first text response
agent = Agent(
    client=client,
    tools=tools,
    terminate_on_text=True
)

# Continues until task is clearly complete
agent = Agent(
    client=client,
    tools=tools,
    terminate_on_text=False
)
```

[Show the difference in behavior]

Use `True` for simple Q&A-style agents. Use `False` when the agent needs to take multiple actions and then report back.

## Conclusion (1 min)

Quick recap: We built autonomous agents that reason and act to solve problems. We learned how to configure behavior through system prompts and parameters. And we explored execution modes from synchronous to streaming.

[Visual: Show agent components diagram]

Agents are powerful, but single agents have limits. Next video, we're building multi-agent systems—teams of specialized agents working together to solve complex problems. It's going to be epic.

Before that, experiment with agent behavior. Try different system prompts, add new tools, play with max_steps. See how small changes create completely different reasoning patterns. It's fascinating.

If you're enjoying this, don't forget to subscribe and hit that bell. I'll catch you in the next one!

[Note for narrator: This should feel like a major milestone—we've built our first autonomous system]
