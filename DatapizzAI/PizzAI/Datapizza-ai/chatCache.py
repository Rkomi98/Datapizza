import time
import os
from dotenv import load_dotenv
from datapizza.memory import Memory
from datapizza.clients.openai import OpenAIClient
from datapizza.type import ROLE, TextBlock
from datapizza.cache import MemoryCache

load_dotenv()

memory = Memory()
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    cache=MemoryCache()
)

t0 = time.perf_counter()

message = TextBlock(content="What is machine learning?")
response1 = client.invoke(message.content, memory=memory)
t1 = time.perf_counter()
print("First response time: ", t1 - t0)
print(response1.text)

t2 = time.perf_counter()
response2 = client.invoke(message.content, memory=memory)

t3 = time.perf_counter()
print("Second response time: ", t3 - t2)
print(response2.text)