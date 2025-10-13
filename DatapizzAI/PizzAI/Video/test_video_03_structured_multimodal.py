"""
Test script for Video 3: Structured Responses and Multimodal Capabilities
This script validates all code examples from the video script.
"""

import os
import json
import base64
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv

# Test imports
print("Testing imports...")
try:
    from datapizza.clients.openai import OpenAIClient
    from datapizza.type import Media, MediaBlock, TextBlock, ROLE
    from datapizza.memory import Memory
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)

load_dotenv()

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    print("✗ OPENAI_API_KEY not found in environment")
    exit(1)

print("\n" + "="*60)
print("TEST 1: JSON Prompting")
print("="*60)
try:
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
    print(f"✓ JSON Prompting successful")
    print(f"  Title: {data.get('title')}")
    print(f"  Status: {data.get('status')}")
    print(f"  Tasks count: {len(data.get('tasks', []))}")
except Exception as e:
    print(f"✗ JSON Prompting failed: {e}")

print("\n" + "="*60)
print("TEST 2: Structured Responses with Pydantic")
print("="*60)
try:
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
    print(f"✓ Structured response successful")
    print(f"  Title: {project.title}")
    print(f"  Status: {project.status}")
    print(f"  Tasks:")
    for task in project.tasks:
        print(f"    - {task.name} - {task.owner} - {task.eta_days} days")
except Exception as e:
    print(f"✗ Structured response failed: {e}")

print("\n" + "="*60)
print("TEST 3: Image from URL")
print("="*60)
try:
    # NASA InSight Mars lander image
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
    print(f"✓ Image from URL successful")
    print(f"  Response: {response.text[:100]}...")
except Exception as e:
    print(f"✗ Image from URL failed: {e}")

print("\n" + "="*60)
print("TEST 4: Image from Base64")
print("="*60)
try:
    # Check if test image exists
    test_image_path = "/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/Client/Example.png"
    if os.path.exists(test_image_path):
        with open(test_image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        media = Media(
            extension="png",
            media_type="image",
            source_type="base64",
            source=image_data,
            detail="high"
        )

        response = client.invoke([
            TextBlock(content="What do you see in this image?"),
            MediaBlock(media=media)
        ])
        print(f"✓ Image from base64 successful")
        print(f"  Response: {response.text[:100]}...")
    else:
        print(f"⊘ Skipping - test image not found at {test_image_path}")
except Exception as e:
    print(f"✗ Image from base64 failed: {e}")

print("\n" + "="*60)
print("TEST 5: Audio from Local File")
print("="*60)
try:
    # Check if test audio exists
    test_audio_path = "/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/session.wav"
    if os.path.exists(test_audio_path):
        with open(test_audio_path, "rb") as f:
            audio_data = base64.b64encode(f.read()).decode()

        audio_media = Media(
            extension="wav",
            media_type="audio",
            source_type="base64",
            source=audio_data
        )

        response = client.invoke([
            TextBlock(content="Transcribe this audio briefly"),
            MediaBlock(media=audio_media)
        ])
        print(f"✓ Audio from local file successful")
        print(f"  Response: {response.text[:100]}...")
    else:
        print(f"⊘ Skipping - test audio not found at {test_audio_path}")
except Exception as e:
    print(f"✗ Audio from local file failed: {e}")

print("\n" + "="*60)
print("TEST 6: Multimodal Memory Conversation")
print("="*60)
try:
    memory = Memory()

    # Use the NASA image
    media = Media(
        extension="jpg",
        media_type="image",
        source_type="url",
        source="https://images-assets.nasa.gov/image/PIA25680/PIA25680~orig.jpg?w=1024&h=1024&fit=clip&crop=faces%2Cfocalpoint",
        detail="high"
    )
    image_block = MediaBlock(media=media)

    # First turn: show image
    memory.add_turn([
        TextBlock(content="What is this?"),
        image_block
    ], ROLE.USER)

    response = client.invoke("", memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
    print(f"✓ First turn successful")
    print(f"  Response: {response.text[:100]}...")

    # Second turn: reference the image
    response = client.invoke(
        "What is the significance of this equipment?", 
        memory=memory
    )
    print(f"✓ Second turn successful")
    print(f"  Response: {response.text[:100]}...")
except Exception as e:
    print(f"✗ Multimodal memory conversation failed: {e}")

print("\n" + "="*60)
print("SUMMARY: Video 3 Code Validation")
print("="*60)
print("All critical code paths have been tested.")
print("Check the results above for any failures.")

