import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

load_dotenv()

print("=" * 70)
print("Video 08: RAG Implementation Test")
print("=" * 70)

# Setup client
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)
print("✅ Client initialized")

# Step 1: Prepare documents
documents = [
    {
        "text": "Machine learning is a branch of artificial intelligence that enables computers to learn from data without being explicitly programmed.",
        "metadata": {"source": "ml_guide", "id": "doc1"}
    },
    {
        "text": "Modern ML systems use statistical algorithms to identify patterns in large datasets.",
        "metadata": {"source": "ml_guide", "id": "doc2"}
    },
    {
        "text": "Deep learning is a subset of machine learning that uses neural networks with multiple layers.",
        "metadata": {"source": "dl_guide", "id": "doc3"}
    }
]
print(f"✅ Prepared {len(documents)} document chunks\n")

# Step 2: Generate embeddings
print("📊 Generating embeddings...")
embedded_docs = []
for doc in documents:
    embedding = client.embed(doc["text"], model_name="text-embedding-3-small")
    embedded_docs.append({
        "id": doc["metadata"]["id"],
        "text": doc["text"],
        "vector": embedding,
        "metadata": doc["metadata"]
    })
print(f"✅ Generated {len(embedded_docs)} embeddings\n")

# Step 3: Store in Qdrant
print("🗄️  Setting up vector store...")
try:
    qdrant_client = QdrantClient(host="localhost", port=6333)
    
    # Clean up if exists
    collections = qdrant_client.get_collections().collections
    if any(c.name == "knowledge_base" for c in collections):
        qdrant_client.delete_collection("knowledge_base")
    
    # Create collection
    qdrant_client.create_collection(
        collection_name="knowledge_base",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
    )
    
    # Store vectors
    points = [
        PointStruct(
            id=hash(doc["id"]) % (10 ** 8),
            vector=doc["vector"],
            payload={"text": doc["text"], "source": doc["metadata"]["source"]}
        )
        for doc in embedded_docs
    ]
    qdrant_client.upsert(collection_name="knowledge_base", points=points)
    print(f"✅ Stored {len(points)} vectors in Qdrant\n")
    
except Exception as e:
    print(f"❌ Qdrant error: {e}")
    print("   Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant\n")
    exit(1)

# Step 4: Query and retrieve
print("🔍 Testing retrieval...")
query = "How does machine learning work?"
query_vector = client.embed(query, model_name="text-embedding-3-small")
print(f"Query: '{query}'")

search_results = qdrant_client.search(
    collection_name="knowledge_base",
    query_vector=query_vector,
    limit=2
)

retrieved_chunks = [
    {"text": hit.payload["text"], "score": hit.score}
    for hit in search_results
]
print(f"✅ Retrieved {len(retrieved_chunks)} relevant chunks\n")

# Step 5: Generate answer
print("💬 Generating answer with retrieved context...")
context = "\n".join([f"- {chunk['text']}" for chunk in retrieved_chunks])

prompt = f"""Answer the following question based on the context provided.

Context:
{context}

Question: {query}

Answer:"""

rag_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a helpful assistant. Answer questions based only on the provided context."
)

response = rag_client.invoke(prompt)

print(f"\n{'─' * 70}")
print("ANSWER:")
print('─' * 70)
print(response.text)
print('─' * 70)

print(f"\n✅ RAG pipeline test completed successfully!")
