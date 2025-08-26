# Multimodal Examples - DatapizzAI

Quick examples for using the **DatapizzAI** framework with multimedia input/output (images + text).

## 1. Image analysis from URL

**When to use**: Analysis of public images, quick tests, demos without local files

**What it does**: The `MediaBlock` encapsulates the image (URL, base64 or file) and combines it with text to create multimodal input. The AI analyzes both the textual prompt and visual content.

```python
from datapizzai.clients import ClientFactory
from datapizzai.type import TextBlock, MediaBlock, Media
import os

client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Analyze image from URL
media = Media(
    extension="jpg",        # Extension without dot for correct MIME type
    media_type="image",     # Media type (image, audio, video)
    source_type="url",      # Source: url, base64, or file
    source="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
)

# Combine text and image for multimodal input
response = client.invoke([
    TextBlock(content="Describe this image in detail"),
    MediaBlock(media=media)  # Wrapper that contains the image
])

print(response.text)
```

---

## 2. Local image analysis

**When to use**: Analysis of personal photos, private documents, non-public images

**What it does**: Converts the local image to base64 for secure transmission via API. The `MediaBlock` handles encoding and transmission of the file.

```python
import base64
from pathlib import Path
from datapizzai.type import Media, MediaBlock, TextBlock

def load_image_as_base64(path: str) -> str:
    """Converts image file to base64 string for secure transmission"""
    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")

# Load local image and convert to base64
image_b64 = load_image_as_base64("my_image.jpg")

# Create Media object with image metadata
media = Media(
    extension="jpg",        # File extension for MIME type
    media_type="image",     # Content type
    source_type="base64",   # Transmission format
    source=image_b64,       # Encoded image data
    detail="high"           # Analysis quality (high for details)
)

# Specific prompt for technical analysis
prompt = "Analyze this image and give me a technical description."

# Invoke AI with multimodal input (text + image)
response = client.invoke([
    TextBlock(content=prompt),
    MediaBlock(media=media)  # Wrapper for the image
])

print(response.text)
```

---

## 4. Multimodal conversation with memory

**When to use**: Progressive image analysis, visual tutoring, iterative development of creative projects

**What it does**: Maintains visual and textual context between conversation turns. The AI remembers the analyzed image and can refer to it in subsequent turns without the user resending it.

```python
from datapizzai.memory import Memory
from datapizzai.type import ROLE, TextBlock
from datapizzai.utils import create_mediablock_from_file

client = ClientFactory.create(provider="openai", api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
memory = Memory()

# First turn: user sends image with request
image_block = create_mediablock_from_file("my_photo.jpg")
memory.add_turn([TextBlock("Analyze this photo"), image_block], ROLE.USER)
resp = client.invoke("", memory=memory)
memory.add_turn([TextBlock(resp.text)], ROLE.ASSISTANT)

# Second turn: follow-up that builds on the previous image
memory.add_turn([TextBlock("What improvements would you recommend?")], ROLE.USER)
resp = client.invoke("", memory=memory)

print(resp.text)
```
