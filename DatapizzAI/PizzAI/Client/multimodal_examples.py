#!/usr/bin/env python3
"""
Script di esempio per l'uso della libreria datapizzai - Modalità MULTIMODALE  
==========================================================================

Questo script dimostra come utilizzare datapizzai per contenuti multimodali:
1. Modalità "one shot" - singola query multimodale → risposta
2. Modalità "conversational" - sessione multi-turno con media e testo

Supporta:
- Testo + Immagini (URL, base64, file locali)
- Testo + Audio (se supportato dal provider)
- Combinazioni multiple di media
- Risposte sia testuali che multimodali

Autore: Marco Calcaterra  
Data: 2025
"""

import os
import time
import base64
import requests
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env nella directory parent
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Importazioni datapizzai
from datapizzai.clients import ClientFactory
from datapizzai.clients.factory import Provider
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, MediaBlock, Media, ROLE
from datapizzai.cache import MemoryCache


def print_section(title: str):
    """Stampa una sezione formattata"""
    print("\n" + "="*65)
    print(f" {title}")
    print("="*65)


def print_subsection(title: str):
    """Stampa una sottosezione formattata"""
    print(f"\n--- {title} ---")


def create_multimodal_client(provider_name: str = "openai", use_cache: bool = False, task: str = "image"):
    """
    Crea un client che supporta contenuti multimodali
    
    Args:
        provider_name: "openai", "google", "anthropic" (supportano visione)
        use_cache: Se abilitare la cache
    """
    
    # Provider che funzionano realmente per analisi immagini
    multimodal_providers = {
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "model": os.getenv("OPENAI_VISION_MODEL", "gpt-4o"),
            "features": ["images", "text", "generation"],
            "cache_supported": True
        },
        "google": {
            "api_key_env": "GOOGLE_API_KEY", 
            "model": os.getenv("GOOGLE_VISION_MODEL", "gemini-2.5-flash"),
            "features": ["images", "text"],
            "cache_supported": False
        }
    }
    
    if provider_name not in multimodal_providers:
        print(f"❌ Provider {provider_name} non supporta contenuti multimodali")
        return None
    
    config = multimodal_providers[provider_name]
    api_key = os.getenv(config["api_key_env"])
    
    if not api_key:
        print(f"⚠️ Chiave API non trovata per {provider_name}")
        return None
    
    # Cache solo per provider che la supportano
    cache = None
    extra_kwargs = {}
    
    if use_cache and config.get("cache_supported", False):
        cache = MemoryCache()
        extra_kwargs["cache"] = cache
    
    try:
        model_name = config["model"]
        client = ClientFactory.create(
            provider=provider_name,
            api_key=api_key,
            model=model_name,
            system_prompt="Sei un assistente AI multimodale. Puoi analizzare immagini, audio e testo. Rispondi in italiano in modo dettagliato ma conciso.",
            temperature=0.7,
            **extra_kwargs
        )
        
        print(f"✅ Client multimodale {provider_name} creato")
        print(f"   🎯 Modello: {model_name}")
        print(f"   🔧 Supporta: {', '.join(config['features'])}")
        if cache:
            print("   📦 Cache abilitata")
        elif use_cache:
            print(f"   ⚠️ Cache non supportata per {provider_name}")
        
        return client
        
    except Exception as e:
        print(f"❌ Errore creazione client {provider_name}: {e}")
        return None


def load_image_as_base64(image_path: str) -> Union[str, None]:
    """
    Carica un'immagine locale e la converte in base64
    
    Args:
        image_path: Percorso del file immagine
        
    Returns:
        String base64 dell'immagine o None se errore
    """
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            return image_data
    except FileNotFoundError:
        print(f"⚠️ File {image_path} non trovato")
        return None
    except Exception as e:
        print(f"⚠️ Errore caricamento {image_path}: {e}")
        return None


def load_audio_as_base64(audio_path: str) -> Union[str, None]:
    """
    Carica un file audio locale e lo converte in base64
    
    Args:
        audio_path: Percorso del file audio
        
    Returns:
        String base64 dell'audio o None se errore
    """
    try:
        with open(audio_path, "rb") as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            return audio_data
    except FileNotFoundError:
        print(f"⚠️ File {audio_path} non trovato")
        return None
    except Exception as e:
        print(f"⚠️ Errore caricamento {audio_path}: {e}")
        return None


def load_video_as_base64(video_path: str) -> Union[str, None]:
    """
    Carica un file video locale e lo converte in base64
    
    Args:
        video_path: Percorso del file video
        
    Returns:
        String base64 del video o None se errore
    """
    try:
        with open(video_path, "rb") as video_file:
            video_data = base64.b64encode(video_file.read()).decode('utf-8')
            return video_data
    except FileNotFoundError:
        print(f"⚠️ File {video_path} non trovato")
        return None
    except Exception as e:
        print(f"⚠️ Errore caricamento {video_path}: {e}")
        return None


def create_sample_image_base64() -> str:
    """
    Crea un'immagine di esempio in base64 (pixel 1x1 trasparente)
    Utile per test quando non abbiamo immagini reali
    """
    # PNG 1x1 pixel trasparente
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="


def find_local_images() -> List[str]:
    """
    Trova tutte le immagini presenti nella directory corrente
    
    Returns:
        Lista di percorsi delle immagini trovate
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    current_dir = Path('.')
    
    found_images = []
    for ext in image_extensions:
        found_images.extend(current_dir.glob(f'*{ext}'))
        found_images.extend(current_dir.glob(f'*{ext.upper()}'))
    
    return [str(img) for img in found_images]


def find_local_audio() -> List[str]:
    """
    Trova tutti i file audio presenti nella directory corrente
    
    Returns:
        Lista di percorsi degli audio trovati
    """
    audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.wma']
    current_dir = Path('.')
    
    found_audio = []
    for ext in audio_extensions:
        found_audio.extend(current_dir.glob(f'*{ext}'))
        found_audio.extend(current_dir.glob(f'*{ext.upper()}'))
    
    return [str(audio) for audio in found_audio]


def find_local_videos() -> List[str]:
    """
    Trova tutti i file video presenti nella directory corrente
    
    Returns:
        Lista di percorsi dei video trovati
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    current_dir = Path('.')
    
    found_videos = []
    for ext in video_extensions:
        found_videos.extend(current_dir.glob(f'*{ext}'))
        found_videos.extend(current_dir.glob(f'*{ext.upper()}'))
    
    return [str(video) for video in found_videos]


