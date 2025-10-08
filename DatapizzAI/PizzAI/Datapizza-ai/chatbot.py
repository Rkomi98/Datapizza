import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    system_prompt="You are a helpful assistant that can answer questions and help with tasks.",
)

response = client.invoke("What is capital of Italy?")
print(response.text)