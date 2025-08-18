# Guida completa: DatapizzAI multimodale

Una guida passo-passo per utilizzare le funzionalità multimodali di DatapizzAI per analizzare immagini, video, audio e generare contenuti.

## Indice

1. [Setup e configurazione](#1-setup-e-configurazione)
2. [Client multimodali supportati](#2-client-multimodali-supportati)
3. [Gestione media: immagini](#3-gestione-media-immagini)
4. [Gestione media: audio](#4-gestione-media-audio)
5. [Gestione media: video](#5-gestione-media-video)
6. [Analisi interattiva](#6-analisi-interattiva)
7. [Generazione da testo](#7-generazione-da-testo)
8. [Script completo di esempio](#8-script-completo-di-esempio)
9. [Troubleshooting](#9-troubleshooting)
10. [Best practices](#10-best-practices)

---

## 1. Setup e configurazione

### Prerequisiti

```bash
# Assicurati di avere il virtual environment attivato
source .venv/bin/activate

# Dipendenze necessarie
pip install python-dotenv
```

### Configurazione variabili d'ambiente

Crea un file `.env` nella directory `PizzAI/` con le tue chiavi API:

```bash
# File .env - Aggiungi almeno una chiave per provider multimodale
OPENAI_API_KEY=sk-your-openai-api-key-here
GOOGLE_API_KEY=your-google-api-key-here  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

### Import base

```python
import os
import base64
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import datapizzai
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, MediaBlock, Media, ROLE
from datapizzai.cache import MemoryCache
```

---

## 2. Client multimodali supportati

### Creazione client multimodali

```python
def create_multimodal_client(provider_name: str = "openai", use_cache: bool = False):
    """
    Crea un client che supporta contenuti multimodali
    
    Args:
        provider_name: "openai", "google", "anthropic"
        use_cache: Se abilitare la cache (solo OpenAI)
    """
    
    # Configurazione provider multimodali
    multimodal_providers = {
        "openai": {
            "api_key_env": "OPENAI_API_KEY", 
            "model": "gpt-4o",  # Supporta immagini
            "features": ["images", "text"],
            "cache_supported": True
        },
        "google": {
            "api_key_env": "GOOGLE_API_KEY",
            "model": "gemini-2.5-flash",  # Supporta immagini, audio, video
            "features": ["images", "text", "audio", "video"],
            "cache_supported": False
        },
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "model": "claude-3-5-sonnet-latest",  # Supporta immagini
            "features": ["images", "text"],
            "cache_supported": False
        }
    }
    
    config = multimodal_providers[provider_name]
    api_key = os.getenv(config["api_key_env"])
    
    if not api_key:
        raise ValueError(f"Chiave API non trovata per {provider_name}")
    
    # Cache solo per provider che la supportano
    extra_kwargs = {}
    if use_cache and config.get("cache_supported", False):
        cache = MemoryCache()
        extra_kwargs["cache"] = cache
    
    client = ClientFactory.create(
        provider=provider_name,
        api_key=api_key,
        model=config["model"],
        system_prompt="Sei un assistente AI multimodale. Rispondi in italiano in modo dettagliato.",
        temperature=0.7,
        **extra_kwargs
    )
    
    print(f"Client multimodale {provider_name} creato")
    print(f"   Modello: {config['model']}")
    print(f"   Supporta: {', '.join(config['features'])}")
    
    return client
```

### Esempio di uso

```python
# Client OpenAI con cache
openai_client = create_multimodal_client("openai", use_cache=True)

# Client Google (migliore per video/audio)
google_client = create_multimodal_client("google")

# Client Anthropic
anthropic_client = create_multimodal_client("anthropic")
```

---

## 3. Gestione media: immagini

### Ricerca immagini locali

```python
def find_local_images() -> List[str]:
    """Trova tutte le immagini nella directory corrente"""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    current_dir = Path('.')
    
    found_images = []
    for ext in image_extensions:
        found_images.extend(current_dir.glob(f'*{ext}'))
        found_images.extend(current_dir.glob(f'*{ext.upper()}'))
    
    return [str(img) for img in found_images]

# Esempio di uso
local_images = find_local_images()
print(f"Trovate {len(local_images)} immagini locali")
```

### Caricamento immagini

#### Da file locale

```python
def load_image_as_base64(image_path: str) -> Union[str, None]:
    """Carica un'immagine locale e la converte in base64"""
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            return image_data
    except Exception as e:
        print(f"Errore caricamento {image_path}: {e}")
        return None

def create_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea MediaBlock da file immagine locale"""
    image_b64 = load_image_as_base64(file_path)
    if not image_b64:
        raise ValueError(f"Impossibile caricare {file_path}")
    
    # IMPORTANTE: Determina l'extension per evitare errori MIME
    file_ext = Path(file_path).suffix.lower()
    if not file_ext:
        file_ext = ".png"  # Fallback
    
    media = Media(
        extension=file_ext,  # Critico per Google
        media_type="image",
        source_type="base64",
        source=image_b64,
        detail="high"
    )
    
    return MediaBlock(media=media)

# Esempio di uso
image_block = create_mediablock_from_file("example.jpg")
```

#### Da URL web

```python
def create_mediablock_from_url(url: str) -> MediaBlock:
    """Crea MediaBlock da URL immagine"""
    # Determina extension dall'URL
    file_ext = None
    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        if ext in url.lower():
            file_ext = ext
            break
    if not file_ext:
        file_ext = ".png"  # Fallback
    
    media = Media(
        extension=file_ext,  # Critico per Google
        media_type="image",
        source_type="url",
        source=url,
        detail="high"
    )
    
    return MediaBlock(media=media)

# Esempio di uso
web_image = create_mediablock_from_url(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
)
```

### Analisi immagini

```python
def analyze_image(client, image_block: MediaBlock, custom_prompt: str = None):
    """Analizza un'immagine con il client specificato"""
    
    default_prompt = """
    Analizza attentamente questa immagine e descrivi tutto quello che vedi in modo dettagliato, 
    includendo:
    - Oggetti e persone presenti
    - Colori dominanti
    - Ambientazione e contesto
    - Stile e composizione
    - Qualsiasi dettaglio rilevante
    """
    
    prompt = custom_prompt or default_prompt
    
    analysis_input = [
        TextBlock(content=prompt),
        image_block
    ]
    
    response = client.invoke(input=analysis_input)
    
    return {
        "text": response.text,
        "tokens_used": response.prompt_tokens_used + response.completion_tokens_used,
        "stop_reason": response.stop_reason
    }

# Esempio completo
client = create_multimodal_client("openai")
image_block = create_mediablock_from_file("my_image.jpg")
result = analyze_image(client, image_block)

print(f"Analisi: {result['text']}")
print(f"Token utilizzati: {result['tokens_used']}")
```

---

## 4. Gestione media: audio

### Supporto audio

```python
def find_local_audio() -> List[str]:
    """Trova tutti i file audio nella directory corrente"""
    audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma']
    current_dir = Path('.')
    
    found_audio = []
    for ext in audio_extensions:
        found_audio.extend(current_dir.glob(f'*{ext}'))
        found_audio.extend(current_dir.glob(f'*{ext.upper()}'))
    
    return [str(audio) for audio in found_audio]

def load_audio_as_base64(audio_path: str) -> Union[str, None]:
    """Carica un file audio e lo converte in base64"""
    try:
        with open(audio_path, "rb") as audio_file:
            return base64.b64encode(audio_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Errore caricamento audio {audio_path}: {e}")
        return None

def create_audio_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea MediaBlock da file audio locale"""
    audio_b64 = load_audio_as_base64(file_path)
    if not audio_b64:
        raise ValueError(f"Impossibile caricare {file_path}")
    
    file_ext = Path(file_path).suffix.lower()
    if not file_ext:
        file_ext = ".mp3"  # Fallback
    
    media = Media(
        extension=file_ext,
        media_type="audio",
        source_type="base64",
        source=audio_b64
    )
    
    return MediaBlock(media=media)

def create_audio_mediablock_from_url(url: str) -> MediaBlock:
    """Crea MediaBlock da URL audio"""
    file_ext = None
    for ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg']:
        if ext in url.lower():
            file_ext = ext
            break
    if not file_ext:
        file_ext = ".mp3"  # Fallback
    
    media = Media(
        extension=file_ext,
        media_type="audio",
        source_type="url",
        source=url
    )
    
    return MediaBlock(media=media)
```

### Analisi audio

```python
def analyze_audio(client, audio_block: MediaBlock):
    """Analizza un file audio"""
    
    analysis_input = [
        TextBlock(content="""
        Descrivi attentamente questo audio. Identifica:
        - Tutti i suoni presenti
        - Musica o melodie
        - Voci e dialoghi (trascrivi se possibile)
        - Rumori di fondo
        - Emozioni o mood trasmessi
        - Qualità audio
        """),
        audio_block
    ]
    
    response = client.invoke(input=analysis_input)
    return response.text

# Esempio di uso (Google supporta meglio l'audio)
client = create_multimodal_client("google")
audio_block = create_audio_mediablock_from_file("my_audio.mp3")
analysis = analyze_audio(client, audio_block)
print(f"Analisi audio: {analysis}")
```

---

## 5. Gestione media: video

### Supporto video

```python
def find_local_videos() -> List[str]:
    """Trova tutti i file video nella directory corrente"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    current_dir = Path('.')
    
    found_videos = []
    for ext in video_extensions:
        found_videos.extend(current_dir.glob(f'*{ext}'))
        found_videos.extend(current_dir.glob(f'*{ext.upper()}'))
    
    return [str(video) for video in found_videos]

def load_video_as_base64(video_path: str) -> Union[str, None]:
    """Carica un file video e lo converte in base64"""
    try:
        with open(video_path, "rb") as video_file:
            return base64.b64encode(video_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Errore caricamento video {video_path}: {e}")
        return None

def create_video_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea MediaBlock da file video locale"""
    video_b64 = load_video_as_base64(file_path)
    if not video_b64:
        raise ValueError(f"Impossibile caricare {file_path}")
    
    file_ext = Path(file_path).suffix.lower()
    if not file_ext:
        file_ext = ".mp4"  # Fallback
    
    media = Media(
        extension=file_ext,
        media_type="video",
        source_type="base64",
        source=video_b64
    )
    
    return MediaBlock(media=media)

def create_video_mediablock_from_url(url: str) -> MediaBlock:
    """Crea MediaBlock da URL video"""
    file_ext = None
    for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        if ext in url.lower():
            file_ext = ext
            break
    if not file_ext:
        file_ext = ".mp4"  # Fallback
    
    media = Media(
        extension=file_ext,
        media_type="video",
        source_type="url",
        source=url
    )
    
    return MediaBlock(media=media)
```

### Analisi video

```python
def analyze_video(client, video_block: MediaBlock):
    """Analizza un video"""
    
    analysis_input = [
        TextBlock(content="""
        Cosa sta accadendo in questo video? Descrivi dettagliatamente:
        - La scena e l'ambientazione
        - Le azioni che si svolgono
        - I personaggi presenti
        - Gli elementi visivi importanti
        - La narrativa o il messaggio
        - Lo stile e la qualità
        """),
        video_block
    ]
    
    response = client.invoke(input=analysis_input)
    return response.text

# Esempio di uso (Google supporta meglio i video)
client = create_multimodal_client("google")
video_block = create_video_mediablock_from_url(
    "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
)
analysis = analyze_video(client, video_block)
print(f"Cosa accade nel video: {analysis}")
```

---

## 6. Analisi interattiva

### Sistema di selezione media

```python
def interactive_media_selection(media_type: str) -> MediaBlock:
    """
    Sistema unificato per selezione interattiva di media
    
    Args:
        media_type: "image", "audio", "video"
    """
    
    # Trova file locali in base al tipo
    if media_type == "image":
        local_files = find_local_images()
        web_examples = [
            {"name": "Wikipedia PNG Demo", "url": "https://upload.wikimedia.org/.../demo.png"},
            {"name": "Test Pattern", "url": "https://via.placeholder.com/400x300"}
        ]
    elif media_type == "audio":
        local_files = find_local_audio()
        web_examples = [
            {"name": "Sample Bell", "url": "https://www.soundjay.com/.../bell.wav"},
            {"name": "Test Beep", "url": "https://www.soundjay.com/.../beep.wav"}
        ]
    elif media_type == "video":
        local_files = find_local_videos()
        web_examples = [
            {"name": "Big Buck Bunny", "url": "http://commondatastorage.googleapis.com/.../BigBuckBunny.mp4"},
            {"name": "Sample Video", "url": "https://www.learningcontainer.com/.../sample.mp4"}
        ]
    
    print(f"\nSelezione {media_type.capitalize()}")
    print("=" * 40)
    
    options = []
    
    # Mostra file locali
    if local_files:
        print(f"File {media_type} locali:")
        for file_path in local_files:
            file_size = Path(file_path).stat().st_size
            print(f"   {len(options) + 1}. {Path(file_path).name} ({file_size:,} bytes)")
            options.append(("local", file_path))
    
    # Mostra opzioni web
    print(f"\n{media_type.capitalize()} dal web:")
    for example in web_examples:
        print(f"   {len(options) + 1}. {example['name']}")
        options.append(("web", example["url"]))
    
    # Input utente
    while True:
        try:
            choice = input(f"\nScegli (1-{len(options)}): ").strip()
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                break
            print("Scelta non valida!")
        except ValueError:
            print("Inserisci un numero valido!")
    
    source_type, source_value = options[choice_idx]
    
    # Crea MediaBlock appropriato
    if source_type == "local":
        if media_type == "image":
            return create_mediablock_from_file(source_value)
        elif media_type == "audio":
            return create_audio_mediablock_from_file(source_value)
        elif media_type == "video":
            return create_video_mediablock_from_file(source_value)
    elif source_type == "web":
        if media_type == "image":
            return create_mediablock_from_url(source_value)
        elif media_type == "audio":
            return create_audio_mediablock_from_url(source_value)
        elif media_type == "video":
            return create_video_mediablock_from_url(source_value)

# Esempio di uso
media_block = interactive_media_selection("image")
client = create_multimodal_client("openai")
result = analyze_image(client, media_block)
print(result["text"])
```

---

## 7. Generazione da testo

### Sistema di generazione guidata

```python
def text_to_content_generation(client):
    """Sistema per generare suggerimenti di contenuti da descrizioni testuali"""
    
    print("Generazione contenuti da testo")
    print("=" * 40)
    
    # Menu di scelta
    content_types = {
        "1": {"name": "Immagine", "tools": ["DALL-E", "Midjourney", "Stable Diffusion"]},
        "2": {"name": "Video", "tools": ["RunwayML", "Pika Labs", "Synthesia"]},
        "3": {"name": "Audio", "tools": ["Mubert", "AIVA", "Soundful"]},
        "4": {"name": "Prompt Dettagliato", "tools": ["Universale"]}
    }
    
    print("Cosa vuoi generare?")
    for key, value in content_types.items():
        print(f"{key}. {value['name']}")
    
    # Input utente
    while True:
        choice = input("\nScegli (1-4): ").strip()
        if choice in content_types:
            break
        print("Scelta non valida!")
    
    # Descrizione del contenuto
    description = input("\nDescrivi cosa vuoi generare: ").strip()
    if not description:
        print("Descrizione necessaria!")
        return
    
    content_info = content_types[choice]
    
    # Genera prompt per AI
    if choice == "4":  # Prompt dettagliato
        ai_prompt = f"""
        L'utente vuole generare contenuti basati su questa descrizione:
        "{description}"
        
        Crea un prompt dettagliato e specifico che potrebbe essere utilizzato con 
        strumenti di generazione AI. Includi:
        - Dettagli visivi/sonori specifici
        - Stile e mood
        - Parametri tecnici
        - Considerazioni creative
        """
    else:
        ai_prompt = f"""
        L'utente vuole generare {content_info['name'].lower()} basato su: "{description}"
        
        Fornisci suggerimenti dettagliati includendo:
        - Tecniche e approcci consigliati  
        - Strumenti specifici da utilizzare
        - Parametri e impostazioni ottimali
        - Considerazioni creative e tecniche
        """
    
    # Genera risposta
    response = client.invoke(ai_prompt)
    
    print(f"\n🎨 Suggerimenti per {content_info['name']}:")
    print(f"{response.text}")
    
    print(f"\n🛠️ Strumenti consigliati:")
    for tool in content_info['tools']:
        print(f"   • {tool}")

# Esempio di uso
client = create_multimodal_client("openai")
text_to_content_generation(client)
```

---

## 8. Script completo di esempio

### Menu principale integrato

```python
#!/usr/bin/env python3
"""
Esempio completo del sistema multimodale DatapizzAI
"""

import os
import sys
from dotenv import load_dotenv

# Carica configurazione
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Import delle funzioni create sopra
# (Includi tutte le funzioni definite nelle sezioni precedenti)

def show_main_menu():
    """Menu principale dell'applicazione"""
    
    # Conta file disponibili
    local_images = find_local_images()
    local_audio = find_local_audio() 
    local_videos = find_local_videos()
    
    print("\n" + "="*60)
    print(" DATAPIZZAI - Analisi e Generazione Multimodale")
    print("="*60)
    
    print("File disponibili nella directory:")
    print(f"   Immagini: {len(local_images)} file")
    print(f"   Audio: {len(local_audio)} file") 
    print(f"   Video: {len(local_videos)} file")
    
    print("""
🚀 Da cosa vuoi partire?

1. Immagine → Analisi dettagliata di un'immagine
2. Video → Descrizione di cosa accade nel video
3. Audio → Analisi e trascrizione audio  
4. Testo → Suggerimenti per generazione contenuti

0. Esci

💡 Per ogni opzione potrai scegliere tra file locali o esempi dal web
    """)

def run_analysis():
    """Funzione principale per eseguire le analisi"""
    
    # Verifica client disponibili
    available_providers = []
    if os.getenv("OPENAI_API_KEY"):
        available_providers.append("OpenAI")
    if os.getenv("GOOGLE_API_KEY"):
        available_providers.append("Google")
    if os.getenv("ANTHROPIC_API_KEY"):
        available_providers.append("Anthropic")
    
    if not available_providers:
        print("Nessuna chiave API configurata!")
        print("Aggiungi almeno una chiave nel file .env")
        return
    
    print(f"✅ Provider disponibili: {', '.join(available_providers)}")
    
    while True:
        try:
            show_main_menu()
            choice = input("Scegli un'opzione: ").strip()
            
            if choice == "0":
                print("👋 Arrivederci!")
                break
            elif choice == "1":
                # Analisi immagine
                print("\nAnalisi immagine")
                client = create_multimodal_client("openai", use_cache=True)
                image_block = interactive_media_selection("image")
                result = analyze_image(client, image_block)
                print(f"\n📋 Risultato:\n{result['text']}")
                print(f"\n📊 Token utilizzati: {result['tokens_used']}")
                
            elif choice == "2":
                # Analisi video
                print("\nAnalisi video")
                client = create_multimodal_client("google")  # Google meglio per video
                video_block = interactive_media_selection("video")
                result = analyze_video(client, video_block)
                print(f"\n📋 Cosa accade nel video:\n{result}")
                
            elif choice == "3":
                # Analisi audio
                print("\nAnalisi audio")
                client = create_multimodal_client("google")  # Google meglio per audio
                audio_block = interactive_media_selection("audio")
                result = analyze_audio(client, audio_block)
                print(f"\n📋 Descrizione audio:\n{result}")
                
            elif choice == "4":
                # Generazione da testo
                print("\nGenerazione da testo")
                client = create_multimodal_client("openai")
                text_to_content_generation(client)
                
            else:
                print("Scelta non valida!")
                continue
            
            input("\nPremi INVIO per continuare...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Uscita forzata!")
            break
        except Exception as e:
            print(f"\nErrore: {e}")
            input("Premi INVIO per continuare...")

if __name__ == "__main__":
    run_analysis()
```

---

## 9. Troubleshooting

### Problemi comuni e soluzioni

#### Errore "Unsupported MIME type"

**Problema**: `400 INVALID_ARGUMENT: Unsupported MIME type: image/None`

**Soluzione**: Assicurati di specificare sempre il campo `extension` nei Media objects:

```python
# Sbagliato - causa errore MIME
media = Media(
    media_type="image",
    source_type="base64",
    source=image_data
)

# Corretto - include extension
media = Media(
    extension=".png",  # Necessario
    media_type="image", 
    source_type="base64",
    source=image_data,
    detail="high"
)
```

#### Cache Non Supportata

**Problema**: `Client.__init__() got an unexpected keyword argument 'cache'`

**Soluzione**: Solo OpenAI supporta il parametro cache nel costruttore:

```python
# Gestione cache sicura
def create_client_with_cache(provider, use_cache=False):
    cache_supported = provider == "openai"
    
    kwargs = {}
    if use_cache and cache_supported:
        kwargs["cache"] = MemoryCache()
    
    return ClientFactory.create(
        provider=provider,
        **other_params,
        **kwargs
    )
```

#### File Non Trovato

**Soluzione**: Verifica sempre l'esistenza del file:

```python
def safe_load_file(file_path: str):
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File non trovato: {file_path}")
    
    if not Path(file_path).is_file():
        raise ValueError(f"Il path non è un file: {file_path}")
    
    # Carica il file...
```

#### Chiavi API Mancanti

```python
def verify_api_keys():
    """Verifica la presenza delle chiavi API necessarie"""
    required_keys = ["OPENAI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"]
    available_keys = [key for key in required_keys if os.getenv(key)]
    
    if not available_keys:
        print("Nessuna chiave API trovata!")
        print("Aggiungi almeno una di queste al file .env:")
        for key in required_keys:
            print(f"   {key}=your-key-here")
        return False
    
    print(f"✅ Chiavi disponibili: {len(available_keys)}")
    return True
```

---

## 10. Best practices

### Gestione errori robusta

```python
def robust_media_analysis(client, media_block, max_retries=3):
    """Analisi media con retry automatico"""
    
    for attempt in range(max_retries):
        try:
            response = client.invoke(input=[
                TextBlock(content="Analizza questo media"),
                media_block
            ])
            return response.text
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Tentativo {attempt + 1} fallito: {e}")
                time.sleep(2 ** attempt)  # Backoff esponenziale
            else:
                print(f"Tutti i tentativi falliti: {e}")
                raise
```

### Ottimizzazione performance

```python
# 1. Usa cache quando possibile
client = create_multimodal_client("openai", use_cache=True)

# 2. Riduci dettaglio per file grandi
media = Media(
    extension=".jpg",
    media_type="image",
    source_type="base64", 
    source=image_data,
    detail="low"  # Invece di "high" per file grandi
)

# 3. Gestisci dimensioni file
def check_file_size(file_path: str, max_size_mb: int = 20):
    size_mb = Path(file_path).stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        print(f"⚠️ File grande: {size_mb:.1f}MB (max: {max_size_mb}MB)")
        return False
    return True
```

### Sicurezza e validazione

```python
def validate_media_input(file_path: str, allowed_types: List[str]):
    """Valida input media per sicurezza"""
    
    # Verifica estensione
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in allowed_types:
        raise ValueError(f"Tipo file non supportato: {file_ext}")
    
    # Verifica dimensioni
    if not check_file_size(file_path):
        raise ValueError("File troppo grande")
    
    # Verifica che sia realmente un file media
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            # Controlla signature del file...
    except Exception:
        raise ValueError("File corrotto o non accessibile")
    
    return True
```

### Logging e monitoraggio

```python
import logging

def setup_logging():
    """Configura logging per debugging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('multimodal_analysis.log'),
            logging.StreamHandler()
        ]
    )

def log_analysis_request(media_type: str, file_info: dict):
    """Log delle richieste di analisi"""
    logging.info(f"Analisi {media_type}: {file_info['name']} ({file_info['size']} bytes)")

def log_token_usage(tokens_used: int, provider: str):
    """Traccia utilizzo token"""
    logging.info(f"Token utilizzati: {tokens_used} (Provider: {provider})")
```

---

## Risorse aggiuntive

### File di esempio per test

Puoi scaricare questi file per testare il sistema:

- **Immagini**: [Lorem Picsum](https://picsum.photos/) - Genera immagini casuali
- **Audio**: [Freesound](https://freesound.org/) - Audio di dominio pubblico  
- **Video**: [Sample Videos](https://sample-videos.com/) - Video di test

### Documentazione ufficiale

- [DatapizzAI Documentation](https://docs.datapizza.tech/)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [Google Gemini Multimodal](https://ai.google.dev/gemini-api/docs/vision)
- [Anthropic Claude Vision](https://docs.anthropic.com/claude/docs/vision)

---

## Conclusioni

Questa guida fornisce tutti gli strumenti necessari per implementare un sistema multimodale completo con DatapizzAI. Le funzionalità includono:

- Analisi immagini con tutti i provider
- Analisi video (Google consigliato)
- Analisi audio (Google consigliato)  
- Generazione guidata da testo
- Gestione errori robusta
- Interface utente intuitiva
- Best practices per produzione

Il sistema è progettato per essere facilmente estensibile e adattabile a diverse esigenze di analisi multimodale.
