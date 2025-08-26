# DatapizzAI Text-Only

Quick guide for using the one-shot and conversational modes of the DatapizzAI framework for textual prompts.

## Available modes

### One-shot (Single Query → Response)
**When to use**: Isolated questions, translations, calculations, independent analysis

```python
from datapizzai.clients import ClientFactory
import os

# Client creation
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Simple query
response = client.invoke("Explain machine learning in 2 sentences")
print(response.text)
```

### Conversational (Multi-turn with memory)
**When to use**: Tutoring, consulting, iterative idea development, technical support

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

# Memory setup
memory = Memory()

# Conversation
def chat_turn(user_input: str):
    # Add user input
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Generate response with context
    response = client.invoke("", memory=memory)
    
    # Add response to memory
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    return response.text

# Usage
print(chat_turn("Hello, I'm Marco, a Python developer"))
print(chat_turn("What are the best practices for Django?"))
print(chat_turn("And for my specific case?"))  # Uses previous context
```

## Mode comparison

| Scenario | One-shot | Conversational | Practical advice |
|----------|----------|----------------|-------------------|
| **Simple FAQ** | ✅ Ideal | ✅ Possible | One-shot (more efficient) |
| **Translations** | ✅ Ideal | ✅ Possible | One-shot (faster) |
| **Mathematical calculations** | ✅ Ideal | ✅ Possible | One-shot (more direct) |
| **Tutoring/Teaching** | ✅ Possible | ✅ Ideal | Conversational (better experience) |
| **Technical consulting** | ✅ Possible | ✅ Ideal | Conversational (persistent context) |
| **Brainstorming** | ✅ Possible | ✅ Ideal | Conversational (idea development) |
| **Assisted debugging** | ✅ Possible | ✅ Ideal | Conversational (error history) |
| **Iterative analysis** | ✅ Possible | ✅ Ideal | Conversational (deepening insights) |

*Note: Both modes support all scenarios. The advice is based on efficiency and user experience, not technical limitations of the framework.*

## Advanced memory management

### Sliding window strategy
```python
def sliding_window_chat(memory: Memory, user_input: str, window_size: int = 6):
    """Keeps only the last N turns to optimize token usage"""
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Limit memory if necessary
    if len(memory.memory) > window_size:
        memory.memory = memory.memory[-window_size:]
    
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    return response
```

### Cache for performance
```python
from datapizzai.cache import MemoryCache

# Only OpenAI supports cache in constructor
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=MemoryCache()  # Reduces costs for repeated queries
)
```

## Complete documentation

➡️ **[GUIDA_TEXT_ONLY.md](GUIDA_TEXT_ONLY.md)** - Complete technical guide with advanced examples, best practices, troubleshooting and copyable code
