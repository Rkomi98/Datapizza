"""
Esempio pratico con TextParser e correzione dell'errore TreeBuilder

Questo esempio mostra come usare correttamente TextParser e LLMTreeBuilder
risolvendo l'errore TypeError che hai riscontrato.
"""

import asyncio
from datapizzai.clients import OpenAIClient
from datapizzai.modules.parsers.text_parser import TextParser, parse_text
from datapizzai.modules.treebuilder import LLMTreeBuilder
from datapizzai.modules.splitters import TextSplitter
from datapizzai.embedders import NodeEmbedder


def extract_text_from_node(node):
    """
    Estrae tutto il testo da un nodo e dai suoi figli
    Utile per convertire strutture Node complesse in testo semplice
    """
    text_parts = []
    
    # Aggiungi contenuto del nodo corrente
    if hasattr(node, 'content') and node.content:
        text_parts.append(node.content)
    
    # Aggiungi contenuto dai figli ricorsivamente
    if hasattr(node, 'children') and node.children:
        for child in node.children:
            child_text = extract_text_from_node(child)
            if child_text.strip():
                text_parts.append(child_text)
    
    return "\n".join(text_parts)


async def text_parser_example():
    """Esempio completo con TextParser"""
    
    print("📝 Esempio TextParser + TreeBuilder")
    print("=" * 40)
    
    # Il tuo testo di esempio
    text = """Vector embeddings have been tasked with an ever-increasing set of retrieval tasks over the years, with a 
nascent rise in using them for reasoning, instruction-following, coding, and more. These new benchmarks
push embeddings to work for any query and any notion of relevance that could be given. While prior
works have pointed out theoretical limitations of vector embeddings, there is a common assumption
that these difficulties are exclusively due to unrealistic queries, and those that are not can be overcome
with better training data and larger models. In this work, we demonstrate that we may encounter these
theoretical limitations in realistic settings with extremely simple queries. We connect known results
in learning theory, showing that the number of top-𝑘 subsets of documents capable of being returned
as the result of some query is limited by the dimension of the embedding. We empirically show that
this holds true even if we restrict to 𝑘 = 2, and directly optimize on the test set with free parameterized
embeddings. We then create a realistic dataset called LIMIT that stress tests models based on these
theoretical results, and observe that even state-of-the-art models fail on this dataset despite the simple
nature of the task. Our work shows the limits of embedding models under the existing single vector
paradigm and calls for future research to develop methods that can resolve this fundamental limitation."""
    
    # 1. PARSING con TextParser
    print("1️⃣ Parsing con TextParser...")
    
    # Metodo 1: Classe
    parser = TextParser()
    document_node = parser.parse(text, metadata={"source": "research_paper"})
    
    # Metodo 2: Funzione di convenienza (equivalente)
    # document_node = parse_text(text)
    
    print(f"   ✅ Documento parsato")
    print(f"   Tipo: {document_node.node_type}")
    print(f"   Figli: {len(document_node.children)} paragrafi")
    print(f"   Metadata: {document_node.metadata}")
    
    # Mostra struttura
    for i, paragraph in enumerate(document_node.children):
        sentences_count = len(paragraph.children) if paragraph.children else 0
        print(f"   Paragrafo {i+1}: {sentences_count} frasi")
    
    # 2. TREE BUILDER (correzione dell'errore)
    print(f"\n2️⃣ Tree Building con LLM...")
    
    # Setup client (sostituisci con le tue credenziali)
    try:
        client = OpenAIClient(api_key="your_openai_key")
        
        tree_builder = LLMTreeBuilder(
            client=client,
            system_prompt="Riorganizza la struttura del documento per migliorare la comprensione."
        )
        
        # CORREZIONE: usa build_tree() con il TESTO, non invoke() con il NODE!
        # L'errore era qui: tree_builder.invoke(document_node) ❌
        # Corretto: tree_builder.build_tree(text) ✅
        
        restructured_node = tree_builder.build_tree(text)
        
        print(f"   ✅ Documento ristrutturato")
        print(f"   Tipo: {restructured_node.node_type}")
        print(f"   Figli: {len(restructured_node.children)}")
        
    except Exception as e:
        print(f"   ⚠️ TreeBuilder saltato (configurare API key): {e}")
        restructured_node = document_node
    
    # 3. ESTRAZIONE TESTO per step successivi
    print(f"\n3️⃣ Estrazione testo per splitting...")
    
    # Estrai tutto il testo dalla struttura
    extracted_text = extract_text_from_node(restructured_node)
    print(f"   ✅ Testo estratto: {len(extracted_text)} caratteri")
    print(f"   Preview: {extracted_text[:100]}...")
    
    # 4. SPLITTING
    print(f"\n4️⃣ Splitting del testo...")
    
    splitter = TextSplitter(max_char=500, overlap=50)
    chunks = splitter.invoke(extracted_text)
    
    print(f"   ✅ Creati {len(chunks)} chunk")
    for i, chunk in enumerate(chunks[:3]):  # Mostra primi 3
        print(f"   Chunk {i+1}: {len(chunk.text)} caratteri")
        print(f"     Preview: {chunk.text[:80]}...")
    
    # 5. EMBEDDING (opzionale)
    print(f"\n5️⃣ Embedding (opzionale)...")
    
    try:
        embedder = NodeEmbedder(
            client=client,
            model_name="text-embedding-3-small"
        )
        
        embedded_chunks = await embedder.a_invoke(chunks)
        print(f"   ✅ Embedding generati per {len(embedded_chunks)} chunk")
        
        # Mostra info embedding
        for chunk in embedded_chunks[:2]:
            for emb in chunk.embeddings:
                print(f"   {emb.name}: {len(emb.vector)} dimensioni")
        
    except Exception as e:
        print(f"   ⚠️ Embedding saltato: {e}")
    
    print(f"\n🎉 Esempio completato!")
    return chunks


def simple_text_parser_demo():
    """Demo semplice senza API calls"""
    
    print("🚀 Demo TextParser semplice (offline)")
    print("=" * 40)
    
    text = """Questo è il primo paragrafo. Ha due frasi.

Questo è il secondo paragrafo. Anche questo ha due frasi."""
    
    # Parsing
    document = parse_text(text)
    
    print("Struttura documento:")
    print(f"Documento ({document.node_type})")
    
    for i, paragraph in enumerate(document.children):
        print(f"  └─ Paragrafo {i+1} ({paragraph.node_type})")
        
        for j, sentence in enumerate(paragraph.children):
            print(f"      └─ Frase {j+1}: '{sentence.content}'")
    
    # Estrazione testo
    extracted = extract_text_from_node(document)
    print(f"\nTesto estratto:\n{extracted}")


if __name__ == "__main__":
    print("Scegli demo:")
    print("1. Demo semplice (offline)")
    print("2. Demo completa (richiede API key)")
    
    choice = input("Scelta (1 o 2): ").strip()
    
    if choice == "1":
        simple_text_parser_demo()
    elif choice == "2":
        asyncio.run(text_parser_example())
    else:
        print("Scelta non valida, eseguo demo semplice...")
        simple_text_parser_demo()
