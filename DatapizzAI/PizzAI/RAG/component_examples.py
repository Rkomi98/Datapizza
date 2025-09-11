"""
Esempi specifici per ogni componente RAG di datapizzai

Questo file contiene esempi focalizzati per ogni singolo componente,
utili per testing e comprensione delle funzionalità individuali.
"""

import asyncio
import json
from pathlib import Path

from datapizzai.clients import OpenAIClient
from datapizzai.embedders import ClientEmbedder, NodeEmbedder
from datapizzai.modules.captioners import LLMCaptioner  
from datapizzai.modules.metatagger import KeywordMetatagger
from datapizzai.modules.parsers import AzureParser
from datapizzai.modules.prompt import ChatPromptTemplate
from datapizzai.modules.rerankers import CohereReranker
from datapizzai.modules.splitters import TextSplitter, RecursiveSplitter
from datapizzai.modules.treebuilder import LLMTreeBuilder
from datapizzai.vectorstores import QdrantVectorstore
from datapizzai.type.type import Chunk


def load_config() -> dict:
    """Carica configurazione da file JSON"""
    config_path = Path("config.json")
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    else:
        print("⚠️  File config.json non trovato. Usando config.example.json")
        with open("config.example.json") as f:
            return json.load(f)


# Configurazione globale
CONFIG = load_config()
CLIENT = OpenAIClient(api_key=CONFIG["openai_key"])


# =============================================================================
# 1. PARSER EXAMPLES
# =============================================================================

def example_azure_parser():
    """Esempio di utilizzo AzureParser"""
    print("📄 Esempio AzureParser")
    
    parser = AzureParser(
        api_key=CONFIG["azure_key"],
        endpoint=CONFIG["azure_endpoint"],
        result_type="markdown"  # "text" o "markdown"
    )
    
    # Esempio con file locale
    file_path = "sample_document.pdf"
    if Path(file_path).exists():
        try:
            # Parsing del documento
            document_node = parser.invoke(file_path)
            
            print(f"✅ Documento parsato: {type(document_node)}")
            print(f"   Tipo nodo: {document_node.node_type}")
            print(f"   Numero figli: {len(document_node.children)}")
            print(f"   Metadata: {list(document_node.metadata.keys())}")
            
            # Mostra struttura gerarchica
            print("\n🌳 Struttura documento:")
            _print_node_structure(document_node, level=0)
            
        except Exception as e:
            print(f"❌ Errore parsing: {e}")
    else:
        print(f"❌ File non trovato: {file_path}")


def _print_node_structure(node, level=0, max_level=3):
    """Stampa struttura gerarchica del nodo"""
    indent = "  " * level
    content_preview = ""
    if hasattr(node, 'content') and node.content:
        content_preview = f" - {node.content[:50]}..." if len(node.content) > 50 else f" - {node.content}"
    
    print(f"{indent}{node.node_type}{content_preview}")
    
    if level < max_level and hasattr(node, 'children'):
        for child in node.children[:3]:  # Mostra solo primi 3 figli
            _print_node_structure(child, level + 1, max_level)
        
        if len(node.children) > 3:
            print(f"{indent}  ... e altri {len(node.children) - 3} nodi")


# =============================================================================
# 2. SPLITTER EXAMPLES  
# =============================================================================

def example_text_splitter():
    """Esempio di utilizzo TextSplitter"""
    print("\n✂️  Esempio TextSplitter")
    
    # Testo di esempio
    sample_text = """
    L'intelligenza artificiale (AI) è una tecnologia che sta trasformando il mondo.
    Essa include machine learning, deep learning, e natural language processing.
    Le applicazioni dell'AI spaziano dalla medicina all'automotive, dalla finanza all'intrattenimento.
    Il machine learning permette ai computer di apprendere dai dati senza essere esplicitamente programmati.
    Il deep learning utilizza reti neurali profonde per riconoscere pattern complessi.
    Il natural language processing consente alle macchine di comprendere e generare linguaggio umano.
    Queste tecnologie stanno creando nuove opportunità ma anche sfide etiche e sociali.
    """ * 3  # Ripeti per avere testo più lungo
    
    # TextSplitter base
    splitter = TextSplitter(
        max_char=200,
        overlap=50
    )
    
    chunks = splitter.invoke(sample_text)
    
    print(f"✅ Testo diviso in {len(chunks)} chunk")
    print(f"   Lunghezza originale: {len(sample_text)} caratteri")
    
    for i, chunk in enumerate(chunks[:3]):  # Mostra primi 3
        print(f"\n📝 Chunk {i+1}:")
        print(f"   ID: {chunk.id}")
        print(f"   Lunghezza: {len(chunk.text)} caratteri")
        print(f"   Testo: {chunk.text[:100]}...")
        print(f"   Metadata: {chunk.metadata}")


