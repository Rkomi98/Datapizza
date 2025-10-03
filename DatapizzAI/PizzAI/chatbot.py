from datapizza.clients import ClientFactory
from datapizza.memory import Memory
from datapizza.type import TextBlock, ROLE
import os
from dotenv import load_dotenv
load_dotenv()

class SimpleChatbot:
    def __init__(self):
        self.client = ClientFactory.create("google", os.getenv("GOOGLE_API_KEY"), "gemini-2.5-flash")
        self.memory = Memory()
    
    def send_message(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        response = self.client.invoke(user_input, memory=self.memory)
        self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        return response.text

# Utilizzo
bot = SimpleChatbot()

while True:
    user_input = input("Tu: ").strip()
    if user_input.lower() in ["esci", "quit"]:
        break
    print("Bot:", bot.send_message(user_input))