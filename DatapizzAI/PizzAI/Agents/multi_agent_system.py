#!/usr/bin/env python3
"""
Multi Agent System - DatapizzAI
===============================

Sistema multi-agente dove diversi agenti specializzati collaborano per completare task complessi.
Ogni agente ha competenze specifiche e può comunicare con altri agenti.

Autore: Mirko Calcaterra
Data: 2025
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env nella directory parent
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Importazioni datapizzai
from datapizzai.clients import ClientFactory
from datapizzai.tools import Tool
from datapizzai.memory import Memory
from datapizzai.type import TextBlock, ROLE


@dataclass
class AgentMessage:
    """Messaggio tra agenti"""
    sender: str
    receiver: str
    content: str
    task_id: str
    message_type: str = "request"  # request, response, info


class MessageBus:
    """Sistema di messaggistica tra agenti"""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.subscribers: Dict[str, List[str]] = {}
    
    def send_message(self, message: AgentMessage):
        """Invia un messaggio"""
        self.messages.append(message)
        print(f"📨 {message.sender} → {message.receiver}: {message.content[:50]}...")
    
    def get_messages_for_agent(self, agent_name: str) -> List[AgentMessage]:
        """Ottieni messaggi per un agente specifico"""
        return [msg for msg in self.messages if msg.receiver == agent_name]
    
    def clear_messages_for_agent(self, agent_name: str):
        """Pulisce i messaggi per un agente"""
        self.messages = [msg for msg in self.messages if msg.receiver != agent_name]


# ==============================================================================
# DEFINIZIONE STRUMENTI SPECIALIZZATI
# ==============================================================================

@Tool
def calcola_avanzato(espressione: str, tipo_calcolo: str = "base") -> str:
    """Esegue calcoli matematici avanzati.
    
    Args:
        espressione: Espressione matematica
        tipo_calcolo: Tipo di calcolo (base, finanziario, statistico)
    
    Returns:
        Risultato del calcolo
    """
    try:
        import math
        import statistics
        
        # Aggiungi funzioni matematiche al namespace
        namespace = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'log': math.log, 'sqrt': math.sqrt, 'pi': math.pi,
            'e': math.e, 'pow': math.pow
        }
        
        if tipo_calcolo == "finanziario":
            # Calcoli finanziari (es: interesse composto)
            if "interesse_composto" in espressione:
                # Formato: interesse_composto(capitale, tasso, anni)
                return "Calcolo finanziario: usa la formula C*(1+r)^t"
        
        # Validazione sicurezza
        allowed_chars = set('0123456789+-*/(). sincostanloge,[]')
        if not all(c in allowed_chars for c in espressione.replace(' ', '')):
            return "Errore: Caratteri non permessi"
        
        result = eval(espressione, namespace)
        return f"Risultato {tipo_calcolo}: {result}"
        
    except Exception as e:
        return f"Errore calcolo: {str(e)}"


@Tool
def analizza_dati(dati: str, tipo_analisi: str = "base") -> str:
    """Analizza dati e fornisce statistiche.
    
    Args:
        dati: Dati da analizzare (formato JSON o lista)
        tipo_analisi: Tipo di analisi (base, avanzata, trend)
    
    Returns:
        Risultati dell'analisi
    """
    try:
        import json
        import statistics
        
        # Prova a parsare come JSON
        if dati.startswith('[') or dati.startswith('{'):
            data = json.loads(dati)
        else:
            # Assume lista di numeri separati da virgola
            data = [float(x.strip()) for x in dati.split(',')]
        
        if isinstance(data, list) and all(isinstance(x, (int, float)) for x in data):
            # Analisi numerica
            risultati = {
                "count": len(data),
                "media": statistics.mean(data),
                "mediana": statistics.median(data),
                "min": min(data),
                "max": max(data)
            }
            
            if tipo_analisi == "avanzata":
                risultati.update({
                    "deviazione_standard": statistics.stdev(data) if len(data) > 1 else 0,
                    "varianza": statistics.variance(data) if len(data) > 1 else 0
                })
            
            return f"Analisi {tipo_analisi}: {json.dumps(risultati, indent=2)}"
        
        return f"Analisi {tipo_analisi} completata per {len(data)} elementi"
        
    except Exception as e:
        return f"Errore analisi: {str(e)}"


@Tool
def cerca_informazioni_avanzate(query: str, dominio: str = "generale") -> str:
    """Cerca informazioni specializzate per dominio.
    
    Args:
        query: Query di ricerca
        dominio: Dominio specializzato (tech, business, science)
    
    Returns:
        Informazioni specializzate
    """
    query_lower = query.lower()
    
    if dominio == "tech":
        if "python" in query_lower:
            return """Informazioni Tech - Python:
