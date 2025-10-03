"""
Esempio pratico di implementazione RAG con datapizza

Questo script mostra come implementare un sistema RAG completo
utilizzando tutti i componenti della libreria datapizza.
"""

import asyncio
import logging
from pathlib import Path

from datapizza.clients import OpenAIClient
from datapizza.embedders import ClientEmbedder, NodeEmbedder
from datapizza.modules.captioners import LLMCaptioner
from datapizza.modules.metatagger import KeywordMetatagger
from datapizza.modules.parsers import AzureParser
from datapizza.modules.prompt import ChatPromptTemplate
from datapizza.modules.rerankers import CohereReranker
from datapizza.modules.splitters import TextSplitter
from datapizza.modules.treebuilder import LLMTreeBuilder
from datapizza.vectorstores import QdrantVectorstore

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGSystem:
    """Sistema RAG completo con datapizza"""
    
    def __init__(self, config: dict):
        """
        Inizializza il sistema RAG
        
        Args:
            config: Dizionario con le configurazioni necessarie
                    {
                        "openai_key": "sk-...",
                        "azure_key": "...",
                        "azure_endpoint": "https://...",
                        "cohere_key": "...",
                        "qdrant_host": "localhost",
                        "qdrant_port": 6333
                    }
        """
        self.config = config
        self.client = OpenAIClient(api_key=config["openai_key"])
        
        # Inizializzazione componenti
        self._setup_components()
    
    def _setup_components(self):
        """Inizializza tutti i componenti del sistema RAG"""
        
        # 1. Parser
        self.parser = AzureParser(
            api_key=self.config["azure_key"],
            endpoint=self.config["azure_endpoint"],
            result_type="markdown"
        )
        
        # 2. Tree Builder (facoltativo)
        self.tree_builder = LLMTreeBuilder(
            client=self.client,
            system_prompt="Riorganizza la struttura del documento mantenendo la gerarchia logica."
        )
        
        # 3. Captioner
        self.captioner = LLMCaptioner(
            client=self.client,
            max_workers=3,
            system_prompt_figure="Descrivi questa immagine in modo dettagliato, includendo elementi chiave visibili.",
            system_prompt_table="Riassumi il contenuto di questa tabella evidenziando dati importanti e tendenze."
        )
        
        # 4. Splitter
        self.splitter = TextSplitter(
            max_char=1000,
            overlap=100
        )
        
        # 5. Metatagger
        self.metatagger = KeywordMetatagger(
            num_keywords=5
        )
        
        # 6. Embedders
        self.document_embedder = NodeEmbedder(
            client=self.client,
            model_name="text-embedding-3-small",
            embedding_name="openai-embedding",
            batch_size=50
        )
        
        self.query_embedder = ClientEmbedder(
            client=self.client,
            model_name="text-embedding-3-small"
        )
        
        # 7. Vector Store
        self.vectorstore = QdrantVectorstore(
            host=self.config.get("qdrant_host", "localhost"),
            port=self.config.get("qdrant_port", 6333)
        )
        
        # 8. Reranker
        if "cohere_key" in self.config:
            self.reranker = CohereReranker(
                api_key=self.config["cohere_key"],
                endpoint="https://api.cohere.com/v1",
                top_n=5,
                threshold=0.5
            )
        else:
            self.reranker = None
        
        # 9. Prompt Template
        self.prompt_template = ChatPromptTemplate(
            template="""Sei un assistente AI che risponde a domande basandosi sui documenti forniti.

Documenti di riferimento:
{context}

Domanda dell'utente: {question}

Istruzioni:
- Usa solo le informazioni presenti nei documenti
- Se non trovi informazioni sufficienti, dillo chiaramente
- Cita i documenti quando possibile
- Rispondi in modo chiaro e completo

Risposta:"""
        )
    
    async def process_document(self, file_path: str, collection_name: str) -> bool:
        """
        Processa un documento e lo aggiunge al vector store
        
        Args:
            file_path: Percorso del documento da processare
            collection_name: Nome della collezione nel vector store
            
        Returns:
            True se il processo è completato con successo
        """
        try:
            logger.info(f"Processamento documento: {file_path}")
            
            # 1. Parsing
            logger.info("Parsing del documento...")
            document_node = self.parser.invoke(file_path)
            
            # 2. Tree Building (facoltativo)
            logger.info("Ristrutturazione del documento...")
            structured_node = self.tree_builder.invoke(document_node)
            
            # 3. Captioning
            logger.info("Generazione caption per immagini e tabelle...")
            captioned_node = await self.captioner.a_invoke(structured_node)
            
            # 4. Estrazione testo per splitting
            text_content = self._extract_text_from_node(captioned_node)
            
            # 5. Splitting
            logger.info("Splitting del testo in chunk...")
            chunks = self.splitter.invoke(text_content)
            logger.info(f"Creati {len(chunks)} chunk")
            
            # 6. Metatagger
            logger.info("Aggiunta metadati ai chunk...")
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "source_file": Path(file_path).name,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
                # Aggiungi keywords (simulazione - il KeywordMetatagger va personalizzato)
                chunk.metadata["keywords"] = self._extract_keywords(chunk.text)
            
            # 7. Embedding
            logger.info("Generazione embedding...")
            embedded_chunks = await self.document_embedder.a_invoke(chunks)
            
            # 8. Salvataggio nel vector store
            logger.info("Salvataggio nel vector store...")
            await self.vectorstore.a_add(embedded_chunks, collection_name=collection_name)
            
            logger.info(f"Documento processato con successo: {len(embedded_chunks)} chunk salvati")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante il processamento del documento: {e}")
            return False
    
    def _extract_text_from_node(self, node) -> str:
        """Estrae tutto il testo da un nodo e dai suoi figli"""
        text_parts = []
        
        if hasattr(node, 'content') and node.content:
            text_parts.append(node.content)
        
        if hasattr(node, 'children'):
            for child in node.children:
                child_text = self._extract_text_from_node(child)
                if child_text:
                    text_parts.append(child_text)
        
        return "\n".join(text_parts)
    
    def _extract_keywords(self, text: str) -> list[str]:
        """Estrae parole chiave dal testo (implementazione semplificata)"""
        # Implementazione base - in produzione usare KeywordMetatagger personalizzato
        words = text.lower().split()
        # Filtra parole comuni e restituisce le più significative
        stop_words = {"il", "la", "di", "che", "e", "a", "un", "per", "in", "con"}
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return list(set(keywords))[:5]
    
    async def query(self, question: str, collection_name: str, top_k: int = 10) -> dict:
        """
        Esegue una query RAG
        
        Args:
            question: Domanda dell'utente
            collection_name: Nome della collezione da interrogare
            top_k: Numero di documenti da recuperare
            
        Returns:
            Dizionario con risposta e metadati
        """
        try:
            logger.info(f"Elaborazione query: {question}")
            
            # 1. Embedding della query
            logger.info("Generazione embedding della query...")
            query_embedding = await self.query_embedder.a_invoke(question)
            
            # 2. Retrieval
            logger.info("Ricerca documenti rilevanti...")
            retrieved_chunks = await self.vectorstore.a_search(
                query_vector=query_embedding,
                collection_name=collection_name,
                top_k=top_k * 2 if self.reranker else top_k  # Recupera più documenti se c'è reranking
            )
            
            # 3. Reranking (se disponibile)
            if self.reranker and len(retrieved_chunks) > 0:
                logger.info("Reranking dei risultati...")
                final_chunks = await self.reranker.a_invoke({
                    "query": question,
                    "documents": retrieved_chunks
                })
            else:
                final_chunks = retrieved_chunks[:top_k]
            
            logger.info(f"Trovati {len(final_chunks)} documenti rilevanti")
            
            # 4. Preparazione contesto
            context = "\n\n".join([
                f"Documento {i+1}: {chunk.text}"
                for i, chunk in enumerate(final_chunks)
            ])
            
            # 5. Generazione risposta
            logger.info("Generazione risposta...")
            formatted_prompt = self.prompt_template.format(
                context=context,
                question=question
            )
            
            response = await self.client.a_invoke([{
                "role": "user",
                "content": formatted_prompt
            }])
            
            return {
                "answer": response.content,
                "sources": [
                    {
                        "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                        "metadata": chunk.metadata,
                        "score": getattr(chunk, 'score', 0.0)
                    }
                    for chunk in final_chunks
                ],
                "total_documents_found": len(retrieved_chunks)
            }
            
        except Exception as e:
            logger.error(f"Errore durante la query: {e}")
            return {
                "answer": "Mi dispiace, si è verificato un errore durante l'elaborazione della query.",
                "sources": [],
                "error": str(e)
            }


