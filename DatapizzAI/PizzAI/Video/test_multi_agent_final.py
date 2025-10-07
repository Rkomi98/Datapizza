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
    model="gpt-4o-mini",
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
    return " | ".join(metrics) if metrics else "No numeric KPI detected."

@tool
def identify_risks(context: str) -> str:
    """Flags risks by scanning for domain keywords."""
    risk_map = {"Compliance": ["gdpr", "normativa"], "Budget": ["budget", "costo"]}
    risks = [name for name, keywords in risk_map.items() if any(k in context.lower() for k in keywords)]
    return " | ".join(risks) if risks else "No material operational risk identified."

analyst_agent = Agent(
    name="AnalystAgent",
    client=shared_client,
    system_prompt=(
        "Call the tool `extract_kpi(context=<<TEXT>>) EXACTLY ONCE.`\n"
        "Immediately after, send a SINGLE text message that repeats the tool output verbatim.\n"
        "You MUST NOT call any other tool.\n"
        "Output format:\n{{TOOL_RESULT}}\n"
    ),
    tools=[extract_kpi],
    terminate_on_text=True,
    max_steps=3,
)

risk_agent = Agent(
    name="RiskAgent",
    client=shared_client,
    system_prompt=(
        "Call the tool `identify_risks(context=<<TEXT>>) EXACTLY ONCE.`\n"
        "Then send a SINGLE text message that contains the tool output verbatim.\n"
        "Stop immediately afterwards. No further tool calls are allowed."
    ),
    tools=[identify_risks],
    terminate_on_text=True,
    max_steps=3,
)

@tool
def run_kpi_analysis(query: str) -> str:
    """Delegates KPI extraction to the specialist agent."""
    print("  -> Delegating to AnalystAgent...")
    result = analyst_agent.run(query)
    # Extract text from StepResult
    if hasattr(result, 'text'):
        return result.text or "KPI analysis did not complete."
    return str(result) or "KPI analysis did not complete."

@tool
def run_risk_assessment(query: str) -> str:
    """Delegates risk screening to the specialist agent."""
    print("  -> Delegating to RiskAgent...")
    result = risk_agent.run(query)
    # Extract text from StepResult
    if hasattr(result, 'text'):
        return result.text or "Risk assessment did not complete."
    return str(result) or "Risk assessment did not complete."

strategic_planner_agent = Agent(
    name="StrategicPlanner",
    client=shared_client,
    system_prompt=(
        "You are a strategic consultant. Produce a business review by following these steps:\n"
        "1. Call `run_kpi_analysis` on the original request to capture metrics.\n"
        "2. Call `run_risk_assessment` on the same request to uncover risks.\n"
        "3. Merge the findings into a final report with **KPI Summary**, **Risk Areas**, and a one-line **Recommendation**."
    ),
    tools=[run_kpi_analysis, run_risk_assessment],
    terminate_on_text=True,
    max_steps=5,
)

if __name__ == "__main__":
    scenarios = [
        "Fintech product growing 30% YoY, €2M revenue, needs GDPR compliance roadmap.",
        "AI adoption program: €500K budget, 180% ROI target, six-month deadline.",
    ]

    for scenario in scenarios:
        print(f"{'-' * 60}\n>> Strategic Planner query: \"{scenario}\"")
        final_report = strategic_planner_agent.run(scenario)
        # Extract text from StepResult
        if hasattr(final_report, 'text'):
            print(f"\nFinal report:\n{final_report.text or 'Unable to produce the final report.'}\n")
        else:
            print(f"\nFinal report:\n{final_report or 'Unable to produce the final report.'}\n")

