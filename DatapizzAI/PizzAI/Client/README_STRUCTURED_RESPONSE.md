# Guida: Risposte strutturate (JSON e structured_response)

Questa guida mostra due modi per ottenere risposte strutturate dai modelli con DatapizzAI:
- Prompting per JSON “puro” e parsing lato client
- Uso di `structured_response` per far restituire al modello un output tipizzato

## 1) JSON via prompting + parsing

```python
import os, json
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory

load_dotenv()
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
)

prompt = (
    "Fornisci un riepilogo progetto come JSON valido, senza testo extra.\n"
    "Schema: {\n"
    "  \"title\": string,\n"
    "  \"status\": one of [planned, in_progress, done],\n"
    "  \"tasks\": array of {\n"
    "    \"name\": string, \"owner\": string, \"eta_days\": integer\n"
    "  }\n"
    "}"
)

resp = client.invoke(prompt)
raw = resp.text

# Parsing lato client
data = json.loads(raw)
print("Titolo:", data["title"])  # es.: "Migrazione a microservizi"
```

Suggerimenti:
- Valida lo schema (pydantic/jsonschema) per robustezza
- Chiedi sempre “JSON valido, senza testo extra” per minimizzare pre/post‑testo

## 2) Output tipizzato con structured_response

Quando il provider lo supporta, puoi definire uno schema e ottenere un output già strutturato.

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory

load_dotenv()
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
)

schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "status": {"type": "string", "enum": ["planned", "in_progress", "done"]},
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "owner": {"type": "string"},
                    "eta_days": {"type": "integer"}
                },
                "required": ["name", "owner", "eta_days"]
            }
        }
    },
    "required": ["title", "status", "tasks"]
}

response = client.invoke(
    input="Riepiloga il piano progetto per il nuovo portale e-commerce",
    structured_response=schema,
)

# A seconda del provider/SDK, il risultato può essere disponibile come
# response.structured_response oppure response.content (tipizzato) oppure response.parsed
structured = getattr(response, "structured_response", None) or getattr(response, "parsed", None)
print(structured)
```

Note pratiche:
- Mantieni lo schema conciso; enum/constraint aiutano la qualità
- In caso di fallback provider non compatibile, usa l’approccio JSON + parsing
- Logga sia l’output grezzo sia quello strutturato per debug
