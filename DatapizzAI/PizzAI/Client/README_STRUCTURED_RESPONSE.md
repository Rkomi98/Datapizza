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
- Valida con Pydantic/JSON Schema per maggiore robustezza
- Specifica “JSON valido, senza testo extra” per ridurre testo pre/post testo.

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
- Preferisci modelli Pydantic per definire la struttura e validare l'output
- Le classi Pydantic offrono validazione automatica e type hints con poco boilerplate
- I dati sono disponibili in `response.structured_data[0]` (primo oggetto)
- Se il provider non supporta output strutturati, usa JSON + parsing (metodo 1)
- Per il debug, logga sia l'output grezzo sia quello strutturato