- Linguaggio interpretato, dinamico
- Eccellente per AI/ML, web development, automation
- Librerie principali: NumPy, Pandas, TensorFlow, Django
- Versione attuale: 3.12+"""
        
        elif "ai" in query_lower or "machine learning" in query_lower:
            return """Informazioni Tech - AI/ML:
- Framework principali: TensorFlow, PyTorch, Scikit-learn
- Tipi: Supervised, Unsupervised, Reinforcement Learning
- Applicazioni: NLP, Computer Vision, Predictive Analytics
- Trend: Large Language Models, Generative AI"""
    
    elif dominio == "business":
        if "roi" in query_lower or "investimento" in query_lower:
            return """Informazioni Business - ROI:
- ROI = (Guadagno - Costo) / Costo * 100
- Metriche correlate: ROAS, IRR, NPV
- Timeframe tipici: 1-3 anni per progetti tech
- Benchmark settoriali variano 15-30%"""
    
    elif dominio == "science":
        if "statistica" in query_lower:
            return """Informazioni Science - Statistica:
- Statistica descrittiva: media, mediana, deviazione
- Statistica inferenziale: test ipotesi, intervalli confidenza
- Distribuzione normale: 68-95-99.7 rule
- P-value: soglia significatività tipica 0.05"""
    
    return f"Informazioni {dominio} per '{query}': ricerca in corso..."


@Tool
def genera_report(titolo: str, contenuto: str, formato: str = "markdown") -> str:
    """Genera report strutturati.
    
    Args:
        titolo: Titolo del report
        contenuto: Contenuto del report
        formato: Formato output (markdown, json, text)
    
    Returns:
        Report formattato
    """
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if formato == "markdown":
        report = f"""# {titolo}

**Generato il:** {timestamp}

## Contenuto

{contenuto}

---
*Report generato automaticamente dal sistema multi-agente*
"""
    
    elif formato == "json":
        report_data = {
            "titolo": titolo,
            "timestamp": timestamp,
            "contenuto": contenuto,
            "formato": formato
        }
        report = json.dumps(report_data, indent=2, ensure_ascii=False)
    
    else:  # text
        report = f"""{titolo}
{'=' * len(titolo)}

Generato: {timestamp}

{contenuto}
"""
    
    return f"Report '{titolo}' generato in formato {formato}"


@Tool
def coordina_task(task_description: str, agenti_richiesti: str) -> str:
    """Coordina task tra più agenti.
    
    Args:
        task_description: Descrizione del task
        agenti_richiesti: Lista agenti necessari (separati da virgola)
    
    Returns:
        Piano di coordinazione
    """
    agenti = [a.strip() for a in agenti_richiesti.split(',')]
    
    piano = f"""Piano di coordinazione per: {task_description}

Agenti coinvolti: {', '.join(agenti)}

Fasi suggerite:
1. Analisi iniziale - {agenti[0] if agenti else 'Coordinator'}
2. Elaborazione dati - {agenti[1] if len(agenti) > 1 else 'DataAnalyst'}
3. Generazione risultati - {agenti[-1] if agenti else 'Reporter'}

