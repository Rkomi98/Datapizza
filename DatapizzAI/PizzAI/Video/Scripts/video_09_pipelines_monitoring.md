# Video 9: Pipelines and Production Monitoring

## Introduction (1.5 min)

Hey everyone, welcome to the final video in this series! We've built chatbots, agents, multi-agent systems, and RAG pipelines. But here's the thing we haven't covered yet: how do you actually run this stuff in production?

[Visual: Show development environment transforming into production architecture]

Production means reliability, observability, and orchestration. You need to process data through complex workflows, monitor what's happening in real time, and actually debug when things inevitably go wrong.

Today we're covering two critical topics: building pipelines for complex data workflows, and implementing comprehensive monitoring with OpenTelemetry, Prometheus, and Grafana.

This is what separates proof-of-concepts from production systems that actually work at scale.

Alright, three pipeline types.

## Content Main (7.5 min)

### Understanding Pipelines (2 min)

So Datapizza-AI gives you three pipeline types, and each one is for different use cases. Let me break them down.

[Visual: Show three pipeline diagrams side by side]

**IngestionPipeline**: For processing documents into vector stores. Parser → Splitter → Embedder → Storage. This is your RAG ingestion flow.

**DagPipeline**: For dependency graphs. Define nodes and connections, execute in parallel where possible. Use this for complex data transformations.

**FunctionalPipeline**: For advanced control flow with branching, loops, and conditional execution. This is for business logic and multi-step workflows.

Let me show you each one.

### IngestionPipeline in Action (1.5 min)

The ingestion pipeline we used in the RAG video is a formal pipeline type:

```python
from datapizza.pipelines import IngestionPipeline
from datapizza.parsers import TextParser
from datapizza.rag.splitter import NodeSplitter
from datapizza.rag.embedder import NodeEmbedder

components = [
    TextParser(),
    NodeSplitter(max_char=1000),
    NodeEmbedder(client=client, model_name="text-embedding-3-small")
]

pipeline = IngestionPipeline(
    modules=components,
    vector_store=vectorstore,
    collection_name="documents"
)

# Process documents
chunks = pipeline.run(
    file_path="document.txt",
    metadata={"source": "internal_docs"}
)
```

[Show execution]

Each component processes the output of the previous one. The pipeline handles sequencing, error propagation, and final storage.

This pattern scales. Add a captioner for images, a metatagger for keywords—just insert components into the list.

### DagPipeline for Complex Dependencies (2 min)

DAG pipelines let you define explicit dependencies between operations.

```python
from datapizza.pipelines import DagPipeline

class DataLoader(PipelineComponent):
    def _run(self, **kwargs):
        return {"reviews": ["Great product!", "Terrible", "It's okay"]}

class SentimentAnalyzer(PipelineComponent):
    def _run(self, reviews, **kwargs):
        results = [
            {"text": r, "sentiment": self._classify(r)} 
            for r in reviews
        ]
        return {"sentiment_results": results}

class StatisticsCalculator(PipelineComponent):
    def _run(self, sentiment_results, **kwargs):
        sentiments = [r["sentiment"] for r in sentiment_results]
        return {
            "stats": {
                "positive": sentiments.count("positive"),
                "negative": sentiments.count("negative")
            }
        }

pipeline = DagPipeline()
pipeline.add_module("loader", DataLoader())
pipeline.add_module("analyzer", SentimentAnalyzer())
pipeline.add_module("stats", StatisticsCalculator())

pipeline.connect("loader", "analyzer", "reviews", "reviews")
pipeline.connect("analyzer", "stats", "sentiment_results", "sentiment_results")

results = pipeline.run({})
```

[Show execution with timing]

The pipeline executes nodes in the correct order based on dependencies. If two nodes have no dependency, they run in parallel.

This is perfect for ETL workflows, data processing pipelines, multi-step analysis.

### FunctionalPipeline with Branching (2 min)

Functional pipelines support conditional execution:

