#!/usr/bin/env python3
"""
Multi Agent-Tool Framework - DatapizzAI
========================================

Questo script dimostra come creare e utilizzare agenti multi-tool con il framework datapizzai.
Gli agenti possono utilizzare diversi strumenti per completare task complessi.

Autore: Marco Calcaterra
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
from datapizzai.agents import Agent
from datapizzai.tools import Tool, ToolResult
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


# ==============================================================================
# DEFINIZIONE STRUMENTI (TOOLS)
# ==============================================================================

class CalculatorTool(Tool):
    """Strumento per calcoli matematici"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Esegue calcoli matematici. Input: espressione matematica come stringa",
            input_schema={"type": "string", "description": "Espressione matematica da calcolare"}
        )
    
    def execute(self, input_data: str) -> ToolResult:
        """Esegue il calcolo matematico"""
        try:
            # Valida input (solo operazioni matematiche sicure)
            allowed_chars = set('0123456789+-*/(). ')
            if not all(c in allowed_chars for c in input_data):
                return ToolResult(
                    success=False,
                    error="Caratteri non permessi. Usa solo numeri e operatori +-*/()"
                )
            
            # Esegue il calcolo
            result = eval(input_data)
            
            return ToolResult(
                success=True,
                result=f"Risultato: {result}",
                metadata={"expression": input_data, "result": result}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Errore nel calcolo: {str(e)}"
            )


