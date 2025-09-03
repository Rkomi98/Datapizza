#!/usr/bin/env python3
"""
Esempio completo e funzionante di QdrantVectorstore
Risolve il problema "Collection doesn't exist" creando prima la collection.

Questo esempio mostra l'uso corretto completo di QdrantVectorstore con:
1. Connessione locale senza API key 
2. Creazione della collection PRIMA dell'uso
3. Aggiunta di documenti
4. Ricerca semantica
"""

import os
import logging
import numpy as np
import uuid
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_vectorstore_with_collection():
    """
    Crea un QdrantVectorstore e la sua collection in modo corretto.
    
    Returns:
        vectorstore: Istanza di QdrantVectorstore pronta all'uso
    """
    print("🔧 Creazione QdrantVectorstore...")
    
    # Importa le classi necessarie
    from datapizzai.vectorstores import QdrantVectorstore, VectorConfig, Distance
    from datapizzai.type import EmbeddingFormat
    
    # 1. Crea il vectorstore (SENZA api_key per locale)
    vectorstore = QdrantVectorstore(
        host="localhost",
        port=6333,
        # NON specificare api_key per connessioni locali HTTP
        # api_key=os.getenv("QDRANT_API"),  # <-- Questo causa l'errore SSL
    )
    
    print("✅ QdrantVectorstore creato")
    
    # 2. Definisci configurazione del vettore
    # IMPORTANTE: Modifica le dimensioni in base al tuo modello di embedding
    vector_config = [
        VectorConfig(
            name="dense",              # Nome del vettore
            dimensions=384,            # 384 per sentence-transformers, 1536 per OpenAI ada-002
            distance=Distance.COSINE,  # Metrica di distanza
            format=EmbeddingFormat.DENSE
        )
    ]
    
    collection_name = "documents"
    
    # 3. Crea la collection SE NON esiste già
    try:
        collections = vectorstore.get_collections()
        collection_exists = any(col.name == collection_name for col in collections.collections)
        
        if not collection_exists:
            print(f"📝 Creazione collection '{collection_name}'...")
            vectorstore.create_collection(
                collection_name=collection_name, 
                vector_config=vector_config
            )
            print(f"✅ Collection '{collection_name}' creata!")
        else:
            print(f"ℹ️  Collection '{collection_name}' già esistente")
            
    except Exception as e:
        logger.error(f"❌ Errore nella creazione collection: {e}")
        raise
    
    return vectorstore, collection_name


def create_sample_embedded_chunks():
    """
    Crea chunk di esempio con embeddings per il test.
    
    Returns:
        list[Chunk]: Lista di chunk con embeddings
    """
    print("📄 Creazione chunk di esempio...")
    
    from datapizzai.type import Chunk, DenseEmbedding
    
    # Crea chunk con embeddings simulati
    # In un caso reale, useresti un embedder vero come NodeEmbedder o ClientEmbedder
    # IMPORTANTE: Qdrant richiede UUID o interi come ID, non stringhe semplici
    doc_ids = [str(uuid.uuid4()) for _ in range(4)]  # Genera UUID validi
    
    embedded_chunks = [
        Chunk(
            id=doc_ids[0],  # UUID valido
            text="DatapizzAI è una libreria Python per costruire applicazioni AI avanzate",
            embeddings=[DenseEmbedding(
                name="dense",  # Nome deve corrispondere alla config del vettore
                vector=np.random.rand(384).tolist()  # Embedding simulato
            )],
            metadata={"source": "docs", "topic": "intro", "category": "library"}
        ),
        Chunk(
            id=doc_ids[1], 
            text="Il sistema RAG combina retrieval di documenti con generazione di testo usando LLM",
            embeddings=[DenseEmbedding(
                name="dense",
                vector=np.random.rand(384).tolist()
            )],
            metadata={"source": "docs", "topic": "rag", "category": "technique"}
        ),
        Chunk(
            id=doc_ids[2],
            text="QdrantVectorstore gestisce la memorizzazione e ricerca di embeddings vettoriali",
            embeddings=[DenseEmbedding(
                name="dense", 
                vector=np.random.rand(384).tolist()
            )],
            metadata={"source": "docs", "topic": "vectorstore", "category": "component"}
        ),
        Chunk(
            id=doc_ids[3],
            text="Gli embeddings trasformano testo in rappresentazioni numeriche dense per il machine learning",
            embeddings=[DenseEmbedding(
                name="dense",
                vector=np.random.rand(384).tolist()
            )],
            metadata={"source": "docs", "topic": "embeddings", "category": "concept"}
        )
    ]
    
    print(f"✅ Creati {len(embedded_chunks)} chunk con embeddings")
    return embedded_chunks, doc_ids


