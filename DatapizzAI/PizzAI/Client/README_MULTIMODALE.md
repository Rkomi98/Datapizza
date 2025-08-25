# Esempi Multimodali - DatapizzAI

Esempi rapidi per usare il framework **DatapizzAI** con input/output multimediali (immagini + testo).

## 1. Analisi immagine da URL

**Quando usare**: Analisi di immagini pubbliche, test rapidi, demo senza file locali

**Cosa fa**: Il `MediaBlock` incapsula l'immagine (URL, base64 o file) e la combina con il testo per creare input multimodale. L'AI analizza sia il prompt testuale che il contenuto visivo.

```python
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media
import os

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
    source="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
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
image_b64 = load_image_as_base64("my_image.jpg")

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
```

---

## 4. Conversazione multimodale con memoria

**Quando usare**: Analisi progressive di immagini, tutoring visivo, sviluppo iterativo di progetti creativi

**Cosa fa**: Mantiene il contesto visivo e testuale tra i turni di conversazione. L'AI ricorda l'immagine analizzata e può fare riferimento ad essa nei turni successivi senza che l'utente la reinvii.

```python
from datapizzai.memory import Memory
from datapizzai.type import ROLE, TextBlock
from datapizzai.utils import create_mediablock_from_file

client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
memory = Memory()

# Primo turno: utente invia immagine con richiesta
image_block = create_mediablock_from_file("my_photo.jpg")
memory.add_turn([TextBlock("Analizza questa foto"), image_block], ROLE.USER)
resp = client.invoke("", memory=memory)
memory.add_turn([TextBlock(resp.text)], ROLE.ASSISTANT)

# Secondo turno: follow-up che si basa sull'immagine precedente
memory.add_turn([TextBlock("Quali miglioramenti consiglieresti?")], ROLE.USER)
resp = client.invoke("", memory=memory)

print(resp.text)
```
