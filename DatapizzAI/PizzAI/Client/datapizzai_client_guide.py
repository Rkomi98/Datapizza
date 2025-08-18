#!/usr/bin/env python3
"""
Guida completa al Client di DatapizzAI
=====================================

Questo file contiene esempi dettagliati su come configurare e utilizzare
tutti i tipi di client disponibili nella libreria datapizzai, con esempi
pratici per ogni funzionalità avanzata.

Autore: Marco Calcaterra
Data: 2025
"""

import os
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Importazioni principali della libreria datapizzai
from datapizzai.clients import (
    ClientFactory, 
    OpenAIClient,
    AnthropicClient, 
    GoogleClient,
    MistralClient,
    AzureOpenAIClient
)
from datapizzai.clients.factory import Provider
from datapizzai.cache import Cache, MemoryCache, RedisCache
from datapizzai.memory import Memory
from datapizzai.tools import Tool
from datapizzai.type import TextBlock, MediaBlock, Media, ROLE

# ==============================================================================
# 1. CONFIGURAZIONE BASE DEI CLIENT
# ==============================================================================

def esempio_client_factory():
    """
    Il ClientFactory è il modo più semplice per creare un client.
    Supporta tutti i provider principali con configurazione automatica.
    """
    print("=== ESEMPIO: Utilizzo del ClientFactory ===")
    
    # Configurazione OpenAI
    openai_client = ClientFactory.create(
        provider=Provider.OPENAI,  # o semplicemente "openai"
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Sei un assistente AI utile e rispondi sempre in italiano.",
        temperature=0.7
    )
    
    # Configurazione Anthropic (Claude)
    anthropic_client = ClientFactory.create(
        provider=Provider.ANTHROPIC,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-sonnet-latest",
        system_prompt="Sei Claude, un assistente AI di Anthropic.",
        temperature=0.5
    )
    
    # Configurazione Google (Gemini)
    google_client = ClientFactory.create(
        provider=Provider.GOOGLE,
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash",
        system_prompt="Sei Gemini, l'assistente AI di Google.",
        temperature=0.6
    )
    
    # Configurazione Mistral
    mistral_client = ClientFactory.create(
        provider=Provider.MISTRAL,
        api_key=os.getenv("MISTRAL_API_KEY"),
        model="mistral-large-latest",
        system_prompt="Sei un assistente AI basato su Mistral.",
        temperature=0.7
    )
    
    print("✅ Client creati con successo usando ClientFactory")
    return openai_client


def esempio_client_diretti():
    """
    Creazione diretta dei client per configurazioni avanzate.
    Ogni client ha parametri specifici per il suo provider.
    """
    print("\n=== ESEMPIO: Creazione diretta dei client ===")
    
    # OpenAI Client con configurazione avanzata
    openai_client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Sei un esperto di programmazione Python.",
        temperature=0.3,  # Più deterministico per il codice
        cache=None  # Vedremo la cache più avanti
    )
    
    # Anthropic Client
    anthropic_client = AnthropicClient(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-sonnet-latest",
        system_prompt="Sei un assistente per la scrittura creativa.",
        temperature=0.8  # Più creativo
    )
    
    # Google Client con opzioni avanzate
    google_client = GoogleClient(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash",
        system_prompt="Sei un tutor di matematica paziente e formale.",
        temperature=0.4,
        # Opzioni specifiche per Google
        project_id=None,  # Per Vertex AI
        location=None,    # Per Vertex AI
        credentials_path=None,  # Per Vertex AI
        use_vertexai=False  # True per usare Vertex AI invece di GenAI
    )
    
    # Azure OpenAI Client (per deployment aziendali)
    azure_client = AzureOpenAIClient(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Sei un assistente aziendale professionale.",
        temperature=0.5,
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        #azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version="2024-02-15-preview"
    )
    
    print("✅ Client specifici creati con configurazioni avanzate")
    return openai_client


# ==============================================================================
# 2. UTILIZZO BASE DEI CLIENT
# ==============================================================================

