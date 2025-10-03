"""
Script per diagnosticare e risolvere problemi con API key

Questo script aiuta a identificare e risolvere problemi comuni con le API key
per OpenAI, Azure OpenAI e altri servizi utilizzati nel RAG.
"""

import os
from dotenv import load_dotenv
import re

def check_environment():
    """Controlla le variabili d'ambiente"""
    
    print("🔍 Controllo configurazione ambiente")
    print("=" * 40)
    
    # Carica .env se esiste
    env_files = ['../.env']
    env_loaded = False
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"📁 Caricando {env_file}")
            load_dotenv(env_file)
            env_loaded = True
            break
    
    if not env_loaded:
        print("⚠️ Nessun file .env trovato")
    
    # Controlla variabili chiave
    keys_to_check = [
        ('OPENAI_API_KEY', 'OpenAI diretto'),
        ('AZURE_OPENAI_API_KEY', 'Azure OpenAI'),
        ('AZURE_OPENAI_ENDPOINT', 'Azure OpenAI endpoint'),
        ('AZURE_DOCUMENT_INTELLIGENCE_API_KEY', 'Azure Document Intelligence'),
        ('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT', 'Azure Document Intelligence endpoint'),
        ('COHERE_API_KEY', 'Cohere (opzionale)')
    ]
    
    print(f"\n🔑 Stato API keys:")
    print("-" * 30)
    
    found_keys = {}
    
    for key, description in keys_to_check:
        value = os.getenv(key)
        if value:
            # Maschera la key per sicurezza
            if key.endswith('_KEY'):
                masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                masked = value
            print(f"✅ {description:25} {masked}")
            found_keys[key] = value
        else:
            print(f"❌ {description:25} Non configurata")
    
    return found_keys

def validate_openai_key(api_key):
    """Valida formato API key OpenAI"""
    
    print(f"\n🔍 Validazione API key OpenAI")
    print("-" * 30)
    
    if not api_key:
        print("❌ API key mancante")
        return False
    
    # Pattern per chiavi OpenAI
    patterns = {
        'OpenAI standard': r'^sk-[A-Za-z0-9]{48}$',
        'OpenAI project': r'^sk-proj-[A-Za-z0-9_-]{64}$',
        'OpenAI org': r'^sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}$'
    }
    
    print(f"Lunghezza: {len(api_key)} caratteri")
    print(f"Inizia con: {api_key[:10]}...")
    print(f"Finisce con: ...{api_key[-4:]}")
    
    valid = False
    for pattern_name, pattern in patterns.items():
        if re.match(pattern, api_key):
            print(f"✅ Formato valido: {pattern_name}")
            valid = True
            break
    
    if not valid:
        print("⚠️ Formato non standard (potrebbe comunque funzionare)")
        
        # Controlli aggiuntivi
        if not api_key.startswith('sk-'):
            print("❌ Dovrebbe iniziare con 'sk-'")
        
        if len(api_key) < 40:
            print("❌ Troppo corta (dovrebbe essere 48+ caratteri)")
        
        if ' ' in api_key or '\n' in api_key:
            print("❌ Contiene spazi o newline")
    
    return valid

def test_openai_connection(api_key):
    """Testa connessione OpenAI"""
    
    print(f"\n🌐 Test connessione OpenAI")
    print("-" * 30)
    
    try:
        from datapizza.clients import OpenAIClient
        
        client = OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            system_prompt="Sei un esperto di programmazione Python.",
            temperature=0.3,  # Più deterministico per il codice
            )

        response = client.invoke("Ciao! Come stai?")
        
        print("✅ Connessione riuscita!")
        print(f"Risposta: {response.content}")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Errore connessione: {error_str}")
        
        # Analisi errori comuni
        if "401" in error_str or "invalid_api_key" in error_str:
            print("💡 Problema: API key non valida")
            print("   - Verifica che sia corretta")
            print("   - Controlla che non sia scaduta")
            print("   - Verifica quota/billing OpenAI")
            
        elif "429" in error_str:
            print("💡 Problema: Rate limiting")
            print("   - Troppo traffico, riprova tra poco")
            
        elif "403" in error_str:
            print("💡 Problema: Accesso negato")
            print("   - Verifica permessi account OpenAI")
            
        return False

