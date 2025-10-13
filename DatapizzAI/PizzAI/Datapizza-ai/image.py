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

with open("Mars.jpg", "rb") as image_file:
    image_data = base64.b64encode(image_file.read()).decode("utf-8")

media = Media(
    media_type="image",
    extension="jpg",
    source_type="base64",
    source=image_data,
    detail="high"
)

media_block = MediaBlock(media=media)

response = client.invoke(
    input=[
        TextBlock(content="What do you see in the image I provided you?"),
        media_block
    ]
)

print(response.text)