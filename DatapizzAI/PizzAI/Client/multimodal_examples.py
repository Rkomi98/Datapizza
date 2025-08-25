#!/usr/bin/env python3
"""
Script di esempio per l'uso della libreria datapizzai - Modalità MULTIMODALE  
==========================================================================

Questo script dimostra come utilizzare datapizzai per contenuti multimodali:
1. Analisi immagini con OpenAI (gpt-4o) e Google (gemini-2.5-flash)
2. Generazione immagini con GPT-5 + DALL-E 3
3. Modalità conversazionale con memoria multimodale

Supporta:
- Testo + Immagini (URL, base64, file locali)
- Analisi dettagliate e tecniche
- Generazione immagini con prompt augmentato
- Conversazioni multi-turno con media

Autore: Marco Calcaterra  
Data: 2025
"""

import os
import time
import base64
import requests
from pathlib import Path
from typing import List, Union, Optional
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


def create_multimodal_client(provider_name: str = "openai", use_cache: bool = False) -> Optional[object]:
    """
    Crea un client che supporta contenuti multimodali
    
    Args:
        provider_name: "openai" o "google"
        use_cache: Se abilitare la cache (solo OpenAI)
        
    Returns:
        Client configurato o None se errore
    """
    
    # Provider che supportano analisi immagini
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
            system_prompt="Sei un assistente AI multimodale specializzato nell'analisi di immagini. Rispondi in italiano in modo dettagliato e professionale.",
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


def load_image_as_base64(image_path: str) -> Optional[str]:
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