```python
from datapizza.pipelines import FunctionalPipeline, Dependency

class DocumentClassifier(PipelineComponent):
    def _run(self, documents, **kwargs):
        urgent = [d for d in documents if d.get("priority") == "urgent"]
        return {
            "documents": documents,
            "urgent_documents": urgent,
            "has_urgent": len(urgent) > 0
        }

class NotificationSender(PipelineComponent):
    def _run(self, **kwargs):
        return {"notification_sent": True}

class ReportGenerator(PipelineComponent):
    def _run(self, documents, **kwargs):
        return {"report": f"Processed {len(documents)} documents"}

pipeline = (
    FunctionalPipeline()
    .run(name="load", node=DataLoader())
    .then(name="classify", node=DocumentClassifier(), target_key="documents")
    .branch(
        condition=lambda ctx: ctx.get("classify", {}).get("has_urgent", False),
        if_true=FunctionalPipeline().run("notify", NotificationSender()),
        if_false=FunctionalPipeline().run("report", ReportGenerator())
    )
)

results = pipeline.execute()
```

[Show both branches executing based on different data]

The pipeline routes execution based on runtime conditions. Urgent documents trigger notifications, normal documents get processed differently.

This is how you encode business logic into reproducible workflows.

### Production Monitoring (2 min)

Alright, now let's talk about observability. Because in production, you NEED to know what's happening at all times.

Datapizza-AI integrates OpenTelemetry for tracing:

```python
from datapizza.monitoring import ContextTracing

tracer = ContextTracing()

with tracer.trace("conversation") as trace:
    memory.add_turn([TextBlock(content=user_input)], ROLE.USER)
    response = client.invoke(user_input, memory=memory)
    memory.add_turn([TextBlock(content=response.text)], ROLE.ASSISTANT)
```

[Show trace output]

You get automatic tracking of token usage, latency, and call patterns.

For metrics, connect Prometheus:

```python
from prometheus_client import Counter, Histogram, start_http_server

request_counter = Counter(
    "chatbot_requests_total",
    "Total requests",
    ["status"]
)

response_time = Histogram(
    "chatbot_response_time_seconds",
    "Response time"
)

token_usage = Counter(
    "chatbot_tokens_total",
    "Token usage",
    ["type"]
)

# Start metrics server
start_http_server(8000)

# Record metrics
with tracer.trace("request"):
    start = time.time()
    try:
        response = client.invoke(query)
        request_counter.labels(status="success").inc()
        token_usage.labels(type="prompt").inc(response.prompt_tokens_used)
        token_usage.labels(type="completion").inc(response.completion_tokens_used)
    except Exception as e:
        request_counter.labels(status="error").inc()
    finally:
        response_time.observe(time.time() - start)
```

[Show Grafana dashboard]

Now you have real-time dashboards showing request rates, error rates, token consumption, and latency percentiles.

This is production-grade observability. You can set alerts, debug issues, optimize costs—all from your monitoring stack.

## Conclusion (1.5 min)

Alright, so let's recap this entire series for a second:

We started with basic chatbots, added memory and caching. We explored structured outputs and multimodal capabilities. We built autonomous agents, then multi-agent systems. We implemented complete RAG pipelines. And today we covered production workflows and monitoring.

[Visual: Show journey from Video 1 to Video 9]

You now have everything you need to build production GenAI applications with Datapizza-AI. Like, actually ship them to production.

The patterns we covered—unified clients, explicit memory management, tool-based agents, RAG pipelines, and observability—these are the foundations of reliable AI systems that companies actually use.

This isn't just about making things work on your laptop. It's about making things work reliably, at scale, with visibility and control. That's the difference between a toy project and a real product.

[Visual: Show production architecture diagram]

If you've followed along and built these systems, you're in a really good position. Now take them further. Deploy to production. Handle real traffic. Scale them up. That's where the real learning happens.

Thanks for sticking with this entire series. Seriously, if you made it this far, you're committed. Now go build something amazing with what you learned.

If this series helped you, hit that subscribe button and drop a comment with what you're building. I'd love to see it. Code for everything is in the description.

Catch you in the next series!

[Note for narrator: This should feel like a graduation—the viewer has learned a complete skill set and is ready for production work]
