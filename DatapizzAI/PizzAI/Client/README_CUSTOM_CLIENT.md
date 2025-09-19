# Client personalizzati DatapizzAI

Questa guida descrive come progettare due adapter completi che permettono di utilizzare DatapizzAI con provider non supportati nativamente o con modelli locali. Come vedremo, è abbastanza intuitivo sia creare che chiamare il client grazie all'interfaccia `invoke`, quindi un modo d'uso già presente nella libreria.

## Principi di base
- **Interfaccia comune**: ogni adapter deve esporre il metodo `invoke(input_text, memory=None)` e restituire un `ClientResponse`.
- **Gestione della memoria**: è necessario trasformare gli oggetti `Memory` in un formato che il provider capisca (prompt stringhe, array di messaggi, ecc.).
- **Osservabilità**: quando il provider non riporta le statistiche sui token, è utile fornire stime o log esplicativi.

## Esempio A — Provider esterno (IBM WatsonX)
Questo è solo un esempio su come configurare un client non presente tra i client disponibili. Vedremo insieme step by
### Procedura dettagliata
1. **Installa il SDK**: `pip install ibm-watsonx-ai` (all'interno dell'ambiente virtuale creato).
2. **Popola il `.env`** con:
   ```bash
   IBM_WATSONX_API_KEY=sk-...
   IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
   IBM_WATSONX_PROJECT_ID=your-project-id
   ```
3. **Verifica le credenziali** eseguendo `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('IBM_WATSONX_API_KEY') is not None)"`.
4. **Apri `custom_client_external.py`** e personalizza, se necessario, `model_id`, `temperature` o altre impostazioni (es. `stop_sequences`).
5. **Integra il client** nel tuo codice applicativo:
   ```python
   from Client.custom_client_external import IBMWatsonXClient

   watson_client = IBMWatsonXClient(model_id="ibm/granite-3-2-8b-instruct")
   response = watson_client.invoke("Dammi un riassunto della vision aziendale.")
   print(response.text)
   ```
6. **Gestisci la memoria**: passa un oggetto `Memory` a `invoke` se vuoi conversazioni multi-turno.
7. **Monitora gli errori**: in caso di risposta con `stop_reason='error'`, stampa l'attributo `content[0].content` per leggere l'errore raw del provider.

### Codice principale (estratto)
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

## Esempio B — Modello locale (Ollama)
### Procedura dettagliata
1. **Installa Ollama** (macOS/Linux): `curl -fsSL https://ollama.com/install.sh | sh`.
2. **Avvia il demone** in un terminale separato: `ollama serve`.
3. **Scarica il modello** di interesse: `ollama pull gemma3n:e2b` (sostituisci il tag con quello che preferisci).
4. **Esegui un smoke test da CLI**: `ollama run gemma3n:e2b "Ciao, chi sei?"` per verificare la risposta locale.
5. Poi devi solo definire il Client.

### Codice principale (estratto)
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