def example_recursive_splitter():
    """Esempio di utilizzo RecursiveSplitter"""
    print("\n✂️  Esempio RecursiveSplitter")
    
    # Testo strutturato
    sample_text = """
# Capitolo 1: Introduzione all'AI

L'intelligenza artificiale è un campo in rapida crescita.

## 1.1 Definizione

L'AI si riferisce alla capacità delle macchine di imitare l'intelligenza umana.

## 1.2 Storia

- 1950: Test di Turing
- 1956: Conferenza di Dartmouth  
- 1980s: Sistemi esperti
- 2010s: Deep learning revolution

# Capitolo 2: Applicazioni

Le applicazioni dell'AI sono numerose e in crescita.

## 2.1 Settore sanitario
- Diagnosi medica
- Scoperta farmaci
- Chirurgia robotica
"""
    
    recursive_splitter = RecursiveSplitter(
        max_char=300,
        overlap=50
    )
    
    chunks = recursive_splitter.invoke(sample_text)
    
    print(f"✅ Testo diviso in {len(chunks)} chunk con splitting ricorsivo")
    
    for i, chunk in enumerate(chunks):
        print(f"\n📝 Chunk {i+1}:")
        print(f"   Lunghezza: {len(chunk.text)} caratteri")
        print(f"   Inizio: {chunk.text[:80]}...")


# =============================================================================
# 3. EMBEDDER EXAMPLES
# =============================================================================

async def example_embedders():
    """Esempi di utilizzo degli embedder"""
    print("\n🔢 Esempio Embedders")
    
    # ClientEmbedder per singoli testi/query
    client_embedder = ClientEmbedder(
        client=CLIENT,
        model_name=CONFIG["embedding_model"],
        embedding_name="query_embedding"
    )
    
    # Test embedding singolo testo
    test_text = "Cos'è il machine learning?"
    embedding = await client_embedder.a_invoke(test_text)
    
    print(f"✅ ClientEmbedder:")
    print(f"   Testo: {test_text}")
    print(f"   Dimensioni embedding: {len(embedding)}")
    print(f"   Primi 5 valori: {embedding[:5]}")
    
    # NodeEmbedder per batch di chunk
    sample_chunks = [
        Chunk(id="1", text="Il machine learning è una sottocategoria dell'AI"),
        Chunk(id="2", text="Il deep learning utilizza reti neurali profonde"),
        Chunk(id="3", text="Il natural language processing elabora il linguaggio")
    ]
    
    node_embedder = NodeEmbedder(
        client=CLIENT,
        model_name=CONFIG["embedding_model"],
        embedding_name="document_embedding",
        batch_size=10
    )
    
    embedded_chunks = await node_embedder.a_invoke(sample_chunks)
    
    print(f"\n✅ NodeEmbedder:")
    print(f"   Chunk processati: {len(embedded_chunks)}")
    
    for chunk in embedded_chunks:
        print(f"   Chunk {chunk.id}:")
        print(f"     Embedding count: {len(chunk.embeddings)}")
        for emb in chunk.embeddings:
            print(f"     {emb.name}: {len(emb.vector)} dim")


# =============================================================================
# 4. CAPTIONER EXAMPLES
# =============================================================================

async def example_captioner():
    """Esempio di utilizzo LLMCaptioner"""
    print("\n🖼️  Esempio LLMCaptioner")
    
    captioner = LLMCaptioner(
        client=CLIENT,
        max_workers=2,
        system_prompt_figure="Descrivi questa immagine con attenzione ai dettagli tecnici",
        system_prompt_table="Analizza questa tabella e riassumi i dati principali"
    )
    
    # Simulazione di nodo con media (normalmente viene da AzureParser)
    print("ℹ️  Il captioner funziona su nodi con immagini/tabelle parsate")
    print("   Richiede input da AzureParser con elementi Media")
    print("   Vedere rag_example.py per implementazione completa")


# =============================================================================
# 5. VECTORSTORE EXAMPLES
# =============================================================================

async def example_vectorstore():
    """Esempio di utilizzo QdrantVectorstore"""
    print("\n🗄️  Esempio QdrantVectorstore")
    
    vectorstore = QdrantVectorstore(
        host=CONFIG["qdrant_host"],
        port=CONFIG["qdrant_port"]
    )
    
    collection_name = "test_collection"
    
    # Creazione chunk di test con embedding
    test_chunks = [
        Chunk(id="1", text="Python è un linguaggio di programmazione"),
        Chunk(id="2", text="JavaScript è usato per lo sviluppo web"),
        Chunk(id="3", text="Machine learning utilizza algoritmi statistici")
    ]
    
    # Aggiungi embedding ai chunk
    embedder = NodeEmbedder(client=CLIENT, model_name=CONFIG["embedding_model"])
    embedded_chunks = await embedder.a_invoke(test_chunks)
    
    try:
        # Aggiunta al vectorstore
        await vectorstore.a_add(embedded_chunks, collection_name=collection_name)
        print(f"✅ Aggiunti {len(embedded_chunks)} chunk alla collezione")
        
        # Test di ricerca
        query = "programmazione Python"
        query_embedder = ClientEmbedder(client=CLIENT)
        query_embedding = await query_embedder.a_invoke(query)
        
        results = await vectorstore.a_search(
            query_vector=query_embedding,
            collection_name=collection_name,
            top_k=3
        )
        
        print(f"\n🔍 Ricerca: '{query}'")
        print(f"   Risultati trovati: {len(results)}")
        for i, result in enumerate(results):
            print(f"   {i+1}. {result.text} (score: {getattr(result, 'score', 'N/A')})")
            
    except Exception as e:
        print(f"❌ Errore vectorstore: {e}")
        print("   Assicurarsi che Qdrant sia in esecuzione su localhost:6333")


