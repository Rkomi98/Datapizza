# Guida rapida Qdrant per DatapizzAI

Il tuo errore `Collection 'documents' doesn't exist!` indica che devi **creare prima la collezione** prima di aggiungere dati.

## 🚀 Soluzione in 3 passi

### 1. Crea la collezione PRIMA di usarla

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Connetti a Qdrant
client = QdrantClient(host="localhost", port=6333)

# Crea collezione (una sola volta)
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=384,  # Dimensione dei tuoi embeddings
        distance=Distance.COSINE
    )
)
```

### 2. POI usa il vectorstore normalmente

```python
from datapizzai.vectorstores import QdrantVectorstore

vectorstore = QdrantVectorstore(
    host="localhost", 
    port=6333,
    https=False  # HTTP locale
)

# Ora puoi aggiungere dati
vectorstore.add(embedded_chunks, collection_name="documents")
```

### 3. Correggi i parametri di ricerca

Nel tuo codice, usa i parametri corretti:

```python
# ❌ SBAGLIATO (dal tuo test)
results = vectorstore.search(
    collection_name="documents",
    query_vector=query,      # ← parametro sbagliato
    k=5                      # ← parametro sbagliato
)

# ✅ CORRETTO 
results = vectorstore.search(
    query_embedding=query,   # ← parametro corretto
    collection_name="documents",
    top_k=5                  # ← parametro corretto
)
```

## 🧪 Test immediato

```bash
# Vai nella directory RAG
cd RAG/

# Esegui l'esempio completo e funzionante
python qdrant_working_example.py
```

Questo script:
- ✅ Testa la connessione
- ✅ Crea la collezione automaticamente
- ✅ Aggiunge documenti di esempio
- ✅ Fa ricerca con parametri corretti
- ✅ Mostra il pattern d'uso corretto

## 📝 Template veloce per il tuo codice

```python
#!/usr/bin/env python3
"""Template rapido per Qdrant + DatapizzAI"""

from datapizzai.vectorstores import QdrantVectorstore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# 1. Setup collezione (una sola volta)
def setup_collection(collection_name="documents", vector_size=384):
    client = QdrantClient(host="localhost", port=6333)
    
    # Controlla se esiste già
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(f"✅ Collezione {collection_name} creata")
    else:
        print(f"✅ Collezione {collection_name} già esistente")

# 2. Usa il vectorstore
def main():
    # Setup (esegui una volta)
    setup_collection()
    
    # Crea vectorstore
    vectorstore = QdrantVectorstore(host="localhost", port=6333, https=False)
    
    # Il tuo codice qui...
    # vectorstore.add(embedded_chunks, collection_name="documents")
    # results = vectorstore.search(query_embedding=query, collection_name="documents", top_k=10)

if __name__ == "__main__":
    main()
```

## 🔧 Debug rapido

Se hai ancora problemi:

```bash
# Verifica Qdrant attivo
curl http://localhost:6333/health

# Dashboard web
firefox http://localhost:6333/dashboard

# Lista collezioni esistenti
python -c "
from qdrant_client import QdrantClient
client = QdrantClient('localhost', 6333)
print('Collezioni:', [c.name for c in client.get_collections().collections])
"
```

## 💡 Punto chiave

**Qdrant richiede che tu crei esplicitamente le collezioni** prima dell'uso, specificando:
- **Nome collezione**
- **Dimensione vettori** (es. 384 per molti modelli embedding)
- **Metrica di distanza** (COSINE, EUCLIDEAN, DOT)

Una volta creata, puoi usare normalmente `vectorstore.add()` e `vectorstore.search()`.

Il tuo server Qdrant è **già attivo** ✅, serve solo creare la collezione! 🚀
