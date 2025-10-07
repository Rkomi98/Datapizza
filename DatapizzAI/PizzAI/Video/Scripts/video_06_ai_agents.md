# Video 6: Building AI Agents

## Introduction (1.5 min)

Hey everyone, and welcome back. We've covered clients, memory, and tools—all the essential building blocks. Now, we're putting them together to create something much more powerful: autonomous AI agents.

[Visual: Show evolution from chatbot to agent]

Here's the key difference: an agent isn't just a chatbot with tools. It's a system that can reason, plan, and take multiple actions to solve complex problems. It operates independently within the boundaries you set for it.

Today, we're building your first agent from scratch. You'll learn how agents "think," how to configure their behavior, and how to control their execution so they don't go rogue on you.

By the end of this video, you'll have a working agent that can solve multi-step problems autonomously. It's pretty cool stuff.

Alright, so what is an agent, exactly?

## Content Main (7.5 min)

### Agent Architecture (2 min)

An agent is fundamentally different from a chatbot. A chatbot simply responds to messages, whereas an agent actively pursues goals. That's a big difference.

[Visual: Show agent reasoning loop diagram]

Here's how an agent works:
1. It receives a task.
2. It reasons about what to do next.
3. It selects and executes the appropriate tools.
4. It evaluates the results of its actions.
5. It repeats this process until the task is complete.

This is often called the "thought-action-observation" loop. The agent thinks, acts, observes the result, and then decides what to do next.

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

The `name` is for logging purposes, while the `client` powers the agent's reasoning. The `system_prompt` defines its personality and behavior, and the `tools` are the actions it can take.

`max_steps` is a safety feature that prevents infinite loops—the agent will stop after five reasoning cycles. `terminate_on_text` tells it to stop immediately after generating a text response, which prevents unnecessary tool calls.

### Running Your First Agent (2 min)

Now, let's see it in action.

```python
response = agent.run("What will the weather be like in Chicago next Monday?")
print(response)
```

[Run and show output]

Watch what happens: the agent reads the task, realizes it needs the weather tool, calls it with the correct parameters, gets the result, and then formulates a final answer.

[Show the step-by-step execution if possible]

You didn't have to tell it to use the tool. You didn't write any of that logic. The agent figured it out on its own.

This is the power of agentic systems. You define the capabilities and constraints, and then you let the agent solve the problem.

Let's make it more interesting by adding multiple tools.

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

The agent searches the database twice, performs a calculation, and then synthesizes a report. It automatically chains multiple actions together to complete the task.

### Controlling Agent Behavior (3.5 min)

The system prompt is your main control interface. Let me show you how different prompts can lead to completely different behaviors.

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

They have the same tools and the same task, but their execution patterns are completely different. The system prompt is what shapes their personality and decision-making.

Now, let's talk about execution modes. You have three main options:

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

Streaming is incredibly powerful for long-running tasks. It allows you to show progress in real-time, log intermediate steps, and even interrupt the execution if something goes wrong.

The `max_steps` parameter is crucial for production environments. Without it, agents can easily get stuck in loops.

```python
agent = Agent(
    name="SafeAgent",
    client=client,
    tools=tools,
    max_steps=10  # Safety limit
)
```

If the agent hits 10 steps, it will stop, regardless of whether the task is complete. This is a critical safety feature that prevents runaway API costs.

Finally, there's `terminate_on_text`. This controls whether the agent stops after generating text or continues to look for more actions to take.

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

Use `True` for simple, Q&A-style agents. Use `False` when the agent needs to take multiple actions before reporting back with a final answer.

## Conclusion (1 min)

Alright, quick recap. We built autonomous agents that can reason and act to solve problems. We learned how to configure their behavior through system prompts and other parameters. And we explored different execution modes, from synchronous to streaming.

[Visual: Show agent components diagram]

Agents are powerful, but single agents have their limits. In the next video, we're going to build multi-agent systems—teams of specialized agents working together to solve even more complex problems. It's going to be epic.

Before that, I encourage you to experiment with agent behavior. Try different system prompts, add new tools, and play around with `max_steps`. You'll see how small changes can create completely different reasoning patterns. It's fascinating stuff.

If you're enjoying this series, don't forget to subscribe and hit that bell. I'll see you in the next one!

[Note for narrator: This should feel like a major milestone—we've built our first autonomous system]
