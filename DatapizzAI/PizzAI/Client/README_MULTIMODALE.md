# DatapizzAI multimodale

Guida rapida per l'utilizzo delle funzionalità di analisi e generazione immagini con framework datapizzai.

## Avvio rapido

```bash
# Attiva ambiente virtuale
cd PizzAI && source .venv/bin/activate

# Configura API keys nel file .env
echo 'OPENAI_API_KEY=your-key-here' > .env
echo 'GOOGLE_API_KEY=your-key-here' >> .env

# Esegui l'esempio
cd Client && python multimodal_examples.py
```

## Funzionalità principali

| Funzione | Descrizione | Provider funzionanti |
|----------|-------------|-------------------|
| **Analisi immagini** | Analizza immagini locali o da URL | OpenAI (gpt-4o), Google (gemini-2.5-flash) |
| **Generazione immagini** | GPT-5 per augmentazione + DALL-E 3 per generazione | OpenAI (GPT-5 + DALL-E 3) |

## Esempio rapido - Analisi immagine

```python
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media
import os

# Setup client
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
    TextBlock(content="Descrivi questa immagine"),
    MediaBlock(media=media)
])

print(response.text)
```

## Esempio rapido - Generazione immagine

```python
from datapizzai.clients import ClientFactory
import openai
import requests
import os

# 1. Augmentazione prompt con GPT-5
gpt5_client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-5",
    temperature=1.0
)

augmented = gpt5_client.invoke("Migliora questo prompt: un gatto che suona il pianoforte")
print(f"Prompt migliorato: {augmented.text}")

# 2. Generazione immagine con DALL-E 3
dalle_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = dalle_client.images.generate(
    model="dall-e-3",
    prompt=augmented.text,
    size="1024x1024",
    quality="standard"
)

# 3. Download locale
image_url = response.data[0].url
img_data = requests.get(image_url).content

with open("generated_image.png", "wb") as f:
    f.write(img_data)

print("✅ Immagine salvata: generated_image.png")
```

## Configurazione

### File .env richiesto

```bash
# Directory: PizzAI/.env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-key-here
```

### Provider e modelli

| Provider | Modello | Analisi immagini | Augmentazione prompt | Generazione immagini | Cache |
|----------|---------|-----------------|-------------------|-------------------|-------|
| OpenAI | gpt-4o | ✅ | ❌ | ❌ | ✅ |
| OpenAI | gpt-5 | ❌ | ✅ | ❌ | ❌ |
| OpenAI | dall-e-3 | ❌ | ❌ | ✅ | ❌ |
| Google | gemini-2.5-flash | ✅ | ❌ | ❌ | ❌ |

## Menu interattivo

```
Da cosa vuoi partire?

1. Analizza immagine → Carica e analizza un'immagine (funziona)
2. Genera immagine → GPT-5 + DALL-E 3 (download locale)

0. Esci

Nota: Audio/video temporaneamente non disponibili (framework in sviluppo)
```

### Opzioni disponibili

**Analisi immagine:**
- File locali (PNG, JPG, GIF, WebP)
- Immagini da URL web (solo per alcuni provider)
- Selezione provider (OpenAI/Google)
- Domande personalizzate

**Generazione immagine:**
- **Augmentazione prompt**: GPT-5 migliora automaticamente la descrizione
- **Generazione**: DALL-E 3 crea l'immagine (1024x1024, qualità standard/HD)
- **Download automatico**: Salvataggio locale in formato PNG
- **Fallback intelligente**: Se GPT-5 non disponibile, usa solo DALL-E 3

## Formati supportati

### Immagini input
- **Estensioni**: .jpg, .jpeg, .png, .gif, .bmp, .webp
- **Dimensione massima**: 20MB
- **Sorgenti**: File locali, URL web

### Immagini output
- **Formato**: PNG (raster)
- **Risoluzione**: 1024x1024, 1792x1024, 1024x1792
- **Qualità**: standard, HD
- **Download**: automatico in locale

## Risoluzione problemi comuni

### Error: "Unsupported MIME type"

```python
# Problema: extension con punto
media = Media(extension=".jpg", media_type="image", source=data)

# Soluzione: extension senza punto per MIME type corretto
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
# Problema: GPT-5 supporta solo temperature=1.0
client = ClientFactory.create(model="gpt-5", temperature=0.7)  # ❌

# Soluzione: usa temperature=1.0 per GPT-5
client = ClientFactory.create(model="gpt-5", temperature=1.0)  # ✅
```

### Error: "Modulo 'requests' non installato"

```bash
# Installa requests per download immagini
pip install requests
```

## Documentazione completa

→ **[GUIDA_MULTIMODALE.md](GUIDA_MULTIMODALE.md)** - Documentazione tecnica dettagliata con esempi completi

## Requisiti tecnici

- Python 3.8+
- Ambiente virtuale attivato
- OPENAI_API_KEY configurata (richiesta per tutte le funzioni)
- GOOGLE_API_KEY configurata (opzionale, solo per analisi con Gemini)
- Moduli: `openai`, `requests` (per download immagini)
- Connessione internet per API calls

## Note sui costi

- **OpenAI GPT-4o**: ~$0.01 per immagine analizzata
- **OpenAI GPT-5**: ~$0.02 per augmentazione prompt
- **OpenAI DALL-E 3**: ~$0.04 per immagine generata (standard), ~$0.08 (HD)
- **Google Gemini**: Tariffe competitive per analisi immagini

Consultare la documentazione ufficiale dei provider per tariffe aggiornate.

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