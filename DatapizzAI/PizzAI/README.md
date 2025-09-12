<h1 align="center">
  <img width="1549" height="539" alt="DatapizzAI Banner" src="https://github.com/user-attachments/assets/f4b9c2e5-2a56-47e9-8db4-6ec41a7c6e3a" />
</h1>

<p>
  <a href="https://www.python.org/downloads/release/python-3120/"><img alt="Python" src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white"/></a>
  <a href="https://github.com/Datapizza/DatapizzAI/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/></a>
  <a href="https://pypi.org/project/datapizzai/"><img alt="Version" src="https://img.shields.io/badge/Version-3.0.8+-black?style=for-the-badge"/></a>
  <a href="https://discord.gg/your-invite-link"><img alt="Discord" src="https://img.shields.io/badge/Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white"/></a>
</p>

## Table of contents

- [Quick start](#quick-start)
- [Chatbot with memory](#chatbot-with-memory)
- [Agents](#agents)
  - [Single agent](#single-agent)
  - [Multi-agent system](#multi-agent-system)
- [RAG system](#rag-system)
  - [Document ingestion](#document-ingestion)
  - [Advanced retrieval](#advanced-retrieval)
- [Pipeline](#pipeline)
  - [Sentiment analysis pipeline](#sentiment-analysis-pipeline)
  - [Branching pipeline](#branching-pipeline)
- [Next steps](#next-steps)

---

## Quick start

Build AI applications in three simple steps: install `datapizzai`, configure your API key, and create a client with `ClientFactory.create()`.

```bash
pip install datapizzai
```

Create a `.env` file with your API keys:

```python
# .env file
OPENAI_API_KEY=sk-your-key-here
```

```python
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory

# Load environment variables
load_dotenv()

# Create your first client in one line
client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)

# Instant test
response = client.invoke("Tell me an interesting fact about pizza 🍕")
print(response.text)
```

---

## Chatbot with memory

Build conversational AI that remembers context across interactions.

```python
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE

class SimpleChatbot:
    def __init__(self):
        self.client = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
        self.memory = Memory()
    
    def send_message(self, user_input: str) -> str:
        # Add user message to memory
        self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        # Get AI response with full conversation context
        response = self.client.invoke("", memory=self.memory)
        
        # Save AI response to memory
        self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        return response.text

# Usage
bot = SimpleChatbot()

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break
    print("Bot:", bot.send_message(user_input))
```

![2025-09-12_10-23-16 mp4](https://github.com/user-attachments/assets/8c759d2f-20a7-4231-ab41-382ff816c894)

---

## Agents

Create autonomous agents that reason, plan, and act using tools.

### Single agent

```python
from datapizzai.agents import Agent
from datapizzai.tools import tool

@tool
def web_search(query: str) -> str:
    """Search information on the web"""
    return f"Results for '{query}': DatapizzAI is the simplest AI framework"

@tool
def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text"""
    return "Sentiment: Positive (95% confidence)"

@tool
def calculate(expression: str) -> str:
    """Perform mathematical calculations"""
    return str(eval(expression))

# Create specialized agent
agent = Agent(
    name="ResearchBot",
    client=client,
    system_prompt="You are an expert researcher. Always analyze sources and sentiment.",
    tools=[web_search, analyze_sentiment, calculate],
    planning_interval=3  # Replan every 3 steps
)

# Agent plans and executes autonomously
result = agent.run("What do developers think about DatapizzAI? Also calculate 127 * 89")
print(result)
```

### Multi-agent system

DatapizzAI enables building teams of specialized agents that work together. A coordinator agent can delegate specific tasks to expert agents - for example, one agent fetches data, another analyzes it, and a third writes the final report. Each agent has its own expertise and tools, while the coordinator orchestrates the workflow and combines their outputs into comprehensive results.

![Multi-Agent System Demo](https://github.com/user-attachments/assets/multi-agent-demo-gif)

---

## RAG system

Build complete Retrieval-Augmented Generation systems in minutes.

### Document ingestion

```python
from datapizzai.modules.parsers.text_parser import parse_text
from datapizzai.modules.splitters import TextSplitter
from datapizzai.embedders import NodeEmbedder
from datapizzai.vectorstores import QdrantVectorstore
# 1. Setup Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

clientQ = QdrantClient(host="localhost", port=6333)
clientQ.create_collection(
    collection_name="docs",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

vectorstore = QdrantVectorstore(host="localhost", port=6333, https=False)

# 1. Prepare documents
text = """
DatapizzAI is a revolutionary AI framework.
It enables rapid development of intelligent systems.
Its simplicity makes it accessible to all developers.
"""

# 2. Parse and split documents
document = parse_text(text)

splitter = TextSplitter(max_char=100, overlap=20)
chunks = splitter(text)  # Use text directly

# 3. Generate embeddings
embedder = NodeEmbedder(
    client=client,
    model_name="text-embedding-3-small"
)
embedded_chunks = embedder(chunks)

# 4. Store in vector database
vectorstore = QdrantVectorstore(host="localhost", port=6333)
for chunk in embedded_chunks:
    vectorstore.add(chunk, collection_name="docs")
```

### Advanced retrieval

```python
ffrom datapizzai.modules.rerankers import CohereReranker
from datapizzai.modules.metatagger import KeywordMetatagger
from datapizzai.embedders import ClientEmbedder

# Add metadata to chunks for better retrieval
metatagger = KeywordMetatagger(client=client)
tagged_chunks = metatagger(chunks)

# Initialize reranker for improved relevance
reranker = CohereReranker(
    api_key=os.getenv("COHERE_API_KEY"),
    endpoint="https://api.cohere.com/v1",
    top_n=3,
)

# Query embedder
query_embedder = ClientEmbedder(client=client, model_name="text-embedding-3-small")

def advanced_rag_query(question: str) -> str:
    # 1. Embed query
    query_vec = query_embedder(question)
    
    # 2. Initial retrieval (cast wide net)
    candidates = vectorstore.search(
        query_vector=query_vec,
        collection_name="docs",
    )
    
    # 4. Generate final answer with best context
    context = "\n".join([d.text for d in candidates])
    response = client.invoke(f"Context: {context}\n\nQuestion: {question}")
    return response.text

# Query the system
response = advanced_rag_query("What is DatapizzAI?")
print(response)
```

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

# Build pipeline
pipeline = DagPipeline()
pipeline.add_module("loader", LoadReviews())
pipeline.add_module("analyzer", AnalyzeSentiment())
pipeline.add_module("reporter", GenerateReport())

# Connect components
pipeline.connect("loader", "analyzer", "reviews", "reviews")
pipeline.connect("analyzer", "reporter", "results", "results")

# Execute
result = pipeline.run({})
print(result["reporter"]["report"])
```

### Branching pipeline

```python
from datapizzai.pipeline import FunctionalPipeline

# Pipeline with conditional branching
pipeline = (
    FunctionalPipeline()
    .run(name="load", node=LoadReviews())
    .then(name="analyze", node=AnalyzeSentiment(), target_key="reviews")
    .branch(
        condition=lambda ctx: len(ctx.get("analyze", {}).get("results", [])) > 10,
        if_true=DetailedAnalysisPipeline(),
        if_false=QuickSummaryPipeline()
    )
)

result = pipeline.execute()
```

---

## Next steps

Now that you've seen the power and simplicity of DatapizzAI, here's how to continue:

1. **Explore complete examples** in the `/examples` folder
2. **Join the community** on Discord for support and ideas  
3. **Contribute** to the project on GitHub

<p align="center">
  <img src="https://via.placeholder.com/600x200/FF0000/FFFFFF?text=Start+Building+Today!" alt="CTA">
</p>

<p align="center">
  <b>🍕 DatapizzAI - AI as simple as ordering pizza!</b>
</p>

---

<p align="center">
  Made with ❤️ by the DataPizza Team
</p>