class WebSearchTool(Tool):
    """Strumento per ricerche web simulate"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Simula una ricerca web. Input: query di ricerca",
            input_schema={"type": "string", "description": "Query di ricerca"}
        )
    
    def execute(self, input_data: str) -> ToolResult:
        """Simula una ricerca web"""
        try:
            # Simula ricerca web con risultati fittizi
            query = input_data.lower()
            
            if "python" in query:
                results = [
                    "Python è un linguaggio di programmazione interpretato",
                    "Guida ufficiale Python: python.org",
                    "Tutorial Python per principianti disponibili online"
                ]
            elif "ai" in query or "artificial intelligence" in query:
                results = [
                    "L'Intelligenza Artificiale è un campo dell'informatica",
                    "Machine Learning è un sottoinsieme dell'AI",
                    "Applicazioni AI: riconoscimento immagini, NLP, robotica"
                ]
            else:
                results = [
                    f"Risultati per '{input_data}' non disponibili in questa demo",
                    "Questo è un simulatore di ricerca web",
                    "In un ambiente reale, qui ci sarebbero risultati reali"
                ]
            
            return ToolResult(
                success=True,
                result=f"Risultati ricerca per '{input_data}':\n" + "\n".join(f"- {r}" for r in results),
                metadata={"query": input_data, "results_count": len(results)}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Errore nella ricerca: {str(e)}"
            )


class FileManagerTool(Tool):
    """Strumento per gestione file simulata"""
    
    def __init__(self):
        super().__init__(
            name="file_manager",
            description="Gestisce file e directory. Input: comando (list, create, delete) e parametri",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "enum": ["list", "create", "delete"]},
                    "path": {"type": "string", "description": "Percorso file/directory"}
                }
            }
        )
        self.files = {
            "docs/": ["README.md", "guide.txt"],
            "src/": ["main.py", "utils.py"],
            "data/": ["dataset.csv", "config.json"]
        }
    
    def execute(self, input_data: Dict[str, str]) -> ToolResult:
        """Esegue comandi di gestione file"""
        try:
            command = input_data.get("command")
            path = input_data.get("path", "")
            
            if command == "list":
                if path in self.files:
                    files_list = self.files[path]
                    return ToolResult(
                        success=True,
                        result=f"Contenuto di {path}:\n" + "\n".join(f"- {f}" for f in files_list),
                        metadata={"command": command, "path": path, "files": files_list}
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=f"Directory {path} non trovata"
                    )
            
            elif command == "create":
                # Simula creazione file
                filename = path.split("/")[-1] if "/" in path else path
                directory = "/".join(path.split("/")[:-1]) + "/" if "/" in path else ""
                
                if directory and directory not in self.files:
                    self.files[directory] = []
                
                if directory:
                    self.files[directory].append(filename)
                else:
                    if "root" not in self.files:
                        self.files["root"] = []
                    self.files["root"].append(filename)
                
                return ToolResult(
                    success=True,
                    result=f"File {filename} creato con successo",
                    metadata={"command": command, "path": path, "created": True}
                )
            
            elif command == "delete":
                # Simula eliminazione file
                filename = path.split("/")[-1] if "/" in path else path
                directory = "/".join(path.split("/")[:-1]) + "/" if "/" in path else ""
                
                if directory and directory in self.files:
                    if filename in self.files[directory]:
                        self.files[directory].remove(filename)
                        return ToolResult(
                            success=True,
                            result=f"File {filename} eliminato con successo",
                            metadata={"command": command, "path": path, "deleted": True}
                        )
                
                return ToolResult(
                    success=False,
                    error=f"File {path} non trovato"
                )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"Comando '{command}' non supportato"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Errore nella gestione file: {str(e)}"
            )


# ==============================================================================
# CREAZIONE AGENTI SPECIALIZZATI
# ==============================================================================

def create_calculator_agent() -> Agent:
    """Crea un agente specializzato in calcoli matematici"""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    
    if not client:
        raise ValueError("Client OpenAI non disponibile")
    
    calculator_tool = CalculatorTool()
    
    agent = Agent(
        name="MathAgent",
        client=client,
        tools=[calculator_tool],
        system_prompt="""Sei un agente specializzato in calcoli matematici. 
        Usa sempre lo strumento calculator per eseguire calcoli.
        Fornisci risposte precise e spiega i passaggi quando possibile."""
    )
    
    return agent


def create_research_agent() -> Agent:
    """Crea un agente specializzato in ricerche e analisi"""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    
    if not client:
        raise ValueError("Client OpenAI non disponibile")
    
    search_tool = WebSearchTool()
    file_tool = FileManagerTool()
    
    agent = Agent(
        name="ResearchAgent",
        client=client,
        tools=[search_tool, file_tool],
        system_prompt="""Sei un agente di ricerca e analisi. 
        Usa web_search per cercare informazioni e file_manager per gestire file.
        Organizza le informazioni in modo chiaro e strutturato."""
    )
    
    return agent


def create_multi_tool_agent() -> Agent:
    """Crea un agente con accesso a tutti gli strumenti"""
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    
    if not client:
        raise ValueError("Client OpenAI non disponibile")
    
    all_tools = [
        CalculatorTool(),
        WebSearchTool(),
        FileManagerTool()
    ]
    
    agent = Agent(
        name="MultiToolAgent",
        client=client,
        tools=all_tools,
        system_prompt="""Sei un agente versatile con accesso a molteplici strumenti.
        Analizza la richiesta dell'utente e scegli lo strumento più appropriato.
        Se necessario, combina più strumenti per completare task complessi.
        Spiega sempre quale strumento stai usando e perché."""
    )
    
    return agent


# ==============================================================================
# DEMO E ESEMPI PRATICI
# ==============================================================================

def demo_single_tool_agent():
    """Dimostra l'uso di un agente con un singolo strumento"""
    print_section("AGENTE SINGOLO STRUMENTO - MathAgent")
    
    try:
        agent = create_calculator_agent()
        print(f"✅ Agente {agent.name} creato con strumento: {[t.name for t in agent.tools]}")
        
        # Test calcoli semplici
        queries = [
            "Calcola 15 + 27 * 3",
            "Quanto fa (100 - 25) / 5?",
            "Calcola l'area di un cerchio con raggio 7"
        ]
        
        for query in queries:
            print_subsection(f"Query: {query}")
            
            response = agent.invoke(query)
            print(f"🤖 {agent.name}: {response.text}")
            
            # Mostra uso strumento
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    print(f"   🔧 Strumento usato: {tool_call.tool_name}")
                    print(f"   📊 Risultato: {tool_call.result}")
            
            print()
            
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_multi_tool_agent():
    """Dimostra l'uso di un agente con più strumenti"""
    print_section("AGENTE MULTI STRUMENTO - ResearchAgent")
    
    try:
        agent = create_research_agent()
        print(f"✅ Agente {agent.name} creato con strumenti: {[t.name for t in agent.tools]}")
        
        # Test ricerche e gestione file
        queries = [
            "Cerca informazioni su Python e crea un file chiamato python_info.txt",
            "Lista i file nella directory docs/ e poi cerca informazioni sull'AI",
            "Crea un file chiamato research_summary.txt nella directory data/"
        ]
        
        for query in queries:
            print_subsection(f"Query: {query}")
            
            response = agent.invoke(query)
            print(f"🤖 {agent.name}: {response.text}")
            
            # Mostra uso strumenti
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    print(f"   🔧 Strumento: {tool_call.tool_name}")
                    print(f"   📊 Risultato: {tool_call.result}")
            
            print()
            
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_complex_workflow():
    """Dimostra un workflow complesso con agente multi-tool"""
    print_section("WORKFLOW COMPLESSO - MultiToolAgent")
    
    try:
        agent = create_multi_tool_agent()
        print(f"✅ Agente {agent.name} creato con tutti gli strumenti disponibili")
        
        # Workflow complesso: ricerca + calcolo + gestione file
        complex_query = """
        Esegui questo workflow:
        1. Cerca informazioni su machine learning
        2. Calcola quanti anni sono passati dal 1990 al 2025
        3. Crea un file chiamato ml_summary.txt nella directory docs/
        4. Calcola la media dei numeri: 85, 92, 78, 96, 88
        5. Lista i file nella directory docs/ per verificare la creazione
        """
        
        print_subsection("Workflow complesso multi-step")
        print(f"Query: {complex_query.strip()}")
        
        response = agent.invoke(complex_query)
        print(f"\n🤖 {agent.name}: {response.text}")
        
        # Mostra tutti gli strumenti utilizzati
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"\n📊 Strumenti utilizzati nel workflow:")
            for i, tool_call in enumerate(response.tool_calls, 1):
                print(f"   {i}. {tool_call.tool_name}: {tool_call.result}")
        
    except Exception as e:
        print(f"❌ Errore: {e}")