Coordinazione attiva."""
    
    return piano


# ==============================================================================
# DEFINIZIONE AGENTI SPECIALIZZATI
# ==============================================================================

class SpecializedAgent:
    """Agente specializzato con competenze specifiche"""
    
    def __init__(self, name: str, specialization: str, tools: List, system_prompt: str, message_bus: MessageBus):
        self.name = name
        self.specialization = specialization
        self.tools = tools
        self.message_bus = message_bus
        self.memory = Memory()
        
        # Crea client OpenAI
        self.client = ClientFactory.create(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            system_prompt=system_prompt
        )
        
        if not self.client:
            raise ValueError(f"❌ Impossibile creare client per {name}")
    
    def process_task(self, task: str, task_id: str = "default") -> str:
        """Elabora un task utilizzando i propri strumenti"""
        
        print(f"\n🤖 {self.name} ({self.specialization}) elabora: {task[:50]}...")
        
        # Controlla messaggi da altri agenti
        messages = self.message_bus.get_messages_for_agent(self.name)
        context = ""
        if messages:
            context = f"\nMessaggi ricevuti:\n" + "\n".join([f"- {msg.sender}: {msg.content}" for msg in messages])
            self.message_bus.clear_messages_for_agent(self.name)
        
        # Aggiungi task alla memoria
        full_task = task + context
        self.memory.add_turn([TextBlock(content=full_task)], ROLE.USER)
        
        try:
            # Usa input diretto invece della memoria per evitare problemi con tool calls
            response = self.client.invoke(
                input=full_task,
                tools=self.tools,
                tool_choice="auto"
            )
            
            # Esegui tool se presenti
            tool_results = self._execute_tool_calls(response)
            
            # Determina output finale
            if response.text.strip():
                result = response.text
            elif tool_results:
                result = f"Operazioni completate: {'; '.join(tool_results[:2])}"
            else:
                result = "Task elaborato senza strumenti specifici"
            
            print(f"✅ {self.name}: {result[:100]}...")
            return result
            
        except Exception as e:
            error_msg = f"Errore in {self.name}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def _execute_tool_calls(self, response) -> List[str]:
        """Esegue i tool call presenti nella risposta"""
        tool_results = []
        
        # Mappa dei tool disponibili
        tool_map = {tool.name: tool for tool in self.tools}
        
        for block in response.content:
            if hasattr(block, 'name') and hasattr(block, 'arguments'):
                tool_name = block.name
                arguments = block.arguments
                
                if tool_name in tool_map:
                    try:
                        result = tool_map[tool_name](**arguments)
                        tool_results.append(result)
                        print(f"   🔧 {tool_name}: {result[:50]}...")
                        

                        
                    except Exception as e:
                        error_msg = f"Errore tool {tool_name}: {e}"
                        tool_results.append(error_msg)
                        print(f"   ❌ {error_msg}")
        
        return tool_results
    
    def send_message_to_agent(self, receiver: str, content: str, task_id: str, message_type: str = "info"):
        """Invia messaggio a un altro agente"""
        message = AgentMessage(
            sender=self.name,
            receiver=receiver,
            content=content,
            task_id=task_id,
            message_type=message_type
        )
        self.message_bus.send_message(message)


class MultiAgentSystem:
    """Sistema di coordinazione multi-agente"""
    
    def __init__(self):
        self.message_bus = MessageBus()
        self.agents: Dict[str, SpecializedAgent] = {}
        self._create_agents()
    
    def _create_agents(self):
        """Crea gli agenti specializzati"""
        
        # Agente Matematico
        math_agent = SpecializedAgent(
            name="MathExpert",
            specialization="Matematica e Calcoli",
            tools=[calcola_avanzato],
            system_prompt="""Sei un esperto matematico. Risolvi problemi matematici complessi, 
            calcoli finanziari e statistici. Usa sempre il tool calcola_avanzato per operazioni precise.
            Comunica con altri agenti quando serve supporto per analisi dati o ricerche.""",
            message_bus=self.message_bus
        )
        
        # Agente Analista Dati
        data_agent = SpecializedAgent(
            name="DataAnalyst",
            specialization="Analisi Dati e Statistiche",
            tools=[analizza_dati, calcola_avanzato],
            system_prompt="""Sei un analista dati esperto. Elabori dataset, calcoli statistiche,
            identifichi trend e pattern. Collabora con MathExpert per calcoli complessi e con
            ResearchAgent per contesto informativo.""",
            message_bus=self.message_bus
        )
        
        # Agente Ricercatore
        research_agent = SpecializedAgent(
            name="ResearchAgent",
            specialization="Ricerca e Informazioni",
            tools=[cerca_informazioni_avanzate],
            system_prompt="""Sei un ricercatore specializzato. Fornisci informazioni dettagliate
            su tecnologia, business e scienza. Supporti altri agenti con contesto e dati di background.
            Specializzati per dominio in base alla richiesta.""",
            message_bus=self.message_bus
        )
        
        # Agente Coordinatore
        coordinator_agent = SpecializedAgent(
            name="Coordinator",
            specialization="Coordinazione e Pianificazione",
            tools=[coordina_task, genera_report],
            system_prompt="""Sei il coordinatore del sistema multi-agente. Pianifichi task complessi,
            assegni lavoro agli agenti specializzati, coordini la collaborazione e generi report finali.
            Hai visione d'insieme di tutte le competenze disponibili.""",
            message_bus=self.message_bus
        )
        
        # Registra agenti
        self.agents = {
            "MathExpert": math_agent,
            "DataAnalyst": data_agent, 
            "ResearchAgent": research_agent,
            "Coordinator": coordinator_agent
        }
        
        print("🌟 Sistema Multi-Agente inizializzato:")
        for name, agent in self.agents.items():
            print(f"   - {name}: {agent.specialization}")
    
    def execute_complex_task(self, task_description: str) -> Dict[str, Any]:
        """Esegue un task complesso coordinando più agenti"""
        
        print(f"\n{'='*70}")
        print(f"🎯 TASK COMPLESSO: {task_description}")
        print(f"{'='*70}")
        
        task_id = f"task_{len(self.message_bus.messages)}"
        results = {}
        
        # Fase 1: Coordinatore analizza il task
        coordinator = self.agents["Coordinator"]
        coordination_plan = coordinator.process_task(
            f"Analizza questo task complesso e crea un piano: {task_description}", 
            task_id
        )
        results["coordination_plan"] = coordination_plan
        
        # Fase 2: Esecuzione specializzata basata sul tipo di task
        if any(keyword in task_description.lower() for keyword in ["calcola", "matematica", "formula"]):
            # Task matematico
            math_result = self.agents["MathExpert"].process_task(task_description, task_id)
            results["math_analysis"] = math_result
            
            # Invia risultato al coordinatore
            self.agents["MathExpert"].send_message_to_agent(
                "Coordinator", f"Calcolo completato: {math_result}", task_id
            )
        
        if any(keyword in task_description.lower() for keyword in ["dati", "analisi", "statistiche"]):
            # Task di analisi dati
            data_result = self.agents["DataAnalyst"].process_task(task_description, task_id)
            results["data_analysis"] = data_result
            
            # Invia risultato al coordinatore
            self.agents["DataAnalyst"].send_message_to_agent(
                "Coordinator", f"Analisi completata: {data_result}", task_id
            )
        
        if any(keyword in task_description.lower() for keyword in ["cerca", "informazioni", "ricerca"]):
            # Task di ricerca
            research_result = self.agents["ResearchAgent"].process_task(task_description, task_id)
            results["research_findings"] = research_result
            
            # Invia risultato al coordinatore
            self.agents["ResearchAgent"].send_message_to_agent(
                "Coordinator", f"Ricerca completata: {research_result}", task_id
            )
        
        # Fase 3: Coordinatore genera report finale
        if len(results) > 1:
            summary = "\n".join([f"{k}: {v[:100]}..." for k, v in results.items()])
            final_report = coordinator.process_task(
                f"Genera un report finale per il task '{task_description}' basato su: {summary}",
                task_id
            )
            results["final_report"] = final_report
        
        return results
    
    def collaborative_analysis(self, data: str, research_topic: str) -> Dict[str, Any]:
        """Esempio di analisi collaborativa tra agenti"""
        
        print(f"\n{'='*70}")
        print(f"🤝 ANALISI COLLABORATIVA")
        print(f"Dati: {data[:50]}...")
        print(f"Ricerca: {research_topic}")
        print(f"{'='*70}")
        
        results = {}
        task_id = "collaborative_analysis"
        
        # 1. DataAnalyst analizza i dati
        data_analysis = self.agents["DataAnalyst"].process_task(
            f"Analizza questi dati: {data}", task_id
        )
        results["data_analysis"] = data_analysis
        
        # 2. ResearchAgent cerca informazioni correlate
        research_findings = self.agents["ResearchAgent"].process_task(
            f"Cerca informazioni su: {research_topic}", task_id
        )
        results["research_findings"] = research_findings
        
        # 3. MathExpert fa calcoli se necessari
        if "calcola" in data_analysis.lower() or any(char in data for char in "0123456789"):
            math_analysis = self.agents["MathExpert"].process_task(
                f"Esegui calcoli avanzati sui dati: {data}", task_id
            )
            results["math_analysis"] = math_analysis
        
        # 4. Coordinator sintetizza tutto
        synthesis = self.agents["Coordinator"].process_task(
            f"Sintetizza l'analisi collaborativa su '{research_topic}' con dati '{data}' e risultati degli agenti",
            task_id
        )
        results["synthesis"] = synthesis
        
        return results


