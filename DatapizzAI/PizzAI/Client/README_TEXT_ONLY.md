# DatapizzAI text-only

Questa guida ti accompagna passo‑passo alla creazione di un chatbot testuale con DatapizzAI. Ogni passaggio spiega non solo cosa fare, ma anche perché farlo.

- Obiettivo: costruire un chatbot conversazionale robusto e performante
- Tecnologie: DatapizzAI (modalità text‑only)
- Risultato: un chatbot a riga di comando con memoria, gestione errori, metriche e cache opzionale

## Indice

- [Prerequisiti](#prerequisiti)
- [1. Configurazione del client](#1-configurazione-del-client)
- [2. Concetti chiave: Memory, TextBlock, ROLE](#2-concetti-chiave-memory-textblock-role)
- [3. Prestazioni: cache e metriche](#3-prestazioni-cache-e-metriche)
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

# Carica variabili da .env (root progetto)
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
response = client.invoke("", memory=memory)
# Salvataggio risposta (usa SEMPRE una stringa)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```
Nota: la risposta è un oggetto. Per salvarla in memoria devi usare `response.text` (stringa). Non passare l'oggetto risposta direttamente nei `TextBlock`, altrimenti otterrai errori di serializzazione JSON.

## 3. Prestazioni: cache e metriche
La cache riduce costi per richieste ripetute. Le metriche aiutano a capire l’impatto delle scelte di prompting/memoria.

Nota importante sulla cache: la cache è implementata dalla libreria `datapizzai` (non dal provider). Puoi usare `MemoryCache` (in‑process) oppure `RedisCache` per ambienti distribuiti. La logica di cache si basa su un hash del contenuto della richiesta.

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

### Nota: strategia sliding window (perché c’è nella classe)
La funzione privata `_apply_sliding_window` è una semplice policy per limitare la memoria ai soli ultimi `N` turni, mantenendo bassi i token e i costi. È una delle tante policy possibili (vedi anche esempio di riassunto periodico più sotto).

## 4. Mettere tutto insieme: chatbot completo
Qui un esempio riassuntivo che unisce tutto quello visto oggi con un esempio di chatbot.

```python
import os
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

class Chatbot:
    def __init__(self, client, window_size: int = 6):
        self.client = client
        self.memory = Memory()
        self.window_size = window_size

    def _apply_sliding_window(self):
        if len(self.memory.memory) > self.window_size:
            self.memory.memory = self.memory.memory[-self.window_size:]

    def send(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        self._apply_sliding_window()
        response = self.client.invoke("", memory=self.memory)
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

bot = Chatbot(client, window_size=6)
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

## 5. Custom memoria: riassunto ogni 5 turni
Ecco un esempio di come implementare una policy che ogni 5 turni crea un riassunto della conversazione e “riparte” da lì. Questo riduce il contesto mantenendo però i punti chiave.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

class SummarizingChat:
    def __init__(self, client, summarize_every: int = 5, max_summary_len: int = 6):
        self.client = client
        self.memory = Memory()
        self.turns = 0
        self.summarize_every = summarize_every
        self.max_summary_len = max_summary_len

    def _summarize(self):
        # Chiede al modello un riassunto della conversazione corrente
        prompt = (
            f"Riassumi la conversazione in {self.max_summary_len} frasi, "
            "mettendo in evidenza decisioni e TODO."
        )
        summary_resp = self.client.invoke(prompt, memory=self.memory)
        summary = summary_resp.text.strip()
        # Resetta la memoria mantenendo solo il riassunto come punto di partenza
        new_mem = Memory()
        new_mem.add_turn([TextBlock(content=f"[Riassunto] {summary}")], ROLE.ASSISTANT)
        self.memory = new_mem

    def send(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        resp = self.client.invoke("", memory=self.memory)
        self.memory.add_turn([TextBlock(content=resp.text)], ROLE.ASSISTANT)
        self.turns += 1
        if self.turns % self.summarize_every == 0:
            self._summarize()
        return resp.text

# Uso:
# chat = SummarizingChat(client, summarize_every=5)
# print(chat.send("Iniziamo a progettare una REST API per un e‑commerce."))
```

Punti d’estensione consigliati (facili da implementare):
- Pre‑processing input (es. riscrittura prompt, filtri di sicurezza)
- Post‑processing output (es. normalizzazione formato, estrazione bullet/JSON)
- Policy memoria (sliding window, riassunti, pin di messaggi)
- Scelta provider dinamica (fallback se un provider è lento o in errore)
- Cache strategy (in‑process vs Redis)

## Riferimenti utili
- `text_only_examples.py`: esempi completi e scenari avanzati.
