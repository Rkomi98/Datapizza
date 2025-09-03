#!/usr/bin/env python3
"""
Esempio robusto per l'uso di QdrantVectorstore con gestione errori.

Questo script gestisce i problemi comuni:
1. Qdrant server non in esecuzione
2. Variabili d'ambiente mancanti
3. Fallback a vectorstore in-memory
4. Test di connessione automatici
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def test_qdrant_connection(host: str = "localhost", port: int = 6333) -> bool:
    """
    Testa la connessione a Qdrant server.
    
    Returns:
        True se la connessione è riuscita, False altrimenti
    """
    try:
        from qdrant_client import QdrantClient
        
        logger.info(f"🔄 Test connessione Qdrant su {host}:{port}...")
        client = QdrantClient(host=host, port=port, timeout=5)
        
        # Prova a ottenere le collezioni per testare la connessione
        collections = client.get_collections()
        
        logger.info(f"✅ Qdrant connesso! Collezioni trovate: {len(collections.collections)}")
        return True
        
    except ImportError:
        logger.error("❌ qdrant-client non installato. Installa con: pip install qdrant-client")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Qdrant non raggiungibile: {e}")
        return False


def start_qdrant_instructions():
    """Mostra istruzioni per avviare Qdrant."""
    print("""
🚀 COME AVVIARE QDRANT SERVER:

Opzione 1 - Docker (raccomandato):
    docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

Opzione 2 - Docker con persistenza:
    mkdir qdrant_storage
    docker run -p 6333:6333 -p 6334:6334 \\
        -v $(pwd)/qdrant_storage:/qdrant/storage:z \\
        qdrant/qdrant

Opzione 3 - Installazione locale:
    # Segui la guida: https://qdrant.tech/documentation/guides/installation/
    
Una volta avviato, il server sarà disponibile su:
- REST API: http://localhost:6333
- Web UI: http://localhost:6333/dashboard
""")


def create_robust_vectorstore():
    """
    Crea un vectorstore robusto con fallback.
    
    Returns:
        (vectorstore, connection_type): tupla con vectorstore e tipo di connessione
    """
    
    # Configurazione da variabili d'ambiente
    qdrant_host = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
    qdrant_api_key = os.getenv("QDRANT_API_KEY")  # Opzionale per installazioni locali
    
    logger.info(f"🔧 Configurazione Qdrant: {qdrant_host}:{qdrant_port}")
    
    # Test connessione a Qdrant server
    if test_qdrant_connection(qdrant_host, qdrant_port):
        try:
            from datapizzai.vectorstores import QdrantVectorstore
            
            vectorstore = QdrantVectorstore(
                host=qdrant_host,
                port=qdrant_port,
                api_key=qdrant_api_key,
            )
            
            logger.info("✅ QdrantVectorstore creato (server remoto/locale)")
            return vectorstore, "qdrant_server"
            
        except Exception as e:
            logger.error(f"❌ Errore creazione QdrantVectorstore: {e}")
    
    # Fallback: Qdrant in-memory
    logger.warning("🔄 Fallback a Qdrant in-memory...")
    try:
        from qdrant_client import QdrantClient
        from datapizzai.vectorstores import QdrantVectorstore
        
        # Client Qdrant in memoria (nessun server richiesto)
        memory_client = QdrantClient(":memory:")
        
        # Crea vectorstore con client in-memory
        vectorstore = QdrantVectorstore(client=memory_client)
        
        logger.info("✅ QdrantVectorstore in-memory creato")
        return vectorstore, "qdrant_memory"
        
    except Exception as e:
        logger.error(f"❌ Fallback in-memory fallito: {e}")
        return None, "failed"


def demo_vectorstore_usage():
    """Dimostra l'uso robusto del vectorstore."""
    
    print("🚀 Demo Robust Qdrant Vectorstore Usage")
    print("=" * 50)
    
    # Crea vectorstore con gestione errori
    vectorstore, connection_type = create_robust_vectorstore()
    
    if not vectorstore:
        print("❌ Impossibile creare vectorstore")
        start_qdrant_instructions()
        return
    
    print(f"✅ Vectorstore attivo: {connection_type}")
    print()
    
    # Crea alcuni chunk di esempio per il test
    try:
        from datapizzai.type import Chunk, DenseEmbedding
        import numpy as np
        
        print("📝 Creazione chunk di esempio...")
        
        # Simula alcuni embeddings (normalmente li otterresti da un modello)
        sample_chunks = [
            Chunk(
                id="doc1_chunk1",
                text="DatapizzAI è una libreria per costruire applicazioni AI",
                embeddings=[DenseEmbedding(
                    name="test_embedding",
                    vector=np.random.rand(384).tolist()  # Embedding simulato
                )],
                metadata={"source": "documentation", "topic": "intro"}
            ),
            Chunk(
                id="doc1_chunk2", 
                text="Il sistema RAG combina retrieval e generazione di testo",
                embeddings=[DenseEmbedding(
                    name="test_embedding",
                    vector=np.random.rand(384).tolist()
                )],
                metadata={"source": "documentation", "topic": "rag"}
            ),
            Chunk(
                id="doc1_chunk3",
                text="QdrantVectorstore gestisce la memorizzazione degli embeddings",
                embeddings=[DenseEmbedding(
                    name="test_embedding", 
                    vector=np.random.rand(384).tolist()
                )],
                metadata={"source": "documentation", "topic": "vectorstore"}
            )
        ]
        
        collection_name = "test_documents"
        
        # Test aggiunta documenti
        print(f"💾 Aggiunta {len(sample_chunks)} chunk alla collezione '{collection_name}'...")
        
        try:
            vectorstore.add(sample_chunks, collection_name=collection_name)
            print("✅ Chunk aggiunti con successo")
        except Exception as e:
            print(f"❌ Errore aggiunta chunk: {e}")
            return
        
        # Test ricerca
        print("\n🔍 Test ricerca similarità...")
        
        # Query di esempio (embedding simulato)
        query_vector = np.random.rand(384).tolist()
        
        try:
            results = vectorstore.search(
                query_embedding=query_vector,
                collection_name=collection_name,
                top_k=2
            )
            
            print(f"✅ Ricerca completata! Trovati {len(results)} risultati:")
            
            for i, result in enumerate(results, 1):
                # I risultati di Qdrant hanno structure diversa, gestiamo entrambi i casi
                if hasattr(result, 'payload'):
                    # Qdrant result object
                    text = result.payload.get('text', 'N/A')
                    score = result.score
                    metadata = result.payload.get('metadata', {})
                else:
                    # Dictionary result  
                    text = result.get('text', result.get('payload', {}).get('text', 'N/A'))
                    score = result.get('score', 0)
                    metadata = result.get('metadata', {})
                
                print(f"  {i}. Score: {score:.4f}")
                print(f"     Testo: {text[:80]}{'...' if len(text) > 80 else ''}")
                print(f"     Topic: {metadata.get('topic', 'N/A')}")
                print()
                
        except Exception as e:
            print(f"❌ Errore ricerca: {e}")
            logger.exception("Dettagli errore ricerca:")
            return
        
        print("🎯 Test completato con successo!")
        
        # Statistiche finali
        print(f"\n📊 STATISTICHE:")
        print(f"Tipo connessione: {connection_type}")
        print(f"Collezione: {collection_name}")
        print(f"Chunk inseriti: {len(sample_chunks)}")
        print(f"Dimensione embedding: 384")
        
        if connection_type == "qdrant_memory":
            print("⚠️  Nota: Usando Qdrant in-memory, i dati si perderanno alla chiusura")
            print("💡 Per persistenza permanente, avvia Qdrant server")
        
    except ImportError as e:
        print(f"❌ Dipendenze mancanti: {e}")
        print("Installa con: pip install numpy datapizzai")
    except Exception as e:
        print(f"❌ Errore durante demo: {e}")
        logger.exception("Dettagli errore demo:")


