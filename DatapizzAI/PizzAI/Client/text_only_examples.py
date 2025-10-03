#!/usr/bin/env python3
"""
Script di esempio per l'uso della libreria datapizza - Modalità TEXT-ONLY
========================================================================

Questo script dimostra come utilizzare datapizza per gestire prompt testuali:
1. Modalità "one shot" - singola query → risposta
2. Modalità "conversational" - sessione multi-turno con memoria

Autore: Marco Calcaterra
Data: 2025
"""

import os
import time
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env nella directory parent
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Importazioni datapizza
from datapizza.clients import ClientFactory
from datapizza.clients.factory import Provider
from datapizza.memory import Memory
from datapizza.type import TextBlock, ROLE
from datapizza.cache import MemoryCache


def print_section(title: str):
    """Stampa una sezione formattata"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def print_subsection(title: str):
    """Stampa una sottosezione formattata"""
    print(f"\n--- {title} ---")


def create_client(provider_name: str = "openai", use_cache: bool = False):
    """
    Crea e restituisce un client datapizza configurato
    
    Args:
        provider_name: Nome del provider ("openai", "anthropic", "google", "mistral")
        use_cache: Se abilitare la cache in memoria
    """
    
    # Mappatura delle chiavi API per provider
    api_keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", 
        "google": "GOOGLE_API_KEY",
        "mistral": "MISTRAL_API_KEY"
    }
    
    # Modelli consigliati per provider
    models = {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-latest",
        "google": "gemini-2.5-flash", 
        "mistral": "mistral-large-latest"
    }
    
    # Provider che supportano cache nel costruttore
    cache_supported_providers = {"openai", "azure_openai"}
    
    api_key = os.getenv(api_keys.get(provider_name))
    if not api_key:
        print(f"⚠️ Chiave API non trovata per {provider_name}. Verifica il file .env")
        return None
    
    # Cache opzionale - solo per provider che la supportano
    cache = None
    extra_kwargs = {}
    
    if use_cache and provider_name.lower() in cache_supported_providers:
        cache = MemoryCache()
        extra_kwargs["cache"] = cache
    
    try:
        client = ClientFactory.create(
            provider=provider_name,
            api_key=api_key,
            model=models[provider_name],
            system_prompt="Sei un assistente AI utile. Rispondi sempre in italiano in modo chiaro e conciso.",
            temperature=0.7,
            **extra_kwargs
        )
        
        print(f"✅ Client {provider_name} creato con successo")
        if cache:
            print("   📦 Cache in memoria abilitata")
        elif use_cache:
            print(f"   ⚠️ Cache non supportata per {provider_name}")
        
        return client
        
    except Exception as e:
        print(f"❌ Errore nella creazione del client {provider_name}: {e}")
        return None


# ==============================================================================
# MODALITÀ ONE-SHOT (Singola Query → Risposta)
# ==============================================================================

def demo_one_shot_basic():
    """
    Dimostra l'utilizzo base one-shot con diverse tipologie di prompt
    """
    print_section("MODALITÀ ONE-SHOT - Esempi Base")
    
    # Crea il client
    client = create_client("openai", use_cache=True)
    if not client:
        print("❌ Impossibile continuare senza client")
        return
    
    # Esempi di prompt diversi
    prompts = [
        {
            "name": "Domanda informativa",
            "prompt": "Cos'è il machine learning in parole semplici?",
            "description": "Richiesta di spiegazione di un concetto"
        },
        {
            "name": "Compito creativo", 
            "prompt": "Scrivi una breve poesia sulla primavera",
            "description": "Task di generazione creativa"
        },
        {
            "name": "Richiesta di analisi",
            "prompt": "Elenca 3 vantaggi e 3 svantaggi del lavoro da remoto",
            "description": "Analisi strutturata di un argomento"
        },
        {
            "name": "Problema matematico",
            "prompt": "Se compro 3 libri a 15€ l'uno e pago con una banconota da 50€, quanto ricevo di resto?",
            "description": "Calcolo matematico semplice"
        }
    ]
    
    for i, example in enumerate(prompts, 1):
        print_subsection(f"{i}. {example['name']}")
        print(f"Descrizione: {example['description']}")
        print(f"Prompt: '{example['prompt']}'")
        
        try:
            # Misuriamo il tempo di risposta
            start_time = time.time()
            
            # Invocazione semplice con stringa
            response = client.invoke(example['prompt'])
            
            end_time = time.time()
            
            # Mostra i risultati
            print(f"\n🤖 Risposta:")
            print(f"   {response.text}")
            print(f"\n📊 Statistiche:")
            print(f"   ⏱️ Tempo: {end_time - start_time:.2f}s")
            print(f"   🎯 Token prompt: {response.prompt_tokens_used}")
            print(f"   💬 Token risposta: {response.completion_tokens_used}")
            print(f"   🔄 Stop reason: {response.stop_reason}")
            
            # Se c'è cache, mostra se è stato un hit
            if hasattr(response, 'cached_tokens_used') and response.cached_tokens_used:
                print(f"   📦 Cache hit: {response.cached_tokens_used} token dalla cache")
                
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        print()  # Riga vuota per separazione


def demo_one_shot_advanced():
    """
    Dimostra utilizzo one-shot avanzato con TextBlock e configurazioni diverse
    """
    print_section("MODALITÀ ONE-SHOT - Esempi Avanzati")
    
    client = create_client("openai")
    if not client:
        return
    
    print_subsection("1. Utilizzo con TextBlock")
    
    # Esempio con TextBlock invece di stringa semplice
    text_blocks = [
        TextBlock(content="Analizza questo testo e dimmi il sentiment: 'Oggi è stata una giornata fantastica! Ho ricevuto una promozione al lavoro!'")
    ]
    
    try:
        response = client.invoke(input=text_blocks)
        print(f"🤖 Analisi sentiment: {response.text}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
    
    print_subsection("2. Prompt con istruzioni specifiche")
    
    structured_prompt = """
    Agisci come un esperto nutrizionista. 
    
    Domanda: Quali sono i benefici delle mele per la salute?
    
    Rispondi seguendo questa struttura:
    1. Benefici principali (max 3)
    2. Valori nutrizionali importanti
    3. Raccomandazione per il consumo giornaliero
    
    Mantieni la risposta concisa ma informativa.
    """
    
    try:
        response = client.invoke(structured_prompt)
        print(f"🤖 Consulto nutrizionale: {response.text}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_one_shot_comparison():
    """
    Confronta le risposte di diversi provider sullo stesso prompt
    """
    print_section("CONFRONTO PROVIDER - Stesso Prompt")
    
    test_prompt = "Spiega la differenza tra intelligenza artificiale e machine learning in 2-3 frasi"
    
    providers = ["openai", "anthropic", "google"]  # Aggiungi "mistral" se hai la chiave
    
    print(f"🎯 Prompt di test: '{test_prompt}'")
    print()
    
    for provider in providers:
        print_subsection(f"Provider: {provider.upper()}")
        
        client = create_client(provider)
        if not client:
            print(f"   ⏭️ Saltato (client non disponibile)")
            continue
            
        try:
            start_time = time.time()
            response = client.invoke(test_prompt)
            end_time = time.time()
            
            print(f"   🤖 Risposta: {response.text}")
            print(f"   ⏱️ Tempo: {end_time - start_time:.2f}s")
            print(f"   📊 Token: {response.prompt_tokens_used + response.completion_tokens_used}")
            
        except Exception as e:
            print(f"   ❌ Errore: {e}")


# ==============================================================================
# MODALITÀ CONVERSATIONAL (Sessioni Multi-turno con Memoria)
# ==============================================================================

def demo_conversational_basic():
    """
    Dimostra una conversazione base con memoria
    """
    print_section("MODALITÀ CONVERSATIONAL - Conversazione Base")
    
    client = create_client("openai")
    if not client:
        return
    
    # Inizializza la memoria per la conversazione
    memory = Memory()
    
    print("🎭 Simulazione di conversazione con memoria:")
    print("   L'assistente dovrebbe ricordare le informazioni precedenti\n")
    
    # Definisci i turni della conversazione
    conversation_turns = [
        {
            "user": "Ciao! Mi chiamo Mirko e sono un GenAI Engineer di 27 anni.",
            "context": "Presentazione iniziale dell'utente"
        },
        {
            "user": "Qual è il mio nome e la mia professione?",
            "context": "Test della memoria - informazioni personali"
        },
        {
            "user": "Quanti anni ho?", 
            "context": "Test della memoria - dettagli specifici"
        },
        {
            "user": "Ora dimmi cosa ne pensi del futuro dell'AI nel mio settore",
            "context": "Domanda che richiede contesto precedente"
        }
    ]
    
    for i, turn in enumerate(conversation_turns, 1):
        print(f"💬 Turno {i}: {turn['context']}")
        print(f"👤 Utente: {turn['user']}")
        
        # Aggiungi il messaggio dell'utente alla memoria
        user_message = TextBlock(content=turn['user'])
        memory.add_turn([user_message], ROLE.USER)
        
        try:
            # Invoca il client passando la memoria
            # Input vuoto perché il contesto è nella memoria
            response = client.invoke(
                input="",  
                memory=memory
            )
            
            # Aggiungi la risposta dell'assistente alla memoria  
            assistant_message = TextBlock(content=response.text)
            memory.add_turn([assistant_message], ROLE.ASSISTANT)
            
            print(f"🤖 Assistente: {response.text}")
            print(f"   📊 Token usati: {response.prompt_tokens_used + response.completion_tokens_used}")
            
        except Exception as e:
            print(f"   ❌ Errore: {e}")
            # In caso di errore, aggiungi comunque un messaggio simulato per continuare la demo
            fallback_msg = TextBlock(content="Mi dispiace, c'è stato un errore tecnico.")
            memory.add_turn([fallback_msg], ROLE.ASSISTANT)
        
        print()  # Riga vuota per separazione
    
    # Statistiche finali sulla conversazione
    print_subsection("Statistiche Conversazione")
    print(f"   📚 Turni totali: {len(memory.memory)}")
    print(f"   💬 Blocchi totali: {len(list(memory.iter_blocks()))}")
    
    # Mostra il contenuto della memoria
    print(f"   🧠 Contenuto della memoria:")
    for i, turn in enumerate(memory.memory):
        role_icon = "👤" if turn.role == ROLE.USER else "🤖"
        content_preview = turn.blocks[0].content[:50] + "..." if len(turn.blocks[0].content) > 50 else turn.blocks[0].content
        print(f"      {role_icon} Turno {i+1}: {content_preview}")


def demo_conversational_advanced():
    """
    Conversazione avanzata con gestione di diversi scenari
    """
    print_section("MODALITÀ CONVERSATIONAL - Scenari Avanzati")
    
    client = create_client("openai", use_cache=True)
    if not client:
        return
    
    memory = Memory()
    
    def chat_turn(user_input: str, description: str = "", show_tokens: bool = True):
        """Helper per gestire un turno di chat"""
        if description:
            print(f"📋 Scenario: {description}")
        print(f"👤 Utente: {user_input}")
        
        # Aggiungi input alla memoria
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            response = client.invoke(user_input, memory=memory)
            
            # Aggiungi risposta alla memoria
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Assistente: {response.text}")
            
            if show_tokens:
                total_tokens = response.prompt_tokens_used + response.completion_tokens_used
                print(f"   📊 Token: {total_tokens} | Cache hits: {getattr(response, 'cached_tokens_used', 0)}")
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            # Fallback per continuare la demo
            memory.add_turn([TextBlock(content="Errore tecnico temporaneo.")], ROLE.ASSISTANT)
        
        print()
    
    # Scenario 1: Conversazione di lavoro
    print_subsection("Scenario 1: Consulenza professionale")
    
    chat_turn(
        "Sono il CTO di una startup e devo decidere se adottare microservizi o un'architettura monolitica.",
        "Richiesta di consulenza tecnica"
    )
    
    chat_turn(
        "Abbiamo un team di 5 sviluppatori e prevediamo di crescere fino a 20 nei prossimi 2 anni.",
        "Fornisco dettagli aggiuntivi per migliorare la consulenza"
    )
    
    chat_turn(
        "Quali sono i primi 3 passi che mi consigli di fare?",
        "Richiesta di piano d'azione basato sul contesto"
    )
    
    # Scenario 2: Cambio di argomento ma con memoria
    print_subsection("Scenario 2: Cambio argomento mantenendo contesto")
    
    chat_turn(
        "Ora cambiamo argomento. Cosa pensi dei viaggi nello spazio?",
        "Cambio completo di argomento"
    )
    
    chat_turn(
        "Ma tornando al discorso di prima, come CTO dovrei preoccuparmi della scalabilità?",
        "Ritorno al contesto precedente - test memoria a lungo termine"
    )
    
    # Scenario 3: Memoria selettiva 
    print_subsection("Scenario 3: Gestione memoria avanzata")
    
    # Creiamo una nuova conversazione ma copiando parte della memoria precedente
    partial_memory = Memory()
    
    # Copiamo solo gli ultimi 4 turni per simulare una memoria "sliding window"
    recent_turns = memory.memory[-4:] if len(memory.memory) >= 4 else memory.memory
    for turn in recent_turns:
        partial_memory.memory.append(turn)
    
    print("🧠 Utilizzando memoria parziale (ultimi 4 turni)...")
    
    try:
        response = client.invoke(
            "Riassumi brevemente di cosa abbiamo parlato",
            memory=partial_memory
        )
        print(f"🤖 Riassunto con memoria parziale: {response.text}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_conversational_memory_management():
    """
    Dimostra diverse tecniche di gestione della memoria
    """
    print_section("GESTIONE AVANZATA DELLA MEMORIA")
    
    client = create_client("openai")
    if not client:
        return
    
    print_subsection("1. Operazioni su memoria")
    
    # Crea una memoria e popolala
    memory = Memory()
    
    # Aggiungi alcuni messaggi di esempio
    sample_messages = [
        ("Mi chiamo Ilaria e lavoro come designer", ROLE.USER),
        ("Piacere di conoscerti Ilaria! Come posso aiutarti oggi?", ROLE.ASSISTANT),
        ("Sto lavorando su un progetto di UI/UX per un'app mobile", ROLE.USER),
        ("Interessante! Di che tipo di app si tratta?", ROLE.ASSISTANT),
        ("È un'app per il fitness con tracciamento degli allenamenti", ROLE.USER)
    ]
    
    for content, role in sample_messages:
        memory.add_turn([TextBlock(content=content)], role)
    
    print(f"   📚 Memoria creata con {len(memory.memory)} turni")
    
    # 1. Copia della memoria
    backup_memory = memory.copy()
    print(f"   💾 Backup creato: {len(backup_memory.memory)} turni")
    
    # 2. Iterazione attraverso i blocchi
    print(f"   🔍 Contenuto dettagliato:")
    for i, (content, role) in enumerate(sample_messages):
        role_icon = "👤" if role == ROLE.USER else "🤖"
        print(f"      {role_icon} {content[:40]}...")
    
    # 3. Test della memoria nella conversazione
    print_subsection("2. Test continuità conversazione")
    
    try:
        response = client.invoke(
            "Come si chiama l'utente e su cosa sta lavorando?",
            memory=memory
        )
        print(f"   🤖 Test memoria: {response.text}")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")
    
    # 4. Pulizia memoria
    print_subsection("3. Gestione dimensione memoria")
    
    print(f"   📊 Prima della pulizia: {len(memory.memory)} turni")
    
    # Simula una pulizia mantenendo solo gli ultimi 3 turni
    if len(memory.memory) > 3:
        recent_turns = memory.memory[-3:]
        memory.memory.clear()
        memory.memory.extend(recent_turns)
        
    print(f"   🧹 Dopo pulizia (ultimi 3): {len(memory.memory)} turni")
    
    # Test che la memoria ridotta funzioni ancora
    try:
        response = client.invoke(
            "Di cosa stavamo parlando?",
            memory=memory
        )
        print(f"   🤖 Test memoria ridotta: {response.text}")
        
    except Exception as e:
        print(f"   ❌ Errore: {e}")


def demo_sliding_window_chat():
    """
    Dimostra l'utilizzo pratico della strategia sliding window per ottimizzare i token
    """
    print_section("STRATEGIA SLIDING WINDOW - Ottimizzazione Token")
    
    client = create_client("openai")
    if not client:
        return
    
    def sliding_window_chat(memory: Memory, user_input: str, window_size: int = 6):
        """
        Gestisce una conversazione mantenendo solo gli ultimi N turni per ottimizzare token usage
        
        Args:
            memory: Oggetto Memory per la conversazione
            user_input: Input dell'utente
            window_size: Numero massimo di turni da mantenere in memoria
        
        Returns:
            Response object dal client
        """
        # Aggiungi input utente
        memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        # Limita memoria se necessario - mantieni solo gli ultimi N turni
        if len(memory.memory) > window_size:
            print(f"   🧹 Pulizia memoria: mantenuti solo ultimi {window_size} turni")
            memory.memory = memory.memory[-window_size:]
        
        # Genera risposta con memoria ottimizzata
        response = client.invoke(user_input, memory=memory)
        
        # Aggiungi risposta alla memoria
        memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
        
        return response
    
    # Simula una conversazione lunga con sliding window
    print("🎭 Simulazione conversazione lunga con sliding window (max 4 turni):")
    print("   La memoria viene automaticamente pulita per mantenere solo i turni recenti\n")
    
    # Crea una nuova memoria per questa demo
    sliding_memory = Memory()
    
    # Conversazione di esempio
    conversation = [
        "Ciao! Sono un sviluppatore Python alle prime armi.",
        "Vorrei imparare a creare un chatbot con Python.",
        "Quali librerie mi consigli per iniziare?",
        "E come gestisco la memoria delle conversazioni?",
        "Puoi mostrarmi un esempio di codice?",
        "Come gestisco gli errori e le eccezioni?",
        "E per il deployment su un server web?",
        "Quali sono le best practices per la sicurezza?",
        "Come posso ottimizzare le performance?",
        "Puoi riassumere i punti principali che abbiamo discusso?"
    ]
    
    for i, user_input in enumerate(conversation, 1):
        print(f"💬 Turno {i}: {user_input}")
        
        try:
            response = sliding_window_chat(sliding_memory, user_input, window_size=4)
            
            print(f"🤖 Assistente: {response.text}")
            print(f"   📊 Token: {response.prompt_tokens_used + response.completion_tokens_used}")
            print(f"   🧠 Memoria: {len(sliding_memory.memory)} turni attivi")
            
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        print()
    
    # Mostra la memoria finale
    print_subsection("Memoria finale dopo sliding window")
    print(f"   📚 Turni totali nella memoria: {len(sliding_memory.memory)}")
    print(f"   🧠 Contenuto memoria (ultimi 4 turni):")
    for i, turn in enumerate(sliding_memory.memory):
        role_icon = "👤" if turn.role == ROLE.USER else "🤖"
        content_preview = turn.blocks[0].content[:60] + "..." if len(turn.blocks[0].content) > 60 else turn.blocks[0].content
        print(f"      {role_icon} {content_preview}")


def demo_complex_chatbot_creation():
    """
    Dimostra un esempio complesso: creazione di un chatbot con diverse funzionalità
    """
    print_section("ESEMPIO COMPLESSO - Creazione Chatbot")
    
    client = create_client("openai")
    if not client:
        return
    
    # Crea una memoria specializzata per il progetto chatbot
    chatbot_memory = Memory()
    
    print("🤖 Simulazione sviluppo chatbot con assistente AI:")
    print("   L'assistente aiuta a progettare e implementare un chatbot completo\n")
    
    # Fase 1: Analisi dei requisiti
    print_subsection("Fase 1: Analisi Requisiti")
    
    requirements_conversation = [
        "Voglio creare un chatbot per un e-commerce di abbigliamento. Puoi aiutarmi?",
        "Il chatbot deve gestire: assistenza clienti, ricerca prodotti, gestione ordini e supporto post-vendita.",
        "Avremo circa 1000 clienti al giorno e dobbiamo gestire 5 lingue diverse.",
        "Quali sono i requisiti tecnici principali che devo considerare?",
        "Come strutturerei l'architettura del sistema?",
        "Quali tecnologie mi consigli per il backend e il frontend?",
        "Come gestisco la scalabilità e la disponibilità del servizio?",
        "Quali sono i costi stimati per l'infrastruttura?"
    ]
    
    for i, user_input in enumerate(requirements_conversation, 1):
        print(f"👤 Analista: {user_input}")
        
        # Aggiungi input alla memoria
        chatbot_memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            response = client.invoke(user_input, memory=chatbot_memory)
            chatbot_memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Consulente: {response.text}")
            print(f"   📊 Token: {response.prompt_tokens_used + response.completion_tokens_used}")
            
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        print()
    
    # Fase 2: Progettazione tecnica
    print_subsection("Fase 2: Progettazione Tecnica")
    
    technical_conversation = [
        "Ora passiamo alla progettazione tecnica. Come strutturerei il database?",
        "Quali API esterne mi servono per integrare i sistemi di pagamento?",
        "Come implemento il sistema di autenticazione e autorizzazione?",
        "Quali sono le best practices per la sicurezza dei dati personali?",
        "Come gestisco il logging e il monitoring del sistema?",
        "Quali test devo implementare per garantire la qualità?",
        "Come strutturerei il deployment e il CI/CD?",
        "Quali metriche devo monitorare per valutare le performance?"
    ]
    
    for i, user_input in enumerate(technical_conversation, 1):
        print(f"👤 Architetto: {user_input}")
        
        chatbot_memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            response = client.invoke(user_input, memory=chatbot_memory)
            chatbot_memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Consulente: {response.text}")
            
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        print()
    
    # Fase 3: Implementazione e testing
    print_subsection("Fase 3: Implementazione e Testing")
    
    implementation_conversation = [
        "Ora passiamo all'implementazione. Puoi mostrarmi la struttura del codice?",
        "Come implemento il sistema di gestione delle conversazioni?",
        "Come gestisco i fallback quando l'AI non capisce la richiesta?",
        "Come implemento il sistema di feedback e rating delle risposte?",
        "Come gestisco l'aggiornamento del modello AI nel tempo?",
        "Quali sono i test automatizzati che devo implementare?",
        "Come faccio il testing con utenti reali?",
        "Come valuto e miglioro le performance del chatbot?"
    ]
    
    for i, user_input in enumerate(implementation_conversation, 1):
        print(f"👤 Sviluppatore: {user_input}")
        
        chatbot_memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
        
        try:
            response = client.invoke(user_input, memory=chatbot_memory)
            chatbot_memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 Consulente: {response.text}")
            
        except Exception as e:
            print(f"   ❌ Errore: {e}")
        
        print()
    
    # Fase 4: Riassunto e prossimi passi
    print_subsection("Fase 4: Riassunto e Prossimi Passi")
    
    try:
        summary_response = client.invoke(
            "Riassumi il progetto del chatbot e fornisci un piano d'azione con i prossimi 5 passi da seguire",
            memory=chatbot_memory
        )
        
        print("📋 Riassunto progetto e piano d'azione:")
        print(f"🤖 {summary_response.text}")
        
    except Exception as e:
        print(f"❌ Errore nel riassunto: {e}")
    
    # Statistiche finali
    print_subsection("Statistiche Progetto Chatbot")
    print(f"   📚 Turni totali: {len(chatbot_memory.memory)}")
    print(f"   🎯 Fasi completate: 4 (Requisiti, Progettazione, Implementazione, Riassunto)")
    print(f"   💬 Conversazioni simulate: {len(requirements_conversation) + len(technical_conversation) + len(implementation_conversation)}")
    print(f"   🧠 Memoria utilizzata: {len(list(chatbot_memory.iter_blocks()))} blocchi")


# ==============================================================================
# FUNZIONE PRINCIPALE E MENU
# ==============================================================================

def show_menu():
    """Mostra il menu delle demo disponibili"""
    print_section("DEMO DATAPIZZA - Modalità TEXT-ONLY")
    
    print("""
