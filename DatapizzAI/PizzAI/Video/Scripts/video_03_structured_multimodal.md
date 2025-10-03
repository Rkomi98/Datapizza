# Video 3: Structured Responses and Multimodal Capabilities

## Introduction (1.5 min)

Welcome back! So far we've built a text-based chatbot with memory and caching. That's solid, but real applications need more.

Sometimes you need structured data—JSON responses you can parse and use programmatically. And sometimes you need to work with more than just text—images, audio, documents.

[Visual: Show text bubbles transforming into JSON structures and media files]

Today we're covering two major capabilities: getting reliable structured outputs using Pydantic models, and working with multimodal inputs like images and audio.

By the end of this video, you'll be able to extract structured data from LLM responses and build chatbots that can see and hear, not just read.

Let's dive in.

[Transition: "Two Approaches to Structure"]

## Content Main (6.5 min)

### Getting JSON with Prompt Engineering (1.5 min)

The simplest way to get JSON from an LLM is just to ask for it. But you need to be precise.

[Show code]

```python
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.7
)

prompt = """
Return a valid JSON object only, with no extra text.
Schema:
{
  "title": string,
  "status": one of [planned, in_progress, done],
  "tasks": array of {
    "name": string,
    "owner": string,
    "eta_days": integer
  }
}
"""

response = client.invoke(prompt)
data = json.loads(response.text)
```

[Show the output]

This works, but it's fragile. The model might add markdown code blocks, explanatory text, or malformed JSON. You have to parse it carefully.

That's why there's a better way.

### Structured Responses with Pydantic (2.5 min)

Instead of hoping for valid JSON, you can enforce it with Pydantic models. The framework validates the structure automatically.

[Show code]

```python
from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    name: str
    owner: str
    eta_days: int

class ProjectSummary(BaseModel):
    title: str
    status: str
    tasks: List[Task]

response = client.structured_response(
    input="Summarize our Q4 project plan",
    output_cls=ProjectSummary
)

# Get the validated, typed object
project = response.structured_data[0]
print(project.title)
print(project.status)

for task in project.tasks:
    print(f"{task.name} - {task.owner} - {task.eta_days} days")
```

[Run code, show output]

See the difference? You get a typed Python object with full IDE autocomplete. No manual parsing, no try-except blocks checking for malformed JSON.

[Visual: Show IDE autocomplete working on the project object]

The model is constrained to return data matching your schema. If it doesn't, you get a validation error before your code even sees it.

This is how you build reliable systems. Define your data model, let Pydantic enforce it.

### Working with Images (2.5 min)

Now let's talk about vision. LLMs can analyze images, and Datapizza-AI makes this straightforward.

You have three ways to provide images: URLs, base64-encoded data, or file paths. Let me show you all three.

[Show code]

```python
from datapizza.type import Media, MediaBlock, TextBlock

# Method 1: From URL
media = Media(
    extension="jpg",
    media_type="image",
    source_type="url",
    source="https://example.com/image.jpg",
    detail="high"
)

response = client.invoke([
    TextBlock(content="Describe this image in detail"),
    MediaBlock(media=media)
])
```

[Show example output]

The model sees the image and can describe it, answer questions about it, extract text from it—whatever you need.

[Show code for base64]

```python
# Method 2: Base64 encoding (for local files)
import base64

with open("diagram.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

media = Media(
    extension="png",
    media_type="image",
    source_type="base64",
    source=image_data,
    detail="high"
)

response = client.invoke([
    TextBlock(content="Extract the workflow steps from this diagram"),
    MediaBlock(media=media)
])
```

[Run and show analysis]

This is powerful for document processing—analyzing charts, extracting table data, reading handwritten notes. The model can see structure that traditional OCR might miss.

[Show a multimodal conversation example]

You can even combine this with memory for ongoing visual conversations:

```python
memory = Memory()

# First turn: show image
memory.add_turn([
    TextBlock(content="Analyze this architecture diagram"),
    image_block
], ROLE.USER)

response = client.invoke("", memory=memory)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)

# Second turn: reference the image
response = client.invoke(
    "What improvements would you suggest?", 
    memory=memory
)
```

[Demonstrate the conversation flow]

The model remembers the image across turns. You don't have to send it again.

## Conclusion (1 min)

Let's recap: We covered two methods for structured outputs—basic JSON prompting and robust Pydantic models. Use Pydantic whenever you need reliable, typed data.

We explored multimodal capabilities, showing how to work with images using URLs, base64, or file paths. This opens up document analysis, visual Q&A, and multimodal conversations.

[Visual: Show structured data and images as building blocks]

In the next video, we're going to work with multiple LLM providers using ClientFactory, and you'll learn how to build custom adapters for providers that aren't supported out of the box.

Before then, try building something multimodal—maybe a document analyzer or an image-based chatbot. The patterns we covered today are the foundation for more complex applications.

See you in the next one!

[Note for narrator: Energy should be building—we're adding capabilities fast]