# =============================================================================
# 6. RERANKER EXAMPLES
# =============================================================================

async def example_reranker():
    """Esempio di utilizzo CohereReranker"""
    print("\n📊 Esempio CohereReranker")
    
    if not CONFIG.get("cohere_key"):
        print("⚠️  Cohere API key non configurata, esempio saltato")
        return
    
    reranker = CohereReranker(
        api_key=CONFIG["cohere_key"],
        endpoint="https://api.cohere.com/v1",
        top_n=3,
        threshold=0.5
    )
    
    # Simulazione risultati di ricerca
    query = "machine learning algorithms"
    mock_results = [
        Chunk(id="1", text="Machine learning algorithms include decision trees and neural networks"),
        Chunk(id="2", text="Python programming language is popular for data science"),
        Chunk(id="3", text="Supervised learning algorithms learn from labeled data"),
        Chunk(id="4", text="Deep learning is a subset of machine learning using neural networks"),
        Chunk(id="5", text="JavaScript frameworks are used for web development")
    ]
    
    try:
        reranked = await reranker.a_invoke({
            "query": query,
            "documents": mock_results
        })
        
        print(f"✅ Reranking completato")
        print(f"   Query: {query}")
        print(f"   Documenti originali: {len(mock_results)}")
        print(f"   Documenti reranked: {len(reranked)}")
        
        print("\n📈 Risultati reranked:")
        for i, doc in enumerate(reranked):
            print(f"   {i+1}. {doc.text[:60]}...")
            
    except Exception as e:
        print(f"❌ Errore reranking: {e}")


# =============================================================================
# 7. PROMPT TEMPLATE EXAMPLES
# =============================================================================

def example_prompt_template():
    """Esempio di utilizzo ChatPromptTemplate"""
    print("\n💬 Esempio ChatPromptTemplate")
    
    # Template semplice
    template = ChatPromptTemplate(
        template="Rispondi alla domanda basandoti su: {context}\n\nDomanda: {question}\nRisposta:"
    )
    
    # Utilizzo del template
    context = "Il machine learning è una branca dell'AI che permette ai computer di apprendere dai dati."
    question = "Cos'è il machine learning?"
    
    formatted_prompt = template.format(context=context, question=question)
    
    print("✅ Template formattato:")
    print(f"   Template: {template.template}")
    print(f"   Output:\n{formatted_prompt}")
    
    # Template più complesso
    advanced_template = ChatPromptTemplate(
        template="""Sei un assistente AI esperto in {domain}.

Contesto:
{context}

Istruzioni:
- Usa solo informazioni dal contesto
- Sii preciso e conciso
- Cita fonti quando possibile

Domanda: {question}

Risposta dettagliata:"""
    )
    
    formatted_advanced = advanced_template.format(
        domain="intelligenza artificiale",
        context=context,
        question=question
    )
    
    print(f"\n📝 Template avanzato:\n{formatted_advanced}")


# =============================================================================
# 8. METATAGGER EXAMPLES
# =============================================================================

def example_metatagger():
    """Esempio di utilizzo KeywordMetatagger"""
    print("\n🏷️  Esempio KeywordMetatagger")
    
    metatagger = KeywordMetatagger(num_keywords=5)
    
    sample_texts = [
        "Il machine learning è una tecnologia che permette ai computer di apprendere automaticamente",
        "Le reti neurali artificiali sono ispirate al funzionamento del cervello umano",
        "L'elaborazione del linguaggio naturale consente alle macchine di comprendere il testo"
    ]
    
    print("✅ Estrazione keywords:")
    for i, text in enumerate(sample_texts):
        # Nota: KeywordMetatagger potrebbe richiedere personalizzazione per funzionare
        print(f"   Testo {i+1}: {text[:50]}...")
        print(f"   Keywords: [implementazione da personalizzare]")
    
    print("\nℹ️  KeywordMetatagger richiede implementazione custom per l'estrazione")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Esegue tutti gli esempi"""
    print("🚀 Esempi componenti RAG datapizzai\n")
    
    # Esempi sincroni
    example_azure_parser()
    example_text_splitter() 
    example_recursive_splitter()
    example_prompt_template()
    example_metatagger()
    
    # Esempi asincroni
    await example_embedders()
    await example_captioner()
    await example_vectorstore()
    await example_reranker()
    
    print("\n✨ Tutti gli esempi completati!")
    print("💡 Per un esempio completo end-to-end, vedere rag_example.py")


if __name__ == "__main__":
    asyncio.run(main())
