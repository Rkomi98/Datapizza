# Guida completa: DatapizzAI multimodale

Una guida tecnica per utilizzare le funzionalità di analisi immagini e generazione con GPT-5 + DALL-E 3 del framework DatapizzAI.

## Indice

1. [Setup e configurazione](#1-setup-e-configurazione)
2. [Client supportati](#2-client-supportati)
3. [Analisi immagini](#3-analisi-immagini)
4. [Generazione immagini](#4-generazione-immagini)
5. [Esempio completo](#5-esempio-completo)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Setup e configurazione

### Prerequisiti

```bash
# Attiva l'ambiente virtuale
source .venv/bin/activate
```

### Configurazione delle API keys

Crea un file `.env` nella directory `PizzAI/`:

```bash
# File .env - OPENAI_API_KEY richiesta per tutte le funzioni
OPENAI_API_KEY=sk-your-openai-api-key-here  # Richiesta (gpt-4o, gpt-5, dall-e-3)
GOOGLE_API_KEY=your-google-api-key-here     # Opzionale (solo per analisi con Gemini)
```

### Import necessari

```python
import os
import base64
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv('../.env')

# Import DatapizzAI
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media

# Import OpenAI per DALL-E 3
import openai
```

---

## 2. Client supportati

### Configurazione client

```python
def create_analysis_client(provider: str = "openai"):
    """
    Crea un client per l'analisi immagini
    
    Args:
        provider: "openai" o "google"
    
    Returns:
        Client configurato per analisi
    """
    
    models = {
        "openai": "gpt-4o",
        "google": "gemini-2.5-flash"
    }
    
    api_key = os.getenv("OPENAI_API_KEY" if provider == "openai" else "GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(f"API key non trovata per {provider}")
    
    return ClientFactory.create(
        provider=provider,
        api_key=api_key,
        model=models[provider],
        temperature=0.7
    )

def create_gpt5_client():
    """
    Crea un client GPT-5 per augmentazione prompt
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY richiesta per GPT-5")
    
    return ClientFactory.create(
        provider="openai",
        api_key=api_key,
        model="gpt-5",
        temperature=1.0  # GPT-5 supporta solo temperature=1.0
    )
```

### Caratteristiche dei provider

| Provider | Modello | Analisi immagini | Augmentazione prompt | Generazione immagini | Cache |
|----------|---------|------------------|-------------------|-------------------|-------|
| OpenAI | gpt-4o | ✅ | ❌ | ❌ | ✅ |
| OpenAI | gpt-5 | ❌ | ✅ | ❌ | ❌ |
| OpenAI | dall-e-3 | ❌ | ❌ | ✅ | ❌ |
| Google | gemini-2.5-flash | ✅ | ❌ | ❌ | ❌ |

**Note:**
- **gpt-4o**: Migliore per analisi dettagliate, supporta cache
- **gpt-5**: Eccellente per augmentazione prompt, solo temperature=1.0
- **dall-e-3**: Generazione immagini di alta qualità, download automatico
- **gemini-2.5-flash**: Alternativa veloce per analisi, nessuna cache

---

## 3. Analisi immagini

### Analisi da file locale

```python
def analyze_local_image(file_path: str, question: str = "Descrivi questa immagine"):
    """
    Analizza un'immagine da file locale
    
    Args:
        file_path: Path al file immagine
        question: Domanda da porre sull'immagine
    
    Returns:
        str: Risposta del modello
    """
    
    # Verifica esistenza file
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File non trovato: {file_path}")
    
    # Carica immagine in base64
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Crea oggetto Media
    media = Media(
        extension=Path(file_path).suffix or ".jpg",
        media_type="image",
        source_type="base64",
        source=image_data,
        detail="high"
    )
    
    # Analizza
    client = create_client("openai")
    response = client.invoke([
        TextBlock(content=question),
        MediaBlock(media=media)
    ])
    
    return response.text

# Esempio d'uso
try:
    result = analyze_local_image("example.jpg", "Cosa vedi in questa immagine?")
    print(result)
except Exception as e:
    print(f"Errore: {e}")
```

### Analisi da URL

```python
def analyze_web_image(url: str, question: str = "Descrivi questa immagine"):
    """
    Analizza un'immagine da URL web
    
    Args:
        url: URL dell'immagine
        question: Domanda da porre sull'immagine
    
    Returns:
        str: Risposta del modello
    """
    
    media = Media(
        extension=".jpg",  # Estensione di default per URL
        media_type="image",
        source_type="url",
        source=url,
        detail="high"
    )
    
    client = create_client("google")  # Google ottimizzato per analisi da URL
    response = client.invoke([
        TextBlock(content=question),
        MediaBlock(media=media)
    ])
    
    return response.text

# Esempio d'uso
url = "https://example.com/image.jpg"
analysis = analyze_web_image(url, "Identifica gli elementi presenti nell'immagine")
print(analysis)
```

### Ricerca immagini locali

```python
def find_local_images(directory: str = ".") -> list:
    """
    Trova tutte le immagini in una directory
    
    Args:
        directory: Directory da cercare (default: directory corrente)
    
    Returns:
        list: Lista di path alle immagini trovate
    """
    
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    images = []
    
    for ext in image_extensions:
        images.extend(Path(directory).glob(f"*{ext}"))
        images.extend(Path(directory).glob(f"*{ext.upper()}"))
    
    return [str(img) for img in sorted(images)]

# Esempio d'uso
local_images = find_local_images()
print(f"Immagini trovate: {len(local_images)}")
for img in local_images:
    print(f"  - {img}")
```

---

## 4. Generazione immagini

### Generazione completa con GPT-5 + DALL-E 3

Il sistema ottimale combina **GPT-5** per l'augmentazione del prompt e **DALL-E 3** per la generazione, con download automatico in locale.

```python
import openai
import requests

def generate_image_complete(prompt: str, enhance_prompt: bool = True, 
                          size: str = "1024x1024", quality: str = "standard"):
    """
    Genera un'immagine con augmentazione GPT-5 + DALL-E 3 + download locale
    
    Args:
        prompt: Descrizione dell'immagine da generare
        enhance_prompt: Se usare GPT-5 per migliorare il prompt
        size: Dimensioni ("1024x1024", "1792x1024", "1024x1792")
        quality: Qualità ("standard" o "hd")
    
    Returns:
        tuple: (image_url, local_filename, enhanced_prompt)
    """
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY non configurata")
    
    final_prompt = prompt
    
    # 1. Augmentazione prompt con GPT-5 (opzionale)
    if enhance_prompt:
        try:
            gpt5_client = create_gpt5_client()
            
            augment_request = f"""Migliora questo prompt per DALL-E 3: "{prompt}"

Aggiungi dettagli su:
- Stile visivo e colori specifici
- Composizione e prospettiva
- Elementi decorativi e atmosfera
- Qualità artistica e tecnica fotografica

Rispondi solo con il prompt migliorato, max 400 caratteri."""

            response = gpt5_client.invoke(augment_request)
            final_prompt = response.text.strip()
            print(f"✅ Prompt augmentato con GPT-5: {final_prompt}")
            
        except Exception as e:
            print(f"⚠️ GPT-5 non disponibile: {e}")
            print("🔄 Uso prompt originale")
    
    # 2. Generazione immagine con DALL-E 3
    dalle_client = openai.OpenAI(api_key=api_key)
    
    try:
        response = dalle_client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            size=size,
            quality=quality,
            n=1
        )
        
        image_url = response.data[0].url
        print(f"✅ Immagine generata con DALL-E 3: {image_url}")
        
        # 3. Download automatico in locale
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        
        filename = f"generated_image_{int(time.time())}.png"
        with open(filename, "wb") as f:
            f.write(img_response.content)
        
        print(f"✅ Immagine salvata: {filename} ({len(img_response.content):,} bytes)")
        
        return image_url, filename, final_prompt
        
    except Exception as e:
        raise Exception(f"Errore generazione: {e}")

# Esempio d'uso completo
try:
    url, file, enhanced = generate_image_complete(
        "Una ragazza tunisina in una strada di Tunisi",
        enhance_prompt=True,
        quality="hd"
    )
    
    print(f"🎨 Prompt originale: Una ragazza tunisina...")
    print(f"🚀 Prompt migliorato: {enhanced}")
    print(f"🔗 URL: {url}")
    print(f"📁 File locale: {file}")
    
except Exception as e:
    print(f"❌ Errore: {e}")
```

### Generazione base con solo DALL-E 3

```python
def generate_enhanced_image(description: str):
    """
    Genera un'immagine migliorando prima il prompt con AI
    
    Args:
        description: Descrizione base dell'immagine
    
    Returns:
        dict: Contiene URL immagine e prompt migliorato
    """
    
    # Step 1: Migliora il prompt
    client = create_client("openai")
    enhanced_prompt = client.invoke(
        f"Migliora questo prompt per DALL-E 3: '{description}'. "
        f"Aggiungi dettagli su stile, lighting, composizione e qualità. "
        f"Rispondi solo con il prompt migliorato, senza spiegazioni."
    ).text
    
    # Step 2: Genera l'immagine
    image_url = generate_image(enhanced_prompt, quality="hd")
    
    return {
        "url": image_url,
        "enhanced_prompt": enhanced_prompt,
        "original_description": description
    }

# Esempio d'uso
result = generate_enhanced_image("Un robot in una cucina")
print(f"Prompt originale: {result['original_description']}")
print(f"Prompt migliorato: {result['enhanced_prompt']}")
print(f"Immagine: {result['url']}")
```

### Salvataggio locale delle immagini

```python
import requests
import time

def save_generated_image(image_url: str, filename: str = None):
    """
    Salva un'immagine generata in locale
    
    Args:
        image_url: URL dell'immagine da salvare
        filename: Nome del file (opzionale, genera timestamp se None)
    
    Returns:
        str: Path del file salvato
    """
    
    if filename is None:
        timestamp = int(time.time())
        filename = f"generated_image_{timestamp}.png"
    
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"Immagine salvata: {filename}")
        return filename
    
    except Exception as e:
        raise Exception(f"Errore salvataggio: {e}")

# Esempio d'uso completo
description = "Un paesaggio montano al tramonto"
result = generate_enhanced_image(description)
saved_file = save_generated_image(result['url'])
print(f"File salvato: {saved_file}")
```

---

## 5. Esempio completo

### Applicazione completa

```python
#!/usr/bin/env python3
"""
DatapizzAI - Esempio completo di analisi e generazione immagini
"""

import os
import base64
import requests
import time
from pathlib import Path
from dotenv import load_dotenv
import openai

# Setup
load_dotenv('../.env')
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media

class ImageProcessor:
    """Classe per processare immagini con DatapizzAI"""
    
    def __init__(self, default_provider: str = "openai"):
        self.default_provider = default_provider
        self._clients = {}
    
    def get_client(self, provider: str = None):
        """Ottieni client per provider specificato"""
        if provider is None:
            provider = self.default_provider
        
        if provider not in self._clients:
            models = {
                "openai": "gpt-4o",
                "google": "gemini-2.5-flash",
                "anthropic": "claude-3-5-sonnet-latest"
            }
            
            api_key = os.getenv(f"{provider.upper()}_API_KEY")
            if not api_key:
                raise ValueError(f"API key mancante per {provider}")
            
            self._clients[provider] = ClientFactory.create(
                provider=provider,
                api_key=api_key,
                model=models[provider]
            )
        
        return self._clients[provider]
    
    def analyze_image(self, source: str, question: str = "Descrivi questa immagine"):
        """
        Analizza un'immagine (locale o web)
        
        Args:
            source: Path file locale o URL web
            question: Domanda sull'immagine
        
        Returns:
            str: Analisi dell'immagine
        """
        
        if source.startswith('http'):
            # URL web
            media = Media(
                extension=".jpg",
                media_type="image",
                source_type="url",
                source=source,
                detail="high"
            )
        else:
            # File locale
            if not Path(source).exists():
                raise FileNotFoundError(f"File non trovato: {source}")
            
            with open(source, "rb") as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            media = Media(
                extension=Path(source).suffix or ".jpg",
                media_type="image",
                source_type="base64",
                source=image_data,
                detail="high"
            )
        
        client = self.get_client()
        response = client.invoke([
            TextBlock(content=question),
            MediaBlock(media=media)
        ])
        
        return response.text
    
    def generate_image(self, description: str, enhance_prompt: bool = True, save_local: bool = False):
        """
        Genera un'immagine da testo
        
        Args:
            description: Descrizione dell'immagine
            enhance_prompt: Se migliorare il prompt con AI
            save_local: Se salvare l'immagine localmente
        
        Returns:
            dict: Risultati della generazione
        """
        
        # Migliora prompt se richiesto
        if enhance_prompt:
            client = self.get_client()
            enhanced_description = client.invoke(
                f"Migliora questo prompt per DALL-E 3: '{description}'. "
                f"Aggiungi dettagli tecnici per qualità professionale. "
                f"Rispondi solo con il prompt migliorato."
            ).text
        else:
            enhanced_description = description
        
        # Genera immagine
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY richiesta per generazione")
        
        openai_client = openai.OpenAI(api_key=api_key)
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=enhanced_description,
            size="1024x1024",
            quality="hd"
        )
        
        image_url = response.data[0].url
        result = {
            "url": image_url,
            "original_prompt": description,
            "enhanced_prompt": enhanced_description if enhance_prompt else None
        }
        
        # Salva localmente se richiesto
        if save_local:
            timestamp = int(time.time())
            filename = f"generated_{timestamp}.png"
            
            img_response = requests.get(image_url)
            with open(filename, 'wb') as f:
                f.write(img_response.content)
            
            result["saved_file"] = filename
        
        return result

def main():
    """Esempio di utilizzo"""
    processor = ImageProcessor()
    
    print("DatapizzAI - Processore immagini")
    print("="*40)
    
    while True:
        print("\n1. Analizza immagine")
        print("2. Genera immagine")
        print("0. Esci")
        
        choice = input("\nScegli un'opzione: ").strip()
        
        try:
            if choice == "1":
                source = input("Path immagine o URL: ").strip()
                question = input("Domanda (Enter per default): ").strip() or "Descrivi questa immagine"
                
                analysis = processor.analyze_image(source, question)
                print(f"\nAnalisi:\n{analysis}")
                
            elif choice == "2":
                description = input("Descrivi l'immagine da generare: ").strip()
                enhance = input("Migliorare il prompt? (s/N): ").strip().lower() == 's'
                save = input("Salvare localmente? (s/N): ").strip().lower() == 's'
                
                result = processor.generate_image(description, enhance, save)
                print(f"\nImmagine generata: {result['url']}")
                
                if result.get('enhanced_prompt'):
                    print(f"Prompt migliorato: {result['enhanced_prompt']}")
                
                if result.get('saved_file'):
                    print(f"Salvata come: {result['saved_file']}")
                
            elif choice == "0":
                print("Arrivederci!")
                break
            
            else:
                print("Opzione non valida")
        
        except Exception as e:
            print(f"Errore: {e}")

if __name__ == "__main__":
    main()
```

---

## 6. Troubleshooting

### Errori comuni

#### Error: "Unsupported MIME type"

**Causa**: Campo `extension` mancante nell'oggetto `Media`

**Soluzione**:
```python
# Errato
media = Media(media_type="image", source=data)

# Corretto
media = Media(
    extension=".jpg",  # Sempre specificare
    media_type="image",
    source=data
)
```

#### Error: "API key not found"

**Causa**: Chiave API non configurata o file `.env` nel path sbagliato

**Soluzione**:
```bash
# Verifica file .env
ls -la PizzAI/.env

# Se manca, crea il file
echo 'OPENAI_API_KEY=your-key-here' > PizzAI/.env
```

#### Error: "Cache not supported"

**Causa**: Cache passata a client che non la supporta

**Soluzione**:
```python
# Solo OpenAI supporta cache nel constructor
def create_safe_client(provider: str):
    kwargs = {
        "provider": provider,
        "api_key": os.getenv(f"{provider.upper()}_API_KEY"),
        "model": get_model(provider)
    }
    
    # Cache solo per OpenAI
    if provider == "openai":
        from datapizzai.cache import MemoryCache
        kwargs["cache"] = MemoryCache()
    
    return ClientFactory.create(**kwargs)
```

### Validazione input

```python
def validate_image_file(file_path: str):
    """Valida un file immagine prima del processamento"""
    
    # Verifica esistenza
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File non trovato: {file_path}")
    
    # Verifica estensione
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    if Path(file_path).suffix.lower() not in allowed_extensions:
        raise ValueError(f"Estensione non supportata. Usa: {allowed_extensions}")
    
    # Verifica dimensione (max 20MB)
    max_size = 20 * 1024 * 1024  # 20MB
    if Path(file_path).stat().st_size > max_size:
        raise ValueError(f"File troppo grande (max {max_size/1024/1024:.1f}MB)")
    
    return True

# Uso
try:
    validate_image_file("large_image.jpg")
    result = analyze_local_image("large_image.jpg")
except Exception as e:
    print(f"Validazione fallita: {e}")
```

### Gestione errori robusta

```python
def safe_image_processing(func, *args, max_retries: int = 3, **kwargs):
    """Wrapper per gestione errori con retry"""
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Backoff esponenziale
                print(f"Tentativo {attempt + 1} fallito: {e}")
                print(f"Riprovo tra {wait_time} secondi...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Operazione fallita dopo {max_retries} tentativi: {e}")

# Uso
try:
    result = safe_image_processing(analyze_local_image, "test.jpg")
    print(result)
except Exception as e:
    print(f"Errore definitivo: {e}")
```

---

## Note tecniche

- **Formati supportati**: JPG, JPEG, PNG, GIF, BMP, WEBP
- **Dimensione massima**: 20MB per file
- **Risoluzioni DALL-E**: 1024x1024, 1792x1024, 1024x1792
- **Qualità DALL-E**: "standard" o "hd"
- **Rate limiting**: Rispetta i limiti API dei provider

Per questioni specifiche consultare la documentazione ufficiale dei provider AI utilizzati.