# ==============================================================================
# DEMO E ESEMPI INTERATTIVI
# ==============================================================================

def demo_simple_collaboration():
    """Demo di collaborazione semplice tra agenti"""
    print_section("COLLABORAZIONE SEMPLICE")
    
    system = MultiAgentSystem()
    
    # Esempio 1: Task matematico
    result1 = system.execute_complex_task(
        "Calcola il ROI di un investimento di 10000€ che genera 2500€ all'anno per 3 anni"
    )
    
    print(f"\n📊 Risultati Task 1:")
    for key, value in result1.items():
        print(f"   {key}: {value[:100]}...")
    
    # Esempio 2: Task di analisi dati
    result2 = system.execute_complex_task(
        "Analizza questi dati di vendite: 1200,1350,980,1450,1600,1100,1750 e calcola trend"
    )
    
    print(f"\n📊 Risultati Task 2:")
    for key, value in result2.items():
        print(f"   {key}: {value[:100]}...")


def demo_advanced_collaboration():
    """Demo di collaborazione avanzata"""
    print_section("COLLABORAZIONE AVANZATA")
    
    system = MultiAgentSystem()
    
    # Analisi collaborativa complessa
    result = system.collaborative_analysis(
        data="150,200,175,220,190,240,210,180,260,230",
        research_topic="trend di crescita nel settore tech"
    )
    
    print(f"\n📊 Risultati Analisi Collaborativa:")
    for key, value in result.items():
        print(f"   {key}: {value[:150]}...")


