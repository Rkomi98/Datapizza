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

Important note on caching: caching is implemented by the `datapizzai` library (not by the provider). You can use in‑process `MemoryCache` or a shared `RedisCache` in distributed environments. The cache key is computed from the request content.

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

# Inspect metrics
print("prompt tokens:", r2.prompt_tokens_used)
print("completion tokens:", r2.completion_tokens_used)
print("stop reason:", r2.stop_reason)
```

Measurement enables data-driven optimizations for latency, cost, and quality.

### Note: sliding window strategy (why it exists)
The `_apply_sliding_window` helper is a simple policy that keeps only the last `N` turns to control token usage and cost. It’s just one policy; see also the periodic summarization example below.

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

## 5. Custom memory: summarize every 5 turns
Here’s how to implement a policy that summarizes the conversation every 5 turns and continues from the summary, preserving key context at lower cost.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

class SummarizingChat:
    def __init__(self, client, summarize_every: int = 5, max_summary_len: int = 6):
        self.client = client
        self.memory = Memory()
        self.turns = 0
        self.summarize_every = summarize_every
        self.max_summary_len = max_summary_len

    def _summarize(self):
        prompt = (
            f"Summarize the conversation in {self.max_summary_len} sentences, "
            "highlighting decisions and TODOs."
        )
        summary_resp = self.client.invoke(prompt, memory=self.memory)
        summary = summary_resp.text.strip()
        new_mem = Memory()
        new_mem.add_turn([TextBlock(content=f"[Summary] {summary}")], ROLE.ASSISTANT)
        self.memory = new_mem

    def send(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        resp = self.client.invoke("", memory=self.memory)
        self.memory.add_turn([TextBlock(content=resp.text)], ROLE.ASSISTANT)
        self.turns += 1
        if self.turns % self.summarize_every == 0:
            self._summarize()
        return resp.text
```

Recommended extension points (easy to customize):
- Input pre‑processing (prompt rewrite, safety filters)
- Output post‑processing (format normalization, bullet/JSON extraction)
- Memory policy (sliding window, periodic summaries, pin key messages)
- Dynamic provider selection (fallback if a provider is slow/errors)
- Cache strategy (in‑process vs Redis)

## Useful References
- `text_only_examples.py`: Contains complete examples and advanced scenarios.