def show_environment_template():
    """Mostra template per il file .env."""
    
    print("""
📋 TEMPLATE FILE .ENV per Qdrant:

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your_api_key_if_needed

# Solo per Qdrant Cloud (opzionale)
# QDRANT_HOST=your-cluster.qdrant.io
# QDRANT_API_KEY=your_cloud_api_key

# Altre configurazioni utili
OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_API_KEY=your_azure_key  
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
""")


def main():
    """Funzione principale con menu interattivo."""
    
    print("🎯 Qdrant Vectorstore - Gestione Robusta Errori")
    print("=" * 55)
    
    while True:
        print("""
Scegli un'azione:
1. 🧪 Test connessione Qdrant
2. 🚀 Demo vectorstore completo  
3. 📋 Mostra template .env
4. 📖 Istruzioni avvio Qdrant
5. 🚪 Esci
""")
        
        choice = input("Scelta (1-5): ").strip()
        
        if choice == "1":
            host = input(f"Host Qdrant [{os.getenv('QDRANT_HOST', 'localhost')}]: ").strip()
            port = input(f"Porta Qdrant [{os.getenv('QDRANT_PORT', '6333')}]: ").strip()
            
            host = host or os.getenv('QDRANT_HOST', 'localhost')
            port = int(port or os.getenv('QDRANT_PORT', '6333'))
            
            success = test_qdrant_connection(host, port)
            if not success:
                start_qdrant_instructions()
                
        elif choice == "2":
            demo_vectorstore_usage()
            
        elif choice == "3":
            show_environment_template()
            
        elif choice == "4":
            start_qdrant_instructions()
            
        elif choice == "5":
            print("👋 Arrivederci!")
            break
            
        else:
            print("❌ Scelta non valida")
        
        input("\nPremi ENTER per continuare...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        logger.exception("Errore dettagliato:")


