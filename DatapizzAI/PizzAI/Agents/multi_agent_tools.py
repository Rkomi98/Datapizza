#!/usr/bin/env python3
"""
Multi Tool Framework - DatapizzAI
=================================

Questo script dimostra come creare e utilizzare client multi-tool con il framework datapizzai.
I client possono utilizzare diversi strumenti per completare task complessi.

Autore: Mirko Calcaterra
Data: 2025
"""

import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env nella directory parent
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Importazioni datapizzai
from datapizzai.clients import ClientFactory
from datapizzai.tools import tool
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE


def print_section(title: str):
    """Stampa una sezione formattata"""
    print("\n" + "="*65)
    print(f" {title}")
    print("="*65)


def print_subsection(title: str):
    """Stampa una sottosezione formattata"""
    print(f"\n--- {title} ---")


def execute_tool_calls(response, available_tools):
    """Esegue i function call presenti nella risposta utilizzando i tool passati.

    Usa response.function_calls invece di scorrere il contenuto testuale.
    """
    tool_results = []
    # Crea mappa dai tool disponibili passati alla funzione
    tool_map = {t.name: t for t in available_tools}

    for call in getattr(response, "function_calls", []) or []:
        tool_name = getattr(call, "name", None)
        arguments = getattr(call, "arguments", {}) or {}

        print(f"   🔧 Strumento usato: {tool_name}")
        print(f"   📋 Argomenti: {arguments}")

        if tool_name in tool_map:
            try:
                result = tool_map[tool_name](**arguments)
                tool_results.append(result)
                print(f"   ✅ Risultato: {result}")
            except Exception as e:
                error_msg = f"Errore nell'esecuzione del tool {tool_name}: {e}"
                tool_results.append(error_msg)
                print(f"   ❌ {error_msg}")
        else:
            error_msg = f"Tool {tool_name} non riconosciuto"
            tool_results.append(error_msg)
            print(f"   ❌ {error_msg}")

    return tool_results


# ==============================================================================
# DEFINIZIONE STRUMENTI (TOOLS)
# ==============================================================================

@tool
def calcola(espressione: str) -> str:
    """Esegue calcoli matematici sicuri.
    
    Args:
        espressione: Espressione matematica da calcolare (es: "2 + 3 * 4")
        
    Returns:
        Risultato del calcolo
    """
    try:
        # Valida input (solo operazioni matematiche sicure)
        allowed_chars = set('0123456789+-*/(). ')
        if not all(c in allowed_chars for c in espressione):
            return "Errore: Caratteri non permessi. Usa solo numeri e operatori +-*/()"
        
        # Esegue il calcolo
        result = eval(espressione)
        return f"Risultato: {result}"
        
    except Exception as e:
        return f"Errore nel calcolo: {str(e)}"


@tool
def cerca_informazioni(query: str) -> str:
    """Simula una ricerca web per trovare informazioni.
    
    Args:
        query: Query di ricerca
        
    Returns:
        Risultati della ricerca simulata
    """
    try:
        # Simula ricerca web con risultati fittizi
        query_lower = query.lower()
        
        if "python" in query_lower:
            results = [
                "Python è un linguaggio di programmazione interpretato",
                "Guida ufficiale Python: python.org",
                "Tutorial Python per principianti disponibili online"
            ]
        elif "ai" in query_lower or "artificial intelligence" in query_lower:
            results = [
                "L'Intelligenza Artificiale è un campo dell'informatica",
                "Machine Learning è un sottoinsieme dell'AI",
                "Applicazioni AI: riconoscimento immagini, NLP, robotica"
            ]
        else:
            results = [
                f"Risultati per '{query}' non disponibili in questa demo",
                "Questo è un simulatore di ricerca web",
                "In un ambiente reale, qui ci sarebbero risultati reali"
            ]
        
        return f"Risultati ricerca per '{query}':\n" + "\n".join(f"- {r}" for r in results)
        
    except Exception as e:
        return f"Errore nella ricerca: {str(e)}"


# Sistema di file simulato globale
FILES_SYSTEM = {
    "docs/": ["README.md", "guide.txt"],
    "src/": ["main.py", "utils.py"],
    "data/": ["dataset.csv", "config.json"]
}

