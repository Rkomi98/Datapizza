"""
Esempio migliorato per TreeBuilder con gestione errori robusta

Questo esempio mostra come gestire gli errori del TreeBuilder e 
fornisce alternative più affidabili per la ristrutturazione del testo.
"""

import asyncio
import logging
from datapizzai.clients import OpenAIClient
from datapizzai.modules.parsers.text_parser import parse_text
from datapizzai.modules.treebuilder import LLMTreeBuilder
from datapizzai.modules.splitters import TextSplitter

# Configura logging per vedere i dettagli
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobustTreeBuilder:
    """TreeBuilder alternativo più robusto per gestire errori LLM"""
    
    def __init__(self, client):
        self.client = client
    
    def build_tree_simple(self, text: str):
        """
        Approccio semplificato che chiede all'LLM di migliorare la struttura
        senza richiedere XML specifico
        """
        prompt = f"""Riorganizza e migliora la struttura del seguente testo.
Mantieni tutto il contenuto originale ma organizzalo in modo più chiaro e logico.
Usa paragrafi ben definiti e una struttura gerarchica quando appropriato.

Testo originale:
{text}

Testo riorganizzato:"""

        try:
            response = self.client.invoke([{
                "role": "user",
                "content": prompt
            }])
            
            improved_text = response.content.strip()
            
            # Usa TextParser sul testo migliorato
            return parse_text(improved_text)
            
        except Exception as e:
            logger.warning(f"TreeBuilder fallback: {e}")
            # Fallback: usa TextParser sul testo originale
            return parse_text(text)


def test_treebuilders(text: str, client):
    """Testa diversi approcci per il TreeBuilder"""
    
    print("🌳 Test TreeBuilder con diversi approcci")
    print("=" * 50)
    
    # 1. TreeBuilder originale (quello che dà errore)
    print("1️⃣ LLMTreeBuilder originale...")
    try:
        tree_builder = LLMTreeBuilder(
            client=client,
            system_prompt="Riorganizza la struttura del documento per migliorare la comprensione."
        )
        
        # Prova con timeout più breve per evitare attese lunghe
        original_result = tree_builder.build_tree(text)
        
        print(f"   ✅ Successo con LLMTreeBuilder")
        print(f"   Tipo: {original_result.node_type}")
        print(f"   Figli: {len(original_result.children)}")
        print(f"   Metadata: {original_result.metadata}")
        
        # Controlla se è fallback
        if original_result.metadata and original_result.metadata.get('llm_fallback'):
            print(f"   ⚠️ Usato fallback automatico")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        original_result = None
    
    # 2. TreeBuilder robusto alternativo
    print(f"\n2️⃣ RobustTreeBuilder alternativo...")
    try:
        robust_builder = RobustTreeBuilder(client)
        robust_result = robust_builder.build_tree_simple(text)
        
        print(f"   ✅ Successo con RobustTreeBuilder")
        print(f"   Tipo: {robust_result.node_type}")
        print(f"   Figli: {len(robust_result.children)}")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        robust_result = None
    
    # 3. Senza TreeBuilder (solo TextParser)
    print(f"\n3️⃣ Solo TextParser (nessun LLM)...")
    try:
        simple_result = parse_text(text)
        
        print(f"   ✅ Successo con TextParser")
        print(f"   Tipo: {simple_result.node_type}")
        print(f"   Figli: {len(simple_result.children)}")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        simple_result = None
    
    # Confronto risultati
    print(f"\n📊 Confronto risultati:")
    print("-" * 30)
    
    results = [
        ("LLMTreeBuilder", original_result),
        ("RobustTreeBuilder", robust_result),
        ("TextParser", simple_result)
    ]
    
    for name, result in results:
        if result:
            paragraphs = len(result.children) if result.children else 0
            print(f"{name:18} ✅ {paragraphs} paragrafi")
        else:
            print(f"{name:18} ❌ Fallito")
    
    # Restituisci il migliore disponibile
    for name, result in results:
        if result:
            print(f"\n🏆 Usando risultato di: {name}")
            return result
    
    return None