def demo_agent_memory():
    """Dimostra l'uso della memoria con agenti multi-tool"""
    print_section("AGENTE CON MEMORIA - Conversazione Multi-Tool")
    
    try:
        agent = create_multi_tool_agent()
        memory = Memory()
        
        print(f"✅ Agente {agent.name} con memoria attivata")
        
        # Conversazione che utilizza diversi strumenti nel tempo
        conversation = [
            "Ciao! Sono Marco e sto lavorando su un progetto di AI",
            "Cerca informazioni sui framework Python per AI",
            "Calcola quanto costa un progetto AI se spendo 500€ al mese per 2 anni",
            "Crea un file chiamato project_plan.txt nella directory docs/",
            "Ricordi il mio nome e cosa sto facendo?",
            "Calcola il ROI se il progetto genera 15000€ di ricavi"
        ]
        
        for i, user_input in enumerate(conversation, 1):
            print_subsection(f"Turno {i}")
            print(f"👤 Utente: {user_input}")
            
            # Aggiungi alla memoria
            memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
            
            # Invoca agente con memoria
            response = agent.invoke("", memory=memory)
            memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
            
            print(f"🤖 {agent.name}: {response.text}")
            
            # Mostra strumenti usati
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    print(f"   🔧 Strumento: {tool_call.tool_name}")
            
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
    print_subsection("Test CalculatorTool")
    calc_tool = CalculatorTool()
    test_cases = ["2 + 2", "10 * 5", "(15 + 5) / 4"]
    
    for test_case in test_cases:
        result = calc_tool.execute(test_case)
        print(f"Input: {test_case}")
        print(f"Output: {result.result if result.success else result.error}")
        print()
    
    # Test WebSearch
    print_subsection("Test WebSearchTool")
    search_tool = WebSearchTool()
    test_queries = ["Python programming", "Artificial Intelligence", "Machine Learning"]
    
    for query in test_queries:
        result = search_tool.execute(query)
        print(f"Query: {query}")
        print(f"Output: {result.result if result.success else result.error}")
        print()
    
    # Test FileManager
    print_subsection("Test FileManagerTool")
    file_tool = FileManagerTool()
    test_commands = [
        {"command": "list", "path": "docs/"},
        {"command": "create", "path": "docs/test.txt"},
        {"command": "list", "path": "docs/"},
        {"command": "delete", "path": "docs/test.txt"}
    ]
    
    for cmd in test_commands:
        result = file_tool.execute(cmd)
        print(f"Comando: {cmd}")
        print(f"Output: {result.result if result.success else result.error}")
        print()


def show_available_tools():
    """Mostra tutti gli strumenti disponibili con descrizioni"""
    print_section("STRUMENTI DISPONIBILI")
    
    tools = [
        CalculatorTool(),
        WebSearchTool(),
        FileManagerTool()
    ]
    
    for tool in tools:
        print_subsection(f"🔧 {tool.name}")
        print(f"Descrizione: {tool.description}")
        print(f"Schema input: {tool.input_schema}")
        print()


# ==============================================================================
# MENU PRINCIPALE
# ==============================================================================

def show_main_menu():
    """Mostra il menu principale"""
    print_section("MULTI AGENT-TOOL FRAMEWORK")
    
    print("""
Demo disponibili:

1. Test strumenti individuali → Verifica funzionamento base
2. Agente singolo strumento → MathAgent con calculator
3. Agente multi strumento → ResearchAgent con search + file
4. Workflow complesso → MultiToolAgent con tutti gli strumenti
5. Agente con memoria → Conversazione multi-turno
6. Mostra strumenti → Lista e descrizioni

0. Esci
    """)


def run_demo(choice: str):
    """Esegue la demo selezionata"""
    demos = {
        "1": test_tools_individually,
        "2": demo_single_tool_agent,
        "3": demo_multi_tool_agent,
        "4": demo_complex_workflow,
        "5": demo_agent_memory,
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

Per utilizzare gli agenti multi-tool, crea un file .env nella directory PizzAI/ con:

 OPENAI_API_KEY=sk-your-openai-key-here

Questa chiave è necessaria per tutte le demo degli agenti.
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
        except Exception as e:
            print(f"\n❌ Errore inaspettato: {e}")
            print("🔄 Riavvio menu...")


if __name__ == "__main__":
    main()