@tool
def gestisci_file(comando: str, percorso: str) -> str:
    """Gestisce file e directory in un sistema simulato.
    
    Args:
        comando: Operazione da eseguire (list, create, delete)
        percorso: Percorso del file o directory
        
    Returns:
        Risultato dell'operazione
    """
    try:
        global FILES_SYSTEM
        
        if comando == "list":
            if percorso in FILES_SYSTEM:
                files_list = FILES_SYSTEM[percorso]
                return f"Contenuto di {percorso}:\n" + "\n".join(f"- {f}" for f in files_list)
            else:
                return f"Directory {percorso} non trovata"
        
        elif comando == "create":
            # Simula creazione file
            filename = percorso.split("/")[-1] if "/" in percorso else percorso
            directory = "/".join(percorso.split("/")[:-1]) + "/" if "/" in percorso else ""
            
            if directory and directory not in FILES_SYSTEM:
                FILES_SYSTEM[directory] = []
            
            if directory:
                FILES_SYSTEM[directory].append(filename)
            else:
                if "root/" not in FILES_SYSTEM:
                    FILES_SYSTEM["root/"] = []
                FILES_SYSTEM["root/"].append(filename)
            
            return f"File {filename} creato con successo"
        
        elif comando == "delete":
            # Simula eliminazione file
            filename = percorso.split("/")[-1] if "/" in percorso else percorso
            directory = "/".join(percorso.split("/")[:-1]) + "/" if "/" in percorso else ""
            
            if directory and directory in FILES_SYSTEM:
                if filename in FILES_SYSTEM[directory]:
                    FILES_SYSTEM[directory].remove(filename)
                    return f"File {filename} eliminato con successo"
            
            return f"File {percorso} non trovato"
        
        else:
            return f"Comando '{comando}' non supportato. Usa: list, create, delete"
            
    except Exception as e:
        return f"Errore nella gestione file: {str(e)}"


# ==============================================================================
# CREAZIONE CLIENT CON STRUMENTI
# ==============================================================================

def create_calculator_client():
    """Crea un client specializzato in calcoli matematici"""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""Sei un assistente specializzato in calcoli matematici. 
        Usa sempre lo strumento calcola per eseguire calcoli.
        Fornisci risposte precise e spiega i passaggi quando possibile."""
    )
    
    if not client:
        raise ValueError("Client OpenAI non disponibile")
    
    return client


def create_research_client():
    """Crea un client specializzato in ricerche e analisi"""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""Sei un assistente di ricerca e analisi. 
        Usa cerca_informazioni per cercare informazioni e gestisci_file per gestire file.
        Organizza le informazioni in modo chiaro e strutturato."""
    )
    
    if not client:
        raise ValueError("Client OpenAI non disponibile")
    
    return client


def create_multi_tool_client():
    """Crea un client con accesso a tutti gli strumenti"""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        system_prompt="""Sei un assistente versatile con accesso a molteplici strumenti.
        Hai a disposizione:
        - calcola: per calcoli matematici
        - cerca_informazioni: per ricerche web simulate
        - gestisci_file: per gestione file e directory
        
        Analizza la richiesta dell'utente e scegli lo strumento più appropriato.
        Se necessario, combina più strumenti per completare task complessi.
        Spiega sempre quale strumento stai usando e perché."""
    )
    
    if not client:
        raise ValueError("Client OpenAI non disponibile")
    
    return client


# ==============================================================================
# DEMO E ESEMPI PRATICI
# ==============================================================================

