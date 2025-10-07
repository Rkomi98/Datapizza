import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a helpful AI assistant."
)

response = client.invoke("Explain quantum computing in one sentence")
print(response.text)

