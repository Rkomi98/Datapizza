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
    return f"{symbol} stock: $245.67 (+3.2%), volume 2.1M shares, P/E ratio 18.5"

@tool
def analyze_trends(data: str) -> str:
    """Analyze market trends"""  
    return f"Analysis: Strong upward trend, good fundamentals, 15% growth projected"

def main():
    print("Multi-agent demo starting...")
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    
    # Create analyst agent
    analyst = Agent(
        name="Analyst",
        client=client,
        system_prompt="You analyze stock data and market trends.",
        tools=[get_stock_data, analyze_trends]
    )
    
    print("Running Tesla analysis...")
    result = analyst.run("Analyze Tesla stock performance and provide investment insights")
    
    print("\nResult:")
    print(result)

if __name__ == "__main__":
    main()
