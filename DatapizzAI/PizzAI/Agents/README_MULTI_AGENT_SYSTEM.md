# Multi Agent System - DatapizzAI

Sistema multi-agente dove diversi agenti specializzati collaborano per completare task complessi. Ogni agente ha competenze specifiche e può comunicare con altri agenti attraverso un sistema di messaggistica.

## Indice

1. [Concetti fondamentali](#concetti-fondamentali)
2. [Architettura del sistema](#architettura-del-sistema)
3. [Configurazione passo-passo](#configurazione-passo-passo)
4. [Agenti specializzati](#agenti-specializzati)
5. [Sistema di messaggistica](#sistema-di-messaggistica)
6. [Pattern di collaborazione](#pattern-di-collaborazione)
7. [Esempi pratici](#esempi-pratici)
8. [Estensione del sistema](#estensione-del-sistema)

## Concetti fondamentali

### Sistema Multi-Agente
Un sistema dove più agenti AI specializzati collaborano per risolvere problemi complessi:

- **Specializzazione**: Ogni agente ha competenze specifiche
- **Collaborazione**: Gli agenti comunicano e si coordinano
- **Coordinamento**: Un agente coordinatore gestisce task complessi
- **Messaggistica**: Sistema di comunicazione inter-agente

### Agente Specializzato
Ogni agente ha:
- **Nome e ruolo**: Identità specifica nel sistema
- **Strumenti**: Tool specializzati per il suo dominio
- **Client OpenAI**: Connessione AI per elaborazione
- **Memoria**: Contesto conversazionale
- **Comunicazione**: Capacità di inviare/ricevere messaggi

## Architettura del sistema

```
┌────────────────────────────────────────────────────────────┐
│                    MultiAgentSystem                        │
├────────────────────────────────────────────────────────────┤
│                    MessageBus                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ MathExpert  │ │DataAnalyst  │ │ResearchAgent│           │
│  │             │ │             │ │             │           │
│  │ • calcola   │ │ • analizza  │ │ • cerca     │           │
│  │   avanzato  │ │   dati      │ │   info      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Coordinator                            │   │
│  │                                                     │   │
│  │ • coordina_task                                     │   │
│  │ • genera_report                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

## Configurazione passo-passo

### Passo 1: Definizione strumenti specializzati

```python
from datapizzai.tools import Tool

@Tool
def calcola_avanzato(espressione: str, tipo_calcolo: str = "base") -> str:
    """Calcoli matematici avanzati con supporto finanziario/statistico."""
    import math
    
    namespace = {
        'sin': math.sin, 'cos': math.cos, 'sqrt': math.sqrt,
        'pi': math.pi, 'e': math.e
    }
    
    try:
        result = eval(espressione, namespace)
        return f"Risultato {tipo_calcolo}: {result}"
    except Exception as e:
        return f"Errore: {str(e)}"

@Tool
def analizza_dati(dati: str, tipo_analisi: str = "base") -> str:
    """Analisi statistica di dataset."""
    import json, statistics
    
    # Parsing dati
    if dati.startswith('['):
        data = json.loads(dati)
    else:
        data = [float(x.strip()) for x in dati.split(',')]
    
    risultati = {
        "media": statistics.mean(data),
        "mediana": statistics.median(data),
        "min": min(data),
        "max": max(data)
    }
    
    return f"Analisi {tipo_analisi}: {json.dumps(risultati, indent=2)}"
```

### Passo 2: Sistema di messaggistica

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class AgentMessage:
    """Messaggio tra agenti"""
    sender: str
    receiver: str
    content: str
    task_id: str
    message_type: str = "request"

class MessageBus:
    """Sistema di messaggistica centralizzato"""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
    
    def send_message(self, message: AgentMessage):
        self.messages.append(message)
        print(f"📨 {message.sender} → {message.receiver}: {message.content[:50]}...")
    
    def get_messages_for_agent(self, agent_name: str) -> List[AgentMessage]:
        return [msg for msg in self.messages if msg.receiver == agent_name]
```

### Passo 3: Creazione agente specializzato

```python
from datapizzai.clients import ClientFactory
from datapizzai.memory import Memory

class SpecializedAgent:
    def __init__(self, name: str, specialization: str, tools: List, 
                 system_prompt: str, message_bus: MessageBus):
        self.name = name
        self.specialization = specialization
        self.tools = tools
        self.message_bus = message_bus
        self.memory = Memory()
        
        # Client OpenAI specializzato
        self.client = ClientFactory.create(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            system_prompt=system_prompt
        )
    
    def process_task(self, task: str, task_id: str) -> str:
        """Elabora task con strumenti specializzati"""
        
        # Controlla messaggi da altri agenti
        messages = self.message_bus.get_messages_for_agent(self.name)
        context = ""
        if messages:
            context = "\nMessaggi ricevuti:\n" + "\n".join([
                f"- {msg.sender}: {msg.content}" for msg in messages
            ])
        
        # Elabora con contesto
        full_task = task + context
        self.memory.add_turn([TextBlock(content=full_task)], ROLE.USER)
        
        response = self.client.invoke(
            input="",
            memory=self.memory,
            tools=self.tools,
            tool_choice="auto"
        )
        
        # Esegui tool e genera risultato
        tool_results = self._execute_tool_calls(response)
        result = response.text or f"Operazioni: {'; '.join(tool_results[:2])}"
        
        return result
    
    def send_message_to_agent(self, receiver: str, content: str, task_id: str):
        """Comunica con altro agente"""
        message = AgentMessage(
            sender=self.name,
            receiver=receiver, 
            content=content,
            task_id=task_id
        )
        self.message_bus.send_message(message)
```

### Passo 4: Sistema multi-agente completo

```python
class MultiAgentSystem:
    def __init__(self):
        self.message_bus = MessageBus()
        self.agents: Dict[str, SpecializedAgent] = {}
        self._create_agents()
    
    def _create_agents(self):
        """Crea agenti specializzati"""
        
        # Agente Matematico
        self.agents["MathExpert"] = SpecializedAgent(
            name="MathExpert",
            specialization="Matematica e Calcoli",
            tools=[calcola_avanzato],
            system_prompt="""Sei un esperto matematico. Risolvi problemi complessi,
            calcoli finanziari e statistici. Collabora con altri agenti.""",
            message_bus=self.message_bus
        )
        
        # Agente Analista Dati  
        self.agents["DataAnalyst"] = SpecializedAgent(
            name="DataAnalyst",
            specialization="Analisi Dati e Statistiche",
            tools=[analizza_dati, calcola_avanzato],
            system_prompt="""Sei un analista dati. Elabori dataset, calcoli statistiche,
            identifichi trend. Collabora con MathExpert per calcoli complessi.""",
            message_bus=self.message_bus
        )
        
        # Agente Coordinatore
        self.agents["Coordinator"] = SpecializedAgent(
            name="Coordinator", 
            specialization="Coordinazione e Pianificazione",
            tools=[coordina_task, genera_report],
            system_prompt="""Coordini il sistema multi-agente. Pianifichi task,
            assegni lavoro, coordini collaborazione e generi report finali.""",
            message_bus=self.message_bus
        )
    
    def execute_complex_task(self, task_description: str) -> Dict[str, Any]:
        """Esegue task complesso con coordinazione multi-agente"""
        
        task_id = f"task_{len(self.message_bus.messages)}"
        results = {}
        
        # Fase 1: Coordinatore analizza task
        coordinator = self.agents["Coordinator"]
        plan = coordinator.process_task(
            f"Crea piano per: {task_description}", task_id
        )
        results["coordination_plan"] = plan
        
        # Fase 2: Esecuzione specializzata
        if "calcola" in task_description.lower():
            math_result = self.agents["MathExpert"].process_task(
                task_description, task_id
            )
            results["math_analysis"] = math_result
        
        if "analisi" in task_description.lower():
            data_result = self.agents["DataAnalyst"].process_task(
                task_description, task_id
            )
            results["data_analysis"] = data_result
        
        # Fase 3: Report finale
        if len(results) > 1:
            summary = "\n".join([f"{k}: {v}" for k, v in results.items()])
            final_report = coordinator.process_task(
                f"Report finale per '{task_description}' con: {summary}", task_id
            )
            results["final_report"] = final_report
        
        return results
```

## Agenti specializzati

### MathExpert
**Competenze**: Calcoli matematici avanzati, formule finanziarie, operazioni statistiche
**Strumenti**: `calcola_avanzato`
**Specializzazione**: Problemi numerici complessi

### DataAnalyst  
**Competenze**: Analisi dataset, statistiche descrittive, identificazione trend
**Strumenti**: `analizza_dati`, `calcola_avanzato`
**Specializzazione**: Elaborazione e interpretazione dati

### ResearchAgent
**Competenze**: Ricerca informazioni specializzate per dominio (tech, business, science)
**Strumenti**: `cerca_informazioni_avanzate`
**Specializzazione**: Knowledge retrieval contestuale

### Coordinator
**Competenze**: Pianificazione task, coordinazione agenti, generazione report
**Strumenti**: `coordina_task`, `genera_report`
**Specializzazione**: Orchestrazione sistema multi-agente

## Sistema di messaggistica

### Comunicazione Inter-Agente

```python
# Invio messaggio
math_agent.send_message_to_agent(
    receiver="DataAnalyst",
    content="Media calcolata: 205.5. Serve analisi varianza?", 
    task_id="analysis_001"
)

# Ricezione e elaborazione
data_agent = system.agents["DataAnalyst"]
response = data_agent.process_task(
    "Calcola varianza per i dati ricevuti", "analysis_001"
)
# Il contesto del messaggio viene automaticamente incluso
```

### Tipi di Messaggio

- **request**: Richiesta di elaborazione
- **response**: Risposta a richiesta
- **info**: Informazione di contesto
- **result**: Risultato di operazione

## Pattern di collaborazione

### Workflow Sequenziale

```python
# 1. Coordinator pianifica
plan = coordinator.process_task("Analizza vendite Q1", task_id)

# 2. DataAnalyst elabora dati  
analysis = data_analyst.process_task("Analizza: 1200,1400,1100,1600", task_id)

# 3. MathExpert calcola trend
trend = math_expert.process_task("Calcola trend crescita", task_id)

# 4. Coordinator sintetizza
report = coordinator.process_task("Report finale con tutti i risultati", task_id)
```

### Collaborazione Parallela

```python
# Esecuzione simultanea di agenti diversi
results = {}

# Analisi dati in parallelo
results["stats"] = data_analyst.process_task(data, task_id)
results["research"] = research_agent.process_task(topic, task_id)  
results["calculations"] = math_expert.process_task(formulas, task_id)

# Sintesi finale
synthesis = coordinator.process_task(f"Sintetizza: {results}", task_id)
```

### Comunicazione Bidirezionale

```python
# DataAnalyst chiede supporto a MathExpert
data_analyst.send_message_to_agent(
    "MathExpert", "Serve calcolo correlazione per dataset", task_id
)

# MathExpert risponde con risultato
math_expert.send_message_to_agent(
    "DataAnalyst", "Correlazione = 0.85 (forte positiva)", task_id  
)

# DataAnalyst continua con contesto aggiornato
final_analysis = data_analyst.process_task("Interpreta correlazione", task_id)
```

## Esempi pratici

### Esempio 1: Analisi ROI Investimento

```python
system = MultiAgentSystem()

result = system.execute_complex_task(
    "Calcola ROI investimento 10000€ che genera 2500€/anno per 3 anni"
)

# Output:
# - coordination_plan: Piano di analisi finanziaria
# - math_analysis: ROI = 75%, payback = 4 anni
# - final_report: Report completo con raccomandazioni
```

### Esempio 2: Analisi Collaborativa Dataset

```python
result = system.collaborative_analysis(
    data="150,200,175,220,190,240,210,180,260,230",
    research_topic="trend crescita settore tech"
)

# Workflow automatico:
# 1. DataAnalyst: statistiche descrittive
# 2. ResearchAgent: contesto settore tech  
# 3. MathExpert: calcoli trend
# 4. Coordinator: sintesi finale
```

### Esempio 3: Task Personalizzato

```python
custom_task = "Analizza performance vendite, calcola crescita e cerca benchmark settoriali"

result = system.execute_complex_task(custom_task)

# Il sistema determina automaticamente:
# - Quali agenti coinvolgere
# - Sequenza di elaborazione
# - Coordinazione risultati
```

## Estensione del sistema

### Aggiungere Nuovo Agente

```python
# Definisci strumenti specifici
@Tool
def nuovo_strumento(param: str) -> str:
    return f"Elaborato: {param}"

# Crea agente specializzato
nuovo_agente = SpecializedAgent(
    name="NuovoExperto",
    specialization="Nuova Competenza",
    tools=[nuovo_strumento],
    system_prompt="Sei specializzato in...",
    message_bus=system.message_bus
)

# Registra nel sistema
system.agents["NuovoExperto"] = nuovo_agente
```

### Personalizzare Coordinazione

```python
def custom_coordination_logic(self, task: str):
    """Logica di coordinazione personalizzata"""
    
    if "urgent" in task.lower():
        # Workflow accelerato
        return self.fast_track_execution(task)
    
    elif "complex" in task.lower():
        # Coinvolgi tutti gli agenti
        return self.full_collaboration(task)
    
    else:
        # Workflow standard
        return self.standard_execution(task)
```

### Aggiungere Nuovi Pattern

```python
def parallel_processing(self, tasks: List[str]) -> Dict[str, Any]:
    """Elaborazione parallela di task multipli"""
    
    results = {}
    for i, task in enumerate(tasks):
        agent = self.select_best_agent(task)
        results[f"task_{i}"] = agent.process_task(task, f"parallel_{i}")
    
    return results
```

Il sistema multi-agente fornisce un framework flessibile e scalabile per task complessi che richiedono competenze specializzate diverse, con comunicazione e coordinazione automatica tra agenti! 🤖🤝
