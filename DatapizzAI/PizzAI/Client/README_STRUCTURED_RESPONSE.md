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
    temperature=1,
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

Quando il provider lo supporta, puoi definire classi Pydantic e ottenere un output già strutturato e validato.

```python
import os
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory

# Definizione delle classi Pydantic per la struttura dati
class Task(BaseModel):
    name: str
    owner: str
    eta_days: int

class ProjectSummary(BaseModel):
    title: str
    status: str  # planned, in_progress, done
    tasks: List[Task]

load_dotenv()
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)

# Uso del metodo structured_response con classe Pydantic
response = client.structured_response(
    input="Riepiloga il piano progetto per il nuovo portale e-commerce",
    output_cls=ProjectSummary,
)

# Il risultato è disponibile come response.structured_data[0] 
structured = response.structured_data[0]
print("Titolo:", structured.title)
print("Status:", structured.status)
print("Tasks:")
for task in structured.tasks:
    print(f"  - {task.name} (owner: {task.owner}, ETA: {task.eta_days} giorni)")
```

Note pratiche:
- Usa classi Pydantic per definire la struttura dati invece di JSON Schema
- Le classi Pydantic forniscono validazione automatica e type hints
- Il risultato è disponibile in `response.structured_data[0]` (primo oggetto strutturato)
- In caso di provider non compatibile, usa l'approccio JSON + parsing del metodo 1
- Logga sia l'output grezzo sia quello strutturato per debug
