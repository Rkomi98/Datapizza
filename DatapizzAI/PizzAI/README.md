<h1 align="center">
  <img width="1549" height="539" alt="DatapizzAI Banner" src="https://github.com/user-attachments/assets/a5782efb-9aed-4fb8-b2cd-03c542a811ba" />
</h1>

<p>
  <a href="https://www.python.org/downloads/release/python-3120/"><img alt="Python" src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white"/></a>
  <a href="https://github.com/Datapizza/DatapizzAI/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/></a>
  <a href="https://pypi.org/project/datapizzai/"><img alt="Version" src="https://img.shields.io/badge/Version-3.0.8+-black?style=for-the-badge"/></a>
  <a href="https://discord.gg/your-invite-link"><img alt="Discord" src="https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white"/></a>
</p>

<p align="center">
  <b>Build reliable GenAI solutions fast</b><br/>
  Datapizza AI provides clear interfaces and predictable behavior for agents and RAG.<br/>
  End-to-end visibility and reliable orchestration keep engineers in control from PoC to scale.
</p>

## Table of contents

- [Quick start](#quick-start)
- [Agents](#agents)
  - [Single agent](#single-agent)
  - [Multi-agent system](#multi-agent-system)
- [Chatbot with memory](#chatbot-with-memory)
- [RAG system](#rag-system)
  - [Document ingestion](#document-ingestion)
  - [Advanced retrieval](#advanced-retrieval)
- [Pipeline](#pipeline)
  - [Sentiment analysis pipeline](#sentiment-analysis-pipeline)

---

## Quick start

Build AI applications in three simple steps: install `datapizzai`, configure your API key, and create an `OpenAIClient`.

Install with `uv pip`:

```bash
uv pip install -U datapizzai
```

Install with `pip`:

```bash
pip install -U datapizzai
```

Create a `.env` file with your API keys:

```python
OPENAI_API_KEY=sk-your-key-here
```

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import OpenAIClient

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a pizza domain expert who answers concisely."
)

response = client.invoke("Tell me an interesting fact about pizza")
print(response.text)
```

---

## Agents

Create autonomous agents that reason, plan, and act using tools.

### Single agent

```python
import os
from dotenv import load_dotenv
from datapizzai.agents import Agent
from datapizzai.clients import OpenAIClient
from datapizzai.tools import tool

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a thoughtful planner who explains reasoning before delegating calculations."
)

@tool(name="calculator")
def calculator(expression: str) -> str:
    return str(eval(expression))

agent = Agent(
    name="PlannerBot",
    client=client,
    system_prompt="You design solution steps and offload arithmetic to the calculator tool.",
    tools=[calculator]
)

result = agent.run("Outline the pricing strategy for 128 pizzas sold at 12.5 euros each and compute the total revenue.")
print(result)
```

### Multi-agent system

DatapizzAI enables building teams of specialized agents that work together. A coordinator agent can delegate specific tasks to expert agents - for example, one agent fetches data, another analyzes it, and a third writes the final report. Each agent has its own expertise and tools, while the coordinator orchestrates the workflow and combines their outputs into comprehensive results.

![Screencast_20250913_155132](https://github.com/user-attachments/assets/4dc42f21-c045-4c44-b0d8-117a6725410f)

---

## Chatbot with memory

Build conversational AI that remembers context across interactions.

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import OpenAIClient
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

load_dotenv()

class SimpleChatbot:
    def __init__(self):
        self.client = OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            system_prompt="You are a friendly assistant who keeps track of past replies."
        )
        self.memory = Memory()

    def send_message(self, user_input: str) -> str:
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        response = self.client.invoke("", memory=self.memory)
        self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        return response.text

bot = SimpleChatbot()

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break
    print("Bot:", bot.send_message(user_input))
```
![Screencast_20250913_154653](https://github.com/user-attachments/assets/56e57e4c-0499-415e-bf12-328e1cf2808f)

---

## RAG system

Build complete Retrieval-Augmented Generation systems in minutes.

### Document ingestion

```python
from datapizzai.modules.parsers.text_parser import parse_text
from datapizzai.modules.splitters import TextSplitter
from datapizzai.embedders import NodeEmbedder
from datapizzai.vectorstores import QdrantVectorstore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

clientQ = QdrantClient(host="localhost", port=6333)
clientQ.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

vectorstore = QdrantVectorstore(host="localhost", port=6333, https=False)

text = """
DatapizzAI is a revolutionary AI framework.
It enables rapid development of intelligent systems.
Its simplicity makes it accessible to all developers.
"""

document = parse_text(text)

splitter = TextSplitter(max_char=100, overlap=20)
chunks = splitter(text)

embedder = NodeEmbedder(
    client=client,
    model_name="text-embedding-3-small"
)
embedded_chunks = embedder(chunks)

vectorstore = QdrantVectorstore(host="localhost", port=6333)
for chunk in embedded_chunks:
    vectorstore.add(chunk, collection_name="docs")
```

### Advanced retrieval

```python
import os
from datapizzai.modules.rerankers import CohereReranker
from datapizzai.embedders import ClientEmbedder

reranker = CohereReranker(
    api_key=os.getenv("COHERE_API_KEY"),
    endpoint="https://api.cohere.com/v1",
    top_n=3
)

query_embedder = ClientEmbedder(client=client, model_name="text-embedding-3-small")

def advanced_rag_query(question: str) -> str:
    query_vec = query_embedder(question)
    candidates = vectorstore.search(
        query_vector=query_vec,
        collection_name="docs"
    )
    reranked = reranker.invoke({"query": question, "documents": candidates})
    context = "\n".join([chunk.text for chunk in reranked])
    response = client.invoke(f"Context: {context}\n\nQuestion: {question}")
    return response.text

response = advanced_rag_query("What is DatapizzAI?")
print(response)
```
![RAG_3](https://github.com/user-attachments/assets/4b6f86ef-8a4c-4ba7-b0f5-93553758eb64)


---

## Pipeline

Build complex processing workflows with modular components.

### Sentiment analysis pipeline

```python
from datapizzai.pipeline import DagPipeline
from datapizzai.core.models import PipelineComponent

class LoadReviews(PipelineComponent):
    def _run(self, **kwargs):
        return {"reviews": [
            "Amazing product, highly recommend!",
            "Terrible experience, avoid at all costs",
            "Average quality, nothing special"
        ]}
    async def _a_run(self, **kwargs):
        return self._run(**kwargs)

class AnalyzeSentiment(PipelineComponent):
    def _run(self, reviews, **kwargs):
        sentiments = []
        print(reviews)
        for review in reviews:
            if "amazing" in review.lower() or "recommend" in review.lower():
                sentiments.append({"text": review, "sentiment": "positive"})
            elif "terrible" in review.lower() or "avoid" in review.lower():
                sentiments.append({"text": review, "sentiment": "negative"})
            else:
                sentiments.append({"text": review, "sentiment": "neutral"})
        return {"results": sentiments}
    async def _a_run(self, **kwargs):
        return self._run(**kwargs)

class GenerateReport(PipelineComponent):
    def _run(self, results, **kwargs):
        pos = sum(1 for r in results if r["sentiment"] == "positive")
        neg = sum(1 for r in results if r["sentiment"] == "negative")
        neu = len(results) - pos - neg
        return {"report": f"📊 Positive: {pos}, Negative: {neg}, Neutral: {neu}"}
    async def _a_run(self, **kwargs):
        return self._run(**kwargs)

pipeline = DagPipeline()
pipeline.add_module("loader", LoadReviews())
pipeline.add_module("analyzer", AnalyzeSentiment())
pipeline.add_module("reporter", GenerateReport())

pipeline.connect("loader", "analyzer", "reviews", "reviews")
pipeline.connect("analyzer", "reporter", "results", "results")

result = pipeline.run({})
print(result["reporter"]["report"])
```
![Pipeline](https://github.com/user-attachments/assets/71beba27-351e-49c2-9aef-5f3288522a47)


---

<p align="center">⭐⭐⭐⭐⭐</p>