Seleziona la demo da eseguire:

MODALITÀ ONE-SHOT:
1. Esempi base one-shot
2. Esempi avanzati one-shot  
3. Confronto tra provider

MODALITÀ CONVERSATIONAL:
4. Conversazione base con memoria
5. Scenari conversazionali avanzati
6. Gestione avanzata della memoria
7. Strategia sliding window (ottimizzazione token)
8. Esempio complesso: creazione chatbot

ALTRO:
9. Esegui tutte le demo
0. Esci

Nota: Assicurati di avere le chiavi API configurate nel file .env
    """)


def run_demo(choice: str):
    """Esegue la demo selezionata"""
    demos = {
        "1": demo_one_shot_basic,
        "2": demo_one_shot_advanced, 
        "3": demo_one_shot_comparison,
        "4": demo_conversational_basic,
        "5": demo_conversational_advanced,
        "6": demo_conversational_memory_management,
        "7": demo_sliding_window_chat,
        "8": demo_complex_chatbot_creation,
        "9": run_all_demos
    }
    
    if choice in demos:
        print(f"\n🚀 Avvio demo {choice}...")
        try:
            demos[choice]()
        except KeyboardInterrupt:
            print("\n\n⏹️ Demo interrotta dall'utente")
        except Exception as e:
            print(f"\n❌ Errore durante l'esecuzione: {e}")
    else:
        print("❌ Scelta non valida")


def run_all_demos():
    """Esegue tutte le demo in sequenza"""
    print_section("ESECUZIONE TUTTE LE DEMO")
    
    all_demos = [
        ("One-shot base", demo_one_shot_basic),
        ("One-shot avanzati", demo_one_shot_advanced),
        ("Confronto provider", demo_one_shot_comparison), 
        ("Conversational base", demo_conversational_basic),
        ("Conversational avanzati", demo_conversational_advanced),
        ("Gestione memoria", demo_conversational_memory_management),
        ("Sliding window", demo_sliding_window_chat),
        ("Creazione chatbot", demo_complex_chatbot_creation)
    ]
    
    for i, (name, demo_func) in enumerate(all_demos, 1):
        print(f"\n🎬 Demo {i}/{len(all_demos)}: {name}")
        print("⏳ Inizio tra 2 secondi... (Ctrl+C per saltare)")
        
        try:
            time.sleep(2)
            demo_func()
        except KeyboardInterrupt:
            print("⏭️ Demo saltata")
        except Exception as e:
            print(f"❌ Errore in {name}: {e}")
    
    print_section("TUTTE LE DEMO COMPLETATE")


def main():
    """Funzione principale con menu interattivo"""
    
    # Verifica configurazione base
    print("🔍 Verifica configurazione...")
    
    # Controlla se il file .env esiste nella directory parent
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        print(f"""
⚠️ File .env non trovato in {env_path}!

