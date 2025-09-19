# DatapizzAI custom clients

This guide describes how to design two complete adapters that enable DatapizzAI to work with providers not natively supported or with local models. As we'll see, it's quite intuitive to both create and call the client thanks to the `invoke` interface, which is already present in the library.

## Basic principles
- **Common interface**: every adapter must expose the `invoke(input_text, memory=None)` method and return a `ClientResponse`.
- **Memory handling**: it's necessary to transform `Memory` objects into a format the provider understands (prompt strings, message arrays, etc.).
- **Observability**: when the provider doesn't report token statistics, it's useful to provide estimates or explanatory logs.

## Example A — External provider (IBM WatsonX)
This is just an example of how to configure a client not present among the available clients. We'll see together step by step.

### Detailed procedure
1. **Install the SDK**: `pip install ibm-watsonx-ai` (within the created virtual environment).
2. **Populate the `.env`** with:
   ```bash
   IBM_WATSONX_API_KEY=sk-...
   IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
   IBM_WATSONX_PROJECT_ID=your-project-id
   ```
3. **Verify credentials** by running `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('IBM_WATSONX_API_KEY') is not None)"`.
4. **Open `custom_client_external.py`** and customize, if necessary, `model_id`, `temperature` or other settings (e.g. `stop_sequences`).
5. **Integrate the client** into your application code:
   ```python
   from Client.custom_client_external import IBMWatsonXClient

   watson_client = IBMWatsonXClient(model_id="ibm/granite-3-2-8b-instruct")
   response = watson_client.invoke("Give me a summary of the corporate vision.")
   print(response.text)
   ```
6. **Handle memory**: pass a `Memory` object to `invoke` if you want multi-turn conversations.
7. **Monitor errors**: in case of response with `stop_reason='error'`, print the `content[0].content` attribute to read the provider's raw error.

### Main code (excerpt)
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

### Step-by-step code explanation
1. **Constructor**: immediately creates IBM credentials and the `APIClient` object, then selects the working project and instantiates `ModelInference` with the main parameters.
2. **Prompt construction**: `_build_prompt` reassembles DatapizzAI memory in the `Human:/Assistant:` schema required by WatsonX and adds the current input.
3. **Invocation**: `invoke` prepares the prompt, calls `generate_text`, normalizes the response and calculates an estimate of tokens used to maintain `ClientResponse` compatibility.