def esempio_utilizzo_base():
    """
    Esempi di utilizzo base dei client per generare risposte.
    """
    print("\n=== ESEMPIO: Utilizzo base dei client ===")
    
    # Crea un client di esempio
    client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Sei un ragazzo di 27 anni esperto di GenAI, rispondi sempre in italiano in modo chiaro e conciso.",
        temperature=0.3,  # Più deterministico per il codice
        cache=None  # Vedremo la cache più avanti
    )
    
    # 1. Invocazione semplice con stringa
    print("1. Invocazione con stringa semplice:")
    try:
        response = client.invoke("Ciao! Come stai?")
        print(f"   Risposta: {response.text}")
        print(f"   Token usati: {response.prompt_tokens_used + response.completion_tokens_used}")
        print(f"   Stop reason: {response.stop_reason}")
    except Exception as e:
        print(f"   ⚠️ Errore (verifica la chiave API): {e}")
    
    # 2. Invocazione con TextBlock
    print("\n2. Invocazione con TextBlock:")
    text_blocks = [
        TextBlock(content="Spiegami cos'è il machine learning in 50 parole.")
    ]
    try:
        response = client.invoke(input=text_blocks)
        print(f"   Risposta: {response.text}")
    except Exception as e:
        print(f"   ⚠️ Errore (verifica la chiave API): {e}")
    
    # 3. Invocazione asincrona
    print("\n3. Invocazione asincrona:")
    import asyncio
    
    async def test_async():
        try:
            response = await client.a_invoke("Dimmi una curiosità sui gatti")
            return response.text
        except Exception as e:
            return f"⚠️ Errore: {e}"
    
    # result = asyncio.run(test_async())
    # print(f"   Risposta asincrona: {result}")
    print("   (Esempio di codice per invocazione asincrona mostrato sopra)")
    
    print("✅ Esempi di utilizzo base completati")


# ==============================================================================
# 3. GESTIONE DELLA MEMORIA (CONVERSAZIONI)
# ==============================================================================

def esempio_memoria():
    """
    La Memory permette di mantenere il contesto di conversazioni multi-turno.
    Ogni turno può contenere più blocchi di diversi tipi.
    """
    print("\n=== ESEMPIO: Gestione della memoria ===")
    
    # Crea un client e una memoria
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        system_prompt="Sei un assistente che ricorda le conversazioni precedenti."
    )
    
    memory = Memory()
    
    # 1. Aggiungi il primo turno dell'utente
    print("1. Primo turno - Utente presenta se stesso:")
    user_message = TextBlock(content="Ciao! Mi chiamo Marco e sono uno sviluppatore Python.")
    memory.add_turn([user_message], ROLE.USER)
    
    try:
        response = client.invoke("", memory=memory)
        # Aggiungi la risposta dell'assistente alla memoria
        assistant_message = TextBlock(content=response.text)
        memory.add_turn([assistant_message], ROLE.ASSISTANT)
        print(f"   Assistente: {response.text}")
    except Exception as e:
        print(f"   ⚠️ Simulazione risposta: Ciao Marco! Piacere di conoscerti. Come posso aiutarti con Python?")
        # Simula l'aggiunta alla memoria
        simulated_response = TextBlock(content="Ciao Marco! Piacere di conoscerti.")
        memory.add_turn([simulated_response], ROLE.ASSISTANT)
    
    # 2. Secondo turno - L'assistente dovrebbe ricordare il nome
    print("\n2. Secondo turno - Test della memoria:")
    user_question = TextBlock(content="Qual è il mio nome?")
    memory.add_turn([user_question], ROLE.USER)
    
    try:
        response = client.invoke("", memory=memory)
        print(f"   Assistente: {response.text}")
    except Exception as e:
        print(f"   ⚠️ Simulazione: Il tuo nome è Marco, come mi hai detto prima!")
    
    # 3. Informazioni sulla memoria
    print(f"\n3. Informazioni sulla memoria:")
    print(f"   Numero di turni: {len(memory.memory)}")
    print(f"   Numero totale di blocchi: {len(list(memory.iter_blocks()))}")
    
    # 4. Iterazione attraverso la memoria
    print(f"\n4. Contenuto della memoria:")
    for i, turn in enumerate(memory.memory):
        print(f"   Turno {i+1} ({turn.role.value}): {len(turn.blocks)} blocchi")
        for j, block in enumerate(turn.blocks):
            content_preview = block.content[:50] + "..." if len(block.content) > 50 else block.content
            print(f"     Blocco {j+1}: {content_preview}")
    
    # 5. Copia e pulizia della memoria
    memory_backup = memory.copy()
    print(f"\n5. Backup creato con {len(memory_backup.memory)} turni")
    
    # memory.clear()
    # print(f"   Memoria pulita: {len(memory.memory)} turni")
    
    print("✅ Gestione della memoria completata")
    return memory


# ==============================================================================
# 4. SISTEMA DI CACHE
# ==============================================================================