def demo_single_tool_client():
    """Dimostra l'uso di un client con strumento specializzato"""
    print_section("CLIENT CON STRUMENTO SPECIALIZZATO - Calculator")
    
    try:
        client = create_calculator_client()
        print(f"✅ Client matematico creato")
        
        # Aggiungi i tool al client
        tools = [calcola]
        
        # Test calcoli semplici
        queries = [
            "Calcola 15 + 27 * 3",
            "Quanto fa (100 - 25) / 5?",
            "Calcola l'area di un cerchio con raggio 7 (usa 3.14 per pi greco)"
        ]
        
        for query in queries:
            print_subsection(f"Query: {query}")
            
            try:
                response = client.invoke(
                    input=query, 
                    tools=tools, 
                    tool_choice="auto"
                )
                
                # Esegui tool se presenti
                tool_results = execute_tool_calls(response, tools)
                
                # Se c'è una risposta testuale, mostrala
                if response.text.strip():
                    print(f"🤖 Assistente: {response.text}")
                elif tool_results:
                    print(f"🤖 Assistente: Ho eseguito l'operazione: {tool_results[0]}")
                
            except Exception as e:
                print(f"   ❌ Errore query: {e}")
            
            print()
            
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_multi_tool_client():
    """Dimostra l'uso di un client con più strumenti"""
    print_section("CLIENT MULTI STRUMENTO - Research Assistant")
    
    try:
        client = create_research_client()
        print(f"✅ Client di ricerca creato")
        
        # Aggiungi tutti i tool
        tools = [cerca_informazioni, gestisci_file]
        
        # Test ricerche e gestione file
        queries = [
            "Cerca informazioni su Python e poi crea un file chiamato python_info.txt nella directory docs/",
            "Lista i file nella directory docs/ e poi cerca informazioni sull'AI",
            "Crea un file chiamato research_summary.txt nella directory data/"
        ]
        
        for query in queries:
            print_subsection(f"Query: {query}")
            
            try:
                response = client.invoke(
                    input=query, 
                    tools=tools, 
                    tool_choice="auto"
                )
                
                # Esegui tool se presenti
                tool_results = execute_tool_calls(response, tools)
                
                # Mostra risposta
                if response.text.strip():
                    print(f"🤖 Assistente: {response.text}")
                elif tool_results:
                    print(f"🤖 Assistente: Ho completato l'operazione: {'; '.join(tool_results[:2])}")
                
            except Exception as e:
                print(f"   ❌ Errore query: {e}")
            
            print()
            
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_complex_workflow():
    """Dimostra un workflow complesso con client multi-tool"""
    print_section("WORKFLOW COMPLESSO - Multi-Tool Client")
    
    try:
        client = create_multi_tool_client()
        print(f"✅ Client multi-tool creato con tutti gli strumenti disponibili")
        
        # Tutti i tool disponibili
        tools = [calcola, cerca_informazioni, gestisci_file]
        
        # Workflow complesso: ricerca + calcolo + gestione file
        complex_query = """
        Esegui questo workflow:
        1. Cerca informazioni su machine learning
        2. Calcola quanti anni sono passati dal 1990 al 2025 (2025 - 1990)
        3. Crea un file chiamato ml_summary.txt nella directory docs/
        4. Calcola la media dei numeri: 85, 92, 78, 96, 88 (somma diviso 5)
        5. Lista i file nella directory docs/ per verificare la creazione
        """
        
        print_subsection("Workflow complesso multi-step")
        print(f"Query: {complex_query.strip()}")
        
        try:
            response = client.invoke(
                input=complex_query, 
                tools=tools, 
                tool_choice="auto"
            )
            
            # Esegui tool se presenti
            tool_results = execute_tool_calls(response, tools)
            
            # Mostra risposta finale
            if response.text.strip():
                print(f"\n🤖 Assistente: {response.text}")
            elif tool_results:
                print(f"\n🤖 Assistente: Workflow completato con {len(tool_results)} operazioni")
                    
        except Exception as e:
            print(f"   ❌ Errore workflow: {e}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_client_memory():
    """Dimostra l'uso della memoria con client multi-tool"""
    print_section("CLIENT CON MEMORIA - Conversazione Multi-Tool")
    
    try:
        client = create_multi_tool_client()
        memory = Memory()
        tools = [calcola, cerca_informazioni, gestisci_file]
        
        print(f"✅ Client multi-tool con memoria attivata")
        
        # Conversazione che utilizza diversi strumenti nel tempo
        conversation = [
            "Ciao! Sono Marco e sto lavorando su un progetto di AI",
            "Cerca informazioni sui framework Python per AI",
            "Calcola quanto costa un progetto AI se spendo 500 euro al mese per 2 anni (500 * 24)",
            "Crea un file chiamato project_plan.txt nella directory docs/",
            "Ricordi il mio nome e cosa sto facendo?",
            "Calcola il ROI se il progetto genera 15000 euro di ricavi (15000 - 12000)"
        ]
        
        for i, user_input in enumerate(conversation, 1):
            print_subsection(f"Turno {i}")
            print(f"👤 Utente: {user_input}")
            
            # Aggiungi alla memoria
            memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
            
            try:
                # Invoca client con memoria
                response = client.invoke(
                    input="", 
                    memory=memory, 
                    tools=tools, 
                    tool_choice="auto"
                )
                memory.add_turn(response.content, ROLE.ASSISTANT)
                
                # Esegui tool se presenti
                tool_results = execute_tool_calls(response, tools)
                
                # Mostra risposta finale
                if response.text.strip():
                    print(f"🤖 Assistente: {response.text}")
                elif tool_results:
                    print(f"🤖 Assistente: {tool_results[0]}")
                        
            except Exception as e:
                print(f"   ❌ Errore turno: {e}")
                # Aggiungi messaggio di errore alla memoria
                memory.add_turn([TextBlock(content=f"Errore: {e}")], ROLE.ASSISTANT)
            
            print()
        
        # Statistiche conversazione
        print_subsection("Statistiche conversazione")
        print(f"   📚 Turni totali: {len(memory.memory)}")
        print(f"   💬 Blocchi totali: {len(list(memory.iter_blocks()))}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")


# ==============================================================================
# UTILITÀ E TESTING
# ==============================================================================

def test_tools_individually():
    """Testa ogni strumento individualmente"""
    print_section("TEST STRUMENTI INDIVIDUALI")
    
    # Test Calculator
    print_subsection("Test Tool: calcola")
    test_cases = ["2 + 2", "10 * 5", "(15 + 5) / 4"]
    
    for test_case in test_cases:
        result = calcola(test_case)
        print(f"Input: {test_case}")
        print(f"Output: {result}")
        print()
    
    # Test WebSearch
    print_subsection("Test Tool: cerca_informazioni")
    test_queries = ["Python programming", "Artificial Intelligence", "Machine Learning"]
    
    for query in test_queries:
        result = cerca_informazioni(query)
        print(f"Query: {query}")
        print(f"Output: {result}")
        print()
    
    # Test FileManager
    print_subsection("Test Tool: gestisci_file")
    test_commands = [
        ("list", "docs/"),
        ("create", "docs/test.txt"),
        ("list", "docs/"),
        ("delete", "docs/test.txt")
    ]
    
    for comando, percorso in test_commands:
        result = gestisci_file(comando, percorso)
        print(f"Comando: {comando} {percorso}")
        print(f"Output: {result}")
        print()


def show_available_tools():
    """Mostra tutti gli strumenti disponibili con descrizioni"""
    print_section("STRUMENTI DISPONIBILI")
    
    print_subsection("🔧 calcola")
    print(f"Descrizione: {calcola.description}")
    print(f"Nome: {calcola.name}")
    print()
    
    print_subsection("🔧 cerca_informazioni")
    print(f"Descrizione: {cerca_informazioni.description}")
    print(f"Nome: {cerca_informazioni.name}")
    print()
    
    print_subsection("🔧 gestisci_file")
    print(f"Descrizione: {gestisci_file.description}")
    print(f"Nome: {gestisci_file.name}")
    print()


# ==============================================================================
# MENU PRINCIPALE
# ==============================================================================

def show_main_menu():
    """Mostra il menu principale"""
    print_section("MULTI TOOL FRAMEWORK - DatapizzAI")
    
    print("""
Demo disponibili:

1. Test strumenti individuali → Verifica funzionamento base
2. Client specializzato → Calculator client con strumento matematico
3. Client multi strumento → Research client con search + file
4. Workflow complesso → Client con tutti gli strumenti
5. Client con memoria → Conversazione multi-turno
6. Mostra strumenti → Lista e descrizioni

0. Esci
    """)


def run_demo(choice: str):
    """Esegue la demo selezionata"""
    demos = {
        "1": test_tools_individually,
        "2": demo_single_tool_client,
        "3": demo_multi_tool_client,
        "4": demo_complex_workflow,
        "5": demo_client_memory,
        "6": show_available_tools
    }
    
    if choice in demos:
        print(f"\nAvvio demo {choice}...")
        try:
            demos[choice]()
        except KeyboardInterrupt:
            print("\n\nOperazione interrotta")
        except Exception as e:
            print(f"\nErrore durante esecuzione: {e}")
    else:
        print("Scelta non valida")


def main():
    """Funzione principale con menu interattivo"""
    
    # Verifica supporto OpenAI
    print("🔍 Verifica supporto OpenAI...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("""
⚠️ OPENAI_API_KEY non configurata!

Per utilizzare i client multi-tool, crea un file .env nella directory PizzAI/ con:

 OPENAI_API_KEY=sk-your-openai-key-here

Questa chiave è necessaria per tutte le demo dei client con strumenti.
        """)
        return
    
    print("✅ OPENAI_API_KEY configurata")
    
    # Menu principale
    while True:
        try:
            show_main_menu()
            choice = input("👉 Scegli un'opzione: ").strip()
            
            if choice == "0":
                print("👋 Arrivederci!")
                break
            
            run_demo(choice)
            
            input("\n⏸️ Premi INVIO per continuare...")
            
        except KeyboardInterrupt:
            print("\n\n👋 Uscita forzata. Arrivederci!")
            break
        except EOFError:
            print("\n👋 Input terminato. Arrivederci!")
            break
        except Exception as e:
            print(f"\n❌ Errore inaspettato: {e}")
            print("🔄 Riavvio menu...")


if __name__ == "__main__":
    main()
