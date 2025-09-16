# Esempi Multimodali - DatapizzAI

Esempi rapidi per usare il framework **DatapizzAI** con input/output multimediali (immagini + testo).

## Indice

- [1. Analisi immagine da URL](#1-analisi-immagine-da-url)
- [2. Analisi immagine locale](#2-analisi-immagine-locale)
- [3. Analisi audio locale](#3-analisi-audio-locale)
- [4. Conversazione multimodale con memoria](#4-conversazione-multimodale-con-memoria)

## 1. Analisi immagine da URL

**Quando usare**: Analisi di immagini pubbliche, test rapidi, demo senza file locali

**Cosa fa**: Il `MediaBlock` incapsula l'immagine (URL, base64 o file) e la combina con il testo per creare input multimodale. L'AI analizza sia il prompt testuale che il contenuto visivo.

```python
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media
from dotenv import load_dotenv
import os

load_dotenv('../.env')
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Analizza immagine da URL
media = Media(
    extension="jpg",        # Estensione senza punto per MIME type corretto
    media_type="image",     # Tipo di media (image, audio, video)
    source_type="url",      # Fonte: url, base64, o file
    source="https://assets.science.nasa.gov/dynamicimage/assets/science/psd/mars/internal_resources/1155.jpeg?w=1767&h=350&fit=clip&crop=faces%2Cfocalpoint",
    detail="high"           # Livello di dettaglio (low|high|auto, se supportato)
)

# Combina testo e immagine per input multimodale
response = client.invoke([
    TextBlock(content="Descrivi questa immagine in dettaglio"),
    MediaBlock(media=media)  # Wrapper che contiene l'immagine
])

print(response.text)
```

---

## 2. Analisi immagine locale

**Quando usare**: Analisi di foto personali, documenti privati, immagini non pubbliche

**Cosa fa**: Converte l'immagine locale in base64 per l'invio sicuro via API. Il `MediaBlock` gestisce la codifica e trasmissione del file.

```python
import base64
from pathlib import Path
from datapizzai.type import Media, MediaBlock, TextBlock

def load_image_as_base64(path: str) -> str:
    """Converte file immagine in stringa base64 per trasmissione sicura"""
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")

# Carica immagine locale e converti in base64
image_b64 = load_image_as_base64("Example.png")

# Crea oggetto Media con metadati dell'immagine
media = Media(
    extension="jpg",        # Estensione file per MIME type
    media_type="image",     # Tipo di contenuto
    source_type="base64",   # Formato di trasmissione
    source=image_b64,       # Dati immagine codificati
    detail="high"           # Qualità analisi (high per dettagli)
)

# Prompt specifico per analisi tecnica
prompt = "Analizza questa immagine e dammi una descrizione tecnica."

# Invoca AI con input multimodale (testo + immagine)
response = client.invoke([
    TextBlock(content=prompt),
    MediaBlock(media=media)  # Wrapper per l'immagine
])

print(response.text)
```

---

## 3. Analisi audio locale

**Quando usare**: Trascrizione di registrazioni, analisi di contenuti audio, conversazioni vocali

**Cosa fa**: Converte l'audio locale in base64 per l'invio sicuro via API. Il `MediaBlock` gestisce la codifica e trasmissione del file audio. L'AI può trascrivere, analizzare o rispondere al contenuto audio.

```python
from pathlib import Path
from datapizzai.type import Media, MediaBlock, TextBlock

analysis_client_google = client = ClientFactory.create(
            model="gemini-2.5-flash",
            api_key=GOOGLE_API_KEY,
            system_prompt="Sei un assistente AI esperto nell'analisi di audio. Rispondi in italiano.",
            temperature=0.5
        )

media = Media(
    extension="wav",
    media_type="audio",
    source_type="path",
    source="TI0TpOD_.wav"        # <— percorso al file
)

prompt = "Trascrivi questo audio e riassumi il contenuto principale."
response = analysis_client_google.invoke([TextBlock(content=prompt), MediaBlock(media=media)])
print(response.text)
```

---

## 4. Conversazione multimodale con memoria

**Quando usare**: Analisi progressive di immagini, tutoring visivo, sviluppo iterativo di progetti creativi

**Cosa fa**: Mantiene il contesto visivo e testuale tra i turni di conversazione. L'AI ricorda l'immagine analizzata e può fare riferimento ad essa nei turni successivi senza che l'utente la reinvii.

```python
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import ROLE, TextBlock, Media, MediaBlock

load_dotenv('../.env')

def create_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea un MediaBlock da un file immagine locale (base64)."""
    data = Path(file_path).read_bytes()
    image_b64 = base64.b64encode(data).decode('utf-8')
    ext = Path(file_path).suffix.lstrip('.').lower() or 'png'
    media = Media(
        extension=ext,
        media_type="image",
        source_type="base64",
        source=image_b64,
        detail="high",
    )
    return MediaBlock(media=media)

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
)
memory = Memory()

# Primo turno: utente invia immagine con richiesta
image_block = create_mediablock_from_file("Example.png")
memory.add_turn([TextBlock("Analizza questa foto, cosa vedi?"), image_block], ROLE.USER)
resp = client.invoke("", memory=memory)
memory.add_turn([TextBlock(resp.text)], ROLE.ASSISTANT) #Aggiungo risposta alla memori

# Secondo turno: follow-up che si basa sull'immagine precedente
resp = client.invoke("Quali miglioramenti consiglieresti", memory=memory)
print(resp.text)
```
