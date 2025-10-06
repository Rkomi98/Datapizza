# Video 8: Complete RAG Implementation

## Introduction (1.5 min)

Hey everyone, welcome back! So we've built agents, multi-agent systems, conversational interfaces. Now we're tackling one of the most practical applications of LLMs: Retrieval-Augmented Generation, or RAG.

[Visual: Show document being broken into chunks, searched, and used to answer questions]

RAG lets you build systems that answer questions using your own documents—internal wikis, product docs, research papers, whatever you've got. The LLM doesn't just generate from its training data—it retrieves relevant context from your documents first.

Today we're building a complete RAG pipeline from scratch: parsing documents, creating embeddings, storing them in a vector database, retrieving relevant chunks, and generating answers. The full stack.

This is a full production pattern that companies actually use. After this, you'll have a working knowledge base you can query with natural language.

Alright, here's the RAG pipeline.

## Content Main (7.5 min)

### Setting Up the Infrastructure (1 min)

So RAG needs a vector database. We're using Qdrant—it's fast, open source, and stupidly easy to run in Docker.

[Show terminal]

```bash
docker run -p 6333:6333 qdrant/qdrant
```

That's it. Qdrant is now running at localhost:6333. You can see the dashboard at that address.

[Show browser with Qdrant dashboard]

Now let's set up our imports and client:

```python
import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)
```

We'll use this client for both embedding and generation.

### Ingestion Pipeline: From Documents to Vectors (2.5 min)

The ingestion pipeline has several steps. Let me walk through each one quickly because there's a lot to cover.

**Step 1: Parse the document**

```python
from datapizza.parsers import TextParser

parser = TextParser()
text = """
Machine learning is a branch of artificial intelligence.
It enables computers to learn from data without being explicitly programmed.
Modern ML systems use statistical algorithms to identify patterns.
"""

document_node = parser.parse(text, metadata={"source": "ml_guide"})
```

[Show the hierarchical structure]

TextParser creates a tree: document → paragraphs → sentences. This structure helps with accurate chunking.

**Step 2: Split into chunks**

```python
from datapizza.rag.splitter import NodeSplitter

splitter = NodeSplitter(max_char=1000)
chunks = splitter(document_node)
```

Each chunk is small enough to embed but large enough to contain meaningful context. The splitter preserves metadata and creates unique IDs.

**Step 3: Generate embeddings**

```python
from datapizza.rag.embedder import NodeEmbedder

embedder = NodeEmbedder(
    client=client,
    model_name="text-embedding-3-small",
    batch_size=100
)

embedded_chunks = embedder(chunks)
```

[Show what an embedded chunk looks like]

Each chunk now has a 1536-dimensional vector representing its semantic meaning. Similar content gets similar vectors.

**Step 4: Store in vector database**

```python
from datapizza.vectorstores.qdrant import QdrantVectorstore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Create collection
qdrant_client = QdrantClient(host="localhost", port=6333)
qdrant_client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Store chunks
vectorstore = QdrantVectorstore(host="localhost", port=6333)
vectorstore.add(embedded_chunks, collection_name="knowledge_base")
```

[Show Qdrant dashboard with stored vectors]

Your documents are now searchable by semantic similarity. Time to build retrieval.

### Retrieval Pipeline: From Query to Answer (3 min)

Now someone asks a question. We need to find relevant chunks and generate an answer. Here's how that works.

**Step 1: Embed the query**

```python
query = "How does machine learning work?"
query_vector = client.embed(query)
```

Same embedding model, same vector space. The query is now comparable to our stored chunks.

**Step 2: Search for relevant chunks**

```python
results = vectorstore.search(
    query_vector=query_vector,
    collection_name="knowledge_base",
    limit=5
)
```

[Show the retrieved chunks]

Vector search found the most semantically similar chunks. This is semantic search—it understands meaning, not just keywords.

**Step 3: Rerank for precision**

```python
from datapizza.rag.reranker import CohereReranker

reranker = CohereReranker(
    api_key=os.getenv("COHERE_API_KEY"),
    top_n=3
)

final_chunks = await reranker.a_run({
    "query": query,
    "documents": results
})
```

[Explain reranking]

Reranking uses a more expensive model to reorder results by actual relevance. It's optional but improves accuracy, especially for complex queries.

**Step 4: Generate the answer**

```python
from datapizza.rag.prompts import ChatPromptTemplate

template = ChatPromptTemplate(
    user_prompt_template="Question: {{ user_prompt }}\nAnswer based on the context provided.",
    retrieval_prompt_template="Context:\n{% for chunk in chunks %}- {{ chunk.text }}\n{% endfor %}"
)

memory = template.format(
    user_prompt=query,
    chunks=final_chunks,
    retrieval_query=query
)

response = client.invoke("", memory=memory)
print(response.text)
```

[Show the full answer]

The model sees the retrieved context and generates an answer based on it. It's grounded in your documents, not just general knowledge.

[Visual: Show complete RAG flow diagram]

### Making It Production-Ready (1 min)

This works, but production RAG needs more sophistication. Here are the patterns:

**Query rewriting**: Transform vague questions into better search queries before retrieval.

```python
from datapizza.rag.rewriter import ToolRewriter

rewriter = ToolRewriter(client=client)
rewritten = rewriter.run("Uhm, how's that ML thing work?")
# Output: "Explain how machine learning algorithms work"
```

**Metadata filtering**: Search within specific document types, dates, or categories.

```python
results = vectorstore.search(
    query_vector=query_vector,
    collection_name="knowledge_base",
    filter={"source": "ml_guide"}
)
```

**Hybrid search**: Combine vector search with keyword matching for better precision.

These are the patterns that make RAG reliable at scale.

## Conclusion (1 min)

Quick recap of the full pipeline: Parse documents into structured nodes. Split into chunks and generate embeddings. Store in a vector database. For queries, embed them, search for relevant chunks, optionally rerank, and generate answers with context.

[Visual: Show complete pipeline with all steps]

This is how you make LLMs useful for real business problems. Product support, internal documentation, research assistance—all built on this exact foundation.

Next up is the final video, where we're covering pipelines for complex workflows and production monitoring so you can actually deploy this stuff and not have it break.

Before that, try building your own knowledge base. Ingest some documents, query them, experiment with chunk sizes and reranking. See how retrieval quality affects answer accuracy. It's fascinating to tune this.

This is production-grade AI engineering. If you're still with me, hit that subscribe button. I'll see you in the final video!

[Note for narrator: This should feel like a culmination—we're building real, deployable systems]
