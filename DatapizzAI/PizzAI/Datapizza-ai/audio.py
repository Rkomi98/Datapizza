import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.type import TextBlock, MediaBlock, Media
import base64

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=1
)

with open("meeting.wav", "rb") as audio_file:
    audio_data = base64.b64encode(audio_file.read()).decode("utf-8")

media = Media(
    media_type="audio",
    extension="wav",
    source_type="base64",
    source=audio_data,
    detail="high"
)

media_block = MediaBlock(media=media)

response = client.invoke(
    input=[
        TextBlock(content="What has been discussed in the meeting?"),
        media_block
    ]
)

print(response.text)