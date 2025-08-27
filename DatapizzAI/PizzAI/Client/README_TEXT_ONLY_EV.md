# DatapizzAI Text-Only

This guide walks you step-by-step through building a text-only chatbot with DatapizzAI. Each section explains not only what to do but also the reasoning behind it.

- **Goal**: Build a robust, high-performance conversational chatbot.
- **Stack**: DatapizzAI (text-only mode), LLM provider (e.g., OpenAI).
- **Outcome**: A CLI chatbot with memory, a sliding context window, error handling, metrics, and optional caching.

## Table of Contents

- [Prerequisites](#prerequisites)
- [1. Client setup](#1-client-setup)
- [2. Core Concepts: Memory, TextBlock, ROLE](#2-core-concepts-memory-textblock-role)
- [3. Step 0: A `chat_turn` function](#3-step-0-a-chat_turn-function)
- [4. From Function to Chatbot: A Class with a Sliding Window](#4-from-function-to-chatbot-a-class-with-a-sliding-window)
- [5. Minimal Interactive REPL](#5-minimal-interactive-repl)
- [6. Improving Response Style](#6-improving-response-style)
- [7. Performance: Caching and Metrics](#7-performance-caching-and-metrics)
- [8. Putting It All Together: Complete Chatbot](#8-putting-it-all-together-complete-chatbot)
- [9. Recommended Extensions](#9-recommended-extensions)
- [Useful References](#useful-references)
- [Appendix: Available Modes](#appendix-available-modes-one-shot-vs-conversational)

## Prerequisites
- Python 3.10+
- Provider API key (e.g., `OPENAI_API_KEY`)
- `.env` file at the project root containing at least:
```
OPENAI_API_KEY=sk-...
```

For full examples, also check `text_only_examples.py`.

## 1. Client setup
To interact with a model, you need a client configured with the provider, API key, and model name. This is also where you define the assistant’s personality (via the system prompt) and creativity (via temperature).

```python
import os
from datapizzai.clients import ClientFactory

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    system_prompt=(
        "You are a helpful and concise assistant. "
        "Respond in Italian, using bullet points when appropriate."
    ),
    temperature=1,
)
```

- `provider`: The LLM vendor (e.g., OpenAI, Anthropic, Google).
- `system_prompt`: Sets the bot’s default behavior and personality.
- `temperature`: Controls the randomness and creativity of the responses.

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

**Note**: The client's response is an object. To save it to memory, you must use the `.text` attribute to get the string content. Passing the entire response object to a `TextBlock` will cause a JSON serialization error.

## 3. Step 0: A `chat_turn` function
Start with a simple function that handles a single turn in a conversation. This helps validate that the basic pipeline is working correctly.

```python
def chat_turn(user_input: str) -> str:
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    return response.text

print(chat_turn("Introduce yourself in one sentence."))
print(chat_turn("Now give me 3 best practices for Django."))
```

Separating the "what" (user input) from the "how" (memory management and client invocation) makes your code more modular and easier to extend.

## 4. From Function to Chatbot: A Class with a Sliding Window
As the conversation continues, the memory grows. To manage costs and stay within the model's context limit, we can implement a "sliding window" strategy that retains only the last N turns.

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

Controlling the memory size preserves recent context while reducing costs and latency.

## 5. Minimal Interactive REPL
A command-line loop lets you test the chatbot with real-time input.

```python
bot = Chatbot(client, window_size=6)
print("Type 'exit' or 'quit' to end the session.")

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

This validates the end-to-end functional flow before adding more complexity.

## 6. Improving Response Style
You can control the bot's style via the `system_prompt` and, if needed, by providing instructions in the user prompt. Use clear formatting and structure for better readability.

```python
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    system_prompt=(
        "You are a technical consulting assistant. "
        "Always respond in Italian, structure your answers in a maximum of 5 bullet points, "
        "and conclude with a brief 'next steps' section."
    ),
    temperature=1,
)
```

This aligns the bot's tone and structure with your specific domain needs (e.g., support, consulting, brainstorming).

## 7. Performance: Caching and Metrics
Caching reduces costs for repeated requests. Metrics help you understand the impact of your prompting and memory strategies.

```python
from datapizzai.cache import MemoryCache

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    cache=MemoryCache(),  # Only supported by OpenAI in the constructor
    temperature=1
)

# Example of inspecting metrics
reply = client.invoke("Give me 3 tips for testing a REST API")
print("Prompt tokens:", reply.prompt_tokens_used)
print("Completion tokens:", reply.completion_tokens_used)
print("Stop reason:", reply.stop_reason)
```

Measurement enables data-driven optimizations for latency, cost, and quality.

## 8. Putting It All Together: Complete Chatbot
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
        print("bot> A temporary error occurred. Please try again.")
```

## 9. Recommended Extensions
- **Persistence**: Save memory to a database or file to maintain context across sessions.
- **Structured Data**: Instruct the model to return JSON for easier integration with other services.
- **Evaluation**: Define benchmark prompts to compare response quality, latency, and costs across different models or prompts.
- **Deployment**: Wrap the chatbot in an API (e.g., using FastAPI) or a web application.
- **Security**: Implement input filtering, rate limiting, and length checks to handle unexpected user behavior.

## Useful References
- `text_only_examples.py`: Contains complete examples and advanced scenarios.
- `GUIDA_TEXT_ONLY.md`: A technical guide with best practices and troubleshooting tips.

---

## Appendix: Available Modes (One-Shot vs. Conversational)

### One-Shot (Single Query)
Use this for isolated questions, translations, calculations, or any task that doesn't require conversational context.

```python
from datapizzai.clients import ClientFactory
import os

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
)

response = client.invoke("Explain machine learning in 2 sentences")
print(response.text)
```

### Conversational (Multi-Turn with Memory)
Use this for tutoring, consulting, assisted debugging, or structured brainstorming sessions where retaining context is essential.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

def chat_turn(user_input: str) -> str:
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    return response.text

print(chat_turn("Hi, I'm Mirko, a Python developer"))
print(chat_turn("What are the best practices for Django?"))
print(chat_turn("And what about for my specific use case?"))
```
