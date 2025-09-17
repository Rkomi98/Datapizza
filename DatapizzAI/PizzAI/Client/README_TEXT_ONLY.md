# DatapizzAI text-only

Questa guida ti accompagna passo‑passo alla creazione di un chatbot testuale con DatapizzAI. Ogni passaggio spiega non solo cosa fare, ma anche perché farlo.

- Obiettivo: costruire un chatbot conversazionale robusto e performante
- Tecnologie: DatapizzAI (modalità text‑only)
- Risultato: un chatbot a riga di comando con memoria, gestione errori, metriche e cache opzionale

## Indice

- [Prerequisiti](#prerequisiti)
- [1. Configurazione del client](#1-configurazione-del-client)
- [2. Concetti chiave: Memory, TextBlock, ROLE](#2-concetti-chiave-memory-textblock-role)
- [3. Cache](#3-cache)
- [4. Mettere tutto insieme: chatbot completo](#4-mettere-tutto-insieme-chatbot-completo)
- [Riferimenti utili](#riferimenti-utili)

## Prerequisiti
- Python 3.10+
- Chiave API del provider (es. `OPENAI_API_KEY`)
- File `.env` nella directory del progetto con almeno:
```
OPENAI_API_KEY=sk-...
```

Per esempi completi consultare anche `text_only_examples.py`.

## 1. Configurazione del client (perché è importante)
Per parlare con un modello serve un client configurato con provider, chiave, temperatura e modello.

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock

load_dotenv()

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1
)

# Invoke sempplice (minimale)
print(client.invoke("Ciao, piacere di conoscerti").text)

# Oppure usando un modulo che vedremo tra un attimo
print(client.invoke(TextBlock(content="Ciao, piacere di conoscerti")).text)
```

- provider: scegli il vendor LLM

## 2. Concetti chiave: Memory, TextBlock, ROLE (perché servono)
Per costruire conversazioni, DatapizzAI usa:
- `Memory`: contiene la cronologia dei turni (utente/assistente)
- `TextBlock`: rappresenta blocchi di testo scambiati nei turni
- `ROLE`: indica chi parla (`ROLE.USER` o `ROLE.ASSISTANT`)

Questi oggetti permettono al modello di “ricordare” il contesto. Nei `TextBlock(content=...)` passa sempre stringhe; usa `response.text` per aggiungere la risposta del modello.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

# Aggiunta di un turno utente
memory.add_turn([TextBlock(content="Ciao, sono Mirko")], ROLE.USER)

# Invocazione con contesto
response = client.invoke("Ciao, sono Mirko", memory=memory)
# Salvataggio risposta (usa SEMPRE una stringa)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```
Nota: la risposta è un oggetto. Per salvarla in memoria devi usare `response.text` (stringa). Non passare l'oggetto risposta direttamente nei `TextBlock`, altrimenti otterrai errori di serializzazione JSON.

## 3. Cache
La cache riduce costi e latenza per richieste ripetute.

Come funziona: se invii due richieste identiche allo stesso client con la cache attiva, la seconda è servita dalla cache (cache hit). In questo caso il provider non viene chiamato e la risposta è restituita immediatamente.

Dettagli di implementazione: la cache è gestita dalla libreria `datapizzai` (non dal provider). La chiave di cache è calcolata da un hash del contenuto della richiesta (prompt, parametri e memoria se presente). Puoi usare `MemoryCache` (in‑process) oppure `RedisCache` per ambienti distribuiti.

```python
from datapizzai.cache import MemoryCache
import time

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1,
    cache=MemoryCache(),  # cache in-memory gestita da datapizzai
)

# Stessa richiesta 2 volte: la seconda dovrebbe colpire la cache
q = "Dimmi 3 vantaggi del TDD in 1 riga"

t0 = time.perf_counter()
r1 = client.invoke(q)
t1 = time.perf_counter()
print("prima:", r1.text)
print(f"⏱️ tempo (prima): {t1 - t0:.3f}s")
#⏱️ tempo (prima): 6.340s

t2 = time.perf_counter()
r2 = client.invoke(q)  # Qui avviene un cache hit, il client non viene invocato
t3 = time.perf_counter()
print("seconda:", r2.text)
print(f"⏱️ tempo (seconda): {t3 - t2:.3f}s")
#⏱️ tempo (seconda): 0.000s

# Alternativa: usare Redis come cache condivisa
from datapizzai.cache import RedisCache
redis_cache = RedisCache(host="localhost", port=6379, db=0)
client_redis = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    cache=redis_cache,
)

```

## 4. Mettere tutto insieme: chatbot completo
Qui un esempio riassuntivo che unisce tutto quello visto oggi con un esempio di chatbot.

```python
import os
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

class Chatbot:
    def __init__(self, client):
        self.client = client
        self.memory = Memory()

    def send(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        response = self.client.invoke(user_input, memory=self.memory)
        self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        # Stampa metriche minime (opzionale)
        total_tokens = (response.prompt_tokens_used or 0) + (response.completion_tokens_used or 0)
        print(f"[metriche] token totali: {total_tokens}")
        return response.text

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1,
)

bot = Chatbot(client)
print("Chat pronta. Digita 'esci' per terminare.")
while True:
    try:
        user = input("tu> ").strip()
        if user.lower() in {"esci", "exit", "quit"}:
            break
        print("bot>", bot.send(user))
    except KeyboardInterrupt:
        break
    except Exception:
        print("bot> Si è verificato un errore temporaneo. Riprova.")
```

 

## Riferimenti utili
- `text_only_examples.py`: esempi completi e scenari avanzati.
