import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
import json

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=1
)

prompt = """
Return a valid JSON object with the following fields and no extra text:
Schema:
{
    "title": string,
    "status": one of ["TODO", "IN_PROGRESS", "DONE"],
    "tasks": array of {
        "name": string,
        "owner": string,
        "eta_days": integer
    },
}
"""

response = client.invoke(prompt)
data = json.loads(response.text)
print("Title: ", data["title"])
print("Status: ", data["status"])
print("Tasks: ")
for task in data["tasks"]:
    print(f"Name: {task['name']}, Owner: {task['owner']}, ETA: {task['eta_days']} days")

print(response.text)