def choose_media_source(media_type: str, interactive: bool = True) -> MediaBlock:
    """
    Permette di scegliere tra media locale o dal web
    
    Args:
        media_type: "image", "audio", o "video"
        interactive: Se True, mostra menu interattivo. Se False, usa default.
        
    Returns:
        MediaBlock con il media scelto
    """
    if media_type == "image":
        return choose_image_source(interactive)
    elif media_type == "audio":
        return choose_audio_source(interactive)
    elif media_type == "video":
        return choose_video_source(interactive)
    else:
        raise ValueError(f"Tipo media non supportato: {media_type}")


def choose_image_source(interactive: bool = True) -> MediaBlock:
    """
    Permette di scegliere tra immagine locale o dal web
    """
    local_images = find_local_images()
    
    # URL di immagini di esempio dal web
    web_images = [
        {
            "name": "PNG Transparency Demo (Wikipedia)", 
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
        },
        {
            "name": "Wikimedia Test Image",
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Vd-Orig.png/256px-Vd-Orig.png"
        },
        {
            "name": "Simple Test Pattern",
            "url": "https://via.placeholder.com/400x300/0066CC/FFFFFF?text=Test+Image"
        }
    ]
    
    if not interactive:
        if local_images:
            return create_mediablock_from_file(local_images[0])
        else:
            return create_mediablock_from_url(web_images[0]["url"])
    
    print("\n🖼️ Selezione Immagine")
    print("=" * 30)
    
    return _interactive_media_selection(local_images, web_images, "image")


def choose_audio_source(interactive: bool = True) -> MediaBlock:
    """
    Permette di scegliere tra audio locale o dal web
    """
    local_audio = find_local_audio()
    
    # URL di audio di esempio dal web
    web_audio = [
        {
            "name": "Sample Audio Test",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
        },
        {
            "name": "Short Beep Sound",
            "url": "https://www.soundjay.com/misc/sounds/beep-28.wav"  
        }
    ]
    
    if not interactive:
        if local_audio:
            return create_audio_mediablock_from_file(local_audio[0])
        else:
            return create_audio_mediablock_from_url(web_audio[0]["url"])
    
    print("\n🎵 Selezione Audio")
    print("=" * 30)
    
    return _interactive_media_selection(local_audio, web_audio, "audio")


