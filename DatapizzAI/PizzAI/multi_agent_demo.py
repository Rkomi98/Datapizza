#!/usr/bin/env python3
"""Showcase a true multi-agent interaction with dynamic delegation."""

import os

from dotenv import load_dotenv

from datapizza.agents import Agent
from datapizza.clients import ClientFactory
from datapizza.tools import tool


load_dotenv()


@tool(name="company_snapshot")
def get_company_snapshot(topic: str) -> str:
    """Return a mocked data snapshot for a company."""
    return (
        f"Snapshot for {topic}: revenue=2.5M, costs=1.8M, users=15000, churn=4%."
    )


@tool(name="extract_metrics")
def extract_metrics(text: str) -> str:
    """Isolate key metrics from a text blob."""
    return "revenue=2.5M; costs=1.8M; users=15000; churn=4%"


@tool(name="calculate")
def safe_calculate(expression: str) -> str:
    """Evaluate simple expressions; understands values expressed in millions."""
    try:
        sanitized = expression.replace("M", "*1_000_000")
        return str(eval(sanitized, {"__builtins__": {}}, {}))
    except Exception as exc:  # noqa: BLE001
        return f"calculation_error: {exc}"


def build_client():
    return ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
    )


def make_delegate_tool(agent: Agent, description: str):
    @tool(name=agent.name, description=description)
    def delegate(task: str) -> str:
        return agent.run(task)

    return delegate


def main() -> None:
    print("Dynamic multi-agent delegation demo...")

    client = build_client()

    research_agent = Agent(
        name="Researcher",
        client=client,
        system_prompt=(
            "You gather business intelligence. When needed, call tools to fetch a snapshot "
            "and extract structured metrics."
        ),
        tools=[get_company_snapshot, extract_metrics],
        max_steps=3,
    )

    finance_agent = Agent(
        name="FinancialAnalyst",
        client=client,
        system_prompt=(
            "You analyse numeric metrics. Derive profits, margins and explain how you got them."
        ),
        tools=[safe_calculate],
        max_steps=3,
    )

    writer_agent = Agent(
        name="Writer",
        client=client,
        system_prompt=(
            "You synthesise insights into a polished executive summary that cites numbers."
        ),
        max_steps=3,
    )

    research_delegate = make_delegate_tool(
        research_agent,
        "Retrieve business intel and structured metrics",
    )
    finance_delegate = make_delegate_tool(
        finance_agent,
        "Perform financial calculations based on provided metrics",
    )
    writer_delegate = make_delegate_tool(
        writer_agent,
        "Compose an executive summary that references the numbers",
    )

    coordinator = Agent(
        name="Coordinator",
        client=client,
        system_prompt=(
            "You are the orchestrator. Decide on the fly which specialist to involve to satisfy the "
            "user's request. Use Researcher to gather facts, FinancialAnalyst for computations, and "
            "Writer to craft the final wording. Keep delegating until the answer is complete."
        ),
        tools=[research_delegate, finance_delegate, writer_delegate],
        max_steps=6,
        planning_interval=2,
    )

    question = (
        "L'utente vuole un quadro sui risultati dell'ultimo trimestre di DatapizzaAI: "
        "recupera i numeri principali, calcola il profitto e il margine e poi scrivi "
        "un riassunto esecutivo."
    )

    final_report = coordinator.run(question)

    print("\nFinal Report from Coordinator:\n")
    print(final_report)


if __name__ == "__main__":
    main()
