# RAG con datapizzai - Quick start

Implementazione rapida di un sistema RAG utilizzando la libreria datapizzai.

## File disponibili

- `AZURE_SERVICES_GUIDE.md` - **LEGGI PRIMA**: Differenze tra servizi Azure
- `test_azure_openai.py` - **TEST FIRST**: Verifica configurazione Azure OpenAI
- `simple_rag_example.py` - **START HERE**: Esempio funzionante solo con Azure OpenAI
- `README_RAG_COMPLETE_GUIDE.md` - Guida completa con tutti i dettagli
- `rag_example.py` - Esempio completo con Azure Document Intelligence
- `component_examples.py` - Esempi specifici per ogni componente
- `azure_openai_config.example.env` - Configurazione solo Azure OpenAI
- `config.example.json` - File di configurazione completo

## ⚠️ Problema comune: servizi Azure

Se ottieni errore `ResourceNotFoundError (404)` con `AzureParser`, è perché stai confondendo:
- **Azure OpenAI** (GPT, embedding) ← quello che probabilmente hai
- **Azure Document Intelligence** (parsing PDF) ← servizio separato richiesto da AzureParser

**Soluzione rapida**: usa `simple_rag_example.py` che funziona solo con Azure OpenAI.

## Setup rapido

### 1. Prerequisiti

```bash
pip install datapizzai
# Installare anche le dipendenze per i servizi utilizzati (OpenAI, Azure, Cohere, Qdrant)
```

### 2. Configurazione

Copiare `config.example.json` in `config.json` e inserire le proprie API key.

### 3. Avvio Qdrant (locale)

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. Test configurazione

```bash
# Prima testa che tutto funzioni
python test_azure_openai.py

# Se tutti i test passano, prova l'esempio
python simple_rag_example.py
```

## Flusso base

1. **Parse** documenti → struttura gerarchica
2. **Caption** immagini/tabelle → descrizioni testuali  
3. **Split** testo → chunk gestibili
4. **Embed** chunk → vettori numerici
5. **Store** nel vector database
6. **Query** → retrieval + generazione risposta

## Componenti principali

| Componente | Descrizione | Obbligatorio |
|------------|-------------|-------------|
| Parser | Estrazione strutturata da PDF/documenti | ✅ |
| Captioner | Descrizione di immagini e tabelle | ✅ |
| Splitter | Divisione in chunk | ✅ |
| Embedder | Conversione in vettori | ✅ |
| VectorStore | Database vettoriale | ✅ |
| TreeBuilder | Ristrutturazione gerarchica | ⚠️ Facoltativo |
| Metatagger | Aggiunta metadati e tag | ⚠️ Facoltativo |
| Reranker | Riordino risultati per rilevanza | ⚠️ Facoltativo |
| PromptTemplate | Template per generazione | ⚠️ Facoltativo |

## Esempio minimo (solo Azure OpenAI)

```python
# Installa: pip install PyPDF2 python-dotenv
import os
from dotenv import load_dotenv
load_dotenv()

from datapizzai.clients import OpenAIClient
from datapizzai.modules.splitters import TextSplitter
from datapizzai.embedders import NodeEmbedder
from datapizzai.vectorstores import QdrantVectorstore

# Parser semplice per PDF (sostituisce AzureParser)
import PyPDF2
from datapizzai.type.type import Node, NodeType

def simple_pdf_parser(file_path):
    with open(file_path, 'rb') as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
    
    return Node(
        children=[],
        content=text,
        node_type=NodeType.DOCUMENT,
        metadata={"source": file_path}
    )

# Setup
splitter = TextSplitter(max_char=1000, overlap=100)
embedder = NodeEmbedder(client=client, model_name="text-embedding-3-small")
vectorstore = QdrantVectorstore(host="localhost")

# Processo
document = simple_pdf_parser("RAG/document.pdf")  # Usa parser semplice
chunks = splitter.invoke(document.content)
embedded_chunks = embedder.invoke(chunks)

# Storage
for chunk in embedded_chunks:
    vectorstore.add(chunk, collection_name="docs")
```

Per esempi dettagliati e configurazioni avanzate, consultare la guida completa.