Crea un file .env nella directory PizzAI/ con le tue chiavi API:

OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here  
GOOGLE_API_KEY=your-google-key-here
MISTRAL_API_KEY=your-mistral-key-here

Almeno una chiave è necessaria per eseguire le demo.
        """)
    
    # Controlla le chiavi disponibili
    available_providers = []
    for provider, env_key in [("OpenAI", "OPENAI_API_KEY"), ("Anthropic", "ANTHROPIC_API_KEY"), 
                             ("Google", "GOOGLE_API_KEY"), ("Mistral", "MISTRAL_API_KEY")]:
        if os.getenv(env_key):
            available_providers.append(provider)
    
    if available_providers:
        print(f"✅ Provider disponibili: {', '.join(available_providers)}")
    else:
        print("⚠️ Nessuna chiave API trovata. Alcune demo potrebbero fallire.")
    
    # Menu interattivo
    while True:
        try:
            show_menu()
            choice = input("👉 Scegli un'opzione: ").strip()
            
            if choice == "0":
                print("👋 Arrivederci!")
                break
                
            run_demo(choice)
            
            # Pausa tra le demo
            input("\n⏸️ Premi INVIO per continuare...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Uscita forzata. Arrivederci!")
            break
        except Exception as e:
            print(f"\n❌ Errore inaspettato: {e}")
            print("🔄 Riavvio del menu...")


if __name__ == "__main__":
    main()
