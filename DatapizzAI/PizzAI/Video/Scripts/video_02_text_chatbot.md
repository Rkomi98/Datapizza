# Video 2: Building Your First Text-Only Chatbot

## Introduction (1.5 min)

What's up! Welcome back. So in the last video, we got Datapizza-AI running and made our first LLM call. Pretty cool, right? But here's the thing—it's not really a chatbot yet. It has no memory, no error handling, nothing you'd actually ship to production.

Today we're fixing all of that. We're building a proper conversational chatbot that remembers what you said, handles errors gracefully, and even implements caching to save you money.

[Visual: Show progression from basic invoke to full chatbot]

This is the foundation you'll need for literally everything else in this series. Once you get memory, caching, and the response lifecycle down, you can build everything.

Alright, here are the three core concepts we're covering.

## Content Main (7 min)

### Understanding Memory (2.5 min)

Okay, so here's something that trips people up: LLMs don't actually remember anything. Like, at all. Every single time you send a request, you have to send the entire conversation history. That's just how these models work.

[Visual: Diagram showing stateless LLM receiving full context]

Datapizza-AI handles this with three simple objects: `Memory`, `TextBlock`, and `ROLE`.

Let me show you how this works:

```python
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock

memory = Memory()

# Add user message
memory.add_turn(
    [TextBlock(content="Hi, I'm Mirko")], 
    ROLE.USER
)

# Call the model
response = client.invoke("Hi, I'm Mirko", memory=memory)

# Store assistant response
memory.add_turn(
    [TextBlock(content=response.text)], 
    ROLE.ASSISTANT
)
```

[Show code running with output]

See what's happening? We're manually tracking the conversation. User says something, we store it. Model responds, we store that too.

Here's the critical part: always use `response.text` when storing the assistant's reply. Don't pass the response object directly: it's not a string. Memory expects strings wrapped in TextBlock.

[Highlight the .text property]

This pattern—add user turn, invoke with memory, add assistant turn is how every chatbot works in Datapizza-AI. Get comfortable with it.

### Implementing Caching (2 min)

Now let's talk about money for a second. Every time you hit an LLM API, you're paying for tokens. If someone asks the same question twice, you're literally paying twice for the exact same answer.

That's wasteful. Caching fixes it, and it's stupid simple to implement.

[Show code]

```python
import time
from datapizza.clients.openai import OpenAIClient
from datapizza.cache import MemoryCache

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=MemoryCache()
)

# First request hits the API
t0 = time.perf_counter()
response1 = client.invoke("What is machine learning?")
t1 = time.perf_counter()
print("first:", r1.text)
print(f"⏱️ time (first): {t1 - t0:.3f}s")

# Second identical request hits the cache
t2 = time.perf_counter()
response2 = client.invoke("What is machine learning?")
t3 = time.perf_counter()
print("second:", r2.text)
print(f"⏱️ time (second): {t3 - t2:.3f}s")
```

[Demonstrate timing difference]

The first request might take 2-3 seconds. The second? Instant. We cannot show the difference in cost, but in the second scenario, there is Zero API cost.

The cache key is computed from your prompt and parameters. Same input equals same output. Different input gets a fresh API call.

[Visual: Show cache hit vs cache miss flowchart]

For production, you'd use `RedisCache` instead of `MemoryCache` so it persists across restarts and works in distributed systems. But for development, memory cache is perfect.

### Building the Complete Chatbot (2.5 min)

Now let's put it all together into something you can actually use. Let's build it line by line.

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

Alright, so to wrap this up—here's what we just built:

We added proper conversation memory using Memory, TextBlock, and ROLE. We implemented caching to eliminate redundant API calls and save you actual money. And we built a complete chatbot class that handles the full conversation lifecycle.

[Visual: Show three key components]

This is your chatbot foundation. Everything from here—tools, agents, RAG systems—all of it builds on this exact pattern.

Next video, we're adding structured outputs so you can get JSON responses reliably, and we'll explore multimodal capabilities—sending images and audio to your models. It gets way more interesting.

Before that though, try extending this chatbot. Add a system prompt, experiment with different temperatures, or swap OpenAI for Claude or Gemini using the same code (remember you have to install other client). That's the power of this unified interface. Till now we have seen only text chatbots. In next video we will analyze also structured and multimodal content.

If this helped, smash that like button. Drop a comment if you run into issues. I'll see you in the next one!

