# DatapizzAI Custom Clients

This guide explains how to design two end-to-end adapters so DatapizzAI can talk to providers that are not bundled with the library or to a local runtime. Both examples keep the familiar `invoke` contract, making them drop-in replacements inside agents, memories, and tools.

## Core principles
- **Uniform interface**: expose `invoke(input_text, memory=None)` and return a `ClientResponse` object.
- **Memory handling**: translate the `Memory` object into the format required by the provider (prompt text, message list, and so on).
- **Observability**: when the provider does not return usage metrics, add clear logs or token estimates.

## Step-by-step setup
1. **Clone or open your project** where DatapizzAI will run.
2. **Create and activate a virtual environment** (e.g., `python -m venv .venv && source .venv/bin/activate`).
3. **Install shared dependencies**: `pip install datapizzai python-dotenv`.
4. **Configure the `.env` file** with the required keys (`OPENAI_API_KEY` plus any custom-provider secrets).
5. **Place the adapters** `custom_client_external.py` and/or `custom_client_ollama.py` inside the `Client/` folder (or any module path you prefer in the project).
6. **Update your imports** to target the new adapter locations (e.g., `from Client.custom_client_external import IBMWatsonXClient`).
7. **Run the quick validation scripts** outlined in [Quick validation](#quick-validation) to confirm everything is wired correctly.

## Example A — External provider (IBM WatsonX)
### Detailed walkthrough
1. **Install the SDK**: `pip install ibm-watsonx-ai` (inside the activated virtualenv).
2. **Populate `.env`** with the IBM secrets:
   ```bash
   IBM_WATSONX_API_KEY=sk-...
   IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
   IBM_WATSONX_PROJECT_ID=your-project-id
   ```
3. **Sanity-check the environment**: run `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('IBM_WATSONX_API_KEY') is not None)"`.
4. **Open `custom_client_external.py`** and tweak defaults such as `model_id`, `temperature`, or `stop_sequences` if needed.
5. **Wire the client into your app**:
   ```python
   from Client.custom_client_external import IBMWatsonXClient

   watson_client = IBMWatsonXClient(model_id="ibm/granite-3-2-8b-instruct")
   response = watson_client.invoke("Summarise our product vision.")
   print(response.text)
   ```
6. **Add conversation memory**: pass `memory=my_memory` to `invoke` for multi-turn interactions.
7. **Inspect failures**: when `stop_reason` is `error`, print the first `content` entry to inspect the provider error message.

### Key code excerpt
```python
class IBMWatsonXClient:
    def __init__(self, model_id: str, temperature: float = 0.7) -> None:
        self.credentials = Credentials(
            url=os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=os.getenv("IBM_WATSONX_API_KEY"),
        )
        self.client = APIClient(self.credentials)
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID")
        if self.project_id:
            self.client.set.default_project(self.project_id)
        self.model = ModelInference(
            model_id=model_id,
            api_client=self.client,
            params={"max_new_tokens": 1_000, "temperature": temperature},
        )

    def _build_prompt(self, input_text: str | None, memory: Optional[Memory]) -> str:
        prompt_parts: list[str] = []
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(block.content for block in turn.blocks if getattr(block, "content", ""))
                if content:
                    prompt_parts.append(f"Human: {content}" if role.lower() == "user" else f"Assistant: {content}")
        if input_text:
            prompt_parts.append(f"Human: {input_text}")
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def invoke(self, input_text: str | None = None, memory: Optional[Memory] = None) -> ClientResponse:
        prompt = self._build_prompt(input_text, memory)
        response = self.model.generate_text(prompt=prompt)
        text = response.get("generated_text", "").strip()
        estimated_prompt_tokens = int(len(prompt.split()) * 1.3)
        estimated_completion_tokens = int(len(text.split()) * 1.3)
        return ClientResponse(
            content=[TextBlock(content=text)],
            prompt_tokens_used=estimated_prompt_tokens,
            completion_tokens_used=estimated_completion_tokens,
            stop_reason="stop",
        )
```

### Step-by-step explanation
1. **Constructor**: sets up credentials, low-level API client, default project, and a reusable `ModelInference` instance with the chosen parameters.
2. **Prompt assembly**: `_build_prompt` reshapes DatapizzAI memory into the `Human:/Assistant:` format WatsonX expects and appends the current user turn.
3. **Invocation**: `invoke` sends the prompt, normalises the output text, estimates token usage, and returns a standard `ClientResponse` object.

### Implementation highlights
- The adapter builds a `ModelInference` handle once and reuses it for efficiency.
- `_build_prompt` converts DatapizzAI memory into a `Human:/Assistant:` dialogue expected by WatsonX.
- Token usage is estimated; extend the class with real metrics if IBM adds them to the payload.

> **Reference**: review the full source in [`Client/custom_client_external.py`](custom_client_external.py).

## Example B — Local model (Ollama)
### Detailed walkthrough
1. **Install Ollama** (macOS/Linux): `curl -fsSL https://ollama.com/install.sh | sh`.
2. **Launch the daemon** in a separate terminal: `ollama serve`.
3. **Pull the desired model**: `ollama pull gemma3n:e2b` (replace the tag with what you need).
4. **Smoke-test via CLI**: `ollama run gemma3n:e2b "Hello, who are you?"`.
5. **Review `custom_client_ollama.py`** and adjust `model` or `base_url` defaults if your setup differs.
6. **Integrate the adapter**:
   ```python
   from Client.custom_client_ollama import OllamaClient

   local_client = OllamaClient(model="gemma3n:e2b")
   response = local_client.invoke("Craft a catchy slogan for our launch.")
   print(response.text)
   ```
7. **Enable conversation memory** by passing a `Memory` instance to `invoke` when you need multi-turn context.
8. **Handle network errors**: ensure the `ollama serve` process is running and that localhost traffic is allowed if you receive connection errors.

### Key code excerpt
```python
class OllamaClient:
    def __init__(self, model: str = "gemma3n:e2b", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _build_messages(self, input_text: str | None, memory: Optional[Memory]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(block.content for block in turn.blocks if getattr(block, "content", ""))
                if content:
                    messages.append({"role": role, "content": content})
        if input_text:
            messages.append({"role": "user", "content": input_text})
        return messages

    def invoke(self, input_text: str | None = None, memory: Optional[Memory] = None) -> ClientResponse:
        payload = {"model": self.model, "messages": self._build_messages(input_text, memory), "stream": False}
        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        text = data.get("message", {}).get("content", "").strip() or str(data)
        prompt_tokens = int(len(" ".join(msg["content"] for msg in payload["messages"]).split()) * 1.3)
        completion_tokens = int(len(text.split()) * 1.3)
        return ClientResponse(
            content=[TextBlock(content=text)],
            prompt_tokens_used=prompt_tokens,
            completion_tokens_used=completion_tokens,
            stop_reason="stop",
        )
```

### Step-by-step explanation
1. **Initialization**: stores the target model and base URL so you can route requests to any Ollama instance without touching the rest of the code.
2. **Message preparation**: `_build_messages` converts DatapizzAI memory into the `{role, content}` structure required by the Ollama chat endpoint and adds the latest user request.
3. **HTTP roundtrip**: `invoke` posts the payload, validates the response, extracts the generated text, estimates token usage, and returns a DatapizzAI-compatible `ClientResponse`.

### Implementation highlights
- `_build_messages` mirrors DatapizzAI memory into the JSON structure expected by Ollama's `/api/chat` endpoint.
- `_estimate_tokens` applies a 1.3× multiplier to approximate token usage when metrics are missing.
- The adapter returns a `ClientResponse`, keeping it interchangeable with built-in DatapizzAI clients.

> **Reference**: see the complete implementation in [`Client/custom_client_ollama.py`](custom_client_ollama.py).

## Quick validation
- Load the environment variables (for example with `dotenv load`) before running the scripts.
- IBM WatsonX: execute `python Client/custom_client_external.py` to print the generated answer and the estimated token usage.
- Ollama: execute `python Client/custom_client_ollama.py` to query the local model and inspect the token estimates.

## Related resources
- Overview of DatapizzAI clients: [Client/README_EV.md](README_EV.md)
- Custom provider strategy: [Method 3](README_EV.md#method-3-custom-provider-via-api-eg-ibm-watsonx)
- Local model workflow: [Method 4](README_EV.md#method-4-local-model-ollamagemma)
