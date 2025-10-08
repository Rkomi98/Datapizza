import os
from dotenv import load_dotenv
from datapizza.memory import Memory
from datapizza.clients.openai import OpenAIClient
from datapizza.type import ROLE, TextBlock

memory = Memory()
load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",    
    system_prompt="You are a helpful assistant that can answer questions and help with tasks.",
)

message = TextBlock(content="What is capital of Italy?")

response = client.invoke(message.content, memory=memory)
print(response.text)

# Add the user message as a turn
memory.add_turn(message, ROLE.USER)
memory.add_turn(
    TextBlock(content=response.text), 
    ROLE.ASSISTANT
    )
message = TextBlock(content="What did I ask you before?")
memory.add_turn(message, ROLE.USER)
response = client.invoke(message.content, memory=memory)
print(response.text)
memory.add_turn(
    TextBlock(content=response.text), 
    ROLE.ASSISTANT
    )
