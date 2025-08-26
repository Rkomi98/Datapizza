# Multi Agent System - DatapizzAI

Multi-agent system where different specialized agents collaborate to complete complex tasks. Each agent has specific competencies and can communicate with other agents through a messaging system.

## Table of contents

1. [Fundamental concepts](#fundamental-concepts)
2. [System architecture](#system-architecture)
3. [Step-by-step configuration](#step-by-step-configuration)
4. [Specialized agents](#specialized-agents)
5. [Messaging system](#messaging-system)
6. [Collaboration patterns](#collaboration-patterns)
7. [Practical examples](#practical-examples)
8. [System extension](#system-extension)

## Fundamental concepts

### Multi-Agent System
A system where multiple specialized AI agents collaborate to solve complex problems:

- **Specialization**: Each agent has specific competencies
- **Collaboration**: Agents communicate and coordinate
- **Coordination**: A coordinator agent manages complex tasks
- **Messaging**: Inter-agent communication system

### Specialized Agent
Each agent has:
- **Name and role**: Specific identity in the system
- **Tools**: Specialized tools for their domain
- **OpenAI Client**: AI connection for processing
- **Memory**: Conversational context
- **Communication**: Ability to send/receive messages

## System architecture

```
┌────────────────────────────────────────────────────────────┐
│                    MultiAgentSystem                        │
├────────────────────────────────────────────────────────────┤
│                    MessageBus                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ MathExpert  │ │DataAnalyst  │ │ResearchAgent│           │
│  │             │ │             │ │             │           │
│  │ • advanced  │ │ • analyze   │ │ • search    │           │
│  │   calculate │ │   data      │ │   info      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Coordinator                            │   │
│  │                                                     │   │
│  │ • coordinate_task                                   │   │
│  │ • generate_report                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

## Step-by-step configuration

### Step 1: Specialized tool definition

```python
from datapizzai.tools import Tool

@Tool
def advanced_calculate(expression: str, calculation_type: str = "base") -> str:
    """Advanced mathematical calculations with financial/statistical support."""
    import math
    
    namespace = {
        'sin': math.sin, 'cos': math.cos, 'sqrt': math.sqrt,
        'pi': math.pi, 'e': math.e
    }
    
    try:
        result = eval(expression, namespace)
        return f"Result {calculation_type}: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@Tool
def analyze_data(data: str, analysis_type: str = "base") -> str:
    """Statistical analysis of datasets."""
    import json, statistics
    
    # Data parsing
    if data.startswith('['):
        data = json.loads(data)
    else:
        data = [float(x.strip()) for x in data.split(',')]
    
    results = {
        "mean": statistics.mean(data),
        "median": statistics.median(data),
        "min": min(data),
        "max": max(data)
    }
    
    return f"Analysis {analysis_type}: {json.dumps(results, indent=2)}"
```

### Step 2: Messaging system

```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class AgentMessage:
    """Message between agents"""
    sender: str
    receiver: str
    content: str
    task_id: str
    message_type: str = "request"

class MessageBus:
    """Centralized messaging system"""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
    
    def send_message(self, message: AgentMessage):
        self.messages.append(message)
        print(f"📨 {message.sender} → {message.receiver}: {message.content[:50]}...")
    
    def get_messages_for_agent(self, agent_name: str) -> List[AgentMessage]:
        return [msg for msg in self.messages if msg.receiver == agent_name]
```

### Step 3: Specialized agent creation

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
        
        # Specialized OpenAI client
        self.client = ClientFactory.create(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o",
            system_prompt=system_prompt
        )
    
    def process_task(self, task: str, task_id: str) -> str:
        """Processes task with specialized tools"""
        
        # Check messages from other agents
        messages = self.message_bus.get_messages_for_agent(self.name)
        context = ""
        if messages:
            context = "\nMessages received:\n" + "\n".join([
                f"- {msg.sender}: {msg.content}" for msg in messages
            ])
        
        # Process with context
        full_task = task + context
        self.memory.add_turn([TextBlock(content=full_task)], ROLE.USER)
        
        response = self.client.invoke(
            input="",
            memory=self.memory,
            tools=self.tools,
            tool_choice="auto"
        )
        
        # Execute tools and generate result
        tool_results = self._execute_tool_calls(response)
        result = response.text or f"Operations: {'; '.join(tool_results[:2])}"
        
        return result
    
    def send_message_to_agent(self, receiver: str, content: str, task_id: str):
        """Communicates with another agent"""
        message = AgentMessage(
            sender=self.name,
            receiver=receiver, 
            content=content,
            task_id=task_id
        )
        self.message_bus.send_message(message)
```

### Step 4: Complete multi-agent system

```python
class MultiAgentSystem:
    def __init__(self):
        self.message_bus = MessageBus()
        self.agents: Dict[str, SpecializedAgent] = {}
        self._create_agents()
    
    def _create_agents(self):
        """Creates specialized agents"""
        
        # Mathematical Agent
        self.agents["MathExpert"] = SpecializedAgent(
            name="MathExpert",
            specialization="Mathematics and Calculations",
            tools=[advanced_calculate],
            system_prompt="""You are a mathematical expert. Solve complex problems,
            financial calculations and statistics. Collaborate with other agents.""",
            message_bus=self.message_bus
        )
        
        # Data Analyst Agent  
        self.agents["DataAnalyst"] = SpecializedAgent(
            name="DataAnalyst",
            specialization="Data Analysis and Statistics",
            tools=[analyze_data, advanced_calculate],
            system_prompt="""You are a data analyst. Process datasets, calculate statistics,
            identify trends. Collaborate with MathExpert for complex calculations.""",
            message_bus=self.message_bus
        )
        
        # Coordinator Agent
        self.agents["Coordinator"] = SpecializedAgent(
            name="Coordinator", 
            specialization="Coordination and Planning",
            tools=[coordinate_task, generate_report],
            system_prompt="""You coordinate the multi-agent system. Plan tasks,
            assign work, coordinate collaboration and generate final reports.""",
            message_bus=self.message_bus
        )
    
    def execute_complex_task(self, task_description: str) -> Dict[str, Any]:
        """Executes complex task with multi-agent coordination"""
        
        task_id = f"task_{len(self.message_bus.messages)}"
        results = {}
        
        # Phase 1: Coordinator analyzes task
        coordinator = self.agents["Coordinator"]
        plan = coordinator.process_task(
            f"Create plan for: {task_description}", task_id
        )
        results["coordination_plan"] = plan
        
        # Phase 2: Specialized execution
        if "calculate" in task_description.lower():
            math_result = self.agents["MathExpert"].process_task(
                task_description, task_id
            )
            results["math_analysis"] = math_result
        
        if "analysis" in task_description.lower():
            data_result = self.agents["DataAnalyst"].process_task(
                task_description, task_id
            )
            results["data_analysis"] = data_result
        
        # Phase 3: Final report
        if len(results) > 1:
            summary = "\n".join([f"{k}: {v}" for k, v in results.items()])
            final_report = coordinator.process_task(
                f"Final report for '{task_description}' with: {summary}", task_id
            )
            results["final_report"] = final_report
        
        return results
```

## Specialized agents

### MathExpert
**Competencies**: Advanced mathematical calculations, financial formulas, statistical operations
**Tools**: `advanced_calculate`
**Specialization**: Complex numerical problems

### DataAnalyst  
**Competencies**: Dataset analysis, descriptive statistics, trend identification
**Tools**: `analyze_data`, `advanced_calculate`
**Specialization**: Data processing and interpretation

### ResearchAgent
**Competencies**: Specialized information search by domain (tech, business, science)
**Tools**: `advanced_search_information`
**Specialization**: Contextual knowledge retrieval

### Coordinator
**Competencies**: Task planning, agent coordination, report generation
**Tools**: `coordinate_task`, `generate_report`
**Specialization**: Multi-agent system orchestration

## Messaging system

### Inter-Agent Communication

```python
# Send message
math_agent.send_message_to_agent(
    receiver="DataAnalyst",
    content="Mean calculated: 205.5. Need variance analysis?", 
    task_id="analysis_001"
)

# Receive and process
data_agent = system.agents["DataAnalyst"]
response = data_agent.process_task(
    "Calculate variance for received data", "analysis_001"
)
# Message context is automatically included
```

### Message Types

- **request**: Processing request
- **response**: Response to request
- **info**: Context information
- **result**: Operation result

## Collaboration patterns

### Sequential Workflow

```python
# 1. Coordinator plans
plan = coordinator.process_task("Analyze Q1 sales", task_id)

# 2. DataAnalyst processes data  
analysis = data_analyst.process_task("Analyze: 1200,1400,1100,1600", task_id)

# 3. MathExpert calculates trend
trend = math_expert.process_task("Calculate growth trend", task_id)

# 4. Coordinator synthesizes
report = coordinator.process_task("Final report with all results", task_id)
```

### Parallel Collaboration

```python
# Simultaneous execution of different agents
results = {}

# Parallel data analysis
results["stats"] = data_analyst.process_task(data, task_id)
results["research"] = research_agent.process_task(topic, task_id)  
results["calculations"] = math_expert.process_task(formulas, task_id)

# Final synthesis
synthesis = coordinator.process_task(f"Synthesize: {results}", task_id)
```

### Bidirectional Communication

```python
# DataAnalyst asks MathExpert for support
data_analyst.send_message_to_agent(
    "MathExpert", "Need correlation calculation for dataset", task_id
)

# MathExpert responds with result
math_expert.send_message_to_agent(
    "DataAnalyst", "Correlation = 0.85 (strong positive)", task_id  
)

# DataAnalyst continues with updated context
final_analysis = data_analyst.process_task("Interpret correlation", task_id)
```

## Practical examples

### Example 1: Investment ROI Analysis

```python
system = MultiAgentSystem()

result = system.execute_complex_task(
    "Calculate ROI for 10000€ investment that generates 2500€/year for 3 years"
)

# Output:
# - coordination_plan: Financial analysis plan
# - math_analysis: ROI = 75%, payback = 4 years
# - final_report: Complete report with recommendations
```

### Example 2: Collaborative Dataset Analysis

```python
result = system.collaborative_analysis(
    data="150,200,175,220,190,240,210,180,260,230",
    research_topic="tech sector growth trend"
)

# Automatic workflow:
# 1. DataAnalyst: descriptive statistics
# 2. ResearchAgent: tech sector context  
# 3. MathExpert: trend calculations
# 4. Coordinator: final synthesis
```

### Example 3: Custom Task

```python
custom_task = "Analyze sales performance, calculate growth and search sector benchmarks"

result = system.execute_complex_task(custom_task)

# The system automatically determines:
# - Which agents to involve
# - Processing sequence
# - Result coordination
```

## System extension

### Adding New Agent

```python
# Define specific tools
@Tool
def new_tool(param: str) -> str:
    return f"Processed: {param}"

# Create specialized agent
new_agent = SpecializedAgent(
    name="NewExpert",
    specialization="New Competency",
    tools=[new_tool],
    system_prompt="You are specialized in...",
    message_bus=system.message_bus
)

# Register in system
system.agents["NewExpert"] = new_agent
```

### Customizing Coordination

```python
def custom_coordination_logic(self, task: str):
    """Custom coordination logic"""
    
    if "urgent" in task.lower():
        # Accelerated workflow
        return self.fast_track_execution(task)
    
    elif "complex" in task.lower():
        # Involve all agents
        return self.full_collaboration(task)
    
    else:
        # Standard workflow
        return self.standard_execution(task)
```

### Adding New Patterns

```python
def parallel_processing(self, tasks: List[str]) -> Dict[str, Any]:
    """Parallel processing of multiple tasks"""
    
    results = {}
    for i, task in enumerate(tasks):
        agent = self.select_best_agent(task)
        results[f"task_{i}"] = agent.process_task(task, f"parallel_{i}")
    
    return results
```

The multi-agent system provides a flexible and scalable framework for complex tasks that require different specialized competencies, with automatic communication and coordination between agents! 🤖🤝
