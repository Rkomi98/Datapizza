# Advanced memory summary management

Advanced example for intelligent conversation memory summary management with DatapizzAI. This example significantly extends the basic functionality by showing professional techniques for production applications.

## Table of contents

- [Differences with the basic example](#differences-with-the-basic-example)
- [Available summarization strategies](#available-summarization-strategies)
- [Configuration](#configuration)
- [Scenario-specific configurations](#scenario-specific-configurations)
- [Basic usage](#basic-usage)
- [Redis cache for production](#redis-cache-for-production)
- [Monitoring and debugging](#monitoring-and-debugging)
- [Error handling and recovery](#error-handling-and-recovery)
- [Production best practices](#production-best-practices)
- [Performance comparison](#performance-comparison)
- [Limitations and future developments](#limitations-and-future-developments)
- [Demo and examples](#demo-and-examples)

## Differences with the basic example

The `SummarizingChat` example in the main README is intentionally simple for educational purposes. This advanced example adds:

- **Multiple strategies** for summarization (not just complete summary)
- **Automatic persistence** to file with backup
- **Intelligent cache** for generated summaries
- **Detailed metrics** for monitoring and debugging
- **Robust error handling** with fallback
- **Flexible configuration** for different scenarios
- **Professional logging** for debugging
- **Periodic auto-save** of memory
- **Memory analysis** before decisions

## Available summarization strategies

### 1. Full summary (FULL_SUMMARY)
Complete summary of all memory, then reset.
- **Use**: when memory becomes too long
- **Pros**: maximum token reduction
- **Cons**: loss of conversational context

### 2. Keep recent (KEEP_RECENT) 
Summarize everything except the last N messages.
- **Use**: maintains recent conversational flow
- **Pros**: balances token reduction and context
- **Cons**: important old messages might be lost

### 3. Importance based (IMPORTANCE_BASED)
Keep messages with important keywords.
- **Use**: technical or business conversations
- **Pros**: preserves critical information
- **Cons**: requires keyword configuration

### 4. Hierarchical (HIERARCHICAL) - *To be implemented*  
Hierarchical summary (summary of summaries).

## Configuration

```python
from advanced_memory_summary import SummaryConfig, SummaryStrategy

# Configuration for production applications
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=10,                     # After 10 turns
    trigger_tokens=6000,                  # Or 6000 estimated tokens
    keep_recent_turns=3,                  # Keep 3 recent turns
    summary_max_tokens=300,               # Summary up to 300 tokens
    importance_keywords=[                 # Custom keywords
        'important', 'decision', 'todo', 'problem', 
        'budget', 'deadline', 'requirement', 'specs'
    ],
    auto_save_interval=5,                 # Save every 5 turns
    cache_summaries=True                  # Cache enabled
)
```

### Configurations for specific scenarios

#### Technical assistant
```python
config = SummaryConfig(
    strategy=SummaryStrategy.IMPORTANCE_BASED,
    trigger_turns=15,
    trigger_tokens=8000,
    importance_keywords=[
        'error', 'bug', 'fix', 'implementation', 
        'api', 'database', 'security', 'performance'
    ]
)
```

#### Customer service chatbot
```python
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=8,
    trigger_tokens=4000,
    keep_recent_turns=4,  # Keep more context
    importance_keywords=[
        'complaint', 'problem', 'urgent', 'resolve',
        'customer', 'order', 'payment', 'shipping'
    ]
)
```

#### Creative brainstorming
```python
config = SummaryConfig(
    strategy=SummaryStrategy.FULL_SUMMARY,  # Creative summary
    trigger_turns=12,
    trigger_tokens=7000,
    summary_max_tokens=400,  # Longer summary for creativity
)
```

## Basic usage

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import OpenAIClient
from advanced_memory_summary import AdvancedMemoryManager, SummaryConfig, SummaryStrategy

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7,
)

# Configuration
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=8,
    trigger_tokens=5000,
    keep_recent_turns=3
)

# Manager with persistence
manager = AdvancedMemoryManager(
    client=client,
    config=config,
    memory_file="conversation_memory.json",
    cache_type="memory"  # or "redis" for distributed environments
)

# Conversation
while True:
    user_input = input("You> ").strip()
    if user_input.lower() in ['exit', 'quit']:
        break
        
    try:
        response = manager.send_message(user_input)
        print(f"Bot> {response}")
        
        # Show statistics occasionally
        if len(manager.memory) % 5 == 0:
            stats = manager.get_memory_stats()
            print(f"[INFO] {stats['current_metrics']['total_turns']} turns, "
                  f"~{stats['current_metrics']['estimated_tokens']} tokens")
            
    except Exception as e:
        print(f"Error: {e}")
```

## Monitoring and debugging

### Available metrics
```python
stats = manager.get_memory_stats()

print("Current metrics:")
print(f"- Turns: {stats['current_metrics']['total_turns']}")  
print(f"- Estimated tokens: {stats['current_metrics']['estimated_tokens']}")
print(f"- Memory age: {stats['current_metrics']['oldest_turn_age']:.1f}s")
print(f"- Generated summaries: {stats['summary_history_count']}")
print(f"- Strategy: {stats['current_strategy']}")
print(f"- Cache active: {stats['cache_enabled']}")
```

### Summary history
```python
# Access complete history
for summary_entry in manager.summary_history:
    print(f"Date: {summary_entry['timestamp']}")
    print(f"Strategy: {summary_entry['strategy']}")
    print(f"Time: {summary_entry['elapsed_time']:.2f}s")
    print(f"Summary: {summary_entry['summary'][:100]}...")
    print(f"Token reduction: {summary_entry['metrics_before']['estimated_tokens']} → {summary_entry['metrics_after']['estimated_tokens']}")
    print()
```

### Logging for debug
```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_manager.log'),
        logging.StreamHandler()
    ]
)

# Now you will see detailed logs of:
# - Summary triggers
# - Cache hit/miss
# - Before/after metrics
# - Errors and fallback
```

## Performance comparison

| Feature        |       Basic example     | Advanced example |
|----------------|------------------------|------------------|
| Strategies     | 1 (complete summary) | 3+ (configurable) |
| Persistence    |            ❌          | ✅ Automatic with backup |
| Cache          |            ❌          | ✅ Memory/Redis |
| Metrics        |            ❌          | ✅ Detailed |
| Error handling |            ❌          | ✅ Robust |
| Logging        |            ❌          | ✅ Professional |
| Configuration  |         Hard-coded | ✅ Flexible |
| Recovery       |            ❌          | ✅ Automatic backups |