def esempio_cache():
    """
    Il sistema di cache permette di evitare chiamate ridondanti alle API,
    risparmiando tempo e costi. Supporta cache in memoria e Redis.
    """
    print("\n=== ESEMPIO: Sistema di cache ===")
    
    # 1. Cache in memoria (per sviluppo e test)
    print("1. Cache in memoria:")
    memory_cache = MemoryCache()
    
    client_with_cache = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        system_prompt="Rispondi sempre la stessa cosa per test di cache.",
        cache=memory_cache
    )
    
    # Simula due chiamate identiche
    prompt = "Dimmi ciao"
    print(f"   Prima chiamata: '{prompt}'")
    try:
        start_time = __import__('time').time()
        response1 = client_with_cache.invoke(prompt)
        time1 = __import__('time').time() - start_time
        print(f"   Tempo prima chiamata: {time1:.2f}s")
    except Exception as e:
        print(f"   ⚠️ Prima chiamata simulata (cache miss)")
    
    print(f"   Seconda chiamata identica: '{prompt}'")
    try:
        start_time = __import__('time').time()
        response2 = client_with_cache.invoke(prompt)
        time2 = __import__('time').time() - start_time
        print(f"   Tempo seconda chiamata: {time2:.2f}s (dovrebbe essere molto più veloce!)")
    except Exception as e:
        print(f"   ⚠️ Seconda chiamata simulata (cache hit - istantanea!)")
    
    # 2. Cache Redis (per produzione)
    print("\n2. Cache Redis (configurazione):")
    try:
        redis_cache = RedisCache(
            host="localhost",
            port=6379,
            db=0,
            password=None    # Optional Redis password
            expiration_time=120  # 2 minuti
        )
        
        client_with_redis = OpenAIClient(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            cache=redis_cache
        )
        print("   ✅ Cache Redis configurata (richiede server Redis attivo)")
    except Exception as e:
        print(f"   ⚠️ Redis non disponibile: {e}")
        print("   💡 Per usare Redis: pip install redis && redis-server")
    
    # 3. Cache personalizzata
    print("\n3. Cache personalizzata:")
    
    class FileCache(Cache):
        """Esempio di cache personalizzata che salva su file"""
        def __init__(self, cache_dir="./cache"):
            import os
            self.cache_dir = cache_dir
            os.makedirs(cache_dir, exist_ok=True)
        
        def get(self, key: str):
            import pickle
            import os
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            return None
        
        def set(self, key: str, value):
            import pickle
            import os
            cache_file = os.path.join(self.cache_dir, f"{key}.cache")
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
    
    file_cache = FileCache()
    print("   ✅ Cache personalizzata su file creata")
    
    print("✅ Sistema di cache completato")


# ==============================================================================
# 5. STRUMENTI (TOOLS) E FUNCTION CALLING
# ==============================================================================

def esempio_tools():
    """
    I tools permettono ai modelli di chiamare funzioni Python per eseguire
    azioni specifiche come calcoli, API calls, accesso a database, etc.
    """
    print("\n=== ESEMPIO: Tools e Function Calling ===")
    
    # 1. Definizione di un tool semplice
    print("1. Definizione di tools:")
    
    @Tool
    def calcola_area_cerchio(raggio: float) -> float:
        """Calcola l'area di un cerchio dato il raggio."""
        import math
        return math.pi * raggio ** 2
    
    @Tool
    def cerca_informazioni_meteo(citta: str, paese: str = "IT") -> str:
        """Cerca informazioni meteo per una città specifica."""
        # Simulazione di una chiamata API meteo
        return f"Il meteo a {citta}, {paese}: Soleggiato, 22°C"
    
    @Tool
    def salva_nota(titolo: str, contenuto: str, categoria: str = "generale") -> str:
        """Salva una nota nel sistema."""
        # Simulazione di salvataggio
        return f"Nota '{titolo}' salvata nella categoria '{categoria}'"
    
    print("   ✅ Tools definiti:")
    print(f"   - {calcola_area_cerchio.name}: {calcola_area_cerchio.description}")
    print(f"   - {cerca_informazioni_meteo.name}: {cerca_informazioni_meteo.description}")
    print(f"   - {salva_nota.name}: {salva_nota.description}")
    
    # 2. Utilizzo dei tools con un client
    print("\n2. Utilizzo dei tools:")
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Sei un assistente che può usare strumenti per aiutare l'utente."
    )
    
    tools = [calcola_area_cerchio, cerca_informazioni_meteo, salva_nota]
    
    # Esempio di richiesta che dovrebbe attivare un tool
    user_request = "Calcola l'area di un cerchio con raggio 5 metri"
    
    try:
        response = client.invoke(
            input=user_request,
            tools=tools,
            tool_choice="auto"  # "auto", "required", "none", o lista di nomi
        )
        
        print(f"   Risposta: {response.text}")
        
        # Controlla se sono stati chiamati dei tools
        for block in response.content:
            if hasattr(block, 'name') and hasattr(block, 'arguments'):
                print(f"   🔧 Tool chiamato: {block.name}")
                print(f"   📋 Argomenti: {block.arguments}")
                
                # Esegui il tool
                if block.name == "calcola_area_cerchio":
                    risultato = calcola_area_cerchio(**block.arguments)
                    print(f"   ✅ Risultato: {risultato}")
                    
    except Exception as e:
        print(f"   ⚠️ Simulazione di function calling:")
        print(f"   🔧 Tool chiamato: calcola_area_cerchio")
        print(f"   📋 Argomenti: {{'raggio': 5.0}}")
        print(f"   ✅ Risultato: {calcola_area_cerchio(5.0)}")
    
    # 3. Tool con configurazione avanzata
    print("\n3. Tool con configurazione avanzata:")
    
    def database_query(query: str, limit: int = 10) -> List[dict]:
        """Esegue una query sul database e restituisce i risultati."""
        # Simulazione
        return [{"id": i, "nome": f"Record {i}"} for i in range(limit)]
    
    # Tool con configurazione manuale
    db_tool = Tool(
        func=database_query,
        name="query_database",
        description="Esegue query SQL sul database aziendale",
        properties={
            "query": {
                "type": "string", 
                "description": "Query SQL da eseguire"
            },
            "limit": {
                "type": "integer", 
                "description": "Numero massimo di risultati",
                "minimum": 1,
                "maximum": 100,
                "default": 10
            }
        },
        required=["query"],
        strict=True  # Modalità strict per OpenAI
    )
    
    print(f"   ✅ Tool avanzato: {db_tool.name}")
    print(f"   📋 Schema: {db_tool.schema}")
    
    print("✅ Tools e Function Calling completati")


