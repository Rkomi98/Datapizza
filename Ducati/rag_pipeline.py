"""
Pipeline RAG con datapizza-ai
=============================
Due modalità:
- ingest: processa documenti e li salva localmente
- chat: chatbot da terminale che risponde solo dalla fonte
"""

import os
import sys
from dotenv import load_dotenv

from datapizza.clients.openai import OpenAIClient
from datapizza.core.vectorstore import VectorConfig
from datapizza.embedders import ChunkEmbedder
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.modules.parsers.docling import DoclingParser
from datapizza.modules.splitters import NodeSplitter
from datapizza.pipeline import IngestionPipeline
from datapizza.vectorstores.qdrant import QdrantVectorstore

# Configurazione
COLLECTION_NAME = "ducati_docs"
QDRANT_PATH = "./qdrant_data"  # Cartella locale per persistenza
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
LLM_MODEL = "gpt-5.1"


def setup_environment():
    """Carica le variabili d'ambiente e restituisce la API key."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Errore: OPENAI_API_KEY non trovata nel file .env")
        sys.exit(1)
    return api_key


def get_vectorstore(create_collection: bool = False) -> QdrantVectorstore:
    """
    Ottiene il vector store Qdrant con persistenza locale.
    
    Args:
        create_collection: se True, crea la collection (per ingestion)
    """
    # location=None bypassa il check, path viene passato a QdrantClient per persistenza locale
    vectorstore = QdrantVectorstore(location=None, path=QDRANT_PATH)
    
    if create_collection:
        vectorstore.create_collection(
            COLLECTION_NAME,
            vector_config=[
                VectorConfig(name=EMBEDDING_MODEL, dimensions=EMBEDDING_DIM)
            ]
        )
    
    return vectorstore


def run_ingestion(file_path: str):
    """
    Esegue l'ingestion di un documento PDF.
    I dati vengono salvati localmente in ./qdrant_data
    """
    if not os.path.exists(file_path):
        print(f"Errore: file non trovato: {file_path}")
        sys.exit(1)
    
    print("=" * 50)
    print("Ingestion documento")
    print("=" * 50)
    
    api_key = setup_environment()
    
    print(f"\nFile: {file_path}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Storage: {QDRANT_PATH}")
    
    # Crea vector store con nuova collection
    print("\nCreazione vector store...")
    vectorstore = get_vectorstore(create_collection=True)
    
    # Crea embedder
    embedder = OpenAIEmbedder(
        api_key=api_key,
        model_name=EMBEDDING_MODEL,
    )
    
    # Crea pipeline di ingestion
    pipeline = IngestionPipeline(
        modules=[
            DoclingParser(),
            NodeSplitter(max_char=1000),
            ChunkEmbedder(client=embedder),
        ],
        vector_store=vectorstore,
        collection_name=COLLECTION_NAME
    )
    
    # Esegui ingestion
    print("\nElaborazione in corso...")
    pipeline.run(file_path, metadata={"source": os.path.basename(file_path)})
    
    print("\nIngestion completata!")
    print(f"I dati sono salvati in: {os.path.abspath(QDRANT_PATH)}")


def run_chatbot():
    """
    Chatbot da terminale che risponde solo in base alla fonte indicizzata.
    """
    print("=" * 50)
    print("Chatbot Ducati")
    print("=" * 50)
    
    # Verifica che esista il database
    if not os.path.exists(QDRANT_PATH):
        print(f"\nErrore: database non trovato in {QDRANT_PATH}")
        print("Esegui prima l'ingestion con: python rag_pipeline.py ingest <file.pdf>")
        sys.exit(1)
    
    api_key = setup_environment()
    
    # Carica vector store esistente
    print("\nCaricamento database...")
    vectorstore = get_vectorstore(create_collection=False)
    
    # Crea embedder per le query
    embedder = OpenAIEmbedder(
        api_key=api_key,
        model_name=EMBEDDING_MODEL,
    )
    
    # Crea client LLM
    llm = OpenAIClient(
        model=LLM_MODEL,
        api_key=api_key
    )
    
    print("Database caricato!")
    print("\nScrivi le tue domande. Digita 'exit' per uscire.\n")
    print("-" * 50)
    
    while True:
        # Input utente
        try:
            query = input("\nTu: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nArrivederci!")
            break
        
        if not query:
            continue
        
        if query.lower() in ["exit", "quit", "q"]:
            print("Arrivederci!")
            break
        
        # Genera embedding della query
        query_embedding = embedder.embed(query)
        
        # Cerca chunk rilevanti
        results = vectorstore.search(
            query_vector=query_embedding,
            collection_name=COLLECTION_NAME,
            k=5
        )
        
        if not results:
            print("\nAssistente: Non ho trovato informazioni rilevanti nel documento.")
            continue
        
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
        print(f"\nAssistente: {response.text}")


def print_usage():
    """Stampa le istruzioni d'uso."""
    print("""
Uso: python rag_pipeline.py <comando> [argomenti]

Comandi:
  ingest <file.pdf>   Processa un documento e lo salva localmente
  chat                Avvia il chatbot da terminale

Esempi:
  python rag_pipeline.py ingest data/MonsterRev02.pdf
  python rag_pipeline.py chat
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "ingest":
        if len(sys.argv) < 3:
            print("Errore: specifica il file da processare")
            print("Uso: python rag_pipeline.py ingest <file.pdf>")
            sys.exit(1)
        run_ingestion(sys.argv[2])
    
    elif command == "chat":
        run_chatbot()
    
    else:
        print(f"Comando non riconosciuto: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
