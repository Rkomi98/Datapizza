"""
Pipeline RAG completa con datapizza-ai
======================================
Questo script implementa una pipeline RAG (Retrieval-Augmented Generation)
utilizzando datapizza-ai per processare documenti PDF Ducati e rispondere
a domande basandosi sul loro contenuto.
"""

import os
from dotenv import load_dotenv

# Componenti datapizza-ai
from datapizza.clients.openai import OpenAIClient
from datapizza.core.vectorstore import VectorConfig
from datapizza.embedders import ChunkEmbedder
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.modules.parsers.docling import DoclingParser
from datapizza.modules.splitters import NodeSplitter
from datapizza.modules.prompt import ChatPromptTemplate
from datapizza.modules.rewriters import ToolRewriter
from datapizza.pipeline import IngestionPipeline, DagPipeline
from datapizza.vectorstores.qdrant import QdrantVectorstore


def setup_environment():
    """
    Carica le variabili d'ambiente dal file .env
    Verifica che OPENAI_API_KEY sia presente.
    """
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY non trovata. "
            "Crea un file .env con: OPENAI_API_KEY=sk-..."
        )
    return api_key


def create_vectorstore(collection_name: str = "ducati_docs"):
    """
    Crea e configura il vector store Qdrant.
    Usa :memory: per testing locale (i dati non persistono).
    Per produzione, usa host e port di un'istanza Qdrant.
    """
    vectorstore = QdrantVectorstore(location=":memory:")
    
    # Crea la collection con la configurazione del vettore
    # text-embedding-3-small produce vettori di 1536 dimensioni
    vectorstore.create_collection(
        collection_name,
        vector_config=[
            VectorConfig(
                name="text-embedding-3-small",
                dimensions=1536
            )
        ]
    )
    
    return vectorstore


def create_ingestion_pipeline(
    api_key: str,
    vectorstore: QdrantVectorstore,
    collection_name: str
) -> IngestionPipeline:
    """
    Crea la pipeline di ingestion per processare documenti.
    
    La pipeline esegue in sequenza:
    1. DoclingParser: estrae testo e struttura dal PDF
    2. NodeSplitter: divide il documento in chunk di max 1000 caratteri
    3. ChunkEmbedder: genera embeddings per ogni chunk
    """
    embedder_client = OpenAIEmbedder(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )
    
    pipeline = IngestionPipeline(
        modules=[
            DoclingParser(),                        # Parsing del PDF
            NodeSplitter(max_char=1000),           # Chunking del testo
            ChunkEmbedder(client=embedder_client), # Generazione embeddings
        ],
        vector_store=vectorstore,
        collection_name=collection_name
    )
    
    return pipeline


def create_retrieval_pipeline(
    api_key: str,
    vectorstore: QdrantVectorstore,
    collection_name: str
) -> DagPipeline:
    """
    Crea la pipeline DAG per il retrieval e la generazione.
    
    Il flusso è:
    query -> rewriter -> embedder -> retriever -> prompt -> generator
    
    Ogni modulo trasforma l'input e lo passa al successivo.
    """
    # Client OpenAI per generazione e rewriting
    openai_client = OpenAIClient(
        model="gpt-4o-mini",
        api_key=api_key
    )
    
    # Riscrive la query per migliorare il retrieval
    query_rewriter = ToolRewriter(
        client=openai_client,
        system_prompt=(
            "Sei un assistente che riscrive le domande degli utenti "
            "per migliorare la ricerca nei documenti tecnici Ducati. "
            "Mantieni il significato ma rendi la query più specifica."
        )
    )
    
    # Embedder per trasformare la query in vettore
    embedder = OpenAIEmbedder(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )
    
    # Template per costruire il prompt finale
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
    
    # Costruzione della pipeline DAG
    dag_pipeline = DagPipeline()
    
    # Aggiunta dei moduli
    dag_pipeline.add_module("rewriter", query_rewriter)
    dag_pipeline.add_module("embedder", embedder)
    dag_pipeline.add_module("retriever", vectorstore)
    dag_pipeline.add_module("prompt", prompt_template)
    dag_pipeline.add_module("generator", openai_client)
    
    # Connessione dei moduli (definisce il flusso dei dati)
    dag_pipeline.connect("rewriter", "embedder", target_key="text")
    dag_pipeline.connect("embedder", "retriever", target_key="query_vector")
    dag_pipeline.connect("retriever", "prompt", target_key="chunks")
    dag_pipeline.connect("prompt", "generator", target_key="memory")
    
    return dag_pipeline