# ==============================================================================
# 6. RISPOSTE STRUTTURATE CON PYDANTIC
# ==============================================================================

def esempio_risposte_strutturate():
    """
    Le risposte strutturate permettono di ottenere output in formati specifici
    usando modelli Pydantic, garantendo validazione e type safety.
    """
    print("\n=== ESEMPIO: Risposte strutturate ===")
    
    # 1. Definizione di modelli Pydantic
    print("1. Definizione di modelli di output:")
    
    class PersonaInfo(BaseModel):
        """Informazioni su una persona"""
        nome: str
        eta: int
        professione: str
        citta: str
        hobby: List[str]
    
    class AnalisiSentiment(BaseModel):
        """Analisi del sentiment di un testo"""
        sentiment: str  # "positivo", "negativo", "neutro"
        confidenza: float  # 0.0 - 1.0
        emozioni_principali: List[str]
        spiegazione: str
    
    class RicettaCucina(BaseModel):
        """Ricetta di cucina strutturata"""
        nome: str
        difficolta: str  # "facile", "media", "difficile"
        tempo_preparazione_minuti: int
        porzioni: int
        ingredienti: List[str]
        istruzioni: List[str]
        calorie_per_porzione: Optional[int] = None
    
    print("   ✅ Modelli definiti:")
    print(f"   - PersonaInfo: {list(PersonaInfo.__fields__.keys())}")
    print(f"   - AnalisiSentiment: {list(AnalisiSentiment.__fields__.keys())}")
    print(f"   - RicettaCucina: {list(RicettaCucina.__fields__.keys())}")
    
    # 2. Utilizzo delle risposte strutturate
    print("\n2. Richiesta di risposte strutturate:")
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Fornisci sempre risposte accurate e complete."
    )
    
    # Esempio 1: Estrazione di informazioni su una persona
    try:
        response = client.structured_response(
            input="Marco Rossi, 35 anni, ingegnere software di Milano. Ama il calcio e la fotografia.",
            output_cls=PersonaInfo
        )
        
        persona = response.structured_data[0]  # Il primo (e unico) oggetto strutturato
        print(f"   ✅ Persona estratta:")
        print(f"   - Nome: {persona.nome}")
        print(f"   - Età: {persona.eta}")
        print(f"   - Professione: {persona.professione}")
        print(f"   - Città: {persona.citta}")
        print(f"   - Hobby: {persona.hobby}")
        
    except Exception as e:
        print(f"   ⚠️ Simulazione estrazione persona:")
        persona_sim = PersonaInfo(
            nome="Marco Rossi",
            eta=35,
            professione="ingegnere software",
            citta="Milano",
            hobby=["calcio", "fotografia"]
        )
        print(f"   - Nome: {persona_sim.nome}")
        print(f"   - Età: {persona_sim.eta}")
        print(f"   - Hobby: {persona_sim.hobby}")
    
    # Esempio 2: Analisi del sentiment
    print("\n   Analisi sentiment:")
    try:
        response = client.structured_response(
            input="Sono molto felice di questo nuovo lavoro! È fantastico!",
            output_cls=AnalisiSentiment
        )
        
        sentiment = response.structured_data[0]
        print(f"   ✅ Sentiment: {sentiment.sentiment}")
        print(f"   📊 Confidenza: {sentiment.confidenza}")
        print(f"   😊 Emozioni: {sentiment.emozioni_principali}")
        
    except Exception as e:
        print(f"   ⚠️ Simulazione analisi sentiment:")
        sentiment_sim = AnalisiSentiment(
            sentiment="positivo",
            confidenza=0.95,
            emozioni_principali=["gioia", "entusiasmo"],
            spiegazione="Il testo esprime chiaramente felicità e soddisfazione"
        )
        print(f"   ✅ Sentiment: {sentiment_sim.sentiment}")
        print(f"   📊 Confidenza: {sentiment_sim.confidenza}")
    
    # 3. Validazione automatica
    print("\n3. Validazione automatica:")
    
    # Esempio di validazione che fallisce
    try:
        # Questo dovrebbe fallire se l'età non è un numero
        persona_invalida = PersonaInfo(
            nome="Test",
            eta="non un numero",  # Errore di tipo
            professione="test",
            citta="test",
            hobby=[]
        )
    except Exception as e:
        print(f"   ✅ Validazione funziona: {type(e).__name__}")
    
    print("✅ Risposte strutturate completate")


