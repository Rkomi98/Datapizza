# DatapizzAI Text-Only

This guide walks you step-by-step through building a text-only chatbot with DatapizzAI. Each section explains not just what to do, but why it matters.

- Goal: build a robust, performant conversational chatbot
- Stack: DatapizzAI (text-only mode)
- Outcome: a CLI chatbot with memory, error handling, metrics, and optional caching

## Table of Contents

- [Prerequisites](#prerequisites)
- [1. Client setup](#1-client-setup)
- [2. Core Concepts: Memory, TextBlock, ROLE](#2-core-concepts-memory-textblock-role)
- [3. Caching](#3-caching)
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
- `Memory`: Stores the history of conversation turns (user/assistant)
- `TextBlock`: Represents text blocks exchanged in turns
- `ROLE`: Identifies the speaker (`ROLE.USER` or `ROLE.ASSISTANT`)

These objects allow the model to retain context. Always pass raw strings to `TextBlock(content=...)` and use `response.text` to add the model's reply to memory.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

# Add a user's turn
memory.add_turn([TextBlock(content="Hi, I'm Mirko")], ROLE.USER)

# Invoke with context
response = client.invoke("", memory=memory)
# Save assistant reply (always a string)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

## 3. Caching
Caching reduces cost and latency for repeated requests.

How it works: if you send two identical requests to the same client with caching enabled, the second one is served from the cache (cache hit). In this case, the provider is not called and the response is returned immediately.

Implementation details: caching is handled by the `datapizzai` library (not by the provider). The cache key is computed as a hash of the request content (prompt, parameters, and memory if present). You can use an in‑process `MemoryCache` or a shared `RedisCache` for distributed setups.

```python
from datapizzai.cache import MemoryCache
import time

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    cache=MemoryCache(),  # in-memory cache provided by datapizzai
)

# Same request twice: second should hit the cache
q = "Give me 3 advantages of TDD in one line"

t0 = time.perf_counter()
r1 = client.invoke(q)
t1 = time.perf_counter()
print("first:", r1.text)
print(f"⏱️ time (first): {t1 - t0:.3f}s")

t2 = time.perf_counter()
r2 = client.invoke(q)
t3 = time.perf_counter()
print("second:", r2.text)
print(f"⏱️ time (second): {t3 - t2:.3f}s")

# Alternative: share cache via Redis
from datapizzai.cache import RedisCache
redis_cache = RedisCache(host="localhost", port=6379, db=0)
client_redis = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    cache=redis_cache,
)

```



## 4. Putting It All Together: Complete Chatbot
Here is a summary example that combines configuration, a simple class, REPL, and basic metrics, using memory for multi-turn context.

```python
import os
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

class Chatbot:
    def __init__(self, client):
        self.client = client
        self.memory = Memory()

    def send(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
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

bot = Chatbot(client)
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
