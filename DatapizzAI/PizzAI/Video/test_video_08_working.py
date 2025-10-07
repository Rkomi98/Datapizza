import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.memory import Memory
from datapizza.type import ROLE, TextBlock
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

load_dotenv()

print("=" * 70)
print("RAG Implementation Test - Working Version")
print("=" * 70)

# Step 1: Setup client
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o"
)
print("✅ Client initialized")

# Step 2: Prepare documents (simulating parsing)
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
print(f"✅ Prepared {len(documents)} document chunks")

# Step 3: Generate embeddings
print("\n📊 Generating embeddings...")
embedded_docs = []
for doc in documents:
    # Use the client's embed method with explicit embedding model
    embedding = client.embed(doc["text"], model_name="text-embedding-3-small")
    embedded_docs.append({
        "id": doc["metadata"]["id"],
        "text": doc["text"],
        "vector": embedding,
        "metadata": doc["metadata"]
    })
print(f"✅ Generated {len(embedded_docs)} embeddings")

# Step 4: Store in Qdrant (check if Qdrant is running)
print("\n🗄️  Setting up vector store...")
try:
    qdrant_client = QdrantClient(host="localhost", port=6333)
    
    # Check if collection exists, delete if it does
    collections = qdrant_client.get_collections().collections
    if any(c.name == "test_kb" for c in collections):
        qdrant_client.delete_collection("test_kb")
    
    # Create collection
    qdrant_client.create_collection(
        collection_name="test_kb",
        vectors_config=VectorParams(size=len(embedded_docs[0]["vector"]), distance=Distance.COSINE)
    )
    
    # Store vectors
    points = [
        PointStruct(
            id=hash(doc["id"]) % (10 ** 8),  # Convert string id to int
            vector=doc["vector"],
            payload={"text": doc["text"], "source": doc["metadata"]["source"]}
        )
        for doc in embedded_docs
    ]
    qdrant_client.upsert(collection_name="test_kb", points=points)
    print(f"✅ Stored {len(points)} vectors in Qdrant")
    QDRANT_AVAILABLE = True
    
except Exception as e:
    print(f"⚠️  Qdrant not available: {e}")
    print("   Continuing with in-memory storage...")
    QDRANT_AVAILABLE = False

# Step 5: Query and retrieve
print("\n🔍 Testing retrieval...")
query = "How does machine learning work?"
query_embedding = client.embed(query, model_name="text-embedding-3-small")
print(f"Query: '{query}'")

if QDRANT_AVAILABLE:
    # Search in Qdrant
    search_results = qdrant_client.search(
        collection_name="test_kb",
        query_vector=query_embedding,
        limit=2
    )
    
    retrieved_chunks = [
        {"text": hit.payload["text"], "score": hit.score}
        for hit in search_results
    ]
    print(f"✅ Retrieved {len(retrieved_chunks)} relevant chunks")
    for i, chunk in enumerate(retrieved_chunks, 1):
        print(f"   {i}. (score: {chunk['score']:.3f}) {chunk['text'][:60]}...")
else:
    # Fallback: simple cosine similarity
    import numpy as np
    
    def cosine_similarity(v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    
    scores = [
        (doc, cosine_similarity(query_embedding, doc["vector"]))
        for doc in embedded_docs
    ]
    scores.sort(key=lambda x: x[1], reverse=True)
    
    retrieved_chunks = [
        {"text": doc["text"], "score": score}
        for doc, score in scores[:2]
    ]
    print(f"✅ Retrieved {len(retrieved_chunks)} relevant chunks (in-memory)")
    for i, chunk in enumerate(retrieved_chunks, 1):
        print(f"   {i}. (score: {chunk['score']:.3f}) {chunk['text'][:60]}...")

# Step 6: Generate answer with context
print("\n💬 Generating answer with retrieved context...")

# Build context from retrieved chunks
context = "\n".join([f"- {chunk['text']}" for chunk in retrieved_chunks])

# Create prompt with context
prompt = f"""Answer the following question based on the context provided.

Context:
{context}

Question: {query}

Answer:"""

# Generate response with system prompt
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
print(f"   - Embeddings: ✓")
print(f"   - Vector store: {'✓' if QDRANT_AVAILABLE else '✓ (in-memory)'}")
print(f"   - Retrieval: ✓")
print(f"   - Generation: ✓")

