# DatapizzAI Text-Only

This guide walks you step by step through building a text-only chatbot with DatapizzAI. Each step explains not only what to do, but why it matters.

- Goal: build a robust, efficient conversational chatbot
- Stack: DatapizzAI (text-only mode), LLM provider (e.g., OpenAI)
- Outcome: a CLI chatbot with memory, sliding window, error handling, metrics, and optional caching

## Prerequisites
- Python 3.10+
- Provider API key (e.g., `OPENAI_API_KEY`)
- `.env` file at the project root containing at least:
```
OPENAI_API_KEY=sk-...
```

For full examples, also check `text_only_examples.py`.

## 1. Client setup (why this matters)
To interact with the model, you need a client configured with provider, key, and model. Here you also define the assistant “style” (system prompt) and creativity (temperature).

```python
import os
from datapizzai.clients import ClientFactory

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt=(
        "You are a helpful, concise assistant. "
        "Respond in Italian and use bullet points when useful."
    ),
    temperature=0.7,
)
```

- provider: choose the LLM vendor (OpenAI, Anthropic, Google, ...)
- system_prompt: sets the bot’s default behavior
- temperature: controls response variability

## 2. Core concepts: Memory, TextBlock, ROLE (why they exist)
To build conversations, DatapizzAI uses:
- `Memory`: stores the history of turns (user/assistant)
- `TextBlock`: represents pieces of text exchanged per turn
- `ROLE`: identifies who speaks (`ROLE.USER` or `ROLE.ASSISTANT`)

These enable the model to “remember” the context.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

# Add a user turn
memory.add_turn([TextBlock(content="Hi, I am Marco")], ROLE.USER)

# Invoke with context
response = client.invoke("", memory=memory)
# Save assistant response
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

## 3. Minimum viable piece: a `chat_turn` function
Start with a single-turn function. It validates the end-to-end pipeline.

```python
def chat_turn(user_input: str) -> str:
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    return response.text

print(chat_turn("Introduce yourself in one sentence."))
print(chat_turn("Now give me 3 Django best practices."))
```

Why: separating the “what” (user text) from the “how” (memory/invocation) keeps code extensible.

## 4. From function to chatbot: class with sliding window
Memory grows at each turn. To avoid token limits and costs, use a sliding-window strategy that keeps only the last N relevant turns.

```python
from typing import Optional

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
        return response.text
```

Why: controlling memory size preserves recent context and reduces cost/latency.

## 5. Minimal interactive run (REPL)
A terminal loop lets you test the chatbot with real input quickly.

```python
bot = Chatbot(client, window_size=6)
print("Type 'exit' to quit.")

while True:
    try:
        user = input("you> ").strip()
        if user.lower() in {"exit", "quit"}:
            break
        answer = bot.send(user)
        print(f"bot> {answer}")
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"error> {e}")
```

Why: validate end-to-end flow before adding complexity.

## 6. Improving answer style
Style is controlled by the `system_prompt` and, when needed, explicit user instructions. Prefer structured output for clarity.

```python
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt=(
        "You are a technical consulting assistant. "
        "Always in Italian, responses in at most 5 bullet points, "
        "finish with a short 'next steps'."
    ),
    temperature=0.5,
)
```

Why: align the bot’s tone and structure with your domain (support, consulting, brainstorming).

## 7. Error handling and robustness
Make the conversation resilient to transient failures.

```python
def safe_send(bot: Chatbot, user_input: str) -> str:
    try:
        return bot.send(user_input)
    except Exception:
        return "Si è verificato un errore temporaneo. Riprova tra poco."
```

Why: user experience first—fallbacks prevent abrupt breaks.

## 8. Performance: caching and metrics
Caching reduces cost for repeated queries. Metrics help you understand the impact of prompting/memory choices.

```python
from datapizzai.cache import MemoryCache

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=MemoryCache(),  # only OpenAI supports cache in constructor
)

reply = client.invoke("Give me 3 quick tips to test a REST API")
print("prompt tokens:", reply.prompt_tokens_used)
print("completion tokens:", reply.completion_tokens_used)
print("stop reason:", reply.stop_reason)
```

Why: measure to optimize (latency/cost/quality).

## 9. Putting it all together: complete chatbot
A concise example that combines setup, class, REPL, and basic metrics.

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
    model="gpt-4o",
    system_prompt=(
        "You are a helpful, concise assistant. Respond in Italian "
        "and always suggest a short list of next steps."
    ),
    temperature=0.6,
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
        print("bot> Si è verificato un errore temporaneo. Riprova.")
```

## 10. Recommended extensions
- Persistence: store memory in a DB or file between sessions
- Structured outputs: ask for JSON to integrate with external services
- Evaluation: set up prompting benchmarks and compare quality/latency/cost
- Deployment: wrap the chatbot in an API (e.g., FastAPI) or a web app
- Security: input filters, rate limiting, length controls

## Useful references
- `text_only_examples.py`: complete examples and advanced scenarios
- `GUIDA_TEXT_ONLY.md`: technical guide with best practices and troubleshooting

---

## Appendix: available modes (one-shot vs conversational)

### One-shot (single query)
When to use: isolated questions, translations, calculations, independent analysis.

```python
from datapizzai.clients import ClientFactory
import os

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)

response = client.invoke("Explain machine learning in 2 sentences")
print(response.text)
```

### Conversational (multi-turn with memory)
When to use: tutoring, consulting, assisted debugging, structured brainstorming.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

def chat_turn(user_input: str) -> str:
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    return response.text

print(chat_turn("Hello, I'm Marco, a Python developer"))
print(chat_turn("What are the best practices for Django?"))
print(chat_turn("And for my specific case?"))
```
