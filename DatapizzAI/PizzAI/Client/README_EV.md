# Datapizza-AI Client Configuration Guide

This guide walks you through configuring every client available in the Datapizza-AI library so you can work with different LLM providers.
For two fully worked custom adapter examples, check the dedicated guide [`README_CUSTOM_CLIENT_EV.md`](README_CUSTOM_CLIENT_EV.md).

## Table of contents

- [Prerequisites](#prerequisites)
- [Basic code setup](#basic-code-setup)
- [Method 1: Direct client configuration](#method-1-direct-client-configuration)
- [Method 2: Using the ClientFactory (recommended)](#method-2-using-the-clientfactory-recommended)
- [Method 3: Custom clients (external provider or local model)](#method-3-custom-clients-external-provider-or-local-model)

## Prerequisites

Prepare your environment by installing the required dependencies and configuring API keys to avoid runtime errors.

### Install dependencies
```bash
pip install datapizza-ai python-dotenv
```

### Set environment variables
Create a `.env` file in the root of your project with at least one API key:

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
This code block provides the minimal initialization shared by all examples: it loads environment variables and imports the required clients.
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Required imports
```
---

## Method 1: Direct client configuration

Direct configuration gives you fine-grained control over provider-specific parameters such as caching options or custom endpoints.

### Direct OpenAI client
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-openai
```
```python
from datapizza.cache import MemoryCache
from datapizza.clients.openai import OpenAIClient


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

### Direct Anthropic client
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-anthropic
```
```python
from datapizza.clients.anthropic import AnthropicClient

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

### Direct Google client
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-google
```
```python
from datapizza.clients.google import GoogleClient

# Standard configuration (GenAI API)
google_client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
    system_prompt="You are a patient math tutor.",
    temperature=0.4
)

# Vertex AI configuration (enterprise deployment)
google_vertex_client = GoogleClient(
    model="gemini-2.5-pro",
    system_prompt="You are a business assistant.",
    temperature=0.5,
    # Vertex AI parameters
    project_id=os.getenv("VERTEX_PROJECT_ID"),
    location="us-central1",
    credentials_path="service-account.json",
    use_vertexai=True
)

# Test the client
response = google_client.invoke("Explain the Pythagorean theorem")
print(f"Response: {response.text}")
```

### Direct Mistral client
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-mistral
```
```python
from datapizza.clients.mistral import MistralClient

mistral_client = MistralClient(
    api_key=os.getenv("MISTRAL_API_KEY"),
    model="mistral-large-latest",
    system_prompt="You are a multilingual assistant specialized in translations.",
    temperature=0.6
)

# Test the client
response = mistral_client.invoke("Translate 'Hello world' into Italian and French")
print(f"Response: {response.text}")
```

### Direct Azure OpenAI client
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-azure-openai
```
```python
from datapizza.clients.azure_openai import AzureOpenAIClient, OpenAIClient

azure_client = AzureOpenAIClient(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a Microsoft Azure business assistant.",
    temperature=0.5,
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version="2024-02-15-preview"
)

# Test the client
response = azure_client.invoke("Explain Azure AI services to me")
print(f"Response: {response.text}")
```

---

## Method 2: Using the ClientFactory (recommended)

`ClientFactory` abstracts provider-specific details, letting you spin up a consistent client quickly while reducing the chance of mistakes.

### OpenAI client
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-openai
```
```python
from datapizza.clients import ClientFactory

from datapizza.clients.factory import Provider

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
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-anthropic
```
```python
from datapizza.clients import ClientFactory

from datapizza.clients.factory import Provider

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
Install the dedicated client with:

```bash
pip install datapizza-ai-clients-google
```
```python
from datapizza.clients import ClientFactory

from datapizza.clients.factory import Provider

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
from datapizza.clients import ClientFactory

from datapizza.clients.factory import Provider

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
from datapizza.clients import ClientFactory

from datapizza.clients.factory import Provider

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

## Method 3: Custom clients (external provider or local model)

Need a provider that is not bundled or a model that runs locally? Define a base adapter first, then specialize it for the remote API or local runtime you want to use. The interface remains `invoke(input_text, memory=None)` just like the other clients. You can explore the full walkthrough in the [deep-dive section](https://github.com/Rkomi98/Datapizza/blob/LastChanges/Datapizza-AI/PizzAI/Client/README_CUSTOM_CLIENT_EV.md). Let's go step by step.

### Step 1: Define the base adapter structure

```python
from typing import Optional, Dict, Any

from datapizza.clients import ClientResponse
from datapizza.memory import Memory
from datapizza.type import TextBlock



class CustomProviderClient:
    def __init__(self, api_key: str, model: str, **default_params: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.default_params = default_params  # e.g., temperature, top_p, etc.

    def _build_payload(self, prompt: str, memory: Optional[Memory] = None) -> Dict[str, Any]:
        messages = []
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(
                    getattr(block, "content", "") for block in turn.blocks if getattr(block, "content", "")
                )
                if content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})
        return {"model": self.model, "messages": messages, **self.default_params}

    def _execute_request(self, payload: Dict[str, Any]) -> str:
        # Place your HTTP/SDK call to the remote provider or local runtime here
        raise NotImplementedError("Replace with the call to your custom provider")

    def invoke(self, input_text: str, memory: Optional[Memory] = None) -> ClientResponse:
        payload = self._build_payload(input_text, memory)
        raw_response = self._execute_request(payload).strip()
        return ClientResponse(
            content=[TextBlock(content=raw_response)],
            prompt_tokens_used=0,  # Optional: replace with a real metric
            completion_tokens_used=0,
            stop_reason="stop"
        )
```

### Step 2: Wire up an external provider (e.g., IBM WatsonX)

Reuse the base class, supply the provider credentials, and map the SDK response back into a `ClientResponse`. Install the necessary libraries and set up the API keys before connecting everything.

The addendum includes a ready-to-use implementation tuned for [IBM WatsonX](https://github.com/Rkomi98/Datapizza/blob/LastChanges/Datapizza-AI/PizzAI/Client/README_CUSTOM_CLIENT_EV.md#example-a--external-provider-ibm-watsonx).

### Step 3: Wire up a local model (e.g., Ollama/Gemma)

If you're relying on a local model, start the service first, then download and launch the model you intend to use.

Among the detailed examples you'll find a dedicated guide for [a local client setup](https://github.com/Rkomi98/Datapizza/blob/LastChanges/Datapizza-AI/PizzAI/Client/README_CUSTOM_CLIENT_EV.md#example-b--local-model-ollama).

---

This guide covers every aspect of client configuration. For advanced features, refer to the full Datapizza-AI documentation.
