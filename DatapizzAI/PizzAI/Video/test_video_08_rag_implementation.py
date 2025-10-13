"""
Test script for Video 8: Complete RAG Implementation
This script validates all code examples from the video script.

NOTE: This test requires:
1. Docker running Qdrant: docker run -p 6333:6333 qdrant/qdrant
2. pip install datapizza-ai-parsers-docling
3. A sample PDF file for testing
"""

import os
from dotenv import load_dotenv

# Test imports
print("Testing imports...")
try:
    from datapizza.clients.openai import OpenAIClient
    from datapizza.embedders.openai import OpenAIEmbedder
    from datapizza.core.vectorstore import VectorConfig
    from datapizza.vectorstores.qdrant import QdrantVectorstore
    from datapizza.pipeline import IngestionPipeline, DagPipeline
    from datapizza.modules.splitters import NodeSplitter
    from datapizza.embedders import ChunkEmbedder
    from datapizza.modules.rewriters import ToolRewriter
    from datapizza.modules.prompt import ChatPromptTemplate
    print("✓ All basic imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)

# Try to import DoclingParser
try:
    from datapizza.modules.parsers.docling import DoclingParser
    print("✓ DoclingParser import successful")
    has_docling = True
except ImportError as e:
    print(f"⚠ DoclingParser not available: {e}")
    print("  Install with: pip install datapizza-ai-parsers-docling")
    has_docling = False

load_dotenv()

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    print("✗ OPENAI_API_KEY not found in environment")
    exit(1)

print("\n" + "="*60)
print("TEST 1: Client Setup")
print("="*60)
try:
    # Client for text generation
    client = OpenAIClient(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini"
    )

    # Embedder client for creating vectors
    embedder_client = OpenAIEmbedder(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    print("✓ Clients initialized successfully")
except Exception as e:
    print(f"✗ Client setup failed: {e}")
    exit(1)

print("\n" + "="*60)
print("TEST 2: Qdrant Connection")
print("="*60)
try:
    vectorstore = QdrantVectorstore(host="localhost", port=6333)
    print("✓ Connected to Qdrant")
except Exception as e:
    print(f"✗ Qdrant connection failed: {e}")
    print("  Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")
    exit(1)

print("\n" + "="*60)
print("TEST 3: Create Collection")
print("="*60)
try:
    collection_name = "test_video_08"
    
    # Delete if exists
    try:
        vectorstore.delete_collection(collection_name)
        print("  Cleaned up existing collection")
    except:
        pass
    
    vectorstore.create_collection(
        collection_name,
        vector_config=[VectorConfig(name="embedding", dimensions=1536)]
    )
    print(f"✓ Collection '{collection_name}' created successfully")
except Exception as e:
    print(f"✗ Collection creation failed: {e}")
    exit(1)

print("\n" + "="*60)
print("TEST 4: Ingestion Pipeline Setup")
print("="*60)
try:
    if not has_docling:
        print("⊘ Skipping - DoclingParser not installed")
    else:
        ingestion_pipeline = IngestionPipeline(
            modules=[
                DoclingParser(),
                NodeSplitter(max_char=1000),
                ChunkEmbedder(client=embedder_client),
            ],
            vector_store=vectorstore,
            collection_name=collection_name
        )
        print("✓ Ingestion pipeline created successfully")
        
        # Test with sample PDF if available
        test_pdf = "/home/mcalcaterra/Documenti/GitHub/Datapizza/DatapizzAI/PizzAI/document.pdf"
        if os.path.exists(test_pdf):
            print("  Found test PDF, running ingestion...")
            ingestion_pipeline.run(test_pdf, metadata={"source": "test_upload"})
            print("✓ Document ingestion successful")
            
            # Verify data was stored
            res = vectorstore.search(
                query_vector=[0.0] * 1536,
                collection_name=collection_name,
                k=2,
            )
            print(f"✓ Search verification: found {len(res)} chunks")
        else:
            print(f"  No test PDF found at {test_pdf}")
            print("  Pipeline setup validated but not executed")
except Exception as e:
    print(f"✗ Ingestion pipeline failed: {e}")

print("\n" + "="*60)
print("TEST 5: DagPipeline Retrieval Setup")
print("="*60)
try:
    # Initialize components
    query_rewriter = ToolRewriter(
        client=client,
        system_prompt="Rewrite user queries to improve retrieval accuracy."
    )

    # Use the same embedder from ingestion
    retriever = QdrantVectorstore(host="localhost", port=6333)

    prompt_template = ChatPromptTemplate(
        user_prompt_template="User question: {{user_prompt}}",
        retrieval_prompt_template="Retrieved content:\n{% for chunk in chunks %}{{ chunk.text }}\n{% endfor %}"
    )

    # Build the DAG
    dag_pipeline = DagPipeline()
    dag_pipeline.add_module("rewriter", query_rewriter)
    dag_pipeline.add_module("embedder", embedder_client)
    dag_pipeline.add_module("retriever", retriever)
    dag_pipeline.add_module("prompt", prompt_template)
    dag_pipeline.add_module("generator", client)

    # Connect the modules
    dag_pipeline.connect("rewriter", "embedder", target_key="text")
    dag_pipeline.connect("embedder", "retriever", target_key="query_vector")
    dag_pipeline.connect("retriever", "prompt", target_key="chunks")
    dag_pipeline.connect("prompt", "generator", target_key="memory")

    print("✓ DagPipeline created successfully")
    print("  Modules: rewriter -> embedder -> retriever -> prompt -> generator")
except Exception as e:
    print(f"✗ DagPipeline setup failed: {e}")
    exit(1)

print("\n" + "="*60)
print("TEST 6: DagPipeline Execution")
print("="*60)
try:
    # Check if we have data in the collection
    test_search = vectorstore.search(
        query_vector=[0.0] * 1536,
        collection_name=collection_name,
        k=1,
    )
    
    if len(test_search) == 0:
        print("⊘ Skipping - no documents in collection")
        print("  Run ingestion first to test retrieval")
    else:
        query = "tell me something about this document"
        result = dag_pipeline.run({
            "rewriter": {"user_prompt": query},
            "prompt": {"user_prompt": query},
            "retriever": {"collection_name": collection_name, "k": 3},
            "generator": {"input": query}
        })

        print(f"✓ DagPipeline execution successful")
        print(f"  Response: {str(result['generator'])[:100]}...")
except Exception as e:
    print(f"✗ DagPipeline execution failed: {e}")

print("\n" + "="*60)
print("TEST 7: Metadata Filtering")
print("="*60)
try:
    if len(test_search) == 0:
        print("⊘ Skipping - no documents in collection")
    else:
        query = "test query"
        result = dag_pipeline.run({
            "rewriter": {"user_prompt": query},
            "prompt": {"user_prompt": query},
            "retriever": {
                "collection_name": collection_name,
                "k": 3,
                "filter": {"source": "test_upload"}
            },
            "generator": {"input": query}
        })
        print(f"✓ Metadata filtering successful")
except Exception as e:
    print(f"✗ Metadata filtering failed: {e}")

print("\n" + "="*60)
print("CLEANUP")
print("="*60)
try:
    vectorstore.delete_collection(collection_name)
    print(f"✓ Test collection deleted")
except Exception as e:
    print(f"⚠ Cleanup warning: {e}")

print("\n" + "="*60)
print("SUMMARY: Video 8 Code Validation")
print("="*60)
print("All critical code paths have been tested.")
print("Check the results above for any failures.")
print("\nPrerequisites for full testing:")
print("  1. Qdrant running on localhost:6333")
print("  2. datapizza-ai-parsers-docling installed")
print("  3. Sample PDF file available")

