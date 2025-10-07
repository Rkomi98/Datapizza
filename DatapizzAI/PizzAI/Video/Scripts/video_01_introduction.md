# Video 1: Introduction to Datapizza-AI

## Introduction (2 min)

Hey everyone! Welcome to this complete series on Datapizza-AI framework. I am Mirko Calcaterra, AI engineer in Datapizza and in this playlist we will show you how to build production-ready AI application from scratch.

If you've been trying to build with LLMs and found yourself wrestling with inconsistent APIs, debugging mysterious errors, or just wondering how to actually ship something that won't break in production, you're in the right place.

[Visual: Show messy code snippets transforming into clean, organized structure]

Datapizza-AI is a framework that gives you clear interfaces and predictable behavior for everything from simple chatbots to complex multi-agent systems. Think of it as your reliable foundation for GenAI work.

Now, before we dive in, quick heads up: this is a hands-on series. By the end of these nine videos, you'll have built chatbots, AI agents, RAG systems, the whole stack. And you'll actually understand how they work under the hood.

In this first video specifically, you're going to understand what makes Datapizza-AI different and have your first working chatbot running in about seven lines of code. That is a pretty solid start.

Alright, here's what we're covering today.

## Content Main (6.5 min)

### What Problem Does Datapizza-AI Solve? (2 min)

Okay, so here's the thing—building with LLMs can be frustrating as hell. You've got different APIs for OpenAI, Anthropic, Google. Each one has its own quirks and weird edge cases. Memory management? All over the place. And when something breaks in production, good luck figuring out why. With datapizza-ai it will be easier to monitor and debug everything you build. This easy-to-use framework merges tools customizations and full control on built application.

[Visual: Split screen showing different provider APIs side by side]

Datapizza-AI solves this by giving you:

**First**: A unified client interface. Whether you're using GPT, Claude, or Gemini, the code looks the same. Write once, swap providers easily.

**Second**: Built-in memory management. No more manually tracking conversation history or losing context mid-chat.

**Third**: End-to-end observability. You can actually see what's happening—token usage, response times, the whole pipeline.

[Visual: Diagram showing unified architecture]

The framework isn't trying to abstract everything away. You still have control. But it handles the tedious stuff so you can focus on building.

### Quick Installation and Setup (1.5 min)

Alright, time to actually install this thing. Takes about 30 seconds, no joke. You'll need Python 3.12 or higher.

[Show terminal]

```bash
pip install datapizza-ai
```

That's it for the core. If you want a specific provider, install the client (OpenAI is already present in the library):

```bash
pip install datapizza-ai-clients-openai
```

Create a `.env` file for your API keys:

```
OPENAI_API_KEY=sk-your-key-here
```

[Note for narrator: Speak casually, like you're helping a friend set this up]

### Your First Working Example (3 min)

Now for the fun part—let's write some code. I'm going to show you the simplest possible chatbot, then we'll break down exactly what's happening.

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

The `response` object gives you not just the text, but metadata too, like tokens used, model info, everything you need for monitoring.

Notice we're using `response.text` to get the actual answer. The framework wraps everything in structured objects so you always know what you're working with.

[Visual: Show response object structure]

This pattern—client, invoke, response—is the foundation for everything we'll build in this series.

## Conclusion (1.5 min)

Alright, so quick recap of what we just built:

Datapizza-AI gives you a unified interface across different LLM providers, handles memory and context automatically, and provides visibility into what's actually happening in your application. You can easily debug and control your code whenever you need.

We installed the framework in literally seconds and built a working chatbot in seven lines of code.

[Visual: Show key points as bullets]

Coming up in the next video, we're taking this way further. We'll add conversation memory so the chatbot actually remembers what you said, implement caching to save you money and speed things up, and handle errors properly so nothing breaks in production.

And this is just the beginning. By the end of this series, you'll be building multi-agent systems and production RAG pipelines. So real and complete products.

If you're coding along, and you should be, try modifying that system prompt or asking different questions. Experiment with it. Get comfortable with the basic client pattern because everything we build from here uses this foundation.

Code's in the description below, and if you found this useful, hit the like button. I'll catch you in the next video!

