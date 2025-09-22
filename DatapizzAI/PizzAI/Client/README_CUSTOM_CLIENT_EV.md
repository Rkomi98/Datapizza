# DatapizzAI Custom Clients

This guide shows how to design two complete adapters so DatapizzAI can talk to providers that are not supported out of the box or to local models. Because every client already exposes the same `invoke` interface, creating and using a custom client stays straightforward.

## Core principles
- **Common interface**: each adapter must expose `invoke(input_text, memory=None)` and return a `ClientResponse`.
- **Memory handling**: convert `Memory` objects into a format the target provider understands (prompt strings, message arrays, etc.).
- **Observability**: when the provider does not expose token statistics, provide reasonable estimates or helpful logs.

## Example A — External provider (IBM WatsonX)
This example explains how to configure a client that is not bundled with DatapizzAI. We will walk through the setup step by step.

### Detailed procedure
1. **Install the SDK**: `pip install ibm-watsonx-ai` (inside your virtual environment).
2. **Populate the `.env`** file with:
   ```bash
   IBM_WATSONX_API_KEY=sk-...
   IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
   IBM_WATSONX_PROJECT_ID=your-project-id
   ```
3. **Verify the credentials** by running `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('IBM_WATSONX_API_KEY') is not None)"`.
4. **Open `custom_client_external.py`** and, if needed, adjust `model_id`, `temperature`, or other parameters such as `stop_sequences`.
5. **Integrate the client** inside your application code:
   ```python
   from Client.custom_client_external import IBMWatsonXClient

   watson_client = IBMWatsonXClient(model_id="ibm/granite-3-2-8b-instruct")
   response = watson_client.invoke("Give me a summary of the corporate vision.")
   print(response.text)
   ```
6. **Handle memory**: pass a `Memory` instance to `invoke` when you need multi-turn conversations.
7. **Monitor errors**: whenever you receive `stop_reason='error'`, inspect `content[0].content` to read the raw provider message.

### Main code (excerpt)
```python
import os
from typing import Optional, List, Dict, Any
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai import APIClient

from datapizzai.type import TextBlock
from datapizzai.memory import Memory
from datapizzai.clients import ClientResponse


class IBMWatsonXClient:
    def __init__(self, model_id: str = "ibm/granite-3-2-8b-instruct", temperature: float = 0.7):
        self.model_id = model_id
        self.temperature = temperature

        # Configure IBM WatsonX credentials
        self.credentials = Credentials(
            url=os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=os.getenv("IBM_WATSONX_API_KEY")
        )

        # Initialise the API client
        self.client = APIClient(self.credentials)
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID")

        # Set a default project if available
        if self.project_id:
            self.client.set.default_project(self.project_id)

        # Create the model once for reuse
        self.model = self._initialize_model()

    def _initialize_model(self):
        """Initialise the IBM WatsonX model once to optimise performance."""
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
        """Build the prompt by appending the conversation memory."""
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

        # Append current input
        if input_text:
            prompt_parts.append(f"Human: {input_text}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def invoke(self, input_text: str = None, memory: Optional[Memory] = None) -> ClientResponse:
        """Call the IBM WatsonX model and return a DatapizzAI-compatible response."""
        try:
            prompt = self._build_prompt(input_text, memory)

            # Query the IBM Watson model
            response = self.model.generate_text(prompt=prompt)

            # Extract the generated text
            if isinstance(response, dict):
                text = response.get("generated_text", "").strip()
                # Remove the "Assistant:" prefix if present
                if text.startswith("Assistant:"):
                    text = text[10:].strip()
            else:
                text = str(response).strip()

            # Approximate token usage (IBM WatsonX does not always expose metrics)
            estimated_prompt_tokens = len(prompt.split()) * 1.3
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

    watsonx_client = IBMWatsonXClient(
        model_id="ibm/granite-3-2-8b-instruct",
        temperature=0.7
    )

    response = watsonx_client.invoke("Hello! Introduce yourself briefly.")
    print(f"Response: {response.text}")
    print(f"Tokens used: {response.prompt_tokens_used + response.completion_tokens_used}")
```

## Example B — Local model (Ollama)

### Detailed procedure
1. **Install Ollama** (macOS/Linux): `curl -fsSL https://ollama.com/install.sh | sh`.
2. **Start the daemon** in a separate terminal: `ollama serve`.
3. **Download the desired model**: `ollama pull gemma3n:e2b` (replace with the tag you prefer).
4. **Run a CLI smoke test**: `ollama run gemma3n:e2b "Hi, who are you?"` to ensure the local setup works.
5. Define the client exactly once and reuse it.

### Main code (excerpt)
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
        """Call the Ollama model and return a DatapizzAI-compatible response."""
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


if __name__ == "__main__":
    # Local client smoke test
    client = OllamaClient()
    response = client.invoke("Hi! Summarise the Pythagorean theorem in one sentence.")

    print(f"Response: {response.text}")
    print(f"Prompt tokens: {response.prompt_tokens_used}")
    print(f"Completion tokens: {response.completion_tokens_used}")
    print(f"Stop reason: {response.stop_reason}")
```