async def main():
    """Esempio di utilizzo del sistema RAG"""
    
    # Configurazione (sostituire con i propri valori)
    config = {
        "openai_key": "your-openai-api-key",
        "azure_key": "your-azure-key",
        "azure_endpoint": "https://your-azure-endpoint.cognitiveservices.azure.com/",
        "cohere_key": "your-cohere-key",  # facoltativo
        "qdrant_host": "localhost",
        "qdrant_port": 6333
    }
    
    # Inizializzazione sistema RAG
    rag_system = RAGSystem(config)
    
    # Nome della collezione
    collection_name = "my_documents"
    
    # Esempio 1: Processamento di un documento
    document_path = "path/to/your/document.pdf"
    
    if Path(document_path).exists():
        print("📄 Processamento documento...")
        success = await rag_system.process_document(document_path, collection_name)
        
        if success:
            print("✅ Documento processato con successo!")
            
            # Esempio 2: Query RAG
            questions = [
                "Qual è il contenuto principale del documento?",
                "Ci sono tabelle o grafici nel documento?",
                "Riassumi i punti chiave del documento."
            ]
            
            for question in questions:
                print(f"\n🔍 Query: {question}")
                result = await rag_system.query(question, collection_name)
                
                print(f"🤖 Risposta: {result['answer']}")
                print(f"📊 Documenti trovati: {result['total_documents_found']}")
                print(f"📎 Fonti utilizzate: {len(result['sources'])}")
                
                if result['sources']:
                    print("📋 Prima fonte:")
                    print(f"   {result['sources'][0]['text']}")
        else:
            print("❌ Errore durante il processamento del documento")
    else:
        print(f"❌ File non trovato: {document_path}")
        print("💡 Aggiorna il percorso del documento nell'esempio")


if __name__ == "__main__":
    asyncio.run(main())
