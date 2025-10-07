import os
import re
from dotenv import load_dotenv
load_dotenv()
from datapizza.agents import Agent
from datapizza.clients import ClientFactory
from datapizza.clients.factory import Provider
from datapizza.tools import tool

shared_client = ClientFactory.create(
    provider=Provider.OPENAI,
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

# SPECIALIZED AGENTS (use tools, but simpler setup)
analyst_agent = Agent(
    name="AnalystAgent",
    client=shared_client,
    system_prompt="You are a KPI extraction specialist. Use the extract_kpi tool on the provided text and return the result.",
    tools=[extract_kpi],
    max_steps=3
)

risk_agent = Agent(
    name="RiskAgent",
    client=shared_client,
    system_prompt="You are a risk identification specialist. Use the identify_risks tool on the provided text and return the result.",
    tools=[identify_risks],
    max_steps=3
)

@tool
def run_kpi_analysis(query: str) -> str:
    """Delegates KPI extraction to the specialist AnalystAgent."""
    print("  -> Delegating to AnalystAgent...")
    result = analyst_agent.run(query)
    # Extract text or tools_used results
    if hasattr(result, 'text') and result.text:
        return result.text
    # Fallback: try to get tool results
    if hasattr(result, 'tools_used') and result.tools_used:
        return str(result.tools_used[0] if result.tools_used else "No result")
    return "KPI analysis inconclusive"

@tool
def run_risk_assessment(query: str) -> str:
    """Delegates risk screening to the specialist RiskAgent."""
    print("  -> Delegating to RiskAgent...")
    result = risk_agent.run(query)
    # Extract text or tools_used results
    if hasattr(result, 'text') and result.text:
        return result.text
    # Fallback: try to get tool results
    if hasattr(result, 'tools_used') and result.tools_used:
        return str(result.tools_used[0] if result.tools_used else "No result")
    return "Risk assessment inconclusive"

# COORDINATOR AGENT
strategic_planner_agent = Agent(
    name="StrategicPlanner",
    client=shared_client,
    system_prompt=(
        "You are a strategic consultant. Follow these steps:\n"
        "1. Call run_kpi_analysis on the request\n"
        "2. Call run_risk_assessment on the same request\n"
        "3. Synthesize findings into a final report with:\n"
        "   - **KPI Summary**\n"
        "   - **Risk Areas**\n"
        "   - **Recommendation** (one sentence)\n"
        "Make the report concise and actionable."
    ),
    tools=[run_kpi_analysis, run_risk_assessment],
    max_steps=8
)

if __name__ == "__main__":
    scenarios = [
        "Fintech product growing 30% YoY, €2M revenue, needs GDPR compliance roadmap.",
    ]

    for scenario in scenarios:
        print(f"\n{'=' * 70}")
        print(f">> Query: \"{scenario}\"")
        print('=' * 70)
        
        final_report = strategic_planner_agent.run(scenario)
        
        print(f"\n{'─' * 70}")
        print("FINAL REPORT:")
        print('─' * 70)
        if hasattr(final_report, 'text') and final_report.text:
            print(final_report.text)
        else:
            print(f"{final_report}")
        print('─' * 70)

