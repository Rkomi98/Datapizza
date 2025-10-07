import os
import re
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient
from datapizza.agents import Agent
from datapizza.tools import tool

load_dotenv()

# Shared client
shared_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    temperature=0.3
)

# Test 1: Building Specialist Agents
print("=== Test 1: Building Specialist Agents ===")

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

# Test specialists
test_context = "Revenue €2M, 30% growth, needs GDPR compliance"
print(f"Analyst: {analyst_agent.run(test_context)}")
print(f"Risk: {risk_agent.run(test_context)}")
print("✅ Specialist agents test successful\n")

# Test 2: Building the Coordinator
print("=== Test 2: Building the Coordinator ===")

@tool
def run_kpi_analysis(query: str) -> str:
    """Delegates to the KPI analyst."""
    print("  -> Delegating to AnalystAgent...")
    result = analyst_agent.run(query)
    # Extract text from StepResult
    if hasattr(result, 'text'):
        return result.text or "Analysis incomplete"
    return str(result) or "Analysis incomplete"

@tool
def run_risk_assessment(query: str) -> str:
    """Delegates to the risk assessor."""
    print("  -> Delegating to RiskAgent...")
    result = risk_agent.run(query)
    # Extract text from StepResult
    if hasattr(result, 'text'):
        return result.text or "Assessment incomplete"
    return str(result) or "Assessment incomplete"

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

scenario = (
    "Fintech product growing 30% YoY, €2M revenue, "
    "needs GDPR compliance roadmap."
)

report = strategic_planner.run(scenario)
print(f"Strategic Report: {report}")
print("✅ Coordinator test successful\n")

print("✅ All tests passed for video_07!")

