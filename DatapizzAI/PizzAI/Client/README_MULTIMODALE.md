# DatapizzAI multimodale

Guida completa per l'utilizzo delle funzionalità multimodali del framework datapizzai, con focus su analisi e generazione di immagini.

## Avvio rapido

```bash
# Attiva ambiente virtuale
cd PizzAI && source .venv/bin/activate

# Configura API keys nel file .env
echo 'OPENAI_API_KEY=your-key-here' > .env
echo 'GOOGLE_API_KEY=your-key-here' >> .env

# Esegui gli esempi
cd Client && python multimodal_examples.py
```

## Funzionalità principali

| Funzione | Descrizione | Provider supportati |
|----------|-------------|-------------------|
| **Analisi immagini** | Analizza immagini locali o da URL con AI | OpenAI (gpt-4o), Google (gemini-2.5-flash) |
| **Generazione immagini** | GPT-5 per augmentazione + DALL-E 3 per generazione | OpenAI (GPT-5 + DALL-E 3) |
| **Conversazione multimodale** | Chat multi-turno con memoria e media | OpenAI (gpt-4o) |
| **Gestione file** | Esplorazione e batch processing di immagini locali | Locale |

## Analisi di immagini

### Esempio base - Analisi da URL

```python
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media
import os

# Setup client OpenAI
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Analizza immagine da URL
media = Media(
    extension="jpg",  # Senza punto per MIME type corretto
    media_type="image",
    source_type="url",
    source="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
)

response = client.invoke([
    TextBlock(content="Descrivi questa immagine in dettaglio"),
    MediaBlock(media=media)
])

print(response.text)
```

### Esempio avanzato - Analisi da file locale

```python
import base64
from pathlib import Path

# Carica immagine locale
def load_image_as_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Crea MediaBlock da file locale
image_b64 = load_image_as_base64("my_image.jpg")
file_ext = Path("my_image.jpg").suffix.lstrip('.')

media = Media(
    extension=file_ext,
    media_type="image",
    source_type="base64",
    source=image_b64,
    detail="high"
)

# Analisi con prompt specifico
analysis_prompt = """
Analizza questa immagine seguendo questi criteri:
1. Descrivi gli elementi visivi principali
2. Identifica i colori dominanti
3. Suggerisci possibili usi o contesti
4. Fornisci una valutazione tecnica
"""

response = client.invoke([
    TextBlock(content=analysis_prompt),
    MediaBlock(media=media)
])
```

## Generazione di immagini

### Flusso completo: GPT-5 + DALL-E 3

```python
import openai
import requests
import os

# 1. Augmentazione prompt con GPT-5
gpt5_client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1.0  # GPT-5 supporta solo temperature=1.0
)

augment_prompt = f"""Migliora questo prompt per generazione immagini AI: "un gatto che suona il pianoforte"

Aggiungi dettagli su:
- Stile visivo e colori specifici
- Composizione e prospettiva
- Elementi decorativi e atmosfera
- Qualità artistica e tecnica fotografica

Rispondi solo con il prompt migliorato, max 400 caratteri."""

augmented = gpt5_client.invoke(augment_prompt)
final_prompt = augmented.text.strip()

# 2. Generazione immagine con DALL-E 3
dalle_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = dalle_client.images.generate(
    model="dall-e-3",
    prompt=final_prompt,
    size="1024x1024",
    quality="standard",  # o "hd" per qualità superiore
    n=1
)

# 3. Download automatico
image_url = response.data[0].url
img_data = requests.get(image_url).content

filename = f"generated_image_{int(time.time())}.png"
with open(filename, "wb") as f:
    f.write(img_data)

print(f"✅ Immagine salvata: {filename}")
```

## Conversazione multimodale

### Chat con memoria e media

```python
from datapizzai.memory import Memory
from datapizzai.type import ROLE

# Inizializza client e memoria
client = create_multimodal_client("openai", use_cache=True)
memory = Memory()

# Turno 1: Utente invia immagine con richiesta
image_block = create_mediablock_from_file("my_photo.jpg")
input_blocks = [
    TextBlock(content="Analizza questa foto e dimmi cosa vedi"),
    image_block
]

memory.add_turn(input_blocks, ROLE.USER)
response = client.invoke("", memory=memory)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)

# Turno 2: Follow-up senza reinviare l'immagine
follow_up = TextBlock(content="Quali miglioramenti consiglieresti?")
memory.add_turn([follow_up], ROLE.USER)

# L'AI ricorda l'immagine precedente
response = client.invoke("", memory=memory)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

### Gestione avanzata della memoria

```python
# Analizza il contenuto della memoria
text_count = 0
media_count = 0

