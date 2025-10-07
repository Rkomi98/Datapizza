# Video 4: Working with Multiple Clients and Custom Adapters

## Introduction (1.5 min)

Hey everyone, and welcome back. So far, we've been building exclusively with OpenAI. But what if you want to use Claude, Gemini, or even a custom model running locally?

The good news is that switching between providers doesn't have to mean rewriting your entire codebase. With Datapizza-AI, it doesn't, and that's exactly what we're going to solve today.

[Visual: Show logos of different providers - OpenAI, Anthropic, Google, etc.]

We'll explore three distinct approaches: directly configuring clients for each provider, using a `ClientFactory` for greater consistency, and building custom adapters for providers that aren't yet supported out of the box.

By the end of this video, you'll be able to swap between any LLM provider with minimal code changes and know how to integrate your own custom models. This is a powerful skill to have in your toolkit.

Let's dive into the three methods.

## Content Main (7.5 min)

### Direct Client Configuration (2 min)

Each provider has its own client class. Let's take a look at the main ones.

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

Notice the pattern here: they all share the same interface. You create a client, call `invoke`, and get a response. Although the underlying API is different for each, your code remains consistent.

This is a crucial design principle. It allows you to develop with one provider and seamlessly switch to another without ever touching your core business logic.

[Visual: Show code using different clients with identical invoke calls]

The main differences lie in the constructor, where you'll find API keys, model names, and other provider-specific parameters. But once you have a client instance, it works just like any other.

### Using ClientFactory (2 min)

While direct configuration is effective, there's a cleaner and more scalable approach: the `ClientFactory`. It abstracts away all the provider-specific details for you.

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

Now, you can control everything through environment variables, allowing you to deploy the same code with different providers across various environments.

### Building Custom Adapters (3.5 min)

But what if you need to use a provider that isn't supported yet, or perhaps a local model? That's when you build a custom adapter.

Let's walk through the pattern using a local Ollama model as an example.

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

The pattern is straightforward: accept `memory`, build the message history, call your provider's API, and return a `ClientResponse`.

The `ClientResponse` wrapper is key because it provides the same standardized interface as all other clients. The code consuming this client doesn't need to know it's communicating with Ollama instead of OpenAI.

[Show it in use]

```python
ollama_client = OllamaClient(model="gemma:2b")
response = ollama_client.invoke("Explain machine learning simply")
print(response.text)
```

[Run and show output]

This works just like any other client. You can use it with memory, agents, and the rest of the framework.

[Show a more complex example with IBM WatsonX from the docs]

The same pattern applies to any provider. You adapt their API to the Datapizza-AI interface, and just like that, everything in the framework becomes compatible with it.

This is how you future-proof your applications. A new provider launches? Build an adapter. Your company requires a specific deployment? Adapter. You want to route requests through a custom gateway? You guessed it—adapter.

## Conclusion (1 min)

Let's do a quick recap. We covered direct client configuration for OpenAI, Anthropic, and Google. We then used `ClientFactory` for cleaner, configuration-driven provider selection. Finally, we built custom adapters, enabling you to integrate any LLM, whether it's a new API or a local model.

[Visual: Show three approaches side by side]

The key takeaway here is the power of a unified interface. You write your business logic once and can swap providers at any time. That's what real architectural flexibility looks like.

In the next video, we'll dive into tools and function calling, giving your LLMs the ability to take action, not just generate text. This is where things get really exciting.

Before you move on, try swapping providers in the chatbot you built in Video 2. Use `ClientFactory` to make it configurable, and see for yourself how easy it is to switch between Claude and GPT with zero changes to your logic.

If you're enjoying this series, don't forget to hit that subscribe button. I'll see you in the next one!

[Note for narrator: Emphasize the power of the unified interface—this is what makes production systems maintainable]