### Key implementation concepts
- The adapter instantiates `ModelInference` only once and reuses it for better performance.
- The `_build_prompt` function converts DatapizzAI memory into the `Human:/Assistant:` style required by WatsonX.
- Token counting is estimated; add your own metrics if the provider supplies more precise data.

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
        
        # Configurazione credenziali IBM WatsonX
        self.credentials = Credentials(
            url=os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=os.getenv("IBM_WATSONX_API_KEY")
        )
        
        # Inizializza il client API
        self.client = APIClient(self.credentials)
        self.project_id = os.getenv("IBM_WATSONX_PROJECT_ID")
        
        # Imposta il progetto di default
        if self.project_id:
            self.client.set.default_project(self.project_id)
        
        # Inizializza il modello
        self.model = self._initialize_model()
    
    def _initialize_model(self):
        """Inizializza il modello IBM WatsonX una sola volta per ottimizzare le performance."""
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
        """Costruisce il prompt includendo la memoria della conversazione."""
        prompt_parts = []
        
        # Aggiungi contesto dalla memoria
        if memory is not None:
            for turn in memory.memory:
                role = turn.role.value if hasattr(turn.role, "value") else str(turn.role)
                content = " ".join(getattr(block, "content", "") for block in turn.blocks)
                if content:
                    if role.lower() == "user":
                        prompt_parts.append(f"Human: {content}")
                    elif role.lower() == "assistant":
                        prompt_parts.append(f"Assistant: {content}")
        
        # Aggiungi input corrente
        if input_text:
            prompt_parts.append(f"Human: {input_text}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def invoke(self, input_text: str = None, memory: Optional[Memory] = None) -> ClientResponse:
        """Invoca il modello IBM Watson e restituisce una risposta compatibile."""
        try:
            prompt = self._build_prompt(input_text, memory)
            
            # Chiamata al modello IBM Watson
            response = self.model.generate_text(prompt=prompt)
            
            # Estrai il testo della risposta
            if isinstance(response, dict):
                text = response.get("generated_text", "").strip()
                # Rimuovi il prefisso "Assistant:" se presente
                if text.startswith("Assistant:"):
                    text = text[10:].strip()
            else:
                text = str(response).strip()
            
            # Stima approssimativa dei token (IBM Watson non sempre fornisce metriche dettagliate)
            estimated_prompt_tokens = len(prompt.split()) * 1.3  # Stima approssimativa
            estimated_completion_tokens = len(text.split()) * 1.3
            
            return ClientResponse(
                content=[TextBlock(content=text)],
                prompt_tokens_used=int(estimated_prompt_tokens),
                completion_tokens_used=int(estimated_completion_tokens),
                stop_reason="stop"
            )
            
        except Exception as e:
            return ClientResponse(
                content=[TextBlock(content=f"Errore IBM Watson: {str(e)}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error"
            )


# Esempio di utilizzo
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Crea il client IBM WatsonX
    watsonx_client = IBMWatsonXClient(
        model_id="ibm/granite-3-2-8b-instruct",
        temperature=0.7
    )
    
    # Test del client
    response = watsonx_client.invoke("Ciao! Presentati brevemente.")
    print(f"Risposta: {response.text}")
    print(f"Token usati: {response.prompt_tokens_used + response.completion_tokens_used}")
    ```


## Example B — Local model (Ollama)
### Detailed procedure
1. **Install Ollama** (macOS/Linux): `curl -fsSL https://ollama.com/install.sh | sh`.
2. **Start the daemon** in a separate terminal: `ollama serve`.
3. **Download the model** of interest: `ollama pull gemma3n:e2b` (replace the tag with the one you prefer).
4. **Run a smoke test from CLI**: `ollama run gemma3n:e2b "Hello, who are you?"` to verify the local response.
5. Then you have only to define the Client.

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
        """Costruisce i messaggi per la chat API di Ollama includendo la memoria."""
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
        """Stima approssimativa del numero di token basata sul conteggio delle parole."""
        return int(len(text.split()) * 1.3)  # Fattore di conversione approssimativo

    def invoke(self, input=None, memory: Optional[Memory] = None) -> ClientResponse:
        """Invoca il modello Ollama e restituisce una risposta compatibile con DatapizzAI."""
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
            
            # Estrai il testo della risposta
            text = data.get("message", {}).get("content", "").strip()
            if not text:
                text = str(data)
            
            # Calcola stime dei token utilizzati
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
                content=[TextBlock(content=f"Errore connessione Ollama: {str(e)}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error"
            )
        except Exception as e:
            return ClientResponse(
                content=[TextBlock(content=f"Errore Ollama: {str(e)}")],
                prompt_tokens_used=0,
                completion_tokens_used=0,
                stop_reason="error"
            )


if __name__ == "__main__":
    # Test del client locale
    client = OllamaClient()
    response = client.invoke("Ciao! Riassumi in una frase il teorema di Pitagora.")
    
    print(f"Risposta: {response.text}")
    print(f"Token prompt: {response.prompt_tokens_used}")
    print(f"Token completion: {response.completion_tokens_used}")
    print(f"Stop reason: {response.stop_reason}")
```

### Step-by-step code explanation
1. **Initialization**: saves model and base URL, so you can point to different hosts or models without modifying the rest of the code.
2. **Message preparation**: `_build_messages` translates memory into a list of `{role, content}` dictionaries compatible with Ollama's chat API and adds the current prompt.
3. **HTTP call**: `invoke` sends the POST request, validates the response, extracts the generated text and estimates tokens before constructing the `ClientResponse`.
