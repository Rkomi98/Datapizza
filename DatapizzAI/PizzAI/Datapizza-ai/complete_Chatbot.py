import os
from dotenv import load_dotenv
from datapizza.memory import Memory
from datapizza.clients.openai import OpenAIClient
from datapizza.type import ROLE, TextBlock
from datapizza.cache import MemoryCache

load_dotenv()

class CompleteChatbot:
    def __init__(self, client):
        self.memory = Memory()
        self.client = client

    def send(self, user_input:str) -> str:
        self.memory.add_turn(TextBlock(content=user_input), ROLE.USER)
        response = self.client.invoke(user_input, memory=self.memory)
        self.memory.add_turn(TextBlock(content=response.text), ROLE.ASSISTANT)
        total_token = response.prompt_tokens_used + response.completion_tokens_used
        print(f"Total token used: {total_token}")
        return response.text
    
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    cache=MemoryCache()
)

chatbot = CompleteChatbot(client)

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        break
    response = chatbot.send(user_input)
    print(f"Chatbot: {response}")
    
        