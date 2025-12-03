# Guida alla pipeline RAG con datapizza-ai

Questa guida spiega come usare la pipeline RAG per indicizzare documenti e interrogarli tramite chatbot.

## Indice

1. [Architettura](#1-architettura)
2. [Setup](#2-setup)
3. [Uso](#3-uso)
4. [Spiegazione del codice](#4-spiegazione-del-codice)

---

## 1. Architettura

Il sistema è diviso in due fasi indipendenti:

### Fase 1: ingestion (una tantum)

```
PDF → DoclingParser → NodeSplitter → ChunkEmbedder → Qdrant (locale)
```

Il documento viene processato e salvato in una cartella locale `./qdrant_data`. I dati persistono tra le esecuzioni.

### Fase 2: chatbot (quando serve)

```
Query utente → Embedding → Ricerca Qdrant → Contesto → LLM → Risposta
```

Il chatbot carica il database locale e risponde solo in base al contenuto indicizzato.

---

## 2. Setup

### 2.1 Installazione dipendenze

```bash
cd /home/mcalcaterra/Documenti/GitHub/Datapizza/Ducati
source .venv/bin/activate
uv sync
```

### 2.2 Configurazione API key

Crea un file `.env` nella root del progetto:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

---

## 3. Uso

### 3.1 Ingestion di un documento

```bash
python rag_pipeline.py ingest data/MonsterRev02.pdf
```

Output:

```
==================================================
Ingestion documento
==================================================

File: data/MonsterRev02.pdf
Collection: ducati_docs
Storage: ./qdrant_data

Creazione vector store...
Elaborazione in corso...

Ingestion completata!
I dati sono salvati in: /path/to/qdrant_data
```

I dati vengono salvati localmente. L'ingestion va eseguita una sola volta per documento.

### 3.2 Avvio del chatbot

```bash
python rag_pipeline.py chat
```

Output:

```
==================================================
Chatbot Ducati
==================================================

Caricamento database...
Database caricato!

Scrivi le tue domande. Digita 'exit' per uscire.

--------------------------------------------------

Tu: Quali sono le caratteristiche del motore?

Assistente: Il motore è un bicilindrico a V di 90°...
```

Il chatbot risponde esclusivamente in base al contenuto del documento indicizzato.

---

## 4. Spiegazione del codice

### 4.1 Configurazione globale

```python
COLLECTION_NAME = "ducati_docs"
QDRANT_PATH = "./qdrant_data"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
LLM_MODEL = "gpt-5.1"
```

- `COLLECTION_NAME`: nome logico per raggruppare i documenti in Qdrant
- `QDRANT_PATH`: cartella locale dove Qdrant salva i dati
- `EMBEDDING_MODEL`: modello OpenAI per generare i vettori
- `EMBEDDING_DIM`: dimensione dei vettori (1536 per text-embedding-3-small)
- `LLM_MODEL`: modello per generare le risposte

### 4.2 Setup ambiente

```python
def setup_environment():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Errore: OPENAI_API_KEY non trovata nel file .env")
        sys.exit(1)
    return api_key
```

Carica la API key dal file `.env`. Termina con errore se non presente.

### 4.3 Vector store con persistenza

```python
def get_vectorstore(create_collection: bool = False) -> QdrantVectorstore:
    vectorstore = QdrantVectorstore(path=QDRANT_PATH)
    
    if create_collection:
        vectorstore.create_collection(
            COLLECTION_NAME,
            vector_config=[
                VectorConfig(name=EMBEDDING_MODEL, dimensions=EMBEDDING_DIM)
            ]
        )
    
    return vectorstore
```

- `path=QDRANT_PATH`: usa storage locale invece di `:memory:`
- `create_collection`: True solo durante l'ingestion
- `VectorConfig`: definisce il nome e le dimensioni del vettore

### 4.4 Pipeline di ingestion

```python
pipeline = IngestionPipeline(
    modules=[
        DoclingParser(),
        NodeSplitter(max_char=1000),
        ChunkEmbedder(client=embedder),
    ],
    vector_store=vectorstore,
    collection_name=COLLECTION_NAME
)
```

La pipeline esegue in sequenza:

1. **DoclingParser()**: estrae testo strutturato dal PDF
2. **NodeSplitter(max_char=1000)**: divide in chunk di max 1000 caratteri
3. **ChunkEmbedder(client=embedder)**: genera un vettore per ogni chunk

I chunk vengono automaticamente salvati nel vector store.

### 4.5 Chatbot semplificato

```python
# Genera embedding della query
query_embedding = embedder.embed(query)

# Cerca chunk rilevanti
results = vectorstore.search(
    query_vector=query_embedding,
    collection_name=COLLECTION_NAME,
    k=5
)
```

- `embedder.embed(query)`: converte la domanda in vettore
- `vectorstore.search()`: trova i 5 chunk più simili

```python
# Costruisci contesto dai chunk recuperati
context = "\n---\n".join([chunk.text for chunk in results])

# Prompt per l'LLM
prompt = f"""Sei un assistente tecnico. Rispondi alla domanda dell'utente basandoti ESCLUSIVAMENTE sul contesto fornito.
Se l'informazione non è presente nel contesto, rispondi: "Non ho trovato questa informazione nel documento."
Non inventare informazioni.

CONTESTO:
{context}

DOMANDA: {query}

RISPOSTA:"""

# Genera risposta
response = llm.invoke(prompt)
```

Il prompt istruisce l'LLM a:
- Usare solo il contesto fornito
- Non inventare informazioni
- Dichiarare quando non trova l'informazione

---

## Riferimenti

- [Documentazione datapizza-ai](https://docs.datapizza.ai/0.0.9/Guides/RAG/rag/)
- [Qdrant documentation](https://qdrant.tech/documentation/)