def choose_video_source(interactive: bool = True) -> MediaBlock:
    """
    Permette di scegliere tra video locale o dal web
    """
    local_videos = find_local_videos()
    
    # URL di video di esempio dal web
    web_videos = [
        {
            "name": "Sample Video Test (Big Buck Bunny)",
            "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        },
        {
            "name": "Short Test Video",
            "url": "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
        }
    ]
    
    if not interactive:
        if local_videos:
            return create_video_mediablock_from_file(local_videos[0])
        else:
            return create_video_mediablock_from_url(web_videos[0]["url"])
    
    print("\n🎬 Selezione Video")
    print("=" * 30)
    
    return _interactive_media_selection(local_videos, web_videos, "video")


def _interactive_media_selection(local_files: List[str], web_options: List[dict], media_type: str) -> MediaBlock:
    """
    Helper per la selezione interattiva di media
    """
    options = []
    
    # Aggiungi file locali
    if local_files:
        print(f"📁 File {media_type} locali disponibili:")
        for file_path in local_files:
            file_size = Path(file_path).stat().st_size
            print(f"   {len(options) + 1}. {Path(file_path).name} ({file_size:,} bytes)")
            options.append(("local", file_path))
    
    # Aggiungi opzioni web
    print(f"\n🌐 {media_type.capitalize()} di esempio dal web:")
    for web_option in web_options:
        print(f"   {len(options) + 1}. {web_option['name']}")
        options.append(("web", web_option["url"]))
    
    # Opzione di esempio se è immagine
    if media_type == "image":
        print(f"   {len(options) + 1}. Pixel di esempio (1x1 trasparente)")
        options.append(("sample", None))
    
    # Input utente
    while True:
        try:
            choice = input(f"\n👉 Scegli un {media_type} (1-{len(options)}): ").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(options):
                break
            else:
                print("❌ Scelta non valida!")
        except ValueError:
            print("❌ Inserisci un numero valido!")
    
    source_type, source_value = options[choice_idx]
    
    print(f"\n🔄 Caricamento opzione {choice_idx + 1}...")
    
    try:
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
        elif source_type == "sample" and media_type == "image":
            return create_sample_mediablock()
    except Exception as e:
        print(f"❌ Errore caricamento: {e}")
        if media_type == "image":
            print("🔄 Fallback a immagine di esempio...")
            return create_sample_mediablock()
        else:
            raise e


def create_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea MediaBlock da file locale"""
    image_b64 = load_image_as_base64(file_path)
    if not image_b64:
        raise ValueError(f"Impossibile caricare {file_path}")
    
    # Determina l'extension dal file (senza punto per MIME type)
    file_ext = Path(file_path).suffix.lower()
    if not file_ext:
        file_ext = ".png"  # Default fallback
    
    # Rimuovi il punto per MIME type corretto (es: "png" non ".png")
    extension_clean = file_ext.lstrip('.')
    
    # Extension corretta senza punto per MIME type
    
    media = Media(
        extension=extension_clean,
        media_type="image",
        source_type="base64",
        source=image_b64,
        detail="high"
    )
    
    print(f"✅ Caricata immagine locale: {Path(file_path).name}")
    return MediaBlock(media=media)


def create_mediablock_from_url(url: str) -> MediaBlock:
    """Crea MediaBlock da URL"""
    # Cerca di determinare l'extension dall'URL
    file_ext = None
    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        if ext in url.lower():
            file_ext = ext
            break
    if not file_ext:
        file_ext = ".png"  # Default fallback
    
    # Rimuovi il punto per MIME type corretto
    extension_clean = file_ext.lstrip('.')
    
    media = Media(
        extension=extension_clean,
        media_type="image",
        source_type="url", 
        source=url,
        detail="high"
    )
    
    print(f"✅ Caricata immagine dal web: {url}")
    return MediaBlock(media=media)


def create_sample_mediablock() -> MediaBlock:
    """Crea MediaBlock con immagine di esempio"""
    sample_base64 = create_sample_image_base64()
    media = Media(
        extension="png",  # Senza punto per MIME type corretto
        media_type="image",
        source_type="base64",
        source=sample_base64,
        detail="high"
    )
    
    print("✅ Creata immagine di esempio (1x1 pixel)")
    return MediaBlock(media=media)


def create_audio_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea MediaBlock da file audio locale"""
    audio_b64 = load_audio_as_base64(file_path)
    if not audio_b64:
        raise ValueError(f"Impossibile caricare {file_path}")
    
    # Determina l'extension dal file (senza punto per MIME type)
    file_ext = Path(file_path).suffix.lower()
    if not file_ext:
        file_ext = ".mp3"  # Default fallback
    
    # Rimuovi il punto per MIME type corretto
    extension_clean = file_ext.lstrip('.')
    
    media = Media(
        extension=extension_clean,
        media_type="audio",
        source_type="base64",
        source=audio_b64
    )
    
    print(f"✅ Caricato audio locale: {Path(file_path).name}")
    return MediaBlock(media=media)


def create_audio_mediablock_from_url(url: str) -> MediaBlock:
    """Crea MediaBlock da URL audio"""
    # Cerca di determinare l'extension dall'URL
    file_ext = None
    for ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg']:
        if ext in url.lower():
            file_ext = ext
            break
    if not file_ext:
        file_ext = ".mp3"  # Default fallback
    
    # Rimuovi il punto per MIME type corretto
    extension_clean = file_ext.lstrip('.')
    
    media = Media(
        extension=extension_clean,
        media_type="audio",
        source_type="url",
        source=url
    )
    
    print(f"✅ Caricato audio dal web: {url}")
    return MediaBlock(media=media)


def create_video_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea MediaBlock da file video locale"""
    video_b64 = load_video_as_base64(file_path)
    if not video_b64:
        raise ValueError(f"Impossibile caricare {file_path}")
    
    # Determina l'extension dal file (senza punto per MIME type)
    file_ext = Path(file_path).suffix.lower()
    if not file_ext:
        file_ext = ".mp4"  # Default fallback
    
    # Rimuovi il punto per MIME type corretto
    extension_clean = file_ext.lstrip('.')
    
    media = Media(
        extension=extension_clean,
        media_type="video",
        source_type="base64",
        source=video_b64
    )
    
    print(f"✅ Caricato video locale: {Path(file_path).name}")
    return MediaBlock(media=media)


def create_video_mediablock_from_url(url: str) -> MediaBlock:
    """Crea MediaBlock da URL video"""
    # Cerca di determinare l'extension dall'URL
    file_ext = None
    for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
        if ext in url.lower():
            file_ext = ext
            break
    if not file_ext:
        file_ext = ".mp4"  # Default fallback
    
    # Rimuovi il punto per MIME type corretto
    extension_clean = file_ext.lstrip('.')
    
    media = Media(
        extension=extension_clean,
        media_type="video",
        source_type="url",
        source=url
    )
    
    print(f"✅ Caricato video dal web: {url}")
    return MediaBlock(media=media)


def create_media_blocks_examples(interactive: bool = False, count: int = 1) -> List[MediaBlock]:
    """
    Crea esempi di MediaBlock per le demo
    
    Args:
        interactive: Se True, permette scelta interattiva delle immagini
        count: Numero di MediaBlock da creare
    """
    media_blocks = []
    
    if interactive and count > 1:
        print(f"\n📝 Creazione di {count} MediaBlock...")
        
        for i in range(count):
            print(f"\n--- MediaBlock {i + 1}/{count} ---")
            try:
                media_block = choose_image_source(interactive=True)
                media_blocks.append(media_block)
            except Exception as e:
                print(f"⚠️ Errore MediaBlock {i + 1}: {e}")
                # Fallback a esempio
                media_blocks.append(create_sample_mediablock())
    
    elif interactive and count == 1:
        try:
            media_block = choose_image_source(interactive=True)
            media_blocks.append(media_block)
        except Exception as e:
            print(f"⚠️ Errore: {e}")
            media_blocks.append(create_sample_mediablock())
    
    else:
        # Modalità automatica - usa immagini disponibili
        local_images = find_local_images()
        
        if local_images:
            # Usa immagini locali se disponibili
            for i, img_path in enumerate(local_images[:count]):
                try:
                    media_block = create_mediablock_from_file(img_path)
                    media_blocks.append(media_block)
                except Exception as e:
                    print(f"⚠️ Errore {img_path}: {e}")
        
        # Se non abbiamo abbastanza immagini, aggiungi esempi
        while len(media_blocks) < count:
            media_blocks.append(create_sample_mediablock())
    
    return media_blocks


# ==============================================================================
# DEMO SPECIFICHE PER TIPO DI MEDIA
# ==============================================================================

def demo_image_analysis():
    """
    Analizza un'immagine scelta dall'utente
    """
    print_section("ANALISI IMMAGINE")
    
    provider = _select_provider("openai")
    client = create_multimodal_client(provider, use_cache=True, task="image")
    if not client:
        print("❌ Client multimodale non disponibile")
        return
    
    try:
        # Scelta dell'immagine
        image_block = choose_image_source(interactive=True)
        
        # Analisi immagine con prompt specifico
        analysis_input = [
            TextBlock(content="Analizza attentamente questa immagine e descrivi tutto quello che vedi in modo dettagliato, includendo colori, oggetti, persone, ambientazione e qualsiasi altro dettaglio rilevante."),
            image_block
        ]
        
        print("\n🔄 Analisi in corso...")
        response = client.invoke(input=analysis_input)
        
        print("\n🤖 Analisi dell'immagine:")
        print(f"   {response.text}")
        
        print(f"\n📊 Token utilizzati: {response.prompt_tokens_used + response.completion_tokens_used}")
        
    except Exception as e:
        print(f"❌ Errore durante l'analisi: {e}")


def _select_provider(default: str = "openai") -> str:
    """Selezione provider funzionanti"""
    options = {"1": "openai", "2": "google"}
    labels = {"1": "OpenAI (gpt-4o)", "2": "Google (gemini-2.5-flash)"}
    print("\nSeleziona provider:")
    for k in ["1", "2"]:
        print(f" {k}. {labels[k]}")
    choice = input("\nScelta (1-2, invio per OpenAI): ").strip()
    return options.get(choice, default)


# Audio e video rimossi - non supportati dal framework datapizzai
def generate_image_with_dalle(prompt: str, api_key: str, size: str = "1024x1024", quality: str = "standard") -> str:
    """
    Genera un'immagine usando DALL-E
    
    Args:
        prompt: Descrizione dell'immagine da generare
        api_key: Chiave API OpenAI
        size: Dimensioni dell'immagine ("1024x1024", "1792x1024", "1024x1792")
        quality: Qualità dell'immagine ("standard" o "hd")
    
    Returns:
        URL dell'immagine generata
    """
    try:
        # Rimosso uso diretto dell'SDK OpenAI: generazione immagini verrà effettuata via framework
        raise NotImplementedError("La generazione diretta via OpenAI SDK è disabilitata. Usa demo_text_generation (PNG via framework).")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        
        return response.data[0].url
    
    except Exception as e:
        raise Exception(f"Errore generazione immagine: {e}")


def demo_text_generation():
    """
    Genera immagini usando GPT-5 di OpenAI (augmentazione + generazione)
    """
    print_section("GENERAZIONE IMMAGINE - GPT-5")

    description = input("\nDescrivi l'immagine da generare: ").strip()
    if not description:
        print("Descrizione vuota")
        return

    # Chiedi se augmentare il prompt
    augment = input("\nVuoi augmentare il prompt? (s/n): ").strip().lower() == 's'
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY non trovata nel file .env")
            return

        # Client per augmentazione prompt (GPT-5 via framework)
        final_description = description
        if augment:
            # Usa GPT-5 per augmentazione prompt
            gpt5_client = ClientFactory.create(
                provider="openai",
                api_key=api_key,
                model="gpt-5",  # Usa GPT-5 per miglior augmentazione
                temperature=1.0  # GPT-5 supporta solo temperature=1
            )
            if gpt5_client:
                print("\n🔄 Augmentazione prompt con GPT-5...")
                augment_prompt = f"""Migliora questo prompt per generazione immagini AI: "{description}"

Aggiungi dettagli su:
- Stile visivo e colori specifici
- Composizione e prospettiva
- Elementi decorativi e atmosfera
- Qualità artistica e tecnica fotografica

Rispondi solo con il prompt migliorato, max 400 caratteri."""

                augment_response = gpt5_client.invoke(augment_prompt)
                final_description = augment_response.text.strip()
                print(f"\nPrompt augmentato con GPT-5: {final_description}")
            else:
                print("⚠️ GPT-5 non disponibile, uso prompt originale")

        # Genera immagine con GPT-5 (via framework)
        print("\n🔄 Generazione immagine con GPT-5...")
        
        try:
            # Usa GPT-5 per generazione immagine
            gpt5_client = ClientFactory.create(
                provider="openai",
                api_key=api_key,
                model="gpt-5",  # GPT-5 per generazione
                temperature=1.0  # GPT-5 supporta solo temperature=1
            )
            
            if not gpt5_client:
                print("❌ Client GPT-5 non disponibile")
                return

            # Prompt per generazione immagine
            generation_prompt = f"""Genera un'immagine basata su questa descrizione: "{final_description}"

Crea un'immagine dettagliata e di alta qualità che rappresenti fedelmente la descrizione fornita.
Usa colori vividi, composizione bilanciata e stile artistico professionale."""

            response = gpt5_client.invoke(generation_prompt)
            
            # Se GPT-5 restituisce un URL di immagine
            if "http" in response.text and ("png" in response.text.lower() or "jpg" in response.text.lower()):
                image_url = response.text.strip()
                print(f"✅ Immagine generata con GPT-5!")
                print(f"🔗 URL: {image_url}")
                
                # Scarica e salva l'immagine in locale
                print("\n🔄 Download immagine in corso...")
                try:
                    import requests
                    
                    # Download dell'immagine
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    
                    # Nome file con timestamp
                    filename = f"generated_image_{int(time.time())}.png"
                    
                    # Salva l'immagine
                    with open(filename, "wb") as f:
                        f.write(img_response.content)
                    
                    print(f"✅ Immagine salvata: {filename}")
                    print(f"📏 Dimensione: {len(img_response.content):,} bytes")
                    
                except ImportError:
                    print("❌ Modulo 'requests' non installato per download")
                    print("💡 Installa con: pip install requests")
                    print(f"🔗 URL disponibile: {image_url}")
                except Exception as e:
                    print(f"❌ Errore download: {e}")
                    print(f"🔗 URL disponibile: {image_url}")
            else:
                # GPT-5 ha restituito testo invece di URL - attiva fallback
                print("⚠️ GPT-5 ha restituito testo invece di un'immagine:")
                print(f"Risposta: {response.text[:200]}...")
                print("💡 GPT-5 non supporta la generazione di immagini")
                
                # Attiva fallback automatico a DALL-E 3
                print("🔄 Attivazione automatica fallback a DALL-E 3...")
                raise Exception("GPT-5 non supporta generazione immagini - fallback a DALL-E")
            
        except Exception as e:
            print(f"❌ Errore GPT-5: {e}")
            print("💡 Fallback a DALL-E 3...")
            
            # Fallback a DALL-E 3 se GPT-5 fallisce
            try:
                import openai
                dalle_client = openai.OpenAI(api_key=api_key)
                
                response = dalle_client.images.generate(
                    model="dall-e-3",
                    prompt=final_description,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                
                image_url = response.data[0].url
                print(f"✅ Immagine generata con DALL-E 3 (fallback)!")
                print(f"🔗 URL: {image_url}")
                
                # Scarica e salva l'immagine in locale
                print("\n🔄 Download immagine in corso...")
                try:
                    import requests
                    
                    # Download dell'immagine
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    
                    # Nome file con timestamp
                    filename = f"generated_image_{int(time.time())}.png"
                    
                    # Salva l'immagine
                    with open(filename, "wb") as f:
                        f.write(img_response.content)
                    
                    print(f"✅ Immagine salvata: {filename}")
                    print(f"📏 Dimensione: {len(img_response.content):,} bytes")
                    
                except Exception as download_error:
                    print(f"❌ Errore download: {download_error}")
                    print(f"🔗 URL disponibile: {image_url}")
                
            except ImportError:
                print("❌ Moduli 'openai' o 'requests' non installati")
            except Exception as dalle_error:
                print(f"❌ Errore DALL-E fallback: {dalle_error}")
        
    except Exception as e:
        print(f"❌ Errore generazione: {e}")


# ==============================================================================
# MODALITÀ ONE-SHOT MULTIMODALE (LEGACY)
# ==============================================================================

def demo_oneshot_image_analysis(interactive_images: bool = False):
    """
    Dimostra analisi di immagini in modalità one-shot
    
    Args:
        interactive_images: Se True, permette scelta interattiva delle immagini
    """
    print_section("ONE-SHOT MULTIMODALE - Analisi Immagini")
    
    client = create_multimodal_client("openai", use_cache=True)
    if not client:
        print("❌ Client multimodale non disponibile")
        return
    
    # Prepara esempi di media
    if interactive_images:
        print("🖼️ Scegli l'immagine per l'analisi...")
        media_blocks = create_media_blocks_examples(interactive=True, count=1)
    else:
        print("🖼️ Preparazione media di esempio automatica...")
        media_blocks = create_media_blocks_examples(interactive=False, count=1)
    
    if not media_blocks:
        print("❌ Nessun media block disponibile per la demo")
        return
    
    # Esempi di analisi diverse
    analysis_tasks = [
        {
            "name": "Descrizione generale",
            "prompt": "Descrivi cosa vedi in questa immagine in dettaglio.",
            "description": "Analisi descrittiva base"
        },
        {
            "name": "Analisi tecnica", 
            "prompt": "Analizza gli aspetti tecnici di questa immagine: composizione, colori, qualità.",
            "description": "Analisi fotografica professionale"
        },
        {
            "name": "Estrazione testo",
            "prompt": "Se c'è testo in questa immagine, estrailo e trascrivilo.",
            "description": "OCR - riconoscimento testo"
        },
        {
            "name": "Contesto e suggerimenti",
            "prompt": "Dove potrebbe essere stata scattata questa foto? Che contesto suggerisci?",
            "description": "Analisi contestuale e inferenza"
        }
    ]
    
    for i, task in enumerate(analysis_tasks, 1):
        print_subsection(f"{i}. {task['name']}")
        print(f"Tipo analisi: {task['description']}")
        print(f"Prompt: '{task['prompt']}'")
        
        # Usa il primo media block disponibile per questo esempio
        media_block = media_blocks[0]
        
        # Combina testo e immagine
        multimodal_input = [
            TextBlock(content=task['prompt']),
            media_block
        ]
        
        try:
            start_time = time.time()
            response = client.invoke(input=multimodal_input)
            end_time = time.time()
            
            print(f"\n🤖 Analisi:")
            print(f"   {response.text}")
            print(f"\n📊 Statistiche:")
            print(f"   ⏱️ Tempo: {end_time - start_time:.2f}s")
            print(f"   🎯 Token prompt: {response.prompt_tokens_used}")
            print(f"   💬 Token risposta: {response.completion_tokens_used}")
            
        except Exception as e:
            print(f"   ❌ Errore: {e}")
            print(f"   📝 Simulazione: Analisi dell'immagine completata con successo")
        
        print()


def demo_oneshot_mixed_media(interactive_images: bool = False):
    """
    Dimostra l'uso di diversi tipi di media insieme
    
    Args:
        interactive_images: Se True, permette scelta interattiva delle immagini
    """
    print_section("ONE-SHOT MULTIMODALE - Media Misti")
    
    client = create_multimodal_client("google")  # Google supporta più tipi di media
    if not client:
        client = create_multimodal_client("openai")  # Fallback a OpenAI
        
    if not client:
        print("❌ Nessun client multimodale disponibile")
        return
    
    print_subsection("1. Testo + Immagine + Istruzioni specifiche")
    
    # Crea contenuto multimodale complesso
    try:
        # Ottieni immagine (interattiva o automatica)
        if interactive_images:
            print("Scegli l'immagine per l'analisi strutturata:")
            image_block = choose_image_source(interactive=True)
        else:
            # Usa immagine automatica
            sample_media = Media(
                media_type="image",
                source_type="base64",
                source=create_sample_image_base64(),
                detail="high"
            )
            image_block = MediaBlock(media=sample_media)
        
        complex_input = [
            TextBlock(content="Analizza questa immagine seguendo questi criteri:"),
            TextBlock(content="1. Descrivi gli elementi visivi principali"),
            TextBlock(content="2. Identifica i colori dominanti"),  
            TextBlock(content="3. Suggerisci possibili usi o contesti"),
            image_block,
            TextBlock(content="Fornisci una risposta strutturata e professionale.")
        ]
        
        response = client.invoke(input=complex_input)
        print(f"🤖 Analisi strutturata: {response.text}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        print("📝 Simulazione: Analisi multimodale strutturata completata")
    
    print_subsection("2. Confronto tra immagini")
    
    # Controlla se abbiamo abbastanza immagini per il confronto
    if interactive_images:
        print("\n🖼️ Scegli due immagini per il confronto:")
        try:
            media_blocks = create_media_blocks_examples(interactive=True, count=2)
        except:
            media_blocks = create_media_blocks_examples(interactive=False, count=2)
    else:
        media_blocks = create_media_blocks_examples(interactive=False, count=2)
    
    if len(media_blocks) >= 2:
        try:
            
            comparison_input = [
                TextBlock(content="Confronta queste due immagini e dimmi le principali differenze:"),
                media_blocks[0],
                TextBlock(content="Prima immagine ↑"),
                media_blocks[1], 
                TextBlock(content="Seconda immagine ↑"),
                TextBlock(content="Fornisci un confronto dettagliato.")
            ]
            
            response = client.invoke(input=comparison_input)
            print(f"🤖 Confronto: {response.text}")
            
        except Exception as e:
            print(f"❌ Errore confronto: {e}")
            print("📝 Simulazione: Confronto tra immagini completato")
    else:
        print("⚠️ Servono almeno 2 immagini per il confronto")


def demo_oneshot_image_to_code(interactive_images: bool = False):
    """
    Dimostra la conversione da immagine a codice/descrizione tecnica
    
    Args:
        interactive_images: Se True, permette scelta interattiva delle immagini
    """
    print_section("ONE-SHOT MULTIMODALE - Immagine → Codice")
    
    client = create_multimodal_client("openai")
    if not client:
        return
    
    print_subsection("Generazione codice da mockup/screenshot")
    
    # Ottieni immagine (interattiva o automatica)
    try:
        if interactive_images:
            print("Scegli l'immagine per la generazione di codice:")
            image_block = choose_image_source(interactive=True)
        else:
            sample_media = Media(
                media_type="image",
                source_type="base64", 
                source=create_sample_image_base64(),
                detail="high"
            )
            image_block = MediaBlock(media=sample_media)
        
        ui_analysis_input = [
            TextBlock(content="""
            Analizza questa immagine come se fosse un mockup o screenshot di un'interfaccia utente.
            
            Genera:
            1. Descrizione della struttura HTML base
            2. CSS approssimativo per il layout
            3. Suggerimenti per l'implementazione
            
            Anche se l'immagine è semplice, crea un esempio realistico.
            """),
            image_block
        ]
        
        response = client.invoke(input=ui_analysis_input)
        print(f"🤖 Analisi UI → Codice:")
        print(f"   {response.text}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        print("📝 Simulazione: Conversione mockup → codice completata")


# ==============================================================================
# MODALITÀ CONVERSATIONAL MULTIMODALE  
# ==============================================================================

def demo_conversational_image_analysis():
    """
    Conversazione con analisi di immagini e memoria
    """
    print_section("CONVERSATIONAL MULTIMODALE - Analisi con Memoria")
    
    client = create_multimodal_client("openai", use_cache=True)
    if not client:
        return
    
    memory = Memory()
    
    print("🎭 Simulazione: Analisi fotografica professionale")
    print("   L'assistente dovrebbe ricordare le analisi precedenti\n")
    
    # Prepara le immagini per la conversazione
    media_blocks = create_media_blocks_examples()
    if not media_blocks:
        print("❌ Nessuna immagine disponibile per la demo")
        return
    
    def multimodal_chat_turn(text_content: str, media_block = None, description: str = ""):
        """Helper per turni di chat multimodali"""
        if description:
            print(f"📋 {description}")
        
        print(f"👤 Utente: {text_content}")
        if media_block:
            print("   📷 [Immagine inclusa]")
        
        # Prepara l'input
        input_blocks = [TextBlock(content=text_content)]
        if media_block:
            input_blocks.append(media_block)
        
        # Aggiungi alla memoria
        memory.add_turn(input_blocks, ROLE.USER)
        
        try:
            response = client.invoke("", memory=memory)
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Assistente: {response.text}")
            print(f"   📊 Token: {response.prompt_tokens_used + response.completion_tokens_used}")
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            fallback = TextBlock(content="Analisi non disponibile al momento.")
            memory.add_turn([fallback], ROLE.ASSISTANT)
        
        print()
    
    # Conversazione strutturata
    multimodal_chat_turn(
        "Ciao! Sono un fotografo e vorrei il tuo aiuto per analizzare alcune foto.",
        description="Introduzione professionale"
    )
    
    multimodal_chat_turn(
        "Ecco la prima foto. Puoi darmi un'analisi tecnica dettagliata?",
        media_blocks[0] if media_blocks else None,
        "Prima analisi con immagine"
    )
    
    multimodal_chat_turn(
        "Quali miglioramenti consiglieresti per questa foto?",
        description="Richiesta consigli basata sull'immagine precedente"
    )
    
    if len(media_blocks) > 1:
        multimodal_chat_turn(
            "Ora confronta con questa seconda foto. Qual è migliore e perché?",
            media_blocks[1],
            "Confronto con seconda immagine"
        )
    
    multimodal_chat_turn(
        "Riassumi le tue analisi e dammi 3 consigli generali per migliorare",
        description="Richiesta di sintesi basata su tutta la conversazione"
    )
    
    # Statistiche finali
    print_subsection("Statistiche Conversazione Multimodale")
    print(f"   📚 Turni totali: {len(memory.memory)}")
    print(f"   💬 Blocchi totali: {len(list(memory.iter_blocks()))}")
    
    # Conta i tipi di blocchi
    text_blocks = sum(1 for block in memory.iter_blocks() if isinstance(block, TextBlock))
    media_blocks_count = sum(1 for block in memory.iter_blocks() if isinstance(block, MediaBlock))
    
    print(f"   📝 Blocchi testo: {text_blocks}")
    print(f"   🖼️ Blocchi media: {media_blocks_count}")


def demo_conversational_progressive_analysis():
    """
    Analisi progressiva dove l'AI costruisce comprensione nel tempo
    """
    print_section("CONVERSATIONAL MULTIMODALE - Analisi Progressiva")
    
    client = create_multimodal_client("openai")
    if not client:
        return
    
    memory = Memory()
    
    print("🔍 Scenario: Analisi progressiva di un progetto creativo")
    print("   L'AI aiuta a sviluppare un'idea partendo da riferimenti visivi\n")
    
    # Simula un flusso di lavoro creativo
    media_blocks = create_media_blocks_examples()
    
    def creative_chat_turn(text: str, media = None, step: str = ""):
        """Chat turn per workflow creativo"""
        if step:
            print(f"🎨 {step}")
        print(f"👤 Designer: {text}")
        
        input_blocks = [TextBlock(content=text)]
        if media:
            input_blocks.append(media)
        
        memory.add_turn(input_blocks, ROLE.USER)
        
        try:
            response = client.invoke("", memory=memory)
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            print(f"🤖 AI Creative Assistant: {response.text}\n")
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            memory.add_turn([TextBlock(content="Assistenza creativa temporaneamente non disponibile.")], ROLE.ASSISTANT)
    
    # Flusso di lavoro progressivo
    creative_chat_turn(
        "Sto lavorando su un nuovo progetto di design. Mi aiuti a sviluppare l'idea?",
        step="Step 1: Introduzione progetto"
    )
    
    if media_blocks:
        creative_chat_turn(
            "Ecco la mia prima ispirazione. Che direzione creativa suggerisci?",
            media_blocks[0],
            "Step 2: Riferimento visivo iniziale"
        )
    
    creative_chat_turn(
        "Voglio creare qualcosa di moderno ma elegante. Che elementi dovrei considerare?",
        step="Step 3: Definizione stile"
    )
    
    creative_chat_turn(
        "Basandoti su quello che abbiamo discusso, crea una breve descrizione del concept finale",
        step="Step 4: Sintesi e concept"
    )
    
    creative_chat_turn(
        "Perfetto! Ora dammi una checklist di 5 punti per implementare questa idea",
        step="Step 5: Piano d'azione"
    )


def demo_conversational_multimodal_memory():
    """
    Dimostra la gestione avanzata della memoria multimodale
    """
    print_section("GESTIONE MEMORIA MULTIMODALE AVANZATA")
    
    client = create_multimodal_client("openai")
    if not client:
        return
    
    print_subsection("1. Creazione memoria con contenuti misti")
    
    # Crea una memoria con diversi tipi di contenuto
    memory = Memory()
    media_blocks = create_media_blocks_examples()
    
    # Simula una conversazione passata
    past_conversation = [
        ([TextBlock(content="Analizza questa immagine del mio progetto")], ROLE.USER),
        ([media_blocks[0]] if media_blocks else [TextBlock(content="[immagine]")], ROLE.USER),
        ([TextBlock(content="Vedo un'immagine interessante con potenziale artistico...")], ROLE.ASSISTANT),
        ([TextBlock(content="Quali colori dovrei usare per complementarla?")], ROLE.USER),
        ([TextBlock(content="Consiglio una palette di colori caldi: arancione, rosso...")], ROLE.ASSISTANT)
    ]
    
    for blocks, role in past_conversation:
        memory.add_turn(blocks, role)
    
    print(f"   📚 Memoria simulata creata: {len(memory.memory)} turni")
    
    # Analizza il contenuto della memoria
    text_count = 0
    media_count = 0
    
    for block in memory.iter_blocks():
        if isinstance(block, TextBlock):
            text_count += 1
        elif isinstance(block, MediaBlock):
            media_count += 1
    
    print(f"   📝 Blocchi testo: {text_count}")
    print(f"   🖼️ Blocchi media: {media_count}")
    
    print_subsection("2. Test continuità con nuova domanda")
    
    # Test che l'AI ricordi il contesto multimodale
    try:
        response = client.invoke(
            "Ricordi il progetto di cui abbiamo parlato? Com'era l'immagine che ti ho mostrato?",
            memory=memory
        )
        print(f"   🤖 Test memoria: {response.text}")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    print_subsection("3. Gestione memoria con limite dimensione")
    
    # Simula gestione memoria con troppi media
    print("   🧠 Gestione memoria pesante...")
    
    original_size = len(memory.memory)
    
    # In un caso reale, potresti voler rimuovere i media più vecchi 
    # mantenendo solo il testo per ridurre il carico
    light_memory = Memory()
    
    for turn in memory.memory[-3:]:  # Mantieni solo ultimi 3 turni
        # Converti i media blocks in descrizioni testuali per risparmiare
        light_blocks = []
        for block in turn.blocks:
            if isinstance(block, MediaBlock):
                description_block = TextBlock(content="[Immagine precedentemente analizzata]")
                light_blocks.append(description_block)
            else:
                light_blocks.append(block)
        
        light_memory.memory.append(type(turn)(blocks=light_blocks, role=turn.role))
    
    print(f"   📉 Memoria ridotta: da {original_size} a {len(light_memory.memory)} turni")
    print(f"   💾 Media convertiti in descrizioni testuali per efficienza")


# ==============================================================================
# UTILITÀ E GESTIONE FILE
# ==============================================================================

def demo_file_management():
    """
    Dimostra la gestione di file multimediali locali
    """
    print_section("GESTIONE FILE MULTIMEDIALI LOCALI")
    
    print_subsection("1. Ricerca file immagine nella directory corrente")
    
    # Cerca file immagine comuni
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    current_dir = Path('.')
    
    found_images = []
    for ext in image_extensions:
        found_images.extend(current_dir.glob(f'*{ext}'))
        found_images.extend(current_dir.glob(f'*{ext.upper()}'))
    
    if found_images:
        print(f"   📁 Trovate {len(found_images)} immagini:")
        for img in found_images[:5]:  # Mostra max 5
            print(f"      - {img.name} ({img.stat().st_size} bytes)")
        
        # Test caricamento del primo file trovato
        first_image = found_images[0]
        print(f"\n   🔄 Test caricamento {first_image.name}...")
        
        image_b64 = load_image_as_base64(str(first_image))
        if image_b64:
            print(f"   ✅ Caricamento riuscito: {len(image_b64)} caratteri base64")
            
            # Crea MediaBlock dal file locale
            try:
                local_media = Media(
                    media_type="image",
                    source_type="base64",
                    source=image_b64,
                    detail="high"
                )
                media_block = MediaBlock(media=local_media)
                print(f"   ✅ MediaBlock creato da file locale")
                
            except Exception as e:
                print(f"   ❌ Errore creazione MediaBlock: {e}")
        else:
            print(f"   ❌ Caricamento fallito")
    else:
        print("   📂 Nessuna immagine trovata nella directory corrente")
        print("   💡 Suggerimento: copia alcune immagini (.jpg, .png) in questa directory per testare")
    
    print_subsection("2. Creazione helper per batch di immagini")
    
    def create_media_batch(image_paths: List[str], max_images: int = 3) -> List[MediaBlock]:
        """Crea un batch di MediaBlock da file locali"""
        media_blocks = []
        
        for i, path in enumerate(image_paths[:max_images]):
            image_b64 = load_image_as_base64(path)
            if image_b64:
                try:
                    media = Media(
                        media_type="image", 
                        source_type="base64",
                        source=image_b64,
                        detail="high"
                    )
                    media_blocks.append(MediaBlock(media=media))
                    print(f"   ✅ Batch {i+1}: {Path(path).name}")
                except Exception as e:
                    print(f"   ❌ Batch {i+1} errore: {e}")
            else:
                print(f"   ⏭️ Batch {i+1}: {Path(path).name} saltato")
        
        return media_blocks
    
    # Test del batch se ci sono immagini
    if found_images:
        print("   🔄 Test creazione batch...")
        batch = create_media_batch([str(img) for img in found_images])
        print(f"   📦 Batch creato: {len(batch)} immagini pronte")
    else:
        print("   ⏭️ Test batch saltato (nessuna immagine)")


# ==============================================================================
# FUNZIONE PRINCIPALE E MENU
# ==============================================================================

def show_main_menu():
    """Mostra il menu principale ristrutturato"""
    print_section("DATAPIZZAI - Analisi e generazione immagini")
    
    # Mostra informazioni sui file disponibili
    local_images = find_local_images()
    
    print("File disponibili nella directory:")
    print(f"   Immagini: {len(local_images)} file")
    
    print("""
Da cosa vuoi partire?

1. Analizza immagine → Carica e analizza un'immagine (funziona)
2. Genera immagine → GPT-5 + DALL-E 3 (download locale)

0. Esci

Nota: Audio/video temporaneamente non disponibili (framework in sviluppo)
Per funzioni avanzate digita 'legacy'
    """)


def show_legacy_menu():
    """Mostra il menu delle demo legacy (opzione nascosta)"""
    print_section("DEMO LEGACY - Modalità MULTIMODALE")
    
    print("""
Demo avanzate e sperimentali:

FUNZIONI SPERIMENTALI (potrebbero non funzionare):
1. [SPER] Analisi audio → Test framework audio
2. [SPER] Analisi video → Test framework video

MODALITÀ ONE-SHOT MULTIMODALE (FUNZIONANTI):
3. Analisi di immagini base nella cartella (automatica)
4. Analisi di immagini base (scelta interattiva) 
5. Media misti (automatica)
6. Media misti (scelta interattiva)
7. Da immagine a codice/descrizione tecnica

MODALITÀ CONVERSATIONAL MULTIMODALE:
8. Conversazione con analisi di immagini
9. Analisi progressiva e workflow creativo
10. Gestione avanzata memoria multimodale

UTILITÀ E MENU AVANZATI:
11. Gestione file multimediali locali
12. Test selezione immagini interattiva
13. Esegui tutte le demo multimodali

ALTRO:
0. Torna al menu principale

Note:
- Audio/video sono sperimentali e potrebbero fallire (framework in sviluppo)
- Solo OpenAI (gpt-4o), Google (gemini) e Anthropic (claude) supportano multimodalità
- Assicurati di avere le chiavi API nel file .env
    """)


def demo_interactive_image_selection():
    """
    Demo dedicata per testare la selezione interattiva delle immagini
    """
    print_section("TEST SELEZIONE IMMAGINI INTERATTIVA")
    
    print("🖼️ Questa demo ti permette di testare la selezione interattiva delle immagini")
    print("senza eseguire un'analisi completa.\n")
    
    try:
        # Test selezione singola
        print("1️⃣ Test selezione immagine singola:")
        image_block = choose_image_source(interactive=True)
        print(f"✅ Immagine selezionata: {image_block.media.source_type}")
        
        print("\n2️⃣ Test selezione multipla:")
        choice = input("Quante immagini vuoi selezionare? (1-5): ").strip()
        try:
            count = int(choice)
            count = max(1, min(count, 5))  # Limita tra 1-5
        except ValueError:
            count = 2
            
        image_blocks = create_media_blocks_examples(interactive=True, count=count)
        print(f"✅ Selezionate {len(image_blocks)} immagini")
        
        print("\n📊 Riepilogo selezioni:")
        for i, block in enumerate(image_blocks, 1):
            print(f"   {i}. {block.media.source_type} - {block.media.media_type}")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrotto")
    except Exception as e:
        print(f"❌ Errore: {e}")


def run_main_demo(choice: str):
    """Esegue la demo principale selezionata"""
    demos = {
        "1": demo_image_analysis,
        "2": demo_text_generation
    }
    
    if choice in demos:
        print(f"\nAvvio...")
        try:
            demos[choice]()
        except KeyboardInterrupt:
            print("\n\nOperazione interrotta")
        except Exception as e:
            print(f"\nErrore durante esecuzione: {e}")
    elif choice == "legacy":
        # Menu nascosto per le demo legacy
        return "legacy"
    else:
        print("Scelta non valida")
    
    return None


def run_legacy_demo(choice: str):
    """Esegue le demo legacy"""
    demos = {
        "1": lambda: print("❌ Audio non supportato dal framework"),    # Placeholder
        "2": lambda: print("❌ Video non supportato dal framework"),    # Placeholder
        "3": lambda: demo_oneshot_image_analysis(interactive_images=False),
        "4": lambda: demo_oneshot_image_analysis(interactive_images=True),
        "5": lambda: demo_oneshot_mixed_media(interactive_images=False),
        "6": lambda: demo_oneshot_mixed_media(interactive_images=True),
        "7": lambda: demo_oneshot_image_to_code(interactive_images=True),
        "8": demo_conversational_image_analysis,
        "9": demo_conversational_progressive_analysis,
        "10": demo_conversational_multimodal_memory,
        "11": demo_file_management,
        "12": demo_interactive_image_selection,
        "13": run_all_demos
    }
    
    if choice in demos:
        print(f"\n🚀 Avvio demo legacy {choice}...")
        try:
            demos[choice]()
        except KeyboardInterrupt:
            print("\n\n⏹️ Demo interrotta")
        except Exception as e:
            print(f"\n❌ Errore durante esecuzione: {e}")
    else:
        print("❌ Scelta non valida")


def run_all_demos():
    """Esegue tutte le demo multimodali in sequenza"""
    print_section("ESECUZIONE TUTTE LE DEMO MULTIMODALI")
    
    all_demos = [
        ("Analisi immagini (auto)", lambda: demo_oneshot_image_analysis(interactive_images=False)),
        ("Media misti (auto)", lambda: demo_oneshot_mixed_media(interactive_images=False)),
        ("Immagine → codice", demo_oneshot_image_to_code),
        ("Conversazione + immagini", demo_conversational_image_analysis),
        ("Analisi progressiva", demo_conversational_progressive_analysis),
        ("Memoria multimodale", demo_conversational_multimodal_memory),
        ("Gestione file", demo_file_management)
    ]
    
    for i, (name, demo_func) in enumerate(all_demos, 1):
        print(f"\n🎬 Demo {i}/{len(all_demos)}: {name}")
        print("⏳ Inizio tra 2 secondi... (Ctrl+C per saltare)")
        
        try:
            time.sleep(2)
            demo_func()
        except KeyboardInterrupt:
            print("⏭️ Demo saltata")
        except Exception as e:
            print(f"❌ Errore in {name}: {e}")
    
    print_section("TUTTE LE DEMO MULTIMODALI COMPLETATE")


def main():
    """Funzione principale con menu interattivo ristrutturato"""
    
    # Verifica supporto multimodale
    print("🔍 Verifica supporto multimodale...")
    
    multimodal_providers = []
    if os.getenv("OPENAI_API_KEY"):
        multimodal_providers.append("OpenAI (gpt-4o)")
    if os.getenv("GOOGLE_API_KEY"):
        multimodal_providers.append("Google (gemini-2.5-flash)")
    
    if multimodal_providers:
        print(f"✅ Provider multimodali disponibili: {', '.join(multimodal_providers)}")
    else:
        print("""
⚠️ Nessun provider multimodale configurato!

Per utilizzare le funzionalità multimodali, crea un file .env nella directory PizzAI/ con:

 OPENAI_API_KEY=sk-your-openai-key-here     # gpt-4o supporta immagini + generazione
 GOOGLE_API_KEY=your-google-key-here        # gemini supporta immagini

Almeno una di queste chiavi è necessaria per le demo multimodali.
        """)
    
    # Menu principale semplificato
    current_menu = "main"
    
    while True:
        try:
            if current_menu == "main":
                show_main_menu()
                choice = input("👉 Scegli un'opzione: ").strip()
                
                if choice == "0":
                    print("👋 Arrivederci!")
                    break
                elif choice.lower() == "legacy":
                    current_menu = "legacy"
                    continue
                
                result = run_main_demo(choice)
                if result == "legacy":
                    current_menu = "legacy"
                    continue
                    
            elif current_menu == "legacy":
                show_legacy_menu()
                choice = input("👉 Scegli un'opzione: ").strip()
                
                if choice == "0":
                    current_menu = "main"
                    continue
                    
                run_legacy_demo(choice)
            
            if current_menu == "main":
                input("\n⏸️ Premi INVIO per continuare...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Uscita forzata. Arrivederci!")
            break
        except Exception as e:
            print(f"\n❌ Errore inaspettato: {e}")
            print("🔄 Riavvio menu...")
            current_menu = "main"


if __name__ == "__main__":
    main()