# ==============================================================================
# 7. STREAMING E RISPOSTE IN TEMPO REALE
# ==============================================================================

def esempio_streaming():
    """
    Lo streaming permette di ricevere la risposta del modello token per token,
    migliorando l'esperienza utente per risposte lunghe.
    """
    print("\n=== ESEMPIO: Streaming ===")
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="Fornisci risposte dettagliate e ben strutturate."
    )
    
    # 1. Streaming sincrono
    print("1. Streaming sincrono:")
    
    try:
        print("   Domanda: 'Spiegami cos'è il machine learning'")
        print("   Risposta in streaming: ", end="", flush=True)
        
        full_response = ""
        for chunk in client.stream_invoke("Spiegami cos'è il machine learning in 100 parole"):
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_response += chunk.text
        
        print(f"\n   ✅ Risposta completa ricevuta ({len(full_response)} caratteri)")
        
    except Exception as e:
        print(f"\n   ⚠️ Simulazione streaming:")
        simulated_tokens = [
            "Il", " machine", " learning", " è", " una", " branca", 
            " dell'intelligenza", " artificiale", "..."
        ]
        for token in simulated_tokens:
            print(token, end="", flush=True)
            __import__('time').sleep(0.1)  # Simula il delay
        print("\n   ✅ Simulazione completata")
    
    # 2. Streaming asincrono
    print("\n2. Streaming asincrono (esempio di codice):")
    
    async_code = '''
async def stream_async_example():
    async for chunk in client.a_stream_invoke("Raccontami una storia"):
        if chunk.text:
            print(chunk.text, end="", flush=True)
        
        # Informazioni sul chunk
        if chunk.prompt_tokens_used:
            print(f"\\nToken usati: {chunk.prompt_tokens_used}")
    '''
    
    print("   Codice per streaming asincrono:")
    print(async_code)
    
    # 3. Gestione degli errori nello streaming
    print("\n3. Gestione errori nello streaming:")
    
    def safe_streaming(client, prompt):
        """Esempio di streaming con gestione errori"""
        try:
            response_parts = []
            for chunk in client.stream_invoke(prompt):
                if chunk.text:
                    response_parts.append(chunk.text)
                    print(chunk.text, end="", flush=True)
                
                # Controlla se c'è un errore
                if chunk.stop_reason == "error":
                    print(f"\n❌ Errore durante streaming: {chunk.stop_reason}")
                    break
            
            return "".join(response_parts)
            
        except Exception as e:
            print(f"\n❌ Errore nello streaming: {e}")
            return None
    
    print("   ✅ Funzione di streaming sicura definita")
    
    print("✅ Streaming completato")


# ==============================================================================
# 8. GESTIONE DI MEDIA E CONTENUTI MULTIMODALI
# ==============================================================================

