# DatapizzAI Client Configuration Guide

This guide will help you set up all kind of clients available in the DatapizzAI library to interact with different LLM model providers.

## Prerequisites

### Installing dependencies
```bash
pip install python-dotenv
```

### Environment variables configuration
Create a `.env` file in your project root with at least one API key:

```bash
# .env file - add only the keys you need
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
MISTRAL_API_KEY=your-mistral-api-key-here
AZURE_OPENAI_API_KEY=your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
```

### Basic code setup
```python
import os
from dotenv import load_dotenv

# Load environment variables
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
```

---

## Method 1: Using ClientFactory (recommended)

The `ClientFactory` is the simplest way to create clients with automatic configuration.

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

# Available models: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
```

### Anthropic client (Claude)
```python
# Basic configuration
anthropic_client = ClientFactory.create(
    provider=Provider.ANTHROPIC,  # or "anthropic"
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-4-sonnet-latest",
    system_prompt="You are Claude, an Anthropic AI assistant.",
    temperature=0.5
)

# Available models: claude-3-5-sonnet-latest, claude-3-5-haiku-latest, claude-3-opus-latest
```

### Google client (Gemini)
```python
# Basic configuration
google_client = ClientFactory.create(
    provider=Provider.GOOGLE,  # or "google"
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash",
    system_prompt="You are Gemini, Google's AI assistant.",
    temperature=0.6
)

# Available models: gemini-2.0-flash, gemini-1.5-pro, gemini-1.5-flash
```

### Mistral client
```python
# Basic configuration
mistral_client = ClientFactory.create(
    provider=Provider.MISTRAL,  # or "mistral"
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-large-latest",
    system_prompt="You are an AI assistant based on Mistral.",
    temperature=0.7
)

# Available models: mistral-large-latest, mistral-medium-latest, mistral-small-latest
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
```

---

## Method 2: Direct client configuration

For advanced configurations, you can create clients directly.

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
    model="claude-3-5-sonnet-latest",
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
    model="gemini-2.0-flash",
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
```

---

## Complete usage example

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

Once you've configured your client, you can explore:

1. **Memory management** for multi-turn conversations
2. **Caching system** to optimize performance
3. **Tools and function calling** for advanced features
4. **Structured responses** with Pydantic models
5. **Streaming** for real-time responses

This guide covers all aspects of client configuration. For advanced features, consult the complete DatapizzAI documentation.
