# DatapizzAI text-only

This guide walks you step by step through building a text-only chatbot with DatapizzAI. Each step explains not only what to do, but also why you should do it.

- Goal: build a robust, high-performing conversational chatbot
- Stack: DatapizzAI (text-only mode)
- Result: a command-line chatbot with memory, error handling, metrics, and optional caching

## Table of Contents

- [1. Client configuration](#1-client-configuration)
- [2. Core concepts: Memory, TextBlock, ROLE](#2-core-concepts-memory-textblock-role)
- [3. Cache](#3-cache)
- [4. Putting it all together: complete chatbot](#4-putting-it-all-together-complete-chatbot)

## 1. Client configuration
To talk to a model you need a client configured with provider, API key, temperature, and model name.

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
    temperature=1
)

print(client.invoke("Hi, nice to meet you").text)

print(client.invoke(TextBlock(content="Hi, nice to meet you")).text)
```

- provider: choose the LLM vendor

## 2. Core concepts: Memory, TextBlock, ROLE
To build conversations, DatapizzAI uses:
- `Memory`: stores the history of turns (user/assistant)
- `TextBlock`: represents the blocks of text exchanged in each turn
- `ROLE`: identifies the speaker (`ROLE.USER` or `ROLE.ASSISTANT`)

These objects let the model remember context. Always pass strings to `TextBlock(content=...)`; use `response.text` to store the model's reply.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

memory.add_turn([TextBlock(content="Hi, I'm Mirko")], ROLE.USER)

response = client.invoke("Hi, I'm Mirko", memory=memory)
# Store the reply (ALWAYS use a string)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

Note: the response is an object. To store it in memory you must use `response.text` (a string). Do not pass the response object directly into `TextBlock`, otherwise you will hit JSON serialization errors.

## 3. Cache
Caching reduces cost and latency for repeated requests.

How it works: if you send two identical requests to the same client with caching enabled, the second one is served from the cache (cache hit). In this case the provider is not called and the response returns immediately.

Implementation details: caching is handled by the `datapizzai` library (not by the provider). The cache key is computed from a hash of the request content (prompt, parameters, and memory if present). You can use `MemoryCache` (in-process) or `RedisCache` for distributed environments.

```python
from datapizzai.cache import MemoryCache
import time

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1,
    cache=MemoryCache(),
)

# Same request twice: the second should hit the cache
q = "Give me 3 advantages of TDD in one line"

t0 = time.perf_counter()
r1 = client.invoke(q)
t1 = time.perf_counter()
print("first:", r1.text)
print(f"⏱️ time (first): {t1 - t0:.3f}s")
#⏱️ time (first): 6.340s

t2 = time.perf_counter()
r2 = client.invoke(q)  # This is a cache hit, the provider is not invoked
t3 = time.perf_counter()
print("second:", r2.text)
print(f"⏱️ time (second): {t3 - t2:.3f}s")
#⏱️ time (second): 0.000s

# Alternative: use Redis as a shared cache
from datapizzai.cache import RedisCache
redis_cache = RedisCache(host="localhost", port=6379, db=0)
client_redis = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    cache=redis_cache,
)

```

## 4. Putting it all together: complete chatbot
Here is a summary example that brings everything together with a simple chatbot.

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
        response = self.client.invoke(user_input, memory=self.memory)
        self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        total_tokens = (response.prompt_tokens_used or 0) + (response.completion_tokens_used or 0)
        print(f"[metrics] total tokens: {total_tokens}")
        return response.text

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1,
)

bot = Chatbot(client)
print("Chat ready. Type 'exit' to quit.")
while True:
    try:
        user = input("you> ").strip()
        if user.lower() in {"esci", "exit", "quit"}:
            break
        print("bot>", bot.send(user))
    except KeyboardInterrupt:
        break
    except Exception:
        print("bot> A temporary error occurred. Please try again.")
```
