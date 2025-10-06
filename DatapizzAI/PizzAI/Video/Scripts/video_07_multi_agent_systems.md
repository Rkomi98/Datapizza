# Video 7: Multi-Agent Systems

## Introduction (1.5 min)

What's up! Welcome back. So single agents are powerful, but here's the thing—complex problems often need specialized expertise. You wouldn't ask one person to handle finance, compliance, and engineering—you'd have a team, right?

That's exactly what we're building today: multi-agent systems where specialized agents collaborate to solve problems.

[Visual: Show organizational chart transforming into agent network]

We're building a strategic planning system with three agents: an analyst who extracts metrics, a risk assessor who identifies problems, and a planner who coordinates everything and produces the final report.

After this, you'll understand agent orchestration, delegation patterns, and how to prevent common pitfalls like infinite loops. This is production-grade stuff.

Alright, architecture first.

## Content Main (6.5 min)

### Designing the System (2 min)

Before we write any code, let's design the architecture. We need three specialized agents, and each one has a specific job:

[Show diagram]

**AnalystAgent**: Extracts KPIs and quantitative metrics. It sees numbers, revenue figures, growth rates.

**RiskAgent**: Identifies operational risks by scanning for keywords like "compliance," "budget," "deadline."

**StrategicPlanner**: The coordinator. It delegates to specialists, waits for their responses, and synthesizes everything into a final report.

[Visual: Show data flow between agents]

The planner doesn't do the actual analysis—it orchestrates. This separation of concerns is critical. Each agent has one job, does it well, and returns control to the planner.

And here's why this is powerful—this pattern scales infinitely. Need legal review? Add a LegalAgent. Need technical assessment? Add an EngineerAgent. The planner's logic stays exactly the same. You just add more specialist tools.

Think about how powerful this is for real-world applications. Customer support? You could have a TechnicalAgent, a BillingAgent, a PolicyAgent—all coordinated by a main planner that routes questions to the right specialist.

### Building Specialist Agents (2 min)

Let's start with the specialists. First, the tools they'll use:

```python
import re
from datapizza.tools import tool

@tool
def extract_kpi(context: str) -> str:
    """Extracts KPIs and metrics from text."""
    patterns = {
        "Revenue": r"(?:revenue|fatturato)[:\s]*([€$]?\d+[\d,.]*[MBK]?)",
        "Growth": r"(\d+[\d,.]*%)\s*(?:growth|yoy)"
    }
    metrics = [
        f"{name}: {match.group(1)}"
        for name, pattern in patterns.items()
        if (match := re.search(pattern, context, re.IGNORECASE))
    ]
    return " | ".join(metrics) if metrics else "No KPIs found"

@tool
def identify_risks(context: str) -> str:
    """Identifies operational risks."""
    risk_map = {
        "Compliance": ["gdpr", "regulation"],
        "Budget": ["budget", "cost", "funding"]
    }
    risks = [
        name for name, keywords in risk_map.items()
        if any(k in context.lower() for k in keywords)
    ]
    return " | ".join(risks) if risks else "No risks identified"
```

[Show the tools working on sample text]

Simple pattern matching, but effective. In production, you'd use more sophisticated extraction.

Now the specialist agents:

```python
from datapizza.agents import Agent

analyst_agent = Agent(
    name="AnalystAgent",
    client=shared_client,
    system_prompt=(
        "Call extract_kpi EXACTLY ONCE with the provided text. "
        "Then output ONLY the tool result. "
        "Do not call any other tools."
    ),
    tools=[extract_kpi],
    terminate_on_text=True,
    max_steps=3
)

risk_agent = Agent(
    name="RiskAgent",
    client=shared_client,
    system_prompt=(
        "Call identify_risks EXACTLY ONCE with the provided text. "
        "Then output ONLY the tool result. "
        "Stop immediately."
    ),
    tools=[identify_risks],
    terminate_on_text=True,
    max_steps=3
)
```

[Highlight the system prompts]

Notice the constraints. "EXACTLY ONCE." "Do not call any other tools." This prevents the agent from getting creative and causing loops.

The `max_steps=3` is a safety net. Even if the agent tries to loop, it hits the limit and stops.

### Building the Coordinator (3 min)

Now the interesting part—the planner that coordinates everything.

We wrap each specialist agent as a tool:

```python
@tool
def run_kpi_analysis(query: str) -> str:
    """Delegates to the KPI analyst."""
    print("  -> Delegating to AnalystAgent...")
    result = analyst_agent.run(query)
    return result or "Analysis incomplete"

@tool
def run_risk_assessment(query: str) -> str:
    """Delegates to the risk assessor."""
    print("  -> Delegating to RiskAgent...")
    result = risk_agent.run(query)
    return result or "Assessment incomplete"
```

[Show this pattern clearly]

This is the key insight: agents become tools. The planner calls these tools, which internally run other agents.

Now the planner itself:

```python
strategic_planner = Agent(
    name="StrategicPlanner",
    client=shared_client,
    system_prompt=(
        "You are a strategic consultant. Follow these steps:\n"
        "1. Call run_kpi_analysis on the request.\n"
        "2. Call run_risk_assessment on the same request.\n"
        "3. Merge findings into a report with sections: "
        "KPI Summary, Risk Areas, Recommendation."
    ),
    tools=[run_kpi_analysis, run_risk_assessment],
    terminate_on_text=True,
    max_steps=5
)
```

[Show execution]

```python
scenario = (
    "Fintech product growing 30% YoY, €2M revenue, "
    "needs GDPR compliance roadmap."
)

report = strategic_planner.run(scenario)
print(report)
```

[Run and show the full delegation chain]

Watch the flow: Planner receives task. Calls KPI tool, which runs AnalystAgent. Gets result. Calls risk tool, which runs RiskAgent. Gets result. Synthesizes final report.

[Visual: Show call stack diagram]

Three agents, coordinated execution, single output. This is multi-agent orchestration.

### Preventing Common Pitfalls (1 min)

Multi-agent systems can fail in predictable ways. Here's how to avoid them:

**Problem 1: Infinite loops**
Solution: Always set max_steps on every agent. Always.

**Problem 2: Ambiguous delegation**
Solution: Be explicit in system prompts. "Call tool X exactly once" beats "use tool X if needed."

**Problem 3: Lost context**
Solution: Pass the original query to every specialist. Don't make them guess what to analyze.

**Problem 4: Uncontrolled tool calls**
Solution: Use terminate_on_text=True for specialists who should run once and return.

[Show side-by-side comparison of good vs bad configurations]

These constraints might seem restrictive, but they're what make multi-agent systems reliable in production.

## Conclusion (1.5 min)

Alright, so to wrap this up: We designed a three-agent system with specialists and a coordinator. We wrapped agents as tools to enable delegation. And we learned how to prevent loops and ensure reliable execution.

[Visual: Show the complete system diagram]

This pattern scales to any complexity you need. Five specialists? Ten? Twenty? The coordinator logic stays the same—delegate, collect, synthesize.

Next video, we're building a complete RAG system—retrieval-augmented generation for answering questions from your own documents. Super practical stuff.

Before that, try extending this system. Add a third specialist—maybe a FinancialAgent or TechnicalAgent. See how the planner adapts automatically. It's pretty amazing when you see it work.

Multi-agent systems are where Datapizza-AI really shines. You're building production-grade AI architectures now, not just toy examples.

If you're getting value from this, smash that like button. Drop a comment if you build something cool with this. I'll see you next time!

[Note for narrator: This should feel like a major architectural lesson—we're building systems now, not just apps]