def run_ingestion(pipeline: IngestionPipeline, file_path: str):
    """Esegue l'ingestion di un documento."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File non trovato: {file_path}")
    
    print(f"📄 Elaborazione documento: {file_path}")
    pipeline.run(
        file_path,
        metadata={"source": os.path.basename(file_path)}
    )
    print("✅ Documento indicizzato con successo!")


def run_query(
    pipeline: DagPipeline,
    query: str,
    collection_name: str,
    k: int = 3
) -> str:
    """
    Esegue una query sulla pipeline RAG.
    
    Args:
        pipeline: La DagPipeline configurata
        query: La domanda dell'utente
        collection_name: Nome della collection Qdrant
        k: Numero di chunk da recuperare
    
    Returns:
        La risposta generata dal modello
    """
    print(f"\n🔍 Query: {query}")
    
    result = pipeline.run({
        "rewriter": {"user_prompt": query},
        "prompt": {"user_prompt": query},
        "retriever": {"collection_name": collection_name, "k": k},
        "generator": {"input": query}
    })
    
    return result["generator"]


def main():
    """Funzione principale che orchestra la pipeline RAG."""
    
    # Configurazione
    COLLECTION_NAME = "ducati_docs"
    PDF_PATH = "data/MonsterRev02.pdf"
    
    print("=" * 60)
    print("🏍️  Pipeline RAG Ducati con datapizza-ai")
    print("=" * 60)
    
    # 1. Setup ambiente
    print("\n[1/4] Configurazione ambiente...")
    api_key = setup_environment()
    print("✅ API key caricata")
    
    # 2. Inizializzazione vector store
    print("\n[2/4] Inizializzazione vector store Qdrant...")
    vectorstore = create_vectorstore(COLLECTION_NAME)
    print("✅ Vector store pronto (in-memory)")
    
    # 3. Ingestion del documento
    print("\n[3/4] Ingestion del documento...")
    ingestion_pipeline = create_ingestion_pipeline(
        api_key, vectorstore, COLLECTION_NAME
    )
    run_ingestion(ingestion_pipeline, PDF_PATH)
    
    # 4. Setup retrieval pipeline
    print("\n[4/4] Configurazione pipeline di retrieval...")
    retrieval_pipeline = create_retrieval_pipeline(
        api_key, vectorstore, COLLECTION_NAME
    )
    print("✅ Pipeline RAG pronta!")
    
    # Demo: esecuzione di alcune query
    print("\n" + "=" * 60)
    print("📝 Demo: Query sulla documentazione Ducati")
    print("=" * 60)
    
    queries = [
        "Quali sono le caratteristiche principali del motore?",
        "Quali sono le specifiche tecniche del telaio?",
    ]
    
    for query in queries:
        response = run_query(
            retrieval_pipeline,
            query,
            COLLECTION_NAME,
            k=3
        )
        print(f"\n💬 Risposta:\n{response.text}")
        print("-" * 60)
    
    # Modalità interattiva
    print("\n" + "=" * 60)
    print("💡 Modalità interattiva (scrivi 'exit' per uscire)")
    print("=" * 60)
    
    while True:
        user_query = input("\n❓ La tua domanda: ").strip()
        if user_query.lower() in ["exit", "quit", "q"]:
            print("👋 Arrivederci!")
            break
        if not user_query:
            continue
            
        response = run_query(
            retrieval_pipeline,
            user_query,
            COLLECTION_NAME,
            k=3
        )
        print(f"\n💬 Risposta:\n{response.text}")


if __name__ == "__main__":
    main()

