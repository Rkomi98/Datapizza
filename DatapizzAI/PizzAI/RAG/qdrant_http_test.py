"""
Quick test for Qdrant over HTTP (no TLS) - VERSIONE CORRETTA

CORREZIONI APPLICATE:
1. Crea collezione PRIMA di aggiungere dati
2. Usa parametri corretti per search (query_embedding, top_k)
"""

import numpy as np
from datapizzai.vectorstores import QdrantVectorstore
from datapizzai.type import Chunk, DenseEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


def create_collection_if_needed(collection_name="documents", vector_size=384):
    """CORREZIONE: Crea collezione se non esiste."""
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        # Controlla collezioni esistenti
        collections = [c.name for c in client.get_collections().collections]
        
        if collection_name not in collections:
            print(f"Creating collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Collection '{collection_name}' created")
        else:
            print(f"✅ Collection '{collection_name}' already exists")
        return True
    except Exception as e:
        print(f"❌ Error creating collection: {e}")
        return False


def main():
    print("Creating QdrantVectorstore with explicit HTTP URL...")
    
    # CORREZIONE 1: Crea collezione PRIMA
    if not create_collection_if_needed("documents", 384):
        return
    
    # Use explicit HTTP by setting https=False
    vectorstore = QdrantVectorstore(host="localhost", port=6333, https=False)

    print("Adding one sample chunk to collection 'documents'...")
    emb = np.random.rand(384).astype(float).tolist()
    import uuid
    chunk = Chunk(
        id=str(uuid.uuid4()),
        text="Documento di test per connessione HTTP a Qdrant",
        embeddings=[DenseEmbedding(name="test", vector=emb)],
        metadata={"source": "qdrant_http_test"},
    )
    vectorstore.add([chunk], collection_name="documents")
    print("✅ Add OK")

    print("Searching similar for a random query vector...")
    query = np.random.rand(384).astype(float).tolist()
    
    # CORREZIONE 2: Usa parametri corretti
    results = vectorstore.search(
        query_embedding=query,  # ← CORRETTO: era query_vector
        collection_name="documents", 
        top_k=5,               # ← CORRETTO: era k
    )
    print(f"✅ Search OK. Got {len(results)} results")


if __name__ == "__main__":
    main()
