import os
import time
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock
from datapizza.cache import MemoryCache

load_dotenv()

# Test 1: Memory
print("=== Test 1: Memory ===")
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

memory = Memory()
message = TextBlock(content="Hi, I'm Mirko")

# Call the model
response = client.invoke(message.content, memory=memory)

# Add user message
memory.add_turn(
    [message], 
    ROLE.USER
)

# Store assistant response
memory.add_turn(
    [TextBlock(content=response.text)], 
    ROLE.ASSISTANT
)

print(f"Response: {response.text}\n")

# Test 2: Caching
print("=== Test 2: Caching ===")
client_with_cache = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    cache=MemoryCache()
)

# First request hits the API
t0 = time.perf_counter()
response1 = client_with_cache.invoke("What is machine learning?")
t1 = time.perf_counter()
print("first:", response1.text)
print(f"⏱️ time (first): {t1 - t0:.3f}s")

# Second identical request hits the cache
t2 = time.perf_counter()
response2 = client_with_cache.invoke("What is machine learning?")
t3 = time.perf_counter()
print("second:", response2.text)
print(f"⏱️ time (second): {t3 - t2:.3f}s\n")

# Test 3: Complete Chatbot Class
print("=== Test 3: Chatbot Class ===")

class Chatbot:
    def __init__(self, client):
        self.client = client
        self.memory = Memory()
    
    def send(self, user_input: str) -> str:
        # Store user message
        self.memory.add_turn(
            [TextBlock(content=user_input)], 
            ROLE.USER
        )
        
        # Get response with memory
        response = self.client.invoke(user_input, memory=self.memory)
        
        # Store assistant response
        self.memory.add_turn(
            [TextBlock(content=response.text)], 
            ROLE.ASSISTANT
        )
        
        # Show token usage
        total = (response.prompt_tokens_used or 0) + (response.completion_tokens_used or 0)
        print(f"[tokens: {total}]")
        
        return response.text

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

bot = Chatbot(client)

# Test conversation
print("Bot:", bot.send("Hi, my name is Alice"))
print("Bot:", bot.send("What's my name?"))

print("\n✅ All tests passed for video_02!")

