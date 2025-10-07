import os
import json
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.type import Media, MediaBlock, TextBlock, ROLE
from datapizza.memory import Memory
from pydantic import BaseModel
from typing import List

load_dotenv()

# Test 1: JSON with Prompt Engineering
print("=== Test 1: JSON with Prompt Engineering ===")
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
try:
    data = json.loads(response.text)
    print("Title:", data["title"])
    print("✅ JSON parsing successful\n")
except Exception as e:
    print(f"❌ JSON parsing failed: {e}\n")

# Test 2: Structured Responses with Pydantic
print("=== Test 2: Structured Responses with Pydantic ===")

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
print(f"Title: {project.title}")
print(f"Status: {project.status}")

for task in project.tasks:
    print(f"  - {task.name} - {task.owner} - {task.eta_days} days")
print("✅ Structured response successful\n")

# Test 3: Working with Images (URL)
print("=== Test 3: Working with Images (URL) ===")

media = Media(
    extension="jpg",
    media_type="image",
    source_type="url",
    source="https://images-assets.nasa.gov/image/PIA25680/PIA25680~orig.jpg?w=1024&h=1024&fit=clip&crop=faces%2Cfocalpoint",
    detail="high"
)

response = client.invoke([
    TextBlock(content="Describe this image in one sentence"),
    MediaBlock(media=media)
])
print(f"Image description: {response.text}")
print("✅ Image processing successful\n")

# Test 4: Multimodal conversation
print("=== Test 4: Multimodal Conversation ===")

memory = Memory()

image_block = MediaBlock(media=media)

# First turn: show image
memory.add_turn([
    TextBlock(content="Analyze this image"),
    image_block
], ROLE.USER)

response = client.invoke("", memory=memory)
memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
print(f"First response: {response.text[:100]}...")

# Second turn: reference the image
memory.add_turn([TextBlock(content="What planet is this?")], ROLE.USER)
response = client.invoke("", memory=memory)
print(f"Second response: {response.text}")
print("✅ Multimodal conversation successful\n")

print("✅ All tests passed for video_03!")

