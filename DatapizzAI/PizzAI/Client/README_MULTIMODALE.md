# Esempi Multimodali - DatapizzAI

Esempi rapidi per usare il framework **DatapizzAI** con input/output multimediali (immagini + testo).

## 1. Analisi immagine da URL

```python
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media
import os

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

media = Media(
    extension="jpg",
    media_type="image",
    source_type="url",
    source="https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"
)

response = client.invoke([
    TextBlock(content="Descrivi questa immagine in dettaglio"),
    MediaBlock(media=media)
])

print(response.text)
```

---

## 2. Analisi immagine locale

```python
import base64
from pathlib import Path
from datapizzai.type import Media

def load_image_as_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")

image_b64 = load_image_as_base64("my_image.jpg")

media = Media(
    extension="jpg",
    media_type="image",
    source_type="base64",
    source=image_b64,
    detail="high"
)

prompt = "Analizza questa immagine e dammi una descrizione tecnica."

response = client.invoke([
    TextBlock(content=prompt),
    MediaBlock(media=media)
])

print(response.text)
```

---

## 3. Generazione immagine (GPT-5 + DALL-E 3)

```python
from datapizzai.clients import ClientFactory
import openai, os, requests, time

# Step 1: migliora il prompt con GPT-5
gpt5 = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1.0
)

prompt = "Un gatto che suona il pianoforte"
final_prompt = gpt5.invoke(f"Migliora questo prompt: '{prompt}'").text.strip()

# Step 2: genera con DALL-E 3
dalle = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
res = dalle.images.generate(model="dall-e-3", prompt=final_prompt, size="1024x1024")

url = res.data[0].url
img = requests.get(url).content
filename = f"generated_{int(time.time())}.png"
open(filename, "wb").write(img)

print(f"Immagine salvata: {filename}")
```

---

## 4. Conversazione multimodale con memoria

```python
from datapizzai.memory import Memory
from datapizzai.type import ROLE, TextBlock
from datapizzai.utils import create_mediablock_from_file

client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
memory = Memory()

# Primo turno con immagine
image_block = create_mediablock_from_file("my_photo.jpg")
memory.add_turn([TextBlock("Analizza questa foto"), image_block], ROLE.USER)
resp = client.invoke("", memory=memory)
memory.add_turn([TextBlock(resp.text)], ROLE.ASSISTANT)

# Secondo turno senza immagine
memory.add_turn([TextBlock("Quali miglioramenti consiglieresti?")], ROLE.USER)
resp = client.invoke("", memory=memory)

print(resp.text)
```
