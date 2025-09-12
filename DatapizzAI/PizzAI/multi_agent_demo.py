#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from datapizzai.clients import ClientFactory
from datapizzai.agents import Agent
from datapizzai.tools import tool

load_dotenv()

@tool
def get_info(topic: str) -> str:
    """Get information about a topic"""
    return f"Info about {topic}: Revenue 2.5M, Costs 1.8M, Users 15000"

@tool
def extract_numbers(text: str) -> str:
    """Extract numbers from text"""
    return "Revenue: 2.5M, Costs: 1.8M, Users: 15000"

@tool
def calculate(expression: str) -> str:
    """Calculate mathematical expressions"""
    try:
        result = eval(expression.replace("M", "*1000000"))
        return str(result)
    except:
        return "Error in calculation"

def main():
    print("Multi-agent workflow demo...")
    
    client = ClientFactory.create(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o"
    )
    
    # Agent 1: Research agent with info and extraction tools
    researcher = Agent(
        name="Researcher",
        client=client,
        system_prompt="Get info and extract numbers. Be brief.",
        tools=[get_info, extract_numbers]
    )
    
    # Agent 2: Calculator agent
    calculator = Agent(
        name="Calculator",
        client=client,
        system_prompt="Do calculations. Be brief.",
        tools=[calculate]
    )
    
    # Agent 3: Formatter agent
    formatter = Agent(
        name="Formatter",
        client=client,
        system_prompt="Format output nicely. Be brief."
    )
    
    print("1. Researcher gathering data...")
    research_result = researcher.run("Get company performance data and extract key numbers")
    
    print("2. Calculator computing profit...")
    calc_result = calculator.run(f"Calculate profit: 2.5M - 1.8M using this data: {research_result}")
    
    print("3. Formatter creating final report...")
    final_result = formatter.run(f"Format this into a nice summary: {research_result} Profit: {calc_result}")
    
    print(f"\nFinal Report:\n{final_result}")

if __name__ == "__main__":
    main()
