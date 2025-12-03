import os
import sys
from dotenv import load_dotenv
from datapizza.modules.parsers.docling import DoclingParser
from datapizza.modules.splitters import RecursiveSplitter
from datapizza.embedders.openai import OpenAIEmbedder
from datapizza.vectorstores.qdrant import QdrantVectorstore as QdrantVectorStore
from datapizza.clients.openai import OpenAIClient

def main():
    # 1. Setup
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("ATTENZIONE: OPENAI_API_KEY non trovata nel file .env")
        # Potremmo voler uscire qui se la chiave è obbligatoria, 
        # ma per ora lasciamo che il codice fallisca dopo se necessario
    
    print("Inizio test RAG...")

    # 2. Ingestion
    file_path = "data/MonsterRev02.pdf"
    if not os.path.exists(file_path):
        print(f"Errore: File non trovato in {file_path}")
        return

    print(f"Leggendo il file: {file_path}")
    parser = DoclingParser()
    try:
        documents = parser.parse(file_path)
    except Exception as e:
        print(f"Errore durante il parsing: {e}")
        return

    print(f"Documenti caricati: {len(documents)}")
    if documents:
        print(f"Anteprima contenuto:\n{documents[0].content[:200]}...")

    # 3. Splitting
    print("\nEseguendo il chunking...")
    splitter = RecursiveSplitter(
        chunk_size=300,
        chunk_overlap=50
    )
    nodes = splitter.split(documents)
    print(f"Abbiamo ottenuto {len(nodes)} chunks.")
    if len(nodes) > 1:
        print("--- Esempio Chunk 1 ---")
        print(nodes[0].content)

    # 4. Embedding & Indexing
    print("\nIndicizzando su Qdrant (in-memory)...")
    embedder = OpenAIEmbedder(api_key=os.getenv("OPENAI_API_KEY"))
    vector_store = QdrantVectorStore(
        collection_name="ducati_demo",
        location=":memory:"
    )
    vector_store.add(nodes, embedder=embedder)
    print("Indicizzazione completata!")

    # 5. Retrieval
    query = "Quali sono le caratteristiche principali del motore del Ducati Monster?"
    print(f"\nEseguendo query: '{query}'")
    
    retrieved_nodes = vector_store.query(query, k=2, embedder=embedder)
    
    print(f"Trovati {len(retrieved_nodes)} nodi rilevanti.")
    for i, node in enumerate(retrieved_nodes):
        print(f"[Risultato {i+1}] (Score: {node.score:.4f}):")
        print(f"...{node.content}...")
        print("-" * 40)

    # 6. Generation
    print("\nGenerazione della risposta con LLM...")
    client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
    
    context_text = "\n\n".join([node.content for node in retrieved_nodes])
    augmented_prompt = f"""
Sei un assistente esperto Ducati. Usa LE SEGUENTI INFORMAZIONI per rispondere alla domanda dell'utente.
Se non trovi la risposta nel testo, dì che non lo sai.

CONTESTO:
{context_text}

DOMANDA UTENTE:
{query}
"""
    
    response = client.invoke(augmented_prompt)
    print("--- RISPOSTA ---")
    print(response.text)

if __name__ == "__main__":
    main()

