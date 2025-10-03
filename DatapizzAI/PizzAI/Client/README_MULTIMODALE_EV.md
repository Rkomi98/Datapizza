# Multimodal Examples - Datapizza-AI

Quick examples that show how to use the **Datapizza-AI** framework with multimodal input/output (images + text).

## Table of Contents

- [1. Image analysis from URL](#1-image-analysis-from-url)
- [2. Local image analysis](#2-local-image-analysis)
- [3. Local audio analysis](#3-local-audio-analysis)
- [4. Multimodal conversation with memory](#4-multimodal-conversation-with-memory)

## 1. Image analysis from URL

**When to use**: Public image analysis, quick tests, demos without local files

**What it does**: The `MediaBlock` wraps the image (URL, base64, or file) and combines it with text so you can create multimodal input. The AI processes both the textual prompt and the visual content.

```python
from dotenv import load_dotenv
import os

from datapizza.clients import OpenAIClient
from datapizza.type import Media, MediaBlock, TextBlock

load_dotenv('../.env')
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

media = Media(
    extension="jpg",        # Extension without dot for the correct MIME type
    media_type="image",     # Media type (image, audio, video)
    source_type="url",      # Source: url, base64, or file
    source="https://assets.science.nasa.gov/dynamicimage/assets/science/psd/mars/internal_resources/1155.jpeg?w=1767&h=350&fit=clip&crop=faces%2Cfocalpoint",
    detail="high"
)

response = client.invoke([
    TextBlock(content="Describe this image in detail"),
    MediaBlock(media=media)
])

print(response.text)
```

---

## 2. Local image analysis

**When to use**: Personal photos, private documents, images that are not publicly accessible

**What it does**: Converts the local image to base64 for safe transfer over the API. The `MediaBlock` takes care of encoding and sending the file.

```python
import base64
from pathlib import Path

from datapizza.type import Media, MediaBlock, TextBlock

def load_image_as_base64(path: str) -> str:
    """Convert an image file into a base64 string for safe transport"""
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")

image_b64 = load_image_as_base64("Example.png")

media = Media(
    extension="jpg",        # File extension used for the MIME type
    media_type="image",     # Content type
    source_type="base64",   # Transmission format
    source=image_b64,        # Encoded image data
    detail="high"
)

prompt = "Analyse this image and give me a technical description."

response = client.invoke([
    TextBlock(content=prompt),
    MediaBlock(media=media)
])

print(response.text)
```

---

## 3. Local audio analysis

**When to use**: Transcribing recordings, analysing audio content, voice conversations

**What it does**: Sends a local audio file for analysis. The `MediaBlock` manages file transmission, and the AI can transcribe, analyse, or respond to the audio content.

```python
import os

from datapizza.clients import GoogleClient
from datapizza.type import Media, MediaBlock, TextBlock

analysis_client_google = GoogleClient(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
    system_prompt="You are an AI assistant specialised in audio analysis. Please, answer in English.",
    temperature=0.5
)

media = Media(
    extension="wav",
    media_type="audio",
    source_type="path",
    source="TI0TpOD_.wav"
)

prompt = "Transcribe this audio and summarise the main content."
response = analysis_client_google.invoke([
    TextBlock(content=prompt),
    MediaBlock(media=media)
])
print(response.text)
```

---

## 4. Multimodal conversation with memory

**When to use**: Progressive image analysis, visual tutoring, iterative development of creative projects

**What it does**: Keeps the visual and textual context across conversation turns. The AI remembers the analysed image and can reference it in later messages without the user sending it again.

```python
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

from datapizza.clients import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock, Media, MediaBlock


load_dotenv('../.env')

def create_mediablock_from_file(file_path: str) -> MediaBlock:
    """Create a MediaBlock from a local image file (base64)."""
    data = Path(file_path).read_bytes()
    image_b64 = base64.b64encode(data).decode('utf-8')
    ext = Path(file_path).suffix.lstrip('.').lower() or 'png'
    media = Media(
        extension=ext,
        media_type="image",
        source_type="base64",
        source=image_b64,
        detail="high",
    )
    return MediaBlock(media=media)

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)
memory = Memory()
image_block = create_mediablock_from_file("Example.png")
memory.add_turn([TextBlock("Analyse this photo, what do you see?"), image_block], ROLE.USER)
resp = client.invoke("Analyse this photo, what do you see?", memory=memory)
memory.add_turn([TextBlock(resp.text)], ROLE.ASSISTANT)
resp = client.invoke("What improvements would you recommend?", memory=memory)
print(resp.text)
```
