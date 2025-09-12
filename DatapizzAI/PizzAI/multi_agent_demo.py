#!/usr/bin/env python3
"""
Multi-Agent System Demo for GIF Recording
Run this script to demonstrate the multi-agent system in action.
"""

import os
import time
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.agents import Agent
from datapizzai.tools import tool

# Load environment variables
load_dotenv()

# Mock tools for demo
@tool
def analyze_market_data(market: str) -> str:
    """Analyze market data and trends"""
    time.sleep(1)  # Simulate processing
    return f"Market analysis for {market}: Growth +15%, Volume increased 23%, Strong bullish trend detected"

@tool
def fetch_financial_data(company: str) -> str:
    """Fetch financial data for a company"""
    time.sleep(1)  # Simulate API call
    return f"Financial data for {company}: Revenue $2.1B (+12% YoY), Profit margin 18%, Strong fundamentals"

@tool
def generate_chart(data_type: str) -> str:
    """Generate charts and visualizations"""
    time.sleep(1)  # Simulate chart generation
    return f"📊 Generated {data_type} chart with trend analysis and projections"

def main():
    print("🚀 Starting Multi-Agent Financial Analysis System")
    print("=" * 60)
    
    # Create client
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    
    # Create specialized agents
    print("👥 Creating specialized agents...")
    
    # Market analyst agent
    market_analyst = Agent(
        name="MarketAnalyst",
        client=client,
        system_prompt="You are a market analyst. Analyze trends, patterns, and provide insights on market conditions.",
        tools=[analyze_market_data, fetch_financial_data]
    )
    
    # Data visualization agent  
    visualizer = Agent(
        name="DataVisualizer",
        client=client,
        system_prompt="You create compelling data visualizations and charts to support analysis.",
        tools=[generate_chart]
    )
    
    # Report writer agent
    writer = Agent(
        name="ReportWriter", 
        client=client,
        system_prompt="You write clear, professional financial reports with actionable insights."
    )
    
    # Coordinator agent
    coordinator = Agent(
        name="FinancialCoordinator",
        client=client,
        system_prompt="You coordinate a team of financial experts to deliver comprehensive market analysis reports.",
        can_call=[market_analyst, visualizer, writer]
    )
    
    print("✅ Agents created successfully!")
    print("\n🎯 Task: Analyze Tesla's market performance and create executive report")
    print("⏳ Coordinator delegating tasks to specialized agents...\n")
    
    # Run the multi-agent system
    result = coordinator.run(
        "Analyze Tesla's current market performance, create visualizations, and write an executive summary report"
    )
    
    print("\n" + "=" * 60)
    print("📋 FINAL REPORT:")
    print("=" * 60)
    print(result)
    print("\n✨ Multi-agent analysis complete!")

if __name__ == "__main__":
    main()
