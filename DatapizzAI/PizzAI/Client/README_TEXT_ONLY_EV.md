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
    # Add user input
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    
    # Limit memory if necessary - keep only the last N turns
    if len(memory.memory) > window_size:
        memory.memory = memory.memory[-window_size:]
    
    # Generate response with optimized memory
    response = client.invoke("", memory=memory)
    
    # Add response to memory
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    return response

# Practical usage
memory = Memory()
conversation = [
    "Hello! I'm a Python developer beginner.",
    "I want to learn how to create a chatbot with Python.",
    "Which libraries do you recommend to start with?",
    "And how do I manage conversation memory?",
    "Can you show me a code example?",
    "How do I handle errors and exceptions?",
    "And for deployment on a web server?",
    "What are the best practices for security?"
]

for user_input in conversation:
    response = sliding_window_chat(memory, user_input, window_size=4)
    print(f"User: {user_input}")
    print(f"Assistant: {response.text}")
    print(f"Active memory: {len(memory.memory)} turns\n")
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

## Complex examples

### Complete chatbot development
```python
def develop_chatbot_with_ai():
    """Develops a complete chatbot with AI assistance"""
    memory = Memory()
    
    # Phase 1: Requirements analysis
    requirements = [
        "I want to create a chatbot for a clothing e-commerce.",
        "The chatbot must handle: customer service, product search, order management.",
        "We'll have about 1000 customers per day and need to support 5 languages.",
        "What are the main technical requirements?"
    ]
    
    for req in requirements:
        memory.add_turn([TextBlock(content=req)], ROLE.USER)
        response = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    # Phase 2: Technical design
    technical_questions = [
        "How would I structure the system architecture?",
        "What technologies do you recommend for backend and frontend?",
        "How do I manage scalability and availability?"
    ]
    
    for question in technical_questions:
        memory.add_turn([TextBlock(content=question)], ROLE.USER)
        response = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    
    # Phase 3: Summary and action plan
    summary_response = client.invoke(
        "Summarize the project and provide an action plan with the next 5 steps",
        memory=memory
    )
    
    return summary_response.text

# Usage
chatbot_plan = develop_chatbot_with_ai()
print(chatbot_plan)
```

### Intelligent memory management
```python
class SmartMemory:
    """Manages memory with advanced strategies"""
    
    def __init__(self, max_turns: int = 10, importance_threshold: float = 0.7):
        self.memory = Memory()
        self.max_turns = max_turns
        self.importance_threshold = importance_threshold
    
    def add_turn(self, content: str, role: ROLE, importance: float = 0.5):
        """Adds a turn with importance evaluation"""
        # Add turn
        self.memory.add_turn([TextBlock(content=content)], role)
        
        # Manage memory size
        if len(self.memory.memory) > self.max_turns:
            # Keep important turns and recent turns
            important_turns = [t for t in self.memory.memory if hasattr(t, 'importance') and t.importance > self.importance_threshold]
            recent_turns = self.memory.memory[-self.max_turns//2:]
            
            # Combine and limit
            combined = list(set(important_turns + recent_turns))
            self.memory.memory = combined[-self.max_turns:]
    
    def get_context_summary(self, client):
        """Generates a context summary to optimize tokens"""
        if len(self.memory.memory) > 5:
            summary_response = client.invoke(
                "Briefly summarize the main points of the conversation",
                memory=self.memory
            )
            return summary_response.text
        return None

# Usage
smart_memory = SmartMemory(max_turns=8)
# ... conversation with automatic memory management
```

## Complete documentation

➡️ **[GUIDA_TEXT_ONLY.md](GUIDA_TEXT_ONLY.md)** - Complete technical guide with advanced examples, best practices, troubleshooting and copyable code

➡️ **[text_only_examples.py](text_only_examples.py)** - Complete script with all demos and practical examples
