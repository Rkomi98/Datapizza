"""
Esempio RAG semplificato senza Azure Document Intelligence

Questo esempio utilizza solo Azure OpenAI (che hai già) e parsing
semplice di file PDF/TXT per iniziare subito.
"""

import os
from pathlib import Path
import asyncio
from typing import List

# Per parsing PDF semplice
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    print("⚠️  PyPDF2 non installato. Usa: pip install PyPDF2")

from datapizzai.clients import OpenAIClient
from datapizzai.embedders import ClientEmbedder, NodeEmbedder
from datapizzai.modules.splitters import TextSplitter
from datapizzai.vectorstores import QdrantVectorstore
from datapizzai.type.type import Chunk, Node, NodeType
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()


class SimpleParser:
    """Parser semplificato per file PDF e TXT senza Azure Document Intelligence"""
    
    def __init__(self):
        pass
    
    def parse_text_file(self, file_path: str) -> str:
        """Legge un file di testo semplice"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse_pdf_file(self, file_path: str) -> str:
        """Estrae testo da PDF usando PyPDF2"""
        if not HAS_PYPDF2:
            raise ImportError("PyPDF2 necessario per PDF. Installa con: pip install PyPDF2")
        
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def invoke(self, file_path: str) -> Node:
        """
        Parsing semplificato che restituisce un Node compatibile
        
        Args:
            file_path: Percorso del file da parsare
            
        Returns:
            Node con il contenuto del file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")
        
        # Determina il tipo di file e parsa
        if file_path.suffix.lower() == '.pdf':
            content = self.parse_pdf_file(str(file_path))
        elif file_path.suffix.lower() in ['.txt', '.md']:
            content = self.parse_text_file(str(file_path))
        else:
            # Prova come file di testo
            try:
                content = self.parse_text_file(str(file_path))
            except Exception as e:
                raise ValueError(f"Tipo file non supportato: {file_path.suffix}. Errore: {e}")
        
        # Crea un Node semplice
        return Node(
            children=[],
            content=content,
            node_type=NodeType.DOCUMENT,
            metadata={
                "source_file": file_path.name,
                "file_type": file_path.suffix,
                "content_length": len(content)
            }
        )


class SimpleRAGSystem:
    """Sistema RAG semplificato che usa solo Azure OpenAI"""
    
    def __init__(self):
        """Inizializza il sistema usando solo le tue credenziali Azure OpenAI"""
        
        # Client Azure OpenAI (quello che hai già)
        self.client = OpenAIClient(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            base_url=os.getenv('AZURE_OPENAI_ENDPOINT'),
            model_name="gpt-4o"  # o il modello che hai deployato
        )
        
        # Parser semplice (invece di AzureParser)
        self.parser = SimpleParser()
        
        # Splitter
        self.splitter = TextSplitter(
            max_char=1000,
            overlap=100
        )
        
        # Embedder per documenti
        self.document_embedder = NodeEmbedder(
            client=self.client,
            model_name="text-embedding-3-small",  # verifica che sia deployato
            embedding_name="azure-embedding",
            batch_size=10
        )
        
        # Embedder per query
        self.query_embedder = ClientEmbedder(
            client=self.client,
            model_name="text-embedding-3-small"
        )
        
        # Vector store (Qdrant locale)
        self.vectorstore = QdrantVectorstore(
            host="localhost",
            port=6333
        )
        
        print("✅ Sistema RAG semplificato inizializzato")
        print(f"   Client: {type(self.client).__name__}")
        print(f"   Parser: {type(self.parser).__name__}")
    
    async def add_document(self, file_path: str, collection_name: str = "documents"):
        """
        Aggiunge un documento al sistema RAG
        
        Args:
            file_path: Percorso del file da aggiungere
            collection_name: Nome della collezione
        """
        try:
            print(f"📄 Processamento: {file_path}")
            
            # 1. Parsing (semplificato)
            document_node = self.parser.invoke(file_path)
            print(f"   ✅ Documento parsato: {len(document_node.content)} caratteri")
            
            # 2. Splitting
            chunks = self.splitter.invoke(document_node.content)
            print(f"   ✅ Creati {len(chunks)} chunk")
            
            # 3. Aggiungi metadati ai chunk
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "source_file": Path(file_path).name,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
            
            # 4. Embedding
            print("   🔢 Generazione embedding...")
            embedded_chunks = await self.document_embedder.a_invoke(chunks)
            print(f"   ✅ Embedding generati per {len(embedded_chunks)} chunk")
            
            # 5. Salvataggio nel vector store
            print("   💾 Salvataggio nel vector store...")
            await self.vectorstore.a_add(embedded_chunks, collection_name=collection_name)
            print(f"   ✅ Salvati {len(embedded_chunks)} chunk nella collezione '{collection_name}'")
            
            return len(embedded_chunks)
            
        except Exception as e:
            print(f"   ❌ Errore durante il processamento: {e}")
            return 0
    
    async def query(self, question: str, collection_name: str = "documents", top_k: int = 5):
        """
        Esegue una query RAG
        
        Args:
            question: Domanda dell'utente
            collection_name: Collezione da interrogare
            top_k: Numero di documenti da recuperare
            
        Returns:
            Risposta del sistema
        """
        try:
            print(f"🔍 Query: {question}")
            
            # 1. Embedding della query
            query_embedding = await self.query_embedder.a_invoke(question)
            print("   ✅ Embedding query generato")
            
            # 2. Ricerca nel vector store
            results = await self.vectorstore.a_search(
                query_vector=query_embedding,
                collection_name=collection_name,
                top_k=top_k
            )
            print(f"   ✅ Trovati {len(results)} documenti rilevanti")
            
            # 3. Preparazione contesto
            context = "\n\n".join([
                f"Documento {i+1}: {chunk.text}"
                for i, chunk in enumerate(results)
            ])
            
            # 4. Generazione risposta
            prompt = f"""Basandoti sui seguenti documenti, rispondi alla domanda dell'utente.

Documenti:
{context}

Domanda: {question}

Rispondi in modo preciso utilizzando solo le informazioni fornite nei documenti:"""

            response = await self.client.a_invoke([{
                "role": "user", 
                "content": prompt
            }])
            
            print("   ✅ Risposta generata")
            
            return {
                "answer": response.content,
                "sources": [
                    {
                        "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                        "metadata": chunk.metadata
                    }
                    for chunk in results
                ]
            }
            
        except Exception as e:
            print(f"   ❌ Errore durante la query: {e}")
            return {
                "answer": f"Errore durante l'elaborazione: {e}",
                "sources": []
            }


