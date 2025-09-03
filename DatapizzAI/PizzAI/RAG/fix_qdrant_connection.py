#!/usr/bin/env python3
"""
Script per risolvere il problema di connessione a Qdrant.

Questo script implementa esattamente il codice dell'utente ma con gestione errori robusta.
"""

import os
from dotenv import load_dotenv

load_dotenv()

def fix_original_code():
    """
    Versione corretta del codice originale dell'utente con gestione errori.
    """
    
    print("🔧 Risoluzione problema QdrantVectorstore")
    print("=" * 45)
    
    # 1. Test connessione Qdrant
    print("\n📡 Test 1: Verifica connessione Qdrant...")
    
    try:
        from qdrant_client import QdrantClient
        
        host = "localhost"
        port = int(os.getenv("QDRANT_PORT", 6333))
        
        print(f"   Connessione a {host}:{port}...")
        client = QdrantClient(host=host, port=port, timeout=5)
        client.get_collections()
        
        print("   ✅ Qdrant server raggiungibile!")
        qdrant_available = True
        
    except ImportError:
        print("   ❌ qdrant-client non installato")
        print("   💡 Installa con: pip install qdrant-client")
        return
    except Exception as e:
        print(f"   ❌ Qdrant server non raggiungibile: {e}")
        print(f"   💡 Avvia Qdrant con: docker run -p {port}:{port} qdrant/qdrant")
        qdrant_available = False
    
    # 2. Test creazione vectorstore
    print("\n🗄️  Test 2: Creazione QdrantVectorstore...")
    
    if qdrant_available:
        try:
            from datapizzai.vectorstores import QdrantVectorstore
            
            vectorstore = QdrantVectorstore(
                host="localhost",
                port=os.getenv("QDRANT_PORT", 6333),
                api_key=os.getenv("QDRANT_API"),
            )
            
            print("   ✅ QdrantVectorstore creato!")
            
            # 3. Test con dati finti (come nel codice originale)
            print("\n💾 Test 3: Operazioni vectorstore...")
            
            # Crea chunk di esempio per il test
            from datapizzai.type import Chunk, DenseEmbedding
            import numpy as np
            
            # Simula embedded_chunks (come nell'esempio originale)
            embedded_chunks = [
                Chunk(
                    id="test1",
                    text="Documento di test per QdrantVectorstore",
                    embeddings=[DenseEmbedding(
                        name="test_embedding",
                        vector=np.random.rand(384).tolist()
                    )],
                    metadata={"source": "test"}
                )
            ]
            
            # Test add (come nel codice originale)
            print("   📤 Test vectorstore.add()...")
            vectorstore.add(embedded_chunks, collection_name="documents")
            print("   ✅ Add completato!")
            
            # Test search (come nel codice originale) 
            print("   🔍 Test vectorstore.search()...")
            query_vector = np.random.rand(384).tolist()
            
            results = vectorstore.search(
                query_embedding=query_vector,
                collection_name="documents", 
                top_k=10
            )
            
            print(f"   ✅ Search completato! Trovati {len(results)} risultati")
            
            print(f"\n🎉 TUTTO FUNZIONA CORRETTAMENTE!")
            print(f"Il tuo codice originale dovrebbe funzionare ora.")
            
        except Exception as e:
            print(f"   ❌ Errore QdrantVectorstore: {e}")
    
    else:
        print("   ⏭️ Skip test vectorstore (server non disponibile)")
        
        # Soluzione alternativa
        print("\n🔄 Alternativa: Qdrant in-memory...")
        
        try:
            from datapizzai.vectorstores import QdrantVectorstore
            from qdrant_client import QdrantClient
            
            # Client in memoria (nessun server richiesto)
            memory_client = QdrantClient(":memory:")
            vectorstore = QdrantVectorstore(client=memory_client)
            
            print("   ✅ QdrantVectorstore in-memory creato!")
            print("   ⚠️  I dati si perderanno alla chiusura")
            
        except Exception as e:
            print(f"   ❌ Anche fallback in-memory fallito: {e}")

def show_quick_solutions():
    """Mostra soluzioni rapide al problema."""
    
    print("""
🚀 SOLUZIONI RAPIDE:

Soluzione 1 - Avvia Qdrant Server:
    docker run -p 6333:6333 qdrant/qdrant
    
    # In un altro terminale, esegui il tuo codice Python

Soluzione 2 - Qdrant in-memory (temporaneo):
    from qdrant_client import QdrantClient  
    from datapizzai.vectorstores import QdrantVectorstore
    
    # Sostituisci il tuo codice con:
    memory_client = QdrantClient(":memory:")
    vectorstore = QdrantVectorstore(client=memory_client)

Soluzione 3 - Verifica variabili ambiente:
    # Nel tuo .env file:
    QDRANT_HOST=localhost
    QDRANT_PORT=6333
    QDRANT_API_KEY=  # Lascia vuoto per istanze locali

Soluzione 4 - Usa Qdrant Cloud:
    # Registrati su https://cloud.qdrant.io
    # Ottieni cluster endpoint e API key
    QDRANT_HOST=your-cluster.qdrant.io
    QDRANT_API_KEY=your-api-key
""")

def create_fixed_code_example():
    """Crea un esempio del codice corretto per l'utente."""
    
    fixed_code = '''
# VERSIONE CORRETTA del tuo codice con gestione errori

import os
from dotenv import load_dotenv
from datapizzai.vectorstores import QdrantVectorstore
from qdrant_client import QdrantClient

load_dotenv()

def create_robust_vectorstore():
    """Crea vectorstore con gestione errori."""
    
    # Test connessione prima
    try:
        host = os.getenv("QDRANT_HOST", "localhost") 
        port = int(os.getenv("QDRANT_PORT", 6333))
        
        # Test connection
        test_client = QdrantClient(host=host, port=port, timeout=5)
        test_client.get_collections()
        
        # Se arriviamo qui, il server è raggiungibile
        return QdrantVectorstore(
            host=host,
            port=port,
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        
    except Exception as e:
        print(f"⚠️  Qdrant server non raggiungibile: {e}")
        print("🔄 Uso Qdrant in-memory come fallback...")
        
        # Fallback in-memory
        memory_client = QdrantClient(":memory:")
        return QdrantVectorstore(client=memory_client)

# USO:
vectorstore = create_robust_vectorstore()

# Il resto del tuo codice rimane uguale:
vectorstore.add(embedded_chunks, collection_name="documents")

results = vectorstore.search(
    query_embedding=query_vector,
    collection_name="documents",
    top_k=10
)
'''
    
    print("💻 CODICE CORRETTO per il tuo caso:")
    print("=" * 50)
    print(fixed_code)
    
    # Salva anche su file
    with open("fixed_qdrant_code.py", "w") as f:
        f.write(fixed_code)
    
    print(f"\n💾 Codice salvato in: fixed_qdrant_code.py")

if __name__ == "__main__":
    fix_original_code()
    print("\n" + "="*50)
    show_quick_solutions() 
    print("\n" + "="*50)
    create_fixed_code_example()


