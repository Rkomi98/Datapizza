import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from pydantic import BaseModel
from typing import List

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=1
)

class Task(BaseModel):
    name: str
    owner: str
    eta_days: int

class Project(BaseModel):
    title: str
    status: str
    tasks: List[Task]

response = client.structured_response(
    input="Summarize the Q4 2025 project plan for the company.",
    output_cls=Project
)

project = response.structured_data[0]
print("Title: ", project.title)
print("Status: ", project.status)
print("Tasks: ")
for task in project.tasks:
    print(f"Name: {task.name}, Owner: {task.owner}, ETA: {task.eta_days} days")

print(response.text)

