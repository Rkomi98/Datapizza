# Video 4: Working with Multiple Clients and Custom Adapters

## Introduction (1.5 min)

Hey everyone, welcome back! We've been building with OpenAI exclusively so far, but what if you want to use Claude? Or Gemini? Or a custom model running locally?

Switching between providers shouldn't mean rewriting your entire codebase. That's exactly what we're solving today.

[Visual: Show logos of different providers - OpenAI, Anthropic, Google, etc.]

We're going to cover three approaches: directly configuring clients for each provider, using ClientFactory for consistency, and building custom adapters for providers that aren't supported yet.

By the end, you'll be able to swap between any LLM provider with minimal code changes, and you'll know how to integrate your own models.

Let's get started.

[Transition: "Three Methods"]

## Content Main (7.5 min)

### Direct Client Configuration (2 min)

Each provider has its own client class. Let me show you the main ones.

[Show code for multiple providers]

```python
# OpenAI
from datapizza.clients.openai import OpenAIClient

openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7
)

# Anthropic (Claude)
from datapizza.clients.anthropic import AnthropicClient

claude_client = AnthropicClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-20250514",
    temperature=0.8
)

# Google (Gemini)
from datapizza.clients.google import GoogleClient

gemini_client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
    temperature=0.6
)
```

[Show each client making a request]

Notice the pattern—they all use the same interface. Create client, call invoke, get a response. The underlying API is different, but your code stays consistent.

This is crucial. You can develop with one provider and switch to another without touching your business logic.

[Visual: Show code using different clients with identical invoke calls]

The main differences are in the constructor—API keys, model names, provider-specific parameters. But once you have a client, it works the same way.

### Using ClientFactory (2 min)

Direct configuration works, but there's a cleaner approach—ClientFactory. It abstracts away provider-specific details.

[Show code]

```python
from datapizza.clients import ClientFactory
from datapizza.clients.factory import Provider

# Create any provider with the same interface
openai = ClientFactory.create(
    provider=Provider.OPENAI,
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7
)

claude = ClientFactory.create(
    provider=Provider.ANTHROPIC,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-20250514",
    temperature=0.7
)

gemini = ClientFactory.create(
    provider=Provider.GOOGLE,
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
    temperature=0.7
)
```

[Run identical invoke calls on all three]

This is my preferred approach for production. You can make provider selection configurable—read it from environment variables or config files—and swap providers without code changes.

[Show example of config-driven selection]

```python
provider_name = os.getenv("LLM_PROVIDER", "openai")
client = ClientFactory.create(
    provider=provider_name,
    api_key=os.getenv(f"{provider_name.upper()}_API_KEY"),
    model=os.getenv("MODEL_NAME"),
    temperature=0.7
)
```

Now you control everything through environment variables. Deploy the same code with different providers in different environments.

### Building Custom Adapters (3.5 min)

What if you need a provider that isn't supported? Or a local model? You build a custom adapter.

Let me show you the pattern with a local Ollama model.

[Show code structure]

```python
from typing import Optional
from datapizza.clients import ClientResponse
from datapizza.memory import Memory
from datapizza.type import TextBlock

class OllamaClient:
    def __init__(self, model: str = "gemma:2b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def invoke(self, input=None, memory: Optional[Memory] = None) -> ClientResponse:
        # Build messages from memory
        messages = []
        if memory:
            for turn in memory.memory:
                role = turn.role.value
                content = " ".join(
                    getattr(b, "content", "") for b in turn.blocks
                )
                if content:
                    messages.append({"role": role, "content": content})
        
        # Add current input
        if isinstance(input, str):
            messages.append({"role": "user", "content": input})
        
        # Call Ollama API
        import requests
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": messages, "stream": False}
        )
        
        # Parse response
        data = response.json()
        text = data.get("message", {}).get("content", "")
        
        # Return ClientResponse
        return ClientResponse(
            content=[TextBlock(content=text)],
            prompt_tokens_used=0,  # Ollama doesn't expose this
            completion_tokens_used=0,
            stop_reason="stop"
        )
```

[Walk through the key parts]

The pattern is straightforward: accept memory, build the message history, call your provider's API, return a ClientResponse.

The ClientResponse wrapper is important—it gives you the same interface as all other clients. Your code consuming this client doesn't need to know it's talking to Ollama instead of OpenAI.

[Show it in use]

```python
ollama_client = OllamaClient(model="gemma:2b")
response = ollama_client.invoke("Explain machine learning simply")
print(response.text)
```

[Run and show output]

This works exactly like any other client. You can use it with memory, with agents, with the full framework.

[Show a more complex example with IBM WatsonX from the docs]

The same pattern applies for any provider. You adapt their API to Datapizza-AI's interface, and suddenly everything in the framework works with it.

This is how you future-proof your code. New provider launches? Build an adapter. Company requires a specific deployment? Adapter. Want to route requests through a custom gateway? Adapter.

## Conclusion (1 min)

Let's review: We covered direct client configuration for OpenAI, Anthropic, and Google. We used ClientFactory for cleaner, config-driven provider selection. And we built custom adapters so you can integrate any LLM, whether it's a new API or a local model.

[Visual: Show three approaches side by side]

The key insight is this unified interface. Write your business logic once, swap providers anytime. That's architectural flexibility.

In the next video, we're moving into tools and function calling—how to give your LLMs the ability to take actions, not just generate text.

Before that, try swapping providers in your chatbot from Video 2. Use ClientFactory to make it configurable. See how easy it is to switch between Claude and GPT with zero logic changes.

See you next time!

[Note for narrator: Emphasize the power of the unified interface—this is what makes production systems maintainable]
