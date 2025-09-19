# Client personalizzati DatapizzAI

Questa guida descrive come progettare due adapter completi che permettono di utilizzare DatapizzAI con provider non supportati nativamente o con modelli locali. Gli esempi riutilizzano l'interfaccia `invoke` così da sfruttare l'ecosistema di agenti, memoria e strumenti già presente nella libreria.

## Principi di base
- **Interfaccia comune**: ogni adapter deve esporre il metodo `invoke(input_text, memory=None)` e restituire un `ClientResponse`.
- **Gestione della memoria**: è necessario trasformare gli oggetti `Memory` in un formato che il provider capisca (prompt stringhe, array di messaggi, ecc.).
- **Osservabilità**: quando il provider non riporta le statistiche sui token, è utile fornire stime o log esplicativi.

## Setup step-by-step
1. **Clona il repository o apri il progetto** in cui vuoi integrare DatapizzAI.
2. **Crea e attiva un ambiente virtuale** (es. `python -m venv .venv && source .venv/bin/activate`).
3. **Installa le dipendenze comuni**: `pip install datapizzai python-dotenv`.
4. **Configura il file `.env`** nella root del progetto con le chiavi necessarie (es. `OPENAI_API_KEY` oltre alle chiavi specifiche del provider custom).
5. **Copia gli adapter** `custom_client_external.py` e/o `custom_client_ollama.py` dentro la cartella `Client/` (o in una directory a tua scelta all'interno del progetto).
6. **Aggiorna l'import path** nei tuoi script (es. `from Client.custom_client_external import IBMWatsonXClient`).
7. **Esegui i test rapidi** descritti nella sezione [Verifiche rapide](#verifiche-rapide) per validare la configurazione.

## Esempio A — Provider esterno (IBM WatsonX)
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

### Spiegazione passo-passo del codice
1. **Costruttore**: crea subito le credenziali IBM e l'oggetto `APIClient`, quindi seleziona il progetto di lavoro e istanzia `ModelInference` con i parametri principali.
2. **Costruzione del prompt**: `_build_prompt` ricompone la memoria DatapizzAI nello schema `Human:/Assistant:` richiesto da WatsonX e aggiunge l'input corrente.
3. **Invocazione**: `invoke` prepara il prompt, chiama `generate_text`, normalizza la risposta e calcola una stima dei token usati per mantenere compatibile il `ClientResponse`.

### Concetti chiave dell'implementazione
- L'adapter istanzia `ModelInference` una sola volta e lo riutilizza per performance migliori.
- La funzione `_build_prompt` converte la memoria DatapizzAI nello stile `Human:/Assistant:` richiesto da WatsonX.
- Il conteggio token è stimato; aggiungi metriche proprie se il provider fornisce dati più precisi.

> **Riferimento**: vedi il file completo [`Client/custom_client_external.py`](custom_client_external.py).

## Esempio B — Modello locale (Ollama)
### Procedura dettagliata
1. **Installa Ollama** (macOS/Linux): `curl -fsSL https://ollama.com/install.sh | sh`.
2. **Avvia il demone** in un terminale separato: `ollama serve`.
3. **Scarica il modello** di interesse: `ollama pull gemma3n:e2b` (sostituisci il tag con quello che preferisci).
4. **Esegui un smoke test da CLI**: `ollama run gemma3n:e2b "Ciao, chi sei?"` per verificare la risposta locale.
5. **Personalizza l'adapter** `custom_client_ollama.py` se vuoi cambiare il modello o l'URL (`base_url`).
6. **Integra il client** nel codice:
   ```python
   from Client.custom_client_ollama import OllamaClient

   local_client = OllamaClient(model="gemma3n:e2b")
   response = local_client.invoke("Genera uno slogan creativo per il nostro prodotto.")
   print(response.text)
   ```
7. **Passa la memoria**: fornisci `memory=my_memory` per ottenere risposte contestualizzate multi-turno.
8. **Gestisci gli errori di rete**: se Ollama non risponde, controlla che il demone sia attivo e che il firewall consenta `localhost:11434`.

### Codice principale (estratto)
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

### Spiegazione passo-passo del codice
1. **Inizializzazione**: salva modello e URL base, così puoi puntare a host o modelli diversi senza modificare il resto del codice.
2. **Preparazione dei messaggi**: `_build_messages` traduce la memoria in una lista di dizionari `{role, content}` compatibile con l'API chat di Ollama e aggiunge il prompt corrente.
3. **Chiamata HTTP**: `invoke` invia la richiesta POST, valida la risposta, estrae il testo generato e stima i token prima di costruire il `ClientResponse`.

### Concetti chiave dell'implementazione
- `_build_messages` riallinea la memoria DatapizzAI al formato JSON della chat API di Ollama.
- `_estimate_tokens` usa una stima a 1.3× per mancanza di usage ufficiale.
- L'adapter restituisce sempre un `ClientResponse` coerente con gli altri client DatapizzAI.

> **Riferimento**: vedi il file completo [`Client/custom_client_ollama.py`](custom_client_ollama.py).

## Verifiche rapide
- Carica le variabili d'ambiente con `python -m dotenv.main set` o `dotenv load` prima di eseguire gli esempi.
- Per IBM WatsonX: `python Client/custom_client_external.py` stampa la risposta del modello e il conteggio stimato dei token.
- Per Ollama: `python Client/custom_client_ollama.py` invia una richiesta al modello locale e mostra le metriche stimate.

## Risorse correlate
- Panoramica generale dei client: [Client/README.md](README.md)
- Strategia per provider custom: [Metodo 3](README.md#metodo-3-provider-personalizzato-via-api-es-ibm-watsonx)
- Esempio di modello locale: [Metodo 4](README.md#metodo-4-modello-locale-ollamagemma)
