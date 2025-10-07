import os
import re
from dotenv import load_dotenv
from datapizza.tools import tool
from datapizza.agents import Agent
from datapizza.clients import ClientFactory
from datapizza.clients.factory import Provider

load_dotenv()

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

# Create shared client for all agents
shared_client = ClientFactory.create(
    provider=Provider.OPENAI,
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.0,
)

# SIMPLIFIED APPROACH: Use tools directly in the planner
strategic_planner = Agent(
    name="StrategicPlanner",
    client=shared_client,
    system_prompt=(
        "You are a strategic consultant. Follow these steps:\n"
        "1. Call extract_kpi on the request to get KPI metrics\n"
        "2. Call identify_risks on the same request to get risk areas\n"
        "3. Synthesize findings into a final report with:\n"
        "   - **KPI Summary**\n"
        "   - **Risk Areas**\n"
        "   - **Recommendation** (one actionable sentence)\n"
        "Make the report concise and actionable."
    ),
    tools=[extract_kpi, identify_risks],
    max_steps=6
)

scenario = (
    "Fintech product growing 30% YoY, €2M revenue, "
    "needs GDPR compliance roadmap."
)

print(f"\n{'=' * 70}")
print(f"Testing Simplified Multi-Tool Agent")
print('=' * 70)
print(f"Scenario: {scenario}\n")

report = strategic_planner.run(scenario)

# Extract and print the final text
print(f"\n{'─' * 70}")
print("FINAL REPORT:")
print('─' * 70)
if hasattr(report, 'text') and report.text:
    print(report.text)
else:
    print(report)
print('─' * 70)
print("\n✅ Test successful!")

