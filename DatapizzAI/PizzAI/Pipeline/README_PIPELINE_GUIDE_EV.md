# DatapizzAI pipeline guide

This guide provides practical examples for using the three pipeline types available in DatapizzAI:

- **IngestionPipeline**: for processing and ingesting documents into vector stores
- **DagPipeline**: for creating dependency graphs between components  
- **FunctionalPipeline**: for functional pipelines with branching, loops, and dependencies

## Installation

```bash
pip install datapizzai python-dotenv pyyaml
```

Configure the `.env` file with the necessary API keys:

```env
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

## 1. Ingestion pipeline

### Description

The IngestionPipeline is designed to process documents and ingest them into vector stores. It's ideal for building knowledge bases and RAG systems.

### Main components

- **Parser**: content extraction from documents
- **Splitter**: content division into chunks
- **Embedder**: vector embeddings generation
- **Vector store**: chunk storage with embeddings

### Practical example

```python
from datapizzai.pipeline import IngestionPipeline
from datapizzai.modules.parsers import TextParser
from datapizzai.modules.splitters import RecursiveSplitter
from datapizzai.embedders import ClientEmbedder
from datapizzai.clients import OpenAIClient

# Configure components
client = OpenAIClient(api_key="your_key", model="gpt-4o-mini")
components = [
    TextParser(),
    RecursiveSplitter(chunk_size=200, chunk_overlap=50),
    ClientEmbedder(client=client, model="text-embedding-3-small")
]

# Create pipeline
pipeline = IngestionPipeline(modules=components)

# Execute processing
chunks = pipeline.run("document.txt", metadata={"source": "example"})
```

### Flow diagram

```mermaid
graph TD
    A[Document] --> B[TextParser]
    B --> C[RecursiveSplitter]
    C --> D[ClientEmbedder]
    D --> E[Vector Store]
    
    B --> F[Text extraction]
    C --> G[Chunk division]
    D --> H[Embeddings generation]
    E --> I[Storage]
```

### Complete script

See `examples/ingestion_example.py` for a complete working example.

## 2. Dag pipeline

### Description

The DagPipeline allows creating dependency graphs (DAG - Directed Acyclic Graph) between components, where each node can depend on the results of previous nodes.

### Main features

- **Nodes**: components that perform specific operations
- **Connections**: define dependencies between nodes
- **Parallel execution**: independent nodes are executed in parallel
- **Error handling**: controlled error propagation through the graph

### Practical example

```python
from datapizzai.pipeline import DagPipeline
from datapizzai.core.models import PipelineComponent

class DataLoader(PipelineComponent):
    def run(self, **kwargs):
        return {"data": ["text1", "text2", "text3"]}

class SentimentAnalyzer(PipelineComponent):
    def run(self, data, **kwargs):
        # Sentiment analysis logic
        return {"results": [{"text": t, "sentiment": "positive"} for t in data]}

# Create DAG pipeline
pipeline = DagPipeline()
pipeline.add_module("loader", DataLoader())
pipeline.add_module("analyzer", SentimentAnalyzer())

# Define connections
pipeline.connect(
    source_node="loader",
    target_node="analyzer",
    source_key="data",
    target_key="data"
)

# Execute
results = pipeline.run({})
```

### Flow diagram

```mermaid
graph TD
    A[DataLoader] --> B[SentimentAnalyzer]
    B --> C[StatisticsCalculator]
    A --> D[MetadataExtractor]
    B --> E[ReportGenerator]
    C --> E
    D --> E
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#f3e5f5
    style D fill:#f3e5f5
    style E fill:#e8f5e8
```

### Complete script

See `examples/dag_example.py` for a sentiment analysis example with dependency graph.

## 3. Functional pipeline

### Description

The FunctionalPipeline offers a functional approach to pipeline construction with support for conditional branching, loops, and complex dependencies.

### Advanced features

- **Branching**: conditional execution of sub-pipelines
- **Foreach**: iteration over data collections
- **Dependencies**: explicit dependency management between nodes
- **Composition**: combination of complex pipelines

### Practical example

```python
from datapizzai.pipeline import FunctionalPipeline, Dependency

# Sub-pipeline for notifications
notification_pipeline = FunctionalPipeline().run(
    name="notify",
    node=NotificationSender()
)

# Main pipeline with branching
pipeline = (
    FunctionalPipeline()
    .run(name="load", node=DataLoader())
    .then(name="classify", node=Classifier(), target_key="data")
    .branch(
        condition=lambda ctx: ctx.get("classify", {}).get("has_urgent", False),
        dependencies=[Dependency(node_name="classify")],
        if_true=notification_pipeline,
        if_false=standard_processing_pipeline
    )
)

# Execute
results = pipeline.execute()
```

### Flow diagram

```mermaid
graph TD
    A[DataLoader] --> B[Classifier]
    B --> C{Condition}
    C -->|True| D[NotificationPipeline]
    C -->|False| E[StandardProcessing]
    
    D --> F[SendNotification]
    E --> G[ProcessGeneral]
    G --> H[BuildReport]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#ffebee
    style E fill:#f1f8e9
    style F fill:#ffebee
    style G fill:#f1f8e9
    style H fill:#e8f5e8
```

### Complete script

See `examples/functional_example.py` for a complete example with branching and foreach.

## YAML configuration

All pipelines support YAML configuration for greater flexibility and reusability.

### Example for DagPipeline

```yaml
dag_pipeline:
  clients:
    openai_client:
      provider: "openai"
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4o-mini"
  
  modules:
    - name: "data_loader"
      module: "mymodules.loaders"
      type: "CSVLoader"
      params:
        file_path: "data.csv"
    
    - name: "analyzer"
      module: "mymodules.analysis"
      type: "TextAnalyzer"
      params:
        client: "openai_client"
  
  connections:
    - from: "data_loader"
      to: "analyzer"
      source_key: "data"
      target_key: "texts"
```

### Example for FunctionalPipeline

```yaml
modules:
  - name: "loader"
    module: "mymodules.loaders"
    type: "DocumentLoader"
  
  - name: "processor"
    module: "mymodules.processors"  
    type: "TextProcessor"

pipeline:
  - type: "run"
    name: "load_data"
    node: "loader"
  
  - type: "then"
    name: "process"
    node: "processor"
    target_key: "documents"
    dependencies:
      - node_name: "load_data"
```

## Pipeline comparison

| Feature | IngestionPipeline | DagPipeline | FunctionalPipeline |
|---------|------------------|-------------|-------------------|
| **Use case** | Document processing | Dependency graphs | Complex pipelines |
| **Complexity** | Low | Medium | High |
| **Branching** | No | No | Yes |
| **Loops** | No | No | Yes (foreach) |
| **Parallelism** | Sequential | Automatic | Controlled |
| **Vector store** | Integrated | Manual | Manual |

## Best practices

### Pipeline selection

- **IngestionPipeline**: for RAG, knowledge bases, document processing
- **DagPipeline**: for workflows with complex dependencies, multi-step analysis  
- **FunctionalPipeline**: for complex business logic, conditional routing

### Error handling

```python
# Always handle exceptions in components
class SafeProcessor(PipelineComponent):
    def run(self, **kwargs):
        try:
            return self.process_data(kwargs)
        except Exception as e:
            return {"error": str(e), "success": False}
```

### Performance

- Use async components when possible
- Minimize dependencies in DagPipeline
- Cache intermediate results for complex pipelines

## Complete examples

Complete and functional example scripts are available in:

- `examples/ingestion_example.py`
- `examples/dag_example.py`  
- `examples/functional_example.py`

Each script includes sample data and can be run directly to test functionality.
