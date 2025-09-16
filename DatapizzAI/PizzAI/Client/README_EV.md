# DatapizzAI Client Configuration Guide

This guide will help you set up all kind of clients available in the DatapizzAI library to interact with different LLM model providers.

## Table of contents

- [Prerequisites](#prerequisites)
- [Basic code setup](#basic-code-setup)
- [Method 1: Using ClientFactory (recommended)](#method-1-using-clientfactory-recommended)
- [Method 2: Direct client configuration](#method-2-direct-client-configuration)
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
```

---

## Method 1: Using ClientFactory (recommended)

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
```

---

## Method 2: Direct client configuration

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
```

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

```python
import os
from typing import Optional, List, Dict, Any
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai import APIClient

from datapizzai.type import TextBlock
from datapizzai.memory import Memory

# Use the same response structure as DatapizzAI clients
# (assuming ClientResponse is available from the library)
try:
    from datapizzai.clients.base import ClientResponse
except ImportError:
    # Fallback if not available
    from pydantic import BaseModel
    class ClientResponse(BaseModel):
        text: str
        prompt_tokens_used: int = 0
        completion_tokens_used: int = 0
        stop_reason: str = "stop"


class IBMWatsonXClient:
    def __init__(self, model_id: str = "ibm/granite-3-2-8b-instruct", temperature: float = 0.7):
        self.model_id = model_id
        self.temperature = temperature
        
        # IBM WatsonX credentials configuration
        self.credentials = Credentials(
            url=os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=os.getenv("IBM_WATSONX_API_KEY")
        )
        
        # Initialize API client
        self.client = APIClient(self.credentials)
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID")
        
        # Set default project
        if self.project_id:
            self.client.set.default_project(self.project_id)
        
        # Initialize the model
        self.model = self._initialize_model()
    
    def _initialize_model(self):
        """Initialize IBM WatsonX model once to optimize performance."""
        model_params = {
            "max_new_tokens": 1000,
            "temperature": self.temperature,
            "stop_sequences": ["Human:", "Assistant:"]
        }
        
        return ModelInference(
            model_id=self.model_id,
            api_client=self.client,
            params=model_params
        )
    
    def _build_prompt(self, input_text: str = None, memory: Optional[Memory] = None) -> str:
        """Build prompt including conversation memory."""
        prompt_parts = []
        
        # Add context from memory
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(getattr(block, "content", "") for block in turn.blocks)
                if content:
                    if role.lower() == "user":
                        prompt_parts.append(f"Human: {content}")
                    elif role.lower() == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
        
        # Add current input
        if input_text:
            prompt_parts.append(f"Human: {input_text}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def invoke(self, input_text: str = None, memory: Optional[Memory] = None) -> ClientResponse:
        """Invoke IBM Watson model and return compatible response."""
        try:
            prompt = self._build_prompt(input_text, memory)
            
            # Call IBM Watson model
            response = self.model.generate_text(prompt=prompt)
            
            # Extract response text
            if isinstance(response, dict):
                text = response.get("generated_text", "").strip()
                # Remove "Assistant:" prefix if present
                if text.startswith("Assistant:"):
                    text = text[10:].strip()
            else:
                text = str(response).strip()
            
            # Approximate token estimation (IBM Watson doesn't always provide detailed metrics)
            estimated_prompt_tokens = len(prompt.split()) * 1.3  # Rough estimate
            estimated_completion_tokens = len(text.split()) * 1.3
            
            return ClientResponse(
                content=[TextBlock(content=text)],
                prompt_tokens_used=int(estimated_prompt_tokens),
                completion_tokens_used=int(estimated_completion_tokens),
                stop_reason="stop"
            )
            
        except Exception as e:
            return ClientResponse(
                content=[TextBlock(content=f"IBM Watson error: {str(e)}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error"
            )


# Usage example
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create IBM WatsonX client
    watsonx_client = IBMWatsonXClient(
        model_id="ibm/granite-3-2-8b-instruct",
        temperature=0.7
    )
    
    # Test the client
    response = watsonx_client.invoke("Hello! Introduce yourself briefly.")
    print(f"Response: {response.text}")
    print(f"Tokens used: {response.prompt_tokens_used + response.completion_tokens_used}")
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

```python
import requests
from typing import Optional, Union, List
from pydantic import BaseModel

from datapizzai.type import TextBlock
from datapizzai.memory import Memory
from datapizzai.clients import ClientResponse

class OllamaClient:
    def __init__(self, model: str = "gemma3n:e2b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _build_messages(self, input=None, memory: Optional[Memory] = None):
        """Build messages for Ollama chat API including memory."""
        msgs = []
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(getattr(b, "content", "") for b in turn.blocks)
                if content:
                    msgs.append({"role": role, "content": content})
        if isinstance(input, str) and input:
            msgs.append({"role": "user", "content": input})
        return msgs

    def _estimate_tokens(self, text: str) -> int:
        """Approximate token count estimation based on word count."""
        return int(len(text.split()) * 1.3)  # Rough conversion factor

    def invoke(self, input=None, memory: Optional[Memory] = None) -> ClientResponse:
        """Invoke Ollama model and return DatapizzAI-compatible response."""
        messages = self._build_messages(input, memory)
        payload = {
            "model": self.model, 
            "messages": messages, 
            "stream": False
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            # Extract response text
            text = data.get("message", {}).get("content", "").strip()
            if not text:
                text = str(data)
            
            # Calculate token usage estimates
            prompt_text = " ".join([msg["content"] for msg in messages])
            prompt_tokens = self._estimate_tokens(prompt_text)
            completion_tokens = self._estimate_tokens(text)
            
            return ClientResponse(
                content=[TextBlock(content=text)],
                prompt_tokens_used=prompt_tokens,
                completion_tokens_used=completion_tokens,
                stop_reason="stop"
            )
            
        except requests.RequestException as e:
            return ClientResponse(
                content=[TextBlock(content=f"Ollama connection error: {str(e)}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error"
            )
        except Exception as e:
            return ClientResponse(
                content=[TextBlock(content=f"Ollama error: {str(e)}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error"
            )


if __name__ == "__main__":
    # Test local client
    client = OllamaClient()
    response = client.invoke("Summarize the Pythagorean theorem in one sentence.")
    
    print(f"Response: {response.text}")
    print(f"Prompt tokens: {response.prompt_tokens_used}")
    print(f"Completion tokens: {response.completion_tokens_used}")
    print(f"Stop reason: {response.stop_reason}")
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

This guide covers all aspects of client configuration. For advanced features, consult the complete DatapizzAI documentation.