def demo_complete_workflow():
    """
    Dimostra il workflow completo e corretto di QdrantVectorstore.
    """
    print("🚀 Demo Completo QdrantVectorstore")
    print("=" * 60)
    
    try:
        # 1. Crea vectorstore e collection
        vectorstore, collection_name = create_vectorstore_with_collection()
        
        # 2. Crea chunk di esempio
        embedded_chunks, doc_ids = create_sample_embedded_chunks()
        
        # 3. Aggiungi documenti al vectorstore
        print(f"\n💾 Aggiunta {len(embedded_chunks)} documenti alla collection...")
        vectorstore.add(embedded_chunks, collection_name=collection_name)
        print("✅ Documenti aggiunti con successo!")
        
        # 4. Test ricerca semantica
        print("\n🔍 Test ricerca semantica...")
        
        # Query di esempio (in un caso reale useresti un vero embedding della query)
        query_text = "Come funziona il sistema RAG?"
        query_vector = np.random.rand(384).tolist()  # Embedding simulato
        
        print(f"   Query: '{query_text}'")
        print("   Esecuzione ricerca...")
        
        results = vectorstore.search(
            query_vector=query_vector,  # Era query_embedding nel tuo codice originale
            collection_name=collection_name,
            k=3  # Parametro corretto nella libreria datapizzai
        )
        
        print(f"✅ Ricerca completata! Trovati {len(results)} risultati:\n")
        
        # 5. Mostra risultati
        for i, result in enumerate(results, 1):
            print(f"   🔹 Risultato {i}:")
            print(f"      ID: {result.id}")
            print(f"      Testo: {result.text}")
            print(f"      Topic: {result.metadata.get('topic', 'N/A')}")
            print(f"      Category: {result.metadata.get('category', 'N/A')}")
            if hasattr(result, 'score'):
                print(f"      Score: {result.score:.4f}")
            print()
        
        # 6. Test retrieve (recupero per ID)
        print("🎯 Test retrieve per ID...")
        retrieved = vectorstore.retrieve(
            collection_name=collection_name,
            ids=[doc_ids[0], doc_ids[2]]  # Usa UUID reali
        )
        print(f"✅ Recuperati {len(retrieved)} documenti per ID")
        
        # 7. Informazioni collection
        print("📊 Informazioni collection:")
        collections = vectorstore.get_collections()
        for col in collections.collections:
            if col.name == collection_name:
                print(f"   Nome: {col.name}")
                print(f"   Status: {col.status}")
                break
        
        print(f"\n🎉 WORKFLOW COMPLETO FUNZIONANTE!")
        print("   Il tuo codice originale ora dovrebbe funzionare seguendo questo schema.")
        
    except Exception as e:
        logger.error(f"❌ Errore nel workflow: {e}")
        logger.exception("Dettagli dell'errore:")
        
        # Suggerimenti per il debug
        print(f"\n🔧 Suggerimenti per il debug:")
        print(f"1. Verifica che Qdrant sia in esecuzione: curl http://localhost:6333")
        print(f"2. Controlla che non ci sia firewall che blocchi la porta 6333")
        print(f"3. Se usi Docker: docker ps per verificare che il container sia up")
        print(f"4. Se persistono errori SSL: rimuovi completamente l'api_key per locale")


def your_fixed_original_code():
    """
    La versione corretta del tuo codice originale.
    """
    print("\n" + "="*60)
    print("🔧 IL TUO CODICE ORIGINALE CORRETTO:")
    print("="*60)
    
    from datapizzai.vectorstores import QdrantVectorstore, VectorConfig, Distance
    from datapizzai.type import EmbeddingFormat
    import os

    # Crea vectorstore SENZA api_key per locale
    vectorstore = QdrantVectorstore(
        host="localhost",
        port=6333,
        # api_key=os.getenv("QDRANT_API"),  # <-- RIMUOVI QUESTA RIGA per locale
    )

    # AGGIUNGI: Crea collection prima dell'uso
    vector_config = [
        VectorConfig(
            name="dense",
            dimensions=384,  # Modifica in base al tuo modello embedding
            distance=Distance.COSINE,
            format=EmbeddingFormat.DENSE
        )
    ]

    collection_name = "documents"
    
    # Verifica e crea collection se necessario
    collections = vectorstore.get_collections()
    collection_exists = any(col.name == collection_name for col in collections.collections)
    
    if not collection_exists:
        vectorstore.create_collection(
            collection_name=collection_name, 
            vector_config=vector_config
        )
        print(f"✅ Collection '{collection_name}' creata")

    # ORA il tuo codice originale funziona:
    # IMPORTANTE: I chunk devono avere ID UUID o interi, non stringhe semplici!
    # 
    # vectorstore.add(embedded_chunks, collection_name="documents")
    # 
    # results = vectorstore.search(
    #     query_vector=query_vector,  # Il parametro corretto nella libreria
    #     collection_name="documents",
    #     k=10  # Il parametro corretto nella libreria
    # )
    
    print("✅ Il tuo codice è ora pronto per funzionare!")


if __name__ == "__main__":
    # Esegui demo completo
    demo_complete_workflow()
    
    # Mostra il codice originale corretto
    your_fixed_original_code()
