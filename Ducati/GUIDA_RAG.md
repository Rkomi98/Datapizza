# Guida alla pipeline RAG con datapizza-ai

Questa guida spiega passo per passo come costruire una pipeline RAG (Retrieval-Augmented Generation) utilizzando la libreria datapizza-ai.

## Indice

1. [Prerequisiti](#1-prerequisiti)
2. [Architettura del sistema](#2-architettura-del-sistema)
3. [Setup dell'ambiente](#3-setup-dellambiente)
4. [Spiegazione del codice](#4-spiegazione-del-codice)
5. [Esecuzione](#5-esecuzione)

---

## 1. Prerequisiti

### Software richiesto

- Python 3.12+
- uv (package manager)
- Docker (opzionale, per Qdrant persistente)

### Chiavi API

Crea un file `.env` nella root del progetto:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

---

## 2. Architettura del sistema

Una pipeline RAG è composta da due fasi principali:

### Fase 1: ingestion

```
PDF → Parser → Splitter → Embedder → Vector Store
```

- **Parser**: estrae testo strutturato dal documento
- **Splitter**: divide il testo in chunk gestibili
- **Embedder**: converte ogni chunk in un vettore numerico
- **Vector store**: memorizza i vettori per ricerche veloci

### Fase 2: retrieval e generazione

```
Query → Rewriter → Embedder → Retriever → Prompt → LLM → Risposta
```

- **Rewriter**: migliora la query per il retrieval
- **Embedder**: converte la query in vettore
- **Retriever**: trova i chunk più simili
- **Prompt**: costruisce il contesto per l'LLM
- **LLM**: genera la risposta finale

---

## 3. Setup dell'ambiente

### 3.1 Attivazione virtual environment

```bash
cd /home/mcalcaterra/Documenti/GitHub/Datapizza/Ducati
source .venv/bin/activate
```

### 3.2 Installazione dipendenze

```bash
uv sync
```

Le dipendenze nel `pyproject.toml` sono:

```toml
dependencies = [
    "datapizza-ai",              # Core della libreria
    "datapizza-ai-parsers-docling", # Parser per PDF
    "qdrant-client",             # Client per vector store
    "python-dotenv",             # Gestione variabili d'ambiente
    "notebook",                  # Jupyter notebooks
]
```

### 3.3 Qdrant vector store

#### Opzione A: in-memory (per sviluppo)

Non richiede setup. Il codice usa `location=":memory:"` che crea un database temporaneo in RAM.

#### Opzione B: Docker (per produzione)

```bash
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```

Per usare Docker, modifica il codice:

```python
vectorstore = QdrantVectorstore(host="localhost", port=6333)
```

---

## 4. Spiegazione del codice

Il file `rag_pipeline.py` è organizzato in funzioni modulari. Analizziamo ogni sezione.

### 4.1 Import delle dipendenze

```python
import os
from dotenv import load_dotenv
```

- `os`: accesso al filesystem e variabili d'ambiente
- `load_dotenv`: carica le variabili dal file `.env`

```python
from datapizza.clients.openai import OpenAIClient
```

Client per interagire con i modelli OpenAI (GPT-4o-mini, GPT-4, ecc.).

```python
from datapizza.core.vectorstore import VectorConfig
```

Configurazione per definire le proprietà dei vettori nel vector store.

```python
from datapizza.embedders import ChunkEmbedder
from datapizza.embedders.openai import OpenAIEmbedder
```

- `ChunkEmbedder`: wrapper che applica l'embedding a ogni chunk
- `OpenAIEmbedder`: genera embeddings usando `text-embedding-3-small`

```python
from datapizza.modules.parsers.docling import DoclingParser
```

Parser che estrae testo e struttura da PDF usando Docling.

```python
from datapizza.modules.splitters import NodeSplitter
```

Divide i nodi del documento in chunk di dimensione configurabile.

```python
from datapizza.modules.prompt import ChatPromptTemplate
```

Template per costruire prompt strutturati con contesto e query.

```python
from datapizza.modules.rewriters import ToolRewriter
```

Riscrive le query utente per migliorare la qualità del retrieval.

```python
from datapizza.pipeline import IngestionPipeline, DagPipeline
```

- `IngestionPipeline`: pipeline sequenziale per l'ingestion
- `DagPipeline`: pipeline a grafo per retrieval complessi

```python
from datapizza.vectorstores.qdrant import QdrantVectorstore
```

Integrazione con Qdrant per lo storage e la ricerca vettoriale.

### 4.2 Setup ambiente

```python
def setup_environment():
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY non trovata. "
            "Crea un file .env con: OPENAI_API_KEY=sk-..."
        )
    return api_key
```

- `load_dotenv()`: legge il file `.env` e carica le variabili nell'ambiente
- `os.getenv("OPENAI_API_KEY")`: recupera la chiave API
- Se manca, solleva un'eccezione con istruzioni chiare

### 4.3 Creazione vector store

```python
def create_vectorstore(collection_name: str = "ducati_docs"):
    vectorstore = QdrantVectorstore(location=":memory:")
```

Crea un'istanza di Qdrant in memoria. Per persistenza usa `host` e `port`.

```python
    vectorstore.create_collection(
        collection_name,
        vector_config=[
            VectorConfig(
                name="text-embedding-3-small",
                dimensions=1536
            )
        ]
    )
```

- `collection_name`: nome logico per raggruppare i documenti
- `VectorConfig`: specifica il modello di embedding e le dimensioni
- `text-embedding-3-small` produce vettori a 1536 dimensioni

### 4.4 Pipeline di ingestion

```python
def create_ingestion_pipeline(api_key, vectorstore, collection_name):
    embedder_client = OpenAIEmbedder(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )
```

Crea l'embedder che verrà usato per convertire i chunk in vettori.

```python
    pipeline = IngestionPipeline(
        modules=[
            DoclingParser(),
            NodeSplitter(max_char=1000),
            ChunkEmbedder(client=embedder_client),
        ],
        vector_store=vectorstore,
        collection_name=collection_name
    )
```

La pipeline esegue i moduli in sequenza:

1. **DoclingParser()**: converte il PDF in nodi strutturati con testo, tabelle e immagini
2. **NodeSplitter(max_char=1000)**: divide ogni nodo in chunk di massimo 1000 caratteri
3. **ChunkEmbedder(client=embedder_client)**: genera un vettore per ogni chunk

I chunk vengono automaticamente salvati nel `vector_store` nella `collection_name` specificata.

### 4.5 Pipeline di retrieval (DagPipeline)

```python
def create_retrieval_pipeline(api_key, vectorstore, collection_name):
    openai_client = OpenAIClient(
        model="gpt-4o-mini",
        api_key=api_key
    )
```

Client per la generazione delle risposte. `gpt-4o-mini` offre buone performance a costo ridotto.

```python
    query_rewriter = ToolRewriter(
        client=openai_client,
        system_prompt=(
            "Sei un assistente che riscrive le domande degli utenti "
            "per migliorare la ricerca nei documenti tecnici Ducati. "
            "Mantieni il significato ma rendi la query più specifica."
        )
    )
```

Il rewriter usa un LLM per riformulare la query. Ad esempio:
- Input: "quanto va forte?"
- Output: "qual è la velocità massima del veicolo?"

```python
    embedder = OpenAIEmbedder(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )
```

Stesso modello usato in ingestion per coerenza dei vettori.

```python
    prompt_template = ChatPromptTemplate(
        system_prompt=(
            "Sei un esperto assistente tecnico Ducati. "
            "Rispondi alle domande basandoti SOLO sul contesto fornito. "
            "Se non trovi l'informazione nel contesto, dillo chiaramente."
        ),
        user_prompt_template="Domanda: {{user_prompt}}",
        retrieval_prompt_template=(
            "Contesto dai documenti Ducati:\n"
            "{% for chunk in chunks %}"
            "---\n{{ chunk.text }}\n"
            "{% endfor %}"
        )
    )
```

- `system_prompt`: istruzioni generali per l'LLM
- `user_prompt_template`: template per la domanda (usa Jinja2)
- `retrieval_prompt_template`: template per i chunk recuperati

```python
    dag_pipeline = DagPipeline()
    
    dag_pipeline.add_module("rewriter", query_rewriter)
    dag_pipeline.add_module("embedder", embedder)
    dag_pipeline.add_module("retriever", vectorstore)
    dag_pipeline.add_module("prompt", prompt_template)
    dag_pipeline.add_module("generator", openai_client)
```

Aggiunge i moduli con un nome identificativo.

```python
    dag_pipeline.connect("rewriter", "embedder", target_key="text")
    dag_pipeline.connect("embedder", "retriever", target_key="query_vector")
    dag_pipeline.connect("retriever", "prompt", target_key="chunks")
    dag_pipeline.connect("prompt", "generator", target_key="memory")
```

Definisce il flusso dei dati tra moduli:

1. `rewriter` → `embedder`: la query riscritta va all'embedder come `text`
2. `embedder` → `retriever`: il vettore va al retriever come `query_vector`
3. `retriever` → `prompt`: i chunk trovati vanno al prompt come `chunks`
4. `prompt` → `generator`: il prompt assemblato va al generatore come `memory`

### 4.6 Esecuzione query

```python
def run_query(pipeline, query, collection_name, k=3):
    result = pipeline.run({
        "rewriter": {"user_prompt": query},
        "prompt": {"user_prompt": query},
        "retriever": {"collection_name": collection_name, "k": k},
        "generator": {"input": query}
    })
    
    return result["generator"]
```

- Ogni modulo riceve i suoi parametri iniziali
- `k=3`: numero di chunk da recuperare
- Il risultato è nel dizionario sotto la chiave del modulo finale

---

## 5. Esecuzione

### 5.1 Attivare l'ambiente e lanciare lo script

```bash
cd /home/mcalcaterra/Documenti/GitHub/Datapizza/Ducati
source .venv/bin/activate
python rag_pipeline.py
```

### 5.2 Output atteso

```
============================================================
🏍️  Pipeline RAG Ducati con datapizza-ai
============================================================

[1/4] Configurazione ambiente...
✅ API key caricata

[2/4] Inizializzazione vector store Qdrant...
✅ Vector store pronto (in-memory)

[3/4] Ingestion del documento...
📄 Elaborazione documento: data/MonsterRev02.pdf
✅ Documento indicizzato con successo!

[4/4] Configurazione pipeline di retrieval...
✅ Pipeline RAG pronta!

============================================================
📝 Demo: Query sulla documentazione Ducati
============================================================

🔍 Query: Quali sono le caratteristiche principali del motore?

💬 Risposta:
[Risposta generata dall'LLM basata sul contenuto del PDF]
```

### 5.3 Modalità interattiva

Dopo le query demo, lo script entra in modalità interattiva dove puoi fare domande libere. Digita `exit` per uscire.

---

## Riferimenti

- [Documentazione ufficiale datapizza-ai](https://docs.datapizza.ai/0.0.9/Guides/RAG/rag/)
- [Qdrant documentation](https://qdrant.tech/documentation/)