def esempio_media():
    """
    Alcuni client supportano contenuti multimodali come immagini.
    Questo esempio mostra come gestire media nei messaggi.
    """
    print("\n=== ESEMPIO: Gestione Media ===")
    
    # 1. Creazione di blocchi media
    print("1. Creazione di blocchi media:")
    
    # Immagine da URL
    media_url = Media(
        media_type="image",
        source_type="url",
        source="https://example.com/image.jpg",
        detail="high"  # "low", "high", "auto"
    )
    
    media_block_url = MediaBlock(
        media=media_url,
        role=ROLE.USER
    )
    
    # Immagine da base64
    # (In un caso reale, caricheresti l'immagine e la convertiresti)
    fake_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    media_base64 = Media(
        media_type="image",
        source_type="base64",
        source=fake_base64,
        detail="high"
    )
    
    media_block_base64 = MediaBlock(
        media=media_base64,
        role=ROLE.USER
    )
    
    print("   ✅ Blocchi media creati:")
    print(f"   - Media da URL: {media_block_url.media.source_type}")
    print(f"   - Media da base64: {media_block_base64.media.source_type}")
    
    # 2. Utilizzo con client che supportano multimodalità
    print("\n2. Utilizzo con client multimodali:")
    
    # OpenAI e Google supportano immagini
    multimodal_client = ClientFactory.create(
        provider="openai",  # o "google"
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",  # Modello che supporta visione
        system_prompt="Puoi analizzare immagini e rispondere a domande su di esse."
    )
    
    # Combinazione di testo e immagine
    mixed_content = [
        TextBlock(content="Cosa vedi in questa immagine?"),
        media_block_url
    ]
    
    try:
        response = multimodal_client.invoke(input=mixed_content)
        print(f"   ✅ Analisi immagine: {response.text}")
    except Exception as e:
        print(f"   ⚠️ Simulazione analisi immagine:")
        print("   'Vedo un'immagine di esempio. Sembra essere un pixel trasparente.'")
    
    # 3. Caricamento di file locali
    print("\n3. Caricamento file locali (esempio):")
    
    def load_image_as_base64(file_path: str) -> str:
        """Carica un'immagine locale e la converte in base64"""
        import base64
        try:
            with open(file_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            return fake_base64  # Fallback per l'esempio
    
    # Esempio di utilizzo
    # image_path = "./my_image.jpg"
    # image_b64 = load_image_as_base64(image_path)
    # 
    # local_media = Media(
    #     media_type="image",
    #     source_type="base64", 
    #     source=image_b64
    # )
    
    print("   ✅ Funzione di caricamento immagini definita")
    
    print("✅ Gestione media completata")


# ==============================================================================
# 9. CONFIGURAZIONI AVANZATE E BEST PRACTICES
# ==============================================================================

def esempio_configurazioni_avanzate():
    """
    Configurazioni avanzate, gestione degli errori, e best practices
    per l'utilizzo in produzione della libreria datapizzai.
    """
    print("\n=== ESEMPIO: Configurazioni avanzate ===")
    
    # 1. Configurazione con variabili d'ambiente
    print("1. Configurazione con variabili d'ambiente:")
    
    def create_production_client():
        """Crea un client per produzione con configurazione da env"""
        import os
        from dotenv import load_dotenv
        
        # Carica variabili d'ambiente da file .env
        # load_dotenv()
        
        # Configurazione flessibile
        provider = os.getenv("LLM_PROVIDER", "openai")
        api_key = os.getenv("LLM_API_KEY")
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        
        if not api_key:
            raise ValueError("LLM_API_KEY non trovata nelle variabili d'ambiente")
        
        # Cache per produzione
        cache = None
        if os.getenv("REDIS_URL"):
            cache = RedisCache(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                expiration_time=int(os.getenv("CACHE_TTL", "3600"))
            )
        
        return ClientFactory.create(
            provider=provider,
            api_key=api_key,
            model=model,
            temperature=temperature,
            cache=cache
        )
    
    print("   ✅ Funzione di configurazione produzione definita")
    
    # 2. Gestione degli errori robusta
    print("\n2. Gestione errori robusta:")
    
    class LLMManager:
        """Manager per gestire client LLM con retry e fallback"""
        
        def __init__(self, primary_client, fallback_client=None, max_retries=3):
            self.primary_client = primary_client
            self.fallback_client = fallback_client
            self.max_retries = max_retries
        
        def invoke_with_retry(self, prompt, **kwargs):
            """Invoca con retry automatico e fallback"""
            import time
            import random
            
            for attempt in range(self.max_retries):
                try:
                    return self.primary_client.invoke(prompt, **kwargs)
                
                except Exception as e:
                    print(f"   ⚠️ Tentativo {attempt + 1} fallito: {e}")
                    
                    if attempt < self.max_retries - 1:
                        # Backoff esponenziale con jitter
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        print(f"   ⏳ Attendo {delay:.1f}s prima del retry...")
                        time.sleep(delay)
                    else:
                        # Ultimo tentativo fallito, prova il fallback
                        if self.fallback_client:
                            print("   🔄 Provo con client di fallback...")
                            try:
                                return self.fallback_client.invoke(prompt, **kwargs)
                            except Exception as fallback_error:
                                print(f"   ❌ Anche il fallback è fallito: {fallback_error}")
                        
                        raise e
    
    # Esempio di utilizzo
    try:
        primary = ClientFactory.create("openai", os.getenv("OPENAI_API_KEY"), "gpt-4o")
        fallback = ClientFactory.create("anthropic", os.getenv("ANTHROPIC_API_KEY"), "claude-3-5-sonnet-latest")
        
        manager = LLMManager(primary, fallback)
        print("   ✅ LLM Manager configurato con fallback")
    except:
        print("   ✅ LLM Manager (classe) definito")
    
    # 3. Monitoring e logging
    print("\n3. Monitoring e logging:")
    
    def setup_logging():
        """Configura logging per datapizzai"""
        import logging
        
        # Logger per datapizzai
        logger = logging.getLogger("datapizzai")
        logger.setLevel(logging.INFO)
        
        # Handler per file
        file_handler = logging.FileHandler("datapizzai.log")
        file_handler.setLevel(logging.INFO)
        
        # Handler per console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Aggiungi handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    # logger = setup_logging()
    print("   ✅ Configurazione logging definita")
    
    # 4. Metriche e costi
    print("\n4. Tracking metriche e costi:")
    
    class MetricsTracker:
        """Traccia metriche di utilizzo e costi"""
        
        def __init__(self):
            self.total_requests = 0
            self.total_prompt_tokens = 0
            self.total_completion_tokens = 0
            self.total_cached_tokens = 0
            self.requests_by_model = {}
        
        def track_request(self, response, model_name):
            """Traccia una richiesta"""
            self.total_requests += 1
            self.total_prompt_tokens += response.prompt_tokens_used or 0
            self.total_completion_tokens += response.completion_tokens_used or 0
            self.total_cached_tokens += response.cached_tokens_used or 0
            
            if model_name not in self.requests_by_model:
                self.requests_by_model[model_name] = 0
            self.requests_by_model[model_name] += 1
        
        def get_stats(self):
            """Ottieni statistiche di utilizzo"""
            total_tokens = self.total_prompt_tokens + self.total_completion_tokens
            return {
                "total_requests": self.total_requests,
                "total_tokens": total_tokens,
                "prompt_tokens": self.total_prompt_tokens,
                "completion_tokens": self.total_completion_tokens,
                "cached_tokens": self.total_cached_tokens,
                "cache_hit_rate": self.total_cached_tokens / max(total_tokens, 1),
                "requests_by_model": self.requests_by_model
            }
        
        def estimate_cost(self, model_pricing=None):
            """Stima i costi (richiede pricing per modello)"""
            if not model_pricing:
                model_pricing = {
                    "gpt-4o": {"prompt": 0.005, "completion": 0.015},  # $/1K tokens
                    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006}
                }
            
            total_cost = 0
            for model, requests in self.requests_by_model.items():
                if model in model_pricing:
                    pricing = model_pricing[model]
                    # Stima approssimativa
                    prompt_cost = (self.total_prompt_tokens / 1000) * pricing["prompt"]
                    completion_cost = (self.total_completion_tokens / 1000) * pricing["completion"]
                    total_cost += prompt_cost + completion_cost
            
            return total_cost
    
    metrics = MetricsTracker()
    print("   ✅ Metrics Tracker configurato")
    
    # Esempio di utilizzo del tracker
    print("\n   Esempio di tracking:")
    # Simula una risposta
    class MockResponse:
        def __init__(self):
            self.prompt_tokens_used = 100
            self.completion_tokens_used = 50
            self.cached_tokens_used = 0
    
    mock_response = MockResponse()
    metrics.track_request(mock_response, "gpt-4o-mini")
    
    stats = metrics.get_stats()
    print(f"   📊 Statistiche: {stats['total_requests']} richieste, {stats['total_tokens']} token")
    print(f"   💰 Costo stimato: ${metrics.estimate_cost():.4f}")
    
    print("✅ Configurazioni avanzate completate")


