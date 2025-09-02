#!/usr/bin/env python3
"""
Esempio di utilizzo di IngestionPipeline per processare documenti di testo
e ingerirli in un vector store Qdrant.

Requisiti:
- pip install python-dotenv pyyaml qdrant-client
- .env con API_KEY del provider di embeddings (es. OPENAI_API_KEY)
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from datapizzai.pipeline import IngestionPipeline
from datapizzai.modules.parsers import TextParser
from datapizzai.modules.splitters import RecursiveSplitter
from datapizzai.embedders import ClientEmbedder
from datapizzai.vectorstores import QdrantVectorstore
from datapizzai.clients import OpenAIClient

# Carica variabili d'ambiente
load_dotenv()

def create_sample_documents():
    """Crea alcuni documenti di esempio per il test."""
    docs_dir = Path("sample_docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Documento 1: Introduzione all'AI
    doc1 = docs_dir / "ai_intro.txt"
    doc1.write_text("""
L'Intelligenza Artificiale (AI) è una branca dell'informatica che si occupa della creazione 
di sistemi capaci di eseguire compiti che normalmente richiederebbero intelligenza umana.

L'AI include diverse sottocategorie:
- Machine Learning: algoritmi che apprendono dai dati
- Deep Learning: reti neurali artificiali profonde
- Natural Language Processing: elaborazione del linguaggio naturale
- Computer Vision: analisi e interpretazione di immagini

Le applicazioni dell'AI spaziano dalla medicina alla finanza, dall'automazione industriale 
ai veicoli autonomi.
    """)
    
    # Documento 2: Pipeline di Data Science
    doc2 = docs_dir / "data_pipeline.txt"
    doc2.write_text("""
Una pipeline di Data Science è un insieme di processi automatizzati che trasformano
i dati grezzi in insights utilizzabili.

Le fasi principali includono:
1. Data Collection: raccolta dati da diverse fonti
2. Data Cleaning: pulizia e preprocessing dei dati
3. Feature Engineering: creazione di caratteristiche rilevanti
4. Model Training: addestramento di modelli predittivi
5. Model Evaluation: valutazione delle performance
6. Model Deployment: messa in produzione del modello

L'automazione di queste fasi è fondamentale per scalare le operazioni di data science.
    """)
    
    return [str(doc1), str(doc2)]

def main():
    # Crea documenti di esempio
    document_paths = create_sample_documents()
    print(f"📄 Documenti creati: {document_paths}")
    
    # Configura client per embeddings
    openai_client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"
    )
    
    # Configura componenti della pipeline
    components = [
        TextParser(),  # Parsing del testo
        RecursiveSplitter(chunk_size=200, chunk_overlap=50),  # Divisione in chunks
        ClientEmbedder(client=openai_client, model="text-embedding-3-small")  # Embeddings
    ]
    
    # Configura vector store (opzionale - se None restituisce solo i chunks)
    vector_store = None
    collection_name = None
    
    # Se vuoi usare Qdrant (decommentare le righe seguenti):
    # vector_store = QdrantVectorstore(url="http://localhost:6333")
    # collection_name = "ai_knowledge_base"
    
    # Crea pipeline
    pipeline = IngestionPipeline(
        modules=components,
        vector_store=vector_store,
        collection_name=collection_name
    )
    
    # Esegui pipeline
    print("🔄 Eseguendo pipeline di ingestion...")
    
    if vector_store:
        # Con vector store - salva direttamente
        for doc_path in document_paths:
            pipeline.run(doc_path, metadata={"source": doc_path})
        print("✅ Documenti processati e salvati nel vector store")
    else:
        # Senza vector store - restituisce chunks
        all_chunks = []
        for doc_path in document_paths:
            chunks = pipeline.run(doc_path, metadata={"source": doc_path})
            all_chunks.extend(chunks)
        
        print(f"✅ Pipeline completata! Generati {len(all_chunks)} chunks:")
        for i, chunk in enumerate(all_chunks[:3]):  # Mostra primi 3 chunks
            print(f"\nChunk {i+1}:")
            print(f"Testo: {chunk.page_content[:100]}...")
            print(f"Metadata: {chunk.metadata}")

if __name__ == "__main__":
    main()
