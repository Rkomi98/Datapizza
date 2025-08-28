# DatapizzAI Text-Only

This guide walks you step-by-step through building a text-only chatbot with DatapizzAI. Each section explains not just what to do, but why it matters.

- Goal: build a robust, performant conversational chatbot
- Stack: DatapizzAI (text-only mode)
- Outcome: a CLI chatbot with memory, error handling, metrics, and optional caching

## Table of Contents

- [Prerequisites](#prerequisites)
- [1. Client setup](#1-client-setup)
- [2. Core Concepts: Memory, TextBlock, ROLE](#2-core-concepts-memory-textblock-role)
- [3. Performance: Caching and Metrics](#3-performance-caching-and-metrics)
- [4. Putting It All Together: Complete Chatbot](#4-putting-it-all-together-complete-chatbot)
- [Useful References](#useful-references)

## Prerequisites
- Python 3.10+
- Provider API key (e.g., `OPENAI_API_KEY`)
- `.env` file at the project root containing at least:
```
OPENAI_API_KEY=sk-...
```

For full examples, also check `text_only_examples.py`.

## 1. Client setup
To interact with a model, you need a client configured with the provider, API key, temperature and model name.

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock

# Load variables from .env (project root)
load_dotenv()

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1,
)

# Minimal invoke
print(client.invoke("Say hi in one line").text)

# Or using a block
print(client.invoke(TextBlock(content="Say hi in one line")).text)
```

- provider: choose your LLM vendor

## 2. Core Concepts: Memory, TextBlock, ROLE
DatapizzAI uses a few core abstractions to manage conversations:
- `Memory`: Stores the history of the conversation turns between the user and the assistant.
- `TextBlock`: Represents a piece of text exchanged in a turn.
- `ROLE`: Identifies the speaker (`ROLE.USER` or `ROLE.ASSISTANT`).

These objects allow the model to retain context from previous turns. You should always pass raw strings to `TextBlock(content=...)` and use `response.text` to add the model's reply to memory.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

# Add a user's turn to memory
memory.add_turn([TextBlock(content="Hi, I'm Mirko")], ROLE.USER)

# Invoke the client with the conversation context
response = client.invoke("", memory=memory)
# Save the assistant's response (use the .text attribute for the string content)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

Note: the client's response is an object. Save `response.text` (a string) to memory. Passing the full response object to a `TextBlock` will cause JSON serialization errors.

## 3. Performance: Caching and Metrics
Caching reduces costs for repeated requests. Metrics help you understand the impact of your prompting and memory strategies.

```python
from datapizzai.cache import MemoryCache

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    cache=MemoryCache(),  # in-memory cache
)

# Same request twice: second should hit the cache
q = "Give me 3 advantages of TDD in one line"
r1 = client.invoke(q)
r2 = client.invoke(q)

print("first:", r1.text)
print("second:", r2.text)

# Inspect metrics
print("prompt tokens:", r2.prompt_tokens_used)
print("completion tokens:", r2.completion_tokens_used)
print("stop reason:", r2.stop_reason)
```

Measurement enables data-driven optimizations for latency, cost, and quality.

## 4. Putting It All Together: Complete Chatbot
Here is a summary example that combines the configuration, class, REPL, and basic metrics.

```python
import os
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

class Chatbot:
    def __init__(self, client, window_size: int = 6):
        self.client = client
        self.memory = Memory()
        self.window_size = window_size

    def _apply_sliding_window(self):
        if len(self.memory.memory) > self.window_size:
            self.memory.memory = self.memory.memory[-self.window_size:]

    def send(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        self._apply_sliding_window()
        response = self.client.invoke("", memory=self.memory)
        self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        total_tokens = (response.prompt_tokens_used or 0) + (response.completion_tokens_used or 0)
        print(f"[metrics] total tokens: {total_tokens}")
        return response.text

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
)

bot = Chatbot(client, window_size=6)
print("Chat ready. Type 'exit' to quit.")
while True:
    try:
        user = input("you> ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        print("bot>", bot.send(user))
    except KeyboardInterrupt:
        break
    except Exception:
        print("bot> A temporary error occurred. Please try again.")
```

## Useful References
- `text_only_examples.py`: Contains complete examples and advanced scenarios.
- `GUIDA_TEXT_ONLY.md`: A technical guide with best practices and troubleshooting tips.
