# Video 1: Introduction to Datapizza-AI

## Introduction (1.5 min)

Hey everyone! Welcome to this complete series on Datapizza-AI, where we're going to build production-ready GenAI applications from scratch.

If you've been trying to build with LLMs and found yourself wrestling with inconsistent APIs, debugging mysterious errors, or wondering how to actually ship something reliable—this series is for you.

[Visual: Show messy code snippets transforming into clean, organized structure]

Datapizza-AI is a framework that gives you clear interfaces and predictable behavior for everything from simple chatbots to complex multi-agent systems. Think of it as your reliable foundation for GenAI work.

By the end of this video, you'll understand what makes Datapizza-AI different and have your first working chatbot running. Let's jump in.

[Transition slide: "What We'll Cover Today"]

## Content Main (6 min)

### What Problem Does Datapizza-AI Solve? (2 min)

Let's be honest—building with LLMs can be frustrating. You've got different APIs for OpenAI, Anthropic, Google. Each one has its own quirks. Memory management is all over the place. And when something breaks in production, good luck figuring out why.

[Visual: Split screen showing different provider APIs side by side]

Datapizza-AI solves this by giving you:

**First**: A unified client interface. Whether you're using GPT, Claude, or Gemini, the code looks the same. Write once, swap providers easily.

**Second**: Built-in memory management. No more manually tracking conversation history or losing context mid-chat.

**Third**: End-to-end observability. You can actually see what's happening—token usage, response times, the whole pipeline.

[Visual: Diagram showing unified architecture]

The framework isn't trying to abstract everything away. You still have control. But it handles the tedious stuff so you can focus on building.

### Quick Installation and Setup (1.5 min)

Getting started takes about 30 seconds. You need Python 3.12 or higher.

[Show terminal]

```bash
pip install datapizza-ai
```

That's it for the core. If you want a specific provider, install the client:

```bash
pip install datapizza-ai-clients-openai
```

Create a `.env` file for your API keys:

```
OPENAI_API_KEY=sk-your-key-here
```

[Note for narrator: Speak casually, like you're helping a friend set this up]

### Your First Working Example (2.5 min)

Let's write some code. I'm going to show you the simplest possible chatbot, then we'll break down what's happening.

[Show code editor]

```python
import os
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient

load_dotenv()

client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o",
    system_prompt="You are a helpful AI assistant."
)

response = client.invoke("Explain quantum computing in one sentence")
print(response.text)
```

[Run the code, show output]

That's it. Seven lines of actual code and you have a working LLM client.

Here's what's happening: We load environment variables, create a client with our API key and model choice, add a system prompt to set behavior, and invoke it with a question.

[Highlight each part as you explain]

The `response` object gives you not just the text, but metadata too—tokens used, model info, everything you need for monitoring.

Notice we're using `response.text` to get the actual answer. The framework wraps everything in structured objects so you always know what you're working with.

[Visual: Show response object structure]

This pattern—client, invoke, response—is the foundation for everything we'll build in this series.

## Conclusion (1.5 min)

Alright, let's recap what we covered:

Datapizza-AI gives you a unified interface across different LLM providers, handles memory and context automatically, and provides visibility into what's actually happening in your application.

We installed the framework in seconds and built a working chatbot in seven lines of code.

[Visual: Show key points as bullets]

In the next video, we're going to take this further. We'll add conversation memory so the chatbot actually remembers what you said, implement caching to save money and speed things up, and handle errors properly so nothing breaks in production.

This is just the beginning. By the end of this series, you'll be building multi-agent systems and production RAG pipelines.

If you're following along, try modifying that system prompt or asking different questions. Get comfortable with the basic client pattern—everything builds from here.

See you in the next one!

[Note for narrator: End with energy, this should feel like the start of something exciting]
