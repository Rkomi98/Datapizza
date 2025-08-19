# DatapizzAI multimodale

Guida rapida per l'utilizzo delle funzionalità di analisi e generazione immagini.

## Avvio rapido

```bash
# Attiva ambiente virtuale
source .venv/bin/activate

# Configura API keys nel file .env
echo 'OPENAI_API_KEY=your-key-here' > PizzAI/.env

# Esegui l'esempio
python Client/multimodal_examples.py
```

## Funzionalità principali

| Funzione | Descrizione | Provider supportati |
|----------|-------------|-------------------|
| **Analisi immagini** | Analizza immagini locali o da URL | OpenAI, Google, Anthropic |
| **Generazione immagini** | Crea immagini da descrizioni testuali | OpenAI (DALL-E 3) |

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
    extension=".jpg",
    media_type="image",
    source_type="url",
    source="https://example.com/image.jpg"
)

response = client.invoke([
    TextBlock(content="Descrivi questa immagine"),
    MediaBlock(media=media)
])

print(response.text)
```

## Esempio rapido - Generazione immagine

```python
import openai
import os

# Setup client DALL-E
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Genera immagine
response = client.images.generate(
    model="dall-e-3",
    prompt="Un gatto che suona il pianoforte",
    size="1024x1024",
    quality="hd"
)

print(f"Immagine generata: {response.data[0].url}")
```

## Configurazione

### File .env richiesto

```bash
# Directory: PizzAI/.env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-key-here  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### Provider e modelli

| Provider | Modello | Analisi | Generazione | Cache |
|----------|---------|---------|-------------|-------|
| OpenAI | gpt-4o | ✅ | ✅ | ✅ |
| Google | gemini-2.5-flash | ✅ | ❌ | ❌ |
| Anthropic | claude-3-5-sonnet | ✅ | ❌ | ❌ |

## Menu interattivo

```
Da cosa vuoi partire?

1. Analizza immagine → Carica e analizza qualsiasi immagine in dettaglio
2. Genera immagine → Crea immagini AI professionali da testo con DALL-E 3

0. Esci
```

### Opzioni disponibili

**Analisi immagine:**
- File locali (PNG, JPG, GIF, WebP)
- Immagini da URL web
- Domande personalizzate

**Generazione immagine:**
- Prompt enhancement automatico (opzionale)
- Qualità HD
- Salvataggio locale automatico

## Formati supportati

### Immagini input
- **Estensioni**: .jpg, .jpeg, .png, .gif, .bmp, .webp
- **Dimensione massima**: 20MB
- **Sorgenti**: File locali, URL web

### Immagini output
- **Formato**: PNG
- **Risoluzioni**: 1024x1024, 1792x1024, 1024x1792
- **Qualità**: standard, hd

## Risoluzione problemi comuni

### Error: "Unsupported MIME type"

```python
# Problema: extension mancante
media = Media(media_type="image", source=data)

# Soluzione: specifica sempre l'extension
media = Media(extension=".jpg", media_type="image", source=data)
```

### Error: "API key not found"

```bash
# Verifica file .env
ls -la PizzAI/.env

# Crea se mancante
echo 'OPENAI_API_KEY=your-key' > PizzAI/.env
```

## Documentazione completa

→ **[GUIDA_MULTIMODALE.md](GUIDA_MULTIMODALE.md)** - Documentazione tecnica dettagliata con esempi completi

## Requisiti tecnici

- Python 3.8+
- Ambiente virtuale attivato
- Almeno una API key configurata
- Connessione internet per API calls

## Note sui costi

- **OpenAI GPT-4o**: ~$0.01 per immagine analizzata
- **Google Gemini**: Tariffe competitive per analisi
- **DALL-E 3**: ~$0.04 per immagine generata (qualità standard), ~$0.08 (HD)
- **Anthropic Claude**: Pricing per token per analisi

Consultare la documentazione ufficiale dei provider per tariffe aggiornate.