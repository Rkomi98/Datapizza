#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.agents import Agent
from datapizzai.tools import tool

load_dotenv()

@tool
def get_stock_data(symbol: str) -> str:
    """Get stock market data"""
    return f"{symbol}: $245.67 (+3.2%), volume 2.1M"

@tool
def write_report(analysis: str) -> str:
    """Write investment report"""
    return f"INVESTMENT REPORT: {analysis}. Recommendation: BUY"

def main():
    print("Multi-agent system demo...")
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    
    # Agent 1: Data collector
    data_agent = Agent(
        name="DataCollector",
        client=client,
        system_prompt="You collect financial data.",
        tools=[get_stock_data]
    )
    
    # Agent 2: Report writer  
    writer_agent = Agent(
        name="ReportWriter",
        client=client,
        system_prompt="You write professional reports.",
        tools=[write_report]
    )
    
    print("Agent 1: Getting Tesla data...")
    data_result = data_agent.run("Get Tesla stock data")
    print(f"Data: {data_result}")
    
    print("\nAgent 2: Writing report...")
    report_result = writer_agent.run(f"Write a report based on: {data_result}")
    print(f"Report: {report_result}")
    
    print("\nMulti-agent task complete!")

if __name__ == "__main__":
    main()