def test_azure_openai_connection(api_key, endpoint):
    """Testa connessione Azure OpenAI"""
    
    print(f"\n🌐 Test connessione Azure OpenAI")
    print("-" * 30)
    
    if not api_key or not endpoint:
        print("❌ API key o endpoint mancanti")
        return False
    
    try:
        from datapizza.clients import OpenAIClient
        
        client = OpenAIClient(
            api_key=api_key,
            base_url=endpoint
        )
        
        response = client.invoke([{
            "role": "user",
            "content": "Rispondi solo 'OK'"
        }])
        
        print("✅ Connessione Azure OpenAI riuscita!")
        print(f"Risposta: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Errore Azure OpenAI: {e}")
        
        error_str = str(e)
        if "404" in error_str:
            print("💡 Problema: Endpoint non trovato")
            print("   - Verifica formato endpoint Azure OpenAI")
            print("   - Dovrebbe essere: https://your-resource.openai.azure.com/")
            
        return False

def create_env_template():
    """Crea template .env con le configurazioni corrette"""
    
    print(f"\n📝 Creazione template .env")
    print("-" * 30)
    
    template = """# Configurazione RAG datapizza
# Scegli UNA delle opzioni per il client LLM

# === OPZIONE 1: OpenAI diretto (raccomandato per iniziare) ===
OPENAI_API_KEY=sk-your-real-openai-key-here

# === OPZIONE 2: Azure OpenAI (alternativa) ===
# AZURE_OPENAI_API_KEY=your-azure-openai-key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# === OPZIONE 3: Azure Document Intelligence (solo per AzureParser) ===
# AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-doc-intel-key
# AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com/

# === Opzionali ===
# COHERE_API_KEY=your-cohere-key

# === Vector Database ===
QDRANT_HOST=localhost
QDRANT_PORT=6333
"""
    
    try:
        with open('.env.template', 'w') as f:
            f.write(template)
        print("✅ Creato .env.template")
        print("💡 Copia in .env e inserisci le tue credenziali reali")
        
    except Exception as e:
        print(f"❌ Errore creazione template: {e}")

def main():
    """Diagnostica completa"""
    
    print("🚀 Diagnostica configurazione RAG")
    print("=" * 50)
    
    # 1. Controllo ambiente
    found_keys = check_environment()
    
    # 2. Test OpenAI se disponibile
    openai_key = found_keys.get('OPENAI_API_KEY')
    if openai_key:
        validate_openai_key(openai_key)
        test_openai_connection(openai_key)
    
    # 3. Test Azure OpenAI se disponibile
    azure_key = found_keys.get('AZURE_OPENAI_API_KEY')
    azure_endpoint = found_keys.get('AZURE_OPENAI_ENDPOINT')
    if azure_key and azure_endpoint:
        test_azure_openai_connection(azure_key, azure_endpoint)
    
    # 4. Raccomandazioni
    print(f"\n💡 Raccomandazioni:")
    print("-" * 30)
    
    if not openai_key and not azure_key:
        print("❌ Nessuna API key LLM configurata")
        print("   1. Vai su https://platform.openai.com/api-keys")
        print("   2. Crea una nuova API key")
        print("   3. Aggiungila al file .env come OPENAI_API_KEY")
        create_env_template()
        
    elif openai_key and "sk-pro" in openai_key:
        print("⚠️ Stai usando una chiave 'sk-proj-' o simile")
        print("   Verifica che sia attiva e abbia crediti")
        
    else:
        print("✅ Configurazione sembra OK")
        print("   Se hai ancora errori, controlla:")
        print("   - Quota/billing OpenAI")
        print("   - Connessione internet")
        print("   - Firewall/proxy")

if __name__ == "__main__":
    main()
