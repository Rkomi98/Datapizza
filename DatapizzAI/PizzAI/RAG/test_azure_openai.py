"""
Test rapido per verificare la configurazione Azure OpenAI
Usa questo script per verificare che tutto funzioni prima di procedere con RAG
"""

import os
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

def test_azure_openai():
    """Testa la connessione ad Azure OpenAI"""
    
    print("🔧 Test configurazione Azure OpenAI")
    print("=" * 40)
    
    # Verifica variabili ambiente
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    print(f"API Key: {'✅ Configurata' if api_key else '❌ Mancante'}")
    print(f"Endpoint: {'✅ ' + endpoint if endpoint else '❌ Mancante'}")
    
    if not api_key or not endpoint:
        print("\n❌ Configurazione mancante!")
        print("Crea file .env con:")
        print("AZURE_OPENAI_API_KEY=your_key_here")
        print("AZURE_OPENAI_ENDPOINT=your_endpoint_here")
        return False
    
    # Test connessione
    try:
        from datapizzai.clients import OpenAIClient
        
        print(f"\n🔌 Test connessione...")
        client = OpenAIClient(
            api_key=api_key,
            base_url=endpoint,
            model_name="gpt-4"  # cambia se hai un modello diverso deployato
        )
        
        # Test semplice
        response = client.invoke([{
            "role": "user",
            "content": "Rispondi con 'OK' se tutto funziona"
        }])
        
        print(f"✅ Connessione riuscita!")
        print(f"Risposta: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Errore connessione: {e}")
        print("\nPossibili cause:")
        print("- Endpoint sbagliato (deve finire con .openai.azure.com/)")
        print("- API key non valida")
        print("- Modello non deployato nella tua risorsa Azure")
        print("- Quota esaurita")
        return False

def test_embedding():
    """Testa gli embedding"""
    
    print(f"\n🔢 Test embedding...")
    
    try:
        from datapizzai.clients import OpenAIClient
        from datapizzai.embedders import ClientEmbedder
        
        client = OpenAIClient(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            base_url=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        
        embedder = ClientEmbedder(
            client=client,
            model_name="text-embedding-3-small"  # verifica che sia deployato
        )
        
        # Test embedding
        text = "Questo è un test per gli embedding"
        embedding = embedder.invoke(text)
        
        print(f"✅ Embedding generato!")
        print(f"Dimensioni: {len(embedding)}")
        print(f"Primi 3 valori: {embedding[:3]}")
        return True
        
    except Exception as e:
        print(f"❌ Errore embedding: {e}")
        print("Verifica che text-embedding-3-small sia deployato in Azure AI Studio")
        return False

def test_pdf_parsing():
    """Testa il parsing PDF semplice"""
    
    print(f"\n📄 Test parsing PDF...")
    
    try:
        import PyPDF2
        from pathlib import Path
        
        # Cerca un PDF di test
        test_files = [
            "RAG/document.pdf",
            "document.pdf", 
            "test.pdf"
        ]
        
        pdf_file = None
        for f in test_files:
            if Path(f).exists():
                pdf_file = f
                break
        
        if not pdf_file:
            print("⚠️  Nessun PDF di test trovato")
            print("Crea un file 'document.pdf' per testare")
            return False
        
        # Parsing
        with open(pdf_file, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        print(f"✅ PDF parsato: {pdf_file}")
        print(f"Pagine: {len(pdf_reader.pages)}")
        print(f"Caratteri estratti: {len(text)}")
        print(f"Preview: {text[:100]}...")
        return True
        
    except ImportError:
        print("❌ PyPDF2 non installato")
        print("Installa con: pip install PyPDF2")
        return False
    except Exception as e:
        print(f"❌ Errore parsing: {e}")
        return False

def test_qdrant():
    """Testa la connessione a Qdrant"""
    
    print(f"\n🗄️  Test Qdrant...")
    
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        
        print(f"✅ Qdrant connesso!")
        print(f"Collezioni esistenti: {len(collections.collections)}")
        return True
        
    except ImportError:
        print("❌ qdrant-client non installato")
        print("Installa con: pip install qdrant-client")
        return False
    except Exception as e:
        print(f"❌ Qdrant non raggiungibile: {e}")
        print("Avvia con: docker run -p 6333:6333 qdrant/qdrant")
        return False

def main():
    """Esegue tutti i test"""
    
    print("🚀 Test completo sistema RAG")
    print("=" * 50)
    
    tests = [
        ("Azure OpenAI", test_azure_openai),
        ("Embedding", test_embedding),
        ("PDF Parsing", test_pdf_parsing),
        ("Qdrant", test_qdrant)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Errore in {test_name}: {e}")
            results[test_name] = False
    
    # Riassunto
    print(f"\n📊 Riassunto test:")
    print("-" * 30)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Tutti i test superati! Puoi procedere con RAG completo")
        print("💡 Prova ora: python simple_rag_example.py")
    else:
        print("⚠️  Alcuni test falliti. Risolvi i problemi prima di procedere")
        print("📚 Consulta AZURE_SERVICES_GUIDE.md per aiuto")

if __name__ == "__main__":
    main()
