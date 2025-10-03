# Video 2: Building Your First Text-Only Chatbot

## Introduction (1.5 min)

Welcome back! In the last video, we got Datapizza-AI running and made our first LLM call. That was cool, but it's not really a chatbot yet—it has no memory, no error handling, nothing production-ready.

Today we're fixing that. We're going to build a proper conversational chatbot that remembers what you said, handles errors gracefully, and even implements caching to save you money.

[Visual: Show progression from basic invoke to full chatbot]

This is the foundation you'll need for everything else in this series. Once you understand memory, caching, and the response lifecycle, you can build anything.

Let's get into it.

[Transition: "Three Core Concepts"]

## Content Main (7 min)

### Understanding Memory (2.5 min)

Here's the thing about LLMs—they don't actually remember anything. Every time you send a request, you have to send the entire conversation history. That's just how they work.

[Visual: Diagram showing stateless LLM receiving full context]

Datapizza-AI handles this with three simple objects: `Memory`, `TextBlock`, and `ROLE`.

Let me show you how this works:

```python
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock

memory = Memory()

# Add user message
memory.add_turn(
    [TextBlock(content="Hi, I'm Sarah")], 
    ROLE.USER
)

# Call the model
response = client.invoke("Hi, I'm Sarah", memory=memory)

# Store assistant response
memory.add_turn(
    [TextBlock(content=response.text)], 
    ROLE.ASSISTANT
)
```

[Show code running with output]

See what's happening? We're manually tracking the conversation. User says something, we store it. Model responds, we store that too.

Here's the critical part: always use `response.text` when storing the assistant's reply. Don't pass the response object directly—it's not a string, and Memory expects strings wrapped in TextBlock.

[Highlight the .text property]

This pattern—add user turn, invoke with memory, add assistant turn—is how every chatbot works in Datapizza-AI. Get comfortable with it.

### Implementing Caching (2 min)

Let's talk about money. Every time you hit an LLM API, you're paying for tokens. If someone asks the same question twice, you're paying twice for the exact same answer.

That's wasteful. Caching fixes it.

[Show code]

```python
from datapizza.cache import MemoryCache

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=MemoryCache()
)

# First request hits the API
response1 = client.invoke("What is machine learning?")

# Second identical request hits the cache
response2 = client.invoke("What is machine learning?")
```

[Demonstrate timing difference]

The first request might take 2-3 seconds. The second? Instant. Zero API cost.

The cache key is computed from your prompt and parameters. Same input equals same output. Different input gets a fresh API call.

[Visual: Show cache hit vs cache miss flowchart]

For production, you'd use `RedisCache` instead of `MemoryCache` so it persists across restarts and works in distributed systems. But for development, memory cache is perfect.

### Building the Complete Chatbot (2.5 min)

Now let's put it all together into something you can actually use.

[Show full code]

```python
import os
from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock

class Chatbot:
    def __init__(self, client):
        self.client = client
        self.memory = Memory()
    
    def send(self, user_input: str) -> str:
        # Store user message
        self.memory.add_turn(
            [TextBlock(content=user_input)], 
            ROLE.USER
        )
        
        # Get response with memory
        response = self.client.invoke(user_input, memory=self.memory)
        
        # Store assistant response
        self.memory.add_turn(
            [TextBlock(content=response.text)], 
            ROLE.ASSISTANT
        )
        
        # Show token usage
        total = (response.prompt_tokens_used or 0) + 
                (response.completion_tokens_used or 0)
        print(f"[tokens: {total}]")
        
        return response.text

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

bot = Chatbot(client)

# Simple chat loop
while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break
    print("Bot:", bot.send(user_input))
```

[Run the chatbot, show conversation]

Look at what we have now: proper memory management, token tracking, and a clean interface.

The chatbot remembers context across turns. Ask it "What's my name?" after introducing yourself, and it'll remember.

[Demonstrate this in the running chatbot]

We're tracking tokens on every response so you know exactly what you're spending. In production, you'd log this to your monitoring system.

And notice the error handling—we're catching exceptions in that try-except block to gracefully handle API failures.

## Conclusion (1.5 min)

Let's review what we built:

We added proper conversation memory using Memory, TextBlock, and ROLE. We implemented caching to eliminate redundant API calls and save money. And we built a complete chatbot class that handles the full conversation lifecycle.

[Visual: Show three key components]

This is your chatbot foundation. Everything from here—tools, agents, RAG systems—builds on this pattern.

In the next video, we're going to add structured outputs so you can get JSON responses reliably, and we'll explore multimodal capabilities—sending images and audio to your models.

Before that, try extending this chatbot. Add a system prompt, experiment with different temperatures, or swap OpenAI for Claude or Gemini using the same code. That's the power of this unified interface.

See you next time!

[Note for narrator: Emphasize that this foundation is crucial—everything builds on it]
