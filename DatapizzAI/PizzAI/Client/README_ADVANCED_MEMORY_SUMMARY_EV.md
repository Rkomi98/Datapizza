# Advanced Memory Summary Management

This guide presents an advanced, production‑oriented approach to managing conversation memory summaries with DatapizzAI. It significantly extends the basic examples with robust techniques and operational best practices.

## Table of Contents

- [Differences vs. the basic example](#differences-vs-the-basic-example)
- [Available summarization strategies](#available-summarization-strategies)
- [Configuration](#configuration)
- [Scenario‑specific configurations](#scenario-specific-configurations)
- [Basic usage](#basic-usage)
- [Redis cache for production](#redis-cache-for-production)
- [Monitoring and debugging](#monitoring-and-debugging)
- [Error handling and recovery](#error-handling-and-recovery)
- [Production best practices](#production-best-practices)
- [Performance comparison](#performance-comparison)
- [Limitations and future work](#limitations-and-future-work)
- [Demo and examples](#demo-and-examples)

## Differences vs. the basic example

The basic `SummarizingChat` in the main README is intentionally simple for learning purposes. This advanced guide adds:

- Multiple summarization strategies (beyond full summary)
- Automatic file persistence with backups
- Smart cache for generated summaries
- Detailed metrics for monitoring and debugging
- Robust error handling with fallbacks
- Flexible configuration for different scenarios
- Professional logging for debugging
- Periodic auto‑save of memory
- Memory analysis before decisions

## Available summarization strategies

### 1. Full summary (FULL_SUMMARY)
Summarize the entire memory, then reset.
- Use when memory becomes too long
- Pros: maximum token reduction
- Cons: conversation context loss

### 2. Keep recent (KEEP_RECENT)
Summarize everything except the last N messages.
- Use to keep the most recent flow in context
- Pros: balances token reduction and context
- Cons: older important messages may be lost

### 3. Importance based (IMPORTANCE_BASED)
Keep messages with important keywords.
- Use for technical/business conversations
- Pros: preserves critical information
- Cons: requires keyword configuration

### 4. Hierarchical (HIERARCHICAL) — to be implemented
Hierarchical summarization (summary of summaries).

## Configuration

```python
from advanced_memory_summary import SummaryConfig, SummaryStrategy

# Production‑oriented configuration
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=10,                     # Trigger after 10 turns
    trigger_tokens=6000,                  # Or ~6000 estimated tokens
    keep_recent_turns=3,                  # Keep last 3 turns
    summary_max_tokens=300,               # Cap summary at ~300 tokens
    importance_keywords=[                 # Custom keywords
        'important', 'decision', 'todo', 'issue',
        'budget', 'deadline', 'requirement', 'specs'
    ],
    auto_save_interval=5,                 # Save every 5 turns
    cache_summaries=True                  # Enable cache for summaries
)
```

## Scenario‑specific configurations

### Technical assistant
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

### Customer service chatbot
```python
config = SummaryConfig(
    strategy=SummaryStrategy.KEEP_RECENT,
    trigger_turns=8,
    trigger_tokens=4000,
    keep_recent_turns=4,  # Keep more recent turns
    importance_keywords=[
        'complaint', 'problem', 'urgent', 'resolve',
        'customer', 'order', 'payment', 'shipping'
    ]
)
```

### Creative brainstorming
```python
config = SummaryConfig(
    strategy=SummaryStrategy.FULL_SUMMARY,
    trigger_turns=12,
    trigger_tokens=7000,
    summary_max_tokens=400,
)
```

## Basic usage

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.cache import MemoryCache
from advanced_memory_summary import AdvancedMemoryManager, SummaryConfig, SummaryStrategy

load_dotenv()

# Client with cache
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7,
    cache=MemoryCache()
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
    cache_type="memory"  # or "redis" in distributed environments
)

# Conversation
while True:
    user_input = input("You> ").strip()
    if user_input.lower() in ['exit', 'quit']:
        break
    try:
        response = manager.send_message(user_input)
        print(f"Bot> {response}")
        # Periodically print stats
        if len(manager.memory) % 5 == 0:
            stats = manager.get_memory_stats()
            print(f"[INFO] {stats['current_metrics']['total_turns']} turns, "
                  f"~{stats['current_metrics']['estimated_tokens']} tokens")
    except Exception as e:
        print(f"Error: {e}")
```

## Redis cache for production

Use Redis as a shared cache in distributed environments:

```python
from datapizzai.cache import RedisCache

redis_cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    expiration_time=7200  # 2 hours
)

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=redis_cache
)

manager = AdvancedMemoryManager(
    client=client,
    config=config,
    memory_file="memory.json",
    cache_type="redis"  # Also cache summaries in Redis
)
```

## Monitoring and debugging

### Available metrics
```python
stats = manager.get_memory_stats()

print("Current metrics:")
print(f"- Turns: {stats['current_metrics']['total_turns']}")
print(f"- Estimated tokens: {stats['current_metrics']['estimated_tokens']}")
print(f"- Memory age: {stats['current_metrics']['oldest_turn_age']:.1f}s")
print(f"- Summaries generated: {stats['summary_history_count']}")
print(f"- Strategy: {stats['current_strategy']}")
print(f"- Cache enabled: {stats['cache_enabled']}")
```

### Summary history
```python
for entry in manager.summary_history:
    print(f"Timestamp: {entry['timestamp']}")
    print(f"Strategy: {entry['strategy']}")
    print(f"Elapsed: {entry['elapsed_time']:.2f}s")
    print(f"Summary: {entry['summary'][:100]}...")
    print(f"Token reduction: {entry['metrics_before']['estimated_tokens']} → {entry['metrics_after']['estimated_tokens']}")
    print()
```

### Logging for debug
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_manager.log'),
        logging.StreamHandler()
    ]
)

# You will see detailed logs for:
# - Summary triggers
# - Cache hit/miss
# - Before/after metrics
# - Errors and fallbacks
```

## Error handling and recovery

The manager handles:

- API errors: safe fallback without losing memory
- Cache issues: continues without cache
- Corrupted files: automatic backups
- Failed summaries: keeps original memory

```python
backup_memory = manager.memory.copy()

try:
    risky_operation()
except Exception as e:
    manager.memory = backup_memory
    logger.error(f"Restored backup after error: {e}")

success = manager.reset_memory(confirm=True)
```

## Production best practices

### 1. Trigger configuration
```python
# Short conversations (< 20 messages)
config = SummaryConfig(trigger_turns=12, trigger_tokens=4000)

# Long conversations (work sessions)
config = SummaryConfig(trigger_turns=25, trigger_tokens=10000)

# Strict token constraints
config = SummaryConfig(trigger_turns=6, trigger_tokens=2000)
```

### 2. Strategy selection
- Customer service: `KEEP_RECENT` (retain immediate context)
- Technical consulting: `IMPORTANCE_BASED` (preserve technical info)
- General chatbot: `FULL_SUMMARY` (max efficiency)

### 3. Production monitoring
```python
def log_metrics_periodically(manager):
    stats = manager.get_memory_stats()
    logger.info("METRICS", extra={
        'turns': stats['current_metrics']['total_turns'],
        'tokens': stats['current_metrics']['estimated_tokens'],
        'summaries': stats['summary_history_count'],
        'strategy': stats['current_strategy']
    })
```

### 4. Persistence management
```python
memory_file = f"memory_{user_id}_{session_id}.json"
manager = AdvancedMemoryManager(
    client=client,
    config=config,
    memory_file=memory_file
)

cleanup_old_memory_files(days_old=30)
```

## Performance comparison

| Feature | Basic example | Advanced example |
|--------|----------------|------------------|
| Strategies | 1 (full summary) | 3+ (configurable) |
| Persistence | ❌ | ✅ Auto with backups |
| Cache | ❌ | ✅ Memory/Redis |
| Metrics | ❌ | ✅ Detailed |
| Error handling | ❌ | ✅ Robust |
| Logging | ❌ | ✅ Professional |
| Configuration | Hard‑coded | ✅ Flexible |
| Recovery | ❌ | ✅ Automatic backups |

## Limitations and future work

### Current limitations
- `HIERARCHICAL` strategy not yet implemented
- Redis cache requires a separate Redis server
- Approximate token estimates (chars/4), not as precise as tiktoken

### Roadmap
- Hierarchical summaries for very long conversations
- tiktoken integration for accurate token counting
- Automatic memory file compression
- Web dashboard for monitoring
- Plugin support for various LLM providers

## Demo and examples

Run the full demo:
```bash
cd Client/
python advanced_memory_summary.py
```

The demo simulates an e‑commerce design conversation showing:
- Automatic summary triggers
- Token reduction
- Memory persistence
- Cache usage
- Real‑time metrics