def debug_llm_output(client, text: str):
    """Debug dell'output LLM per capire perché l'XML non è valido"""
    
    print("🔍 Debug output LLM TreeBuilder")
    print("=" * 40)
    
    # Usa lo stesso prompt del TreeBuilder originale
    system_prompt = """You are an expert text structuring tool. Your task is to analyze the given text and structure it hierarchically into sections, paragraphs, and sentences.
Output the structured text using XML-like tags: `<document>`, `<section>`, `<paragraph>`, and `<sentence>`.
Ensure all original text content is preserved within the innermost tags (sentences). Do not add any explanations or introductory text outside the main <document> tag."""

    try:
        response = client.invoke([{
            "role": "system", 
            "content": system_prompt
        }, {
            "role": "user",
            "content": text
        }])
        
        llm_output = response.content
        
        print("Raw LLM Output:")
        print("-" * 20)
        print(repr(llm_output))  # Mostra caratteri speciali
        print("\nFormatted Output:")
        print("-" * 20)
        print(llm_output)
        
        # Analizza problemi comuni
        print(f"\n🔍 Analisi problemi:")
        print(f"- Inizia con '<document>'? {llm_output.strip().startswith('<document>')}")
        print(f"- Finisce con '</document>'? {llm_output.strip().endswith('</document>')}")
        print(f"- Contiene caratteri non-ASCII? {not llm_output.isascii()}")
        print(f"- Lunghezza: {len(llm_output)} caratteri")
        
        # Controlla tag bilanciati
        open_tags = llm_output.count('<document>') + llm_output.count('<section>') + \
                   llm_output.count('<paragraph>') + llm_output.count('<sentence>')
        close_tags = llm_output.count('</document>') + llm_output.count('</section>') + \
                    llm_output.count('</paragraph>') + llm_output.count('</sentence>')
        
        print(f"- Tag aperti: {open_tags}, Tag chiusi: {close_tags}")
        print(f"- Tag bilanciati? {open_tags == close_tags}")
        
    except Exception as e:
        print(f"❌ Errore nel debug: {e}")


async def main():
    """Esempio principale con gestione errori migliorata"""
    
    # Testo di test (quello che ti dava errore)
    text = """Vector embeddings have been tasked with an ever-increasing set of retrieval tasks over the years, with a 
nascent rise in using them for reasoning, instruction-following, coding, and more. These new benchmarks
push embeddings to work for any query and any notion of relevance that could be given. While prior
works have pointed out theoretical limitations of vector embeddings, there is a common assumption
that these difficulties are exclusively due to unrealistic queries, and those that are not can be overcome
with better training data and larger models. In this work, we demonstrate that we may encounter these
theoretical limitations in realistic settings with extremely simple queries."""
    
    print("🚀 Test TreeBuilder con gestione errori migliorata")
    print("=" * 60)
    
    # Setup client (sostituisci con le tue credenziali)
    try:
        client = OpenAIClient(api_key="your_openai_key")
        
        # Debug dell'output LLM
        print("FASE 1: Debug output LLM")
        debug_llm_output(client, text[:500])  # Usa solo parte del testo per debug
        
        print(f"\n" + "=" * 60)
        print("FASE 2: Test diversi approcci TreeBuilder")
        
        # Test diversi approcci
        best_result = test_treebuilders(text, client)
        
        if best_result:
            print(f"\n✅ Risultato finale ottenuto!")
            
            # Procedi con il resto della pipeline
            print(f"\n🔄 Continuo con splitting...")
            
            # Estrai testo per splitting
            def extract_text_from_node(node):
                text_parts = []
                if hasattr(node, 'content') and node.content:
                    text_parts.append(node.content)
                if hasattr(node, 'children') and node.children:
                    for child in node.children:
                        child_text = extract_text_from_node(child)
                        if child_text.strip():
                            text_parts.append(child_text)
                return "\n".join(text_parts)
            
            final_text = extract_text_from_node(best_result)
            
            # Splitting
            splitter = TextSplitter(max_char=500, overlap=50)
            chunks = splitter.invoke(final_text)
            
            print(f"   ✅ Creati {len(chunks)} chunk")
            print(f"   Lunghezza testo finale: {len(final_text)} caratteri")
            
        else:
            print(f"\n❌ Nessun risultato ottenuto")
        
    except Exception as e:
        print(f"❌ Errore nella configurazione client: {e}")
        print("💡 Suggerimenti:")
        print("   1. Verifica API key OpenAI")
        print("   2. Controlla connessione internet")
        print("   3. Prova con un testo più breve")
        
        # Fallback senza LLM
        print(f"\n🔄 Fallback: uso solo TextParser...")
        simple_result = parse_text(text)
        print(f"   ✅ TextParser: {len(simple_result.children)} paragrafi")


def simple_solution():
    """Soluzione semplice senza TreeBuilder per evitare errori"""
    
    print("💡 Soluzione semplice senza TreeBuilder")
    print("=" * 40)
    
    text = """Vector embeddings have been tasked with an ever-increasing set of retrieval tasks..."""
    
    # Usa solo TextParser - più affidabile
    document = parse_text(text)
    
    print(f"✅ Parsing completato")
    print(f"   Paragrafi: {len(document.children)}")
    
    # Splitting diretto
    splitter = TextSplitter(max_char=500, overlap=50)
    chunks = splitter.invoke(text)
    
    print(f"✅ Splitting completato")
    print(f"   Chunk: {len(chunks)}")
    
    print(f"\n💡 Raccomandazione: per iniziare, salta il TreeBuilder")
    print("   Il TextParser è già molto efficace per la maggior parte dei casi")


if __name__ == "__main__":
    print("Scegli test:")
    print("1. Test completo con debug (richiede API key)")
    print("2. Soluzione semplice senza TreeBuilder")
    
    choice = input("Scelta (1 o 2): ").strip()
    
    if choice == "1":
        asyncio.run(main())
    else:
        simple_solution()