def choose_image_source(interactive: bool = True) -> MediaBlock:
    """
    Permette di scegliere tra immagine locale o dal web
    
    Args:
        interactive: Se True, mostra menu interattivo. Se False, usa default.
        
    Returns:
        MediaBlock con l'immagine scelta
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
    
    options = []
    
    # Aggiungi file locali
    if local_images:
        print(f"📁 File immagine locali disponibili:")
        for file_path in local_images:
            file_size = Path(file_path).stat().st_size
            print(f"   {len(options) + 1}. {Path(file_path).name} ({file_size:,} bytes)")
            options.append(("local", file_path))
    
    # Aggiungi opzioni web
    print(f"\n🌐 Immagini di esempio dal web:")
    for web_option in web_images:
        print(f"   {len(options) + 1}. {web_option['name']}")
        options.append(("web", web_option["url"]))
    
    # Opzione di esempio
    print(f"   {len(options) + 1}. Pixel di esempio (1x1 trasparente)")
    options.append(("sample", None))
    
    # Input utente
    while True:
        try:
            choice = input(f"\n👉 Scegli un'immagine (1-{len(options)}): ").strip()
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
            return create_mediablock_from_file(source_value)
        elif source_type == "web":
            return create_mediablock_from_url(source_value)
        elif source_type == "sample":
            return create_sample_mediablock()
    except Exception as e:
        print(f"❌ Errore caricamento: {e}")
        print("🔄 Fallback a immagine di esempio...")
        return create_sample_mediablock()


def create_mediablock_from_file(file_path: str) -> MediaBlock:
    """Crea MediaBlock da file locale"""
    image_b64 = load_image_as_base64(file_path)
    if not image_b64:
        raise ValueError(f"Impossibile caricare {file_path}")
    
    # Determina l'extension dal file (senza punto per MIME type)
    file_ext = Path(file_path).suffix.lower()
    if not file_ext:
        file_ext = ".png"  # Default fallback
    
    # Rimuovi il punto per MIME type corretto
    extension_clean = file_ext.lstrip('.')
    
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


def _select_provider(default: str = "openai") -> str:
    """Selezione provider funzionanti"""
    options = {"1": "openai", "2": "google"}
    labels = {"1": "OpenAI (gpt-4o)", "2": "Google (gemini-2.5-flash)"}
    print("\nSeleziona provider:")
    for k in ["1", "2"]:
        print(f" {k}. {labels[k]}")
    choice = input("\nScelta (1-2, invio per OpenAI): ").strip()
    return options.get(choice, default)


# ==============================================================================
# FUNZIONALITÀ PRINCIPALI
# ==============================================================================

def demo_image_analysis():
    """
    Analizza un'immagine scelta dall'utente
    """
    print_section("ANALISI IMMAGINE")
    
    provider = _select_provider("openai")
    client = create_multimodal_client(provider, use_cache=True)
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


def demo_image_generation():
    """
    Genera immagini usando GPT-5 per augmentazione + DALL-E 3 per generazione
    """
    print_section("GENERAZIONE IMMAGINE - GPT-5 + DALL-E 3")

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

        # Client per augmentazione prompt (GPT-5)
        final_description = description
        if augment:
            try:
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
            except Exception as e:
                print(f"⚠️ Errore augmentazione GPT-5: {e}")
                print("💡 Uso prompt originale")

        # Genera immagine con DALL-E 3
        print("\n🔄 Generazione immagine con DALL-E 3...")
        
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
            print(f"✅ Immagine generata con DALL-E 3!")
            print(f"🔗 URL: {image_url}")
            
            # Scarica e salva l'immagine in locale
            print("\n🔄 Download immagine in corso...")
            try:
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
                
        except ImportError:
            print("❌ Modulo 'openai' non installato")
            print("💡 Installa con: pip install openai")
        except Exception as e:
            print(f"❌ Errore DALL-E 3: {e}")
        
    except Exception as e:
        print(f"❌ Errore generazione: {e}")


def demo_conversational_analysis():
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
    
    # Prepara l'immagine per la conversazione
    try:
        image_block = choose_image_source(interactive=True)
    except Exception as e:
        print(f"❌ Errore selezione immagine: {e}")
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
        image_block,
        "Prima analisi con immagine"
    )
    
    multimodal_chat_turn(
        "Quali miglioramenti consiglieresti per questa foto?",
        description="Richiesta consigli basata sull'immagine precedente"
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


def demo_file_management():
    """
    Dimostra la gestione di file multimediali locali
    """
    print_section("GESTIONE FILE MULTIMEDIALI LOCALI")
    
    print_subsection("1. Ricerca file immagine nella directory corrente")
    
    # Cerca file immagine comuni
    found_images = find_local_images()
    
    if found_images:
        print(f"   📁 Trovate {len(found_images)} immagini:")
        for img in found_images[:5]:  # Mostra max 5
            img_path = Path(img)
            print(f"      - {img_path.name} ({img_path.stat().st_size} bytes)")
        
        # Test caricamento del primo file trovato
        first_image = found_images[0]
        print(f"\n   🔄 Test caricamento {Path(first_image).name}...")
        
        image_b64 = load_image_as_base64(first_image)
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
    """Mostra il menu principale"""
    print_section("DATAPIZZAI - Analisi e generazione immagini")
    
    # Mostra informazioni sui file disponibili
    local_images = find_local_images()
    
    print("File disponibili nella directory:")
    print(f"   Immagini: {len(local_images)} file")
    
    print("""
Da cosa vuoi partire?

1. Analizza immagine → Carica e analizza un'immagine
2. Genera immagine → GPT-5 + DALL-E 3 (download locale)
3. Conversazione multimodale → Analisi con memoria
4. Gestione file → Esplora immagini locali

0. Esci
    """)


def run_main_demo(choice: str):
    """Esegue la demo principale selezionata"""
    demos = {
        "1": demo_image_analysis,
        "2": demo_image_generation,
        "3": demo_conversational_analysis,
        "4": demo_file_management
    }
    
    if choice in demos:
        print(f"\nAvvio...")
        try:
            demos[choice]()
        except KeyboardInterrupt:
            print("\n\nOperazione interrotta")
        except Exception as e:
            print(f"\nErrore durante esecuzione: {e}")
    else:
        print("Scelta non valida")


def main():
    """Funzione principale con menu interattivo"""
    
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
    
    # Menu principale
    while True:
        try:
            show_main_menu()
            choice = input("👉 Scegli un'opzione: ").strip()
            
            if choice == "0":
                print("👋 Arrivederci!")
                break
            
            run_main_demo(choice)
            
            input("\n⏸️ Premi INVIO per continuare...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Uscita forzata. Arrivederci!")
            break
        except Exception as e:
            print(f"\n❌ Errore inaspettato: {e}")
            print("🔄 Riavvio menu...")


if __name__ == "__main__":
    main()
