# Risoluzione errore Qdrant "Connection refused"

Il tuo errore `ConnectError: [Errno 111] Connection refused` indica che **Qdrant server non è in esecuzione**.

## 🚀 Soluzioni immediate

### Soluzione 1: Avvia Qdrant con Docker (raccomandato)

```bash
# Avvio semplice
docker run -p 6333:6333 qdrant/qdrant

# Avvio con persistenza dati
mkdir qdrant_storage
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant

# Con Docker Compose (persistente + configurato)
docker-compose -f docker-compose-qdrant.yml up -d
```

### Soluzione 2: Fallback in-memory (temporaneo)

Modifica il tuo codice per usare Qdrant in memoria:

```python
from qdrant_client import QdrantClient
from datapizzai.vectorstores import QdrantVectorstore

# Invece del tuo codice originale:
# vectorstore = QdrantVectorstore(host="localhost", port=...)

# Usa questo (nessun server richiesto):
memory_client = QdrantClient(":memory:")
vectorstore = QdrantVectorstore(client=memory_client)

# Il resto del codice rimane uguale
vectorstore.add(embedded_chunks, collection_name="documents")
results = vectorstore.search(query_embedding=query_vector, collection_name="documents", top_k=10)
```

### Soluzione 3: Codice robusto con auto-fallback

```python
import os
from qdrant_client import QdrantClient
from datapizzai.vectorstores import QdrantVectorstore

def create_robust_vectorstore():
    """Crea vectorstore con gestione automatica degli errori."""
    try:
        # Prova connessione server
        host = os.getenv("QDRANT_HOST", "localhost") 
        port = int(os.getenv("QDRANT_PORT", 6333))
        
        test_client = QdrantClient(host=host, port=port, timeout=5)
        test_client.get_collections()  # Test connessione
        
        print(f"✅ Usando Qdrant server su {host}:{port}")
        return QdrantVectorstore(host=host, port=port, api_key=os.getenv("QDRANT_API_KEY"))
        
    except Exception as e:
        print(f"⚠️ Server non raggiungibile, uso in-memory: {e}")
        memory_client = QdrantClient(":memory:")
        return QdrantVectorstore(client=memory_client)

# Uso
vectorstore = create_robust_vectorstore()
```

## 🔧 Test e debug

### Test connessione rapido

```python
# Script per testare la connessione
python fix_qdrant_connection.py
```

### Test completo

```python
# Demo completa con gestione errori  
python robust_qdrant_example.py
```

### Verifica status Qdrant

```bash
# Verifica se Qdrant è in esecuzione
curl http://localhost:6333/health

# Oppure apri nel browser:
# http://localhost:6333/dashboard
```

## 📋 Configurazione .env

Crea/aggiorna il tuo file `.env`:

```env
# Qdrant locale (default)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=

# Per Qdrant Cloud (alternativa)
# QDRANT_HOST=your-cluster.qdrant.io  
# QDRANT_API_KEY=your-cloud-api-key
```

## 🐳 Comandi Docker utili

```bash
# Avvio persistente con Docker Compose
docker-compose -f docker-compose-qdrant.yml up -d

# Verifica status
docker-compose -f docker-compose-qdrant.yml ps

# Logs
docker-compose -f docker-compose-qdrant.yml logs -f qdrant

# Stop
docker-compose -f docker-compose-qdrant.yml down

# Stop e rimozione volumi (ATTENZIONE: cancella dati)
docker-compose -f docker-compose-qdrant.yml down -v
```

## ✅ Verifica finale

Una volta avviato Qdrant, il tuo codice originale dovrebbe funzionare:

```python
from datapizzai.vectorstores import QdrantVectorstore

vectorstore = QdrantVectorstore(
    host="localhost",
    port=os.getenv("QDRANT_PORT"),
    api_key=os.getenv("QDRANT_API"),
)

# Dovrebbe funzionare ora senza errori
vectorstore.add(embedded_chunks, collection_name="documents")
results = vectorstore.search(query_embedding=query_vector, collection_name="documents", top_k=10)
```

## 🔗 Link utili

- **Qdrant Dashboard**: http://localhost:6333/dashboard (quando server attivo)
- **Documentazione Qdrant**: https://qdrant.tech/documentation/
- **Qdrant Cloud** (alternativa hosted): https://cloud.qdrant.io

## 🆘 Se hai ancora problemi

1. **Dipendenze mancanti**:
   ```bash
   pip install qdrant-client datapizzai numpy
   ```

2. **Porta occupata**:
   ```bash
   # Trova processo su porta 6333
   lsof -i :6333
   
   # O usa porta diversa
   docker run -p 6334:6333 qdrant/qdrant
   # Poi aggiorna QDRANT_PORT=6334 nel .env
   ```

3. **Permessi Docker**:
   ```bash
   # Se hai errori di permessi
   sudo docker run -p 6333:6333 qdrant/qdrant
   ```

4. **Usa gli script di debug**:
   ```bash
   python fix_qdrant_connection.py    # Diagnosi e fix
   python robust_qdrant_example.py    # Demo completa
   ```

La soluzione più rapida è di gran lunga **avviare Qdrant con Docker** come mostrato nella Soluzione 1! 🚀