for block in memory.iter_blocks():
    if isinstance(block, TextBlock):
        text_count += 1
    elif isinstance(block, MediaBlock):
        media_count += 1

print(f"Blocchi testo: {text_count}")
print(f"Blocchi media: {media_count}")

# Gestione memoria con limite dimensione
# In un caso reale, potresti voler rimuovere i media più vecchi
# mantenendo solo il testo per ridurre il carico
```

## Gestione file multimediali

### Ricerca e batch processing

```python
from pathlib import Path

def find_local_images() -> List[str]:
    """Trova tutte le immagini nella directory corrente"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    current_dir = Path('.')
    
    found_images = []
    for ext in image_extensions:
        found_images.extend(current_dir.glob(f'*{ext}'))
        found_images.extend(current_dir.glob(f'*{ext.upper()}'))
    
    return [str(img) for img in found_images]

def create_media_batch(image_paths: List[str], max_images: int = 3) -> List[MediaBlock]:
    """Crea un batch di MediaBlock da file locali"""
    media_blocks = []
    
    for i, path in enumerate(image_paths[:max_images]):
        image_b64 = load_image_as_base64(path)
        if image_b64:
            media = Media(
                media_type="image", 
                source_type="base64",
                source=image_b64,
                detail="high"
            )
            media_blocks.append(MediaBlock(media=media))
    
    return media_blocks

# Utilizzo
local_images = find_local_images()
batch = create_media_batch(local_images, max_images=5)
```

## Configurazione

### File .env richiesto

```bash
# Directory: PizzAI/.env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-key-here
```

### Provider e modelli supportati

| Provider | Modello | Analisi immagini | Augmentazione prompt | Generazione immagini | Cache |
|----------|---------|-----------------|-------------------|-------------------|-------|
| OpenAI | gpt-4o | ✅ | ❌ | ❌ | ✅ |
| OpenAI | gpt-5 | ❌ | ✅ | ❌ | ❌ |
| OpenAI | dall-e-3 | ❌ | ❌ | ✅ | ❌ |
| Google | gemini-2.5-flash | ✅ | ❌ | ❌ | ❌ |

### Variabili d'ambiente opzionali

```bash
# Modelli personalizzati (se diversi dai default)
OPENAI_VISION_MODEL=gpt-4o
GOOGLE_VISION_MODEL=gemini-2.5-flash
```

## Menu interattivo

```
DATAPIZZAI - Analisi e generazione immagini
=================================================================

File disponibili nella directory:
   Immagini: X file

Da cosa vuoi partire?

1. Analizza immagine → Carica e analizza un'immagine
2. Genera immagine → GPT-5 + DALL-E 3 (download locale)
3. Conversazione multimodale → Analisi con memoria
4. Gestione file → Esplora immagini locali

0. Esci
```

## Formati supportati

### Immagini input
- **Estensioni**: .jpg, .jpeg, .png, .gif, .bmp, .webp
- **Dimensione massima**: 20MB
- **Sorgenti**: File locali, URL web, base64
- **Qualità**: "high" per analisi dettagliata

### Immagini output
- **Formato**: PNG (raster)
- **Risoluzione**: 1024x1024, 1792x1024, 1024x1792
- **Qualità**: standard, HD
- **Download**: automatico in locale con timestamp

## Risoluzione problemi comuni

### Error: "Unsupported MIME type"

```python
# ❌ Problema: extension con punto
media = Media(extension=".jpg", media_type="image", source=data)

# ✅ Soluzione: extension senza punto per MIME type corretto
media = Media(extension="jpg", media_type="image", source=data)
```

### Error: "API key not found"

```bash
# Verifica file .env
ls -la PizzAI/.env

# Crea se mancante
echo 'OPENAI_API_KEY=your-key' > PizzAI/.env
```

### Error: "temperature does not support 0.7 with this model"

```python
# ❌ Problema: GPT-5 supporta solo temperature=1.0
client = ClientFactory.create(model="gpt-5", temperature=0.7)

# ✅ Soluzione: usa temperature=1.0 per GPT-5
client = ClientFactory.create(model="gpt-5", temperature=1.0)
```

### Error: "Modulo 'requests' non installato"

```bash
# Installa requests per download immagini
pip install requests
```

### Error: "Modulo 'openai' non installato"

```bash
# Installa openai per DALL-E 3
pip install openai
```

## Esempi avanzati

### Analisi comparativa tra immagini

```python
# Carica due immagini per confronto
image1 = create_mediablock_from_file("photo1.jpg")
image2 = create_mediablock_from_file("photo2.jpg")

comparison_input = [
    TextBlock(content="Confronta queste due immagini e dimmi le principali differenze:"),
    image1,
    TextBlock(content="Prima immagine ↑"),
    image2, 
    TextBlock(content="Seconda immagine ↑"),
    TextBlock(content="Fornisci un confronto dettagliato.")
]

response = client.invoke(input=comparison_input)
```

### Workflow creativo progressivo

```python
# Scenario: sviluppo progetto creativo con riferimenti visivi
memory = Memory()

# Step 1: Introduzione
memory.add_turn([TextBlock(content="Sto lavorando su un nuovo progetto di design")], ROLE.USER)

# Step 2: Riferimento visivo
image_block = create_mediablock_from_file("inspiration.jpg")
memory.add_turn([
    TextBlock(content="Ecco la mia prima ispirazione. Che direzione creativa suggerisci?"),
    image_block
], ROLE.USER)

# Step 3: Sviluppo idea
response = client.invoke("", memory=memory)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)

# Step 4: Richiesta specifica
memory.add_turn([TextBlock(content="Voglio creare qualcosa di moderno ma elegante")], ROLE.USER)
```

## Note sui costi

- **OpenAI GPT-4o**: ~$0.01 per immagine analizzata
- **OpenAI GPT-5**: ~$0.02 per augmentazione prompt
- **OpenAI DALL-E 3**: ~$0.04 per immagine generata (standard), ~$0.08 (HD)
- **Google Gemini**: Tariffe competitive per analisi immagini

Consultare la documentazione ufficiale dei provider per tariffe aggiornate.

## Testing e sviluppo

### Test rapido con immagine di esempio

```python
def create_sample_image_base64() -> str:
    """Crea un'immagine di esempio in base64 (pixel 1x1 trasparente)"""
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

