import os
import re
from dotenv import load_dotenv
load_dotenv()
from datapizza.agents import Agent
from datapizza.clients import ClientFactory
from datapizza.tools import tool

shared_client = ClientFactory.create(
    provider="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.0,
)

@tool
def extract_kpi(context: str) -> str:
    """Extracts KPIs and quantitative metrics from raw text."""
    patterns = {
        "Revenue": r"(?:revenue|fatturato)[:\s]*([€$]?\d+[\d,.]*[MBK]?)",
        "Growth": r"(\d+[\d,.]*%)\s*(?:growth|yoy)",
    }
    metrics = [
        f"{name}: {match.group(1)}"
        for name, pattern in patterns.items()
        if (match := re.search(pattern, context, re.IGNORECASE))
    ]
    return " | ".join(metrics) if metrics else "No KPIs found"

@tool
def identify_risks(context: str) -> str:
    """Flags risks by scanning for domain keywords."""
    risk_map = {"Compliance": ["gdpr", "regulation"], "Budget": ["budget", "cost"]}
    risks = [name for name, keywords in risk_map.items() if any(k in context.lower() for k in keywords)]
    return " | ".join(risks) if risks else "No risks identified"

# Specialist Agents with very strict prompts
analyst_agent = Agent(
    name="AnalystAgent",
    client=shared_client,
    system_prompt=(
        "You are a KPI extraction specialist. Your ONLY job:\n"
        "1. Call extract_kpi ONCE with the full text provided\n"
        "2. Immediately return the tool result as your final answer\n"
        "3. NEVER call the tool more than once\n"
        "4. NEVER add commentary, just return the tool output"
    ),
    tools=[extract_kpi],
    terminate_on_text=True,
    max_steps=2,
)

risk_agent = Agent(
    name="RiskAgent",
    client=shared_client,
    system_prompt=(
        "You are a risk identification specialist. Your ONLY job:\n"
        "1. Call identify_risks ONCE with the full text provided\n"
        "2. Immediately return the tool result as your final answer\n"
        "3. NEVER call the tool more than once\n"
        "4. NEVER add commentary, just return the tool output"
    ),
    tools=[identify_risks],
    terminate_on_text=True,
    max_steps=2,
)

@tool
def run_kpi_analysis(query: str) -> str:
    """Delegates KPI extraction to the specialist agent."""
    print("  -> Delegating to AnalystAgent...")
    result = analyst_agent.run(query)
    if hasattr(result, 'text'):
        return result.text or "No KPIs found"
    return str(result) or "No KPIs found"

@tool
def run_risk_assessment(query: str) -> str:
    """Delegates risk screening to the specialist agent."""
    print("  -> Delegating to RiskAgent...")
    result = risk_agent.run(query)
    if hasattr(result, 'text'):
        return result.text or "No risks identified"
    return str(result) or "No risks identified"

# Coordinator with explicit step-by-step instructions
strategic_planner_agent = Agent(
    name="StrategicPlanner",
    client=shared_client,
    system_prompt=(
        "You are a strategic consultant. Execute this EXACT sequence:\n\n"
        "STEP 1: Call run_kpi_analysis with the full query\n"
        "STEP 2: Call run_risk_assessment with the full query\n"
        "STEP 3: After BOTH tools have been called, synthesize a final report with these sections:\n"
        "   **KPI Summary**: [results from step 1]\n"
        "   **Risk Areas**: [results from step 2]\n"
        "   **Recommendation**: [one actionable sentence]\n\n"
        "CRITICAL: Call each tool EXACTLY ONCE, then immediately write the final report. Do NOT repeat tool calls."
    ),
    tools=[run_kpi_analysis, run_risk_assessment],
    terminate_on_text=True,
    max_steps=10,
)

if __name__ == "__main__":
    scenarios = [
        "Fintech product growing 30% YoY, €2M revenue, needs GDPR compliance roadmap.",
        "AI adoption program: €500K budget, 180% ROI target, six-month deadline.",
    ]

    for scenario in scenarios:
        print(f"\n{'=' * 70}\n>> Strategic Planner query: \"{scenario}\"\n{'=' * 70}")
        final_report = strategic_planner_agent.run(scenario)
        
        if hasattr(final_report, 'text'):
            print(f"\n{'─' * 70}\nFINAL REPORT:\n{'─' * 70}")
            print(final_report.text or 'Unable to produce the final report.')
            print('─' * 70)
        else:
            print(f"\nFINAL REPORT:\n{final_report or 'Unable to produce the final report.'}")