async def main():
    """Esempio di utilizzo del sistema RAG semplificato"""
    
    print("🚀 Sistema RAG Semplificato con Azure OpenAI")
    print("=" * 50)
    
    # Verifica configurazione
    if not os.getenv('AZURE_OPENAI_API_KEY'):
        print("❌ AZURE_OPENAI_API_KEY non configurata")
        return
    
    if not os.getenv('AZURE_OPENAI_ENDPOINT'):
        print("❌ AZURE_OPENAI_ENDPOINT non configurata")
        return
    
    # Inizializza sistema
    rag = SimpleRAGSystem()
    
    # Collezione di test
    collection_name = "test_docs"
    
    # Test con file di esempio (crea o usa file esistenti)
    test_files = [
        "RAG/document.pdf",  # il tuo PDF
        "README.md",         # file di testo esistente
    ]
    
    print(f"\n📚 Aggiunta documenti alla collezione '{collection_name}':")
    print("-" * 30)
    
    total_chunks = 0
    for file_path in test_files:
        if Path(file_path).exists():
            chunks_added = await rag.add_document(file_path, collection_name)
            total_chunks += chunks_added
        else:
            print(f"⚠️  File non trovato: {file_path}")
    
    if total_chunks == 0:
        print("❌ Nessun documento aggiunto. Controlla i percorsi dei file.")
        return
    
    print(f"\n✅ Totale chunk aggiunti: {total_chunks}")
    
    # Test query
    print(f"\n💬 Test query:")
    print("-" * 20)
    
    questions = [
        "Di cosa tratta il documento?",
        "Quali sono i punti principali?",
        "Riassumi il contenuto in breve"
    ]
    
    for question in questions:
        result = await rag.query(question, collection_name)
        
        print(f"\nDomanda: {question}")
        print(f"Risposta: {result['answer']}")
        print(f"Fonti: {len(result['sources'])} documenti")
        
        if result['sources']:
            print(f"Prima fonte: {result['sources'][0]['text']}")


if __name__ == "__main__":
    # Verifica dipendenze
    print("🔧 Verifica dipendenze...")
    
    missing = []
    
    if not HAS_PYPDF2:
        missing.append("PyPDF2")
    
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        missing.append("qdrant-client")
    
    if missing:
        print(f"❌ Dipendenze mancanti: {', '.join(missing)}")
        print("Installa con:")
        for dep in missing:
            print(f"   pip install {dep}")
        exit(1)
    
    # Verifica Qdrant
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        client.get_collections()
        print("✅ Qdrant connesso")
    except Exception:
        print("❌ Qdrant non raggiungibile")
        print("Avvia Qdrant con: docker run -p 6333:6333 qdrant/qdrant")
        exit(1)
    
    print("✅ Tutte le dipendenze OK")
    print()
    
    asyncio.run(main())
