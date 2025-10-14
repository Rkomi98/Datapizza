import os
from dotenv import load_dotenv
from datapizza.clients.google import GoogleClient
from datapizza.type import TextBlock, MediaBlock, Media
import base64

load_dotenv()

client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.5-flash",
)

media = Media(
    media_type="audio",
    extension="mp3",
    source_type="path",
    source="meeting.mp3",
    detail="high"
)

media_block = MediaBlock(media=media)

response = client.invoke(
    input=[
        TextBlock(content="What was said during the meeting? Please provide a summary."),
        media_block
    ]
)

print(response.text)