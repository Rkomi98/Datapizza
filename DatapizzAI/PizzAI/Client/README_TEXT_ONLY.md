# DatapizzAI text-only

Questa guida ti accompagna passo‑passo alla creazione di un chatbot testuale con DatapizzAI. Ogni passaggio spiega non solo cosa fare, ma anche perché farlo.

- Obiettivo: costruire un chatbot conversazionale robusto e performante
- Tecnologie: DatapizzAI (modalità text‑only), provider LLM (es. OpenAI)
- Risultato: un chatbot a riga di comando con memoria, sliding window, gestione errori, metriche e cache opzionale

## Prerequisiti
- Python 3.10+
- Chiave API del provider (es. `OPENAI_API_KEY`)
- File `.env` nella directory del progetto con almeno:
```
OPENAI_API_KEY=sk-...
```

Per esempi completi consultare anche `text_only_examples.py` e la guida tecnica `GUIDA_TEXT_ONLY.md`.

## 1. Configurazione del client (perché è importante)
Per parlare con un modello serve un client configurato con provider, chiave e modello. Qui definisci anche lo “stile” dell’assistente (system prompt) e la creatività (temperature).

```python
import os
from datapizzai.clients import ClientFactory

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt=(
        "Sei un assistente utile e conciso. "
        "Rispondi in italiano, usa elenchi puntati quando opportuno."
    ),
    temperature=0.7,
)
```

- provider: scegli il vendor LLM (OpenAI, Anthropic, Google, ...)
- system_prompt: imposta il comportamento predefinito del bot
- temperature: controlla la variabilità delle risposte

## 2. Concetti chiave: Memory, TextBlock, ROLE (perché servono)
Per costruire conversazioni, DatapizzAI usa:
- `Memory`: contiene la cronologia dei turni (utente/assistente)
- `TextBlock`: rappresenta blocchi di testo scambiati nei turni
- `ROLE`: indica chi parla (`ROLE.USER` o `ROLE.ASSISTANT`)

Questi oggetti permettono al modello di “ricordare” il contesto.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

# Aggiunta di un turno utente
memory.add_turn([TextBlock(content="Ciao, sono Marco")], ROLE.USER)

# Invocazione con contesto
response = client.invoke("", memory=memory)
# Salvataggio risposta
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

## 3. Minimo funzionante: una funzione `chat_turn`
Partiamo da una funzione semplice che gestisce un turno di chat. Serve per validare che la pipeline funzioni.

```python
def chat_turn(user_input: str) -> str:
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    return response.text

print(chat_turn("Presentati in una frase."))
print(chat_turn("Ora dimmi 3 best practice per Django."))
```

Perché: separare il “cosa” (testo utente) dal “come” (gestione memoria/invocazione) rende il codice estendibile.

## 4. Da funzione a chatbot: classe con sliding window
La memoria cresce ad ogni turno. Per evitare costi e limiti token, usiamo una strategia a “finestra scorrevole” (sliding window) mantenendo solo gli ultimi N turni rilevanti.

```python
from typing import Optional

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
        return response.text
```

Perché: controllare la dimensione della memoria preserva contesto recente e riduce costi/latency.

## 5. Esecuzione interattiva (REPL) minimale
Un loop a riga di comando consente di testare il chatbot con input reali.

```python
bot = Chatbot(client, window_size=6)
print("Scrivi 'esci' o 'exit' per terminare.")

while True:
    try:
        user = input("tu> ").strip()
        if user.lower() in {"esci", "exit", "quit"}:
            break
        answer = bot.send(user)
        print(f"bot> {answer}")
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"errore> {e}")
```

Perché: validi funzionalmente il flusso end‑to‑end prima di aggiungere complessità.

## 6. Migliorare lo stile delle risposte
Lo stile si controlla dal `system_prompt` e, all’occorrenza, da istruzioni nel prompt utente. Usa formattazione e struttura per chiarezza.

```python
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt=(
        "Sei un assistente per consulenza tecnica. "
        "Sempre in italiano, risposte strutturate in massimo 5 punti, "
        "concludi con un breve 'prossimi passi'."
    ),
    temperature=0.5,
)
```

Perché: allinei lo stile del bot alle esigenze del dominio (es. supporto, consulenza, brainstorming).

## 7. Gestione errori e robustezza
Rendi la conversazione resiliente a errori di rete/configurazione.

```python
def safe_send(bot: Chatbot, user_input: str) -> str:
    try:
        return bot.send(user_input)
    except Exception as e:
        # Fallback controllato
        return "Si è verificato un errore temporaneo. Riprova tra poco."
```

Perché: l’esperienza utente è centrale; un fallback evita interruzioni brusche.

## 8. Prestazioni: cache e metriche
La cache riduce costi per richieste ripetute. Le metriche aiutano a capire l’impatto delle scelte di prompting/memoria.

```python
from datapizzai.cache import MemoryCache

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=MemoryCache(),  # supportato solo da OpenAI nel costruttore
)

# Esempio di ispezione metrica
reply = client.invoke("Dammi 3 consigli per testare un'API REST")
print("token prompt:", reply.prompt_tokens_used)
print("token risposta:", reply.completion_tokens_used)
print("stop reason:", reply.stop_reason)
```

Perché: la misurazione consente ottimizzazioni guidate dai dati (latency/costi/qualità).

## 9. Mettere tutto insieme: chatbot completo
Qui un esempio riassuntivo che unisce configurazione, classe, REPL e metriche base.

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
    model="gpt-4o",
    system_prompt=(
        "Sei un assistente utile e conciso. Rispondi in italiano "
        "e proponi sempre un breve elenco di prossimi passi."
    ),
    temperature=0.6,
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

## 10. Estensioni consigliate
- Persistenza: salva la memoria su database o file tra le sessioni
- Strutture dati: chiedi risposte in JSON per integrare facilmente con servizi esterni
- Valutazione: definisci prompt di benchmark e confronta qualità/latency/costi
- Deployment: incapsula il chatbot in un’API (es. FastAPI) o in un’app web
- Sicurezza: filtri di input, rate limiting, controllo lunghezze

## Riferimenti utili
- `text_only_examples.py`: esempi completi e scenari avanzati
- `GUIDA_TEXT_ONLY.md`: guida tecnica con best practice e troubleshooting

---

## Appendice: modalità disponibili (one‑shot vs conversational)

### One-shot (query singola)
Quando usare: domande isolate, traduzioni, calcoli, analisi indipendenti.

```python
from datapizzai.clients import ClientFactory
import os

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)

response = client.invoke("Spiega il machine learning in 2 frasi")
print(response.text)
```

### Conversational (multi‑turno con memoria)
Quando usare: tutoring, consulenza, debugging assistito, brainstorming strutturato.

```python
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

memory = Memory()

def chat_turn(user_input: str) -> str:
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    return response.text

print(chat_turn("Ciao, sono Marco, sviluppatore Python"))
print(chat_turn("Quali sono le best practice per Django?"))
print(chat_turn("E per il mio caso specifico?"))
```