def demo_message_passing():
    """Demo del sistema di messaggistica tra agenti"""
    print_section("SISTEMA MESSAGGISTICA")
    
    system = MultiAgentSystem()
    
    # Simula scambio di messaggi
    math_agent = system.agents["MathExpert"]
    data_agent = system.agents["DataAnalyst"]
    
    # MathExpert invia risultato a DataAnalyst
    math_agent.send_message_to_agent(
        "DataAnalyst", 
        "Ho calcolato media=205.5 per i tuoi dati. Serve analisi varianza?",
        "demo_task"
    )
    
    # DataAnalyst elabora con contesto del messaggio
    response = data_agent.process_task(
        "Analizza varianza e deviazione standard per i dati ricevuti",
        "demo_task"
    )
    
    print(f"\n📨 Risposta con contesto: {response[:200]}...")


def print_section(title: str):
    """Stampa una sezione formattata"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")


def show_main_menu():
    """Mostra il menu principale"""
    print_section("SISTEMA MULTI-AGENTE - DatapizzAI")
    
    print("""
Demo disponibili:

1. Collaborazione semplice → Task coordinati tra agenti
2. Collaborazione avanzata → Analisi collaborative complesse  
3. Sistema messaggistica → Comunicazione inter-agente
4. Task personalizzato → Inserisci il tuo task
5. Mostra agenti → Lista agenti e competenze

0. Esci
    """)


def run_demo(choice: str):
    """Esegue la demo selezionata"""
    demos = {
        "1": demo_simple_collaboration,
        "2": demo_advanced_collaboration,
        "3": demo_message_passing,
        "4": demo_custom_task,
        "5": show_agents_info
    }
    
    if choice in demos:
        print(f"\nAvvio demo {choice}...")
        try:
            demos[choice]()
        except Exception as e:
            print(f"❌ Errore demo: {e}")
    else:
        print("❌ Opzione non valida. Scegli un numero da 0 a 5.")


def demo_custom_task():
    """Demo con task personalizzato dall'utente"""
    print_section("TASK PERSONALIZZATO")
    
    task = input("Inserisci il tuo task complesso: ").strip()
    if not task:
        print("❌ Task non inserito")
        return
    
    system = MultiAgentSystem()
    result = system.execute_complex_task(task)
    
    print(f"\n📊 Risultati Task Personalizzato:")
    for key, value in result.items():
        print(f"   {key}: {value[:200]}...")


def show_agents_info():
    """Mostra informazioni sugli agenti"""
    print_section("AGENTI DISPONIBILI")
    
    system = MultiAgentSystem()
    
    for name, agent in system.agents.items():
        print(f"\n🤖 {name}")
        print(f"   Specializzazione: {agent.specialization}")
        print(f"   Strumenti: {[tool.name for tool in agent.tools]}")


def main():
    """Funzione principale con menu interattivo"""
    
    # Verifica supporto OpenAI
    print("🔍 Verifica supporto OpenAI...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("""
⚠️ OPENAI_API_KEY non configurata!

Per utilizzare il sistema multi-agente, crea un file .env nella directory PizzAI/ con:

 OPENAI_API_KEY=sk-your-openai-key-here

Questa chiave è necessaria per tutti gli agenti del sistema.
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