# Test rapido senza file esterni
sample_media = Media(
    extension="png",
    media_type="image",
    source_type="base64",
    source=create_sample_image_base64(),
    detail="high"
)

response = client.invoke([
    TextBlock(content="Descrivi questa immagine"),
    MediaBlock(media=sample_media)
])
```

### Debug e logging

```python
# Abilita cache per debugging
client = create_multimodal_client("openai", use_cache=True)

# Verifica token utilizzati
print(f"Token prompt: {response.prompt_tokens_used}")
print(f"Token completamento: {response.completion_tokens_used}")
print(f"Token totali: {response.prompt_tokens_used + response.completion_tokens_used}")
```

## Documentazione completa

→ **[GUIDA_MULTIMODALE.md](GUIDA_MULTIMODALE.md)** - Documentazione tecnica dettagliata con esempi completi

→ **[Multimodal_Guide.ipynb](Multimodal_Guide.ipynb)** - Notebook interattivo con esempi e test

## Requisiti tecnici

- Python 3.8+
- Ambiente virtuale attivato
- OPENAI_API_KEY configurata (richiesta per tutte le funzioni)
- GOOGLE_API_KEY configurata (opzionale, solo per analisi con Gemini)
- Moduli: `openai`, `requests` (per download immagini)
- Connessione internet per API calls

## Stato funzionalità

| Funzione | OpenAI | Google | Note |
|----------|--------|--------|------|
| Analisi immagini | ✅ gpt-4o | ✅ gemini-2.5-flash | Entrambi testati e funzionanti |
| Augmentazione prompt | ✅ gpt-5 | ❌ | Solo OpenAI, temperature=1.0 |
| Generazione immagini | ✅ dall-e-3 | ❌ | Solo OpenAI, download automatico |
| Audio/Video | ❌ | ❌ | Framework in sviluppo |

## Flusso completo generazione

1. **Input utente**: Descrizione dell'immagine
2. **Augmentazione GPT-5**: Migliora il prompt (opzionale)
3. **Generazione DALL-E 3**: Crea l'immagine PNG
4. **Download automatico**: Salva in locale con timestamp
5. **Fallback intelligente**: Se GPT-5 fallisce, usa solo DALL-E 3

## Best practices

- Usa sempre `extension` senza punto per MIME type corretto
- Imposta `detail="high"` per analisi dettagliate
- Gestisci la memoria per conversazioni lunghe
- Usa cache per debugging e sviluppo
- Testa sempre con immagini di esempio prima di usare file reali