# ==============================================================================
# 10. ESEMPIO COMPLETO: ASSISTENTE INTELLIGENTE
# ==============================================================================

def esempio_assistente_completo():
    """
    Esempio completo che combina tutte le funzionalità per creare
    un assistente intelligente con memoria, tools, cache e gestione errori.
    """
    print("\n=== ESEMPIO: Assistente intelligente completo ===")
    
    # 1. Setup completo
    print("1. Setup assistente:")
    
    # Cache
    cache = MemoryCache()
    
    # Client con configurazione ottimale
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""Sei un assistente AI intelligente e utile. 
        Puoi usare strumenti per aiutare l'utente con calcoli, ricerche e altre attività.
        Mantieni sempre il contesto della conversazione e fornisci risposte precise.""",
        temperature=0.7,
        cache=cache
    )
    
    # Memoria per la conversazione
    memory = Memory()
    
    # Tools disponibili
    @Tool
    def calcola(espressione: str) -> str:
        """Calcola espressioni matematiche."""
        try:
            # ATTENZIONE: eval è pericoloso in produzione!
            # Usa una libreria come simpleeval per sicurezza
            result = eval(espressione)
            return f"Il risultato di '{espressione}' è: {result}"
        except Exception as e:
            return f"Errore nel calcolo: {e}"
    
    @Tool
    def cerca_definizione(termine: str) -> str:
        """Cerca la definizione di un termine."""
        # Simulazione di ricerca
        definizioni = {
            "python": "Linguaggio di programmazione ad alto livello",
            "ai": "Intelligenza Artificiale - capacità delle macchine di simulare l'intelligenza umana",
            "api": "Application Programming Interface - insieme di protocolli per costruire software"
        }
        return definizioni.get(termine.lower(), f"Definizione di '{termine}' non trovata nel database locale.")
    
    @Tool
    def salva_promemoria(testo: str, categoria: str = "generale") -> str:
        """Salva un promemoria per l'utente."""
        # Simulazione di salvataggio
        return f"✅ Promemoria salvato nella categoria '{categoria}': {testo}"
    
    tools = [calcola, cerca_definizione, salva_promemoria]
    
    print("   ✅ Assistente configurato con:")
    print(f"   - Client: {client.__class__.__name__}")
    print(f"   - Cache: {cache.__class__.__name__}")
    print(f"   - Tools: {len(tools)} disponibili")
    print(f"   - Memoria: Inizializzata")
    
    # 2. Simulazione di conversazione
    print("\n2. Simulazione conversazione:")
    
    def chat_turn(user_input: str, show_internal=True):
        """Simula un turno di conversazione"""
        print(f"\n👤 Utente: {user_input}")
        
        # Aggiungi input utente alla memoria
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            # Invoca l'assistente
            response = client.invoke(
                input="",  # Input vuoto perché usiamo la memoria
                memory=memory,
                tools=tools,
                tool_choice="auto"
            )
            
            # Mostra informazioni interne se richiesto
            if show_internal:
                print(f"   🔍 Token usati: {response.prompt_tokens_used + response.completion_tokens_used}")
                print(f"   🔍 Stop reason: {response.stop_reason}")
                
                # Controlla se sono stati usati tools
                tool_calls = [block for block in response.content if hasattr(block, 'name')]
                if tool_calls:
                    print(f"   🔧 Tools usati: {[t.name for t in tool_calls]}")
            
            # Aggiungi risposta alla memoria
            memory.add_turn(response.content, ROLE.ASSISTANT)
            
            print(f"🤖 Assistente: {response.text}")
            return response
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            # Simulazione per demo
            simulated_response = f"Mi dispiace, non posso elaborare la richiesta al momento. (Errore simulato per demo)"
            memory.add_turn([TextBlock(content=simulated_response)], ROLE.ASSISTANT)
            print(f"🤖 Assistente: {simulated_response}")
            return None
    
    # Conversazione di esempio
    chat_turn("Ciao! Mi chiamo Mirko e sono un GenAI Engineer.")
    chat_turn("Puoi calcolare 15 * 8 + 32?")
    chat_turn("Che cos'è un'API?")
    chat_turn("Ricordami di rivedere il codice domani")
    chat_turn("Qual è il mio nome?")  # Test della memoria
    
    # 3. Statistiche finali
    print(f"\n3. Statistiche conversazione:")
    print(f"   📚 Turni di conversazione: {len(memory.memory)}")
    print(f"   💬 Blocchi totali: {len(list(memory.iter_blocks()))}")
    
    # Analizza i tipi di blocchi
    block_types = {}
    for block in memory.iter_blocks():
        block_type = type(block).__name__
        block_types[block_type] = block_types.get(block_type, 0) + 1
    
    print(f"   📊 Tipi di blocchi: {block_types}")
    
    print("✅ Esempio assistente completo terminato")


