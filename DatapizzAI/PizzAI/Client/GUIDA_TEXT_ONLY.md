# Guida completa: DatapizzAI text-only

Una guida tecnica per utilizzare le modalità one-shot e conversational del framework DatapizzAI per prompt testuali.

## Indice

1. [Setup e configurazione](#1-setup-e-configurazione)
2. [Modalità one-shot](#2-modalità-one-shot)
3. [Modalità conversational](#3-modalità-conversational)
4. [Gestione della memoria](#4-gestione-della-memoria)
5. [Confronto tra provider](#5-confronto-tra-provider)
6. [Best practices](#6-best-practices)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Setup e configurazione

### Prerequisiti

```bash
# Attiva l'ambiente virtuale
source .venv/bin/activate
```

### Configurazione API keys

Crea un file `.env` nella directory `PizzAI/`:

```bash
# File .env - Almeno una chiave API è richiesta
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here  
GOOGLE_API_KEY=your-google-api-key-here
MISTRAL_API_KEY=your-mistral-api-key-here
```

### Import necessari

```python
import os
import time
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv('../.env')

# Import DatapizzAI
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE
from datapizzai.cache import MemoryCache
```

### Creazione client con supporto cache

```python
def create_client(provider_name: str = "openai", use_cache: bool = False):
    """
    Crea un client DatapizzAI configurato
    
    Args:
        provider_name: "openai", "anthropic", "google", "mistral"
        use_cache: Abilita cache in memoria (solo OpenAI/Azure)
    
    Returns:
        Client configurato o None se errore
    """
    
    # Configurazione provider
    api_keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", 
        "google": "GOOGLE_API_KEY",
        "mistral": "MISTRAL_API_KEY"
    }
    
    models = {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-latest",
        "google": "gemini-2.5-flash", 
        "mistral": "mistral-large-latest"
    }
    
    # Solo OpenAI e Azure supportano cache nel costruttore
    cache_supported = {"openai", "azure_openai"}
    
    # Verifica API key
    api_key = os.getenv(api_keys.get(provider_name))
    if not api_key:
        print(f"⚠️ Chiave API non trovata per {provider_name}")
        return None
    
    # Configura cache se supportata
    extra_kwargs = {}
    if use_cache and provider_name.lower() in cache_supported:
        extra_kwargs["cache"] = MemoryCache()
    
    try:
        client = ClientFactory.create(
            provider=provider_name,
            api_key=api_key,
            model=models[provider_name],
            system_prompt="Sei un assistente AI utile. Rispondi in italiano in modo chiaro.",
            temperature=0.7,
            **extra_kwargs
        )
        
        print(f"✅ Client {provider_name} creato")
        if "cache" in extra_kwargs:
            print("   📦 Cache abilitata")
        elif use_cache:
            print(f"   ⚠️ Cache non supportata per {provider_name}")
        
        return client
        
    except Exception as e:
        print(f"❌ Errore creazione client: {e}")
        return None

# Esempio d'uso
client = create_client("openai", use_cache=True)
```

---

## 2. Modalità one-shot

### Concetto base

La modalità one-shot esegue una singola query senza mantenere contesto tra le chiamate. Ogni invocazione è indipendente.

**Quando usare one-shot:**
- Domande isolate senza contesto precedente
- Analisi di testi singoli
- Traduzioni
- Calcoli matematici
- Generazione di contenuti indipendenti

### Utilizzo base con stringa

```python
def simple_one_shot_example():
    """Esempio base one-shot con stringa semplice"""
    
    client = create_client("openai")
    if not client:
        return
    
    # Query semplice
    prompt = "Spiega il concetto di machine learning in 2 frasi"
    
    try:
        # Invocazione diretta con stringa
        response = client.invoke(prompt)
        
        print(f"Domanda: {prompt}")
        print(f"Risposta: {response.text}")
        print(f"Token usati: {response.prompt_tokens_used + response.completion_tokens_used}")
        
    except Exception as e:
        print(f"Errore: {e}")

# Esecuzione
simple_one_shot_example()
```

### Utilizzo avanzato con TextBlock

```python
def advanced_one_shot_example():
    """Esempio avanzato con TextBlock e strutturazione"""
    
    client = create_client("openai")
    if not client:
        return
    
    # Prompt strutturato con TextBlock
    structured_prompt = """
    Agisci come un esperto di cybersecurity.
    
    Domanda: Quali sono le 3 minacce principali per un'azienda nel 2024?
    
    Formato risposta:
    1. Minaccia 1: [nome] - [breve descrizione]
    2. Minaccia 2: [nome] - [breve descrizione] 
    3. Minaccia 3: [nome] - [breve descrizione]
    
    Includi una raccomandazione di sicurezza per ciascuna.
    """
    
    # Crea TextBlock per controllo maggiore
    text_block = TextBlock(content=structured_prompt)
    
    try:
        start_time = time.time()
        response = client.invoke(input=[text_block])
        end_time = time.time()
        
        print("🔐 Consulenza Cybersecurity:")
        print(response.text)
        print(f"\n📊 Statistiche:")
        print(f"   Tempo: {end_time - start_time:.2f}s")
        print(f"   Token prompt: {response.prompt_tokens_used}")
        print(f"   Token risposta: {response.completion_tokens_used}")
        print(f"   Stop reason: {response.stop_reason}")
        
    except Exception as e:
        print(f"Errore: {e}")

advanced_one_shot_example()
```

### Esempi pratici one-shot

```python
def practical_one_shot_examples():
    """Esempi pratici per diversi casi d'uso"""
    
    client = create_client("openai")
    if not client:
        return
    
    examples = [
        {
            "name": "Analisi sentiment",
            "prompt": "Analizza il sentiment di questo testo: 'La presentazione è andata malissimo, ma almeno ho imparato qualcosa di nuovo.'",
            "category": "NLP"
        },
        {
            "name": "Traduzione tecnica",
            "prompt": "Traduci in inglese tecnico: 'L'algoritmo di machine learning ha raggiunto un'accuratezza del 94% sul dataset di test.'",
            "category": "Traduzione"
        },
        {
            "name": "Problem solving",
            "prompt": "Un server gestisce 1000 richieste al secondo. Se ogni richiesta richiede 50ms di elaborazione, quanti thread minimi servono per evitare accumulo?",
            "category": "Calcolo"
        },
        {
            "name": "Code generation",
            "prompt": "Scrivi una funzione Python che calcola il fattoriale di un numero usando la ricorsione. Includi docstring e gestione errori.",
            "category": "Programmazione"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n--- Esempio {i}: {example['name']} ({example['category']}) ---")
        print(f"Prompt: {example['prompt'][:80]}...")
        
        try:
            response = client.invoke(example['prompt'])
            print(f"Risposta: {response.text[:200]}...")
            print(f"Token: {response.prompt_tokens_used + response.completion_tokens_used}")
            
        except Exception as e:
            print(f"Errore: {e}")

practical_one_shot_examples()
```

---

## 3. Modalità conversational

### Concetto base

La modalità conversational mantiene la memoria della conversazione attraverso l'oggetto `Memory`, permettendo riferimenti al contesto precedente.

**Quando usare conversational:**
- Sessioni di tutoring o consulenza
- Analisi iterative di documenti
- Sviluppo progressivo di idee
- Supporto tecnico multi-step
- Brainstorming collaborativo

### Setup base conversational

```python
def basic_conversational_example():
    """Esempio base di conversazione con memoria"""
    
    client = create_client("openai")
    if not client:
        return
    
    # Inizializza la memoria
    memory = Memory()
    
    def chat_turn(user_input: str, description: str = ""):
        """Helper per gestire un turno di conversazione"""
        
        if description:
            print(f"📋 {description}")
        print(f"👤 Utente: {user_input}")
        
        # Aggiungi messaggio utente alla memoria
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            # Invoca con memoria (input vuoto perché contesto è in memoria)
            response = client.invoke("", memory=memory)
            
            # Aggiungi risposta alla memoria
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Assistente: {response.text}")
            print(f"   Token: {response.prompt_tokens_used + response.completion_tokens_used}")
            
            return response
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            # Fallback per continuare la conversazione
            memory.add_turn([TextBlock(content="Errore tecnico.")], ROLE.ASSISTANT)
            return None
    
    # Simulazione conversazione
    print("🎭 Simulazione conversazione con memoria:\n")
    
    chat_turn(
        "Ciao! Sono Marco, sviluppatore Python senior con 8 anni di esperienza.",
        "Presentazione iniziale"
    )
    
    chat_turn(
        "Quali sono le migliori pratiche per ottimizzare le performance in Python?",
        "Richiesta consulenza tecnica"
    )
    
    chat_turn(
        "E per il mio caso specifico, considerando che lavoro principalmente con Django?",
        "Follow-up che richiede contesto (nome, esperienza, framework)"
    )
    
    chat_turn(
        "Perfetto! Puoi ricordarmi il mio nome e la mia esperienza?",
        "Test esplicito della memoria"
    )
    
    # Statistiche finali
    print(f"\n📊 Conversazione completata:")
    print(f"   Turni: {len(memory.memory)}")
    print(f"   Blocchi totali: {len(list(memory.iter_blocks()))}")

basic_conversational_example()
```

### Gestione conversazioni avanzate

```python
def advanced_conversational_scenarios():
    """Scenari conversational complessi"""
    
    client = create_client("openai", use_cache=True)
    if not client:
        return
    
    memory = Memory()
    
    def enhanced_chat_turn(user_input: str, context_info: str = ""):
        """Chat turn con informazioni aggiuntive"""
        
        if context_info:
            print(f"📋 Contesto: {context_info}")
        print(f"👤 Utente: {user_input}")
        
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            response = client.invoke("", memory=memory)
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Assistente: {response.text}")
            
            # Mostra cache hits se disponibili
            cache_hits = getattr(response, 'cached_tokens_used', 0)
            total_tokens = response.prompt_tokens_used + response.completion_tokens_used
            print(f"   📊 Token: {total_tokens} | Cache: {cache_hits}")
            
            return response
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            memory.add_turn([TextBlock(content="Errore temporaneo.")], ROLE.ASSISTANT)
    
    print("🔬 Scenario avanzato: Consulenza architetturale progressiva\n")
    
    # Step 1: Definizione problema
    enhanced_chat_turn(
        "Devo progettare l'architettura per un sistema di e-commerce che gestirà 100k utenti simultanei",
        "Definizione requisiti iniziali"
    )
    
    # Step 2: Approfondimento requisiti
    enhanced_chat_turn(
        "Il budget è di 50k€, il team ha 6 sviluppatori e dobbiamo lanciare in 6 mesi",
        "Aggiunta vincoli di budget e timing"
    )
    
    # Step 3: Scelta tecnologica
    enhanced_chat_turn(
        "Il team conosce principalmente Java Spring e React. Preferisci architettura monolitica o microservizi?",
        "Considerazione competenze team"
    )
    
    # Step 4: Cambio di focus mantenendo contesto
    enhanced_chat_turn(
        "Ora parliamo di sicurezza. Che misure consigli per il sistema che abbiamo discusso?",
        "Cambio argomento mantenendo contesto architetturale"
    )
    
    # Step 5: Ritorno al contesto precedente
    enhanced_chat_turn(
        "Tornando all'architettura, mi serve un piano di deployment. Ricordi i nostri vincoli?",
        "Test memoria a lungo termine con vincoli multipli"
    )
    
    # Step 6: Riassunto contestuale
    enhanced_chat_turn(
        "Perfetto! Ora riassumi tutto: problema, vincoli, architettura scelta e prossimi step",
        "Richiesta di sintesi contestuale completa"
    )

advanced_conversational_scenarios()
```

### Conversazione multi-topic con gestione contesto

```python
def multi_topic_conversation():
    """Gestione conversazioni con cambio di argomenti"""
    
    client = create_client("openai")
    if not client:
        return
    
    memory = Memory()
    
    def topic_aware_chat(user_input: str, topic: str, context_level: str = "full"):
        """
        Chat con awareness del topic
        
        Args:
            context_level: "full" usa tutta la memoria, "recent" usa solo ultimi turni
        """
        
        working_memory = memory
        
        # Se richiesta memoria ridotta, crea memoria parziale
        if context_level == "recent" and len(memory.memory) > 4:
            working_memory = Memory()
            recent_turns = memory.memory[-4:]  # Ultimi 4 turni
            working_memory.memory.extend(recent_turns)
            print("🧠 Usando memoria ridotta (ultimi 4 turni)")
        
        print(f"📂 Topic: {topic}")
        print(f"👤 Utente: {user_input}")
        
        # Aggiungi alla memoria principale (non a quella working)
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            response = client.invoke("", memory=working_memory)
            
            # Aggiungi risposta alla memoria principale
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Assistente: {response.text}")
            
            return response
            
        except Exception as e:
            print(f"❌ Errore: {e}")
    
    print("🎭 Conversazione multi-topic:\n")
    
    # Topic 1: Programmazione
    topic_aware_chat(
        "Ciao, sono Alice, lavoro come Data Scientist e uso principalmente Python e SQL",
        "Presentazione professionale"
    )
    
    topic_aware_chat(
        "Quali librerie Python consigli per l'analisi di time series?",
        "Consulenza tecnica - Data Science"
    )
    
    # Topic 2: Viaggi (cambio completo di argomento)
    topic_aware_chat(
        "Cambiamo argomento. Sto pianificando un viaggio in Giappone. Consigli per Tokyo?",
        "Viaggi - pianificazione"
    )
    
    topic_aware_chat(
        "Quali sono i piatti tipici che devo assolutamente provare?",
        "Viaggi - gastronomia"
    )
    
    # Topic 3: Ritorno al contesto lavorativo
    topic_aware_chat(
        "Ora torniamo al lavoro. Ricordi la mia professione e la domanda sulle time series?",
        "Ritorno contesto professionale - test memoria",
        context_level="full"
    )
    
    # Topic 4: Mix dei contesti
    topic_aware_chat(
        "Durante il viaggio in Giappone, potrei lavorare in remoto. Come Alice, che consigli per produttività?",
        "Mix contesti: viaggio + lavoro + personale",
        context_level="full"
    )

multi_topic_conversation()
```

---

## 4. Gestione della memoria

### Operazioni base sulla memoria

```python
def memory_operations_guide():
    """Guida completa alle operazioni sulla memoria"""
    
    client = create_client("openai")
    if not client:
        return
    
    print("🧠 Operazioni avanzate sulla memoria\n")
    
    # 1. Creazione e popolamento memoria
    memory = Memory()
    
    # Aggiungi messaggi di esempio
    sample_conversation = [
        ("Sono Luigi, ingegnere meccanico con 15 anni di esperienza", ROLE.USER),
        ("Piacere Luigi! Come posso aiutarti oggi?", ROLE.ASSISTANT),
        ("Sto progettando un sistema di ventilazione per un edificio commerciale", ROLE.USER),
        ("Interessante! Che tipo di edificio e che superficie?", ROLE.ASSISTANT),
        ("Uffici di 2000mq su 4 piani, circa 200 persone", ROLE.USER),
        ("Per 200 persone servono almeno 3000 m³/h di aria fresca", ROLE.ASSISTANT)
    ]
    
    for content, role in sample_conversation:
        memory.add_turn([TextBlock(content=content)], role)
    
    print(f"📚 Memoria creata: {len(memory.memory)} turni")
    
    # 2. Analisi contenuto memoria
    print(f"🔍 Analisi memoria:")
    for i, turn in enumerate(memory.memory):
        role_icon = "👤" if turn.role == ROLE.USER else "🤖"
        content = turn.blocks[0].content[:60] + "..." if len(turn.blocks[0].content) > 60 else turn.blocks[0].content
        print(f"   {role_icon} Turno {i+1}: {content}")
    
    # 3. Copia e backup
    backup_memory = memory.copy()
    print(f"\n💾 Backup creato: {len(backup_memory.memory)} turni")
    
    # 4. Test continuità
    print(f"\n🧪 Test continuità memoria:")
    try:
        response = client.invoke(
            "Qual è il nome dell'utente e su cosa sta lavorando?",
            memory=memory
        )
        print(f"   Risposta: {response.text}")
    except Exception as e:
        print(f"   Errore: {e}")
    
    # 5. Gestione memoria limitata (sliding window)
    print(f"\n🪟 Simulazione sliding window:")
    print(f"   Prima: {len(memory.memory)} turni")
    
    # Mantieni solo ultimi 4 turni
    if len(memory.memory) > 4:
        recent_turns = memory.memory[-4:]
        limited_memory = Memory()
        limited_memory.memory.extend(recent_turns)
        print(f"   Dopo sliding window: {len(limited_memory.memory)} turni")
        
        # Test memoria limitata
        try:
            response = client.invoke(
                "Di cosa stavamo parlando?",
                memory=limited_memory
            )
            print(f"   Test memoria limitata: {response.text}")
        except Exception as e:
            print(f"   Errore: {e}")
    
    # 6. Iterazione blocchi
    print(f"\n🔄 Iterazione attraverso tutti i blocchi:")
    for i, block in enumerate(memory.iter_blocks()):
        print(f"   Blocco {i+1}: {block.content[:40]}...")

memory_operations_guide()
```

### Strategie di gestione memoria

```python
def memory_management_strategies():
    """Diverse strategie per gestire la memoria in conversazioni lunghe"""
    
    client = create_client("openai")
    if not client:
        return
    
    print("📋 Strategie gestione memoria per conversazioni lunghe\n")
    
    # Strategia 1: Memoria completa (fino a limiti token)
    def full_memory_strategy(memory: Memory, user_input: str):
        """Usa tutta la memoria disponibile"""
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        response = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        return response
    
    # Strategia 2: Sliding window
    def sliding_window_strategy(memory: Memory, user_input: str, window_size: int = 6):
        """Mantiene solo gli ultimi N turni"""
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        # Crea memoria limitata
        if len(memory.memory) > window_size:
            windowed_memory = Memory()
            windowed_memory.memory.extend(memory.memory[-window_size:])
        else:
            windowed_memory = memory
        
        response = client.invoke("", memory=windowed_memory)
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        return response
    
    # Strategia 3: Memoria con riassunto
    def summary_strategy(memory: Memory, user_input: str, summary_threshold: int = 10):
        """Riassume la conversazione quando diventa troppo lunga"""
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        if len(memory.memory) > summary_threshold:
            # Genera riassunto della conversazione precedente
            try:
                summary_response = client.invoke(
                    "Riassumi brevemente questa conversazione mantenendo informazioni chiave",
                    memory=memory
                )
                
                # Crea nuova memoria con il riassunto
                summarized_memory = Memory()
                summarized_memory.add_turn([TextBlock(content=f"Riassunto conversazione precedente: {summary_response.text}")], ROLE.ASSISTANT)
                
                # Aggiungi ultimi 2 turni per continuità
                recent_turns = memory.memory[-2:]
                summarized_memory.memory.extend(recent_turns)
                
                response = client.invoke("", memory=summarized_memory)
                print("📝 Conversazione riassunta per ottimizzare token")
                
            except Exception:
                # Fallback a sliding window
                response = sliding_window_strategy(memory, "", 6)
        else:
            response = client.invoke("", memory=memory)
        
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        return response
    
    # Test delle strategie
    test_memory = Memory()
    
    # Popola con conversazione di esempio
    conversation_turns = [
        "Sono Maria, product manager in una startup fintech",
        "Stiamo sviluppando un'app per gestione del budget personale",
        "Il target sono giovani professionisti 25-35 anni",
        "Abbiamo raccolto 500k€ di seed funding",
        "Il team è di 12 persone tra sviluppatori e designer",
        "Vogliamo lanciare il MVP in 4 mesi",
        "La concorrenza principale è YNAB e Mint",
        "Puntiamo su UX semplificata e gamification",
        "Hai consigli per la strategia di go-to-market?"
    ]
    
    print("🧪 Test strategie con conversazione lunga:")
    
    # Simula una conversazione usando sliding window
    for i, turn in enumerate(conversation_turns):
        print(f"\nTurno {i+1}: {turn[:50]}...")
        
        try:
            # Usa sliding window con finestra di 4 turni
            response = sliding_window_strategy(test_memory, turn, window_size=4)
            print(f"Risposta: {response.text[:100]}...")
            print(f"Token: {response.prompt_tokens_used + response.completion_tokens_used}")
            
        except Exception as e:
            print(f"Errore: {e}")
    
    print(f"\n📊 Memoria finale: {len(test_memory.memory)} turni totali")

memory_management_strategies()
```

---

## 5. Confronto tra provider

### Analisi comparativa performance

```python
def provider_comparison_analysis():
    """Confronto sistematico tra provider su diversi tipi di task"""
    
    providers = ["openai", "anthropic", "google"]
    
    # Test cases diversificati
    test_cases = [
        {
            "name": "Analisi tecnica",
            "prompt": "Spiega la differenza tra REST e GraphQL in contesto enterprise",
            "category": "Technical"
        },
        {
            "name": "Creatività",
            "prompt": "Scrivi uno slogan accattivante per un'app di fitness per millennials",
            "category": "Creative"
        },
        {
            "name": "Reasoning logico",
            "prompt": "Se tutti i gatti sono mammiferi e alcuni mammiferi volano, possono volare alcuni gatti?",
            "category": "Logic"
        },
        {
            "name": "Calcolo numerico",
            "prompt": "Calcola ROI di un investimento di 10k€ che genera 1.2k€/anno per 5 anni con inflazione 2%",
            "category": "Math"
        }
    ]
    
    print("⚖️ Confronto sistematico provider\n")
    
    results = []
    
    for test in test_cases:
        print(f"--- {test['name']} ({test['category']}) ---")
        print(f"Prompt: {test['prompt']}")
        
        test_results = {"test": test["name"], "category": test["category"]}
        
        for provider in providers:
            print(f"\n🔧 Provider: {provider.upper()}")
            
            client = create_client(provider)
            if not client:
                print("   ❌ Client non disponibile")
                test_results[provider] = {"status": "unavailable"}
                continue
            
            try:
                start_time = time.time()
                response = client.invoke(test["prompt"])
                end_time = time.time()
                
                # Statistiche
                response_time = end_time - start_time
                total_tokens = response.prompt_tokens_used + response.completion_tokens_used
                response_length = len(response.text)
                
                print(f"   ✅ Risposta: {response.text[:80]}...")
                print(f"   📊 Tempo: {response_time:.2f}s")
                print(f"   📊 Token: {total_tokens}")
                print(f"   📊 Lunghezza: {response_length} caratteri")
                
                test_results[provider] = {
                    "status": "success",
                    "time": response_time,
                    "tokens": total_tokens,
                    "length": response_length,
                    "response": response.text[:200]
                }
                
            except Exception as e:
                print(f"   ❌ Errore: {e}")
                test_results[provider] = {"status": "error", "error": str(e)}
        
        results.append(test_results)
        print("\n" + "-"*60)
    
    # Analisi aggregata
    print("\n📊 ANALISI AGGREGATA RISULTATI")
    
    # Performance per categoria
    categories = {}
    for result in results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = {"tests": 0, "providers": {}}
        
        categories[cat]["tests"] += 1
        for provider in providers:
            if provider not in categories[cat]["providers"]:
                categories[cat]["providers"][provider] = {"success": 0, "total_time": 0, "total_tokens": 0}
            
            if provider in result and result[provider]["status"] == "success":
                categories[cat]["providers"][provider]["success"] += 1
                categories[cat]["providers"][provider]["total_time"] += result[provider]["time"]
                categories[cat]["providers"][provider]["total_tokens"] += result[provider]["tokens"]
    
    # Report per categoria
    for category, data in categories.items():
        print(f"\n🎯 Categoria: {category}")
        for provider in providers:
            if provider in data["providers"]:
                provider_data = data["providers"][provider]
                success_rate = (provider_data["success"] / data["tests"]) * 100
                avg_time = provider_data["total_time"] / max(provider_data["success"], 1)
                avg_tokens = provider_data["total_tokens"] / max(provider_data["success"], 1)
                
                print(f"   {provider.upper()}:")
                print(f"     Success rate: {success_rate:.1f}%")
                print(f"     Tempo medio: {avg_time:.2f}s")
                print(f"     Token medi: {avg_tokens:.0f}")

provider_comparison_analysis()
```

### Confronto conversational vs one-shot

```python
def conversational_vs_oneshot_comparison():
    """Confronta efficacia modalità conversational vs one-shot"""
    
    client = create_client("openai")
    if not client:
        return
    
    print("🔄 Confronto: Conversational vs One-shot\n")
    
    # Scenario di test: consulenza progressiva
    scenario = {
        "context": "Consulenza per startup tech",
        "queries": [
            "Ho un'idea per un'app di delivery. Come posso validarla?",
            "Il mio budget è limitato, 10k€. Che strategia consigli?",
            "Il team sono io più un developer. È sufficiente per iniziare?",
            "Dove posso trovare i primi beta tester per l'app?"
        ]
    }
    
    print(f"🎯 Scenario: {scenario['context']}")
    print(f"📋 {len(scenario['queries'])} domande progressive\n")
    
    # Test 1: Modalità ONE-SHOT (ogni domanda indipendente)
    print("--- MODALITÀ ONE-SHOT ---")
    oneshot_results = []
    oneshot_total_tokens = 0
    
    for i, query in enumerate(scenario["queries"], 1):
        print(f"\nDomanda {i}: {query}")
        
        try:
            start_time = time.time()
            response = client.invoke(query)
            end_time = time.time()
            
            tokens = response.prompt_tokens_used + response.completion_tokens_used
            oneshot_total_tokens += tokens
            
            print(f"Risposta: {response.text[:150]}...")
            print(f"Token: {tokens} | Tempo: {end_time - start_time:.2f}s")
            
            oneshot_results.append({
                "query": query,
                "response": response.text,
                "tokens": tokens,
                "time": end_time - start_time
            })
            
        except Exception as e:
            print(f"Errore: {e}")
    
    # Test 2: Modalità CONVERSATIONAL (con memoria)
    print(f"\n{'='*60}")
    print("--- MODALITÀ CONVERSATIONAL ---")
    
    memory = Memory()
    conversational_results = []
    conversational_total_tokens = 0
    
    for i, query in enumerate(scenario["queries"], 1):
        print(f"\nDomanda {i}: {query}")
        
        # Aggiungi query alla memoria
        memory.add_turn([TextBlock(content=query)], ROLE.USER)
        
        try:
            start_time = time.time()
            response = client.invoke("", memory=memory)
            end_time = time.time()
            
            # Aggiungi risposta alla memoria
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            tokens = response.prompt_tokens_used + response.completion_tokens_used
            conversational_total_tokens += tokens
            
            print(f"Risposta: {response.text[:150]}...")
            print(f"Token: {tokens} | Tempo: {end_time - start_time:.2f}s")
            
            conversational_results.append({
                "query": query,
                "response": response.text,
                "tokens": tokens,
                "time": end_time - start_time
            })
            
        except Exception as e:
            print(f"Errore: {e}")
    
    # Analisi comparativa
    print(f"\n{'='*60}")
    print("📊 ANALISI COMPARATIVA")
    
    print(f"\n📈 Statistiche generali:")
    print(f"   One-shot token totali: {oneshot_total_tokens}")
    print(f"   Conversational token totali: {conversational_total_tokens}")
    print(f"   Differenza token: {conversational_total_tokens - oneshot_total_tokens:+d}")
    
    # Calcola tempo medio
    if oneshot_results:
        oneshot_avg_time = sum(r["time"] for r in oneshot_results) / len(oneshot_results)
        print(f"   One-shot tempo medio: {oneshot_avg_time:.2f}s")
    
    if conversational_results:
        conv_avg_time = sum(r["time"] for r in conversational_results) / len(conversational_results)
        print(f"   Conversational tempo medio: {conv_avg_time:.2f}s")
    
    # Analisi qualitativa (simulata)
    print(f"\n🎯 Osservazioni qualitative:")
    print("   One-shot:")
    print("     ✅ Risposte indipendenti e complete")
    print("     ❌ Manca continuità e personalizzazione")
    print("     💰 Token usage più basso per query singole")
    
    print("   Conversational:")
    print("     ✅ Risposte contestualizzate e progressive")
    print("     ✅ Riferimenti a informazioni precedenti") 
    print("     ❌ Token usage crescente con la memoria")
    print("     🎯 Migliore per consulenze complesse")

conversational_vs_oneshot_comparison()
```

---

## 6. Best practices

### Pattern di utilizzo ottimali

```python
def best_practices_guide():
    """Guida alle best practices per one-shot e conversational"""
    
    print("📋 BEST PRACTICES - DatapizzAI Text-Only\n")
    
    # Best practice 1: Gestione errori robusta
    print("1. 🛡️ GESTIONE ERRORI ROBUSTA")
    
    def robust_query(client, prompt: str, max_retries: int = 3):
        """Query con retry automatico e gestione errori"""
        
        for attempt in range(max_retries):
            try:
                response = client.invoke(prompt)
                return response
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Backoff esponenziale
                    print(f"   ⚠️ Tentativo {attempt + 1} fallito: {e}")
                    print(f"   ⏳ Retry tra {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Query fallita dopo {max_retries} tentativi: {e}")
    
    # Best practice 2: Ottimizzazione token
    print("\n2. 💰 OTTIMIZZAZIONE TOKEN")
    
    def token_efficient_conversation():
        """Conversazione ottimizzata per token usage"""
        
        client = create_client("openai")
        if not client:
            return
        
        memory = Memory()
        MAX_MEMORY_TURNS = 8  # Limite turni in memoria
        
        def optimized_chat(user_input: str):
            # Aggiungi input
            memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
            
            # Gestione memoria limitata
            if len(memory.memory) > MAX_MEMORY_TURNS:
                # Mantieni solo gli ultimi N turni
                memory.memory = memory.memory[-MAX_MEMORY_TURNS:]
                print("   🔄 Memoria ottimizzata (ultimi 8 turni)")
            
            try:
                response = client.invoke("", memory=memory)
                memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
                
                print(f"   📊 Token: {response.prompt_tokens_used + response.completion_tokens_used}")
                print(f"   📚 Turni in memoria: {len(memory.memory)}")
                
                return response
                
            except Exception as e:
                print(f"   ❌ Errore: {e}")
        
        # Esempio di uso ottimizzato
        optimized_chat("Iniziamo una consulenza per il mio progetto startup")
        optimized_chat("È un'app mobile per il food delivery")
        # ... la memoria si manterrà entro limiti ragionevoli
    
    # Best practice 3: Prompt engineering
    print("\n3. 🎯 PROMPT ENGINEERING EFFICACE")
    
    def effective_prompting_examples():
        """Esempi di prompt engineering per migliori risultati"""
        
        examples = {
            "Prompt vago": {
                "bad": "Dimmi qualcosa sulle API",
                "good": "Spiega i vantaggi delle API REST rispetto a SOAP per un'applicazione web moderna, includendo 3 esempi pratici"
            },
            "Prompt senza struttura": {
                "bad": "Analizza questo business plan",
                "good": """Analizza questo business plan secondo questi criteri:
                1. Viabilità del mercato
                2. Strategia competitiva  
                3. Proiezioni finanziarie
                4. Rischi principali
                
                Per ogni punto, fornisci valutazione e raccomandazioni."""
            },
            "Prompt senza contesto": {
                "bad": "È una buona idea?",
                "good": "Nel contesto di una startup fintech con budget di 100k€, è una buona idea investire il 30% in marketing digitale nel primo anno?"
            }
        }
        
        for category, example in examples.items():
            print(f"\n   📝 {category}:")
            print(f"      ❌ Inefficace: {example['bad']}")
            print(f"      ✅ Efficace: {example['good'][:80]}...")
    
    effective_prompting_examples()
    
    # Best practice 4: Scelta modalità appropriata
    print("\n4. 🎚️ SCELTA MODALITÀ APPROPRIATA")
    
    decision_matrix = """
    ┌─────────────────────┬─────────────┬──────────────────┐
    │ Scenario            │ One-shot    │ Conversational   │
    ├─────────────────────┼─────────────┼──────────────────┤
    │ Traduzione singola  │ ✅ Ideale   │ ❌ Overhead      │
    │ FAQ semplici        │ ✅ Ideale   │ ❌ Non necessario│
    │ Calcoli matematici  │ ✅ Ideale   │ ❌ Overhead      │
    │ Tutoring/Teaching   │ ❌ Limitato │ ✅ Necessario    │
    │ Consulenza tecnica  │ ❌ Limitato │ ✅ Necessario    │
    │ Brainstorming       │ ❌ Limitato │ ✅ Necessario    │
    │ Debug assistito     │ ❌ Limitato │ ✅ Necessario    │
    │ Analisi iterativa   │ ❌ Limitato │ ✅ Necessario    │
    └─────────────────────┴─────────────┴──────────────────┘
    """
    
    print(decision_matrix)
    
    # Best practice 5: Monitoring e debugging
    print("\n5. 🔍 MONITORING E DEBUGGING")
    
    def monitored_conversation():
        """Conversazione con monitoring avanzato"""
        
        client = create_client("openai", use_cache=True)
        if not client:
            return
        
        memory = Memory()
        conversation_stats = {
            "total_tokens": 0,
            "total_time": 0,
            "cache_hits": 0,
            "errors": 0
        }
        
        def monitored_chat(user_input: str):
            print(f"👤 Input: {user_input}")
            memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
            
            try:
                start_time = time.time()
                response = client.invoke("", memory=memory)
                end_time = time.time()
                
                # Aggiorna statistiche
                tokens = response.prompt_tokens_used + response.completion_tokens_used
                response_time = end_time - start_time
                cache_hits = getattr(response, 'cached_tokens_used', 0)
                
                conversation_stats["total_tokens"] += tokens
                conversation_stats["total_time"] += response_time
                conversation_stats["cache_hits"] += cache_hits
                
                memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
                
                print(f"🤖 Output: {response.text[:100]}...")
                print(f"   📊 Token: {tokens} (Cache: {cache_hits})")
                print(f"   ⏱️ Tempo: {response_time:.2f}s")
                
                return response
                
            except Exception as e:
                conversation_stats["errors"] += 1
                print(f"   ❌ Errore: {e}")
        
        # Esempio monitorato
        monitored_chat("Aiutami con la strategia di marketing")
        monitored_chat("Budget disponibile: 50k€ per 6 mesi")
        monitored_chat("Target: professionisti 30-45 anni")
        
        # Report finale
        print(f"\n📈 REPORT CONVERSAZIONE:")
        print(f"   Token totali: {conversation_stats['total_tokens']}")
        print(f"   Tempo totale: {conversation_stats['total_time']:.2f}s")
        print(f"   Cache hits: {conversation_stats['cache_hits']}")
        print(f"   Errori: {conversation_stats['errors']}")
        print(f"   Efficienza cache: {(conversation_stats['cache_hits']/conversation_stats['total_tokens']*100):.1f}%")
        print(f"   Turni memoria: {len(memory.memory)}")
    
    monitored_conversation()

best_practices_guide()
```

---

## 7. Troubleshooting

### Problemi comuni e soluzioni

```python
def troubleshooting_guide():
    """Guida completa al troubleshooting"""
    
    print("🔧 TROUBLESHOOTING - Problemi comuni e soluzioni\n")
    
    # Problema 1: API Key issues
    print("1. ❌ PROBLEMI API KEY")
    
    def diagnose_api_keys():
        """Diagnostica problemi con le API keys"""
        
        providers = {
            "OpenAI": "OPENAI_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY", 
            "Google": "GOOGLE_API_KEY",
            "Mistral": "MISTRAL_API_KEY"
        }
        
        print("   🔍 Controllo chiavi API:")
        
        for provider, env_var in providers.items():
            key = os.getenv(env_var)
            if key:
                # Verifica formato chiave (primi e ultimi caratteri)
                if len(key) > 10:
                    masked_key = f"{key[:8]}...{key[-4:]}"
                    print(f"   ✅ {provider}: {masked_key}")
                else:
                    print(f"   ⚠️ {provider}: Chiave troppo corta")
            else:
                print(f"   ❌ {provider}: Non configurata")
        
        # Test connessione
        print("\n   🧪 Test connessioni:")
        for provider_name in ["openai", "anthropic", "google"]:
            try:
                client = create_client(provider_name)
                if client:
                    # Test semplice
                    response = client.invoke("Test: rispondi solo 'OK'")
                    print(f"   ✅ {provider_name}: Connessione OK")
                else:
                    print(f"   ❌ {provider_name}: Client creation failed")
            except Exception as e:
                print(f"   ❌ {provider_name}: {str(e)[:50]}...")
    
    diagnose_api_keys()
    
    # Problema 2: Memoria e performance
    print(f"\n2. 🧠 PROBLEMI MEMORIA E PERFORMANCE")
    
    def memory_performance_diagnosis():
        """Diagnostica problemi di memoria e performance"""
        
        print("   📊 Controllo utilizzo memoria:")
        
        # Simula una conversazione per test
        test_memory = Memory()
        
        # Aggiungi molti turni per test
        for i in range(20):
            test_memory.add_turn([TextBlock(content=f"Messaggio di test {i}")], ROLE.USER)
            test_memory.add_turn([TextBlock(content=f"Risposta di test {i}")], ROLE.ASSISTANT)
        
        print(f"   📚 Turni in memoria: {len(test_memory.memory)}")
        print(f"   🧩 Blocchi totali: {len(list(test_memory.iter_blocks()))}")
        
        # Calcola dimensione approssimativa
        total_chars = sum(len(block.content) for block in test_memory.iter_blocks())
        estimated_tokens = total_chars / 4  # Stima approssimativa
        
        print(f"   📝 Caratteri totali: {total_chars}")
        print(f"   🎯 Token stimati: {estimated_tokens:.0f}")
        
        if estimated_tokens > 8000:
            print("   ⚠️ ATTENZIONE: Memoria potrebbe essere troppo grande")
            print("   💡 Soluzioni:")
            print("      - Usa sliding window (mantieni ultimi N turni)")
            print("      - Riassumi conversazione periodicamente")
            print("      - Pulisci memoria manualmente")
        else:
            print("   ✅ Dimensione memoria accettabile")
    
    memory_performance_diagnosis()
    
    # Problema 3: Errori di rate limiting
    print(f"\n3. 🚦 RATE LIMITING E TIMEOUT")
    
    def rate_limiting_solutions():
        """Soluzioni per rate limiting"""
        
        print("   ⚠️ Sintomi rate limiting:")
        print("      - Errore 429 (Too Many Requests)")
        print("      - Timeout improvvisi")
        print("      - Risposte lente")
        
        print("\n   💡 Soluzioni:")
        
        def rate_limited_client(provider: str = "openai"):
            """Client con gestione rate limiting"""
            
            client = create_client(provider)
            if not client:
                return None
                
            def safe_invoke(prompt: str, max_retries: int = 3):
                """Invoke con gestione rate limiting"""
                
                for attempt in range(max_retries):
                    try:
                        response = client.invoke(prompt)
                        return response
                        
                    except Exception as e:
                        error_str = str(e).lower()
                        
                        if "rate" in error_str or "429" in error_str:
                            # Rate limiting detected
                            wait_time = (2 ** attempt) * 5  # Backoff più lungo
                            print(f"      🚦 Rate limit hit, attendo {wait_time}s...")
                            time.sleep(wait_time)
                        elif "timeout" in error_str:
                            # Timeout
                            wait_time = 2 ** attempt
                            print(f"      ⏱️ Timeout, attendo {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            # Altri errori
                            raise e
                
                raise Exception("Max retries exceeded")
            
            return safe_invoke
        
        # Esempio di utilizzo
        print("\n      📝 Esempio implementazione:")
        print("""
        safe_client = rate_limited_client("openai")
        try:
            response = safe_client("La mia domanda")
            print(response.text)
        except Exception as e:
            print(f"Errore definitivo: {e}")
        """)
    
    rate_limiting_solutions()
    
    # Problema 4: Inconsistenza nelle risposte
    print(f"\n4. 🎲 INCONSISTENZA NELLE RISPOSTE")
    
    def response_consistency_analysis():
        """Analizza e migliora consistenza risposte"""
        
        print("   🔍 Test consistenza:")
        
        client = create_client("openai")
        if not client:
            return
        
        test_prompt = "Elenca 3 vantaggi del cloud computing"
        responses = []
        
        print(f"   📝 Prompt test: {test_prompt}")
        print("   🔄 Eseguo 3 volte per test consistenza...")
        
        for i in range(3):
            try:
                response = client.invoke(test_prompt)
                responses.append(response.text)
                print(f"      Risposta {i+1}: {response.text[:60]}...")
            except Exception as e:
                print(f"      Errore {i+1}: {e}")
        
        if len(responses) >= 2:
            # Analisi semplice di similarità
            avg_length = sum(len(r) for r in responses) / len(responses)
            length_variance = sum((len(r) - avg_length)**2 for r in responses) / len(responses)
            
            print(f"\n   📊 Analisi consistenza:")
            print(f"      Lunghezza media: {avg_length:.0f} caratteri")
            print(f"      Varianza lunghezza: {length_variance:.0f}")
            
            if length_variance > 1000:
                print("      ⚠️ Alta variabilità nelle risposte")
                print("      💡 Suggerimenti:")
                print("         - Usa temperature più bassa (0.1-0.3)")
                print("         - Prompt più specifici e strutturati")
                print("         - System prompt più dettagliato")
            else:
                print("      ✅ Consistenza accettabile")
    
    response_consistency_analysis()
    
    # Problema 5: Debugging conversazioni
    print(f"\n5. 🐛 DEBUGGING CONVERSAZIONI")
    
    def conversation_debugging_tools():
        """Tools per debugging conversazioni complesse"""
        
        print("   🔧 Tools di debugging:")
        
        class ConversationDebugger:
            def __init__(self, client):
                self.client = client
                self.memory = Memory()
                self.debug_log = []
            
            def debug_chat(self, user_input: str, debug_level: str = "normal"):
                """Chat con logging dettagliato"""
                
                log_entry = {
                    "timestamp": time.time(),
                    "input": user_input,
                    "memory_size_before": len(self.memory.memory)
                }
                
                if debug_level == "verbose":
                    print(f"   🔍 DEBUG: Input ricevuto: {user_input}")
                    print(f"   🔍 DEBUG: Memoria pre-invocazione: {len(self.memory.memory)} turni")
                
                # Aggiungi input
                self.memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
                log_entry["memory_size_after_input"] = len(self.memory.memory)
                
                try:
                    start_time = time.time()
                    response = self.client.invoke("", memory=self.memory)
                    end_time = time.time()
                    
                    # Aggiungi risposta
                    self.memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
                    
                    log_entry.update({
                        "response": response.text,
                        "tokens_used": response.prompt_tokens_used + response.completion_tokens_used,
                        "response_time": end_time - start_time,
                        "memory_size_final": len(self.memory.memory),
                        "status": "success"
                    })
                    
                    if debug_level == "verbose":
                        print(f"   🔍 DEBUG: Risposta generata in {log_entry['response_time']:.2f}s")
                        print(f"   🔍 DEBUG: Token utilizzati: {log_entry['tokens_used']}")
                        print(f"   🔍 DEBUG: Memoria finale: {log_entry['memory_size_final']} turni")
                    
                    print(f"🤖 Risposta: {response.text}")
                    
                except Exception as e:
                    log_entry.update({
                        "error": str(e),
                        "status": "error"
                    })
                    print(f"❌ Errore: {e}")
                
                self.debug_log.append(log_entry)
            
            def print_debug_summary(self):
                """Stampa riassunto della sessione di debug"""
                
                print("\n   📊 DEBUG SUMMARY:")
                total_tokens = sum(entry.get("tokens_used", 0) for entry in self.debug_log)
                total_time = sum(entry.get("response_time", 0) for entry in self.debug_log)
                errors = sum(1 for entry in self.debug_log if entry["status"] == "error")
                
                print(f"      Interazioni totali: {len(self.debug_log)}")
                print(f"      Token totali: {total_tokens}")
                print(f"      Tempo totale: {total_time:.2f}s")
                print(f"      Errori: {errors}")
                print(f"      Memoria finale: {len(self.memory.memory)} turni")
        
        # Esempio di utilizzo del debugger
        print("\n   📝 Esempio utilizzo ConversationDebugger:")
        print("""
        debugger = ConversationDebugger(client)
        debugger.debug_chat("Prima domanda", debug_level="verbose")
        debugger.debug_chat("Seconda domanda collegata")
        debugger.print_debug_summary()
        """)
    
    conversation_debugging_tools()

troubleshooting_guide()
```

### Validazione e test automatici

```python
def validation_and_testing():
    """Sistema di validazione e test automatici"""
    
    print("✅ SISTEMA VALIDAZIONE E TEST AUTOMATICI\n")
    
    def validate_environment():
        """Valida configurazione ambiente completa"""
        
        print("🔍 Validazione ambiente:")
        
        validation_results = {
            "env_file": False,
            "api_keys": [],
            "client_creation": [],
            "basic_functionality": []
        }
        
        # 1. Verifica file .env
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        validation_results["env_file"] = os.path.exists(env_path)
        print(f"   {'✅' if validation_results['env_file'] else '❌'} File .env: {'OK' if validation_results['env_file'] else 'Mancante'}")
        
        # 2. Verifica API keys
        providers = ["openai", "anthropic", "google", "mistral"]
        for provider in providers:
            key_var = f"{provider.upper()}_API_KEY"
            has_key = bool(os.getenv(key_var))
            validation_results["api_keys"].append((provider, has_key))
            print(f"   {'✅' if has_key else '❌'} {provider}: {'Configurata' if has_key else 'Mancante'}")
        
        # 3. Test creazione client
        for provider in providers[:3]:  # Test solo i principali
            try:
                client = create_client(provider)
                success = client is not None
                validation_results["client_creation"].append((provider, success))
                print(f"   {'✅' if success else '❌'} Client {provider}: {'OK' if success else 'Fallito'}")
            except Exception as e:
                validation_results["client_creation"].append((provider, False))
                print(f"   ❌ Client {provider}: {str(e)[:50]}...")
        
        # 4. Test funzionalità base
        for provider, success in validation_results["client_creation"]:
            if success:
                try:
                    client = create_client(provider)
                    response = client.invoke("Test: rispondi solo 'OK'")
                    func_test = "ok" in response.text.lower()
                    validation_results["basic_functionality"].append((provider, func_test))
                    print(f"   {'✅' if func_test else '⚠️'} Funzionalità {provider}: {'OK' if func_test else 'Parziale'}")
                except Exception:
                    validation_results["basic_functionality"].append((provider, False))
                    print(f"   ❌ Funzionalità {provider}: Fallita")
        
        return validation_results
    
    def run_automated_tests():
        """Esegue suite di test automatici"""
        
        print("\n🧪 Suite test automatici:")
        
        test_results = []
        
        # Test 1: One-shot basic
        print("\n   Test 1: One-shot basic")
        try:
            client = create_client("openai")
            if client:
                response = client.invoke("Calcola 2+2")
                contains_four = "4" in response.text or "quattro" in response.text.lower()
                test_results.append(("one_shot_basic", contains_four))
                print(f"      {'✅' if contains_four else '❌'} Calcolo matematico: {'OK' if contains_four else 'Fallito'}")
            else:
                test_results.append(("one_shot_basic", False))
                print("      ❌ Client non disponibile")
        except Exception as e:
            test_results.append(("one_shot_basic", False))
            print(f"      ❌ Errore: {e}")
        
        # Test 2: Conversational memory
        print("\n   Test 2: Conversational memory")
        try:
            client = create_client("openai")
            if client:
                memory = Memory()
                
                # Step 1: Presentazione
                memory.add_turn([TextBlock(content="Mi chiamo TestUser")], ROLE.USER)
                response1 = client.invoke("", memory=memory)
                memory.add_turn([TextBlock(content=response1.text)], ROLE.ASSISTANT)
                
                # Step 2: Test memoria
                memory.add_turn([TextBlock(content="Qual è il mio nome?")], ROLE.USER)
                response2 = client.invoke("", memory=memory)
                
                memory_works = "testuser" in response2.text.lower()
                test_results.append(("conversational_memory", memory_works))
                print(f"      {'✅' if memory_works else '❌'} Memoria conversazione: {'OK' if memory_works else 'Fallita'}")
            else:
                test_results.append(("conversational_memory", False))
                print("      ❌ Client non disponibile")
        except Exception as e:
            test_results.append(("conversational_memory", False))
            print(f"      ❌ Errore: {e}")
        
        # Test 3: Cache functionality (se supportata)
        print("\n   Test 3: Cache functionality")
        try:
            client = create_client("openai", use_cache=True)
            if client:
                # Stessa query due volte
                query = "Test cache: rispondi con 'CACHE_TEST'"
                response1 = client.invoke(query)
                response2 = client.invoke(query)
                
                # Verifica se la seconda ha cache hits (approssimativo)
                cache_works = hasattr(response2, 'cached_tokens_used')
                test_results.append(("cache_functionality", cache_works))
                print(f"      {'✅' if cache_works else '⚠️'} Cache system: {'OK' if cache_works else 'Non verificabile'}")
            else:
                test_results.append(("cache_functionality", False))
                print("      ❌ Client non disponibile")
        except Exception as e:
            test_results.append(("cache_functionality", False))
            print(f"      ❌ Errore: {e}")
        
        # Report finale
        print(f"\n📊 REPORT FINALE TEST:")
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"   Test superati: {passed_tests}/{total_tests}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("   ✅ Sistema pronto per l'uso")
        elif success_rate >= 50:
            print("   ⚠️ Sistema parzialmente funzionale")
        else:
            print("   ❌ Sistema necessita configurazione")
        
        return test_results
    
    # Esegui validazione completa
    validation_results = validate_environment()
    test_results = run_automated_tests()
    
    return validation_results, test_results

validation_and_testing()
```

---

## Conclusioni

### Riassunto modalità di utilizzo

**One-shot** - Ideale per:
- Query indipendenti senza contesto
- Traduzioni, calcoli, analisi singole
- Sistemi FAQ e supporto base
- Costi token ottimizzati per task isolati

**Conversational** - Essenziale per:
- Consulenze e tutoring progressivo
- Sviluppo iterativo di idee
- Supporto tecnico multi-step
- Analisi collaborative di documenti

### Pattern di implementazione consigliati

```python
# Pattern One-shot per task indipendenti
def independent_task(client, prompt: str):
    return client.invoke(prompt)

# Pattern Conversational per sessioni interattive  
def interactive_session(client):
    memory = Memory()
    while True:
        user_input = input("Utente: ")
        if user_input.lower() == 'exit':
            break
        
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        response = client.invoke("", memory=memory)
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        
        print(f"Assistente: {response.text}")
```

### Metriche di performance

- **One-shot**: ~50-200 token per query, latenza 1-3s
- **Conversational**: Token crescenti con memoria, latenza variabile
- **Cache hit**: Riduzione costi ~50% per query ripetute
- **Memory management**: Fondamentale per conversazioni >10 turni

Il framework DatapizzAI text-only fornisce un'interfaccia unificata per gestire entrambe le modalità con semplicità e flessibilità ottimali per ogni scenario d'uso.
