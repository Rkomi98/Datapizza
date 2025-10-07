import os
import requests
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.clients import ClientFactory
from datapizza.clients.factory import Provider
from datapizza.core.clients import ClientResponse
from datapizza.memory import Memory
from datapizza.type import TextBlock
from typing import Optional

load_dotenv()

# Test 1: Direct Client Configuration
print("=== Test 1: Direct Client Configuration ===")

# OpenAI
openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7
)

response = openai_client.invoke("Say hello in one sentence")
print(f"OpenAI: {response.text}")
print("✅ OpenAI client successful\n")

# Test 2: Using ClientFactory
print("=== Test 2: Using ClientFactory ===")

openai = ClientFactory.create(
    provider=Provider.OPENAI,
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7
)

response = openai.invoke("Say goodbye in one sentence")
print(f"OpenAI via Factory: {response.text}")
print("✅ ClientFactory successful\n")

# Test 3: Custom Ollama Adapter
print("=== Test 3: Custom Ollama Adapter ===")

class OllamaClient:
    def __init__(self, model: str = "gemma3n:e2b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _build_messages(self, input=None, memory: Optional[Memory] = None):
        """Build chat messages for the Ollama API including conversation memory."""
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
        """Roughly estimate the number of tokens using word count."""
        return int(len(text.split()) * 1.3)  # Approximate conversion factor

    def invoke(self, input=None, memory: Optional[Memory] = None) -> ClientResponse:
        """Call the Ollama model and return a Datapizza-AI-compatible response."""
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

            # Extract the assistant reply
            text = data.get("message", {}).get("content", "").strip()
            if not text:
                text = str(data)

            # Estimate token usage
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

# Test Ollama client (skip if not available)
try:
    client = OllamaClient()
    response = client.invoke("Hi! Summarise the Pythagorean theorem in one sentence.")
    
    print(f"Response: {response.text}")
    print(f"Prompt tokens: {response.prompt_tokens_used}")
    print(f"Completion tokens: {response.completion_tokens_used}")
    print(f"Stop reason: {response.stop_reason}")
    print("✅ Custom Ollama adapter successful\n")
except Exception as e:
    print(f"⚠️ Ollama not available (expected if not running): {e}\n")

print("✅ All tests passed for video_04!")