# ==============================================================================
# FUNZIONE PRINCIPALE
# ==============================================================================

def main():
    """
    Funzione principale che esegue tutti gli esempi.
    Commenta/decommenta le sezioni che vuoi testare.
    """
    print("🚀 GUIDA COMPLETA AL CLIENT DI DATAPIZZAI")
    print("=" * 50)
    
    # Esegui tutti gli esempi
    # NOTA: Molti esempi falliranno senza chiavi API reali, ma mostrano la struttura corretta
    
    #esempio_client_factory()
    #esempio_client_diretti()
    #esempio_utilizzo_base()
    #esempio_memoria()
    esempio_cache()
    #esempio_tools()
    #esempio_risposte_strutturate()
    #esempio_streaming()
    #esempio_media()
    #esempio_configurazioni_avanzate()
    #esempio_assistente_completo()
    
    print("\n" + "=" * 50)
    print("✅ GUIDA COMPLETATA!")
    print("\n💡 PROSSIMI PASSI:")
    '''
    print("1. Crea un file .env con le tue chiavi API (vedi esempio sotto)")
    print("2. Installa le dipendenze aggiuntive se necessario (redis, python-dotenv)")
    print("3. Testa gli esempi uno alla volta")
    print("4. Personalizza i parametri per le tue esigenze")
    
    print("\n📋 ESEMPIO FILE .env:")
    print("# Crea un file chiamato .env nella directory PizzAI/ con:")
    print("OPENAI_API_KEY=sk-your-openai-api-key-here")
    print("ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here")
    print("GOOGLE_API_KEY=your-google-api-key-here")
    print("# MISTRAL_API_KEY=your-mistral-api-key-here  # opzionale")
    
    print("\n📚 DOCUMENTAZIONE:")
    print("- Consulta la documentazione ufficiale di datapizzai")
    print("- Controlla gli esempi nella cartella snippets/")
    print("- Usa il logging per debug in caso di problemi")
    '''


if __name__ == "__main__":
    main()
