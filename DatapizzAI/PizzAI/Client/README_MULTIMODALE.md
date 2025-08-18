# DatapizzAI multimodale - quick start

> Sistema completo per analisi e generazione di contenuti multimodali (immagini, video, audio) con DatapizzAI

## Avvio rapido

```bash
# 1. Attiva l'ambiente virtuale
source .venv/bin/activate

# 2. Esegui il sistema multimodale
python Client/multimodal_examples.py
```

## Menu principale

```
Da cosa vuoi partire?

1. Immagine → Analisi dettagliata di un'immagine
2. Video → Descrizione di cosa accade nel video  
3. Audio → Analisi e trascrizione audio
4. Testo → Suggerimenti per generazione contenuti
```

## Esempio veloce

```python
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media

# Crea client
client = ClientFactory.create(
    provider="openai", 
    api_key="your-key",
    model="gpt-4o"
)

# Analizza immagine
image_media = Media(
    extension=".jpg",
    media_type="image", 
    source_type="url",
    source="https://example.com/image.jpg"
)

response = client.invoke(input=[
    TextBlock(content="Descrivi questa immagine"),
    MediaBlock(media=image_media)
])

print(response.text)
```

## Configurazione

### File .env richiesto

```bash
# Aggiungi almeno una chiave API
OPENAI_API_KEY=sk-your-openai-key        # Immagini
GOOGLE_API_KEY=your-google-key           # Tutto
ANTHROPIC_API_KEY=sk-ant-your-key        # Immagini
```

### Provider supportati

| Provider | Immagini | Video | Audio | Cache | Modello Consigliato |
|----------|----------|--------|-------|--------|---------------------|
| **OpenAI** | ✅ | ❌ | ❌ | ✅ | `gpt-4o` |
| **Google** | ✅ | ✅ | ✅ | ❌ | `gemini-2.5-flash` |  
| **Anthropic** | ✅ | ❌ | ❌ | ❌ | `claude-3-5-sonnet-latest` |

## File supportati

### Immagini
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`

### Audio  
- `.mp3`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.flac`, `.wma`

### Video
- `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`, `.webm`

## Casi d'uso principali

### 1. Analisi immagine
```python
# Carica immagine locale
image_block = create_mediablock_from_file("my_image.jpg")

# Analizza
result = client.invoke(input=[
    TextBlock(content="Analizza questa immagine in dettaglio"),
    image_block
])
```

### 2. Analisi video
```python  
# Video dal web
video_block = create_video_mediablock_from_url("https://example.com/video.mp4")

# Analizza cosa accade
result = client.invoke(input=[
    TextBlock(content="Cosa sta accadendo in questo video?"),
    video_block
])
```

### 3. Analisi audio
```python
# Audio locale
audio_block = create_audio_mediablock_from_file("audio.mp3")

# Trascrivi e descrivi
result = client.invoke(input=[
    TextBlock(content="Descrivi questo audio e trascrivi eventuali parole"),
    audio_block
])
```

### 4. Generazione da testo
```python
# Suggerimenti per generare contenuti
prompt = "Crea suggerimenti per generare un'immagine di un tramonto sulla montagna"
result = client.invoke(prompt)
```

## Fix errore MIME importante

**Sempre specificare `extension` nei Media objects per evitare errori:**

```python
# Errore: Unsupported MIME type
media = Media(media_type="image", source=data)

# Corretto
media = Media(
    extension=".png",  # Necessario 
    media_type="image",
    source=data
)
```

## Documentazione completa

➡️ **[GUIDA_MULTIMODALE.md](GUIDA_MULTIMODALE.md)** - Documentazione completa con tutti i dettagli

## Script disponibili

| File | Descrizione | Uso |
|------|-------------|-----|
| `multimodal_examples.py` | **Sistema completo multimodale** | `python multimodal_examples.py` |
| `text_only_examples.py` | Esempi solo testo | `python text_only_examples.py` |
| `datapizzai_client_guide.py` | Guida completa client | `python datapizzai_client_guide.py` |

## Demo interattive disponibili

### Menu principale (semplificato)
1. **Analisi immagine** - scegli e analizza immagini
2. **Analisi video** - descrivi cosa accade nei video
3. **Analisi audio** - trascrivi e descrivi audio
4. **Generazione testo** - suggerimenti per creare contenuti

### Menu legacy (avanzato)
- Accesso a tutte le demo originali
- Funzionalità conversazionali
- Gestione memoria avanzata
- Strumenti di debugging

## Troubleshooting rapido

### Problema: "No module named 'datapizzai'"
```bash
# Soluzione: Attiva l'ambiente virtuale
source .venv/bin/activate
```

### Problema: "API key not found"
```bash
# Soluzione: Verifica file .env nella directory PizzAI/
ls -la PizzAI/.env
```

### Problema: "Unsupported MIME type"
```python
# Soluzione: Aggiungi extension ai Media objects
media = Media(extension=".jpg", media_type="image", ...)
```

### Problema: "Client cache error"
```python
# Soluzione: Cache solo per OpenAI
if provider == "openai":
    client = ClientFactory.create(..., cache=MemoryCache())
else:
    client = ClientFactory.create(...)  # Senza cache
```

## Informazioni sui token

| Operazione | Token Medi | Provider | Note |
|------------|------------|----------|------|
| Analisi immagine semplice | 100-300 | OpenAI | Dipende da dettaglio |
| Analisi video breve | 200-500 | Google | Varia con durata |  
| Trascrizione audio | 50-200 | Google | Dipende da lunghezza |
| Generazione suggerimenti | 100-400 | Tutti | Base alla complessità |

## Prossimi passi

1. **Inizia** → `python multimodal_examples.py`
2. **Esplora** → prova tutti i 4 tipi di analisi
3. **Approfondisci** → leggi [GUIDA_MULTIMODALE.md](GUIDA_MULTIMODALE.md)
4. **Personalizza** → modifica i prompt per le tue esigenze
5. **Sviluppa** → integra nel tuo progetto

---

> **Suggerimento**: inizia con l'analisi di un'immagine locale per familiarizzare con il sistema, poi esplora video e audio dal web.
