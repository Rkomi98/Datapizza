# DatapizzAI Client Configuration Guide

This guide will help you set up all kind of clients available in the DatapizzAI library to interact with different LLM model providers.
For two fully worked custom adapters take a look at [`README_CUSTOM_CLIENT_EV.md`](README_CUSTOM_CLIENT_EV.md).

## Table of contents

- [Prerequisites](#prerequisites)
- [Basic code setup](#basic-code-setup)
- [Method 1: Direct client configuration](#method-1-direct-client-configuration)
- [Method 2: Using ClientFactory (recommended)](#method-2-using-clientfactory-recommended)
- [Method 3: Custom provider via API (e.g., IBM WatsonX)](#method-3-custom-provider-via-api-eg-ibm-watsonx)
- [Method 4: Local model (Ollama/Gemma)](#method-4-local-model-ollamagemma)
- [Complete usage example](#complete-usage-example)
- [Next steps](#next-steps)

## Prerequisites

This step prepares your environment by installing dependencies and configuring API keys to prevent runtime errors.

### Installing dependencies
```bash
pip install python-dotenv
```

### Environment variables configuration
Create a `.env` file in your project root with at least one API key:

```bash
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
MISTRAL_API_KEY=your-mistral-api-key-here
AZURE_OPENAI_API_KEY=your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### Basic code setup
This code block handles the minimal initialization—loading environment variables and importing the required clients—used in all examples.
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Required imports
from datapizzai.clients import (
    ClientFactory, 
    OpenAIClient,
    AnthropicClient, 
    GoogleClient,
    MistralClient,
    AzureOpenAIClient
)
from datapizzai.clients.factory import Provider
---

## Method 1: Direct client configuration

Direct configuration offers fine-grained control over provider-specific parameters, such as caching options or custom endpoints.

### Advanced OpenAI client
```python
from datapizzai.cache import MemoryCache

# Configuration with cache
cache = MemoryCache()

openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a Python programming expert.",
    temperature=0.3,  # More deterministic for code
    cache=cache  # Optional cache to optimize performance
)

# Test the client
response = openai_client.invoke("Hello! How are you?")
print(f"Response: {response.text}")
```

### Advanced Anthropic client
```python
anthropic_client = AnthropicClient(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-20250514",
    system_prompt="You are an assistant for creative writing.",
    temperature=0.8  # More creative for writing
)

# Test the client
response = anthropic_client.invoke("Write a short poem about technology")
print(f"Response: {response.text}")
```

### Advanced Google client
```python
# Standard configuration (GenAI API)
google_client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
    system_prompt="You are a patient math tutor.",
    temperature=0.4
)

# Vertex AI configuration (enterprise deployment)
google_vertex_client = GoogleClient(
    model="gemini-1.5-pro",
    system_prompt="You are a business assistant.",
    temperature=0.5,
    # Vertex AI parameters
    project_id="your-gcp-project-id",
    location="us-central1",
    credentials_path="/path/to/service-account.json",
    use_vertexai=True
)

# Test the client
response = google_client.invoke("Explain the Pythagorean theorem")
print(f"Response: {response.text}")
```

### Advanced Mistral client
```python
mistral_client = MistralClient(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-large-latest",
    system_prompt="You are a multilingual assistant specialized in translations.",
    temperature=0.6
)

# Test the client
response = mistral_client.invoke("Translate 'Hello world' to Italian and French")
print(f"Response: {response.text}")
```

### Advanced Azure OpenAI client
```python
azure_client = AzureOpenAIClient(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a business assistant for Microsoft Azure.",
    temperature=0.5,
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version="2024-02-15-preview"
)

# Test the client
response = azure_client.invoke("Explain Azure AI services")
print(f"Response: {response.text}")
---

## Method 2: Using ClientFactory (recommended)

The `ClientFactory` abstracts away provider-specific details, allowing you to create a consistent client quickly while reducing configuration mistakes.

### OpenAI client
```python
# Basic configuration
openai_client = ClientFactory.create(
    provider=Provider.OPENAI,  # or simply "openai"
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a helpful AI assistant.",
    temperature=0.7
)

 
```

### Anthropic client (Claude)
```python
# Basic configuration
anthropic_client = ClientFactory.create(
    provider=Provider.ANTHROPIC,  # or "anthropic"
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-sonnet-4-20250514",
    system_prompt="You are Claude, an Anthropic AI assistant.",
    temperature=0.5
)

 
```

### Google client (Gemini)
```python
# Basic configuration
google_client = ClientFactory.create(
    provider=Provider.GOOGLE,  # or "google"
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
    system_prompt="You are Gemini, Google's AI assistant.",
    temperature=0.6
)

 
```

### Mistral client
```python
# Basic configuration
mistral_client = ClientFactory.create(
    provider=Provider.MISTRAL,  # or "mistral"
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-small-latest",
    system_prompt="You are an AI assistant based on Mistral.",
    temperature=0.7
)

 
```

### Azure OpenAI client
```python
# Basic configuration
azure_client = ClientFactory.create(
    provider=Provider.AZURE_OPENAI,  # or "azure_openai"
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a professional business assistant.",
    temperature=0.5,
    # Azure-specific parameters
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version="2024-02-15-preview"
)
---

## Method 3: Custom provider via API (e.g., IBM WatsonX)

To integrate custom providers like IBM Watson, you can create an adapter that respects the standard `invoke(input, memory)` interface.

### IBM WatsonX configuration

Prerequisites:
```bash
pip install ibm-watsonx-ai
```

Environment variables:
```bash
IBM_WATSONX_API_KEY=your-ibm-watsonx-api-key
IBM_WATSONX_PROJECT_ID=your-project-id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Adapter implementation:

The fully commented implementation now lives in [`Client/custom_client_external.py`](Client/custom_client_external.py). The module shows how to wrap any external provider and expose the DatapizzAI `invoke` contract.

Quick usage example:

```python
from dotenv import load_dotenv
from custom_client_external import IBMWatsonXClient

load_dotenv()

client = IBMWatsonXClient(
    model_id="ibm/granite-3-2-8b-instruct",
    temperature=0.7,
)
response = client.invoke("Hello! Introduce yourself briefly.")
print(response.text)
```

## Method 4: Local model (Ollama/Gemma)

Running locally ensures privacy, predictable costs, and low latency. With [Ollama](https://ollama.com), you can run Gemma (or others) locally and integrate it with the same `invoke` interface.

Prerequisites (Linux/macOS):

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the service (in a separate terminal)
ollama serve | cat

# Pull the Gemma model (replace the tag if you use a different variant)
ollama pull gemma3n:e2b
```

Quick CLI test:

```bash
ollama run gemma3n:e2b "Hello! Introduce yourself briefly."
```

Python adapter for full DatapizzAI compatibility:

The fully commented code lives in [`Client/custom_client_ollama.py`](Client/custom_client_ollama.py). It keeps the familiar `invoke` interface so you can call a local Ollama instance once the daemon is running (`ollama serve`).

Quick usage example:

```python
from custom_client_ollama import OllamaClient

client = OllamaClient()
response = client.invoke("Summarise the Pythagorean theorem in one sentence.")
print(response.text)
```

---

## Complete usage example

This complete script verifies that the setup and configuration for your chosen client work correctly end-to-end.

```python
#!/usr/bin/env python3
"""
Complete DatapizzAI client usage example
"""

import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.clients.factory import Provider

# Setup
load_dotenv()

def main():
    # Choose your preferred provider
    client = ClientFactory.create(
        provider=Provider.OPENAI,  # Change here to test other providers
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="You are a helpful and professional AI assistant.",
        temperature=0.7
    )
    
    # Test the client
    print("DatapizzAI Client Test")
    print("-" * 30)
    
    response = client.invoke("Hello! Introduce yourself briefly.")
    print(f"Response: {response.text}")
    print(f"Tokens used: {response.prompt_tokens_used + response.completion_tokens_used}")
    print(f"Stop reason: {response.stop_reason}")

if __name__ == "__main__":
    main()
```
---

## Next steps

Once you have validated the basic configuration, you can explore the library's advanced features.

1. **Memory management** for multi‑turn conversations (e.g., periodic summaries)
2. **Library‑side cache** (`MemoryCache`, `RedisCache`) to optimize cost/latency
3. **Tools and function calling** for advanced features
4. **Structured responses** with Pydantic models
5. **Streaming** for real-time responses

For a step-by-step walkthrough of custom adapters, see [`README_CUSTOM_CLIENT_EV.md`](README_CUSTOM_CLIENT_EV.md).

This guide covers all aspects of client configuration. For advanced features, consult the complete DatapizzAI documentation.
